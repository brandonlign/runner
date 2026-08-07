#!/usr/bin/env python3
"""One-shot v10 multiplicity-persistence rank-consensus development."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v8.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-rank-consensus-v10-development"
TOP_K = 100
EXPECTED_FAMILIES = 226
EXPECTED_QUALIFIED = 95
EXPECTED_M_RECOVERY = 58
EXPECTED_P_RECOVERY = 59
EXPECTED_M_PRECISION = 0.6884631112636006
EXPECTED_M_MRR = 0.045531138942766655
MIN_FULL_RECOVERY = 60
MIN_FULL_PRECISION = 0.68
SPLIT_PREFIX = "orbittrace-v10-label-split|"
CANDIDATES = ("rank_product", "rank_sum")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def consensus_order(multiplicity: list[str], persistence: list[str], method: str) -> list[str]:
    require(set(multiplicity) == set(persistence), "rank-consensus universe mismatch")
    rm = {fid: i for i, fid in enumerate(multiplicity, 1)}
    rp = {fid: i for i, fid in enumerate(persistence, 1)}
    if method == "rank_product":
        key = lambda fid: (rm[fid] * rp[fid], rm[fid] + rp[fid], rm[fid], rp[fid], fid)
    elif method == "rank_sum":
        key = lambda fid: (rm[fid] + rp[fid], rm[fid] * rp[fid], rm[fid], rp[fid], fid)
    else:
        raise ValueError(method)
    return sorted(multiplicity, key=key)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def label_panel(label: str) -> str:
    digest = hashlib.sha256((SPLIT_PREFIX + label).encode("utf-8")).digest()
    return "development" if digest[0] % 2 == 0 else "validation"


def masked_labels(hidden_labels: dict[str, str], allowed: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for event_id, label in hidden_labels.items():
        if label == "SPORADIC" or label in allowed:
            out[event_id] = label
        else:
            out[event_id] = "SPORADIC"
    return out


def better_candidate(name: str, metrics: dict[str, dict[str, Any]]) -> tuple[Any, ...]:
    m = metrics[name]
    median = float(m["median_rank"]) if m["median_rank"] is not None else float("inf")
    fixed_priority = 0 if name == "rank_product" else 1
    return (-int(m["recovered_at_100"]), -float(m["mrr"]), median, fixed_priority)


def exact_metric_match(observed: dict[str, Any], expected: dict[str, Any]) -> bool:
    scalar_keys = ("eligible_labels", "qualified_matches", "recovered_at_100", "recovered_at_500")
    if any(int(observed[k]) != int(expected[k]) for k in scalar_keys):
        return False
    float_keys = ("mrr", "macro_f1", "top100_dominant_precision")
    if any(abs(float(observed[k]) - float(expected[k])) > 1e-12 for k in float_keys):
        return False
    om = observed.get("median_rank")
    em = expected.get("median_rank")
    if om is None or em is None:
        return om is em
    return abs(float(om) - float(em)) <= 1e-12


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v8_result_json.read_text())

    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(predecessor["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 predecessor did not pass")
    require(int(predecessor["family_count"]) == EXPECTED_FAMILIES, "v8 family count changed")
    require(int(predecessor["qualified_known_showers"]) == EXPECTED_QUALIFIED, "v8 qualified count changed")
    require(int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]) == EXPECTED_M_RECOVERY, "v8 multiplicity recovery changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]) == EXPECTED_P_RECOVERY, "v8 persistence recovery changed")
    require(abs(float(predecessor["metrics"]["multiplicity"]["top100_dominant_precision"]) - EXPECTED_M_PRECISION) <= 1e-12, "v8 multiplicity precision changed")
    require(abs(float(predecessor["metrics"]["multiplicity"]["mrr"]) - EXPECTED_M_MRR) <= 1e-12, "v8 multiplicity MRR changed")
    require(all(predecessor["integrity_gates"].values()) and all(predecessor["scientific_gates"].values()), "v8 predecessor gates changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)

    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family-link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal gates changed")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 scale changed")

    # FIRST DEVELOPMENT DATA ACCESS. Frozen parser removes 20-55 before labels can be evaluated.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
    require([s["key"] for s in catalogue_sources] == list(MONTH_KEYS), "monthly source universe changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)
        print(f"rank-consensus-v10 year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(len(families) == EXPECTED_FAMILIES, f"v8 family universe changed: {len(families)}")
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence universe mismatch")
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)

    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every family scored")
    multiplicity_order = mult.rank_scored(scored, "multiplicity")
    baseline_orders = {
        "multiplicity": multiplicity_order,
        "label_free_persistence": persistence_order,
    }
    candidate_orders = {name: consensus_order(multiplicity_order, persistence_order, name) for name in CANDIDATES}

    prelabel_payload = {
        "family_count": len(families),
        "multiplicity": multiplicity_order,
        "label_free_persistence": persistence_order,
        **candidate_orders,
    }
    prelabel_sha = sha256_json(prelabel_payload)
    args.output.joinpath("rank_consensus_v10_prelabel_rankings.json").write_text(json.dumps(prelabel_payload, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("rank_consensus_v10_prelabel_rankings.sha256").write_text(prelabel_sha + "\n")

    # FIRST SHOWER-LABEL USE. Every family and every candidate ranking is already frozen above.
    eligible = mult.eligible_labels(hidden_labels)
    eligible_codes = sorted(eligible)
    dev_codes = {code for code in eligible_codes if label_panel(code) == "development"}
    val_codes = set(eligible_codes) - dev_codes
    require(dev_codes and val_codes, "label split produced an empty panel")
    split_payload = {
        "prefix": SPLIT_PREFIX,
        "eligible_label_count": len(eligible_codes),
        "development_codes": sorted(dev_codes),
        "validation_codes": sorted(val_codes),
    }
    split_sha = sha256_json(split_payload)

    dev_hidden = masked_labels(hidden_labels, dev_codes)
    dev_metrics_full = {
        **{name: mult.evaluate_order(dev_hidden, families, order) for name, order in baseline_orders.items()},
        **{name: mult.evaluate_order(dev_hidden, families, order) for name, order in candidate_orders.items()},
    }
    dev_metrics = {name: compact(value) for name, value in dev_metrics_full.items()}
    selected = min(CANDIDATES, key=lambda name: better_candidate(name, dev_metrics))

    dev_best_recovery = max(int(dev_metrics["multiplicity"]["recovered_at_100"]), int(dev_metrics["label_free_persistence"]["recovered_at_100"]))
    dev_best_mrr = max(float(dev_metrics["multiplicity"]["mrr"]), float(dev_metrics["label_free_persistence"]["mrr"]))
    development_authorization = {
        "selected_recovers_at_least_one_more_than_both_v8_baselines": int(dev_metrics[selected]["recovered_at_100"]) >= dev_best_recovery + 1,
        "selected_mrr_at_least_best_v8_baseline": float(dev_metrics[selected]["mrr"]) >= dev_best_mrr,
    }
    validation_opened = all(development_authorization.values())

    validation_metrics: dict[str, dict[str, Any]] | None = None
    full_metrics: dict[str, dict[str, Any]] | None = None
    validation_gates = {
        "validation_panel_opened_only_after_development_authorization": validation_opened,
        "validation_has_at_least_30_qualified_baseline_showers": False,
        "selected_validation_recovery_improves_both_v8_baselines": False,
        "selected_validation_mrr_at_least_best_v8_baseline": False,
    }
    full_result_gates = {
        "selected_full_recovery_at_least_60": False,
        "selected_full_top100_precision_at_least_068": False,
        "selected_full_mrr_at_least_v8_multiplicity": False,
        "exact_v8_full_metrics_reproduced": False,
    }

    if validation_opened:
        val_hidden = masked_labels(hidden_labels, val_codes)
        validation_metrics = {
            "multiplicity": compact(mult.evaluate_order(val_hidden, families, multiplicity_order)),
            "label_free_persistence": compact(mult.evaluate_order(val_hidden, families, persistence_order)),
            selected: compact(mult.evaluate_order(val_hidden, families, candidate_orders[selected])),
        }
        val_best_recovery = max(int(validation_metrics["multiplicity"]["recovered_at_100"]), int(validation_metrics["label_free_persistence"]["recovered_at_100"]))
        val_best_mrr = max(float(validation_metrics["multiplicity"]["mrr"]), float(validation_metrics["label_free_persistence"]["mrr"]))
        validation_gates.update({
            "validation_has_at_least_30_qualified_baseline_showers": min(int(validation_metrics["multiplicity"]["qualified_matches"]), int(validation_metrics["label_free_persistence"]["qualified_matches"])) >= 30,
            "selected_validation_recovery_improves_both_v8_baselines": int(validation_metrics[selected]["recovered_at_100"]) >= val_best_recovery + 1,
            "selected_validation_mrr_at_least_best_v8_baseline": float(validation_metrics[selected]["mrr"]) >= val_best_mrr,
        })

        full_metrics = {
            "multiplicity": compact(mult.evaluate_order(hidden_labels, families, multiplicity_order)),
            "label_free_persistence": compact(mult.evaluate_order(hidden_labels, families, persistence_order)),
            selected: compact(mult.evaluate_order(hidden_labels, families, candidate_orders[selected])),
        }
        exact_baselines = (
            exact_metric_match(full_metrics["multiplicity"], predecessor["metrics"]["multiplicity"])
            and exact_metric_match(full_metrics["label_free_persistence"], predecessor["metrics"]["label_free_persistence"])
        )
        full_result_gates.update({
            "selected_full_recovery_at_least_60": int(full_metrics[selected]["recovered_at_100"]) >= MIN_FULL_RECOVERY,
            "selected_full_top100_precision_at_least_068": float(full_metrics[selected]["top100_dominant_precision"]) >= MIN_FULL_PRECISION,
            "selected_full_mrr_at_least_v8_multiplicity": float(full_metrics[selected]["mrr"]) >= EXPECTED_M_MRR,
            "exact_v8_full_metrics_reproduced": exact_baselines,
        })

    integrity_gates = {
        "frozen_v8_source_predecessor_and_self_tests": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_applied": all(a["score_threshold_applied"] is False for a in scan_audits),
        "exact_v8_family_count_226": len(families) == EXPECTED_FAMILIES,
        "v8_centroid_repair_nonvacuous": int(repair["families_with_duplicate_same_year_components"]) > 0 and int(repair["changed_duplicate_year_centroids"]) > 0,
        "v8_non_centroid_structure_unchanged": repair["non_centroid_family_structure_unchanged"] is True,
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128],
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= 1e-10,
        "candidate_set_exactly_two_and_parameter_free": tuple(candidate_orders) == CANDIDATES,
        "all_rankings_frozen_before_label_evaluation": bool(prelabel_sha) and all(set(order) == set(multiplicity_order) for order in candidate_orders.values()),
        "deterministic_nonempty_label_split": bool(split_sha) and bool(dev_codes) and bool(val_codes),
    }

    passed = (
        all(integrity_gates.values())
        and all(development_authorization.values())
        and all(validation_gates.values())
        and all(full_result_gates.values())
    )
    verdict = "PASS_RANK_CONSENSUS_V10_DEVELOPMENT" if passed else "FAIL_RANK_CONSENSUS_V10_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "family_count_expected": EXPECTED_FAMILIES,
            "family_builder": "exact passed-v8/v6 connected recurrent family graph",
            "centroid_repair": "exact passed-v8 pooled same-year centroid",
            "episode_size": 128,
            "top_k": TOP_K,
            "candidates": list(CANDIDATES),
            "rank_product": "ascending rM*rP; tie rM+rP,rM,rP,id",
            "rank_sum": "ascending rM+rP; tie rM*rP,rM,rP,id",
            "label_split": "SHA256('orbittrace-v10-label-split|'+label) first-byte parity",
            "no_weight_search": True,
            "no_threshold_search": True,
            "no_family_change": True,
            "no_score_change": True,
            "no_candidate_addition_after_execution": True,
        },
        "predecessor": {
            "verdict": predecessor["verdict"],
            "family_count": int(predecessor["family_count"]),
            "multiplicity_recovered_at_100": EXPECTED_M_RECOVERY,
            "persistence_recovered_at_100": EXPECTED_P_RECOVERY,
            "multiplicity_top100_precision": EXPECTED_M_PRECISION,
            "multiplicity_mrr": EXPECTED_M_MRR,
        },
        "retained_quartet_counts": passing_counts,
        "centroid_repair_diagnostics": repair,
        "family_scoring_summary": scoring_summary,
        "prelabel_ranking_sha256": prelabel_sha,
        "label_split_sha256": split_sha,
        "label_split_counts": {"eligible": len(eligible_codes), "development": len(dev_codes), "validation": len(val_codes)},
        "development_metrics": dev_metrics,
        "selected_candidate": selected,
        "development_authorization": development_authorization,
        "validation_opened": validation_opened,
        "validation_metrics": validation_metrics,
        "validation_gates": validation_gates,
        "full_metrics": full_metrics,
        "full_result_gates": full_result_gates,
        "integrity_gates": integrity_gates,
        "claim_boundary": "Development-only rank-consensus test on already-exposed target-excluded GMN 2022-2023. Exact v8 families, pooled centroids, physical scores, and all candidate rankings were frozen before shower-label evaluation. Candidate selection used only the deterministic development-label panel; validation labels were evaluated only if development authorization passed. No OrbitTrace target information or 20-55 degree target-region event entered the method.",
    }
    args.output.joinpath("rank_consensus_v10_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# OrbitTrace rank-consensus v10 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- families: **{len(families)}**",
        f"- eligible shower labels split: **{len(dev_codes)} development / {len(val_codes)} validation**",
        f"- selected fusion candidate: **{selected}**",
        f"- development authorization: **{all(development_authorization.values())}**",
        f"- validation opened: **{validation_opened}**",
    ]
    if validation_metrics is not None and full_metrics is not None:
        md.extend([
            f"- selected validation recovery@100: **{validation_metrics[selected]['recovered_at_100']}**",
            f"- v8 multiplicity / persistence validation recovery@100: **{validation_metrics['multiplicity']['recovered_at_100']} / {validation_metrics['label_free_persistence']['recovered_at_100']}**",
            f"- selected full recovery@100: **{full_metrics[selected]['recovered_at_100']}**",
            f"- selected full top-100 precision: **{full_metrics[selected]['top100_dominant_precision']:.6f}**",
            f"- selected full MRR: **{full_metrics[selected]['mrr']:.6f}**",
        ])
    md.extend(["", "No OrbitTrace target information was accessed."])
    args.output.joinpath("RANK_CONSENSUS_V10_DEVELOPMENT.md").write_text("\n".join(md) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
