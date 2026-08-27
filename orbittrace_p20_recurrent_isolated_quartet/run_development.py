#!/usr/bin/env python3
"""P20: target-excluded recurrent isolated-quartet rescue development."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-p20-recurrent-isolated-quartet-development"
BLIND = (20.0, 55.0)
LINK_RADIUS = 1.5
EXPECTED_V8_FAMILIES = 226
EXPECTED_V8_QUALIFIED = 95
EXPECTED_V8_RECOVERY100 = 58
EXPECTED_V8_MACRO_F1 = 0.1736657194465356
EXPECTED_V8_TOP100_PRECISION = 0.6884631112636006
EXPECTED_V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
EXPECTED_V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SIZE_BINS = (
    ("4-9", 4, 9),
    ("10-24", 10, 24),
    ("25-49", 25, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def pooled_centroid(events: list[dict[str, Any]], support: Any) -> dict[str, float]:
    require(events, "cannot pool empty event set")
    return {
        "sol": float(support.circular_mean_deg(float(e["sol"]) for e in events)),
        "sun_lon": float(support.circular_mean_deg(float(e["sun_lon"]) for e in events)),
        "ecl_lat": float(np.median([float(e["ecl_lat"]) for e in events])),
        "vg": float(np.median([float(e["vg"]) for e in events])),
    }


def quartet_preference_key(q: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(q["anchor_count"]),
        -float(q["bin_strength"]),
        -float(q["score"]),
        int(q["bin"]),
        tuple(q["quartet_ids"]),
    )


def isolated_quartets(
    year: int,
    passing: list[dict[str, Any]],
    components: list[dict[str, Any]],
    events: list[dict[str, Any]],
    support: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    event_lookup = {str(e["id"]): e for e in events}
    component_event_ids = {
        str(eid)
        for component in components
        for eid in component["event_ids"]
    }
    by_event_set: dict[tuple[str, ...], dict[str, Any]] = {}
    overlap_rejected = 0
    for record in passing:
        ids = tuple(sorted(str(x) for x in record["quartet_ids"]))
        require(len(ids) == 4 and len(set(ids)) == 4, "retained fixed4 quartet is not exactly four unique events")
        if any(eid in component_event_ids for eid in ids):
            overlap_rejected += 1
            continue
        quartet_events = [event_lookup[eid] for eid in ids]
        q = {
            "quartet_id": f"Q{year}-" + hashlib.sha256("|".join(ids).encode()).hexdigest()[:16],
            "year": int(year),
            "quartet_ids": list(ids),
            "anchor_count": int(record["anchor_count"]),
            "bin_strength": float(record["bin_strength"]),
            "score": float(record["score"]),
            "bin": int(record["bin"]),
            "centroid": pooled_centroid(quartet_events, support),
        }
        prior = by_event_set.get(ids)
        if prior is None or quartet_preference_key(q) < quartet_preference_key(prior):
            by_event_set[ids] = q
    quartets = sorted(by_event_set.values(), key=lambda q: str(q["quartet_id"]))
    audit = {
        "year": int(year),
        "retained_fixed4_quartets": len(passing),
        "component_count": len(components),
        "component_event_count": len(component_event_ids),
        "quartet_records_rejected_for_any_component_overlap": int(overlap_rejected),
        "isolated_unique_quartets": len(quartets),
        "all_isolated_quartets_exactly_four_events": all(len(q["quartet_ids"]) == 4 for q in quartets),
        "zero_component_event_overlap": all(
            not (set(q["quartet_ids"]) & component_event_ids) for q in quartets
        ),
    }
    return quartets, audit


def bins_for_sol(sol: float) -> tuple[int, ...]:
    # Same conservative computational prefilter already frozen in P19: exact
    # centroid distance <=1.5 implies solar-longitude separation <=6 degrees.
    center = int(math.floor(float(sol))) % 360
    return tuple((center + offset) % 360 for offset in range(-7, 8))


def quartet_bins(quartets: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    bins: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for q in quartets:
        bins[int(math.floor(float(q["centroid"]["sol"]))) % 360].append(q)
    for key in bins:
        bins[key].sort(key=lambda q: str(q["quartet_id"]))
    return dict(bins)


def nearest_other_year(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> tuple[dict[str, str], dict[tuple[str, str], float], dict[str, int]]:
    target_bins = quartet_bins(target)
    mapping: dict[str, str] = {}
    distances: dict[tuple[str, str], float] = {}
    prefilter_considered = 0
    exact_within_radius = 0
    for q in source:
        center = q["centroid"]
        rows: list[tuple[Any, ...]] = []
        for key in bins_for_sol(float(center["sol"])):
            for other in target_bins.get(key, []):
                # Necessary inherited-coordinate prefilters used by P19 only to
                # avoid exact distance calls that cannot possibly pass radius 1.5.
                if abs(float(other["centroid"]["ecl_lat"]) - float(center["ecl_lat"])) > 3.0:
                    continue
                if abs(float(other["centroid"]["vg"]) - float(center["vg"])) > 3.0:
                    continue
                prefilter_considered += 1
                d = float(support.centroid_distance(center, other["centroid"], base))
                if d > LINK_RADIUS:
                    continue
                exact_within_radius += 1
                rows.append((
                    d,
                    -int(other["anchor_count"]),
                    -float(other["bin_strength"]),
                    -float(other["score"]),
                    tuple(other["quartet_ids"]),
                    str(other["quartet_id"]),
                ))
        if not rows:
            continue
        rows.sort()
        best = rows[0]
        other_id = str(best[-1])
        mapping[str(q["quartet_id"])] = other_id
        distances[(str(q["quartet_id"]), other_id)] = float(best[0])
    return mapping, distances, {
        "source_quartets": len(source),
        "target_quartets": len(target),
        "sources_with_partner_within_radius": len(mapping),
        "prefilter_exact_distance_calls": int(prefilter_considered),
        "exact_pairs_within_radius": int(exact_within_radius),
    }


def build_recurrent_isolated_quartets(
    quartets_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    q22 = quartets_by_year[2022]
    q23 = quartets_by_year[2023]
    by_id = {str(q["quartet_id"]): q for q in q22 + q23}
    m22, d22, a22 = nearest_other_year(q22, q23, support, base)
    m23, d23, a23 = nearest_other_year(q23, q22, support, base)

    families: list[dict[str, Any]] = []
    for q22_id in sorted(m22):
        q23_id = m22[q22_id]
        if m23.get(q23_id) != q22_id:
            continue
        q_a = by_id[q22_id]
        q_b = by_id[q23_id]
        d = float(d22[(q22_id, q23_id)])
        reverse_d = float(d23[(q23_id, q22_id)])
        require(abs(d - reverse_d) < 1e-12, "reciprocal quartet distance mismatch")
        require(d <= LINK_RADIUS, "reciprocal quartet pair exceeds inherited radius")
        event_ids = sorted(set(q_a["quartet_ids"]) | set(q_b["quartet_ids"]))
        require(len(event_ids) == 8, "P20 recurrent isolated-quartet family is not exact 4+4")
        stable = hashlib.sha256((q22_id + "|" + q23_id).encode()).hexdigest()[:16]
        family = {
            "family_id": "RIQ" + stable,
            "family_type": "recurrent_isolated_quartet_4plus4",
            "years": [2022, 2023],
            "year_count": 2,
            "component_ids": [],
            "component_count": 0,
            "event_ids": event_ids,
            "event_count": 8,
            "quartet_count": 2,
            "anchor_count": int(q_a["anchor_count"] + q_b["anchor_count"]),
            "best_score": float(max(q_a["score"], q_b["score"])),
            "year_strengths": {
                "2022": float(q_a["bin_strength"]),
                "2023": float(q_b["bin_strength"]),
            },
            "centroids": {
                "2022": q_a["centroid"],
                "2023": q_b["centroid"],
            },
            "ranks": {},
            "ranking_scores": {},
            "p20_quartet_ids": {"2022": q22_id, "2023": q23_id},
            "p20_cross_year_distance": d,
            "p20_min_anchor_count": int(min(q_a["anchor_count"], q_b["anchor_count"])),
            "p20_min_bin_strength": float(min(q_a["bin_strength"], q_b["bin_strength"])),
            "p20_min_quartet_score": float(min(q_a["score"], q_b["score"])),
        }
        families.append(family)

    families.sort(key=lambda f: (
        float(f["p20_cross_year_distance"]),
        -int(f["p20_min_anchor_count"]),
        -float(f["p20_min_bin_strength"]),
        -float(f["p20_min_quartet_score"]),
        str(f["family_id"]),
    ))
    require(len({str(f["family_id"]) for f in families}) == len(families), "P20 family IDs not unique")
    require(len({tuple(f["event_ids"]) for f in families}) == len(families), "P20 exact family event sets not unique")
    diagnostics = {
        "2022_to_2023": a22,
        "2023_to_2022": a23,
        "mutual_reciprocal_family_count": len(families),
        "all_family_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in families),
        "all_pair_distances_within_inherited_1_5": all(float(f["p20_cross_year_distance"]) <= LINK_RADIUS for f in families),
        "membership_expansion": False,
        "recursion": False,
        "new_scientific_radius": False,
    }
    return families, diagnostics


def structural_family_payload(family: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "family_id", "family_type", "years", "year_count", "component_ids", "component_count",
        "event_ids", "event_count", "quartet_count", "anchor_count", "best_score", "year_strengths",
        "centroids", "p20_quartet_ids", "p20_cross_year_distance", "p20_min_anchor_count",
        "p20_min_bin_strength", "p20_min_quartet_score",
    )
    return {name: family[name] for name in keep if name in family}


def annual_bin_metrics(hidden_labels: dict[str, str], families: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        label_counts = Counter(
            label for eid, label in hidden_labels.items()
            if int(str(eid)[:4]) == year and label != "SPORADIC"
        )
        per_label: dict[str, dict[str, float]] = {}
        for label, total in sorted(label_counts.items()):
            if total < 4:
                continue
            best = {"f1": 0.0, "precision": 0.0, "recall": 0.0, "overlap": 0.0}
            for family in families:
                year_ids = [eid for eid in family["event_ids"] if int(str(eid)[:4]) == year]
                if not year_ids:
                    continue
                overlap = sum(hidden_labels.get(eid) == label for eid in year_ids)
                if overlap == 0:
                    continue
                precision = overlap / len(year_ids)
                recall = overlap / total
                f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
                candidate = (f1, precision, overlap)
                current = (best["f1"], best["precision"], best["overlap"])
                if candidate > current:
                    best = {
                        "f1": float(f1), "precision": float(precision),
                        "recall": float(recall), "overlap": int(overlap),
                    }
            per_label[label] = {"total": int(total), **best}

        bins: dict[str, Any] = {}
        for name, low, high in SIZE_BINS:
            rows = [
                row for row in per_label.values()
                if row["total"] >= low and (high is None or row["total"] <= high)
            ]
            bins[name] = {
                "showers": len(rows),
                "mean_f1": float(np.mean([r["f1"] for r in rows])) if rows else 0.0,
                "mean_precision": float(np.mean([r["precision"] for r in rows])) if rows else 0.0,
                "mean_recall": float(np.mean([r["recall"] for r in rows])) if rows else 0.0,
            }
        all_rows = list(per_label.values())
        bins["all"] = {
            "showers": len(all_rows),
            "mean_f1": float(np.mean([r["f1"] for r in all_rows])) if all_rows else 0.0,
            "mean_precision": float(np.mean([r["precision"] for r in all_rows])) if all_rows else 0.0,
            "mean_recall": float(np.mean([r["recall"] for r in all_rows])) if all_rows else 0.0,
        }
        out[str(year)] = bins
    return out


def delta_bins(challenger: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        str(year): {
            name: float(challenger[str(year)][name]["mean_f1"] - baseline[str(year)][name]["mean_f1"])
            for name, _low, _high in SIZE_BINS
        }
        for year in YEARS
    }


def combined_4_24_mean(panel: dict[str, Any], year: int) -> float:
    a = panel[str(year)]["4-9"]
    b = panel[str(year)]["10-24"]
    n = int(a["showers"]) + int(b["showers"])
    return (
        float(a["mean_f1"]) * int(a["showers"]) + float(b["mean_f1"]) * int(b["showers"])
    ) / max(1, n)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    raw_v8 = args.v8_result_json.read_bytes()
    require(hashlib.sha256(raw_v8).hexdigest() == EXPECTED_V8_RESULT_SHA256, "v8 result JSON hash changed")
    v8_result = json.loads(raw_v8)
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 predecessor did not pass")
    require(int(v8_result["family_count"]) == EXPECTED_V8_FAMILIES, "v8 family count changed")
    require(int(v8_result["metrics"]["multiplicity"]["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "v8 qualified baseline changed")
    require(int(v8_result["metrics"]["multiplicity"]["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "v8 recovery baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-15, "v8 precision baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-15, "v8 macro baseline changed")
    require(v8_result["configuration"]["blind_exclusion"] == [20.0, 55.0], "v8 blind interval changed")

    require(all(mult.v3.self_test().values()), "v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target exclusion changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4, "within-year component event floor changed")
    require(int(support.MIN_COMPONENT_QUARTETS) == 2, "within-year component quartet floor changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "hard recurrence minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - LINK_RADIUS) < 1e-15, "hard link radius changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2, "retained-quartet anchor multiplicity changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == 512, "retained-quartet bin cap changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    # FIRST DEVELOPMENT CATALOGUE ACCESS. Inherited parser removes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "month universe changed")

    components: list[dict[str, Any]] = []
    components_by_year: dict[int, list[dict[str, Any]]] = {}
    passing_by_year: dict[int, list[dict[str, Any]]] = {}
    scan_audits: list[dict[str, Any]] = []
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_by_year[year] = passing
        components_by_year[year] = year_components
        components.extend(year_components)

    # Reconstruct exact v8 hard universe/ranking first.
    hard_families, support_rankings = support.build_families(components, base)
    require(len(hard_families) == EXPECTED_V8_FAMILIES, f"exact v8 hard family count changed: {len(hard_families)}")
    hard_persistence = [str(x) for x in support_rankings["persistence"]]
    repair = v8.repair_year_centroids(hard_families, components, scan_by_year, support, base)
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100
    hard_scored, hard_scoring = mult.score_families(hard_families, scan_by_year, runtime, base)
    hard_multiplicity = mult.rank_scored(hard_scored, "multiplicity")
    require(len(hard_multiplicity) == EXPECTED_V8_FAMILIES, "hard multiplicity order incomplete")

    # P20 family-generation change. Hidden labels are not passed.
    quartets_by_year: dict[int, list[dict[str, Any]]] = {}
    isolated_audits: dict[str, Any] = {}
    for year in YEARS:
        quartets, audit = isolated_quartets(
            year, passing_by_year[year], components_by_year[year], scan_by_year[year], support
        )
        quartets_by_year[year] = quartets
        isolated_audits[str(year)] = audit
    soft_families, soft_diag = build_recurrent_isolated_quartets(quartets_by_year, support, base)
    combined_families = hard_families + soft_families
    p20_order = hard_multiplicity + [str(f["family_id"]) for f in soft_families]
    require(p20_order[:len(hard_multiplicity)] == hard_multiplicity, "v8 hard ranking prefix changed")
    require(len(p20_order) == len(combined_families), "combined order/family count mismatch")
    require(len(set(p20_order)) == len(p20_order), "combined family IDs not unique")

    prelabel_payload = {
        "hard_order": hard_multiplicity,
        "hard_families": [structural_family_payload(f) for f in hard_families],
        "isolated_quartets": {
            str(year): quartets_by_year[year] for year in YEARS
        },
        "soft_families": [structural_family_payload(f) for f in soft_families],
        "isolated_audits": isolated_audits,
        "soft_diagnostics": soft_diag,
    }
    prelabel_sha = sha256_json(prelabel_payload)

    # FIRST SCIENTIFIC LABEL EVALUATION.
    baseline = mult.evaluate_order(hidden_labels, hard_families, hard_multiplicity)
    p20_metrics = mult.evaluate_order(hidden_labels, combined_families, p20_order)
    baseline_annual = annual_bin_metrics(hidden_labels, hard_families)
    p20_annual = annual_bin_metrics(hidden_labels, combined_families)
    annual_delta = delta_bins(p20_annual, baseline_annual)
    combined_delta = {
        str(year): float(combined_4_24_mean(p20_annual, year) - combined_4_24_mean(baseline_annual, year))
        for year in YEARS
    }

    require(int(baseline["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "rerun v8 qualified mismatch")
    require(int(baseline["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "rerun v8 recovery@100 mismatch")
    require(abs(float(baseline["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-12, "rerun v8 macro mismatch")
    require(abs(float(baseline["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-12, "rerun v8 precision mismatch")

    component_events_by_year = {
        year: {str(eid) for c in components_by_year[year] for eid in c["event_ids"]}
        for year in YEARS
    }
    integrity_gates = {
        "exact_target_excluded_2022_2023_panel": True,
        "exact_v8_hard_family_count_226": len(hard_families) == EXPECTED_V8_FAMILIES,
        "exact_v8_hard_ranking_prefix_preserved": p20_order[:EXPECTED_V8_FAMILIES] == hard_multiplicity,
        "every_isolated_quartet_exactly_four_events": all(
            len(q["quartet_ids"]) == 4 for year in YEARS for q in quartets_by_year[year]
        ),
        "every_isolated_quartet_zero_component_overlap": all(
            not (set(q["quartet_ids"]) & component_events_by_year[year])
            for year in YEARS for q in quartets_by_year[year]
        ),
        "every_soft_family_exact_4plus4": all(int(f["event_count"]) == 8 for f in soft_families),
        "every_soft_pair_within_inherited_1_5": all(float(f["p20_cross_year_distance"]) <= LINK_RADIUS for f in soft_families),
        "pooled_centroid_repair_nonvacuous": int(repair["changed_duplicate_year_centroids"]) > 0,
        "prelabel_family_payload_frozen": bool(prelabel_sha),
        "no_membership_expansion": bool(soft_diag["membership_expansion"] is False),
        "no_recursion": bool(soft_diag["recursion"] is False),
        "no_new_scientific_radius": bool(soft_diag["new_scientific_radius"] is False),
        "no_label_parameter_search": True,
        "no_detector_threshold_change": True,
        "no_component_threshold_change": True,
        "no_target_information_access": True,
    }
    scientific_gates = {
        "qualified_matches_at_least_95": int(p20_metrics["qualified_matches"]) >= EXPECTED_V8_QUALIFIED,
        "recovery_at_100_at_least_58": int(p20_metrics["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100,
        "top100_precision_exact_v8_prefix": abs(float(p20_metrics["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) <= 1e-12,
        "macro_f1_gain_at_least_005": float(p20_metrics["macro_f1"]) >= EXPECTED_V8_MACRO_F1 + 0.05,
        "sparse_4_9_mean_f1_gain_at_least_005_both_years": all(
            annual_delta[str(year)]["4-9"] >= 0.05 for year in YEARS
        ),
        "combined_4_24_mean_f1_gain_positive_both_years": all(combined_delta[str(year)] > 0.0 for year in YEARS),
        "isolated_quartet_recurrence_nonvacuous": len(soft_families) > 0,
    }
    passed = all(integrity_gates.values()) and all(scientific_gates.values())
    verdict = "PASS_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT" if passed else "FAIL_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(MONTH_KEYS),
            "corpus": CORPUS,
            "blind_exclusion": list(BLIND),
            "base_method": "promoted v8 pooled-year-centroid label-free sparse-support multiplicity",
            "change_layer": "recurrent family existence from isolated retained fixed4 quartets only",
            "isolated_quartet_rule": "zero event overlap with every same-year exact v8 component",
            "cross_year_rule": "mutual nearest isolated quartet centroids within inherited radius 1.5",
            "reported_membership": "exact four quartet events per year, no expansion",
            "ranking": "exact v8 multiplicity order as immutable prefix, then reciprocal isolated-quartet families",
            "parameter_search": False,
            "threshold_search": False,
            "radius_search": False,
            "component_floor_search": False,
            "variant_search": False,
        },
        "v8_predecessor": {
            "artifact_digest": EXPECTED_V8_ARTIFACT_DIGEST,
            "result_sha256": EXPECTED_V8_RESULT_SHA256,
            "family_count": EXPECTED_V8_FAMILIES,
            "qualified_matches": EXPECTED_V8_QUALIFIED,
            "recovery_at_100": EXPECTED_V8_RECOVERY100,
            "macro_f1": EXPECTED_V8_MACRO_F1,
            "top100_dominant_precision": EXPECTED_V8_TOP100_PRECISION,
        },
        "catalogue_sources": catalogue_sources,
        "scan_audits": scan_audits,
        "isolated_quartet_audits": isolated_audits,
        "soft_diagnostics": soft_diag,
        "hard_family_count": len(hard_families),
        "soft_family_count": len(soft_families),
        "combined_family_count": len(combined_families),
        "prelabel_payload_sha256": prelabel_sha,
        "centroid_repair": repair,
        "hard_persistence_family_count": len(hard_persistence),
        "hard_scoring_summary": hard_scoring,
        "baseline_metrics": {k: v for k, v in baseline.items() if k != "per_label"},
        "p20_metrics": {k: v for k, v in p20_metrics.items() if k != "per_label"},
        "baseline_annual": baseline_annual,
        "p20_annual": p20_annual,
        "annual_mean_f1_delta": annual_delta,
        "combined_4_24_mean_f1_delta": combined_delta,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": (
            "Target-excluded GMN 2022/2023 development only. Exact promoted-v8 proposal generation, "
            "components, hard families, pooled centroids, scoring, and ranking are preserved. P20 adds "
            "only reciprocal cross-year families from retained fixed4 quartets completely excluded from "
            "all existing within-year components. Full candidate payload is frozen before labels. No "
            "SonotaCo/MAARSY scientific value or OrbitTrace target information is accessed."
        ),
    }
    (args.output / "p20_recurrent_isolated_quartet_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "p20_prelabel_payload.json").write_text(
        json.dumps(prelabel_payload, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# OrbitTrace P20 recurrent isolated-quartet development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- hard v8 families: **{len(hard_families)}**",
        f"- isolated retained quartets 2022/2023: **{len(quartets_by_year[2022])} / {len(quartets_by_year[2023])}**",
        f"- added reciprocal 4+4 families: **{len(soft_families)}**",
        f"- qualified matches: **{baseline['qualified_matches']} -> {p20_metrics['qualified_matches']}**",
        f"- recovery@100: **{baseline['recovered_at_100']} -> {p20_metrics['recovered_at_100']}**",
        f"- macro F1: **{baseline['macro_f1']:.6f} -> {p20_metrics['macro_f1']:.6f}**",
        f"- top-100 dominant precision: **{baseline['top100_dominant_precision']:.6f} -> {p20_metrics['top100_dominant_precision']:.6f}**",
        f"- 2022 4-9 mean-F1 delta: **{annual_delta['2022']['4-9']:+.6f}**",
        f"- 2023 4-9 mean-F1 delta: **{annual_delta['2023']['4-9']:+.6f}**",
        f"- 2022 combined 4-24 mean-F1 delta: **{combined_delta['2022']:+.6f}**",
        f"- 2023 combined 4-24 mean-F1 delta: **{combined_delta['2023']:+.6f}**",
        "",
        "No OrbitTrace target information or target-region event was accessed.",
    ]
    (args.output / "P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
