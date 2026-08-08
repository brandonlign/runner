#!/usr/bin/env python3
"""Source-only audit of v8 family-year representation on target-excluded GMN 2022-2023."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-family-year-representation-audit"
EXPECTED_FAMILIES = 226
FAMILY_LINK_RADIUS = 1.5


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def summary(values: list[float]) -> dict[str, float | int | None]:
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


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")

    mult = v6.mult
    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - FAMILY_LINK_RADIUS) < 1e-15, "family radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal gates changed")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 geometry changed")

    # FIRST AND ONLY SCIENTIFIC-VALUE ACCESS. The frozen parser removes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    # `hidden_labels` is intentionally never indexed, iterated, counted, normalized, or serialized in this audit.
    require(hidden_labels is not None, "parser label handle missing")
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    require([s["key"] for s in catalogue_sources] == list(MONTH_KEYS), "monthly source universe changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    for year in YEARS:
        audit, _passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        components.extend(year_components)

    families, _rankings = support.build_families(components, base)
    require(len(families) == EXPECTED_FAMILIES, f"family universe changed: {len(families)}")
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")
    event_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}

    component_counts: list[int] = []
    duplicate_counts: list[int] = []
    pooled_to_nearest: list[float] = []
    pooled_to_farthest: list[float] = []
    duplicate_spreads: list[float] = []
    pooled_outside_all_link_radius = 0
    duplicate_family_years = 0
    families_with_duplicate = 0

    for family in families:
        has_duplicate = False
        for year in YEARS:
            year_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family['family_id']} missing {year}")
            component_counts.append(len(year_components))
            if len(year_components) == 1:
                continue
            has_duplicate = True
            duplicate_family_years += 1
            duplicate_counts.append(len(year_components))

            year_event_ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
            require(all(eid in event_lookup[year] for eid in year_event_ids), "family-year event missing from target-excluded scan")
            pooled = v8.pooled_centroid([event_lookup[year][eid] for eid in year_event_ids], support)
            distances = [float(support.centroid_distance(pooled, c["centroid"], base)) for c in year_components]
            nearest = min(distances)
            farthest = max(distances)
            pooled_to_nearest.append(nearest)
            pooled_to_farthest.append(farthest)
            if nearest > FAMILY_LINK_RADIUS:
                pooled_outside_all_link_radius += 1

            spread = 0.0
            for i in range(len(year_components)):
                for j in range(i + 1, len(year_components)):
                    spread = max(
                        spread,
                        float(support.centroid_distance(year_components[i]["centroid"], year_components[j]["centroid"], base)),
                    )
            duplicate_spreads.append(spread)
        if has_duplicate:
            families_with_duplicate += 1

    result = {
        "verdict": "PASS_FAMILY_YEAR_REPRESENTATION_SOURCE_ONLY_AUDIT",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "family_count_expected": EXPECTED_FAMILIES,
            "family_link_radius_reference": FAMILY_LINK_RADIUS,
            "episode_centering_from_frozen_source": "build_local_episode uses family.centroids[year] as sol window center and full radiant-speed anchor, then selects the exact 128 smallest frozen wavelet-r2 events",
            "label_use": "none; hidden_labels handle returned by parser but never inspected",
        },
        "family_count": len(families),
        "family_year_count": len(families) * len(YEARS),
        "families_with_duplicate_same_year_components": families_with_duplicate,
        "duplicate_family_years": duplicate_family_years,
        "single_component_family_years": sum(1 for x in component_counts if x == 1),
        "component_count_all_family_years": summary([float(x) for x in component_counts]),
        "component_count_duplicate_family_years": summary([float(x) for x in duplicate_counts]),
        "pooled_to_nearest_constituent_component_distance": summary(pooled_to_nearest),
        "pooled_to_farthest_constituent_component_distance": summary(pooled_to_farthest),
        "constituent_component_pairwise_max_distance": summary(duplicate_spreads),
        "pooled_centroid_outside_every_constituent_1p5_neighborhood_count": pooled_outside_all_link_radius,
        "pooled_centroid_outside_every_constituent_1p5_neighborhood_fraction": (
            pooled_outside_all_link_radius / duplicate_family_years if duplicate_family_years else 0.0
        ),
        "interpretation_boundary": (
            "Geometry only. No shower labels, target-region events, OrbitTrace constants, family ranks, or benchmark outcomes are used. "
            "The 1.5 comparison is descriptive only because it is the already-frozen v8 family-link radius; it is not a tuned threshold."
        ),
        "integrity_gates": {
            "exact_target_excluded_2022_2023_panel": sorted(scan_by_year) == list(YEARS) and [s["key"] for s in catalogue_sources] == list(MONTH_KEYS),
            "exact_v8_family_count_226": len(families) == EXPECTED_FAMILIES,
            "no_label_dependent_calibration": all(a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False for a in scan_audits),
            "no_score_threshold": all(a["score_threshold_applied"] is False for a in scan_audits),
            "duplicate_representation_nonvacuous": duplicate_family_years > 0,
            "labels_not_used_by_audit_code": True,
        },
    }
    require(all(result["integrity_gates"].values()), "source-only audit integrity gate failed")
    args.output.joinpath("family_year_representation_source_only_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
