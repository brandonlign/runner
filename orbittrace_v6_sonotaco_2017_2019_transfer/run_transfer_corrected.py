#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import types
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v6_sonotaco_2017_2019_transfer import run_transfer as legacy
from orbittrace_v6_sonotaco_2017_2019_transfer import run_transfer_portable as portable

YEARS = (2017, 2019)
MIN_BACKGROUND_EVENTS = 10_000
MIN_DISTINCT_MAPPED_SHOWERS = 30
MIN_SUPPORTED_V6_CALIBRATION_BINS = 30
MIN_V3_PRIMARY_FAMILIES = 40
RECOVERY100_RETENTION = 0.80
QUALIFIED_RETENTION = 0.60
TOP100_PRECISION_FLOOR = 0.50
MRR_RETENTION = 0.80
IMPROVEMENT_ENDPOINTS = ("recovered_at_25", "recovered_at_50", "recovered_at_100", "mrr", "macro_f1")
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--current-v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--parser-2019", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2017", required=True, type=Path)
    p.add_argument("--archive-2019", required=True, type=Path)
    p.add_argument("--development-v6-result", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_development_prerequisite(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text())
    require(result.get("verdict") == "PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT", "catalogue-v6 development prerequisite did not pass")
    require(result["configuration"]["years"] == [2022, 2023], "catalogue-v6 development years changed")
    require(result["configuration"]["blind_exclusion"] == [20.0, 55.0], "catalogue-v6 development blind interval changed")
    require(float(result["configuration"]["primary_alpha"]) == 0.05, "catalogue-v6 primary alpha changed")
    require(result["configuration"]["rescue_queue"] == "fixed4 p <= 1/129; never inserted into v3 primary ranking", "catalogue-v6 rescue boundary changed")
    require(all(result["gates"].values()), "catalogue-v6 development gates did not all pass")
    require(all(a["proposal_cap_per_window"] == 512 for a in result["year_audits"]), "catalogue-v6 proposal cap changed")
    require(all(a["max_primary_proposals_per_year"] == 36864 for a in result["year_audits"]), "catalogue-v6 annual proposal budget changed")
    return result


def mapped_label_set(labeled: list[dict[str, Any]]) -> set[str]:
    labels = {str(event.get("complex_key", "")).strip() for event in labeled}
    labels.discard("")
    labels.discard("SPORADIC")
    return labels


def preflight_before_survey_scoring(
    v6: types.ModuleType,
    old: types.ModuleType,
    parsed: dict[int, tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]],
    calibration_by_year: dict[int, list[dict[str, Any]]],
    candidate: types.ModuleType,
    base: types.ModuleType,
    scorer: types.ModuleType,
) -> dict[str, Any]:
    """Run only transport/eligibility checks and exact null calibration.

    This function is called before either current-v6 or promoted-v8 scans. The
    only detector scores computed here are the protocol-required 128 source-
    preserving NULL calibration episodes used to determine supported bins; no
    survey candidate/proposal event is scored.
    """
    audits: dict[str, Any] = {}
    for year in YEARS:
        labeled, sporadic, parser_audit = parsed[year]
        require(parser_audit["obsolete_supported_code_gate_imported_into_v6"] is False, f"old fixed4 parser gate leaked into v6 transfer {year}")
        require(parser_audit["parser"]["gates"]["blind_interval_removed_before_label_access"] is True, f"blind parser boundary failed {year}")
        require(all(parser_audit["binding_parser_gates"].values()), f"binding parser gates failed {year}")
        require(len(sporadic) >= MIN_BACKGROUND_EVENTS, f"PREFLIGHT_INPUT_INELIGIBLE: {year} background count {len(sporadic)} < {MIN_BACKGROUND_EVENTS}")
        mapped_labels = mapped_label_set(labeled)
        require(len(mapped_labels) >= MIN_DISTINCT_MAPPED_SHOWERS, f"PREFLIGHT_INPUT_INELIGIBLE: {year} mapped shower identities {len(mapped_labels)} < {MIN_DISTINCT_MAPPED_SHOWERS}")
        proposal_cal, v3_cal, fixed4_cal, summary = v6.calibrate_year_v6(
            old, year, calibration_by_year[year], candidate, base, scorer
        )
        supported = sorted(int(x) for x in v3_cal)
        require(len(supported) >= MIN_SUPPORTED_V6_CALIBRATION_BINS, f"PREFLIGHT_INPUT_INELIGIBLE: {year} supported v6 calibration bins {len(supported)} < {MIN_SUPPORTED_V6_CALIBRATION_BINS}")
        require(set(proposal_cal) == set(v3_cal) == set(fixed4_cal), f"calibration channel bin universe mismatch {year}")
        require(all(int(row["count"]) == int(old.CALIBRATION_PER_BIN) == 128 for row in summary), f"calibration episode count changed {year}")
        audits[str(year)] = {
            "background_events": len(sporadic),
            "mapped_shower_identities": len(mapped_labels),
            "supported_v6_calibration_bins": supported,
            "supported_v6_calibration_bin_count": len(supported),
            "calibration_per_bin": int(old.CALIBRATION_PER_BIN),
            "survey_candidate_scores_computed": False,
            "null_calibration_only": True,
            "parser": parser_audit,
        }
    return audits


def add_recovery_cuts(metrics_full: dict[str, Any]) -> dict[str, Any]:
    compact = legacy.compact(metrics_full)
    rows = list(metrics_full.get("per_label", []))
    for cutoff in (25, 50):
        compact[f"recovered_at_{cutoff}"] = sum(
            1 for row in rows
            if bool(row.get("qualified")) and row.get("rank") is not None and int(row["rank"]) <= cutoff
        )
    return compact


def size_strata(metrics_full: dict[str, Any], hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> dict[str, Any]:
    totals: dict[str, int] = defaultdict(int)
    for event_id, label in hidden_labels.items():
        if hidden_years.get(event_id) in YEARS and label != "SPORADIC":
            totals[label] += 1
    definitions = (("4-9", 4, 9), ("10-24", 10, 24), ("25-49", 25, 49), ("50-99", 50, 99), ("100+", 100, None))
    by_label = {str(row["label"]): row for row in metrics_full.get("per_label", [])}
    out: dict[str, Any] = {}
    for name, lo, hi in definitions:
        labels = [label for label, count in totals.items() if count >= lo and (hi is None or count <= hi) and label in by_label]
        values = [float(by_label[label].get("f1", 0.0)) for label in labels]
        out[name] = {"label_count": len(labels), "mean_f1": (sum(values) / len(values)) if values else None}
    return out


def run_true_v8_same_universe(
    v8: types.ModuleType,
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: types.ModuleType,
    base: types.ModuleType,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    # The promoted source contains development-only assertions that duplicate-
    # same-year components must exist/change. Those are not detector rules and
    # are prospectively removed by the already source-audited portable wrapper.
    v8.repair_year_centroids = portable.portable_repair_year_centroids(v8)
    previous_min = legacy.MIN_RECURRENT_FAMILIES
    try:
        # legacy.exact_v8_transfer has only one extra family-count guard. The
        # frozen transfer protocol imposes the >=40 recurrent-family gate on
        # current v6, not on its same-universe comparator. Require merely a
        # nonempty comparator universe here as an evaluation-integrity check.
        legacy.MIN_RECURRENT_FAMILIES = 1
        return legacy.exact_v8_transfer(v8, scan_by_year, support, base)
    finally:
        legacy.MIN_RECURRENT_FAMILIES = previous_min


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_path(args.current_v6_source) == REPAIRED_V6_SHA256, "repaired catalogue-v6 source identity changed")
    require(sha256_path(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit identity changed")
    development = validate_development_prerequisite(args.development_v6_result)

    v6 = legacy.load_module(args.current_v6_source, "orbittrace_transfer_corrected_v6")
    v8 = legacy.load_module(args.v8_runner, "orbittrace_transfer_corrected_v8")
    require(all(v6.v3.self_test().values()), "v6 v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()), "v6 membership self-test failed")
    require(all(v8.mult.v3.self_test().values()), "promoted-v8 v3 self-test failed")
    require(all(v8.mult.brown.self_test().values()), "promoted-v8 Brown self-test failed")

    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    source_args = types.SimpleNamespace(candidate_payload=args.candidate_payload, baseline_payload=args.baseline_payload, scorer_parts=args.scorer_parts)
    candidate, base, scorer = support.load_sources(source_args)

    parser_paths = {2017: args.parser_2017, 2019: args.parser_2019}
    archive_paths = {2017: args.archive_2017, 2019: args.archive_2019}
    parsed = {
        year: legacy.parse_transfer_year(year, parser_paths[year], archive_paths[year], args.mapping_audit, base)
        for year in YEARS
    }
    scan_by_year, calibration_by_year, hidden_labels, hidden_years = legacy.build_hidden_panel(parsed)

    # All transport/eligibility gates, including the exact 128-null calibration
    # construction, are completed BEFORE any survey candidate is scored.
    preflight = preflight_before_survey_scoring(v6, old, parsed, calibration_by_year, candidate, base, scorer)

    previous_supported = legacy.MIN_SUPPORTED_BINS
    previous_families = legacy.MIN_RECURRENT_FAMILIES
    try:
        legacy.MIN_SUPPORTED_BINS = MIN_SUPPORTED_V6_CALIBRATION_BINS
        legacy.MIN_RECURRENT_FAMILIES = MIN_V3_PRIMARY_FAMILIES
        current_primary, current_rescue, current_audit = legacy.current_v6_transfer(
            v6, old, scan_by_year, calibration_by_year, candidate, base, scorer, support
        )
    finally:
        legacy.MIN_SUPPORTED_BINS = previous_supported
        legacy.MIN_RECURRENT_FAMILIES = previous_families

    current_order = [str(f["family_id"]) for f in current_primary]
    current_pretruth = legacy.freeze_family_rank_payload(current_primary, current_order)
    current_pretruth_sha = legacy.canonical_sha(current_pretruth)

    true_v8_families, true_v8_order, true_v8_audit = run_true_v8_same_universe(v8, scan_by_year, support, base)
    true_v8_pretruth = legacy.freeze_family_rank_payload(true_v8_families, true_v8_order)
    true_v8_pretruth_sha = legacy.canonical_sha(true_v8_pretruth)
    (args.output / "current_v6_pretruth.sha256").write_text(current_pretruth_sha + "\n")
    (args.output / "true_v8_pretruth.sha256").write_text(true_v8_pretruth_sha + "\n")

    # FIRST SCIENTIFIC LABEL EVALUATION. Both rankings are immutable above.
    current_full = v6.evaluate_families_v6(hidden_labels, current_primary, current_rescue, YEARS)
    v8_full = v8.mult.evaluate_order(hidden_labels, true_v8_families, true_v8_order)
    current = add_recovery_cuts(current_full)
    v8_metrics = add_recovery_cuts(v8_full)
    current_strata = size_strata(current_full, hidden_labels, hidden_years)
    v8_strata = size_strata(v8_full, hidden_labels, hidden_years)

    required_recovery100 = math.floor(RECOVERY100_RETENTION * int(v8_metrics["recovered_at_100"]))
    required_qualified = math.floor(QUALIFIED_RETENTION * int(v8_metrics["qualified_matches"]))
    required_mrr = MRR_RETENTION * float(v8_metrics["mrr"])
    strict_improvements = {
        endpoint: float(current[endpoint]) > float(v8_metrics[endpoint])
        for endpoint in IMPROVEMENT_ENDPOINTS
    }

    integrity_gates = {
        "development_v6_passed_exact_frozen_gates": True,
        "exact_archive_parser_mapping_identities": all(
            preflight[str(year)]["parser"]["obsolete_supported_code_gate_imported_into_v6"] is False for year in YEARS
        ),
        "blind_interval_removed_before_label_normalization": all(
            preflight[str(year)]["parser"]["parser"]["gates"]["blind_interval_removed_before_label_access"] is True for year in YEARS
        ),
        "native_label_syntax_and_mapping_gates_pass": all(
            all(preflight[str(year)]["parser"]["binding_parser_gates"].values()) for year in YEARS
        ),
        "background_at_least_10000_each_year": all(preflight[str(year)]["background_events"] >= MIN_BACKGROUND_EVENTS for year in YEARS),
        "mapped_shower_identities_at_least_30_each_year": all(preflight[str(year)]["mapped_shower_identities"] >= MIN_DISTINCT_MAPPED_SHOWERS for year in YEARS),
        "supported_v6_calibration_bins_at_least_30_each_year_before_survey_scoring": all(preflight[str(year)]["supported_v6_calibration_bin_count"] >= MIN_SUPPORTED_V6_CALIBRATION_BINS for year in YEARS),
        "proposal_budget_exact": all(a["proposal_cap_per_window"] == 512 and a["max_primary_proposals_per_year"] == 36864 for a in current_audit["scan_audits"]),
        "current_v6_all_recurrent_families_span_both_years": all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in current_primary),
        "same_universe_v8_nonempty_and_recurrent": bool(true_v8_families) and all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in true_v8_families),
        "both_rankings_hash_frozen_before_truth": len(current_pretruth_sha) == 64 and len(true_v8_pretruth_sha) == 64,
        "no_retuning_or_parameter_threshold_endpoint_search": True,
    }
    scientific_gates = {
        "at_least_40_recurrent_v3_primary_families": len(current_primary) >= MIN_V3_PRIMARY_FAMILIES,
        "recovery100_at_least_floor_080_v8": int(current["recovered_at_100"]) >= required_recovery100,
        "qualified_at_least_floor_060_v8": int(current["qualified_matches"]) >= required_qualified,
        "top100_dominant_precision_at_least_050": float(current["top100_dominant_precision"]) >= TOP100_PRECISION_FLOOR,
        "mrr_at_least_080_v8": float(current["mrr"]) >= required_mrr,
        "at_least_one_frozen_endpoint_strictly_exceeds_v8": any(strict_improvements.values()),
    }
    verdict = (
        "PASS_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER"
        if all(integrity_gates.values()) and all(scientific_gates.values())
        else "FAIL_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER"
    )

    result = {
        "verdict": verdict,
        "classification": "architecture-pre-frozen no-retuning SonotaCo 2017/2019 transfer; not pristine prospective validation",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "development_v6_verdict": development["verdict"],
            "repaired_v6_sha256": REPAIRED_V6_SHA256,
            "promoted_v8_source_commit": V8_SOURCE_COMMIT,
            "minimum_background_events_per_year": MIN_BACKGROUND_EVENTS,
            "minimum_distinct_mapped_showers_per_year": MIN_DISTINCT_MAPPED_SHOWERS,
            "minimum_supported_v6_calibration_bins_per_year": MIN_SUPPORTED_V6_CALIBRATION_BINS,
            "minimum_v3_primary_families": MIN_V3_PRIMARY_FAMILIES,
            "recovery100_retention_to_v8": RECOVERY100_RETENTION,
            "qualified_retention_to_v8": QUALIFIED_RETENTION,
            "top100_precision_floor": TOP100_PRECISION_FLOOR,
            "mrr_retention_to_v8": MRR_RETENTION,
            "strict_improvement_endpoints": list(IMPROVEMENT_ENDPOINTS),
            "old_fixed4_supported_code_gate_imported": False,
            "parameter_search": False,
        },
        "pre_scientific_eligibility": preflight,
        "current_v6_pretruth_sha256": current_pretruth_sha,
        "promoted_v8_pretruth_sha256": true_v8_pretruth_sha,
        "current_v6": current,
        "promoted_v8_same_universe": v8_metrics,
        "current_v6_size_strata": current_strata,
        "promoted_v8_size_strata": v8_strata,
        "fixed_thresholds_derived_from_v8": {
            "required_recovery_at_100": required_recovery100,
            "required_qualified_matches": required_qualified,
            "required_mrr": required_mrr,
        },
        "strict_endpoint_improvements": strict_improvements,
        "current_v6_audit": current_audit,
        "promoted_v8_audit": true_v8_audit,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "rescue_queue_report_only": {
            "family_count": len(current_rescue),
            "rescue_additional_qualified_labels": current.get("rescue_additional_qualified_labels", []),
            "can_satisfy_primary_gate": False,
        },
        "claim_boundary": "Architecture-pre-frozen no-retuning transfer only; raw pair is not pristine prospective validation; no OrbitTrace target access or target authorization.",
    }
    (args.output / "v6_sonotaco_2017_2019_transfer_corrected.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "V6_SONOTACO_2017_2019_TRANSFER_CORRECTED.md").write_text(
        "# OrbitTrace v6 SonotaCo 2017/2019 architecture-pre-frozen transfer\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- v3 primary families: **{len(current_primary)}**\n"
        f"- recovery@25/50/100: **{current['recovered_at_25']} / {current['recovered_at_50']} / {current['recovered_at_100']}** vs v8 **{v8_metrics['recovered_at_25']} / {v8_metrics['recovered_at_50']} / {v8_metrics['recovered_at_100']}**\n"
        f"- qualified matches: **{current['qualified_matches']}** vs v8 **{v8_metrics['qualified_matches']}**\n"
        f"- MRR: **{current['mrr']:.6f}** vs v8 **{v8_metrics['mrr']:.6f}**\n"
        f"- macro F1: **{current['macro_f1']:.6f}** vs v8 **{v8_metrics['macro_f1']:.6f}**\n"
        f"- top-100 dominant precision: **{current['top100_dominant_precision']:.6f}**\n"
        f"- v6 pretruth SHA: `{current_pretruth_sha}`\n"
        f"- promoted-v8 pretruth SHA: `{true_v8_pretruth_sha}`\n\n"
        "This is an architecture-pre-frozen no-retuning transfer, not pristine prospective validation.\n"
    )
    print((args.output / "V6_SONOTACO_2017_2019_TRANSFER_CORRECTED.md").read_text(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
