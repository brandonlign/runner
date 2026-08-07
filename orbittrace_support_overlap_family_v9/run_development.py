#!/usr/bin/env python3
"""One-shot development of parameter-free support-overlap recurrence v9."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v8.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-support-overlap-family-v9-development"
TOP_K = 100
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 72
MIN_PERSISTENCE_RECOVERY = 55
MIN_MULTIPLICITY_ABSOLUTE_RECOVERY = 54
MIN_V8_NONREGRESSION_RECOVERY = 58
BROWN_EQ_TOL = 1e-10
OLD_FIXED_RADIUS = 1.5
EXPECTED_V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"


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


def component_support_radii(
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[list[float], dict[str, Any]]:
    event_lookup = {
        year: {str(event["id"]): event for event in scan_by_year[year]}
        for year in YEARS
    }
    radii: list[float] = []
    event_counts: list[int] = []
    zero_count = 0
    radius_records: list[tuple[str, float, int]] = []

    for component in components:
        year = int(component["year"])
        require(year in event_lookup, f"unexpected component year {year}")
        event_ids = sorted(set(str(value) for value in component["event_ids"]))
        require(len(event_ids) == int(component["event_count"]), f"component {component['component_id']} event union changed")
        require(event_ids and all(event_id in event_lookup[year] for event_id in event_ids), f"component {component['component_id']} event lookup failed")
        distances = [
            float(support.centroid_distance(component["centroid"], event_lookup[year][event_id], base))
            for event_id in event_ids
        ]
        require(all(math.isfinite(value) and value >= 0.0 for value in distances), f"component {component['component_id']} has invalid member distance")
        radius = float(max(distances))
        require(math.isfinite(radius) and radius >= 0.0, f"component {component['component_id']} support radius invalid")
        radii.append(radius)
        event_counts.append(len(event_ids))
        if radius == 0.0:
            zero_count += 1
        radius_records.append((str(component["component_id"]), radius, len(event_ids)))

    digest_payload = json.dumps(radius_records, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    summary = {
        "component_count": len(components),
        "radius_count": len(radii),
        "all_component_events_used_exactly_once_per_unique_id": True,
        "zero_radius_components": zero_count,
        "radius_min": float(min(radii)) if radii else None,
        "radius_median": float(np.median(radii)) if radii else None,
        "radius_p95": float(np.quantile(radii, 0.95)) if radii else None,
        "radius_max": float(max(radii)) if radii else None,
        "component_event_count_min": int(min(event_counts)) if event_counts else None,
        "component_event_count_median": float(np.median(event_counts)) if event_counts else None,
        "component_event_count_max": int(max(event_counts)) if event_counts else None,
        "component_radius_records_sha256": hashlib.sha256(digest_payload).hexdigest(),
        "radius_definition": "max frozen centroid_distance over all unique component member events",
        "radius_multiplier": None,
        "radius_quantile": None,
    }
    return radii, summary


def build_support_overlap_families(
    components: list[dict[str, Any]],
    radii: list[float],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, Any]]:
    require(len(components) == len(radii), "component/radius length mismatch")
    adjacency: dict[int, set[int]] = {}
    total_cross_year_pairs = 0
    overlap_edges = 0
    old_fixed_edges = 0
    overlap_only_edges = 0
    old_only_edges = 0
    same_year_edges = 0
    max_overlap_margin = -math.inf
    min_overlap_margin = math.inf

    for i, left in enumerate(components):
        for j in range(i + 1, len(components)):
            right = components[j]
            if int(left["year"]) == int(right["year"]):
                continue
            total_cross_year_pairs += 1
            distance = float(support.centroid_distance(left["centroid"], right["centroid"], base))
            threshold = float(radii[i] + radii[j])
            require(math.isfinite(distance) and distance >= 0.0, "cross-year centroid distance invalid")
            require(math.isfinite(threshold) and threshold >= 0.0, "support-overlap threshold invalid")
            overlap = distance <= threshold
            old_fixed = distance <= OLD_FIXED_RADIUS
            margin = threshold - distance
            min_overlap_margin = min(min_overlap_margin, margin)
            max_overlap_margin = max(max_overlap_margin, margin)
            if overlap:
                adjacency.setdefault(i, set()).add(j)
                adjacency.setdefault(j, set()).add(i)
                overlap_edges += 1
            if old_fixed:
                old_fixed_edges += 1
            if overlap and not old_fixed:
                overlap_only_edges += 1
            if old_fixed and not overlap:
                old_only_edges += 1

    # By construction no same-year edge can be inserted; verify rather than assume.
    for i, neighbors in adjacency.items():
        for j in neighbors:
            if int(components[i]["year"]) == int(components[j]["year"]):
                same_year_edges += 1
    require(same_year_edges == 0, "same-year support-overlap edge created")

    seen: set[int] = set()
    families: list[dict[str, Any]] = []
    for start in range(len(components)):
        if start in seen or start not in adjacency:
            continue
        queue = deque([start])
        seen.add(start)
        members: list[int] = []
        while queue:
            idx = queue.popleft()
            members.append(idx)
            for nxt in sorted(adjacency[idx]):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        family_components = [components[index] for index in members]
        years = sorted({int(component["year"]) for component in family_components})
        if len(years) < int(support.MIN_FAMILY_YEARS):
            continue
        event_ids = sorted(set().union(*(set(component["event_ids"]) for component in family_components)))
        component_ids = sorted(str(component["component_id"]) for component in family_components)
        stable_id = "G" + hashlib.sha256("|".join(component_ids).encode()).hexdigest()[:12]
        year_strengths = {
            str(year): float(max(component["component_strength"] for component in family_components if int(component["year"]) == year))
            for year in years
        }
        family = {
            "family_id": stable_id,
            "years": years,
            "year_count": len(years),
            "component_ids": component_ids,
            "component_count": len(family_components),
            "event_ids": event_ids,
            "event_count": len(event_ids),
            "quartet_count": int(sum(component["quartet_count"] for component in family_components)),
            "anchor_count": int(sum(component["anchor_count"] for component in family_components)),
            "best_score": float(max(component["best_score"] for component in family_components)),
            "year_strengths": year_strengths,
            # Preserve exact v6 pre-repair semantics; v8 repair below recomputes duplicate-year centroids.
            "centroids": {str(component["year"]): component["centroid"] for component in family_components},
            "ranks": {},
        }
        family["ranking_scores"] = support.family_scores(family)
        families.append(family)

    require(len({str(family["family_id"]) for family in families}) == len(families), "family IDs not unique")
    rankings = support.rank_families(families)
    family_ids = {str(family["family_id"]) for family in families}
    require(set(str(value) for value in rankings["persistence"]) == family_ids, "persistence family universe mismatch")

    adjacency_audit = {
        "total_cross_year_pairs": total_cross_year_pairs,
        "support_overlap_edges": overlap_edges,
        "old_fixed_1p5_edges": old_fixed_edges,
        "support_overlap_only_edges": overlap_only_edges,
        "old_fixed_only_edges": old_only_edges,
        "same_year_direct_edges": same_year_edges,
        "adjacency_diff_edge_count": overlap_only_edges + old_only_edges,
        "support_overlap_condition": "centroid_distance <= radius_left + radius_right",
        "support_radius_definition": "max member-event centroid distance",
        "support_radius_multiplier": None,
        "support_radius_quantile": None,
        "minimum_pair_margin_threshold_minus_distance": float(min_overlap_margin) if total_cross_year_pairs else None,
        "maximum_pair_margin_threshold_minus_distance": float(max_overlap_margin) if total_cross_year_pairs else None,
        "all_cross_year_pairs_evaluated_exactly_once": True,
        "all_edges_and_nonedges_defined_by_single_closed_ball_rule": True,
    }
    return families, rankings, adjacency_audit


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v8_result_json.read_text())

    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False and source_audit["labels_enter_candidate_generation"] is False, "source blindness changed")
    require(predecessor["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 predecessor did not pass")
    require(all(predecessor["integrity_gates"].values()) and all(predecessor["scientific_gates"].values()), "v8 predecessor gates changed")
    require(int(predecessor["family_count"]) == 226, "v8 family baseline changed")
    require(int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]) == MIN_V8_NONREGRESSION_RECOVERY, "v8 multiplicity baseline changed")
    require(int(predecessor["metrics"]["brown"]["recovered_at_100"]) == 55, "v8 Brown baseline changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]) == 59, "v8 persistence baseline changed")

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
    require(abs(float(support.FAMILY_LINK_RADIUS) - OLD_FIXED_RADIUS) < 1e-15, "predecessor fixed-radius source changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == 64 and int(support.AUDIT_SHORTLIST_K) == 128, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal gates changed")
    for name in ("centroid_distance", "family_scores", "rank_families", "circular_mean_deg"):
        require(hasattr(support, name), f"support missing {name}")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    # FIRST DEVELOPMENT DATA ACCESS. Frozen parser removes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
    require([source["key"] for source in catalogue_sources] == list(MONTH_KEYS), "development monthly source set changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_counts: dict[str, int] = {}
    component_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        retained_counts[str(year)] = len(passing)
        component_counts[str(year)] = len(year_components)
        components.extend(year_components)
        print(f"support-overlap-v9 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    radii, radius_summary = component_support_radii(components, scan_by_year, support, base)
    families, support_rankings, adjacency_audit = build_support_overlap_families(components, radii, support, base)
    require(adjacency_audit["adjacency_diff_edge_count"] > 0, "support-overlap adjacency is vacuous relative to fixed 1.5")

    # Exact passed-v8 semantic repair, applied after v9 topology is frozen.
    pooled_audit = v8.repair_year_centroids(families, components, scan_by_year, support, base)
    persistence_order = [str(value) for value in support_rankings["persistence"]]

    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every family scored")
    rankings = {
        "multiplicity": mult.rank_scored(scored, "multiplicity"),
        "brown": mult.rank_scored(scored, "brown"),
        "v3": mult.rank_scored(scored, "v3"),
        "label_free_persistence": persistence_order,
    }
    family_ids = {str(family["family_id"]) for family in families}
    require(all(set(order) == family_ids and len(order) == len(family_ids) for order in rankings.values()), "ranking family universe mismatch")
    ranking_hashes = {
        name: hashlib.sha256(json.dumps(order, separators=(",", ":")).encode("utf-8")).hexdigest()
        for name, order in rankings.items()
    }

    # FIRST SHOWER-LABEL USE: components, radii, links, families, pooled centroids, scores, and rankings are frozen above.
    metrics_full = {name: mult.evaluate_order(hidden_labels, families, order) for name, order in rankings.items()}
    metrics = {name: compact(value) for name, value in metrics_full.items()}
    correlations = {
        "multiplicity_brown_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["brown"]),
        "multiplicity_v3_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["v3"]),
        "multiplicity_persistence_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["label_free_persistence"]),
    }
    top100_overlaps = {
        "multiplicity_brown": mult.overlap100(rankings["multiplicity"], rankings["brown"]),
        "multiplicity_v3": mult.overlap100(rankings["multiplicity"], rankings["v3"]),
        "multiplicity_persistence": mult.overlap100(rankings["multiplicity"], rankings["label_free_persistence"]),
    }

    qualified = int(metrics["multiplicity"]["qualified_matches"])
    same_qualified = len({int(value["qualified_matches"]) for value in metrics.values()}) == 1
    persistence_recovery = int(metrics["label_free_persistence"]["recovered_at_100"])
    multiplicity_recovery = int(metrics["multiplicity"]["recovered_at_100"])
    brown_recovery = int(metrics["brown"]["recovered_at_100"])
    required_vs_persistence = int(math.ceil(0.90 * persistence_recovery))

    exact_years = all(sorted(int(year) for year in family["years"]) == list(YEARS) for family in families)
    integrity_gates = {
        "frozen_v6_v8_sources_and_self_tests": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [source["key"] for source in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(audit["calibration_events_used"] == 0 and audit["source_labels_used_for_proposals"] is False for audit in scan_audits),
        "no_score_threshold_applied": all(audit["score_threshold_applied"] is False for audit in scan_audits),
        "at_least_24_scannable_bins_each_year": all(int(audit["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for audit in scan_audits),
        "all_component_support_radii_finite_nonnegative": int(radius_summary["radius_count"]) == len(components) and radius_summary["radius_min"] is not None and float(radius_summary["radius_min"]) >= 0.0,
        "all_unique_component_events_used_for_support_radius": radius_summary["all_component_events_used_exactly_once_per_unique_id"] is True,
        "all_edges_and_nonedges_exact_support_overlap_rule": adjacency_audit["all_cross_year_pairs_evaluated_exactly_once"] is True and adjacency_audit["all_edges_and_nonedges_defined_by_single_closed_ball_rule"] is True,
        "no_same_year_direct_edges": int(adjacency_audit["same_year_direct_edges"]) == 0,
        "support_overlap_adjacency_nonvacuous_vs_fixed15": int(adjacency_audit["adjacency_diff_edge_count"]) > 0,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "all_families_span_both_years": exact_years,
        "at_least_72_qualified_known_showers": qualified >= MIN_QUALIFIED and same_qualified,
        "v8_pooled_centroid_repair_semantics": pooled_audit["non_centroid_family_structure_unchanged"] is True and float(pooled_audit["max_single_component_centroid_distance"]) <= 1e-12,
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128] if families else False,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "rankings_frozen_before_first_label_use": len(ranking_hashes) == 4,
        "no_label_or_target_input_to_method": True,
    }
    scientific_gates = {
        "label_free_persistence_recovered_at_100_at_least_55": persistence_recovery >= MIN_PERSISTENCE_RECOVERY,
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_label_free_persistence": multiplicity_recovery >= required_vs_persistence,
        "multiplicity_recovered_at_100_at_least_54": multiplicity_recovery >= MIN_MULTIPLICITY_ABSOLUTE_RECOVERY,
        "multiplicity_top100_precision_at_least_050": float(metrics["multiplicity"]["top100_dominant_precision"]) >= 0.50,
        "multiplicity_nonregression_vs_passed_v8_at_least_58": multiplicity_recovery >= MIN_V8_NONREGRESSION_RECOVERY,
    }
    verdict = "PASS_SUPPORT_OVERLAP_FAMILY_V9_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_SUPPORT_OVERLAP_FAMILY_V9_DEVELOPMENT"

    family_sizes = [int(family["event_count"]) for family in families]
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "proposal_generator": "exact v6 label-free fixed4 structural proposals",
            "family_link_rule": "cross-year closed support-ball overlap",
            "component_support_radius": "maximum frozen-metric distance from component centroid to every unique component member event",
            "link_condition": "centroid_distance <= radius_left + radius_right",
            "radius_multiplier": None,
            "radius_quantile": None,
            "connected_family_closure": True,
            "same_year_components_allowed_via_cross_year_paths": True,
            "pooled_year_centroids": "exact passed-v8 union-of-unique-events repair",
            "centroid_statistic": pooled_audit["pooling_statistic"],
            "episode_size": 128,
            "primary_ranking": "worst-year multiplicity descending, geometric-mean multiplicity descending, family id",
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "top_k": TOP_K,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_radius_multiplier": True,
            "no_radius_quantile": True,
            "no_cap_search": True,
            "no_weight_search": True,
            "no_family_variant_search": True,
            "no_rrf": True,
            "no_source_labels_in_method": True,
        },
        "predecessor_v8": {
            "artifact_digest": EXPECTED_V8_ARTIFACT_DIGEST,
            "verdict": predecessor["verdict"],
            "family_count": int(predecessor["family_count"]),
            "multiplicity_recovered_at_100": int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]),
            "brown_recovered_at_100": int(predecessor["metrics"]["brown"]["recovered_at_100"]),
            "persistence_recovered_at_100": int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]),
        },
        "retained_quartet_counts": retained_counts,
        "component_counts": component_counts,
        "component_count_total": len(components),
        "support_radius_summary": radius_summary,
        "adjacency_audit": adjacency_audit,
        "family_count": len(families),
        "family_size_summary": {
            "min": int(min(family_sizes)) if family_sizes else None,
            "median": float(np.median(family_sizes)) if family_sizes else None,
            "p95": float(np.quantile(family_sizes, 0.95)) if family_sizes else None,
            "max": int(max(family_sizes)) if family_sizes else None,
        },
        "pooled_centroid_audit": pooled_audit,
        "family_scoring_summary": scoring_summary,
        "ranking_sha256_before_label_use": ranking_hashes,
        "metrics": metrics,
        "correlations": correlations,
        "top100_overlaps": top100_overlaps,
        "qualified_known_showers": qualified,
        "required_multiplicity_recovery_vs_persistence": required_vs_persistence,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": "Development-only support-overlap recurrence test on already-exposed target-excluded GMN 2022-2023. The 20-55 degree interval was removed before labels. Component support radii, cross-year links, connected families, pooled-year centroids, scores, and all rankings were frozen before known-shower labels were consulted. No OrbitTrace target information or target-region event entered the method.",
    }
    args.output.joinpath("support_overlap_family_v9_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("SUPPORT_OVERLAP_FAMILY_V9_DEVELOPMENT.md").write_text(
        "# Support-overlap family v9 development\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"- components 2022/2023: {component_counts.get('2022')} / {component_counts.get('2023')}\n"
        f"- support-overlap / old fixed-1.5 edges: {adjacency_audit['support_overlap_edges']} / {adjacency_audit['old_fixed_1p5_edges']}\n"
        f"- recurrent families: {len(families)}\n"
        f"- multiplicity / Brown / persistence recovery@100: {multiplicity_recovery} / {brown_recovery} / {persistence_recovery}\n"
        f"- multiplicity top-100 precision: {metrics['multiplicity']['top100_dominant_precision']:.6f}\n\n"
        "No OrbitTrace target information was accessed.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
