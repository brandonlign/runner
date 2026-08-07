#!/usr/bin/env python3
"""One-shot development of pooled-year-centroid v8 on target-excluded GMN 2022-2023."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-pooled-year-centroid-v8-development"
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 72
TOP_K = 100
MIN_PERSISTENCE_RECOVERY = 55
MIN_MULTIPLICITY_ABSOLUTE_RECOVERY = 54
BROWN_EQ_TOL = 1e-10
EXPECTED_V6_FAMILY_COUNT = 226
EXPECTED_V6_PERSISTENCE_RECOVERY = 59
EXPECTED_V6_QUALIFIED = 95
V6_ARTIFACT_DIGEST = "sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b"
CENTROID_AUDIT_ARTIFACT_DIGEST = "sha256:a1faacf51e1f4ca2a3a92b20e27d1f07f00e1d32ab33993916379ff36acea062"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--centroid-audit-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def structural_snapshot(family: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": str(family["family_id"]),
        "years": [int(x) for x in family["years"]],
        "year_count": int(family["year_count"]),
        "component_ids": list(family["component_ids"]),
        "component_count": int(family["component_count"]),
        "event_ids": list(family["event_ids"]),
        "event_count": int(family["event_count"]),
        "quartet_count": int(family["quartet_count"]),
        "anchor_count": int(family["anchor_count"]),
        "best_score": float(family["best_score"]),
        "year_strengths": dict(family["year_strengths"]),
        "ranking_scores": dict(family["ranking_scores"]),
        "ranks": dict(family["ranks"]),
    }


def pooled_centroid(events: list[dict[str, Any]], support: Any) -> dict[str, float]:
    require(events, "cannot pool empty event set")
    return {
        "sol": float(support.circular_mean_deg(float(e["sol"]) for e in events)),
        "sun_lon": float(support.circular_mean_deg(float(e["sun_lon"]) for e in events)),
        "ecl_lat": float(np.median([float(e["ecl_lat"]) for e in events])),
        "vg": float(np.median([float(e["vg"]) for e in events])),
    }


def repair_year_centroids(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")
    event_lookup = {
        year: {str(e["id"]): e for e in scan_by_year[year]}
        for year in YEARS
    }
    before = {str(f["family_id"]): structural_snapshot(f) for f in families}

    duplicate_family_count = 0
    duplicate_family_year_count = 0
    pooled_event_counts: list[int] = []
    single_component_distances: list[float] = []
    duplicate_component_distances: list[float] = []
    changed_duplicate_year_centroids = 0

    for family in families:
        pooled: dict[str, dict[str, float]] = {}
        has_duplicate = False
        for year in YEARS:
            year_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family['family_id']} missing components for {year}")
            if len(year_components) > 1:
                has_duplicate = True
                duplicate_family_year_count += 1
            year_event_ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
            require(year_event_ids, f"family {family['family_id']} {year} has no pooled events")
            require(all(eid in event_lookup[year] for eid in year_event_ids), "pooled event missing from target-excluded scan corpus")
            events = [event_lookup[year][eid] for eid in year_event_ids]
            center = pooled_centroid(events, support)
            pooled[str(year)] = center
            pooled_event_counts.append(len(events))

            if len(year_components) == 1:
                d = float(support.centroid_distance(center, year_components[0]["centroid"], base))
                single_component_distances.append(d)
            else:
                old = family["centroids"][str(year)]
                d = float(support.centroid_distance(center, old, base))
                duplicate_component_distances.append(d)
                if d > 1e-12:
                    changed_duplicate_year_centroids += 1

        if has_duplicate:
            duplicate_family_count += 1
        family["centroids"] = pooled

    after = {str(f["family_id"]): structural_snapshot(f) for f in families}
    require(before == after, "pooled-centroid repair changed non-centroid family structure")
    max_single = max(single_component_distances) if single_component_distances else 0.0
    require(max_single <= 1e-12, f"source-audited pooling failed single-component equivalence: {max_single}")
    require(duplicate_family_count > 0 and duplicate_family_year_count > 0, "centroid repair was vacuous")
    require(changed_duplicate_year_centroids > 0, "duplicate-year centroids never changed")

    return {
        "families_with_duplicate_same_year_components": duplicate_family_count,
        "duplicate_family_years": duplicate_family_year_count,
        "changed_duplicate_year_centroids": changed_duplicate_year_centroids,
        "single_component_family_years": len(single_component_distances),
        "max_single_component_centroid_distance": float(max_single),
        "duplicate_year_old_to_pooled_distance_median": float(np.median(duplicate_component_distances)) if duplicate_component_distances else None,
        "duplicate_year_old_to_pooled_distance_max": float(max(duplicate_component_distances)) if duplicate_component_distances else None,
        "pooled_event_count_min": int(min(pooled_event_counts)),
        "pooled_event_count_median": float(np.median(pooled_event_counts)),
        "pooled_event_count_max": int(max(pooled_event_counts)),
        "pooling_statistic": {
            "sol": "circular_mean_deg",
            "sun_lon": "circular_mean_deg",
            "ecl_lat": "median",
            "vg": "median",
        },
        "non_centroid_family_structure_unchanged": True,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    centroid_audit = json.loads(args.centroid_audit_json.read_text())

    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor did not pass")
    require(all(predecessor["integrity_gates"].values()) and all(predecessor["scientific_gates"].values()), "v6 predecessor gates changed")
    require(int(predecessor["family_count"]) == EXPECTED_V6_FAMILY_COUNT, "v6 family count changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]) == EXPECTED_V6_PERSISTENCE_RECOVERY, "v6 persistence recovery changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["qualified_matches"]) == EXPECTED_V6_QUALIFIED, "v6 qualified baseline changed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "centroid source audit did not pass")
    require(centroid_audit["support_source_sha256"] == source_audit["support_source_sha256"], "centroid audit support source mismatch")
    require(centroid_audit["catalogue_access"] is False and centroid_audit["scientific_value_access"] is False, "centroid audit crossed data boundary")
    require(centroid_audit["target_information_access"] is False, "centroid audit accessed target information")
    require("circular_mean_deg" in centroid_audit["component_records_called_names"], "source audit did not establish circular centroid statistic")
    require("median" in centroid_audit["component_records_called_names"], "source audit did not establish median centroid statistic")

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
    for name in ("feature_matrix", "exact_anchor_distances", "quartet_score", "component_records", "build_families", "centroid_distance", "circular_mean_deg"):
        require(hasattr(support, name), f"frozen support missing {name}")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    # FIRST DEVELOPMENT DATA ACCESS. The frozen parser removes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
    require([s["key"] for s in catalogue_sources] == list(MONTH_KEYS), "development monthly sources changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)
        print(f"pooled-centroid-v8 source year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    # Exact passed-v6 family graph and structural ranking are formed before the sole centroid repair.
    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(len(families) == EXPECTED_V6_FAMILY_COUNT, f"v6 family universe changed: {len(families)}")
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence family universe mismatch")
    repair = repair_year_centroids(families, components, scan_by_year, support, base)

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

    # FIRST SHOWER-LABEL USE: family graph, pooled centroids, scores, and rankings are frozen above.
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
    same_qualified = len({int(v["qualified_matches"]) for v in metrics.values()}) == 1
    persistence_recovery = int(metrics["label_free_persistence"]["recovered_at_100"])
    multiplicity_recovery = int(metrics["multiplicity"]["recovered_at_100"])
    brown_recovery = int(metrics["brown"]["recovered_at_100"])
    required_vs_persistence = int(math.ceil(0.90 * persistence_recovery))

    persistence_baseline_reproduced = (
        persistence_recovery == int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"])
        and int(metrics["label_free_persistence"]["qualified_matches"]) == int(predecessor["metrics"]["label_free_persistence"]["qualified_matches"])
        and int(metrics["label_free_persistence"]["recovered_at_500"]) == int(predecessor["metrics"]["label_free_persistence"]["recovered_at_500"])
        and abs(float(metrics["label_free_persistence"]["top100_dominant_precision"]) - float(predecessor["metrics"]["label_free_persistence"]["top100_dominant_precision"])) <= 1e-12
    )

    integrity_gates = {
        "frozen_source_v6_centroid_audit_and_self_tests": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_applied": all(a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits),
        "exact_v6_family_count_226": len(families) == EXPECTED_V6_FAMILY_COUNT,
        "v6_persistence_baseline_exactly_reproduced": persistence_baseline_reproduced,
        "centroid_repair_nonvacuous": int(repair["families_with_duplicate_same_year_components"]) > 0 and int(repair["changed_duplicate_year_centroids"]) > 0,
        "single_component_centroid_equivalence": float(repair["max_single_component_centroid_distance"]) <= 1e-12,
        "non_centroid_family_structure_unchanged": repair["non_centroid_family_structure_unchanged"] is True,
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128],
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "at_least_72_qualified_known_showers": qualified >= MIN_QUALIFIED and same_qualified,
    }
    scientific_gates = {
        "label_free_persistence_recovered_at_100_at_least_55": persistence_recovery >= MIN_PERSISTENCE_RECOVERY,
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_label_free_persistence": multiplicity_recovery >= required_vs_persistence,
        "multiplicity_recovered_at_100_at_least_54": multiplicity_recovery >= MIN_MULTIPLICITY_ABSOLUTE_RECOVERY,
        "multiplicity_top100_precision_at_least_050": float(metrics["multiplicity"]["top100_dominant_precision"]) >= 0.50,
    }
    verdict = "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_POOLED_YEAR_CENTROID_V8_DEVELOPMENT"

    family_sizes = [int(f["event_count"]) for f in families]
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "family_builder": "exact passed-v6 connected recurrent family graph",
            "centroid_repair": "per-family-year union of unique same-year component events",
            "centroid_statistic": repair["pooling_statistic"],
            "family_link_radius": 1.5,
            "primary_ranking": "worst-year multiplicity descending, geometric-mean multiplicity descending, family id",
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "episode_size": 128,
            "top_k": TOP_K,
            "no_source_labels_in_proposal_family_pooling_or_scoring": True,
            "no_calibration_threshold": True,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_cap_search": True,
            "no_weight_search": True,
            "no_pooling_rule_search": True,
            "no_rrf": True,
        },
        "predecessor": {
            "artifact_digest": V6_ARTIFACT_DIGEST,
            "verdict": predecessor["verdict"],
            "family_count": int(predecessor["family_count"]),
            "multiplicity_recovered_at_100": int(predecessor["metrics"]["multiplicity"]["recovered_at_100"]),
            "persistence_recovered_at_100": int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]),
            "qualified_matches": int(predecessor["metrics"]["multiplicity"]["qualified_matches"]),
        },
        "centroid_source_audit": {
            "artifact_digest": CENTROID_AUDIT_ARTIFACT_DIGEST,
            "verdict": centroid_audit["verdict"],
            "target_information_access": False,
        },
        "retained_quartet_counts": passing_counts,
        "family_count": len(families),
        "family_size_summary": {
            "min": min(family_sizes),
            "median": float(np.median(family_sizes)),
            "p95": float(np.quantile(family_sizes, 0.95)),
            "max": max(family_sizes),
        },
        "centroid_repair_diagnostics": repair,
        "family_scoring_summary": scoring_summary,
        "metrics": metrics,
        "correlations": correlations,
        "top100_overlaps": top100_overlaps,
        "qualified_known_showers": qualified,
        "required_multiplicity_recovery_vs_persistence": required_vs_persistence,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": "Development-only semantic repair on already-exposed target-excluded GMN 2022-2023. Labels were first consulted after exact v6 families, source-grounded pooled centroids, scores, and rankings were frozen. No OrbitTrace target information or 20-55 degree target-region event entered the method.",
    }
    args.output.joinpath("pooled_year_centroid_v8_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# Pooled-year-centroid v8 development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- families: {len(families)}",
        f"- duplicate same-year families repaired: {repair['families_with_duplicate_same_year_components']}",
        f"- multiplicity recovery@100: {multiplicity_recovery}",
        f"- Brown recovery@100: {brown_recovery}",
        f"- persistence recovery@100: {persistence_recovery}",
        f"- multiplicity top-100 precision: {metrics['multiplicity']['top100_dominant_precision']:.6f}",
        "",
        "No OrbitTrace target information was accessed.",
    ]
    args.output.joinpath("POOLED_YEAR_CENTROID_V8_DEVELOPMENT.md").write_text("\n".join(md) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
