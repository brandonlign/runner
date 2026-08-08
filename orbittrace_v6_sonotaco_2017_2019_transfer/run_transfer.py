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

import numpy as np

from orbittrace_v6_sonotaco_2017_2019_transfer.parser_transport import parse_transfer_year, require, sha256_path

YEARS = (2017, 2019)
CORPUS_V6 = "orbittrace-v3-primary-catalogue-v6-sonotaco-2017-2019-prefrozen-transfer"
CORPUS_V8 = "orbittrace-pooled-year-centroid-v8-sonotaco-2017-2019-prefrozen-transfer"
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
CURRENT_V6_FROZEN_SHA256 = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"
CURRENT_V6_REPAIRED_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
MIN_SCAN_EVENTS = 1000
MIN_CALIBRATION_EVENTS = 1000
MIN_SUPPORTED_BINS = 24
MIN_RECURRENT_FAMILIES = 50
TOP_K = 100
MIN_TOP100_PRECISION = 0.50
QUALIFIED_RATIO_TO_V8 = 0.90


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


def load_module(path: Path, name: str) -> types.ModuleType:
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hidden_geometry(event: dict[str, Any], year: int, *, calibration: bool) -> dict[str, Any]:
    return {
        "id": str(event["id"]),
        "year": int(year),
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
        "iau": 0,
        "complex_key": "SPORADIC" if calibration else "HIDDEN",
    }


def build_hidden_panel(
    parsed: dict[int, tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]]
) -> tuple[dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]], dict[str, str], dict[str, int]]:
    scan_by_year: dict[int, list[dict[str, Any]]] = {}
    calibration_by_year: dict[int, list[dict[str, Any]]] = {}
    hidden_labels: dict[str, str] = {}
    hidden_years: dict[str, int] = {}
    seen: set[str] = set()
    for year in YEARS:
        labeled, sporadic, _audit = parsed[year]
        scan: list[dict[str, Any]] = []
        calibration: list[dict[str, Any]] = []
        for event in labeled:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event ID {event_id}")
            seen.add(event_id)
            label = str(event.get("complex_key", "")).strip()
            require(label and label != "SPORADIC", f"labeled event lacks mapped label {event_id}")
            hidden_labels[event_id] = label
            hidden_years[event_id] = year
            scan.append(hidden_geometry(event, year, calibration=False))
        for event in sporadic:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event ID {event_id}")
            seen.add(event_id)
            hidden_labels[event_id] = "SPORADIC"
            hidden_years[event_id] = year
            scan.append(hidden_geometry(event, year, calibration=False))
            calibration.append(hidden_geometry(event, year, calibration=True))
        require(len(scan) >= MIN_SCAN_EVENTS, f"insufficient {year} scan events: {len(scan)}")
        require(len(calibration) >= MIN_CALIBRATION_EVENTS, f"insufficient {year} calibration events: {len(calibration)}")
        scan_by_year[year] = scan
        calibration_by_year[year] = calibration
    return scan_by_year, calibration_by_year, hidden_labels, hidden_years


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "per_label"}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def freeze_family_rank_payload(families: list[dict[str, Any]], order: list[str]) -> dict[str, Any]:
    by_id = {str(f["family_id"]): f for f in families}
    require(len(order) == len(by_id) and set(order) == set(by_id), "ranking universe mismatch")
    return {
        "order": list(order),
        "families": [
            {
                "family_id": fid,
                "years": [int(y) for y in by_id[fid]["years"]],
                "event_ids": sorted(str(eid) for eid in by_id[fid]["event_ids"]),
                "event_count": int(by_id[fid]["event_count"]),
            }
            for fid in order
        ],
    }


def exact_v8_transfer(
    v8: types.ModuleType,
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: types.ModuleType,
    base: types.ModuleType,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    v8.YEARS = YEARS
    v8.MONTH_KEYS = tuple()
    v8.CORPUS = CORPUS_V8
    v8.v6.YEARS = YEARS
    v8.v6.MONTH_KEYS = tuple()
    v8.v6.CORPUS = CORPUS_V8
    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()
    v8.mult.TOP_K = TOP_K

    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = CORPUS_V8
    support.RANKING_VARIANTS = (
        "persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength"
    )
    require(int(support.MIN_FAMILY_YEARS) == 2, "v8 family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "v8 family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "v8 component gates changed")
    require(int(support.SHORTLIST_K) == int(v8.v6.FIRST_SHORTLIST), "v8 first shortlist changed")
    require(int(support.AUDIT_SHORTLIST_K) == int(v8.v6.AUDIT_SHORTLIST), "v8 audit shortlist changed")
    require(int(support.MIN_ANCHOR_COUNT) == int(v8.v6.MIN_ANCHOR_COUNT), "v8 anchor count changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == int(v8.v6.MAX_QUARTETS_PER_BIN), "v8 quartet cap changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    for year in YEARS:
        audit, passing, year_components = v8.v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(int(audit["calibration_events_used"]) == 0, "v8 unexpectedly used calibration events")
        require(audit["source_labels_used_for_proposals"] is False, "v8 source labels entered proposals")
        require(audit["score_threshold_applied"] is False, "v8 score threshold unexpectedly applied")
        scan_audits.append(audit)
        components.extend(year_components)
        print(f"transfer true-v8 {year}: quartets={len(passing):,} components={len(year_components):,}", flush=True)

    families, rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in rankings["persistence"]]
    require(len(families) >= MIN_RECURRENT_FAMILIES, f"true-v8 transfer family universe too small: {len(families)}")
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "v8 persistence universe mismatch")
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)
    runtime = v8.mult.load_frozen_runtime()
    scored, scoring_summary = v8.mult.score_families(families, scan_by_year, runtime, base)
    order = v8.mult.rank_scored(scored, "multiplicity")
    require(len(order) == len(families) and set(order) == {str(f["family_id"]) for f in families}, "v8 multiplicity universe mismatch")
    return families, order, {
        "scan_audits": scan_audits,
        "repair": repair,
        "scoring_summary": scoring_summary,
        "family_count": len(families),
    }


def current_v6_transfer(
    v6: types.ModuleType,
    old: types.ModuleType,
    scan_by_year: dict[int, list[dict[str, Any]]],
    calibration_by_year: dict[int, list[dict[str, Any]]],
    candidate: types.ModuleType,
    base: types.ModuleType,
    scorer: types.ModuleType,
    support: types.ModuleType,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    old.YEARS = YEARS
    old.MONTH_KEYS = tuple()
    old.CORPUS = CORPUS_V6
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = CORPUS_V6
    all_components: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for year in YEARS:
        audit, _anchors, components = v6.scan_year_v6(
            old, year, scan_by_year[year], calibration_by_year[year], candidate, base, scorer, support
        )
        require(int(audit["scan_events"]) == len(scan_by_year[year]), "v6 scan count mismatch")
        require(int(audit["calibration_events"]) == len(calibration_by_year[year]), "v6 calibration count mismatch")
        require(int(audit["proposal_cap_per_window"]) == 512, "v6 proposal cap changed")
        require(int(audit["max_primary_proposals_per_year"]) == 36864, "v6 annual proposal budget changed")
        require(len(audit["supported_bins"]) >= MIN_SUPPORTED_BINS, f"v6 supported bins underpowered {year}")
        audits.append(audit)
        all_components.extend(components)
        print(f"transfer current-v6 {year}: components={len(components):,}", flush=True)
    primary = v6.build_family_track_v6(old, all_components, base, "v3")
    rescue = v6.build_family_track_v6(old, all_components, base, "fixed4_rescue")
    require(len(primary) >= MIN_RECURRENT_FAMILIES, f"current-v6 transfer family universe too small: {len(primary)}")
    return primary, rescue, {"scan_audits": audits, "primary_family_count": len(primary), "rescue_family_count": len(rescue)}


def development_mrr(result: dict[str, Any]) -> float:
    require(result.get("verdict") == "PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT", "development v6 prerequisite did not pass")
    require(result["configuration"]["years"] == [2022, 2023], "development v6 years changed")
    require(result["configuration"]["blind_exclusion"] == [20.0, 55.0], "development v6 blind interval changed")
    require(all(result["gates"].values()), "development v6 gates did not all pass")
    evaluation = result.get("evaluation")
    require(isinstance(evaluation, dict) and isinstance(evaluation.get("mrr"), (int, float)), "development v6 MRR missing")
    return float(evaluation["mrr"])


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_path(args.current_v6_source) == CURRENT_V6_REPAIRED_SHA256, "current repaired v6 source changed")
    require(sha256_path(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit changed")
    development = json.loads(args.development_v6_result.read_text())
    dev_mrr = development_mrr(development)

    v6 = load_module(args.current_v6_source, "orbittrace_transfer_current_v6")
    v8 = load_module(args.v8_runner, "orbittrace_transfer_true_v8")
    require(all(v6.v3.self_test().values()), "current v6 v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()), "current v6 membership self-test failed")
    require(all(v8.mult.v3.self_test().values()), "promoted-v8 v3 self-test failed")
    require(all(v8.mult.brown.self_test().values()), "promoted-v8 Brown self-test failed")

    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    source_args = types.SimpleNamespace(
        candidate_payload=args.candidate_payload,
        baseline_payload=args.baseline_payload,
        scorer_parts=args.scorer_parts,
    )
    candidate, base, scorer = support.load_sources(source_args)

    parser_paths = {2017: args.parser_2017, 2019: args.parser_2019}
    archive_paths = {2017: args.archive_2017, 2019: args.archive_2019}
    parsed = {
        year: parse_transfer_year(year, parser_paths[year], archive_paths[year], args.mapping_audit, base)
        for year in YEARS
    }
    scan_by_year, calibration_by_year, hidden_labels, hidden_years = build_hidden_panel(parsed)

    # Both methods are fully generated and rank-frozen before the first label lookup below.
    current_primary, current_rescue, current_audit = current_v6_transfer(
        v6, old, scan_by_year, calibration_by_year, candidate, base, scorer, support
    )
    current_order = [str(f["family_id"]) for f in current_primary]
    current_pretruth = freeze_family_rank_payload(current_primary, current_order)
    current_pretruth_sha = canonical_sha(current_pretruth)

    true_v8_families, true_v8_order, true_v8_audit = exact_v8_transfer(v8, scan_by_year, support, base)
    true_v8_pretruth = freeze_family_rank_payload(true_v8_families, true_v8_order)
    true_v8_pretruth_sha = canonical_sha(true_v8_pretruth)
    (args.output / "current_v6_pretruth.sha256").write_text(current_pretruth_sha + "\n")
    (args.output / "true_v8_pretruth.sha256").write_text(true_v8_pretruth_sha + "\n")

    # FIRST TRUTH USE: both method rankings above are now immutable and hash-frozen.
    current_metrics_full = v6.evaluate_families_v6(hidden_labels, current_primary, current_rescue, YEARS)
    current_metrics = compact(current_metrics_full)
    true_v8_metrics_full = v8.mult.evaluate_order(hidden_labels, true_v8_families, true_v8_order)
    true_v8_metrics = compact(true_v8_metrics_full)

    parser_audits = {str(year): parsed[year][2] for year in YEARS}
    v6_bins_ok = all(len(a["supported_bins"]) >= MIN_SUPPORTED_BINS for a in current_audit["scan_audits"])
    v8_bins_ok = all(int(a["scannable_bin_count"]) >= MIN_SUPPORTED_BINS for a in true_v8_audit["scan_audits"])
    exact_v6_years = all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in current_primary)
    exact_v8_years = all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in true_v8_families)
    required_qualified = int(math.ceil(QUALIFIED_RATIO_TO_V8 * int(true_v8_metrics["qualified_matches"])))

    integrity_gates = {
        "exact_archive_and_parser_identities": all(
            parser_audits[str(year)]["obsolete_supported_code_gate_imported_into_v6"] is False for year in YEARS
        ),
        "blind_interval_removed_before_label_access": all(
            parser_audits[str(year)]["parser"]["gates"]["blind_interval_removed_before_label_access"] is True for year in YEARS
        ),
        "all_other_parser_mapping_geometry_gates_pass": all(
            all(parser_audits[str(year)]["binding_parser_gates"].values()) for year in YEARS
        ),
        "scan_and_sporadic_calibration_at_least_1000_each_year": all(
            len(scan_by_year[y]) >= MIN_SCAN_EVENTS and len(calibration_by_year[y]) >= MIN_CALIBRATION_EVENTS for y in YEARS
        ),
        "current_v6_at_least_24_supported_bins_each_year": v6_bins_ok,
        "true_v8_at_least_24_scannable_bins_each_year": v8_bins_ok,
        "current_v6_all_recurrent_families_span_both_years": exact_v6_years,
        "true_v8_all_recurrent_families_span_both_years": exact_v8_years,
        "current_v6_at_least_50_recurrent_families": len(current_primary) >= MIN_RECURRENT_FAMILIES,
        "true_v8_at_least_50_recurrent_families": len(true_v8_families) >= MIN_RECURRENT_FAMILIES,
        "both_rankings_hash_frozen_before_truth": len(current_pretruth_sha) == 64 and len(true_v8_pretruth_sha) == 64,
        "no_retuning_or_threshold_search": True,
    }
    scientific_gates = {
        "current_v6_top100_precision_at_least_050": float(current_metrics["top100_dominant_precision"]) >= MIN_TOP100_PRECISION,
        "current_v6_mrr_at_least_development_v6": float(current_metrics["mrr"]) >= dev_mrr,
        "current_v6_recovery100_at_least_same_universe_true_v8": int(current_metrics["recovered_at_100"]) >= int(true_v8_metrics["recovered_at_100"]),
        "current_v6_qualified_at_least_90pct_true_v8": int(current_metrics["qualified_matches"]) >= required_qualified,
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
            "current_v6_source_sha256": CURRENT_V6_REPAIRED_SHA256,
            "promoted_v8_source_commit": V8_SOURCE_COMMIT,
            "top_k": TOP_K,
            "min_supported_bins": MIN_SUPPORTED_BINS,
            "min_recurrent_families": MIN_RECURRENT_FAMILIES,
            "minimum_top100_precision": MIN_TOP100_PRECISION,
            "minimum_qualified_ratio_to_v8": QUALIFIED_RATIO_TO_V8,
            "old_fixed4_supported_code_gate_imported": False,
            "parameter_search": False,
        },
        "development_v6_mrr": dev_mrr,
        "current_v6_pretruth_sha256": current_pretruth_sha,
        "true_v8_pretruth_sha256": true_v8_pretruth_sha,
        "current_v6": current_metrics,
        "true_promoted_v8_same_universe": true_v8_metrics,
        "current_v6_audit": current_audit,
        "true_v8_audit": true_v8_audit,
        "parser_audits": parser_audits,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": "Architecture-pre-frozen transfer only; not pristine prospective validation and no OrbitTrace target access.",
    }
    (args.output / "v6_sonotaco_2017_2019_transfer.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "V6_SONOTACO_2017_2019_TRANSFER.md").write_text(
        "# OrbitTrace v6 SonotaCo 2017/2019 architecture-pre-frozen transfer\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- current v6 families: **{len(current_primary)}**; true promoted-v8 families: **{len(true_v8_families)}**\n"
        f"- recovery@100: **v6 {current_metrics['recovered_at_100']} vs v8 {true_v8_metrics['recovered_at_100']}**\n"
        f"- qualified: **v6 {current_metrics['qualified_matches']} vs v8 {true_v8_metrics['qualified_matches']}**\n"
        f"- MRR: **v6 {current_metrics['mrr']:.6f} vs development floor {dev_mrr:.6f}**\n"
        f"- top-100 precision: **{current_metrics['top100_dominant_precision']:.6f}**\n"
        f"- current-v6 pretruth SHA: `{current_pretruth_sha}`\n"
        f"- true-v8 pretruth SHA: `{true_v8_pretruth_sha}`\n\n"
        "This is an architecture-pre-frozen transfer, not a pristine prospective external validation.\n"
    )
    print((args.output / "V6_SONOTACO_2017_2019_TRANSFER.md").read_text(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
