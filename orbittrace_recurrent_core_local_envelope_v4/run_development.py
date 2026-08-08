#!/usr/bin/env python3
"""One-shot recurrent-core local-envelope membership refinement on frozen v8."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

V3_RUN = 31235669516
V3_ARTIFACT = 9015567085
V3_ARTIFACT_DIGEST = "sha256:80c5590a5702f3d641315321c5d8ef1387c61a6fcf6a57057b2a7ebe7b7ecfcb"
V3_SOURCE_COMMIT = "f3616eed5a14118c5148513b865eb7491e6f346f"

_CAPTURED_COMPONENTS: list[dict[str, Any]] = []
_ORIGINAL_SCAN_YEAR = v1.v6.label_free_scan_year


def capture_scan_year(*args: Any, **kwargs: Any):
    audit, passing, components = _ORIGINAL_SCAN_YEAR(*args, **kwargs)
    _CAPTURED_COMPONENTS.extend(copy.deepcopy(components))
    return audit, passing, components


def fixed_centroid_radius(
    component: dict[str, Any],
    event_lookup: dict[str, dict[str, Any]],
) -> float:
    year = str(int(component["year"]))
    lookup = event_lookup[year]
    member_ids = [str(x) for x in component["event_ids"]]
    v1.require(member_ids, f"component {component['component_id']} has no events")
    v1.require(all(eid in lookup for eid in member_ids), "component seed event missing from scan corpus")
    members = [lookup[eid] for eid in member_ids]
    center = [dict(component["centroid"])]
    distances = v1.min_exact_distances(members, center)
    v1.require(len(distances) == len(members), "component radius distance count mismatch")
    radius = float(np.max(distances))
    v1.require(np.isfinite(radius) and radius >= 0.0, "invalid component envelope radius")
    return radius


def crossfit_expand_local_envelope(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    v1.require(_CAPTURED_COMPONENTS, "component capture is empty")
    component_by_id = {str(c["component_id"]): c for c in _CAPTURED_COMPONENTS}
    v1.require(len(component_by_id) == len(_CAPTURED_COMPONENTS), "captured component IDs are not unique")

    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup_int = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    event_lookup = {str(y): event_lookup_int[y] for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        "support_unit": "same-year frozen v8 component envelope",
        "component_radius_rule": "maximum original seed-event distance to frozen component centroid",
        "global_membership_radius_used": False,
        "radius_multiplier": None,
        "radius_quantile": None,
        "component_centroids_refit": False,
        "same_year_support_only": True,
        "cross_year_recurrence_preserved_by_frozen_v8_family": True,
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "component_radius_min_by_year": {},
        "component_radius_median_by_year": {},
        "component_radius_p95_by_year": {},
        "component_radius_max_by_year": {},
        "assigned_normalized_radius_median_by_year": {},
        "assigned_normalized_radius_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "component_ids_from_frozen_family_graph_only": True,
    }

    radius_by_component = {
        cid: fixed_centroid_radius(component, event_lookup)
        for cid, component in component_by_id.items()
    }

    for target_year in v1.YEARS:
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events], dtype=np.float64)

        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup_int[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, float, str]] = {}
        eligible_pairs = 0
        year_radii: list[float] = []

        for family in families:
            fid = str(family["family_id"])
            target_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == target_year
            ]
            v1.require(target_components, f"family {fid} lacks target-year components")

            for component in target_components:
                cid = str(component["component_id"])
                radius = float(radius_by_component[cid])
                year_radii.append(radius)
                center = dict(component["centroid"])
                v1.require(
                    all(k in center for k in ("sol", "sun_lon", "ecl_lat", "vg")),
                    f"component {cid} centroid schema changed",
                )

                sol_half_width = min(180.0, 4.0 * radius + 1e-12)
                delta_sol = ((target_sol - (float(center["sol"]) % 360.0) + 180.0) % 360.0) - 180.0
                idx = np.flatnonzero(np.abs(delta_sol) <= sol_half_width)
                candidates = [target_events[int(i)] for i in idx]
                distances = v1.min_exact_distances(candidates, [center])

                for i, distance in zip(idx.tolist(), distances.tolist()):
                    if float(distance) > radius + 1e-12:
                        continue
                    event_id = str(target_events[i]["id"])
                    if event_id in target_seed_owner:
                        continue
                    eligible_pairs += 1
                    normalized = (float(distance) / radius) if radius > 0.0 else 0.0
                    cand = (float(distance), normalized, fid)
                    old = best.get(event_id)
                    if old is None or (cand[0], cand[2]) < (old[0], old[2]):
                        best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        normalized_values: list[float] = []
        for eid, (_distance, normalized, fid) in best.items():
            by_family[fid].append(eid)
            normalized_values.append(float(normalized))

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
        diagnostics["component_radius_min_by_year"][str(target_year)] = float(min(year_radii))
        diagnostics["component_radius_median_by_year"][str(target_year)] = float(np.median(year_radii))
        diagnostics["component_radius_p95_by_year"][str(target_year)] = float(np.quantile(year_radii, 0.95))
        diagnostics["component_radius_max_by_year"][str(target_year)] = float(max(year_radii))
        diagnostics["assigned_normalized_radius_median_by_year"][str(target_year)] = (
            float(np.median(normalized_values)) if normalized_values else None
        )
        diagnostics["assigned_normalized_radius_max_by_year"][str(target_year)] = (
            float(max(normalized_values)) if normalized_values else None
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
    v1.crossfit_expand = crossfit_expand_local_envelope
    v1.CORPUS = "orbittrace-recurrent-core-local-envelope-v4-development"
    rc = v1.main()

    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())

    result["configuration"].update({
        "membership_rule": "same-year frozen component envelope; radius equals max original seed-event distance to frozen component centroid; exclusive nearest-component family assignment",
        "support_unit": "same-year frozen v8 component envelope",
        "component_radius_rule": "max original seed-event distance to frozen component centroid",
        "global_membership_radius": None,
        "global_membership_radius_search": False,
        "radius_multiplier": None,
        "radius_quantile": None,
        "same_year_support": True,
        "cross_year_recurrence_preserved_by_frozen_v8_family": True,
        "component_centroids_refit": False,
        "family_link_radius_reused_as_membership_radius": False,
        "v8_family_link_radius_unchanged": 1.5,
        "v3_predecessor_run": V3_RUN,
        "v3_predecessor_artifact": V3_ARTIFACT,
        "v3_predecessor_artifact_digest": V3_ARTIFACT_DIGEST,
        "v3_source_commit": V3_SOURCE_COMMIT,
    })

    result["integrity_gates"].pop("other_year_seed_support_only", None)
    result["integrity_gates"]["same_year_frozen_component_support_only"] = (
        result["expansion_diagnostics"]["same_year_support_only"] is True
    )
    result["integrity_gates"]["cross_year_recurrence_preserved_by_frozen_v8_family"] = (
        result["expansion_diagnostics"]["cross_year_recurrence_preserved_by_frozen_v8_family"] is True
    )
    result["integrity_gates"]["component_radius_is_exact_seed_extent"] = (
        result["expansion_diagnostics"]["component_radius_rule"]
        == "maximum original seed-event distance to frozen component centroid"
        and result["expansion_diagnostics"]["global_membership_radius_used"] is False
        and result["expansion_diagnostics"]["radius_multiplier"] is None
        and result["expansion_diagnostics"]["radius_quantile"] is None
    )
    result["integrity_gates"]["component_ids_from_frozen_family_graph_only"] = (
        result["expansion_diagnostics"]["component_ids_from_frozen_family_graph_only"] is True
    )
    result["integrity_gates"]["component_centroids_not_refit"] = (
        result["expansion_diagnostics"]["component_centroids_refit"] is False
    )

    result["claim_boundary"] = (
        "Target-excluded v4 development only. The exact v8 recurrent family universe and ranking were frozen first. "
        "Membership refinement uses only same-year frozen component centroids and each component's exact original seed "
        "extent; cross-year recurrence remains supplied by the frozen v8 family. No OrbitTrace target information, "
        "target-region event, Stage A/B output, global membership radius, radius multiplier, quantile search, or "
        "literature-benchmark parameter tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_RECURRENT_CORE_LOCAL_ENVELOPE_V4_DEVELOPMENT"
        if passed else "FAIL_RECURRENT_CORE_LOCAL_ENVELOPE_V4_DEVELOPMENT"
    )

    dst_json = out / "recurrent_core_local_envelope_v4_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "recurrent_core_local_envelope_v4_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "recurrent_core_local_envelope_v4_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    diag = result["expansion_diagnostics"]
    lines = [
        "# OrbitTrace recurrent-core local-envelope v4 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- baseline / refined macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / refined recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / refined qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / refined top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(
            f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**"
        )
        lines.append(
            f"- {y} component-radius median / p95 / max: "
            f"**{diag['component_radius_median_by_year'][str(y)]:.6f} / "
            f"{diag['component_radius_p95_by_year'][str(y)]:.6f} / "
            f"{diag['component_radius_max_by_year'][str(y)]:.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "RECURRENT_CORE_LOCAL_ENVELOPE_V4_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n"
    )
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
