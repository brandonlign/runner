#!/usr/bin/env python3
"""One-shot anisotropic cross-year membership expansion on the exact frozen v8 seeds."""
from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

V4_RUN = 31236659166
V4_ARTIFACT = 9015894267
V4_ARTIFACT_DIGEST = "sha256:1a823ee65b29622065c8f52c81a27e17c1247246323d971a85de6238c1d5ce07"
V4_SOURCE_COMMIT = "62ba13f6f4fb20fb78b6d5d8066b5f64844a25a8"
COVARIANCE_ESTIMATOR = "sklearn.covariance.LedoitWolf(assume_centered=True)"
RAW_CAP = 1.5

_CAPTURED_COMPONENTS: list[dict[str, Any]] = []
_ORIGINAL_SCAN_YEAR = v1.v6.label_free_scan_year


def capture_scan_year(*args: Any, **kwargs: Any):
    audit, passing, components = _ORIGINAL_SCAN_YEAR(*args, **kwargs)
    _CAPTURED_COMPONENTS.extend(copy.deepcopy(components))
    return audit, passing, components


def residual_matrix(center: dict[str, Any], events: list[dict[str, Any]]) -> np.ndarray:
    """Exact four scaled residual coordinates underlying the frozen centroid distance."""
    if not events:
        return np.empty((0, 4), dtype=np.float64)
    csol = float(center["sol"])
    clon = float(center["sun_lon"])
    clat = float(center["ecl_lat"])
    cvg = float(center["vg"])
    sol = np.asarray([float(e["sol"]) for e in events], dtype=np.float64)
    lon = np.asarray([float(e["sun_lon"]) for e in events], dtype=np.float64)
    lat = np.asarray([float(e["ecl_lat"]) for e in events], dtype=np.float64)
    vg = np.asarray([float(e["vg"]) for e in events], dtype=np.float64)
    dsol = ((sol - csol + 180.0) % 360.0 - 180.0) / 4.0
    dlon_raw = ((lon - clon + 180.0) % 360.0 - 180.0)
    dlon = dlon_raw * np.cos(np.radians(0.5 * (lat + clat))) / 2.0
    dlat = (lat - clat) / 2.0
    dvg = (vg - cvg) / 2.0
    out = np.column_stack((dsol, dlon, dlat, dvg))
    v1.require(out.shape == (len(events), 4) and np.all(np.isfinite(out)), "invalid residual matrix")
    return out


def build_component_profiles(
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    event_lookup = {
        year: {str(event["id"]): event for event in scan_by_year[year]}
        for year in v1.YEARS
    }
    profiles: dict[str, dict[str, Any]] = {}
    shrinkages: list[float] = []
    thresholds: list[float] = []
    min_eigenvalues: list[float] = []
    event_counts: list[int] = []

    for component in components:
        cid = str(component["component_id"])
        year = int(component["year"])
        event_ids = sorted(set(str(value) for value in component["event_ids"]))
        v1.require(len(event_ids) == int(component["event_count"]), f"component {cid} event union changed")
        v1.require(event_ids and all(eid in event_lookup[year] for eid in event_ids), f"component {cid} event lookup failed")
        events = [event_lookup[year][eid] for eid in event_ids]
        residuals = residual_matrix(component["centroid"], events)
        v1.require(len(residuals) >= 4, f"component {cid} violates frozen >=4 event gate")

        model = LedoitWolf(assume_centered=True).fit(residuals)
        covariance = np.asarray(model.covariance_, dtype=np.float64)
        precision = np.asarray(model.precision_, dtype=np.float64)
        v1.require(covariance.shape == (4, 4) and precision.shape == (4, 4), f"component {cid} covariance schema changed")
        v1.require(np.all(np.isfinite(covariance)) and np.all(np.isfinite(precision)), f"component {cid} non-finite covariance")
        covariance = 0.5 * (covariance + covariance.T)
        precision = 0.5 * (precision + precision.T)
        eig = np.linalg.eigvalsh(covariance)
        v1.require(np.all(np.isfinite(eig)) and float(np.min(eig)) > 0.0, f"component {cid} covariance not positive definite")

        train_md2 = np.einsum("ij,jk,ik->i", residuals, precision, residuals)
        v1.require(np.all(np.isfinite(train_md2)) and np.all(train_md2 >= -1e-10), f"component {cid} invalid training Mahalanobis distance")
        train_md2 = np.maximum(train_md2, 0.0)
        threshold = float(np.max(train_md2))
        v1.require(math.isfinite(threshold) and threshold >= 0.0, f"component {cid} invalid support threshold")
        v1.require(bool(np.all(train_md2 <= threshold + 1e-12)), f"component {cid} training support threshold excludes member")

        profiles[cid] = {
            "year": year,
            "centroid": dict(component["centroid"]),
            "precision": precision,
            "mahalanobis2_threshold": threshold,
            "shrinkage": float(model.shrinkage_),
            "event_count": len(event_ids),
            "covariance_min_eigenvalue": float(np.min(eig)),
        }
        shrinkages.append(float(model.shrinkage_))
        thresholds.append(threshold)
        min_eigenvalues.append(float(np.min(eig)))
        event_counts.append(len(event_ids))

    summary = {
        "component_count": len(components),
        "profile_count": len(profiles),
        "residual_dimension": 4,
        "covariance_estimator": COVARIANCE_ESTIMATOR,
        "assume_centered": True,
        "component_centroid_refit": False,
        "threshold_definition": "maximum squared Mahalanobis distance over all unique original component member residuals",
        "threshold_multiplier": None,
        "threshold_quantile": None,
        "raw_distance_cap": RAW_CAP,
        "shrinkage_min": float(min(shrinkages)),
        "shrinkage_median": float(np.median(shrinkages)),
        "shrinkage_max": float(max(shrinkages)),
        "mahalanobis2_threshold_min": float(min(thresholds)),
        "mahalanobis2_threshold_median": float(np.median(thresholds)),
        "mahalanobis2_threshold_p95": float(np.quantile(thresholds, 0.95)),
        "mahalanobis2_threshold_max": float(max(thresholds)),
        "covariance_min_eigenvalue_global_min": float(min(min_eigenvalues)),
        "component_event_count_min": int(min(event_counts)),
        "component_event_count_median": float(np.median(event_counts)),
        "component_event_count_max": int(max(event_counts)),
        "all_covariances_positive_definite": True,
        "all_training_members_inside_own_mahalanobis_envelope": True,
    }
    return profiles, summary


def component_candidate_scores(
    profile: dict[str, Any],
    target_events: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    """Return eligibility and raw exact-distance values for one frozen source component."""
    residuals = residual_matrix(profile["centroid"], target_events)
    if not len(residuals):
        return np.empty(0, dtype=bool), np.empty(0, dtype=np.float64)
    raw2 = np.einsum("ij,ij->i", residuals, residuals)
    precision = np.asarray(profile["precision"], dtype=np.float64)
    md2 = np.einsum("ij,jk,ik->i", residuals, precision, residuals)
    md2 = np.maximum(md2, 0.0)
    eligible = (
        (raw2 <= RAW_CAP * RAW_CAP + 1e-12)
        & (md2 <= float(profile["mahalanobis2_threshold"]) + 1e-12)
    )
    return eligible, np.sqrt(np.maximum(raw2, 0.0))


def crossfit_expand_anisotropic(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    v1.require(_CAPTURED_COMPONENTS, "component capture is empty")
    component_by_id = {str(c["component_id"]): c for c in _CAPTURED_COMPONENTS}
    v1.require(len(component_by_id) == len(_CAPTURED_COMPONENTS), "captured component IDs are not unique")
    profiles, profile_summary = build_component_profiles(_CAPTURED_COMPONENTS, scan_by_year)

    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        **profile_summary,
        "solar_prefilter_deg": v1.SOL_PREFILTER,
        "support_unit": "frozen source-year component Ledoit-Wolf shrinkage ellipsoid",
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "eligible_component_event_hits_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "assigned_raw_distance_median_by_year": {},
        "assigned_raw_distance_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "component_ids_from_frozen_family_graph_only": True,
        "covariance_estimator_search": False,
        "mahalanobis_threshold_search": False,
        "raw_cap_search": False,
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

        global_best: dict[str, tuple[float, str]] = {}
        family_event_pairs = 0
        component_event_hits = 0

        for family in families:
            fid = str(family["family_id"])
            source_component_ids = [
                str(cid) for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == source_year
            ]
            v1.require(source_component_ids, f"family {fid} lacks source-year components")
            family_best: dict[str, float] = {}

            for cid in source_component_ids:
                profile = profiles[cid]
                center_sol = float(profile["centroid"]["sol"])
                mask = v1.in_expanded_arc(target_sol, [center_sol])
                idx = np.flatnonzero(mask)
                candidates = [target_events[int(i)] for i in idx]
                eligible, raw_distance = component_candidate_scores(profile, candidates)
                for i, ok, distance in zip(idx.tolist(), eligible.tolist(), raw_distance.tolist()):
                    if not ok:
                        continue
                    event_id = str(target_events[i]["id"])
                    if event_id in target_seed_owner:
                        continue
                    component_event_hits += 1
                    old = family_best.get(event_id)
                    if old is None or float(distance) < old:
                        family_best[event_id] = float(distance)

            family_event_pairs += len(family_best)
            for event_id, distance in family_best.items():
                cand = (float(distance), fid)
                old = global_best.get(event_id)
                if old is None or cand < old:
                    global_best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_distances: list[float] = []
        for eid, (distance, fid) in global_best.items():
            by_family[fid].append(eid)
            assigned_distances.append(float(distance))

        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(global_best)
        diagnostics["eligible_family_event_pairs_by_year"][str(target_year)] = family_event_pairs
        diagnostics["eligible_component_event_hits_by_year"][str(target_year)] = component_event_hits
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, family_event_pairs - len(global_best))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)
        diagnostics["assigned_raw_distance_median_by_year"][str(target_year)] = (
            float(np.median(assigned_distances)) if assigned_distances else None
        )
        diagnostics["assigned_raw_distance_max_by_year"][str(target_year)] = (
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
    diagnostics["all_assigned_raw_distances_le_1p5"] = all(
        value is None or float(value) <= RAW_CAP + 1e-12
        for value in diagnostics["assigned_raw_distance_max_by_year"].values()
    )
    return expanded, diagnostics, assignments


def main() -> int:
    _CAPTURED_COMPONENTS.clear()
    v1.v6.label_free_scan_year = capture_scan_year
    v1.crossfit_expand = crossfit_expand_anisotropic
    v1.CORPUS = "orbittrace-cross-year-anisotropic-envelope-v5-development"
    rc = v1.main()

    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    diag = result["expansion_diagnostics"]
    result["configuration"].update({
        "membership_rule": "other-year frozen component Ledoit-Wolf shrinkage ellipsoid; max source-member squared Mahalanobis support; raw exact distance <=1.5; exclusive nearest-family assignment",
        "support_unit": "frozen source-year component anisotropic envelope",
        "residual_representation": "exact four scaled residual coordinates underlying frozen v6/v8 centroid distance",
        "covariance_estimator": COVARIANCE_ESTIMATOR,
        "assume_centered": True,
        "mahalanobis_threshold": "maximum source-member squared Mahalanobis distance",
        "threshold_multiplier": None,
        "threshold_quantile": None,
        "raw_distance_cap": RAW_CAP,
        "component_centroids_refit": False,
        "covariance_estimator_search": False,
        "threshold_search_v5": False,
        "raw_cap_search": False,
        "v4_predecessor_run": V4_RUN,
        "v4_predecessor_artifact": V4_ARTIFACT,
        "v4_predecessor_artifact_digest": V4_ARTIFACT_DIGEST,
        "v4_source_commit": V4_SOURCE_COMMIT,
    })
    result["integrity_gates"]["exact_frozen_anisotropic_estimator"] = (
        diag["covariance_estimator"] == COVARIANCE_ESTIMATOR
        and diag["assume_centered"] is True
        and diag["residual_dimension"] == 4
    )
    result["integrity_gates"]["max_training_mahalanobis_support_no_multiplier"] = (
        diag["threshold_definition"] == "maximum squared Mahalanobis distance over all unique original component member residuals"
        and diag["threshold_multiplier"] is None
        and diag["threshold_quantile"] is None
        and diag["all_training_members_inside_own_mahalanobis_envelope"] is True
    )
    result["integrity_gates"]["all_covariances_positive_definite"] = diag["all_covariances_positive_definite"] is True
    result["integrity_gates"]["raw_predecessor_cap_1p5_preserved"] = (
        abs(float(diag["raw_distance_cap"]) - RAW_CAP) <= 1e-15
        and diag["all_assigned_raw_distances_le_1p5"] is True
    )
    result["integrity_gates"]["no_anisotropic_parameter_search"] = (
        diag["covariance_estimator_search"] is False
        and diag["mahalanobis_threshold_search"] is False
        and diag["raw_cap_search"] is False
    )
    result["claim_boundary"] = (
        "Target-excluded v5 development only. The exact v8 family universe and ranking were frozen first. "
        "The sole successor change is a fixed Ledoit-Wolf shrinkage ellipsoid per original other-year component, "
        "thresholded by that component's maximum source-member squared Mahalanobis distance and intersected with "
        "the unchanged raw 1.5 predecessor cap. No OrbitTrace target information, target-region event, Stage A/B "
        "output, covariance/threshold search, literature-benchmark tuning, reranking, or recursive growth entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_ANISOTROPIC_ENVELOPE_V5_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_ANISOTROPIC_ENVELOPE_V5_DEVELOPMENT"
    )

    dst_json = out / "cross_year_anisotropic_envelope_v5_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_anisotropic_envelope_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_anisotropic_envelope_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace cross-year anisotropic envelope v5 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- Ledoit-Wolf shrinkage median: **{diag['shrinkage_median']:.6f}**",
        f"- squared-Mahalanobis threshold median / p95 / max: **{diag['mahalanobis2_threshold_median']:.6f} / {diag['mahalanobis2_threshold_p95']:.6f} / {diag['mahalanobis2_threshold_max']:.6f}**",
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
    (out / "CROSS_YEAR_ANISOTROPIC_ENVELOPE_V5_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
