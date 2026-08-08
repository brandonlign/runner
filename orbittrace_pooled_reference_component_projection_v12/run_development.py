#!/usr/bin/env python3
"""One-shot target-excluded development of pooled-reference nearest-component projection v12."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-pooled-reference-component-projection-v12-development"
TOP_K = 100
MIN_SCANNABLE_BINS = 24
BROWN_EQ_TOL = 1e-10
EXPECTED_FAMILY_COUNT = 226
EXPECTED_QUALIFIED = 95
EXPECTED_PERSISTENCE_RECOVERY = 59
EXPECTED_DUPLICATE_FAMILY_YEARS = 118
EXPECTED_DUPLICATE_FAMILIES = 75
EXPECTED_SINGLE_FAMILY_YEARS = 334
MIN_MULTIPLICITY_RECOVERY = 59
MIN_MULTIPLICITY_PRECISION = 0.68
V8_MRR_BASELINE = 0.045531138942766655
V8_PRECISION_BASELINE = 0.6884631112636006
V8_RECOVERY_BASELINE = 58
V8_BROWN_RECOVERY = 55
V8_V3_RECOVERY = 55
V6_ARTIFACT_DIGEST = "sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b"
CENTROID_AUDIT_ARTIFACT_DIGEST = "sha256:a1faacf51e1f4ca2a3a92b20e27d1f07f00e1d32ab33993916379ff36acea062"
V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
REPRESENTATION_AUDIT_ARTIFACT_DIGEST = "sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--centroid-audit-json", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--representation-audit-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def float_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "median": None, "p90": None, "p95": None, "max": None}
    a = np.asarray(values, dtype=float)
    return {
        "count": int(a.size),
        "min": float(np.min(a)),
        "median": float(np.median(a)),
        "p90": float(np.quantile(a, 0.90)),
        "p95": float(np.quantile(a, 0.95)),
        "max": float(np.max(a)),
    }


def projected_scoring_centroids(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    representation_audit: dict[str, Any],
) -> dict[str, Any]:
    """Use exact v8 pooled reference, projected deterministically to nearest constituent component centroid."""
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")
    event_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}
    before = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}

    duplicate_family_years = 0
    families_with_duplicate = 0
    single_family_years = 0
    changed_vs_pooled = 0
    pooled_to_selected: list[float] = []
    single_pool_to_component: list[float] = []
    selection_records: list[str] = []

    for family in families:
        centers: dict[str, dict[str, float]] = {}
        family_has_duplicate = False
        for year in YEARS:
            year_components = sorted(
                [
                    component_by_id[str(cid)]
                    for cid in family["component_ids"]
                    if int(component_by_id[str(cid)]["year"]) == year
                ],
                key=lambda c: str(c["component_id"]),
            )
            require(year_components, f"family {family['family_id']} missing components for {year}")
            year_event_ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
            require(year_event_ids, f"family {family['family_id']} {year} has no family-year events")
            require(all(eid in event_lookup[year] for eid in year_event_ids), "family-year event missing from target-excluded scan corpus")
            pooled = v8.pooled_centroid([event_lookup[year][eid] for eid in year_event_ids], support)

            candidates = [
                (
                    float(support.centroid_distance(pooled, component["centroid"], base)),
                    str(component["component_id"]),
                    component,
                )
                for component in year_components
            ]
            selected_distance, selected_id, selected_component = min(candidates, key=lambda row: (row[0], row[1]))
            selected_centroid = {
                "sol": float(selected_component["centroid"]["sol"]),
                "sun_lon": float(selected_component["centroid"]["sun_lon"]),
                "ecl_lat": float(selected_component["centroid"]["ecl_lat"]),
                "vg": float(selected_component["centroid"]["vg"]),
            }
            centers[str(year)] = selected_centroid
            selection_records.append(f"{family['family_id']}|{year}|{selected_id}|{selected_distance:.17g}")

            if len(year_components) == 1:
                single_family_years += 1
                single_pool_to_component.append(selected_distance)
                require(selected_id == str(year_components[0]["component_id"]), "single-component projection selected wrong component")
            else:
                family_has_duplicate = True
                duplicate_family_years += 1
                pooled_to_selected.append(selected_distance)
                if selected_distance > 1e-12:
                    changed_vs_pooled += 1
                # The chosen center must be literally one of the constituent component centers.
                require(any(selected_id == str(c["component_id"]) for c in year_components), "selected center is not a constituent component")
                min_distance = min(row[0] for row in candidates)
                require(abs(selected_distance - min_distance) <= 1e-15, "projection did not choose minimum pooled-reference distance")
                tied_ids = sorted(row[1] for row in candidates if abs(row[0] - min_distance) <= 1e-15)
                require(selected_id == tied_ids[0], "projection tie break is not stable component ID")

        if family_has_duplicate:
            families_with_duplicate += 1
        family["centroids"] = centers

    after = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}
    require(before == after, "v12 representation changed non-centroid family structure")
    max_single = max(single_pool_to_component) if single_pool_to_component else 0.0
    require(max_single <= 1e-12, f"single-component family-year changed from v8: {max_single}")
    require(duplicate_family_years == EXPECTED_DUPLICATE_FAMILY_YEARS, "duplicate family-year count changed")
    require(families_with_duplicate == EXPECTED_DUPLICATE_FAMILIES, "duplicate family count changed")
    require(single_family_years == EXPECTED_SINGLE_FAMILY_YEARS, "single family-year count changed")

    audit_nearest = representation_audit["pooled_to_nearest_constituent_component_distance"]
    computed = float_summary(pooled_to_selected)
    require(int(audit_nearest["count"]) == int(computed["count"]), "source-only audit nearest-distance count mismatch")
    require(abs(float(audit_nearest["median"]) - float(computed["median"])) <= 1e-12, "source-only audit nearest-distance median mismatch")
    require(abs(float(audit_nearest["max"]) - float(computed["max"])) <= 1e-12, "source-only audit nearest-distance max mismatch")
    require(float(computed["max"]) <= 1.5 + 1e-12, "selected constituent lies beyond inherited 1.5 reference radius")

    selection_digest = hashlib.sha256("\n".join(selection_records).encode("utf-8")).hexdigest()
    return {
        "families_with_duplicate_same_year_components": families_with_duplicate,
        "duplicate_family_years": duplicate_family_years,
        "single_component_family_years": single_family_years,
        "changed_duplicate_family_year_centers_vs_v8_pooled_reference": changed_vs_pooled,
        "max_single_component_pool_to_component_distance": float(max_single),
        "pooled_reference_to_selected_component_distance": computed,
        "selection_digest_sha256": selection_digest,
        "selection_rule": "minimum exact frozen centroid distance from exact v8 pooled family-year reference to constituent same-year component centroid; stable component-id tie break",
        "selection_uses_labels": False,
        "selection_uses_scores": False,
        "all_selected_centers_are_constituent_component_centroids": True,
        "non_centroid_family_structure_unchanged": True,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    centroid_audit = json.loads(args.centroid_audit_json.read_text())
    v8_result = json.loads(args.v8_result_json.read_text())
    representation_audit = json.loads(args.representation_audit_json.read_text())

    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor did not pass")
    require(int(predecessor["family_count"]) == EXPECTED_FAMILY_COUNT, "v6 family count changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["recovered_at_100"]) == EXPECTED_PERSISTENCE_RECOVERY, "v6 persistence changed")
    require(int(predecessor["metrics"]["label_free_persistence"]["qualified_matches"]) == EXPECTED_QUALIFIED, "v6 qualified count changed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "component centroid audit did not pass")
    require(centroid_audit["catalogue_access"] is False and centroid_audit["scientific_value_access"] is False, "component centroid audit crossed value boundary")
    require(centroid_audit["target_information_access"] is False, "component centroid audit accessed target information")
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 baseline did not pass")
    require(int(v8_result["family_count"]) == EXPECTED_FAMILY_COUNT, "v8 family count changed")
    require(int(v8_result["metrics"]["multiplicity"]["recovered_at_100"]) == V8_RECOVERY_BASELINE, "v8 recovery baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["top100_dominant_precision"]) - V8_PRECISION_BASELINE) <= 1e-15, "v8 precision baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["mrr"]) - V8_MRR_BASELINE) <= 1e-15, "v8 MRR baseline changed")
    require(representation_audit["verdict"] == "PASS_FAMILY_YEAR_REPRESENTATION_SOURCE_ONLY_AUDIT", "representation source-only audit did not pass")
    require(int(representation_audit["family_count"]) == EXPECTED_FAMILY_COUNT, "representation audit family count changed")
    require(int(representation_audit["duplicate_family_years"]) == EXPECTED_DUPLICATE_FAMILY_YEARS, "representation audit duplicate count changed")
    require(int(representation_audit["families_with_duplicate_same_year_components"]) == EXPECTED_DUPLICATE_FAMILIES, "representation audit duplicate-family count changed")
    require(representation_audit["configuration"]["label_use"].startswith("none"), "representation audit used labels")

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

    # FIRST DEVELOPMENT DATA ACCESS. The frozen parser removes solar longitude 20-55 before labels.
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
        print(f"v12 source year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    # Exact promoted-v8 family topology and structural persistence order.
    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(len(families) == EXPECTED_FAMILY_COUNT, f"v8 family universe changed: {len(families)}")
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence family universe mismatch")

    representation = projected_scoring_centroids(
        families, components, scan_by_year, support, base, representation_audit
    )

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

    # Freeze all label-free representation/scoring/ranking products BEFORE FIRST SHOWER-LABEL USE.
    ranking_bytes = (json.dumps(rankings, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ranking_sha256 = hashlib.sha256(ranking_bytes).hexdigest()
    args.output.joinpath("v12_rankings_prelabel.json").write_bytes(ranking_bytes)
    args.output.joinpath("v12_representation_prelabel.json").write_text(json.dumps(representation, indent=2, sort_keys=True) + "\n")

    # FIRST SHOWER-LABEL USE. No architecture, center, score, or ranking can change after this line.
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
    multiplicity_recovery = int(metrics["multiplicity"]["recovered_at_100"])
    multiplicity_precision = float(metrics["multiplicity"]["top100_dominant_precision"])
    multiplicity_mrr = float(metrics["multiplicity"]["mrr"])
    persistence_recovery = int(metrics["label_free_persistence"]["recovered_at_100"])
    brown_recovery = int(metrics["brown"]["recovered_at_100"])
    v3_recovery = int(metrics["v3"]["recovered_at_100"])
    required_vs_persistence = int(math.ceil(0.90 * persistence_recovery))

    persistence_baseline_reproduced = (
        persistence_recovery == EXPECTED_PERSISTENCE_RECOVERY
        and int(metrics["label_free_persistence"]["qualified_matches"]) == EXPECTED_QUALIFIED
        and int(metrics["label_free_persistence"]["recovered_at_500"]) == int(predecessor["metrics"]["label_free_persistence"]["recovered_at_500"])
        and abs(float(metrics["label_free_persistence"]["top100_dominant_precision"]) - float(predecessor["metrics"]["label_free_persistence"]["top100_dominant_precision"])) <= 1e-12
    )

    integrity_gates = {
        "frozen_source_predecessors_audits_and_self_tests": True,
        "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
        "zero_label_dependent_calibration_events": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_applied": all(a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits),
        "exact_v8_family_count_226": len(families) == EXPECTED_FAMILY_COUNT,
        "exact_qualified_family_membership_universe_95": qualified == EXPECTED_QUALIFIED and same_qualified,
        "v8_persistence_baseline_exactly_reproduced": persistence_baseline_reproduced,
        "exact_duplicate_family_year_count_118": int(representation["duplicate_family_years"]) == EXPECTED_DUPLICATE_FAMILY_YEARS,
        "exact_duplicate_family_count_75": int(representation["families_with_duplicate_same_year_components"]) == EXPECTED_DUPLICATE_FAMILIES,
        "single_component_family_years_exact_v8": int(representation["single_component_family_years"]) == EXPECTED_SINGLE_FAMILY_YEARS and float(representation["max_single_component_pool_to_component_distance"]) <= 1e-12,
        "all_selected_centers_are_constituent_components": representation["all_selected_centers_are_constituent_component_centroids"] is True,
        "projection_uses_no_labels_or_scores": representation["selection_uses_labels"] is False and representation["selection_uses_scores"] is False,
        "non_centroid_family_structure_unchanged": representation["non_centroid_family_structure_unchanged"] is True,
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128],
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "prelabel_ranking_frozen": len(ranking_sha256) == 64,
    }
    scientific_gates = {
        "multiplicity_recovered_at_100_at_least_59": multiplicity_recovery >= MIN_MULTIPLICITY_RECOVERY,
        "multiplicity_top100_precision_at_least_068": multiplicity_precision >= MIN_MULTIPLICITY_PRECISION,
        "multiplicity_mrr_at_least_v8": multiplicity_mrr + 1e-15 >= V8_MRR_BASELINE,
        "persistence_recovered_at_100_exactly_59": persistence_recovery == EXPECTED_PERSISTENCE_RECOVERY,
        "brown_recovered_at_100_at_least_55": brown_recovery >= V8_BROWN_RECOVERY,
        "v3_recovered_at_100_at_least_55": v3_recovery >= V8_V3_RECOVERY,
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_persistence": multiplicity_recovery >= required_vs_persistence,
    }
    verdict = (
        "PASS_POOLED_REFERENCE_COMPONENT_PROJECTION_V12_DEVELOPMENT"
        if all(integrity_gates.values()) and all(scientific_gates.values())
        else "FAIL_POOLED_REFERENCE_COMPONENT_PROJECTION_V12_DEVELOPMENT"
    )

    family_sizes = [int(f["event_count"]) for f in families]
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "corpus": CORPUS,
            "family_builder": "exact promoted-v8 connected multi-component family topology",
            "semantic_family_year_reference": "exact v8 pooled centroid from union of unique same-year family-component events",
            "scoring_center": "constituent same-year component centroid nearest the pooled reference in exact frozen centroid distance; stable component-id tie break",
            "family_link_radius": 1.5,
            "episode_size": 128,
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "primary_ranking": "worst-year multiplicity descending, geometric-mean multiplicity descending, family id",
            "top_k": TOP_K,
            "one_successor_only": True,
            "no_label_based_candidate_selection": True,
            "no_threshold_search": True,
            "no_radius_search": True,
            "no_cap_search": True,
            "no_weight_search": True,
            "no_score_fusion": True,
            "no_representation_search": True,
        },
        "predecessor_artifacts": {
            "v6_digest": V6_ARTIFACT_DIGEST,
            "component_centroid_audit_digest": CENTROID_AUDIT_ARTIFACT_DIGEST,
            "v8_digest": V8_ARTIFACT_DIGEST,
            "representation_source_only_audit_digest": REPRESENTATION_AUDIT_ARTIFACT_DIGEST,
        },
        "v8_baseline": {
            "multiplicity_recovered_at_100": V8_RECOVERY_BASELINE,
            "multiplicity_top100_dominant_precision": V8_PRECISION_BASELINE,
            "multiplicity_mrr": V8_MRR_BASELINE,
            "persistence_recovered_at_100": EXPECTED_PERSISTENCE_RECOVERY,
            "brown_recovered_at_100": V8_BROWN_RECOVERY,
            "v3_recovered_at_100": V8_V3_RECOVERY,
        },
        "retained_quartet_counts": passing_counts,
        "family_count": len(families),
        "family_size_summary": {
            "min": min(family_sizes),
            "median": float(np.median(family_sizes)),
            "p95": float(np.quantile(family_sizes, 0.95)),
            "max": max(family_sizes),
        },
        "representation_diagnostics": representation,
        "family_scoring_summary": scoring_summary,
        "pre_label_ranking_sha256": ranking_sha256,
        "metrics": metrics,
        "correlations": correlations,
        "top100_overlaps": top100_overlaps,
        "qualified_known_showers": qualified,
        "required_multiplicity_recovery_vs_persistence": required_vs_persistence,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "decision": (
            "PROVISIONALLY_PROMOTE_V12_AND_BENCHMARK_WITHOUT_RETUNING"
            if verdict.startswith("PASS_")
            else "PERMANENT_NO_GO_V12_PRESERVE_V8_AS_FINAL_ARCHITECTURE"
        ),
        "claim_boundary": (
            "One-shot target-excluded GMN 2022-2023 representation-layer development. The 20-55 degree interval was removed by the frozen parser before method access. "
            "Families, projected centers, scores, and rankings were frozen before known-shower labels were evaluated. No OrbitTrace target information, target-region event, benchmark outcome, or reveal artifact entered method selection."
        ),
    }
    args.output.joinpath("pooled_reference_component_projection_v12_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v12_families.json.gz").write_bytes(gzip.compress(json.dumps(families, separators=(",", ":")).encode("utf-8")))
    args.output.joinpath("v12_scores.json.gz").write_bytes(gzip.compress(json.dumps(scored, separators=(",", ":")).encode("utf-8")))
    args.output.joinpath("v12_evaluation.json.gz").write_bytes(gzip.compress(json.dumps(metrics_full, separators=(",", ":")).encode("utf-8")))
    lines = [
        "# OrbitTrace pooled-reference nearest-component projection v12 development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- families: {len(families)}",
        f"- duplicate family-years projected: {representation['duplicate_family_years']}",
        f"- multiplicity recovery@100: {multiplicity_recovery}",
        f"- multiplicity precision@100: {multiplicity_precision:.9f}",
        f"- multiplicity MRR: {multiplicity_mrr:.12f}",
        f"- persistence recovery@100: {persistence_recovery}",
        f"- Brown recovery@100: {brown_recovery}",
        f"- v3 recovery@100: {v3_recovery}",
        f"- decision: {result['decision']}",
        "",
        "No OrbitTrace target information or target-region event was accessed.",
    ]
    args.output.joinpath("POOLED_REFERENCE_COMPONENT_PROJECTION_V12_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
