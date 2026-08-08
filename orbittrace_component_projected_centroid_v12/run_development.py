#!/usr/bin/env python3
"""One-shot clean-room development of component-projected centroid v12."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from orbittrace_pooled_year_centroid_v8 import run_development as v8

ORIGINAL_REPAIR = v8.repair_year_centroids
V8_RECOVERY = 58
V8_PRECISION = 0.6884631112636006
V8_MRR = 0.045531138942766655
MIN_RECOVERY = 59
MIN_PRECISION = 0.68
EXPECTED_FAMILIES = 226
EXPECTED_FAMILY_YEARS = 452
EXPECTED_DUPLICATE_FAMILIES = 75
EXPECTED_DUPLICATE_FAMILY_YEARS = 118
EXPECTED_QUALIFIED = 95
EXPECTED_PERSISTENCE_RECOVERY = 59
REPRESENTATION_AUDIT_RUN = 31229695771
REPRESENTATION_AUDIT_ARTIFACT = 9013581721
REPRESENTATION_AUDIT_DIGEST = "sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def projected_repair(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    """Compute exact v8 pooled centers, then project each family-year to its nearest constituent component centroid."""
    pooled_diagnostics = ORIGINAL_REPAIR(families, components, scan_by_year, support, base)
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")

    projected_family_years = 0
    duplicate_family_years = 0
    duplicate_families: set[str] = set()
    projection_distances: list[float] = []
    single_component_distances: list[float] = []
    selected_component_ids: list[str] = []

    for family in families:
        family_id = str(family["family_id"])
        for year in v8.YEARS:
            key = str(year)
            pooled = dict(family["centroids"][key])
            year_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family_id} missing components for {year}")

            candidates: list[tuple[float, str, dict[str, Any]]] = []
            for component in year_components:
                component_id = str(component["component_id"])
                distance = float(support.centroid_distance(pooled, component["centroid"], base))
                require(math.isfinite(distance) and distance >= 0.0, "invalid pooled-to-component distance")
                candidates.append((distance, component_id, component))
            candidates.sort(key=lambda item: (item[0], item[1]))
            distance, component_id, selected = candidates[0]

            projected = {
                "sol": float(selected["centroid"]["sol"]),
                "sun_lon": float(selected["centroid"]["sun_lon"]),
                "ecl_lat": float(selected["centroid"]["ecl_lat"]),
                "vg": float(selected["centroid"]["vg"]),
            }
            family["centroids"][key] = projected
            selected_component_ids.append(component_id)
            projected_family_years += 1

            if len(year_components) == 1:
                single_component_distances.append(distance)
            else:
                duplicate_family_years += 1
                duplicate_families.add(family_id)
                projection_distances.append(distance)

    max_single = max(single_component_distances) if single_component_distances else 0.0
    max_projection = max(projection_distances) if projection_distances else 0.0
    require(projected_family_years == EXPECTED_FAMILY_YEARS, "family-year count changed")
    require(len(duplicate_families) == EXPECTED_DUPLICATE_FAMILIES, "duplicate-family count changed")
    require(duplicate_family_years == EXPECTED_DUPLICATE_FAMILY_YEARS, "duplicate-family-year count changed")
    require(max_single <= 1e-12, f"single-component projection diverged from v8: {max_single}")
    require(max_projection <= 1.5 + 1e-12, f"source-only geometry premise changed: nearest projected component beyond 1.5 ({max_projection})")

    return {
        **pooled_diagnostics,
        "projection_rule": "nearest existing same-year component centroid to exact v8 pooled centroid; ties stable component_id",
        "projection_uses_episode_scores": False,
        "projection_uses_labels": False,
        "projected_family_years": projected_family_years,
        "projected_duplicate_families": len(duplicate_families),
        "projected_duplicate_family_years": duplicate_family_years,
        "max_single_component_projection_distance": float(max_single),
        "duplicate_projection_distance_min": float(min(projection_distances)) if projection_distances else None,
        "duplicate_projection_distance_median": float(sorted(projection_distances)[len(projection_distances)//2]) if projection_distances else None,
        "duplicate_projection_distance_max": float(max_projection),
        "selected_component_ids_unique": len(set(selected_component_ids)),
        "all_projected_anchors_are_constituent_component_centroids": True,
    }


def main() -> int:
    args = v8.parse_args()

    # Freeze the only scientific change before v8 opens the target-excluded development catalogue.
    v8.repair_year_centroids = projected_repair
    v8.CORPUS = "orbittrace-component-projected-centroid-v12-development"

    rc = v8.main()
    require(rc == 0, "inherited v8 execution failed")

    source_path = args.output / "pooled_year_centroid_v8_development.json"
    result = json.loads(source_path.read_text())
    metrics = result["metrics"]
    projection = result["centroid_repair_diagnostics"]

    require(int(result["family_count"]) == EXPECTED_FAMILIES, "family count changed")
    require(int(result["qualified_known_showers"]) == EXPECTED_QUALIFIED, "qualified shower universe changed")
    require(int(metrics["label_free_persistence"]["recovered_at_100"]) == EXPECTED_PERSISTENCE_RECOVERY, "persistence baseline changed")
    require(int(projection["projected_family_years"]) == EXPECTED_FAMILY_YEARS, "projection family-year count changed")
    require(int(projection["projected_duplicate_family_years"]) == EXPECTED_DUPLICATE_FAMILY_YEARS, "projection duplicate count changed")

    multiplicity = metrics["multiplicity"]
    successor_gates = {
        "all_inherited_integrity_gates_pass": all(bool(v) for v in result["integrity_gates"].values()),
        "all_inherited_scientific_gates_pass": all(bool(v) for v in result["scientific_gates"].values()),
        "exact_family_count_226": int(result["family_count"]) == EXPECTED_FAMILIES,
        "exact_family_year_count_452": int(projection["projected_family_years"]) == EXPECTED_FAMILY_YEARS,
        "exact_duplicate_family_year_count_118": int(projection["projected_duplicate_family_years"]) == EXPECTED_DUPLICATE_FAMILY_YEARS,
        "exact_qualified_known_showers_95": int(result["qualified_known_showers"]) == EXPECTED_QUALIFIED,
        "persistence_recovery_exactly_59": int(metrics["label_free_persistence"]["recovered_at_100"]) == EXPECTED_PERSISTENCE_RECOVERY,
        "multiplicity_recovery_at_least_59": int(multiplicity["recovered_at_100"]) >= MIN_RECOVERY,
        "multiplicity_precision_at_least_068": float(multiplicity["top100_dominant_precision"]) >= MIN_PRECISION,
        "multiplicity_mrr_at_least_v8": float(multiplicity["mrr"]) >= V8_MRR - 1e-15,
        "all_local_episode_sizes_exact_128": result["family_scoring_summary"]["episode_sizes"] == [128],
        "single_component_projection_exact": float(projection["max_single_component_projection_distance"]) <= 1e-12,
        "all_projected_anchors_are_constituent_components": projection["all_projected_anchors_are_constituent_component_centroids"] is True,
        "projection_is_label_and_score_free": projection["projection_uses_labels"] is False and projection["projection_uses_episode_scores"] is False,
        "source_only_geometry_premise_preserved": float(projection["duplicate_projection_distance_max"]) <= 1.5 + 1e-12,
    }

    promoted = all(successor_gates.values())
    verdict = "PASS_COMPONENT_PROJECTED_CENTROID_V12_PROMOTE" if promoted else "FAIL_COMPONENT_PROJECTED_CENTROID_V12_NO_GO"

    result["verdict"] = verdict
    result["configuration"]["corpus"] = v8.CORPUS
    result["configuration"]["centroid_repair"] = "exact v8 pooled all-event centroid followed by deterministic nearest-constituent-component projection for episode anchoring"
    result["configuration"]["episode_centroid_rule"] = "single component: exact component centroid; duplicate same-year components: nearest existing component centroid to v8 pooled centroid, ties stable component_id"
    result["configuration"]["no_component_rule_search"] = True
    result["configuration"]["no_score_based_component_selection"] = True
    result["configuration"]["no_label_based_component_selection"] = True
    result["incumbent_v8_baseline"] = {
        "multiplicity_recovered_at_100": V8_RECOVERY,
        "multiplicity_top100_dominant_precision": V8_PRECISION,
        "multiplicity_mrr": V8_MRR,
    }
    result["representation_source_only_audit"] = {
        "run_id": REPRESENTATION_AUDIT_RUN,
        "artifact_id": REPRESENTATION_AUDIT_ARTIFACT,
        "artifact_zip_digest": REPRESENTATION_AUDIT_DIGEST,
        "labels_used": False,
        "target_region_accessed": False,
    }
    result["successor_gates"] = successor_gates
    result["claim_boundary"] = (
        "One-shot clean-room representation-layer successor on target-excluded GMN 2022-2023. "
        "The exact projection rule and promotion gates were frozen before label evaluation. "
        "Solar longitude 20-55 degrees was excluded by the inherited guarded parser before labels, proposals, scoring, or evaluation. "
        "No OrbitTrace target coordinates, members, family ranks, target-region events, Stage A output, or Stage B output were accessed."
    )

    output_json = args.output / "component_projected_centroid_v12_development.json"
    output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Component-projected centroid v12 development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- recurrent families: **{result['family_count']}**",
        f"- duplicate family-years projected: **{projection['projected_duplicate_family_years']}**",
        f"- multiplicity recovery@100: **{multiplicity['recovered_at_100']}** (v8: {V8_RECOVERY})",
        f"- multiplicity top-100 precision: **{float(multiplicity['top100_dominant_precision']):.6f}** (v8: {V8_PRECISION:.6f})",
        f"- multiplicity MRR: **{float(multiplicity['mrr']):.9f}** (v8: {V8_MRR:.9f})",
        f"- persistence recovery@100: **{metrics['label_free_persistence']['recovered_at_100']}**",
        f"- Brown recovery@100: **{metrics['brown']['recovered_at_100']}**",
        f"- v3 recovery@100: **{metrics['v3']['recovered_at_100']}**",
        "",
        "No OrbitTrace target information or 20°–55° target-region event entered development.",
    ]
    (args.output / "COMPONENT_PROJECTED_CENTROID_V12_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
