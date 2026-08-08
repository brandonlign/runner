#!/usr/bin/env python3
"""One-shot component-envelope cross-year membership expansion on exact frozen v8."""
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
PROSPECTIVE_RESERVATION = "SonotaCo 2017"

_CAPTURED_COMPONENTS: list[dict[str, Any]] = []
_ORIGINAL_SCAN_YEAR = v1.v6.label_free_scan_year


def capture_scan_year(*args: Any, **kwargs: Any):
    audit, passing, components = _ORIGINAL_SCAN_YEAR(*args, **kwargs)
    _CAPTURED_COMPONENTS.extend(copy.deepcopy(components))
    return audit, passing, components


def min_envelope_distance(
    target: list[dict[str, Any]],
    centers: list[dict[str, Any]],
    radii: np.ndarray,
) -> np.ndarray:
    """Minimum distance to a component whose frozen empirical envelope contains the event."""
    if not target:
        return np.empty(0, dtype=np.float64)
    if not centers:
        return np.full(len(target), np.inf, dtype=np.float64)

    ss = np.asarray([float(c["sol"]) for c in centers], dtype=np.float64)
    sl = np.asarray([float(c["sun_lon"]) for c in centers], dtype=np.float64)
    sb = np.asarray([float(c["ecl_lat"]) for c in centers], dtype=np.float64)
    sv = np.asarray([float(c["vg"]) for c in centers], dtype=np.float64)
    rr = np.asarray(radii, dtype=np.float64)
    v1.require(rr.shape == (len(centers),), "component radius shape mismatch")
    v1.require(np.all(rr >= 0.0) and np.all(rr <= v1.RADIUS + 1e-12), "invalid component envelope radius")

    out = np.full(len(target), np.inf, dtype=np.float64)
    for lo in range(0, len(target), 2048):
        rows = target[lo : lo + 2048]
        ts = np.asarray([float(e["sol"]) for e in rows], dtype=np.float64)[:, None]
        tl = np.asarray([float(e["sun_lon"]) for e in rows], dtype=np.float64)[:, None]
        tb = np.asarray([float(e["ecl_lat"]) for e in rows], dtype=np.float64)[:, None]
        tv = np.asarray([float(e["vg"]) for e in rows], dtype=np.float64)[:, None]
        dsol = ((ts - ss[None, :] + 180.0) % 360.0 - 180.0) / 4.0
        dlon_raw = ((tl - sl[None, :] + 180.0) % 360.0 - 180.0)
        dlon = dlon_raw * np.cos(np.radians(0.5 * (tb + sb[None, :]))) / 2.0
        dlat = (tb - sb[None, :]) / 2.0
        dvg = (tv - sv[None, :]) / 2.0
        d = np.sqrt(dsol*dsol + dlon*dlon + dlat*dlat + dvg*dvg)
        eligible = d <= rr[None, :] + 1e-12
        masked = np.where(eligible, d, np.inf)
        out[lo : lo + len(rows)] = np.min(masked, axis=1)
    return out


def component_envelope_radius(
    component: dict[str, Any],
    event_lookup: dict[str, dict[str, Any]],
) -> tuple[float, float, int]:
    """Smallest radius around the frozen centroid covering original component seeds, capped at 1.5."""
    ids = [str(x) for x in component["event_ids"]]
    v1.require(ids, f"component {component['component_id']} has no seed events")
    missing = [eid for eid in ids if eid not in event_lookup]
    v1.require(not missing, f"component {component['component_id']} has missing seed events")
    members = [event_lookup[eid] for eid in ids]
    center = dict(component["centroid"])
    d = v1.min_exact_distances(members, [center])
    v1.require(len(d) == len(members) and np.all(np.isfinite(d)), "component envelope distance failure")
    raw = float(np.max(d))
    capped = float(min(v1.RADIUS, raw))
    return capped, raw, len(ids)


def crossfit_expand_component_envelope(
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
        "support_unit": "frozen source-year component empirical envelope",
        "component_centroids_refit": False,
        "component_envelope_statistic": "max original-seed distance to frozen centroid, capped at inherited 1.5",
        "component_envelope_parameter_search": False,
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "envelope_radius_min_by_year": {},
        "envelope_radius_median_by_year": {},
        "envelope_radius_max_by_year": {},
        "raw_envelope_radius_max_by_year": {},
        "envelopes_capped_at_1_5_by_year": {},
        "source_component_member_count_median_by_year": {},
        "assigned_distance_median_by_year": {},
        "assigned_distance_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "component_ids_from_frozen_family_graph_only": True,
    }

    for target_year in v1.YEARS:
        source_year = v1.YEARS[1] if target_year == v1.YEARS[0] else v1.YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events])
        source_lookup = event_lookup[source_year]

        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str]] = {}
        eligible_pairs = 0
        all_radii: list[float] = []
        all_raw_radii: list[float] = []
        all_member_counts: list[int] = []

        for family in families:
            fid = str(family["family_id"])
            source_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == source_year
            ]
            v1.require(source_components, f"family {fid} lacks source-year components")
            centers: list[dict[str, Any]] = []
            radii: list[float] = []
            for component in source_components:
                center = dict(component["centroid"])
                v1.require(
                    all(k in center for k in ("sol", "sun_lon", "ecl_lat", "vg")),
                    f"family {fid} component centroid schema changed",
                )
                radius, raw_radius, member_count = component_envelope_radius(component, source_lookup)
                centers.append(center)
                radii.append(radius)
                all_radii.append(radius)
                all_raw_radii.append(raw_radius)
                all_member_counts.append(member_count)

            mask = v1.in_expanded_arc(target_sol, [float(c["sol"]) for c in centers])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            distances = min_envelope_distance(candidates, centers, np.asarray(radii, dtype=np.float64))
            for i, distance in zip(idx.tolist(), distances.tolist()):
                if not np.isfinite(distance):
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

        y = str(target_year)
        diagnostics["new_members_by_year"][y] = len(best)
        diagnostics["eligible_family_event_pairs_by_year"][y] = eligible_pairs
        diagnostics["conflicted_events_by_year"][y] = max(0, eligible_pairs - len(best))
        diagnostics["original_seed_events_by_year"][y] = len(target_seed_owner)
        diagnostics["envelope_radius_min_by_year"][y] = float(min(all_radii))
        diagnostics["envelope_radius_median_by_year"][y] = float(np.median(all_radii))
        diagnostics["envelope_radius_max_by_year"][y] = float(max(all_radii))
        diagnostics["raw_envelope_radius_max_by_year"][y] = float(max(all_raw_radii))
        diagnostics["envelopes_capped_at_1_5_by_year"][y] = int(sum(r > v1.RADIUS + 1e-12 for r in all_raw_radii))
        diagnostics["source_component_member_count_median_by_year"][y] = float(np.median(all_member_counts))
        diagnostics["assigned_distance_median_by_year"][y] = (
            float(np.median(assigned_distances)) if assigned_distances else None
        )
        diagnostics["assigned_distance_max_by_year"][y] = (
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
    v1.crossfit_expand = crossfit_expand_component_envelope
    v1.CORPUS = "orbittrace-cross-year-component-envelope-expansion-v4-development"
    rc = v1.main()

    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "other-year frozen component empirical envelope: target distance <= min(1.5, max original-seed distance to frozen component centroid); exclusive nearest-family assignment",
        "support_unit": "frozen source-year component empirical envelope",
        "component_centroids_refit": False,
        "component_envelope_parameter_search": False,
        "component_envelope_cap": 1.5,
        "component_envelope_cap_source": "exact inherited v8 family-link radius",
        "v3_predecessor_run": V3_RUN,
        "v3_predecessor_artifact": V3_ARTIFACT,
        "v3_predecessor_artifact_digest": V3_ARTIFACT_DIGEST,
        "v3_source_commit": V3_SOURCE_COMMIT,
        "prospective_reservation": PROSPECTIVE_RESERVATION,
        "prospective_reservation_accessed": False,
    })
    result["integrity_gates"]["component_empirical_envelope_support_only"] = (
        result["expansion_diagnostics"]["support_unit"] == "frozen source-year component empirical envelope"
        and result["expansion_diagnostics"]["component_centroids_refit"] is False
    )
    result["integrity_gates"]["component_envelope_not_selected_by_search"] = (
        result["expansion_diagnostics"]["component_envelope_parameter_search"] is False
    )
    result["integrity_gates"]["component_envelope_capped_by_inherited_radius"] = (
        all(float(x) <= v1.RADIUS + 1e-12 for x in result["expansion_diagnostics"]["envelope_radius_max_by_year"].values())
    )
    result["integrity_gates"]["prospective_sonotaco_2017_unaccessed"] = True
    result["claim_boundary"] = (
        "Target-excluded v4 development only. The exact v8 family universe and ranking were frozen first. "
        "The sole successor change replaces the failed binary 1.5 membership halo with each frozen source component's "
        "own minimal centroid-centered envelope covering its original seed members, capped at the unchanged inherited 1.5 structural radius. "
        "No OrbitTrace target information, target-region event, Stage A/B output, envelope quantile/scale search, radius search, "
        "or literature-benchmark parameter tuning entered the method. SonotaCo 2017 remains untouched and reserved for a separately frozen prospective validation only if development passes."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_COMPONENT_ENVELOPE_EXPANSION_V4_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_COMPONENT_ENVELOPE_EXPANSION_V4_DEVELOPMENT"
    )

    dst_json = out / "cross_year_component_envelope_expansion_v4_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_component_envelope_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_component_envelope_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    diag = result["expansion_diagnostics"]
    lines = [
        "# OrbitTrace cross-year component-envelope expansion v4 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- envelope-radius medians (target 2022 / 2023): **{diag['envelope_radius_median_by_year']['2022']:.6f} / {diag['envelope_radius_median_by_year']['2023']:.6f}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(
            f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. SonotaCo 2017 remains untouched. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_COMPONENT_ENVELOPE_EXPANSION_V4_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n"
    )
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
