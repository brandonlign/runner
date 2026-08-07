#!/usr/bin/env python3
"""Run the preregistered target-excluded v8 literature benchmark on SonotaCo 2023+2025.

This file transports the exact frozen v8 family/scoring machinery to two already-audited
SonotaCo years. Labels are retained outside the scanner and first used only after all
families, pooled centroids, scores, and rankings are frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_pooled_year_centroid_v8 import run_development as v8

YEARS = (2023, 2025)
CORPUS = "sonotaco-2023-2025-v8-literature-matched"
RAW_FIXED4_RANKING_VARIANTS = (
    "persistence",
    "mean_year_strength",
    "sqrt_support_strength",
    "min_year_strength",
    "size_penalized_strength",
)
V8_SOURCE_SHA = "f248df78e1258b132b41aecca6a985a5eb782654"
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
RUNTIME_SOURCE_SHA256 = "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51"
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
ARCHIVE_SHA256 = {
    2023: "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430",
    2025: "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52",
}
EXPECTED_MEMBERS = {
    2023: "023a/_U2_20230101_S.csv",
    2025: "025a/_U2_20250101_S.csv",
}
DEVELOPMENT_FAMILY_COUNT = 226
DEVELOPMENT_TOP_K = 100
MIN_SCAN_EVENTS = 1000
MIN_SCANNABLE_BINS = 24
BROWN_EQ_TOL = 1e-10


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2023", required=True, type=Path)
    p.add_argument("--parser-2025", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--competitor-freeze", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parser_gate_dict(audit: dict[str, Any]) -> dict[str, bool]:
    for key in ("gates", "parser_gates", "integrity_gates"):
        value = audit.get(key)
        if isinstance(value, dict):
            return {str(k): bool(v) for k, v in value.items()}
    raise RuntimeError("parser returned no integrity-gate dictionary")


def parse_year(year: int, parser: Any, archive: Path, mapping_audit: Path, base: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    function = getattr(parser, f"parse_sonotaco_{year}_events")
    parsed = function(archive, mapping_audit, base)
    require(isinstance(parsed, tuple) and len(parsed) == 3, f"unexpected parser return for {year}")
    labeled, sporadic, audit = parsed
    require(isinstance(labeled, list) and isinstance(sporadic, list) and isinstance(audit, dict), f"invalid parser payload for {year}")
    gates = parser_gate_dict(audit)
    require(gates and all(gates.values()), f"SonotaCo {year} parser gates failed: {gates}")
    return labeled, sporadic, audit


def hidden_geometry(event: dict[str, Any], year: int) -> dict[str, Any]:
    return {
        "id": str(event["id"]),
        "year": int(year),
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def build_hidden_panel(parsed: dict[int, tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]]) -> tuple[dict[int, list[dict[str, Any]]], dict[str, str], dict[str, int]]:
    scan_by_year: dict[int, list[dict[str, Any]]] = {}
    hidden_labels: dict[str, str] = {}
    hidden_years: dict[str, int] = {}
    seen: set[str] = set()
    for year in YEARS:
        labeled, sporadic, _audit = parsed[year]
        scan: list[dict[str, Any]] = []
        for event in labeled:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event id {event_id}")
            seen.add(event_id)
            label = str(event.get("complex_key", "")).strip()
            require(label and label != "SPORADIC", f"mapped label missing for {event_id}")
            hidden_labels[event_id] = label
            hidden_years[event_id] = year
            scan.append(hidden_geometry(event, year))
        for event in sporadic:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event id {event_id}")
            seen.add(event_id)
            hidden_labels[event_id] = "SPORADIC"
            hidden_years[event_id] = year
            scan.append(hidden_geometry(event, year))
        require(len(scan) >= MIN_SCAN_EVENTS, f"insufficient scan rows for {year}: {len(scan)}")
        require(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan), f"excluded solar-longitude event entered {year} scan")
        scan_by_year[year] = scan
    return scan_by_year, hidden_labels, hidden_years


def size_bin(n: int) -> str:
    if 4 <= n <= 9:
        return "4-9"
    if 10 <= n <= 24:
        return "10-24"
    if 25 <= n <= 49:
        return "25-49"
    if 50 <= n <= 99:
        return "50-99"
    if n >= 100:
        return "100+"
    return "<4"


def label_counts(hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> dict[int, Counter[str]]:
    out = {year: Counter() for year in YEARS}
    for event_id, label in hidden_labels.items():
        if label == "SPORADIC":
            continue
        out[int(hidden_years[event_id])][label] += 1
    return out


def family_year_ids(family: dict[str, Any], year: int, hidden_years: dict[str, int]) -> list[str]:
    return [str(event_id) for event_id in family["event_ids"] if int(hidden_years[str(event_id)]) == year]


def prf(overlap: int, predicted: int, actual: int) -> tuple[float, float, float]:
    precision = overlap / predicted if predicted else 0.0
    recall = overlap / actual if actual else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return float(precision), float(recall), float(f1)


def best_annual_matches(families: list[dict[str, Any]], hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> tuple[dict[str, Any], dict[str, Any]]:
    counts = label_counts(hidden_labels, hidden_years)
    per_year: dict[str, Any] = {}
    summaries: dict[str, Any] = {}
    for year in YEARS:
        rows: list[dict[str, Any]] = []
        for label, actual in sorted(counts[year].items()):
            if actual < 4:
                continue
            candidates: list[tuple[float, float, int, str, float]] = []
            for family in families:
                ids = family_year_ids(family, year, hidden_years)
                predicted = len(ids)
                if not predicted:
                    continue
                overlap = sum(hidden_labels[event_id] == label for event_id in ids)
                precision, _recall, f1 = prf(overlap, predicted, actual)
                candidates.append((f1, precision, overlap, str(family["family_id"]), float(_recall)))
            if candidates:
                f1, precision, overlap, family_id, recall = max(candidates, key=lambda x: (x[0], x[1], x[2], x[3]))
            else:
                f1 = precision = recall = 0.0
                overlap = 0
                family_id = None
            rows.append({
                "label": label,
                "annual_members": int(actual),
                "size_bin": size_bin(int(actual)),
                "family_id": family_id,
                "overlap": int(overlap),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            })
        per_year[str(year)] = rows
        by_bin: dict[str, Any] = {}
        for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+"):
            subset = [row for row in rows if row["size_bin"] == bin_name]
            by_bin[bin_name] = {
                "showers": len(subset),
                "mean_f1": float(np.mean([row["f1"] for row in subset])) if subset else None,
                "f1_gt_0_5": sum(float(row["f1"]) > 0.5 for row in subset),
                "f1_gt_0_8": sum(float(row["f1"]) > 0.8 for row in subset),
            }
        summaries[str(year)] = by_bin
    return per_year, summaries


def best_recurrent_matches(families: list[dict[str, Any]], hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    counts = label_counts(hidden_labels, hidden_years)
    labels = sorted(set(counts[YEARS[0]]) | set(counts[YEARS[1]]))
    rows: list[dict[str, Any]] = []
    for label in labels:
        actual = {year: int(counts[year].get(label, 0)) for year in YEARS}
        if any(actual[year] < 4 for year in YEARS):
            continue
        candidates: list[tuple[float, float, int, str, dict[int, dict[str, float]]]] = []
        for family in families:
            annual: dict[int, dict[str, float]] = {}
            total_overlap = 0
            for year in YEARS:
                ids = family_year_ids(family, year, hidden_years)
                overlap = sum(hidden_labels[event_id] == label for event_id in ids)
                precision, recall, f1 = prf(overlap, len(ids), actual[year])
                annual[year] = {
                    "predicted": len(ids),
                    "overlap": int(overlap),
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                }
                total_overlap += overlap
            f1s = [annual[year]["f1"] for year in YEARS]
            minimum = float(min(f1s))
            geometric = float(math.sqrt(max(f1s[0], 0.0) * max(f1s[1], 0.0)))
            candidates.append((minimum, geometric, total_overlap, str(family["family_id"]), annual))
        minimum, geometric, total_overlap, family_id, annual = max(candidates, key=lambda x: (x[0], x[1], x[2], x[3])) if candidates else (0.0, 0.0, 0, None, {})
        minimum_members = min(actual.values())
        rows.append({
            "label": label,
            "family_id": family_id,
            "annual_members": {str(year): actual[year] for year in YEARS},
            "minimum_annual_members": int(minimum_members),
            "size_bin": size_bin(int(minimum_members)),
            "annual": {str(year): annual.get(year, {}) for year in YEARS},
            "minimum_annual_f1": float(minimum),
            "geometric_mean_annual_f1": float(geometric),
            "total_overlap": int(total_overlap),
        })
    summary: dict[str, Any] = {
        "eligible_recurrent_showers": len(rows),
        "minimum_annual_f1_ge_0_5": sum(row["minimum_annual_f1"] >= 0.5 for row in rows),
        "minimum_annual_f1_ge_0_8": sum(row["minimum_annual_f1"] >= 0.8 for row in rows),
        "mean_minimum_annual_f1": float(np.mean([row["minimum_annual_f1"] for row in rows])) if rows else 0.0,
        "mean_geometric_annual_f1": float(np.mean([row["geometric_mean_annual_f1"] for row in rows])) if rows else 0.0,
        "size_strata": {},
    }
    for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+"):
        subset = [row for row in rows if row["size_bin"] == bin_name]
        summary["size_strata"][bin_name] = {
            "showers": len(subset),
            "mean_minimum_annual_f1": float(np.mean([row["minimum_annual_f1"] for row in subset])) if subset else None,
            "recovered_ge_0_5": sum(row["minimum_annual_f1"] >= 0.5 for row in subset),
            "recovered_ge_0_8": sum(row["minimum_annual_f1"] >= 0.8 for row in subset),
        }
    return rows, summary


def ranking_metrics(families: list[dict[str, Any]], order: list[str], hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> dict[str, Any]:
    family_by_id = {str(f["family_id"]): f for f in families}
    require(len(order) == len(family_by_id) and set(order) == set(family_by_id), "ranking universe mismatch")
    n = len(order)
    k = (DEVELOPMENT_TOP_K * n + DEVELOPMENT_FAMILY_COUNT - 1) // DEVELOPMENT_FAMILY_COUNT if n else 0
    rank_map = {family_id: rank for rank, family_id in enumerate(order, 1)}
    counts = label_counts(hidden_labels, hidden_years)
    labels = sorted(label for label in set(counts[YEARS[0]]) | set(counts[YEARS[1]]) if all(counts[y].get(label, 0) >= 4 for y in YEARS))
    match_rows: list[dict[str, Any]] = []
    qualified_ranks: list[int] = []
    recovered = 0
    for label in labels:
        total = sum(int(counts[year][label]) for year in YEARS)
        candidates: list[tuple[float, float, int, str]] = []
        for family in families:
            overlap = sum(hidden_labels.get(str(event_id), "SPORADIC") == label for event_id in family["event_ids"])
            if overlap < 1:
                continue
            precision, recall, f1 = prf(overlap, int(family["event_count"]), total)
            candidates.append((f1, precision, overlap, str(family["family_id"])))
        if not candidates:
            match_rows.append({"label": label, "qualified": False, "rank": None})
            continue
        f1, precision, overlap, family_id = max(candidates, key=lambda x: (x[0], x[1], x[2], x[3]))
        rank = rank_map[family_id]
        qualified = bool(precision >= 0.5 and overlap >= 4)
        if qualified:
            qualified_ranks.append(rank)
            recovered += int(rank <= k)
        match_rows.append({
            "label": label,
            "family_id": family_id,
            "rank": rank,
            "qualified": qualified,
            "precision": float(precision),
            "recall": float(overlap / total),
            "f1": float(f1),
            "overlap": int(overlap),
        })
    dominant_precision: list[float] = []
    for family_id in order[:k]:
        family = family_by_id[family_id]
        c = Counter(hidden_labels.get(str(event_id), "SPORADIC") for event_id in family["event_ids"])
        c.pop("SPORADIC", None)
        dominant = c.most_common(1)[0][1] if c else 0
        dominant_precision.append(dominant / int(family["event_count"]) if int(family["event_count"]) else 0.0)
    return {
        "family_count": n,
        "scaled_k": k,
        "scaled_k_formula": "ceil(100*N/226)",
        "eligible_recurrent_labels": len(labels),
        "qualified_matches": len(qualified_ranks),
        "recovered_at_scaled_k": recovered,
        "mrr": float(np.mean([1.0 / rank for rank in qualified_ranks])) if qualified_ranks else 0.0,
        "median_rank": float(np.median(qualified_ranks)) if qualified_ranks else None,
        "topk_dominant_precision": float(np.mean(dominant_precision)) if dominant_precision else 0.0,
        "per_label": match_rows,
    }


def compare_sparse(v8_annual: dict[str, Any], competitors: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"hdbscan": {}, "sugar_uncertainty": {}}
    for year in YEARS:
        y = str(year)
        out["hdbscan"][y] = {}
        out["sugar_uncertainty"][y] = {}
        for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+"):
            vf = v8_annual[y][bin_name]["mean_f1"]
            hf = competitors["hdbscan"][y]["coverage"]["size_strata_mean_f1"].get(bin_name)
            sugar_bin = competitors["sugar_uncertainty"][y]["size_strata"].get(bin_name, {})
            sf = sugar_bin.get("mean_f1")
            out["hdbscan"][y][bin_name] = {
                "v8_mean_f1": vf,
                "competitor_mean_f1": hf,
                "delta_v8_minus_competitor": None if vf is None or hf is None else float(vf - hf),
            }
            out["sugar_uncertainty"][y][bin_name] = {
                "v8_mean_f1": vf,
                "competitor_mean_f1": sf,
                "delta_v8_minus_competitor": None if vf is None or sf is None else float(vf - sf),
            }
    return out


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()

    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    require(sha256_file(args.archive_2023) == ARCHIVE_SHA256[2023], "2023 archive hash changed")
    require(sha256_file(args.archive_2025) == ARCHIVE_SHA256[2025], "2025 archive hash changed")
    competitors = json.loads(args.competitor_freeze.read_text())
    require(competitors["status"] == "frozen_before_v8_sonotaco_matched_execution", "competitor record not pre-frozen")
    require(competitors["benchmark_years"] == [2023, 2025], "competitor years changed")
    require(competitors["blind_exclusion_deg"] == [20.0, 55.0], "competitor blind interval changed")

    require(all(v8.mult.v3.self_test().values()), "v3 self-test failed")
    require(all(v8.mult.brown.self_test().values()), "Brown self-test failed")
    runtime = v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "support blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) <= 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.MIN_ANCHOR_COUNT) == v8.v6.MIN_ANCHOR_COUNT, "minimum anchor count changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == v8.v6.MAX_QUARTETS_PER_BIN, "quartet cap changed")

    # Survey transport only: no scientific constant changes.
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = RAW_FIXED4_RANKING_VARIANTS
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) <= 1e-15, "fixed4 scale changed")

    parsers = {
        2023: load_module(args.parser_2023, "matched_sonotaco_2023_parser"),
        2025: load_module(args.parser_2025, "matched_sonotaco_2025_parser"),
    }
    for year in YEARS:
        parser = parsers[year]
        require(int(parser.YEAR) == year, f"parser year mismatch {year}")
        require(str(parser.MEMBER) == EXPECTED_MEMBERS[year], f"parser member mismatch {year}")
        require(float(parser.BLIND_SOLAR_MIN) == 20.0 and float(parser.BLIND_SOLAR_MAX) == 55.0, f"parser blind interval mismatch {year}")

    # FIRST CATALOGUE PARSE. Both parser sources remove 20-55 before reading the shower token.
    parsed = {
        2023: parse_year(2023, parsers[2023], args.archive_2023, args.mapping_audit, base),
        2025: parse_year(2025, parsers[2025], args.archive_2025, args.mapping_audit, base),
    }
    scan_by_year, hidden_labels, hidden_years = build_hidden_panel(parsed)

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_quartets: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v8.v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(audit["source_labels_used_for_proposals"] is False, f"labels entered proposals for {year}")
        require(audit["score_threshold_applied"] is False, f"score threshold entered proposals for {year}")
        scan_audits.append(audit)
        retained_quartets[str(year)] = len(passing)
        components.extend(year_components)
        print(f"matched v8 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence universe mismatch")
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)

    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()
    scored, scoring_summary = v8.mult.score_families(families, scan_by_year, runtime, base)
    multiplicity_order = v8.mult.rank_scored(scored, "multiplicity")
    brown_order = v8.mult.rank_scored(scored, "brown")
    v3_order = v8.mult.rank_scored(scored, "v3")
    require(set(multiplicity_order) == set(persistence_order), "multiplicity universe mismatch")

    # FIRST LABEL-DEPENDENT EVALUATION. All proposals/families/centroids/scores/ranks above are frozen.
    annual_rows, annual_summary = best_annual_matches(families, hidden_labels, hidden_years)
    recurrent_rows, recurrent_summary = best_recurrent_matches(families, hidden_labels, hidden_years)
    rank_metrics = ranking_metrics(families, multiplicity_order, hidden_labels, hidden_years)
    comparisons = compare_sparse(annual_summary, competitors)

    integrity_gates = {
        "competitor_records_frozen_before_execution": True,
        "exact_2023_2025_archive_hashes": True,
        "mapping_audit_hash_exact": True,
        "parser_integrity_panels_pass": all(all(parser_gate_dict(parsed[year][2]).values()) for year in YEARS),
        "blind_interval_absent_from_scan_geometry": all(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan_by_year[year]) for year in YEARS),
        "zero_source_labels_in_proposals": all(a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold": all(a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits),
        "all_recurrent_families_span_both_years": all(sorted(int(y) for y in family["years"]) == list(YEARS) for family in families),
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128] if families else True,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "pooled_centroid_repair_nonvacuous_or_not_needed": int(repair["families_with_duplicate_same_year_components"]) == 0 or int(repair["changed_duplicate_year_centroids"]) > 0,
        "single_component_centroid_equivalence": float(repair["max_single_component_centroid_distance"]) <= 1e-12,
        "non_centroid_family_structure_unchanged": repair["non_centroid_family_structure_unchanged"] is True,
    }
    verdict = "PASS_V8_LITERATURE_MATCHED_SONOTACO_EXECUTION" if all(integrity_gates.values()) else "FAIL_V8_LITERATURE_MATCHED_SONOTACO_INTEGRITY"

    result = {
        "verdict": verdict,
        "classification": "comparison-only transport of frozen v8 to the same SonotaCo survey years used by the frozen published comparators",
        "configuration": {
            "years": list(YEARS),
            "corpus": CORPUS,
            "blind_exclusion": [20.0, 55.0],
            "v8_source_commit": "c9d6c44704013ba0c9430100e98a29a56b453304",
            "v8_source_blob": V8_SOURCE_SHA,
            "support_source_sha256": SUPPORT_SOURCE_SHA256,
            "runtime_source_sha256": RUNTIME_SOURCE_SHA256,
            "family_link_radius": 1.5,
            "episode_size": 128,
            "multiplicity": "(v3/Brown)^2",
            "no_v8_parameter_change": True,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_weight_search": True,
            "no_pooling_search": True,
            "labels_first_used_after_rank_freeze": True,
        },
        "parser_audits": {str(year): parsed[year][2] for year in YEARS},
        "scan_events": {str(year): len(scan_by_year[year]) for year in YEARS},
        "retained_quartets": retained_quartets,
        "component_count": len(components),
        "family_count": len(families),
        "centroid_repair": repair,
        "scoring_summary": scoring_summary,
        "ranking": {
            "multiplicity": {k: v for k, v in rank_metrics.items() if k != "per_label"},
            "brown_topk_overlap": len(set(multiplicity_order[:rank_metrics["scaled_k"]]) & set(brown_order[:rank_metrics["scaled_k"]])),
            "v3_topk_overlap": len(set(multiplicity_order[:rank_metrics["scaled_k"]]) & set(v3_order[:rank_metrics["scaled_k"]])),
            "persistence_topk_overlap": len(set(multiplicity_order[:rank_metrics["scaled_k"]]) & set(persistence_order[:rank_metrics["scaled_k"]])),
        },
        "annual_coverage": annual_summary,
        "recurrent_coverage": recurrent_summary,
        "comparisons": comparisons,
        "competitor_freeze": competitors,
        "integrity_gates": integrity_gates,
        "runtime_seconds": float(time.perf_counter() - start),
        "claim_boundary": "Benchmark-only result. The SonotaCo 2023/2025 survey years were already exposed in prior comparator work. The 20-55 degree interval was removed before shower-label access. No OrbitTrace target coordinates, members, identity, target-region event, or final target recovery result was accessed. Published comparators retain their original method-specific quality filters, so this execution is matched at raw survey/year and blinded-label scope, not yet identical event-row filtering.",
    }

    args.output.joinpath("v8_literature_matched_sonotaco.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_annual_per_label.json").write_text(json.dumps(annual_rows, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_recurrent_per_label.json").write_text(json.dumps(recurrent_rows, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_ranking_per_label.json").write_text(json.dumps(rank_metrics["per_label"], indent=2, sort_keys=True) + "\n")

    md = [
        "# OrbitTrace v8 matched literature benchmark",
        "",
        f"**Execution verdict:** `{verdict}`",
        "",
        f"- recurrent v8 families: {len(families)}",
        f"- scaled ranking K: {rank_metrics['scaled_k']}",
        f"- qualified recurrent known-shower matches: {rank_metrics['qualified_matches']}",
        f"- multiplicity recovery at scaled K: {rank_metrics['recovered_at_scaled_k']}",
        f"- top-K dominant-label precision: {rank_metrics['topk_dominant_precision']:.6f}",
        f"- recurrent showers with min annual F1 >= .5: {recurrent_summary['minimum_annual_f1_ge_0_5']}/{recurrent_summary['eligible_recurrent_showers']}",
        "",
        "## Annual mean F1 by size bin",
        "",
        "| Year | Bin | v8 | HDBSCAN | Sugar retained |",
        "|---:|:---|---:|---:|---:|",
    ]
    for year in YEARS:
        y = str(year)
        for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+"):
            vf = annual_summary[y][bin_name]["mean_f1"]
            hf = competitors["hdbscan"][y]["coverage"]["size_strata_mean_f1"].get(bin_name)
            sf = competitors["sugar_uncertainty"][y]["size_strata"].get(bin_name, {}).get("mean_f1")
            def fmt(value: Any) -> str:
                return "n/a" if value is None else f"{float(value):.6f}"
            md.append(f"| {year} | {bin_name} | {fmt(vf)} | {fmt(hf)} | {fmt(sf)} |")
    md += [
        "",
        "The published comparators retain their frozen method-specific quality filters. This is therefore matched at survey/year and target-excluded label scope, not yet identical event-row filtering.",
        "",
        "No OrbitTrace target information was accessed.",
    ]
    args.output.joinpath("V8_LITERATURE_MATCHED_SONOTACO.md").write_text("\n".join(md) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
