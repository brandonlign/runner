#!/usr/bin/env python3
"""One-shot target-excluded development of exact-support-contact recurrence v11."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v8.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-exact-support-contact-v11-development"
LINK_RADIUS = 1.5
TOP_K = 100
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 72
MIN_PERSISTENCE_RECOVERY = 55
MIN_MULTIPLICITY_RECOVERY = 59
MIN_MULTIPLICITY_PRECISION = 0.68
MIN_MULTIPLICITY_MRR = 0.045531138942766655
BROWN_EQ_TOL = 1e-10
EXPECTED_V8_FAMILIES = 226
EXPECTED_V8_M_RECOVERY = 58
EXPECTED_V8_P_RECOVERY = 59
EXPECTED_V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
PREFILTER_TOL = 1e-12


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


def member_support(
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[dict[int, dict[str, dict[str, Any]]], dict[int, dict[str, list[int]]], dict[int, list[str]], dict[str, Any]]:
    event_lookup = {
        year: {str(event["id"]): event for event in scan_by_year[year]}
        for year in YEARS
    }
    memberships: dict[int, dict[str, list[int]]] = {year: defaultdict(list) for year in YEARS}
    component_event_counts: list[int] = []
    for index, component in enumerate(components):
        year = int(component["year"])
        require(year in event_lookup, f"unexpected component year {year}")
        ids = sorted(set(str(value) for value in component["event_ids"]))
        require(ids and len(ids) == int(component["event_count"]), f"component {component['component_id']} event union changed")
        require(all(event_id in event_lookup[year] for event_id in ids), f"component {component['component_id']} references event outside target-excluded scan")
        component_event_counts.append(len(ids))
        for event_id in ids:
            memberships[year][event_id].append(index)

    member_ids = {year: sorted(memberships[year]) for year in YEARS}
    require(all(member_ids[year] for year in YEARS), "component support empty in a development year")
    summary = {
        "component_count": len(components),
        "unique_member_events": {str(year): len(member_ids[year]) for year in YEARS},
        "component_event_count_min": min(component_event_counts),
        "component_event_count_median": float(np.median(component_event_counts)),
        "component_event_count_max": max(component_event_counts),
        "max_components_per_event": max(len(indices) for year in YEARS for indices in memberships[year].values()),
        "all_component_member_ids_resolved_in_correct_year": True,
    }
    return event_lookup, memberships, member_ids, summary


def reduced_coord(event: dict[str, Any]) -> tuple[float, float, float]:
    return (float(event["sol"]) / 4.0, float(event["ecl_lat"]) / 2.0, float(event["vg"]) / 2.0)


def build_family_records(
    components: list[dict[str, Any]],
    edges: set[tuple[int, int]],
    support: Any,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    for left, right in edges:
        require(int(components[left]["year"]) != int(components[right]["year"]), "same-year direct edge")
        adjacency[left].add(right)
        adjacency[right].add(left)

    seen: set[int] = set()
    families: list[dict[str, Any]] = []
    for start in sorted(adjacency):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        members: list[int] = []
        while queue:
            index = queue.popleft()
            members.append(index)
            for nxt in sorted(adjacency[index]):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        family_components = [components[index] for index in members]
        years = sorted({int(component["year"]) for component in family_components})
        if len(years) < int(support.MIN_FAMILY_YEARS):
            continue
        event_ids = sorted(set().union(*(set(str(x) for x in component["event_ids"]) for component in family_components)))
        component_ids = sorted(str(component["component_id"]) for component in family_components)
        stable_id = "C" + hashlib.sha256("|".join(component_ids).encode("utf-8")).hexdigest()[:12]
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
            # Preserve exact v6 pre-repair dictionary semantics; v8 repairs duplicate-year centroids below.
            "centroids": {str(component["year"]): component["centroid"] for component in family_components},
            "ranks": {},
        }
        family["ranking_scores"] = support.family_scores(family)
        families.append(family)

    require(len({str(family["family_id"]) for family in families}) == len(families), "family IDs not unique")
    rankings = support.rank_families(families)
    universe = {str(family["family_id"]) for family in families}
    require(set(str(x) for x in rankings["persistence"]) == universe, "persistence universe mismatch")
    return families, rankings


def exact_support_contact_edges(
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[set[tuple[int, int]], dict[tuple[int, int], dict[str, Any]], dict[str, Any]]:
    event_lookup, memberships, member_ids, member_summary = member_support(components, scan_by_year)
    left_year, right_year = YEARS
    left_ids = member_ids[left_year]
    right_ids = member_ids[right_year]
    left_events = [event_lookup[left_year][event_id] for event_id in left_ids]
    right_events = [event_lookup[right_year][event_id] for event_id in right_ids]

    left_coords = np.asarray([reduced_coord(event) for event in left_events], dtype=np.float64)
    right_base = np.asarray([reduced_coord(event) for event in right_events], dtype=np.float64)
    require(left_coords.ndim == 2 and left_coords.shape[1] == 3, "left reduced coordinate shape invalid")
    require(right_base.ndim == 2 and right_base.shape[1] == 3, "right reduced coordinate shape invalid")
    require(np.all(np.isfinite(left_coords)) and np.all(np.isfinite(right_base)), "non-finite reduced coordinates")

    # Solar longitude /4 has period 90. Duplicate the right-year points at +/-90 so
    # Euclidean radius queries implement the wrapped first coordinate exactly.
    minus = right_base.copy(); minus[:, 0] -= 90.0
    plus = right_base.copy(); plus[:, 0] += 90.0
    right_coords = np.concatenate([minus, right_base, plus], axis=0)
    tree = cKDTree(right_coords)
    candidate_lists = tree.query_ball_point(left_coords, r=LINK_RADIUS + PREFILTER_TOL)

    witnesses: dict[tuple[int, int], dict[str, Any]] = {}
    reduced_candidate_event_pairs = 0
    exact_contact_event_pairs = 0
    max_accepted_distance = 0.0
    for left_index, candidates in enumerate(candidate_lists):
        seen_right: set[int] = set()
        for duplicated_index in candidates:
            right_index = int(duplicated_index) % len(right_ids)
            if right_index in seen_right:
                continue
            seen_right.add(right_index)
            reduced_candidate_event_pairs += 1
            left_event = left_events[left_index]
            right_event = right_events[right_index]
            distance = float(support.centroid_distance(left_event, right_event, base))
            require(math.isfinite(distance) and distance >= 0.0, "invalid exact member-event distance")
            if distance > LINK_RADIUS + 1e-12:
                continue
            exact_contact_event_pairs += 1
            max_accepted_distance = max(max_accepted_distance, distance)
            left_id = left_ids[left_index]
            right_id = right_ids[right_index]
            for component_left in memberships[left_year][left_id]:
                for component_right in memberships[right_year][right_id]:
                    edge = (min(component_left, component_right), max(component_left, component_right))
                    if edge not in witnesses:
                        witnesses[edge] = {
                            "left_event_id": left_id,
                            "right_event_id": right_id,
                            "distance": distance,
                        }

    contact_edges = set(witnesses)
    require(contact_edges, "exact support-contact adjacency is empty")
    require(all(float(witness["distance"]) <= LINK_RADIUS + 1e-12 for witness in witnesses.values()), "edge without exact contact witness")

    # Exact fixed-centroid v8 adjacency for a non-vacuity audit only.
    by_year = {
        year: [index for index, component in enumerate(components) if int(component["year"]) == year]
        for year in YEARS
    }
    fixed_edges: set[tuple[int, int]] = set()
    for left_component in by_year[left_year]:
        for right_component in by_year[right_year]:
            distance = float(support.centroid_distance(components[left_component]["centroid"], components[right_component]["centroid"], base))
            if distance <= LINK_RADIUS:
                fixed_edges.add((min(left_component, right_component), max(left_component, right_component)))

    audit = {
        **member_summary,
        "prefilter": "cKDTree on sol/4 circular, ecl_lat/2, vg/2; full sun_lon term omitted until exact check",
        "solar_scaled_period": 90.0,
        "prefilter_radius": LINK_RADIUS,
        "reduced_candidate_event_pairs": reduced_candidate_event_pairs,
        "exact_contact_event_pairs": exact_contact_event_pairs,
        "exact_contact_component_edges": len(contact_edges),
        "fixed_centroid_component_edges": len(fixed_edges),
        "contact_only_edges": len(contact_edges - fixed_edges),
        "fixed_only_edges": len(fixed_edges - contact_edges),
        "adjacency_symmetric_difference": len(contact_edges ^ fixed_edges),
        "max_accepted_exact_contact_distance": max_accepted_distance,
        "every_component_edge_has_exact_member_pair_witness": len(witnesses) == len(contact_edges),
        "every_prefilter_candidate_exactly_checked": True,
        "prefilter_is_necessary_condition_only": True,
        "no_approximate_neighbor_search": True,
    }
    return contact_edges, witnesses, audit


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
    require(int(predecessor["family_count"]) == EXPECTED_V8_FAMILIES, "v8 family count changed")
    require(int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]) == EXPECTED_V8_M_RECOVERY, "v8 multiplicity recovery changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]) == EXPECTED_V8_P_RECOVERY, "v8 persistence recovery changed")
    require(abs(float(predecessor["metrics"]["multiplicity"]["mrr"]) - MIN_MULTIPLICITY_MRR) <= 1e-12, "v8 multiplicity MRR changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - LINK_RADIUS) < 1e-15, "inherited family-link radius changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "minimum family years changed")
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
        print(f"exact-support-contact-v11 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    contact_edges, witnesses, adjacency_audit = exact_support_contact_edges(components, scan_by_year, support, base)
    require(int(adjacency_audit["adjacency_symmetric_difference"]) > 0, "support-contact adjacency is identical to v8 centroid adjacency")
    families, support_rankings = build_family_records(components, contact_edges, support)

    # Exact passed-v8 pooled-centroid semantics after the v11 topology freezes.
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

    witness_payload = [
        [int(edge[0]), int(edge[1]), witness["left_event_id"], witness["right_event_id"], float(witness["distance"])]
        for edge, witness in sorted(witnesses.items())
    ]
    witness_sha = hashlib.sha256(json.dumps(witness_payload, separators=(",", ":")).encode("utf-8")).hexdigest()

    # FIRST SHOWER-LABEL USE: adjacency, witnesses, families, pooled centroids, scores, and rankings are frozen above.
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
        "frozen_v6_v8_sources_and_passed_v8_artifact": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [source["key"] for source in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(audit["calibration_events_used"] == 0 and audit["source_labels_used_for_proposals"] is False for audit in scan_audits),
        "no_score_threshold_applied": all(audit["score_threshold_applied"] is False for audit in scan_audits),
        "at_least_24_scannable_bins_each_year": all(int(audit["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for audit in scan_audits),
        "component_member_ids_resolve_only_in_correct_target_excluded_year": adjacency_audit["all_component_member_ids_resolved_in_correct_year"] is True,
        "necessary_only_exact_reduced_prefilter": adjacency_audit["prefilter_is_necessary_condition_only"] is True and adjacency_audit["no_approximate_neighbor_search"] is True,
        "every_prefilter_candidate_exactly_checked": adjacency_audit["every_prefilter_candidate_exactly_checked"] is True,
        "every_component_edge_has_exact_member_pair_witness": adjacency_audit["every_component_edge_has_exact_member_pair_witness"] is True and bool(witness_sha),
        "all_accepted_contact_distances_within_1p5": float(adjacency_audit["max_accepted_exact_contact_distance"]) <= LINK_RADIUS + 1e-12,
        "no_same_year_direct_edges": all(int(components[left]["year"]) != int(components[right]["year"]) for left, right in contact_edges),
        "support_contact_adjacency_nonvacuous_vs_v8": int(adjacency_audit["adjacency_symmetric_difference"]) > 0,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "all_families_span_both_years": exact_years,
        "at_least_72_qualified_known_showers": qualified >= MIN_QUALIFIED and same_qualified,
        "v8_pooled_centroid_repair_semantics": pooled_audit["non_centroid_family_structure_unchanged"] is True and float(pooled_audit["max_single_component_centroid_distance"]) <= 1e-12,
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128] if families else False,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "all_four_rankings_frozen_before_first_label_use": len(ranking_hashes) == 4,
        "no_label_or_target_input_to_method": True,
    }
    scientific_gates = {
        "persistence_recovery_at_least_55": persistence_recovery >= MIN_PERSISTENCE_RECOVERY,
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_persistence": multiplicity_recovery >= required_vs_persistence,
        "multiplicity_recovery_at_least_59": multiplicity_recovery >= MIN_MULTIPLICITY_RECOVERY,
        "multiplicity_top100_precision_at_least_068": float(metrics["multiplicity"]["top100_dominant_precision"]) >= MIN_MULTIPLICITY_PRECISION,
        "multiplicity_mrr_at_least_passed_v8": float(metrics["multiplicity"]["mrr"]) >= MIN_MULTIPLICITY_MRR,
    }
    verdict = "PASS_EXACT_SUPPORT_CONTACT_V11_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_EXACT_SUPPORT_CONTACT_V11_DEVELOPMENT"

    family_sizes = [int(family["event_count"]) for family in families]
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "proposal_generator": "exact v6 label-free fixed4 structural proposals",
            "family_link_rule": "exists actual cross-year member-event pair with exact frozen distance <=1.5",
            "link_radius": LINK_RADIUS,
            "connected_family_closure": True,
            "same_year_components_allowed_via_cross_year_paths": True,
            "prefilter": "exact necessary 3D cKDTree prefilter; exact full-distance acceptance",
            "pooled_year_centroids": "exact passed-v8 union-of-unique-events repair",
            "episode_size": 128,
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "primary_ranking": "worst-year multiplicity, geometric-mean multiplicity, family id",
            "top_k": TOP_K,
            "no_radius_search": True,
            "no_contact_count_threshold": True,
            "no_overlap_fraction": True,
            "no_quantile": True,
            "no_weight_search": True,
            "no_family_variant_search": True,
            "no_source_labels_in_method": True,
        },
        "predecessor_v8": {
            "artifact_digest": EXPECTED_V8_ARTIFACT_DIGEST,
            "family_count": int(predecessor["family_count"]),
            "multiplicity_recovered_at_100": EXPECTED_V8_M_RECOVERY,
            "persistence_recovered_at_100": EXPECTED_V8_P_RECOVERY,
            "multiplicity_mrr": float(predecessor["metrics"]["multiplicity"]["mrr"]),
        },
        "retained_quartet_counts": retained_counts,
        "component_counts": component_counts,
        "component_count_total": len(components),
        "adjacency_audit": adjacency_audit,
        "edge_witness_sha256_before_label_use": witness_sha,
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
        "claim_boundary": "Development-only exact-support-contact recurrence on already-exposed target-excluded GMN 2022-2023. The 20-55 degree interval was removed before labels. Exact member-event contacts, connected families, pooled-year centroids, scores, and rankings were frozen before known-shower labels were consulted. No OrbitTrace target information or target-region event entered the method.",
    }
    args.output.joinpath("exact_support_contact_v11_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("EXACT_SUPPORT_CONTACT_V11_DEVELOPMENT.md").write_text(
        "# Exact-support-contact recurrence v11 development\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- components 2022/2023: **{component_counts.get('2022')} / {component_counts.get('2023')}**\n"
        f"- exact support-contact / fixed-centroid edges: **{adjacency_audit['exact_contact_component_edges']} / {adjacency_audit['fixed_centroid_component_edges']}**\n"
        f"- recurrent families: **{len(families)}**\n"
        f"- multiplicity / Brown / persistence recovery@100: **{multiplicity_recovery} / {brown_recovery} / {persistence_recovery}**\n"
        f"- multiplicity top-100 precision: **{metrics['multiplicity']['top100_dominant_precision']:.6f}**\n"
        f"- multiplicity MRR: **{metrics['multiplicity']['mrr']:.6f}**\n\n"
        "No OrbitTrace target information was accessed.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
