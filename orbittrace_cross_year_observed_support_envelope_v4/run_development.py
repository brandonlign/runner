#!/usr/bin/env python3
"""One-shot observed-support-envelope cross-year membership expansion on frozen v8."""
from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1
from orbittrace_support_overlap_family_v9 import run_development as v9

V3_RUN = 31235669516
V3_ARTIFACT = 9015567085
V3_ARTIFACT_DIGEST = "sha256:80c5590a5702f3d641315321c5d8ef1387c61a6fcf6a57057b2a7ebe7b7ecfcb"
V3_SOURCE_COMMIT = "f3616eed5a14118c5148513b865eb7491e6f346f"
V9_SOURCE_COMMIT = "ae15e7f28c6ccbcdcff57cc2efd44cb9aa01b0b3"
V9_RADIUS_SOURCE_BLOB = "ae098dfea19c0affba8af67c286f3f4153a91136"

_CAPTURED_COMPONENTS: list[dict[str, Any]] = []
_CAPTURED_SUPPORT: Any | None = None
_CAPTURED_BASE: Any | None = None
_ORIGINAL_SCAN_YEAR = v1.v6.label_free_scan_year


def capture_scan_year(year: int, events: list[dict[str, Any]], support: Any, base: Any):
    global _CAPTURED_SUPPORT, _CAPTURED_BASE
    _CAPTURED_SUPPORT = support
    _CAPTURED_BASE = base
    audit, passing, components = _ORIGINAL_SCAN_YEAR(year, events, support, base)
    _CAPTURED_COMPONENTS.extend(copy.deepcopy(components))
    return audit, passing, components


def min_admitting_component_distances(
    target: list[dict[str, Any]],
    centers: list[dict[str, Any]],
    effective_radii: list[float],
) -> np.ndarray:
    """Minimum exact frozen-metric distance among component balls that admit each event."""
    if not target:
        return np.empty(0, dtype=np.float64)
    v1.require(centers and len(centers) == len(effective_radii), "component center/radius mismatch")
    radii = np.asarray(effective_radii, dtype=np.float64)
    v1.require(np.all(np.isfinite(radii)) and np.all(radii >= 0.0), "invalid effective component radius")
    v1.require(np.all(radii <= v1.RADIUS + 1e-12), "effective radius exceeds inherited 1.5 cap")

    ss = np.asarray([float(c["sol"]) for c in centers], dtype=np.float64)
    sl = np.asarray([float(c["sun_lon"]) for c in centers], dtype=np.float64)
    sb = np.asarray([float(c["ecl_lat"]) for c in centers], dtype=np.float64)
    sv = np.asarray([float(c["vg"]) for c in centers], dtype=np.float64)
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
        admitted = d <= radii[None, :] + 1e-12
        eligible_distance = np.where(admitted, d, np.inf)
        out[lo : lo + len(rows)] = np.min(eligible_distance, axis=1)

    return out


def crossfit_expand_observed_envelope(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    v1.require(_CAPTURED_COMPONENTS, "component capture is empty")
    v1.require(_CAPTURED_SUPPORT is not None and _CAPTURED_BASE is not None, "frozen support/base capture missing")

    component_by_id = {str(c["component_id"]): c for c in _CAPTURED_COMPONENTS}
    v1.require(len(component_by_id) == len(_CAPTURED_COMPONENTS), "captured component IDs are not unique")

    raw_radii, v9_radius_summary = v9.component_support_radii(
        _CAPTURED_COMPONENTS,
        scan_by_year,
        _CAPTURED_SUPPORT,
        _CAPTURED_BASE,
    )
    v1.require(len(raw_radii) == len(_CAPTURED_COMPONENTS), "v9 radius count mismatch")
    raw_radius_by_id = {
        str(component["component_id"]): float(radius)
        for component, radius in zip(_CAPTURED_COMPONENTS, raw_radii)
    }
    effective_radius_by_id = {
        cid: float(min(v1.RADIUS, radius))
        for cid, radius in raw_radius_by_id.items()
    }
    effective_values = list(effective_radius_by_id.values())
    clipped_count = sum(raw_radius_by_id[cid] > v1.RADIUS for cid in raw_radius_by_id)

    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}

    diagnostics: dict[str, Any] = {
        "global_predecessor_cap": v1.RADIUS,
        "solar_prefilter_deg": v1.SOL_PREFILTER,
        "support_unit": "frozen source-year component centroid with pre-existing v9 observed support radius",
        "raw_radius_definition": v9_radius_summary["radius_definition"],
        "raw_radius_multiplier": v9_radius_summary["radius_multiplier"],
        "raw_radius_quantile": v9_radius_summary["radius_quantile"],
        "raw_radius_component_count": v9_radius_summary["component_count"],
        "raw_radius_records_sha256": v9_radius_summary["component_radius_records_sha256"],
        "raw_radius_min": v9_radius_summary["radius_min"],
        "raw_radius_median": v9_radius_summary["radius_median"],
        "raw_radius_p95": v9_radius_summary["radius_p95"],
        "raw_radius_max": v9_radius_summary["radius_max"],
        "effective_radius_rule": "min(1.5, exact pre-existing v9 observed component radius)",
        "effective_radius_min": float(min(effective_values)),
        "effective_radius_median": float(np.median(effective_values)),
        "effective_radius_p95": float(np.quantile(effective_values, 0.95)),
        "effective_radius_max": float(max(effective_values)),
        "components_clipped_by_1p5_cap": int(clipped_count),
        "component_centroids_refit": False,
        "component_radii_refit_after_expansion": False,
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "assigned_min_distance_median_by_year": {},
        "assigned_min_distance_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "component_ids_from_frozen_family_graph_only": True,
        "radius_search": False,
        "radius_multiplier_search": False,
        "radius_quantile_search": False,
    }

    for target_year in v1.YEARS:
        source_year = v1.YEARS[1] if target_year == v1.YEARS[0] else v1.YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events], dtype=np.float64)

        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str]] = {}
        eligible_pairs = 0

        for family in families:
            fid = str(family["family_id"])
            source_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == source_year
            ]
            v1.require(source_components, f"family {fid} lacks source-year components")
            centers = [dict(component["centroid"]) for component in source_components]
            radii = [effective_radius_by_id[str(component["component_id"])] for component in source_components]

            # 6 degrees is the necessary solar-longitude prefilter for the unchanged maximum possible radius 1.5.
            mask = v1.in_expanded_arc(target_sol, [float(center["sol"]) for center in centers])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            distances = min_admitting_component_distances(candidates, centers, radii)

            for i, distance in zip(idx.tolist(), distances.tolist()):
                if not math.isfinite(float(distance)):
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
        diagnostics["assigned_min_distance_median_by_year"][str(target_year)] = (
            float(np.median(assigned_distances)) if assigned_distances else None
        )
        diagnostics["assigned_min_distance_max_by_year"][str(target_year)] = (
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
    diagnostics["all_effective_radii_le_1p5"] = all(
        radius <= v1.RADIUS + 1e-12 for radius in effective_values
    )
    diagnostics["all_effective_radii_exact_min_rule"] = all(
        abs(effective_radius_by_id[cid] - min(v1.RADIUS, raw_radius_by_id[cid])) <= 1e-15
        for cid in raw_radius_by_id
    )
    return expanded, diagnostics, assignments


def main() -> int:
    _CAPTURED_COMPONENTS.clear()
    global _CAPTURED_SUPPORT, _CAPTURED_BASE
    _CAPTURED_SUPPORT = None
    _CAPTURED_BASE = None

    v1.v6.label_free_scan_year = capture_scan_year
    v1.crossfit_expand = crossfit_expand_observed_envelope
    v1.CORPUS = "orbittrace-cross-year-observed-support-envelope-v4-development"
    rc = v1.main()

    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "other-year frozen component-centroid support with radius min(1.5, exact pre-existing v9 maximum-member observed radius); exclusive nearest-family assignment",
        "support_unit": "frozen source-year component centroid",
        "observed_radius_definition": "exact v9 max frozen centroid_distance over all unique original component member events",
        "effective_radius_rule": "min(1.5, observed radius)",
        "component_centroids_refit": False,
        "component_radii_refit_after_expansion": False,
        "radius_search": False,
        "radius_multiplier": None,
        "radius_quantile": None,
        "v3_predecessor_run": V3_RUN,
        "v3_predecessor_artifact": V3_ARTIFACT,
        "v3_predecessor_artifact_digest": V3_ARTIFACT_DIGEST,
        "v3_source_commit": V3_SOURCE_COMMIT,
        "v9_radius_source_commit": V9_SOURCE_COMMIT,
        "v9_radius_source_blob": V9_RADIUS_SOURCE_BLOB,
    })
    diag = result["expansion_diagnostics"]
    result["integrity_gates"]["exact_preexisting_v9_observed_radius_definition"] = (
        diag["raw_radius_definition"] == "max frozen centroid_distance over all unique component member events"
        and diag["raw_radius_multiplier"] is None
        and diag["raw_radius_quantile"] is None
    )
    result["integrity_gates"]["effective_radius_exact_min_1p5_observed"] = (
        diag["all_effective_radii_le_1p5"] is True
        and diag["all_effective_radii_exact_min_rule"] is True
        and abs(float(diag["effective_radius_max"]) - min(v1.RADIUS, float(diag["raw_radius_max"]))) <= 1e-12
    )
    result["integrity_gates"]["component_centroids_and_radii_not_refit_after_expansion"] = (
        diag["component_centroids_refit"] is False
        and diag["component_radii_refit_after_expansion"] is False
    )
    result["integrity_gates"]["no_radius_multiplier_or_quantile_search"] = (
        diag["radius_search"] is False
        and diag["radius_multiplier_search"] is False
        and diag["radius_quantile_search"] is False
    )
    result["claim_boundary"] = (
        "Target-excluded v4 development only. The exact v8 family universe and ranking were frozen first. "
        "The sole successor change replaces v3's global 1.5 membership ball by min(1.5, the exact pre-existing "
        "v9 observed radius of each frozen source component). No OrbitTrace target information, target-region event, "
        "Stage A/B output, radius multiplier/quantile search, literature-benchmark parameter tuning, reranking, or "
        "recursive membership growth entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_OBSERVED_SUPPORT_ENVELOPE_V4_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_OBSERVED_SUPPORT_ENVELOPE_V4_DEVELOPMENT"
    )

    dst_json = out / "cross_year_observed_support_envelope_v4_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_observed_support_envelope_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_observed_support_envelope_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace cross-year observed-support envelope v4 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- raw observed radius median / p95 / max: **{diag['raw_radius_median']:.6f} / {diag['raw_radius_p95']:.6f} / {diag['raw_radius_max']:.6f}**",
        f"- effective radius median / p95 / max: **{diag['effective_radius_median']:.6f} / {diag['effective_radius_p95']:.6f} / {diag['effective_radius_max']:.6f}**",
        f"- components clipped by 1.5 cap: **{diag['components_clipped_by_1p5_cap']}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for year in v1.YEARS:
        lines.append(
            f"- {year} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(year)]['all']:+.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_OBSERVED_SUPPORT_ENVELOPE_V4_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n"
    )
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
