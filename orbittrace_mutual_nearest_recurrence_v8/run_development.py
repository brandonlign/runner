#!/usr/bin/env python3
"""One-shot target-excluded development of mutual-nearest bottleneck-recurrence v8."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-mutual-nearest-bottleneck-v8-development"
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 72
TOP_K = 100
MIN_PRIMARY_RECOVERY = 55
MIN_PRIMARY_PRECISION = 0.50
BROWN_EQ_TOL = 1e-10
V6_ARTIFACT_DIGEST = "sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b"
V7_ARTIFACT_DIGEST = "sha256:98d6d4c729d2366eaf454b9f74c2d158493cd98fcdb5283b0bdb6a06889aac88"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--v7-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def nearest_maps(
    left: list[dict[str, Any]], right: list[dict[str, Any]], support: Any, base: Any
) -> tuple[dict[int, int], dict[int, int], dict[tuple[int, int], float], int]:
    radius = float(support.FAMILY_LINK_RADIUS)
    require(abs(radius - 1.5) < 1e-15, "family link radius changed")
    left_best: dict[int, tuple[float, str, int]] = {}
    right_best: dict[int, tuple[float, str, int]] = {}
    edge_distance: dict[tuple[int, int], float] = {}
    eligible_edges = 0
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            d = float(support.centroid_distance(a["centroid"], b["centroid"], base))
            require(math.isfinite(d) and d >= 0.0, "non-finite centroid distance")
            if d > radius + 1e-15:
                continue
            eligible_edges += 1
            edge_distance[(i, j)] = d
            candidate_left = (d, str(b["component_id"]), j)
            candidate_right = (d, str(a["component_id"]), i)
            if i not in left_best or candidate_left < left_best[i]:
                left_best[i] = candidate_left
            if j not in right_best or candidate_right < right_best[j]:
                right_best[j] = candidate_right
    return (
        {i: item[2] for i, item in left_best.items()},
        {j: item[2] for j, item in right_best.items()},
        edge_distance,
        eligible_edges,
    )


def build_mutual_nearest_families(
    components: list[dict[str, Any]], support: Any, base: Any
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, Any]]:
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
    left_best, right_best, edge_distance, eligible_edges = nearest_maps(left, right, support, base)

    reciprocal: list[tuple[int, int, float]] = []
    for i, j in sorted(left_best.items()):
        if right_best.get(j) == i:
            reciprocal.append((i, j, float(edge_distance[(i, j)])))
    reciprocal.sort(
        key=lambda item: (
            str(left[item[0]]["component_id"]),
            str(right[item[1]]["component_id"]),
        )
    )
    require(reciprocal, "no reciprocal nearest-neighbor recurrent pairs")
    require(len({i for i, _, _ in reciprocal}) == len(reciprocal), "left component reuse")
    require(len({j for _, j, _ in reciprocal}) == len(reciprocal), "right component reuse")

    families: list[dict[str, Any]] = []
    for i, j, distance in reciprocal:
        a, b = left[i], right[j]
        component_ids = [str(a["component_id"]), str(b["component_id"])]
        stable_id = "R" + hashlib.sha256("|".join(component_ids).encode()).hexdigest()[:12]
        event_ids = sorted(set(a["event_ids"]) | set(b["event_ids"]))
        family_components = [a, b]
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
            "year_strengths": {
                str(int(c["year"])): float(c["component_strength"]) for c in family_components
            },
            "centroids": {str(int(c["year"])): c["centroid"] for c in family_components},
            "link_distance": float(distance),
            "ranks": {},
        }
        family["ranking_scores"] = support.family_scores(family)
        families.append(family)

    families.sort(key=lambda f: str(f["family_id"]))
    # Only the two predeclared structural outputs are instantiated.
    support.RANKING_VARIANTS = ("persistence", "min_year_strength")
    rankings = support.rank_families(families)

    distances = [d for _, _, d in reciprocal]
    diagnostics = {
        "left_components": len(left),
        "right_components": len(right),
        "eligible_edges": eligible_edges,
        "left_components_with_eligible_edge": len(left_best),
        "right_components_with_eligible_edge": len(right_best),
        "reciprocal_pair_count": len(reciprocal),
        "link_radius": float(support.FAMILY_LINK_RADIUS),
        "mean_link_distance": float(np.mean(distances)),
        "median_link_distance": float(np.median(distances)),
        "max_link_distance": float(max(distances)),
        "one_component_per_year": all(f["component_count"] == 2 for f in families),
        "component_reuse": False,
        "association_rule": "reciprocal nearest eligible cross-year component; exact distance then stable component-id tie break",
    }
    return families, rankings, diagnostics


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    v6_result = json.loads(args.v6_result_json.read_text())
    v7_result = json.loads(args.v7_result_json.read_text())

    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "development source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(v6_result["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor changed")
    require(all(v6_result["integrity_gates"].values()) and all(v6_result["scientific_gates"].values()), "v6 predecessor gates changed")
    require(v7_result["verdict"] == "FAIL_ONE_TO_ONE_FAMILY_V7_DEVELOPMENT", "v7 no-go prerequisite changed")
    require(all(v7_result["integrity_gates"].values()), "v7 was not integrity-clean")
    require(v7_result["family_count"] == 533, "v7 preserved family count changed")
    require(v7_result["matching"]["assignment_cardinality"] == 533, "v7 preserved matching changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "min_year_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal gates changed")
    for name in ("centroid_distance", "family_scores", "rank_families"):
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
        print(f"mutual-v8 source year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, structural_rankings, association = build_mutual_nearest_families(components, support, base)
    primary_order = [str(x) for x in structural_rankings["min_year_strength"]]
    persistence_order = [str(x) for x in structural_rankings["persistence"]]
    family_ids = [str(f["family_id"]) for f in families]
    require(set(primary_order) == set(family_ids) and len(primary_order) == len(family_ids), "primary universe mismatch")
    require(set(persistence_order) == set(family_ids), "persistence universe mismatch")

    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every family scored")
    rankings = {
        "bottleneck_recurrence": primary_order,
        "persistence": persistence_order,
        "multiplicity": mult.rank_scored(scored, "multiplicity"),
        "brown": mult.rank_scored(scored, "brown"),
        "v3": mult.rank_scored(scored, "v3"),
    }

    # FIRST LABEL USE: all associations, structural rankings, episode scores, and comparator rankings are frozen above.
    metrics_full = {name: mult.evaluate_order(hidden_labels, families, order) for name, order in rankings.items()}
    metrics = {name: compact(value) for name, value in metrics_full.items()}
    qualified = int(metrics["bottleneck_recurrence"]["qualified_matches"])
    same_qualified = len({int(v["qualified_matches"]) for v in metrics.values()}) == 1
    primary_recovery = int(metrics["bottleneck_recurrence"]["recovered_at_100"])
    persistence_recovery = int(metrics["persistence"]["recovered_at_100"])

    all_component_ids = [cid for f in families for cid in f["component_ids"]]
    exact_semantics = all(
        f["component_count"] == 2
        and sorted(int(y) for y in f["years"]) == list(YEARS)
        and len(f["centroids"]) == 2
        and float(f["link_distance"]) <= 1.5 + 1e-15
        for f in families
    )
    no_reuse = len(all_component_ids) == len(set(all_component_ids))
    scannable = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
    exact_episode_sizes = scoring_summary["episode_sizes"] == [128] if families else False

    # Recompute reciprocity from the final component universe as an integrity check independent of family ids.
    left = sorted([c for c in components if int(c["year"]) == YEARS[0]], key=lambda c: str(c["component_id"]))
    right = sorted([c for c in components if int(c["year"]) == YEARS[1]], key=lambda c: str(c["component_id"]))
    left_best, right_best, _, _ = nearest_maps(left, right, support, base)
    expected_pairs = {(i, j) for i, j in left_best.items() if right_best.get(j) == i}
    actual_pairs = {
        (
            next(i for i, c in enumerate(left) if str(c["component_id"]) == f["component_ids"][0]),
            next(j for j, c in enumerate(right) if str(c["component_id"]) == f["component_ids"][1]),
        )
        for f in families
    }

    integrity_gates = {
        "frozen_source_v6_and_self_tests": True,
        "preserved_v7_no_go_integrity_clean": v7_result["verdict"] == "FAIL_ONE_TO_ONE_FAMILY_V7_DEVELOPMENT" and all(v7_result["integrity_gates"].values()),
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_applied": all(a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": scannable,
        "exact_reciprocal_nearest_pair_set": actual_pairs == expected_pairs,
        "exactly_one_component_per_year_per_family": exact_semantics,
        "no_component_reused_across_families": no_reuse,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "all_local_episode_sizes_exact_128": exact_episode_sizes,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "at_least_72_qualified_known_showers": qualified >= MIN_QUALIFIED and same_qualified,
    }
    scientific_gates = {
        "bottleneck_recurrence_recovered_at_100_at_least_55": primary_recovery >= MIN_PRIMARY_RECOVERY,
        "bottleneck_recurrence_top100_precision_at_least_050": float(metrics["bottleneck_recurrence"]["top100_dominant_precision"]) >= MIN_PRIMARY_PRECISION,
        "bottleneck_recurrence_recovers_at_least_plain_persistence": primary_recovery >= persistence_recovery,
    }
    verdict = "PASS_MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT"

    family_sizes = [int(f["event_count"]) for f in families]
    correlations = {
        "bottleneck_persistence_spearman": mult.rank_spearman(rankings["bottleneck_recurrence"], rankings["persistence"]),
        "bottleneck_multiplicity_spearman": mult.rank_spearman(rankings["bottleneck_recurrence"], rankings["multiplicity"]),
        "multiplicity_brown_spearman": mult.rank_spearman(rankings["multiplicity"], rankings["brown"]),
    }
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "proposal_generator": "exact passed label-free sparse-support v6",
            "family_builder": "reciprocal nearest eligible cross-year components",
            "family_link_radius": 1.5,
            "primary_ranking": "immutable support min_year_strength ranking (bottleneck recurrence)",
            "episode_size": 128,
            "top_k": TOP_K,
            "no_source_labels_in_proposal_association_or_ranking": True,
            "no_calibration_threshold": True,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_cap_search": True,
            "no_weight_search": True,
            "no_matching_variant_search": True,
            "no_ranking_variant_search": True,
            "no_rrf": True,
        },
        "predecessors": {
            "v6_verdict": v6_result["verdict"],
            "v6_artifact_digest": V6_ARTIFACT_DIGEST,
            "v7_verdict": v7_result["verdict"],
            "v7_artifact_digest": V7_ARTIFACT_DIGEST,
            "v7_family_count": int(v7_result["family_count"]),
            "v7_multiplicity_recovered_at_100": int(v7_result["metrics"]["multiplicity"]["recovered_at_100"]),
            "v7_persistence_recovered_at_100": int(v7_result["metrics"]["one_to_one_persistence"]["recovered_at_100"]),
        },
        "association": association,
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
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": "Development-only mutual-nearest recurrence successor on already-exposed target-excluded GMN 2022-2023 data. Labels were first consulted only after every association and ranking was frozen. No OrbitTrace target information or 20-55 degree target-region event entered the method.",
    }
    (args.output / "mutual_nearest_recurrence_v8_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# OrbitTrace mutual-nearest bottleneck-recurrence v8 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- eligible cross-year edges: **{association['eligible_edges']}**",
        f"- reciprocal nearest-neighbor families: **{len(families)}**",
        f"- qualified known showers: **{qualified}**",
        f"- bottleneck recurrence recovered@100: **{primary_recovery}**; precision: **{metrics['bottleneck_recurrence']['top100_dominant_precision']:.4f}**",
        f"- plain persistence recovered@100: **{persistence_recovery}**",
        f"- multiplicity / Brown / total-v3 recovered@100: **{metrics['multiplicity']['recovered_at_100']} / {metrics['brown']['recovered_at_100']} / {metrics['v3']['recovered_at_100']}**",
        f"- mean / median / max reciprocal link distance: **{association['mean_link_distance']:.4f} / {association['median_link_distance']:.4f} / {association['max_link_distance']:.4f}**",
        "",
        "Every family is an exact reciprocal-nearest cross-year pair under the unchanged radius 1.5. No source shower label entered proposal generation, association, structural ranking, episode scoring, or rank freezing. The 20°–55° target interval remained excluded before label access.",
    ]
    (args.output / "MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT.md").write_text("\n".join(md) + "\n")
    print("\n".join(md), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
