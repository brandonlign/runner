#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

YEARS = (2022, 2023)
BLIND_EXCLUSION = (20.0, 55.0)
FROZEN_V6_SHA256 = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
P1_SOURCE_SHA256 = "e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508"
P1_TRANSFER_COMMIT = "785554905113626bebffecdd441616238eb76b04"
P1_TRANSFER_GIT_BLOB = "498daf762bc82a664679998ea751feecff8033de"
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"

MACRO_F1_GAIN_GATE = 0.08
MRR_RETENTION = 0.95
ABSOLUTE_PRECISION_FLOOR = 0.65
PRECISION_REGRESSION_ALLOWANCE = 0.02


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def normalized_event_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "id": str(e["id"]),
        "year": int(e["year"]),
        "sol": float(e["sol"]),
        "sun_lon": float(e["sun_lon"]),
        "ecl_lat": float(e["ecl_lat"]),
        "vg": float(e["vg"]),
        "iau": int(e.get("iau", 0)),
        "complex_key": str(e.get("complex_key", "")),
    } for e in rows]


def event_rows_sha256(rows: list[dict[str, Any]]) -> str:
    return canonical_sha(normalized_event_rows(rows))


def load_year_checkpoint(path: Path, year: int) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing year checkpoint SHA {year}")
    require(sidecar.read_text().strip().split()[0] == sha256_bytes(raw), f"year checkpoint SHA mismatch {year}")
    obj = pickle.loads(raw)
    require(obj["format"] == "orbittrace-v6-development-year-checkpoint-v1", f"wrong checkpoint format {year}")
    require(int(obj["year"]) == year, f"wrong checkpoint year {year}")
    require(obj["frozen_v6_sha256"] == FROZEN_V6_SHA256, f"frozen v6 identity changed {year}")
    require(obj["repaired_v6_sha256"] == REPAIRED_V6_SHA256, f"repaired v6 identity changed {year}")
    require(obj["audit"]["proposal_cap_per_window"] == 512, f"proposal cap changed {year}")
    require(obj["audit"]["max_primary_proposals_per_year"] == 36864, f"annual proposal budget changed {year}")
    require(obj["firewall"]["target_interval_remains_excluded"] is True, f"target firewall failed {year}")
    require(obj["firewall"]["hidden_labels_not_saved"] is True, f"labels saved in checkpoint {year}")
    require(obj["firewall"]["scientific_result_not_evaluated_in_year_job"] is True, f"truth evaluated in checkpoint {year}")
    return obj


def validate_v6_pass_without_reading_evaluation(result: dict[str, Any]) -> None:
    require(result["verdict"] == "PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT", "C1 requires v6 development PASS")
    require(result["configuration"]["years"] == [2022, 2023], "v6 result years changed")
    require(result["configuration"]["blind_exclusion"] == [20.0, 55.0], "v6 blind exclusion changed")
    require(all(result["gates"].values()), "v6 result did not pass every frozen gate")
    require(all(a["proposal_cap_per_window"] == 512 for a in result["year_audits"]), "v6 result proposal cap changed")
    require(all(a["max_primary_proposals_per_year"] == 36864 for a in result["year_audits"]), "v6 result annual budget changed")


def metric_subset(metric: dict[str, Any]) -> dict[str, Any]:
    keys = ("qualified_matches", "recovered_at_100", "top100_dominant_precision", "mrr", "macro_f1")
    require(all(k in metric for k in keys), f"required endpoint missing: {set(keys)-set(metric)}")
    return {k: metric[k] for k in keys}


def require_baseline_reproduction(authoritative: dict[str, Any], reproduced: dict[str, Any]) -> None:
    expected = metric_subset(authoritative)
    got = metric_subset(reproduced)
    require(int(got["qualified_matches"]) == int(expected["qualified_matches"]), "C1 baseline qualified mismatch")
    require(int(got["recovered_at_100"]) == int(expected["recovered_at_100"]), "C1 baseline recovery@100 mismatch")
    require(abs(float(got["top100_dominant_precision"]) - float(expected["top100_dominant_precision"])) < 1e-12,
            "C1 baseline top100 precision mismatch")
    require(abs(float(got["mrr"]) - float(expected["mrr"])) < 1e-15, "C1 baseline MRR mismatch")
    require(abs(float(got["macro_f1"]) - float(expected["macro_f1"])) < 1e-12, "C1 baseline macro F1 mismatch")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--checkpoint-2022", required=True, type=Path)
    p.add_argument("--checkpoint-2023", required=True, type=Path)
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--p1-source", required=True, type=Path)
    p.add_argument("--p1-transfer-runner", required=True, type=Path)
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.v6_source) == REPAIRED_V6_SHA256, "repaired v6 source changed")
    require(sha256_file(args.p1_source) == P1_SOURCE_SHA256, "frozen P1 source changed")

    v6_result = json.loads(args.v6_result_json.read_text())
    validate_v6_pass_without_reading_evaluation(v6_result)
    checkpoints = {
        2022: load_year_checkpoint(args.checkpoint_2022, 2022),
        2023: load_year_checkpoint(args.checkpoint_2023, 2023),
    }

    v6 = load_module(args.v6_source, "orbittrace_c1_v6")
    old = load_module(args.base_runner, "orbittrace_c1_base")
    p1 = load_module(args.p1_source, "orbittrace_c1_p1")
    transfer = load_module(args.p1_transfer_runner, "orbittrace_c1_exact_p1_transfer")
    v8 = load_module(args.v8_runner, "orbittrace_c1_exact_v8")
    require(getattr(v8, "YEARS", None) == YEARS, "exact evaluator years changed")
    require(hasattr(v8, "mult") and hasattr(v8.mult, "evaluate_order"), "exact inherited evaluator unavailable")
    require(hasattr(transfer, "apply_exact_p1_membership"), "audited P1 membership engine unavailable")
    require(tuple(transfer.YEARS) == (2023, 2025), "pinned P1 transfer source year identity changed")
    transfer.YEARS = YEARS

    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)

    # FIRST DEVELOPMENT DATA ACCESS. The inherited frozen parser excludes 20-55.
    scan_by_year, calibration_by_year, hidden_labels, _sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "C1 development year universe changed")
    require(all(not (BLIND_EXCLUSION[0] <= float(e["sol"]) <= BLIND_EXCLUSION[1])
                for year in YEARS for e in scan_by_year[year]), "target interval entered C1 scan")
    for year in YEARS:
        require(event_rows_sha256(scan_by_year[year]) == checkpoints[year]["scan_rows_sha256"],
                f"C1 scan rows differ from v6 checkpoint {year}")
        require(event_rows_sha256(calibration_by_year[year]) == checkpoints[year]["calibration_rows_sha256"],
                f"C1 calibration rows differ from v6 checkpoint {year}")

    all_components = [component for year in YEARS for component in checkpoints[year]["components"]]
    primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
    require(primary_families, "no v6 primary families reconstructed")
    rank_order = [str(f["family_id"]) for f in primary_families]
    require(len(rank_order) == len(set(rank_order)), "v6 primary family IDs are not unique")
    rank_sha = canonical_sha(rank_order)
    seed_sha = canonical_sha(primary_families)

    # The exact P1 membership code is reused unchanged; only the seed/core universe
    # and year tuple are supplied by C1.
    expanded, diagnostics = transfer.apply_exact_p1_membership(p1, primary_families, scan_by_year, base)
    require([str(f["family_id"]) for f in expanded] == rank_order, "C1 changed v6 primary rank")
    require(all(set(map(str, primary_families[i]["event_ids"])) <= set(map(str, expanded[i]["event_ids"]))
                for i in range(len(primary_families))), "C1 removed a v6 seed")

    membership_payload = {
        "classification": "C1 pretruth frozen v6 rank and probabilistic membership",
        "years": list(YEARS),
        "blind_exclusion": list(BLIND_EXCLUSION),
        "v6_rank_pretruth_sha256": rank_sha,
        "v6_seed_families_pretruth_sha256": seed_sha,
        "rank_order": rank_order,
        "expanded_families": expanded,
        "diagnostics": diagnostics,
        "membership_engine": {
            "source_commit": P1_TRANSFER_COMMIT,
            "git_blob": P1_TRANSFER_GIT_BLOB,
            "function": "apply_exact_p1_membership",
            "p1_scientific_source_sha256": P1_SOURCE_SHA256,
            "year_tuple_override_only": [2022, 2023],
        },
        "configuration": {
            "inner_prob": float(p1.INNER_PROB),
            "outer_prob": float(p1.OUTER_PROB),
            "background_upper_confidence": float(p1.BACKGROUND_UPPER_CONFIDENCE),
            "responsibility_threshold": float(p1.MAP_THRESHOLD),
            "fixed4_rescue_can_seed_c1": False,
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact v6 primary order",
            "parameter_search": False,
        },
    }
    membership_sha = canonical_sha(membership_payload)
    (args.output / "c1_membership_pretruth.json").write_text(json.dumps(membership_payload, indent=2, sort_keys=True) + "\n")
    (args.output / "c1_membership_pretruth.sha256").write_text(membership_sha + "\n")

    # FIRST KNOWN-SHOWER LABEL USE. Both v6 rank and C1 membership are frozen above.
    baseline_full = v8.mult.evaluate_order(hidden_labels, primary_families, rank_order)
    c1_full = v8.mult.evaluate_order(hidden_labels, expanded, rank_order)
    baseline = compact(baseline_full)
    c1_metric = compact(c1_full)

    # Empirical evaluator-integrity proof: inherited evaluator must reproduce the
    # authoritative repaired-v6 endpoints before C1 can receive a scientific verdict.
    require_baseline_reproduction(v6_result["evaluation"], baseline)

    precision_floor = max(
        ABSOLUTE_PRECISION_FLOOR,
        float(baseline["top100_dominant_precision"]) - PRECISION_REGRESSION_ALLOWANCE,
    )
    gates = {
        "v6_baseline_reproduced": True,
        "expansion_nonvacuous": int(diagnostics["assigned_nonseed_events"]) > 0,
        "qualified_no_regression": int(c1_metric["qualified_matches"]) >= int(baseline["qualified_matches"]),
        "recovery100_no_regression": int(c1_metric["recovered_at_100"]) >= int(baseline["recovered_at_100"]),
        "top100_precision_floor": float(c1_metric["top100_dominant_precision"]) >= precision_floor,
        "macro_f1_gain_ge_008": float(c1_metric["macro_f1"]) - float(baseline["macro_f1"]) >= MACRO_F1_GAIN_GATE,
        "mrr_retention_ge_095": float(c1_metric["mrr"]) >= MRR_RETENTION * float(baseline["mrr"]),
    }
    verdict = (
        "PASS_V6_CORE_PROBABILISTIC_MEMBERSHIP_C1_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_V6_CORE_PROBABILISTIC_MEMBERSHIP_C1_NO_GO"
    )
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND_EXCLUSION),
            "v6_source_sha256": REPAIRED_V6_SHA256,
            "p1_source_sha256": P1_SOURCE_SHA256,
            "p1_transfer_commit": P1_TRANSFER_COMMIT,
            "p1_transfer_git_blob": P1_TRANSFER_GIT_BLOB,
            "v8_source_commit": V8_SOURCE_COMMIT,
            "family_count": len(primary_families),
            "fixed4_rescue_can_seed_c1": False,
            "parameter_search": False,
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact v6 primary order",
        },
        "v6_rank_pretruth_sha256": rank_sha,
        "v6_seed_families_pretruth_sha256": seed_sha,
        "membership_pretruth_sha256": membership_sha,
        "baseline_v6": baseline,
        "c1": c1_metric,
        "gates": gates,
        "diagnostics": diagnostics,
        "precision_floor": precision_floor,
        "claim_boundary": (
            "Target-excluded GMN 2022/2023 C1 development only. "
            "No Sugar/HDBSCAN superiority, external validation, or target access is established here."
        ),
    }
    (args.output / "v6_core_probabilistic_membership_c1_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "V6_CORE_PROBABILISTIC_MEMBERSHIP_C1_DEVELOPMENT.md").write_text(
        "# OrbitTrace v6-core probabilistic membership C1\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- v6 baseline macro F1: **{float(baseline['macro_f1']):.6f}**\n"
        f"- C1 macro F1: **{float(c1_metric['macro_f1']):.6f}**\n"
        f"- v6/C1 qualified: **{int(baseline['qualified_matches'])} / {int(c1_metric['qualified_matches'])}**\n"
        f"- v6/C1 recovery@100: **{int(baseline['recovered_at_100'])} / {int(c1_metric['recovered_at_100'])}**\n"
        f"- v6/C1 top100 precision: **{float(baseline['top100_dominant_precision']):.6f} / {float(c1_metric['top100_dominant_precision']):.6f}**\n"
        f"- assigned non-seed events: **{int(diagnostics['assigned_nonseed_events'])}**\n"
        f"- contested proposal events: **{int(diagnostics['conflicted_proposal_events'])}**\n"
    )
    print("ORBITTRACE_C1_RESULT_BEGIN")
    print(json.dumps({
        "verdict": verdict,
        "baseline_v6": baseline,
        "c1": c1_metric,
        "gates": gates,
        "diagnostics": {k: v for k, v in diagnostics.items() if k != "family_year_audits"},
    }, indent=2, sort_keys=True))
    print("ORBITTRACE_C1_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
