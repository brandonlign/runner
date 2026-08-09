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
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
P1_SOURCE_SHA256 = "e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508"
P1_TRANSFER_COMMIT = "785554905113626bebffecdd441616238eb76b04"
P1_TRANSFER_GIT_BLOB = "498daf762bc82a664679998ea751feecff8033de"

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
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metric.items() if key != "per_label"}


def load_lf_checkpoint(path: Path, year: int) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing C1-LF year SHA sidecar {year}")
    require(sidecar.read_text().strip().split()[0] == sha256_bytes(raw), f"C1-LF year SHA mismatch {year}")
    obj = pickle.loads(raw)
    require(obj["format"] == "orbittrace-v6-lf-year-checkpoint-v1", f"wrong v6-LF checkpoint format {year}")
    require(int(obj["year"]) == year, f"wrong v6-LF checkpoint year {year}")
    require(obj["repaired_v6_sha256"] == REPAIRED_V6_SHA256, f"repaired v6 identity changed {year}")
    require(int(obj["audit"]["proposal_cap_per_window"]) == 512, f"proposal cap changed {year}")
    require(int(obj["audit"]["max_primary_proposals_per_year"]) == 36864, f"annual proposal budget changed {year}")
    firewall = obj["firewall"]
    require(firewall["target_interval_remains_excluded"] is True, f"target firewall failed {year}")
    require(firewall["label_values_not_accessed"] is True, f"label value reached year checkpoint {year}")
    require(firewall["all_event_calibration"] is True, f"all-event calibration lost {year}")
    require(firewall["scientific_result_not_evaluated"] is True, f"truth evaluated in year checkpoint {year}")
    return obj


def validate_lf_pass(result: dict[str, Any]) -> None:
    require(result["verdict"] == "PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT", "C1-LF requires v6-LF development PASS")
    configuration = result["configuration"]
    require(configuration["years"] == [2022, 2023], "v6-LF result years changed")
    require(configuration["blind_exclusion"] == [20.0, 55.0], "v6-LF blind exclusion changed")
    require(
        configuration["calibration_reservoir"]
        == "all geometrically valid target-excluded scan events; no shower-label selection",
        "v6-LF calibration reservoir changed",
    )
    require(configuration["parameter_search"] is False, "v6-LF parameter search was enabled")
    require(configuration["null_trimming"] is False, "v6-LF null trimming was enabled")
    require(int(configuration["proposal_cap_per_window"]) == 512, "v6-LF proposal cap changed")
    require(int(configuration["max_primary_proposals_per_year"]) == 36864, "v6-LF annual proposal budget changed")
    require(all(bool(value) for value in result["gates"].values()), "v6-LF did not pass every frozen development gate")
    require(len(str(result["pretruth_sha256"])) == 64, "v6-LF pretruth family hash missing")


def metric_subset(metric: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "qualified_matches",
        "recovered_at_100",
        "top100_dominant_precision",
        "mrr",
        "macro_f1",
        "v3_family_count",
        "rescue_only_family_count",
    )
    require(all(key in metric for key in keys), f"required endpoint missing: {set(keys) - set(metric)}")
    return {key: metric[key] for key in keys}


def require_baseline_reproduction(authoritative: dict[str, Any], reproduced: dict[str, Any]) -> None:
    expected = metric_subset(authoritative)
    got = metric_subset(reproduced)
    for key in ("qualified_matches", "recovered_at_100", "v3_family_count", "rescue_only_family_count"):
        require(int(got[key]) == int(expected[key]), f"C1-LF baseline integer mismatch: {key}")
    require(
        abs(float(got["top100_dominant_precision"]) - float(expected["top100_dominant_precision"])) < 1e-12,
        "C1-LF baseline top100 precision mismatch",
    )
    require(abs(float(got["mrr"]) - float(expected["mrr"])) < 1e-15, "C1-LF baseline MRR mismatch")
    require(abs(float(got["macro_f1"]) - float(expected["macro_f1"])) < 1e-12, "C1-LF baseline macro F1 mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v6-lf-result-json", required=True, type=Path)
    parser.add_argument("--checkpoint-2022", required=True, type=Path)
    parser.add_argument("--checkpoint-2023", required=True, type=Path)
    parser.add_argument("--repaired-v6-source", required=True, type=Path)
    parser.add_argument("--lf-runner", required=True, type=Path)
    parser.add_argument("--base-runner", required=True, type=Path)
    parser.add_argument("--p1-source", required=True, type=Path)
    parser.add_argument("--p1-transfer-runner", required=True, type=Path)
    parser.add_argument("--support-source-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.repaired_v6_source) == REPAIRED_V6_SHA256, "repaired v6 source changed")
    require(sha256_file(args.p1_source) == P1_SOURCE_SHA256, "frozen P1 scientific source changed")

    lf_result = json.loads(args.v6_lf_result_json.read_text())
    validate_lf_pass(lf_result)
    checkpoints = {
        2022: load_lf_checkpoint(args.checkpoint_2022, 2022),
        2023: load_lf_checkpoint(args.checkpoint_2023, 2023),
    }

    v6 = load_module(args.repaired_v6_source, "orbittrace_c1_lf_v6")
    lf = load_module(args.lf_runner, "orbittrace_c1_lf_geometry")
    p1 = load_module(args.p1_source, "orbittrace_c1_lf_p1")
    transfer = load_module(args.p1_transfer_runner, "orbittrace_c1_lf_exact_p1_transfer")
    old = v6.load_base_runner(args.base_runner)
    require(tuple(lf.YEARS) == YEARS, "v6-LF geometry runner years changed")
    require(float(lf.BLIND_EXCLUSION[0]) == 20.0 and float(lf.BLIND_EXCLUSION[1]) == 55.0 if hasattr(lf, "BLIND_EXCLUSION") else True,
            "v6-LF geometry runner blind interval changed")
    require(hasattr(transfer, "apply_exact_p1_membership"), "audited P1 membership engine unavailable")
    require(tuple(transfer.YEARS) == (2023, 2025), "pinned P1 transfer year identity changed")
    transfer.YEARS = YEARS

    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")

    # FIRST DEVELOPMENT DATA ACCESS. This parser is the exact v6-LF geometry-only
    # path and intentionally does not read any shower-label value.
    scan_by_year, calibration_by_year, geometry_audits, pretruth_ids = lf.parse_geometry_only(support, base)
    require(sorted(scan_by_year) == list(YEARS), "C1-LF development year universe changed")
    for year in YEARS:
        require(lf.canonical_sha(scan_by_year[year]) == checkpoints[year]["scan_rows_sha256"],
                f"C1-LF scan rows differ from v6-LF checkpoint {year}")
        require(lf.canonical_sha(calibration_by_year[year]) == checkpoints[year]["calibration_rows_sha256"],
                f"C1-LF calibration rows differ from v6-LF checkpoint {year}")
        require(len(scan_by_year[year]) == len(calibration_by_year[year]), f"all-event calibration count changed {year}")
        require([row["id"] for row in scan_by_year[year]] == [row["id"] for row in calibration_by_year[year]],
                f"all-event calibration ID order changed {year}")
        year_audits = [row for row in geometry_audits if str(row["key"]).startswith(str(year))]
        year_audit_sha = hashlib.sha256(
            json.dumps(year_audits, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        require(year_audit_sha == checkpoints[year]["geometry_audit_sha256"], f"geometry audit changed {year}")
    require(all(row["label_value_accessed"] is False for row in geometry_audits), "label value entered geometry pass")
    require(all(not (BLIND_EXCLUSION[0] <= float(event["sol"]) <= BLIND_EXCLUSION[1])
                for year in YEARS for event in scan_by_year[year]), "target interval entered C1-LF scan")

    all_components = [component for year in YEARS for component in checkpoints[year]["components"]]
    primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
    rescue_families = v6.build_family_track_v6(old, all_components, base, "fixed4_rescue")
    require(primary_families, "no v6-LF primary families reconstructed")

    # Prove the exact v6-LF pretruth family payload is reproduced before changing membership.
    baseline_family_payload = lf.freeze_families(primary_families, rescue_families)
    baseline_family_sha = lf.canonical_sha(baseline_family_payload)
    require(baseline_family_sha == lf_result["pretruth_sha256"], "v6-LF pretruth family identity was not reproduced")

    rank_order = [str(family["family_id"]) for family in primary_families]
    require(len(rank_order) == len(set(rank_order)), "v6-LF primary family IDs are not unique")
    rank_sha = canonical_sha(rank_order)
    seed_sha = canonical_sha(primary_families)

    # Reuse the exact frozen P1/C1 membership engine unchanged. Only the seed/core
    # universe and the year tuple differ from its audited SonotaCo transport use.
    expanded, diagnostics = transfer.apply_exact_p1_membership(p1, primary_families, scan_by_year, base)
    require([str(family["family_id"]) for family in expanded] == rank_order, "C1-LF changed v6-LF primary rank")
    for original, grown in zip(primary_families, expanded):
        require(set(map(str, original["event_ids"])) <= set(map(str, grown["event_ids"])),
                f"C1-LF removed immutable seed from {original['family_id']}")

    membership_payload = {
        "classification": "C1-LF pretruth frozen v6-LF rank and conservative probabilistic membership",
        "years": list(YEARS),
        "blind_exclusion": list(BLIND_EXCLUSION),
        "v6_lf_pretruth_family_sha256": baseline_family_sha,
        "v6_lf_rank_pretruth_sha256": rank_sha,
        "v6_lf_seed_families_pretruth_sha256": seed_sha,
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
            "fixed4_rescue_can_seed_c1_lf": False,
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact v6-LF primary order",
            "calibration_semantics": "all geometrically valid target-excluded events",
            "parameter_search": False,
        },
    }
    membership_sha = canonical_sha(membership_payload)
    (args.output / "c1_lf_membership_pretruth.json").write_text(json.dumps(membership_payload, indent=2, sort_keys=True) + "\n")
    (args.output / "c1_lf_membership_pretruth.sha256").write_text(membership_sha + "\n")

    # FIRST KNOWN-SHOWER LABEL VALUE ACCESS. Exact rank, immutable seeds, expanded
    # memberships, model diagnostics and their SHA-256 are already frozen above.
    hidden_labels, truth_audits = lf.parse_truth_after_freeze(support, pretruth_ids)
    baseline_full = v6.evaluate_families_v6(hidden_labels, primary_families, rescue_families, YEARS)
    c1_full = v6.evaluate_families_v6(hidden_labels, expanded, rescue_families, YEARS)
    baseline = compact(baseline_full)
    c1_metric = compact(c1_full)
    require_baseline_reproduction(lf_result["evaluation"], baseline)

    precision_floor = max(
        ABSOLUTE_PRECISION_FLOOR,
        float(baseline["top100_dominant_precision"]) - PRECISION_REGRESSION_ALLOWANCE,
    )
    gates = {
        "v6_lf_pass_reproduced": True,
        "v6_lf_pretruth_family_identity_reproduced": baseline_family_sha == lf_result["pretruth_sha256"],
        "rank_unchanged": [str(family["family_id"]) for family in expanded] == rank_order,
        "all_original_seeds_preserved": all(
            set(map(str, original["event_ids"])) <= set(map(str, grown["event_ids"]))
            for original, grown in zip(primary_families, expanded)
        ),
        "fixed4_rescue_never_seeded": True,
        "pretruth_membership_frozen_before_truth": len(membership_sha) == 64,
        "geometry_parser_never_accessed_label_values": all(row["label_value_accessed"] is False for row in geometry_audits),
        "truth_event_universe_exact": set(hidden_labels) == pretruth_ids,
        "expansion_nonvacuous": int(diagnostics["assigned_nonseed_events"]) > 0,
        "qualified_no_regression": int(c1_metric["qualified_matches"]) >= int(baseline["qualified_matches"]),
        "recovery100_no_regression": int(c1_metric["recovered_at_100"]) >= int(baseline["recovered_at_100"]),
        "top100_precision_floor": float(c1_metric["top100_dominant_precision"]) >= precision_floor,
        "macro_f1_gain_ge_008": float(c1_metric["macro_f1"]) - float(baseline["macro_f1"]) >= MACRO_F1_GAIN_GATE,
        "mrr_retention_ge_095": float(c1_metric["mrr"]) >= MRR_RETENTION * float(baseline["mrr"]),
    }
    verdict = (
        "PASS_V6_LF_CORE_PROBABILISTIC_MEMBERSHIP_C1_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_V6_LF_CORE_PROBABILISTIC_MEMBERSHIP_C1_NO_GO"
    )
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND_EXCLUSION),
            "calibration_reservoir": "all geometrically valid target-excluded scan events; no shower-label selection",
            "repaired_v6_source_sha256": REPAIRED_V6_SHA256,
            "p1_source_sha256": P1_SOURCE_SHA256,
            "p1_transfer_commit": P1_TRANSFER_COMMIT,
            "p1_transfer_git_blob": P1_TRANSFER_GIT_BLOB,
            "family_count": len(primary_families),
            "fixed4_rescue_can_seed_c1_lf": False,
            "parameter_search": False,
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact v6-LF primary order",
        },
        "v6_lf_pretruth_family_sha256": baseline_family_sha,
        "v6_lf_rank_pretruth_sha256": rank_sha,
        "v6_lf_seed_families_pretruth_sha256": seed_sha,
        "membership_pretruth_sha256": membership_sha,
        "baseline_v6_lf": baseline,
        "c1_lf": c1_metric,
        "gates": gates,
        "diagnostics": diagnostics,
        "truth_audits": truth_audits,
        "precision_floor": precision_floor,
        "claim_boundary": (
            "Fully label-free target-excluded GMN 2022/2023 C1-LF development only. "
            "No literature superiority, held-out generalization, or OrbitTrace recovery claim is established here."
        ),
    }
    (args.output / "v6_lf_core_probabilistic_membership_c1_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "V6_LF_CORE_PROBABILISTIC_MEMBERSHIP_C1_DEVELOPMENT.md").write_text(
        "# OrbitTrace v6-LF-core probabilistic membership C1-LF\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- v6-LF baseline macro F1: **{float(baseline['macro_f1']):.6f}**\n"
        f"- C1-LF macro F1: **{float(c1_metric['macro_f1']):.6f}**\n"
        f"- v6-LF/C1-LF qualified: **{int(baseline['qualified_matches'])} / {int(c1_metric['qualified_matches'])}**\n"
        f"- v6-LF/C1-LF recovery@100: **{int(baseline['recovered_at_100'])} / {int(c1_metric['recovered_at_100'])}**\n"
        f"- v6-LF/C1-LF top100 precision: **{float(baseline['top100_dominant_precision']):.6f} / {float(c1_metric['top100_dominant_precision']):.6f}**\n"
        f"- assigned non-seed events: **{int(diagnostics['assigned_nonseed_events'])}**\n"
        f"- membership pretruth SHA-256: `{membership_sha}`\n"
    )
    print("ORBITTRACE_C1_LF_RESULT_BEGIN")
    print(json.dumps({
        "verdict": verdict,
        "baseline_v6_lf": baseline,
        "c1_lf": c1_metric,
        "gates": gates,
        "diagnostics": {key: value for key, value in diagnostics.items() if key != "family_year_audits"},
    }, indent=2, sort_keys=True))
    print("ORBITTRACE_C1_LF_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
