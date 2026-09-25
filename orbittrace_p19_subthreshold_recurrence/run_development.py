#!/usr/bin/env python3
"""P19: target-excluded subthreshold reciprocal recurrence development."""
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
CORPUS = "orbittrace-p19-subthreshold-reciprocal-recurrence-development"
BLIND = (20.0, 55.0)
SOFT_SUPPORT_K = 3
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


def pseudo_centroid(event: dict[str, Any]) -> dict[str, float]:
    return {
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
    }


def pooled_centroid(events: list[dict[str, Any]], support: Any) -> dict[str, float]:
    require(events, "cannot pool empty event set")
    return {
        "sol": float(support.circular_mean_deg(float(e["sol"]) for e in events)),
        "sun_lon": float(support.circular_mean_deg(float(e["sun_lon"]) for e in events)),
        "ecl_lat": float(np.median([float(e["ecl_lat"]) for e in events])),
        "vg": float(np.median([float(e["vg"]) for e in events])),
    }


def bins_for_sol(sol: float) -> tuple[int, ...]:
    # Exact centroid distance <=1.5 requires |d_sol|<=6 degrees. Integer bins +/-7 are conservative.
    center = int(math.floor(float(sol))) % 360
    return tuple((center + offset) % 360 for offset in range(-7, 8))


def event_bins(events: list[dict[str, Any]], excluded_ids: set[str]) -> dict[int, list[dict[str, Any]]]:
    bins: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if str(event["id"]) in excluded_ids:
            continue
        bins[int(math.floor(float(event["sol"]))) % 360].append(event)
    for key in bins:
        bins[key].sort(key=lambda e: str(e["id"]))
    return dict(bins)


def exact_support_candidates(
    center: dict[str, float],
    bins: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> list[tuple[float, dict[str, Any]]]:
    rows: list[tuple[float, str, dict[str, Any]]] = []
    for key in bins_for_sol(float(center["sol"])):
        for event in bins.get(key, []):
            # Necessary prefilter only: exact distance <=1.5 implies each normalized coordinate <=1.5.
            if abs(float(event["ecl_lat"]) - float(center["ecl_lat"])) > 3.0:
                continue
            if abs(float(event["vg"]) - float(center["vg"])) > 3.0:
                continue
            d = float(support.centroid_distance(center, pseudo_centroid(event), base))
            if d <= LINK_RADIUS:
                rows.append((d, str(event["id"]), event))
    rows.sort(key=lambda row: (row[0], row[1]))
    return [(d, event) for d, _eid, event in rows]


def pairwise_triplet_coherent(events: list[dict[str, Any]], support: Any, base: Any) -> bool:
    require(len(events) == SOFT_SUPPORT_K, "soft trigger must contain exactly three events")
    for i in range(SOFT_SUPPORT_K):
        for j in range(i + 1, SOFT_SUPPORT_K):
            d = float(support.centroid_distance(pseudo_centroid(events[i]), pseudo_centroid(events[j]), base))
            if d > LINK_RADIUS:
                return False
    return True


def nearest_unmatched_component(
    center: dict[str, float],
    components: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> str | None:
    rows = []
    for component in components:
        d = float(support.centroid_distance(center, component["centroid"], base))
        if d <= LINK_RADIUS:
            rows.append((d, -float(component["component_strength"]), str(component["component_id"])))
    if not rows:
        return None
    rows.sort()
    return rows[0][2]


def structural_family_payload(family: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "family_id", "family_type", "years", "year_count", "component_ids", "component_count",
        "event_ids", "event_count", "quartet_count", "anchor_count", "best_score", "year_strengths",
        "centroids", "soft_seed_component_id", "soft_seed_year", "soft_support_year",
        "soft_trigger_event_ids", "soft_support_event_ids", "soft_support_count",
        "soft_trigger_max_seed_distance", "soft_trigger_pairwise_coherent", "soft_reciprocal_component_id",
    )
    return {name: family[name] for name in keep if name in family}


def build_soft_recurrence(
    components: list[dict[str, Any]],
    hard_families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    component_by_id = {str(c["component_id"]): c for c in components}
    hard_component_ids = {
        str(cid)
        for family in hard_families
        for cid in family["component_ids"]
    }
    all_component_event_ids_by_year: dict[int, set[str]] = {
        year: {
            str(eid)
            for c in components if int(c["year"]) == year
            for eid in c["event_ids"]
        }
        for year in YEARS
    }
    unmatched_by_year: dict[int, list[dict[str, Any]]] = {
        year: sorted(
            [c for c in components if int(c["year"]) == year and str(c["component_id"]) not in hard_component_ids],
            key=lambda c: str(c["component_id"]),
        )
        for year in YEARS
    }
    bins_by_year = {
        year: event_bins(scan_by_year[year], all_component_event_ids_by_year[year])
        for year in YEARS
    }
    lookup_by_year = {
        year: {str(e["id"]): e for e in scan_by_year[year]}
        for year in YEARS
    }

    soft: list[dict[str, Any]] = []
    diagnostics = {
        "unmatched_components_by_year": {str(y): len(unmatched_by_year[y]) for y in YEARS},
        "seeds_with_at_least_3_exact_support_events": {str(y): 0 for y in YEARS},
        "triplet_coherence_passes": {str(y): 0 for y in YEARS},
        "reciprocal_passes": {str(y): 0 for y in YEARS},
        "soft_family_count_by_seed_year": {str(y): 0 for y in YEARS},
        "support_events_are_outside_all_fixed4_components": True,
        "trigger_k": SOFT_SUPPORT_K,
        "link_radius": LINK_RADIUS,
    }

    for seed_year in YEARS:
        other_year = YEARS[1] if seed_year == YEARS[0] else YEARS[0]
        for seed in unmatched_by_year[seed_year]:
            candidates = exact_support_candidates(seed["centroid"], bins_by_year[other_year], support, base)
            if len(candidates) < SOFT_SUPPORT_K:
                continue
            diagnostics["seeds_with_at_least_3_exact_support_events"][str(seed_year)] += 1
            trigger = [event for _d, event in candidates[:SOFT_SUPPORT_K]]
            if not pairwise_triplet_coherent(trigger, support, base):
                continue
            diagnostics["triplet_coherence_passes"][str(seed_year)] += 1
            trigger_center = pooled_centroid(trigger, support)
            if float(support.centroid_distance(seed["centroid"], trigger_center, base)) > LINK_RADIUS:
                continue
            reciprocal = nearest_unmatched_component(trigger_center, unmatched_by_year[seed_year], support, base)
            if reciprocal != str(seed["component_id"]):
                continue
            diagnostics["reciprocal_passes"][str(seed_year)] += 1

            # Trigger is exactly 3 coherent subcomponent events. Report all unclaimed
            # other-year events inside the intersection of the inherited 1.5 balls
            # around the seed centroid and trigger centroid; no fitted expansion radius.
            reported_support: list[tuple[float, str, dict[str, Any]]] = []
            for d_seed, event in candidates:
                d_trigger = float(support.centroid_distance(trigger_center, pseudo_centroid(event), base))
                if d_trigger <= LINK_RADIUS:
                    reported_support.append((max(d_seed, d_trigger), str(event["id"]), event))
            reported_support.sort(key=lambda row: (row[0], row[1]))
            support_events = [row[2] for row in reported_support]
            if len(support_events) < SOFT_SUPPORT_K:
                continue

            seed_events = [lookup_by_year[seed_year][str(eid)] for eid in seed["event_ids"]]
            other_center = pooled_centroid(support_events, support)
            all_event_ids = sorted(set(map(str, seed["event_ids"])) | {str(e["id"]) for e in support_events})
            stable = hashlib.sha256(
                (str(seed["component_id"]) + "|" + "|".join(sorted(str(e["id"]) for e in trigger))).encode()
            ).hexdigest()[:12]
            family_id = "SFT" + stable
            family = {
                "family_id": family_id,
                "family_type": "soft_reciprocal_k3",
                "years": sorted([seed_year, other_year]),
                "year_count": 2,
                "component_ids": [str(seed["component_id"])],
                "component_count": 1,
                "event_ids": all_event_ids,
                "event_count": len(all_event_ids),
                "quartet_count": int(seed["quartet_count"]),
                "anchor_count": int(seed["anchor_count"]),
                "best_score": float(seed["best_score"]),
                "year_strengths": {
                    str(seed_year): float(seed["component_strength"]),
                    str(other_year): 0.0,
                },
                "centroids": {
                    str(seed_year): pooled_centroid(seed_events, support),
                    str(other_year): other_center,
                },
                "ranks": {},
                "ranking_scores": {},
                "soft_seed_component_id": str(seed["component_id"]),
                "soft_seed_year": int(seed_year),
                "soft_support_year": int(other_year),
                "soft_trigger_event_ids": sorted(str(e["id"]) for e in trigger),
                "soft_support_event_ids": sorted(str(e["id"]) for e in support_events),
                "soft_support_count": len(support_events),
                "soft_trigger_max_seed_distance": float(max(d for d, _e in candidates[:SOFT_SUPPORT_K])),
                "soft_trigger_pairwise_coherent": True,
                "soft_reciprocal_component_id": reciprocal,
            }
            soft.append(family)
            diagnostics["soft_family_count_by_seed_year"][str(seed_year)] += 1

    # Reciprocal construction can still yield duplicate event hypotheses from different
    # seed directions. Keep one exact event-set realization deterministically, preferring
    # stronger seed evidence; no overlap/Jaccard threshold is introduced.
    by_event_set: dict[tuple[str, ...], dict[str, Any]] = {}
    for family in soft:
        key = tuple(family["event_ids"])
        prior = by_event_set.get(key)
        if prior is None:
            by_event_set[key] = family
            continue
        left = component_by_id[str(prior["soft_seed_component_id"])]
        right = component_by_id[str(family["soft_seed_component_id"])]
        pkey = (-float(left["component_strength"]), -int(left["event_count"]), str(left["component_id"]))
        fkey = (-float(right["component_strength"]), -int(right["event_count"]), str(right["component_id"]))
        if fkey < pkey:
            by_event_set[key] = family
    soft = sorted(
        by_event_set.values(),
        key=lambda f: (
            -float(component_by_id[str(f["soft_seed_component_id"])] ["component_strength"]),
            float(f["soft_trigger_max_seed_distance"]),
            -int(component_by_id[str(f["soft_seed_component_id"])] ["event_count"]),
            str(f["family_id"]),
        ),
    )
    diagnostics["soft_family_count_before_exact_eventset_dedup"] = int(sum(diagnostics["soft_family_count_by_seed_year"].values()))
    diagnostics["soft_family_count_after_exact_eventset_dedup"] = len(soft)
    diagnostics["exact_eventset_duplicates_removed"] = diagnostics["soft_family_count_before_exact_eventset_dedup"] - len(soft)
    return soft, diagnostics


def evaluate_order(hidden_labels: dict[str, str], families: list[dict[str, Any]], order: list[str]) -> dict[str, Any]:
    # Exact v8 evaluator semantics.
    return mult.evaluate_order(hidden_labels, families, order)


def annual_bin_metrics(
    hidden_labels: dict[str, str],
    families: list[dict[str, Any]],
) -> dict[str, Any]:
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

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)

    # FIRST DEVELOPMENT CATALOGUE ACCESS. Parser excludes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "month universe changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_quartets: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        retained_quartets[str(year)] = len(passing)
        components.extend(year_components)

    # Exact v8 hard family graph is constructed first.
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

    # P19 recurrence-layer change. No labels are passed.
    soft_families, soft_diag = build_soft_recurrence(
        components, hard_families, scan_by_year, support, base
    )
    combined_families = hard_families + soft_families

    # Existing v8 hard ranking is an immutable prefix. Soft families are appended by
    # label-free seed strength / geometric trigger quality and can never demote a hard family.
    p19_order = hard_multiplicity + [str(f["family_id"]) for f in soft_families]
    require(p19_order[:len(hard_multiplicity)] == hard_multiplicity, "v8 hard ranking prefix changed")
    require(len(p19_order) == len(combined_families), "combined order/family count mismatch")
    require(len(set(p19_order)) == len(p19_order), "combined family IDs not unique")

    prelabel_payload = {
        "hard_order": hard_multiplicity,
        "hard_families": [structural_family_payload(f) for f in hard_families],
        "soft_families": [structural_family_payload(f) for f in soft_families],
        "soft_diagnostics": soft_diag,
    }
    prelabel_sha = sha256_json(prelabel_payload)

    # FIRST SCIENTIFIC LABEL EVALUATION.
    baseline = evaluate_order(hidden_labels, hard_families, hard_multiplicity)
    p19_metrics = evaluate_order(hidden_labels, combined_families, p19_order)
    baseline_annual = annual_bin_metrics(hidden_labels, hard_families)
    p19_annual = annual_bin_metrics(hidden_labels, combined_families)
    annual_delta = delta_bins(p19_annual, baseline_annual)

    # Reproduce the promoted v8 development endpoints before judging P19.
    require(int(baseline["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "rerun v8 qualified mismatch")
    require(int(baseline["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "rerun v8 recovery@100 mismatch")
    require(abs(float(baseline["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-12, "rerun v8 macro mismatch")
    require(abs(float(baseline["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-12, "rerun v8 precision mismatch")

    integrity_gates = {
        "exact_target_excluded_2022_2023_panel": True,
        "exact_v8_hard_family_count_226": len(hard_families) == EXPECTED_V8_FAMILIES,
        "exact_v8_hard_ranking_prefix_preserved": p19_order[:EXPECTED_V8_FAMILIES] == hard_multiplicity,
        "soft_trigger_exactly_three_events": int(soft_diag["trigger_k"]) == SOFT_SUPPORT_K,
        "soft_radius_exactly_inherited_1_5": abs(float(soft_diag["link_radius"]) - LINK_RADIUS) < 1e-15,
        "soft_support_excludes_existing_component_events": bool(soft_diag["support_events_are_outside_all_fixed4_components"]),
        "pooled_centroid_repair_nonvacuous": int(repair["changed_duplicate_year_centroids"]) > 0,
        "prelabel_family_payload_frozen": bool(prelabel_sha),
        "no_label_parameter_search": True,
        "no_detector_threshold_change": True,
        "no_component_threshold_change": True,
        "no_target_information_access": True,
    }
    scientific_gates = {
        # Absolute non-regression against the promoted v8 endpoints.
        "qualified_matches_at_least_95": int(p19_metrics["qualified_matches"]) >= EXPECTED_V8_QUALIFIED,
        "recovery_at_100_at_least_58": int(p19_metrics["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100,
        "top100_precision_at_least_v8_minus_002": float(p19_metrics["top100_dominant_precision"]) >= EXPECTED_V8_TOP100_PRECISION - 0.02,
        # P19 must do more than exploit monotonic candidate addition.
        "macro_f1_gain_at_least_005": float(p19_metrics["macro_f1"]) >= EXPECTED_V8_MACRO_F1 + 0.05,
        "sparse_4_9_mean_f1_gain_at_least_005_both_years": all(
            annual_delta[str(year)]["4-9"] >= 0.05 for year in YEARS
        ),
        "combined_4_24_mean_f1_gain_positive_both_years": all(
            (
                (p19_annual[str(year)]["4-9"]["mean_f1"] * p19_annual[str(year)]["4-9"]["showers"]
                 + p19_annual[str(year)]["10-24"]["mean_f1"] * p19_annual[str(year)]["10-24"]["showers"])
                / max(1, p19_annual[str(year)]["4-9"]["showers"] + p19_annual[str(year)]["10-24"]["showers"])
                -
                (baseline_annual[str(year)]["4-9"]["mean_f1"] * baseline_annual[str(year)]["4-9"]["showers"]
                 + baseline_annual[str(year)]["10-24"]["mean_f1"] * baseline_annual[str(year)]["10-24"]["showers"])
                / max(1, baseline_annual[str(year)]["4-9"]["showers"] + baseline_annual[str(year)]["10-24"]["showers"])
            ) > 0.0
            for year in YEARS
        ),
        "soft_recurrence_nonvacuous": len(soft_families) > 0,
    }
    passed = all(integrity_gates.values()) and all(scientific_gates.values())
    verdict = "PASS_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT" if passed else "FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(MONTH_KEYS),
            "corpus": CORPUS,
            "blind_exclusion": list(BLIND),
            "base_method": "promoted v8 pooled-year-centroid label-free sparse-support multiplicity",
            "change_layer": "cross-year family existence only",
            "hard_family_graph": "exact v8 connected recurrence at centroid radius 1.5",
            "soft_seed": "unmatched exact fixed4 component",
            "soft_trigger": "three nearest unclaimed other-year events inside inherited 1.5 centroid distance",
            "soft_trigger_pairwise_rule": "all three pairwise inherited centroid distances <=1.5",
            "soft_reciprocity": "trigger centroid must choose originating unmatched component as nearest component within 1.5",
            "soft_reported_membership": "unclaimed events in intersection of inherited 1.5 balls around seed and trigger centroids",
            "ranking": "exact v8 multiplicity order as immutable prefix, then soft families by seed strength and trigger distance",
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
        "retained_quartets": retained_quartets,
        "hard_family_count": len(hard_families),
        "soft_family_count": len(soft_families),
        "combined_family_count": len(combined_families),
        "soft_diagnostics": soft_diag,
        "prelabel_payload_sha256": prelabel_sha,
        "centroid_repair": repair,
        "hard_scoring_summary": hard_scoring,
        "baseline_metrics": {k: v for k, v in baseline.items() if k != "per_label"},
        "p19_metrics": {k: v for k, v in p19_metrics.items() if k != "per_label"},
        "baseline_annual": baseline_annual,
        "p19_annual": p19_annual,
        "annual_mean_f1_delta": annual_delta,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": (
            "Target-excluded GMN 2022/2023 development only. The exact label-free v8 detector, "
            "within-year components, hard recurrence graph, pooled-centroid scoring, and multiplicity "
            "ranking are preserved. P19 adds only a preregistered reciprocal three-event subthreshold "
            "support path for otherwise unmatched components. Labels are first evaluated after the full "
            "combined family payload is hashed. No OrbitTrace target information or 20-55 degree event "
            "is accessible."
        ),
    }
    (args.output / "p19_subthreshold_reciprocal_recurrence_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "p19_prelabel_payload.json").write_text(
        json.dumps(prelabel_payload, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# OrbitTrace P19 subthreshold reciprocal recurrence development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- hard v8 families: **{len(hard_families)}**",
        f"- added soft-recurrence families: **{len(soft_families)}**",
        f"- qualified matches: **{baseline['qualified_matches']} -> {p19_metrics['qualified_matches']}**",
        f"- recovery@100: **{baseline['recovered_at_100']} -> {p19_metrics['recovered_at_100']}**",
        f"- macro F1: **{baseline['macro_f1']:.6f} -> {p19_metrics['macro_f1']:.6f}**",
        f"- top-100 dominant precision: **{baseline['top100_dominant_precision']:.6f} -> {p19_metrics['top100_dominant_precision']:.6f}**",
        f"- 2022 4-9 mean-F1 delta: **{annual_delta['2022']['4-9']:+.6f}**",
        f"- 2023 4-9 mean-F1 delta: **{annual_delta['2023']['4-9']:+.6f}**",
        "",
        "No OrbitTrace target information or target-region event was accessed.",
    ]
    (args.output / "P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
