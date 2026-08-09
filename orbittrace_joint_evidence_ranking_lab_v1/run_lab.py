#!/usr/bin/env python3
"""Development-only lab: jointly score all recurrent candidates with frozen v8 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_unified_recurrent_catalogue_lab_v2 import run_lab as v2

YEARS = v1.YEARS
MONTH_KEYS = v1.MONTH_KEYS
CORPUS = "orbittrace-joint-evidence-ranking-lab-v1"
BLIND = v1.BLIND
EXPECTED_HARD = v1.EXPECTED_HARD
EXPECTED_SOFT = v1.EXPECTED_SOFT
EXPECTED_COMBINED = v1.EXPECTED_COMBINED
EXPECTED_P19_RESULT_SHA256 = v1.EXPECTED_P19_RESULT_SHA256
EXPECTED_P19_PRELABEL_SHA256 = v1.EXPECTED_P19_PRELABEL_SHA256
METHODS = ("multiplicity", "v3", "brown")
GEO_SUPPRESSION = (None, 0.25, 0.50, 0.75, 1.00, 1.50)
EVENT_JACCARD = (None, 0.10)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p19-result-json", required=True, type=Path)
    p.add_argument("--p19-prelabel-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def metric_key(metrics: dict[str, Any], suppression: dict[str, int]) -> tuple[float, ...]:
    return (
        float(metrics["recovered_at_100"]),
        float(metrics["recovered_at_50"]),
        float(metrics["recovered_at_25"]),
        float(metrics["top100_dominant_precision"]),
        float(metrics["mrr"]),
        -float(metrics["mean_qualified_candidates_per_recovered_label"]),
        -float(suppression["kept"]),
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(v1.sha256_file(args.p19_result_json) == EXPECTED_P19_RESULT_SHA256, "P19 result hash changed")
    require(v1.sha256_file(args.p19_prelabel_json) == EXPECTED_P19_PRELABEL_SHA256, "P19 prelabel hash changed")
    p19 = json.loads(args.p19_result_json.read_text())
    require(p19["verdict"] == "FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT", "P19 identity changed")
    payload = json.loads(args.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    soft = payload["soft_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    families = hard + soft
    require((len(hard), len(soft), len(families)) == (EXPECTED_HARD, EXPECTED_SOFT, EXPECTED_COMBINED), "family universe changed")

    v1.mult.YEARS = YEARS
    v1.mult.MONTH_KEYS = MONTH_KEYS
    v1.mult.TOP_K = 100
    runtime = v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _cal, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "months changed")

    eligible = v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in families}
    truths = {fid: v1.family_truth(f, hidden_labels, eligible) for fid, f in by_id.items()}
    hard_metrics = v1.monotone_metrics(hard, hard_order, truths, eligible)

    # Core experiment: every hard and soft candidate receives the exact same frozen v8
    # local-episode evidence calculation. No labels enter scoring.
    scored, scoring_summary = v1.mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == EXPECTED_COMBINED, "not all recurrent candidates scored")
    sets = {fid: set(map(str, by_id[fid]["event_ids"])) for fid in by_id}

    candidates = []
    best = None
    raw_orders = {}
    for method in METHODS:
        raw = [str(x) for x in v1.mult.rank_scored(scored, method)]
        require(len(raw) == EXPECTED_COMBINED and len(set(raw)) == EXPECTED_COMBINED, f"{method} rank invalid")
        raw_orders[method] = raw
        for geo in GEO_SUPPRESSION:
            for jac in EVENT_JACCARD:
                order, supdiag = v2.suppress(raw, by_id, sets, support, base, geo, jac)
                metrics = v1.monotone_metrics(families, order, truths, eligible)
                row = {
                    "method": method,
                    "geo_suppression": geo,
                    "event_jaccard": jac,
                    "suppression": supdiag,
                    "metrics": {k: v for k, v in metrics.items() if k != "first_rank_by_label"},
                    "order_sha256": hashlib.sha256("\n".join(order).encode()).hexdigest(),
                }
                candidates.append(row)
                key = metric_key(metrics, supdiag)
                if best is None or key > best["key"]:
                    best = {"key": key, "row": row, "order": order, "metrics": metrics}
    require(best is not None, "no joint evidence ranking")

    # Also expose the unsuppressed raw ranking for each evidence family.
    raw_metrics = {
        method: {k: v for k, v in v1.monotone_metrics(families, raw_orders[method], truths, eligible).items() if k != "first_rank_by_label"}
        for method in METHODS
    }

    viable = (
        int(best["metrics"]["recovered_at_100"]) >= int(hard_metrics["recovered_at_100"]) + 5
        and int(best["metrics"]["recovered_at_50"]) >= int(hard_metrics["recovered_at_50"])
        and float(best["metrics"]["top100_dominant_precision"]) >= float(hard_metrics["top100_dominant_precision"]) - 0.05
        and int(best["metrics"]["qualified_matches"]) >= int(hard_metrics["qualified_matches"]) + 20
    )
    verdict = "PASS_JOINT_FROZEN_EVIDENCE_RANKING_FEASIBILITY" if viable else "FAIL_JOINT_FROZEN_EVIDENCE_RANKING_FEASIBILITY"

    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 target-excluded development-only ranking laboratory",
        "candidate_universe": {"hard": len(hard), "soft": len(soft), "combined": len(families)},
        "hard_baseline": {k: v for k, v in hard_metrics.items() if k != "first_rank_by_label"},
        "raw_joint_evidence_rankings": raw_metrics,
        "best": best["row"],
        "grid": candidates,
        "scoring_summary": scoring_summary,
        "integrity": {
            "p19_result_sha256": EXPECTED_P19_RESULT_SHA256,
            "p19_prelabel_sha256": EXPECTED_P19_PRELABEL_SHA256,
            "labels_enter_family_scoring": False,
            "candidate_generation_changed": False,
            "membership_changed": False,
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": "Development feasibility only; exact P19 remains a no-go. PASS would justify joint evidence ranking inside a separately frozen URC architecture.",
    }
    (args.output / "joint_evidence_ranking_lab_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "JOINT_EVIDENCE_RANKING_LAB_V1.md").write_text(
        "# Joint frozen-evidence ranking lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- hard recovery@100: `{hard_metrics['recovered_at_100']}`\n"
        f"- best recovery@100: `{best['metrics']['recovered_at_100']}`\n"
        f"- best recovery@50: `{best['metrics']['recovered_at_50']}`\n"
        f"- best recovery@25: `{best['metrics']['recovered_at_25']}`\n"
        f"- best qualified: `{best['metrics']['qualified_matches']}`\n"
        f"- best top100 precision: `{best['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- method: `{best['row']['method']}`\n"
        f"- geometric suppression: `{best['row']['geo_suppression']}`\n"
        f"- Jaccard suppression: `{best['row']['event_jaccard']}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "hard_recovery100": hard_metrics["recovered_at_100"],
        "best_recovery100": best["metrics"]["recovered_at_100"],
        "best_recovery50": best["metrics"]["recovered_at_50"],
        "best_recovery25": best["metrics"]["recovered_at_25"],
        "best_qualified": best["metrics"]["qualified_matches"],
        "best_top100_precision": best["metrics"]["top100_dominant_precision"],
        "method": best["row"]["method"],
        "geo": best["row"]["geo_suppression"],
        "jac": best["row"]["event_jaccard"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
