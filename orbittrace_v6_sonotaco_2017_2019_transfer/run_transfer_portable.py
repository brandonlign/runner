#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import numpy as np

from orbittrace_v6_sonotaco_2017_2019_transfer import run_transfer as transfer
from orbittrace_v6_sonotaco_2017_2019_transfer.parallel_exact_rescore import install as install_parallel_exact

_ORIGINAL_LOAD_MODULE = transfer.load_module
_PARALLEL_EXECUTION: dict[str, Any] | None = None


def portable_repair_year_centroids(v8: Any):
    def repair_year_centroids(
        families: list[dict[str, Any]],
        components: list[dict[str, Any]],
        scan_by_year: dict[int, list[dict[str, Any]]],
        support: Any,
        base: Any,
    ) -> dict[str, Any]:
        component_by_id = {str(c["component_id"]): c for c in components}
        transfer.require(len(component_by_id) == len(components), "component IDs not unique")
        event_lookup = {
            year: {str(e["id"]): e for e in scan_by_year[year]}
            for year in transfer.YEARS
        }
        before = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}

        duplicate_family_count = 0
        duplicate_family_year_count = 0
        pooled_event_counts: list[int] = []
        single_component_distances: list[float] = []
        duplicate_component_distances: list[float] = []
        changed_duplicate_year_centroids = 0

        for family in families:
            pooled: dict[str, dict[str, float]] = {}
            has_duplicate = False
            for year in transfer.YEARS:
                year_components = [
                    component_by_id[str(cid)]
                    for cid in family["component_ids"]
                    if int(component_by_id[str(cid)]["year"]) == year
                ]
                transfer.require(year_components, f"family {family['family_id']} missing components for {year}")
                if len(year_components) > 1:
                    has_duplicate = True
                    duplicate_family_year_count += 1
                year_event_ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
                transfer.require(year_event_ids, f"family {family['family_id']} {year} has no pooled events")
                transfer.require(all(eid in event_lookup[year] for eid in year_event_ids), "pooled event missing from target-excluded transfer corpus")
                events = [event_lookup[year][eid] for eid in year_event_ids]
                center = v8.pooled_centroid(events, support)
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

        after = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}
        transfer.require(before == after, "pooled-centroid repair changed non-centroid family structure")
        max_single = max(single_component_distances) if single_component_distances else 0.0
        transfer.require(max_single <= 1e-12, f"pooling failed single-component equivalence: {max_single}")
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
            "development_only_nonvacuity_assertions_imported": False,
        }

    return repair_year_centroids


def guarded_load_module(path, name):
    global _PARALLEL_EXECUTION
    module = _ORIGINAL_LOAD_MODULE(path, name)
    if name == "orbittrace_transfer_current_v6":
        _PARALLEL_EXECUTION = install_parallel_exact(module, workers=4, min_parallel_records=256)
        print(f"V6_TRANSFER_PARALLEL_EXECUTOR {_PARALLEL_EXECUTION}", flush=True)
    elif name == "orbittrace_transfer_true_v8":
        module.repair_year_centroids = portable_repair_year_centroids(module)
    return module


def main() -> int:
    transfer.load_module = guarded_load_module
    try:
        return int(transfer.main())
    finally:
        transfer.load_module = _ORIGINAL_LOAD_MODULE


if __name__ == "__main__":
    raise SystemExit(main())
