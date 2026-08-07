#!/usr/bin/env python3
"""One-shot development of the one-component-per-year family layer v7."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-one-to-one-family-v7-development"
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 72
TOP_K = 100
MIN_PERSISTENCE_RECOVERY = 55
MIN_MULTIPLICITY_ABSOLUTE_RECOVERY = 54
BROWN_EQ_TOL = 1e-10
V6_RESULT_DIGEST = "sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def hopcroft_karp_cardinality(adjacency: list[list[int]], n_right: int) -> int:
    """Independent deterministic maximum-cardinality bipartite matching size."""
    n_left = len(adjacency)
    pair_left = [-1] * n_left
    pair_right = [-1] * n_right
    distance = [0] * n_left
    inf = n_left + n_right + 1

    def bfs() -> bool:
        q: deque[int] = deque()
        found = False
        for u in range(n_left):
            if pair_left[u] < 0:
                distance[u] = 0
                q.append(u)
            else:
                distance[u] = inf
        while q:
            u = q.popleft()
            for v in adjacency[u]:
                mate = pair_right[v]
                if mate < 0:
                    found = True
                elif distance[mate] == inf:
                    distance[mate] = distance[u] + 1
                    q.append(mate)
        return found

    def dfs(u: int) -> bool:
        for v in adjacency[u]:
            mate = pair_right[v]
            if mate < 0 or (distance[mate] == distance[u] + 1 and dfs(mate)):
                pair_left[u] = v
                pair_right[v] = u
                return True
        distance[u] = inf
        return False

    matching = 0
    while bfs():
        for u in range(n_left):
            if pair_left[u] < 0 and dfs(u):
                matching += 1
    return matching


def build_one_to_one_families(
    components: list[dict[str, Any]], support: Any, base: Any
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, Any]]:
    radius = float(support.FAMILY_LINK_RADIUS)
    require(abs(radius - 1.5) < 1e-15, "family link radius changed")
    left = sorted(
        [c for c in components if int(c["year"]) == YEARS[0]],
        key=lambda c: str(c["component_id"]),
    )
    right = sorted(
        [c for c in components if int(c["year"]) == YEARS[1]],
        key=lambda c: str(c["component_id"]),
    )
    require(len(left) + len(right) == len(components), "unexpected component year")
    require(left and right, "empty component side")

    adjacency: list[list[int]] = [[] for _ in left]
    edge_distance: dict[tuple[int, int], float] = {}
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            d = float(support.centroid_distance(a["centroid"], b["centroid"], base))
            require(math.isfinite(d) and d >= 0.0, "non-finite centroid distance")
            if d <= radius + 1e-15:
                adjacency[i].append(j)
                edge_distance[(i, j)] = d
        adjacency[i].sort(key=lambda j: (edge_distance[(i, j)], str(right[j]["component_id"])))

    maximum_cardinality = hopcroft_karp_cardinality(adjacency, len(right))
    require(maximum_cardinality > 0, "no eligible recurrent component pairs")

    # Lexicographic objective encoded as assignment:
    # every eligible real-real match replaces two unmatched penalties, so cardinality is maximized first;
    # with cardinality fixed, the sum of real-real centroid distances is minimized.
    n_left, n_right = len(left), len(right)
    size = n_left + n_right
    unmatched_penalty = radius + 1.0
    invalid_cost = float((size + 1) * unmatched_penalty * 1000.0)
    cost = np.full((size, size), invalid_cost, dtype=np.float64)
    for (i, j), d in edge_distance.items():
        cost[i, j] = d
    for i in range(n_left):
        cost[i, n_right + i] = unmatched_penalty
    for j in range(n_right):
        cost[n_left + j, j] = unmatched_penalty
    cost[n_left:, n_right:] = 0.0

    row_ind, col_ind = linear_sum_assignment(cost)
    matches: list[tuple[int, int, float]] = []
    for row, col in zip(row_ind.tolist(), col_ind.tolist()):
        if row < n_left and col < n_right and (row, col) in edge_distance:
            matches.append((row, col, edge_distance[(row, col)]))
    matches.sort(key=lambda item: (str(left[item[0]]["component_id"]), str(right[item[1]]["component_id"])))
    require(len(matches) == maximum_cardinality, "assignment did not achieve maximum cardinality")

    used_left = {i for i, _, _ in matches}
    used_right = {j for _, j, _ in matches}
    require(len(used_left) == len(matches) and len(used_right) == len(matches), "component reuse in matching")

    families: list[dict[str, Any]] = []
    for i, j, distance in matches:
        a, b = left[i], right[j]
        require(int(a["year"]) != int(b["year"]), "same-year family pair")
        component_ids = sorted([str(a["component_id"]), str(b["component_id"])])
        stable_id = "M" + hashlib.sha256("|".join(component_ids).encode()).hexdigest()[:12]
        family_components = [a, b]
        event_ids = sorted(set(a["event_ids"]) | set(b["event_ids"]))
        year_strengths = {
            str(int(c["year"])): float(c["component_strength"]) for c in family_components
        }
        family = {
            "family_id": stable_id,
            "years": list(YEARS),
            "year_count": 2,
            "component_ids": component_ids,
            "component_count": 2,
            "event_ids": event_ids,
            "event_count": len(event_ids),
            "quartet_count": int(sum(int(c["quartet_count"]) for c in family_components)),
            "anchor_count": int(sum(int(c["anchor_count"]) for c in family_components)),
            "best_score": float(max(float(c["best_score"]) for c in family_components)),
            "year_strengths": year_strengths,
            "centroids": {str(int(c["year"])): c["centroid"] for c in family_components},
            "link_distance": float(distance),
            "ranks": {},
        }
        family["ranking_scores"] = support.family_scores(family)
        families.append(family)

    families.sort(key=lambda f: str(f["family_id"]))
    rankings = support.rank_families(families)
    diagnostics = {
        "left_components": n_left,
        "right_components": n_right,
        "eligible_edges": len(edge_distance),
        "independent_maximum_cardinality": maximum_cardinality,
        "assignment_cardinality": len(matches),
        "unmatched_2022_components": n_left - len(matches),
        "unmatched_2023_components": n_right - len(matches),
        "unmatched_penalty": unmatched_penalty,
        "link_radius": radius,
        "total_link_distance": float(sum(d for _, _, d in matches)),
        "mean_link_distance": float(np.mean([d for _, _, d in matches])) if matches else None,
        "max_link_distance": float(max(d for _, _, d in matches)) if matches else None,
        "one_component_per_year": all(f["component_count"] == 2 and f["years"] == list(YEARS) for f in families),
        "component_reuse": False,
    }
    return families, rankings, diagnostics


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor did not pass")
    require(all(predecessor["integrity_gates"].values()) and all(predecessor["scientific_gates"].values()), "v6 predecessor gates changed")

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
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal gates changed")
    for name in ("feature_matrix", "exact_anchor_distances", "quartet_score", "component_records", "centroid_distance", "family_scores", "rank_families"):
        require(hasattr(support, name), f"frozen support missing {name}")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "candidate scale changed")

    # FIRST DEVELOPMENT DATA ACCESS. Frozen parser removes 20-55 before label normalization.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development years changed")
    require([s["key"] for s in catalogue_sources] == list(MONTH_KEYS), "development monthly sources changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_quartets: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        retained_quartets[str(year)] = len(passing)
        components.extend(year_components)
        print(f"one-to-one-v7 source year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings, matching = build_one_to_one_families(components, support, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    family_ids = [str(f["family_id"]) for f in families]
    require(set(persistence_order) == set(family_ids) and len(persistence_order) == len(family_ids), "persistence universe mismatch")

    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every family scored")
    rankings = {
        "multiplicity": mult.rank_scored(scored, "multiplicity"),
        "brown": mult.rank_scored(scored, "brown"),
        "v3": mult.rank_scored(scored, "v3"),
        "one_to_one_persistence": persistence_order,
    }

    # FIRST LABEL USE: candidate generation, one-to-one matching, scoring, and rankings are frozen above.
    metrics_full = {name: mult.evaluate_order(hidden_labels, families, order) for name, order in rankings.items()}
    metrics = {name: compact(value) for name, value in metrics_full.items()}
    correlations = {
        "multiplicity_brown_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["brown"]),
        "multiplicity_v3_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["v3"]),
        "multiplicity_persistence_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["one_to_one_persistence"]),
    }
    top100_overlaps = {
        "multiplicity_brown": mult.overlap100(rankings["multiplicity"], rankings["brown"]),
        "multiplicity_v3": mult.overlap100(rankings["multiplicity"], rankings["v3"]),
        "multiplicity_persistence": mult.overlap100(rankings["multiplicity"], rankings["one_to_one_persistence"]),
    }

    qualified = int(metrics["multiplicity"]["qualified_matches"])
    same_qualified = len({int(v["qualified_matches"]) for v in metrics.values()}) == 1
    persistence_recovery = int(metrics["one_to_one_persistence"]["recovered_at_100"])
    multiplicity_recovery = int(metrics["multiplicity"]["recovered_at_100"])
    brown_recovery = int(metrics["brown"]["recovered_at_100"])
    required_vs_persistence = int(math.ceil(0.90 * persistence_recovery))

    all_component_ids = [cid for f in families for cid in f["component_ids"]]
    exact_semantics = all(
        f["component_count"] == 2
        and sorted(int(y) for y in f["years"]) == list(YEARS)
        and len(f["centroids"]) == 2
        for f in families
    )
    no_reuse = len(all_component_ids) == len(set(all_component_ids))
    link_distances_valid = all(float(f["link_distance"]) <= 1.5 + 1e-15 for f in families)
    scannable = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
    exact_episode_sizes = scoring_summary["episode_sizes"] == [128] if families else False

    integrity_gates = {
        "frozen_source_v6_and_self_tests": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_applied": all(a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": scannable,
        "matching_cardinality_independently_maximal": matching["assignment_cardinality"] == matching["independent_maximum_cardinality"],
        "exactly_one_component_per_year_per_family": exact_semantics,
        "no_component_reused_across_families": no_reuse,
        "all_link_distances_within_frozen_1_5_radius": link_distances_valid,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "all_local_episode_sizes_exact_128": exact_episode_sizes,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "at_least_72_qualified_known_showers": qualified >= MIN_QUALIFIED and same_qualified,
    }
    scientific_gates = {
        "one_to_one_persistence_recovered_at_100_at_least_55": persistence_recovery >= MIN_PERSISTENCE_RECOVERY,
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_one_to_one_persistence": multiplicity_recovery >= required_vs_persistence,
        "multiplicity_recovered_at_100_at_least_54": multiplicity_recovery >= MIN_MULTIPLICITY_ABSOLUTE_RECOVERY,
        "multiplicity_top100_precision_at_least_050": float(metrics["multiplicity"]["top100_dominant_precision"]) >= 0.50,
    }
    verdict = "PASS_ONE_TO_ONE_FAMILY_V7_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_ONE_TO_ONE_FAMILY_V7_DEVELOPMENT"

    family_sizes = [int(f["event_count"]) for f in families]
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "proposal_generator": "exact passed label-free sparse-support v6",
            "family_builder": "maximum-cardinality then minimum-total-distance one-to-one bipartite matching",
            "family_link_radius": 1.5,
            "unmatched_penalty_definition": "FAMILY_LINK_RADIUS + 1",
            "first_shortlist": v6.FIRST_SHORTLIST,
            "audit_shortlist": v6.AUDIT_SHORTLIST,
            "min_anchor_count": v6.MIN_ANCHOR_COUNT,
            "max_quartets_per_bin": v6.MAX_QUARTETS_PER_BIN,
            "primary_ranking": "worst-year multiplicity descending, geometric-mean multiplicity descending, family id",
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "episode_size": 128,
            "top_k": TOP_K,
            "no_source_labels_in_proposal_or_matching": True,
            "no_calibration_threshold": True,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_cap_search": True,
            "no_weight_search": True,
            "no_matching_variant_search": True,
            "no_rrf": True,
        },
        "predecessor": {
            "verdict": predecessor["verdict"],
            "artifact_digest": V6_RESULT_DIGEST,
            "v6_family_count": int(predecessor["family_count"]),
            "v6_multiplicity_recovered_at_100": int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]),
        },
        "matching": matching,
        "family_count": len(families),
        "qualified_known_showers": qualified,
        "retained_quartet_counts": retained_quartets,
        "scan_audits": scan_audits,
        "family_scoring_summary": scoring_summary,
        "family_size_summary": {
            "min": min(family_sizes) if family_sizes else None,
            "median": float(np.median(family_sizes)) if family_sizes else None,
            "p95": float(np.quantile(family_sizes, 0.95)) if family_sizes else None,
            "max": max(family_sizes) if family_sizes else None,
        },
        "metrics": metrics,
        "correlations": correlations,
        "top100_overlaps": top100_overlaps,
        "required_multiplicity_recovery_vs_persistence": required_vs_persistence,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": "Development-only correction of cross-year family semantics on already-exposed target-excluded GMN 2022-2023 data. Labels were first consulted after all one-to-one families and rankings were frozen. No OrbitTrace target information or 20-55 degree target-region event entered the method.",
    }
    (args.output / "one_to_one_family_v7_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# OrbitTrace one-to-one family v7 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- eligible cross-year component edges: **{matching['eligible_edges']}**",
        f"- independent maximum matching / assignment cardinality: **{matching['independent_maximum_cardinality']} / {matching['assignment_cardinality']}**",
        f"- recurrent one-to-one families: **{len(families)}**",
        f"- qualified known showers: **{qualified}**",
        f"- one-to-one persistence recovered@100: **{persistence_recovery}**; precision: **{metrics['one_to_one_persistence']['top100_dominant_precision']:.4f}**",
        f"- multiplicity recovered@100: **{multiplicity_recovery}**; precision: **{metrics['multiplicity']['top100_dominant_precision']:.4f}**",
        f"- Brown recovered@100: **{brown_recovery}**",
        f"- total-v3 recovered@100: **{metrics['v3']['recovered_at_100']}**",
        f"- mean / max matched centroid distance: **{matching['mean_link_distance']:.4f} / {matching['max_link_distance']:.4f}**",
        "",
        "No component is reused and every family contains exactly one component from each development year. No source shower label entered proposal generation, family matching, episode scoring, or ranking. The 20°–55° target interval remained excluded before label access.",
    ]
    (args.output / "ONE_TO_ONE_FAMILY_V7_DEVELOPMENT.md").write_text("\n".join(md) + "\n")
    print("\n".join(md), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
