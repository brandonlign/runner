#!/usr/bin/env python3
"""One-shot component-centroid cross-year membership expansion on exact frozen v8."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

V2_RUN = 31234638558
V2_ARTIFACT = 9015207416
V2_ARTIFACT_DIGEST = "sha256:b16a01a154cd43c0a6e6f8af2f013d9ee35260757f6178366f0b2a3643436219"
V2_SOURCE_COMMIT = "5a3cf9b9a4b3b7bc08570cb7346ec1cfce9f5fd0"

_CAPTURED_COMPONENTS: list[dict[str, Any]] = []
_ORIGINAL_SCAN_YEAR = v1.v6.label_free_scan_year


def capture_scan_year(*args: Any, **kwargs: Any):
    audit, passing, components = _ORIGINAL_SCAN_YEAR(*args, **kwargs)
    _CAPTURED_COMPONENTS.extend(copy.deepcopy(components))
    return audit, passing, components


def crossfit_expand_component_centroid(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    v1.require(_CAPTURED_COMPONENTS, "component capture is empty")
    component_by_id = {str(c["component_id"]): c for c in _CAPTURED_COMPONENTS}
    v1.require(len(component_by_id) == len(_CAPTURED_COMPONENTS), "captured component IDs are not unique")

    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        "radius": v1.RADIUS,
        "solar_prefilter_deg": v1.SOL_PREFILTER,
        "support_unit": "frozen source-year component centroid",
        "component_centroids_refit": False,
        "event_level_witness_multiplicity_used": False,
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "source_component_count_min_by_year": {},
        "source_component_count_median_by_year": {},
        "source_component_count_max_by_year": {},
        "assigned_min_component_distance_median_by_year": {},
        "assigned_min_component_distance_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "component_ids_from_frozen_family_graph_only": True,
    }

    for target_year in v1.YEARS:
        source_year = v1.YEARS[1] if target_year == v1.YEARS[0] else v1.YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events])

        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str]] = {}
        eligible_pairs = 0
        source_component_counts: list[int] = []

        for family in families:
            fid = str(family["family_id"])
            source_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == source_year
            ]
            v1.require(source_components, f"family {fid} lacks source-year components")
            source_component_counts.append(len(source_components))
            centers = [dict(c["centroid"]) for c in source_components]
            v1.require(
                all(all(k in center for k in ("sol", "sun_lon", "ecl_lat", "vg")) for center in centers),
                f"family {fid} component centroid schema changed",
            )

            mask = v1.in_expanded_arc(target_sol, [float(c["sol"]) for c in centers])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            distances = v1.min_exact_distances(candidates, centers)

            for i, distance in zip(idx.tolist(), distances.tolist()):
                if float(distance) > v1.RADIUS + 1e-12:
                    continue
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                eligible_pairs += 1
                cand = (float(distance), fid)
                old = best.get(event_id)
                if old is None or cand < old:
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_distances: list[float] = []
        for eid, (distance, fid) in best.items():
            by_family[fid].append(eid)
            assigned_distances.append(float(distance))

        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["eligible_family_event_pairs_by_year"][str(target_year)] = eligible_pairs
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, eligible_pairs - len(best))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)
        diagnostics["source_component_count_min_by_year"][str(target_year)] = int(min(source_component_counts))
        diagnostics["source_component_count_median_by_year"][str(target_year)] = float(np.median(source_component_counts))
        diagnostics["source_component_count_max_by_year"][str(target_year)] = int(max(source_component_counts))
        diagnostics["assigned_min_component_distance_median_by_year"][str(target_year)] = (
            float(np.median(assigned_distances)) if assigned_distances else None
        )
        diagnostics["assigned_min_component_distance_max_by_year"][str(target_year)] = (
            float(max(assigned_distances)) if assigned_distances else None
        )

    for before, after in zip(
        sorted(families, key=lambda x: str(x["family_id"])),
        sorted(expanded, key=lambda x: str(x["family_id"])),
    ):
        v1.require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in (
            "years", "year_count", "component_ids", "component_count", "quartet_count",
            "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids",
        ):
            v1.require(before[field] == after[field], f"expansion changed frozen family field {field}")
        v1.require(set(before["event_ids"]).issubset(set(after["event_ids"])), "seed membership lost")

    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = v1.sha256_json(
        {str(f["family_id"]): f["event_ids"] for f in expanded}
    )
    return expanded, diagnostics, assignments


def main() -> int:
    _CAPTURED_COMPONENTS.clear()
    v1.v6.label_free_scan_year = capture_scan_year
    v1.crossfit_expand = crossfit_expand_component_centroid
    v1.CORPUS = "orbittrace-cross-year-component-centroid-expansion-v3-development"
    rc = v1.main()

    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "other-year frozen v8 component-centroid support within exact inherited distance <=1.5; exclusive nearest-family assignment",
        "support_unit": "frozen source-year component centroid",
        "component_centroids_refit": False,
        "event_level_witness_multiplicity": False,
        "component_support_threshold_search": False,
        "v2_predecessor_run": V2_RUN,
        "v2_predecessor_artifact": V2_ARTIFACT,
        "v2_predecessor_artifact_digest": V2_ARTIFACT_DIGEST,
        "v2_source_commit": V2_SOURCE_COMMIT,
    })
    result["integrity_gates"]["component_centroid_support_only"] = (
        result["expansion_diagnostics"]["support_unit"] == "frozen source-year component centroid"
        and result["expansion_diagnostics"]["component_centroids_refit"] is False
    )
    result["integrity_gates"]["event_level_witness_multiplicity_removed"] = (
        result["expansion_diagnostics"]["event_level_witness_multiplicity_used"] is False
    )
    result["integrity_gates"]["component_ids_from_frozen_family_graph_only"] = (
        result["expansion_diagnostics"]["component_ids_from_frozen_family_graph_only"] is True
    )
    result["claim_boundary"] = (
        "Target-excluded v3 development only. The exact v8 family universe and ranking were frozen first. "
        "The sole successor change collapses redundant other-year seed-event witnesses to the already-existing "
        "frozen v8 component centroids before membership assignment. No OrbitTrace target information, target-region "
        "event, Stage A/B output, component-support threshold search, radius search, or literature-benchmark parameter "
        "tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_COMPONENT_CENTROID_EXPANSION_V3_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_COMPONENT_CENTROID_EXPANSION_V3_DEVELOPMENT"
    )

    dst_json = out / "cross_year_component_centroid_expansion_v3_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_component_centroid_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_component_centroid_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    diag = result["expansion_diagnostics"]
    lines = [
        "# OrbitTrace cross-year component-centroid expansion v3 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(
            f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_COMPONENT_CENTROID_EXPANSION_V3_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n"
    )
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
