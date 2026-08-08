#!/usr/bin/env python3
"""One-shot cross-year affine-trajectory conformal membership expansion on frozen v8 seeds."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

ALPHA = 0.05
MODEL_ORDER = 1
ACTIVITY_PADDING_DEG = 6.0
RESIDUAL_CEILING = 1.5
V3_RUN = 31235705928
V3_ARTIFACT = 9015557724
V3_ARTIFACT_DIGEST = "sha256:f702124b40452624ffc7210e52978e6d9622e60f0a000af3299abda81e3fa7d7"
V3_SOURCE_COMMIT = "c386f1570a82ce0ce9700e962bb650c3ba5af66e"


def wrap180(x: np.ndarray | float) -> np.ndarray:
    return (np.asarray(x, dtype=np.float64) + 180.0) % 360.0 - 180.0


def circular_mean_deg(values: list[float]) -> float:
    a = np.radians(np.asarray(values, dtype=np.float64) % 360.0)
    c = float(np.mean(np.cos(a)))
    s = float(np.mean(np.sin(a)))
    v1.require(abs(c) + abs(s) > 1e-15, "undefined circular mean")
    return float(np.degrees(np.arctan2(s, c)) % 360.0)


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    v1.require(len(x) == len(y) and len(x) >= 2, "invalid affine fit sample")
    design = np.column_stack((np.ones(len(x), dtype=np.float64), np.asarray(x, dtype=np.float64)))
    beta = np.linalg.lstsq(design, np.asarray(y, dtype=np.float64), rcond=None)[0]
    return float(beta[0]), float(beta[1])


def fit_trajectory(events: list[dict[str, Any]]) -> dict[str, float]:
    v1.require(len(events) >= 3, "trajectory fit has fewer than three events")
    sol0 = circular_mean_deg([float(e["sol"]) for e in events])
    lon0 = circular_mean_deg([float(e["sun_lon"]) for e in events])
    x = wrap180(np.asarray([float(e["sol"]) for e in events]) - sol0)
    ylon = wrap180(np.asarray([float(e["sun_lon"]) for e in events]) - lon0)
    lat = np.asarray([float(e["ecl_lat"]) for e in events], dtype=np.float64)
    vg = np.asarray([float(e["vg"]) for e in events], dtype=np.float64)
    lon_intercept, lon_slope = fit_line(x, ylon)
    lat_intercept, lat_slope = fit_line(x, lat)
    vg_intercept, vg_slope = fit_line(x, vg)
    return {
        "sol0": sol0, "lon0": lon0,
        "lon_intercept": lon_intercept, "lon_slope": lon_slope,
        "lat_intercept": lat_intercept, "lat_slope": lat_slope,
        "vg_intercept": vg_intercept, "vg_slope": vg_slope,
    }


def predict(model: dict[str, float], events: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not events:
        return np.empty(0), np.empty(0), np.empty(0)
    sol = np.asarray([float(e["sol"]) for e in events], dtype=np.float64)
    x = wrap180(sol - float(model["sol0"]))
    lon = (float(model["lon0"]) + float(model["lon_intercept"]) + float(model["lon_slope"]) * x) % 360.0
    lat = float(model["lat_intercept"]) + float(model["lat_slope"]) * x
    vg = float(model["vg_intercept"]) + float(model["vg_slope"]) * x
    return np.asarray(lon), np.asarray(lat), np.asarray(vg)


def trajectory_residuals(model: dict[str, float], events: list[dict[str, Any]]) -> np.ndarray:
    if not events:
        return np.empty(0, dtype=np.float64)
    lon_hat, lat_hat, vg_hat = predict(model, events)
    lon = np.asarray([float(e["sun_lon"]) for e in events], dtype=np.float64)
    lat = np.asarray([float(e["ecl_lat"]) for e in events], dtype=np.float64)
    vg = np.asarray([float(e["vg"]) for e in events], dtype=np.float64)
    dlon = wrap180(lon - lon_hat) * np.cos(np.radians(0.5 * (lat + lat_hat))) / 2.0
    dlat = (lat - lat_hat) / 2.0
    dvg = (vg - vg_hat) / 2.0
    return np.sqrt(dlon*dlon + dlat*dlat + dvg*dvg)


def loo_residuals(source_events: list[dict[str, Any]]) -> np.ndarray:
    n = len(source_events)
    v1.require(n >= 4, "trajectory source has fewer than four original seeds")
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        train = source_events[:i] + source_events[i+1:]
        model = fit_trajectory(train)
        out[i] = trajectory_residuals(model, [source_events[i]])[0]
    return out


def conformal_pvalues(target: np.ndarray, reference: np.ndarray) -> np.ndarray:
    ref = np.sort(np.asarray(reference, dtype=np.float64))
    n = len(ref)
    ge = n - np.searchsorted(ref, np.asarray(target, dtype=np.float64), side="left")
    return (1.0 + ge.astype(np.float64)) / float(n + 1)


def in_activity_arc(sol: np.ndarray, source_values: list[float]) -> np.ndarray:
    start, end = v1.circular_arc(source_values)
    width = (end - start) % 360.0
    if width + 2.0 * ACTIVITY_PADDING_DEG >= 360.0:
        return np.ones(len(sol), dtype=bool)
    s = (start - ACTIVITY_PADDING_DEG) % 360.0
    e = (end + ACTIVITY_PADDING_DEG) % 360.0
    return (sol >= s) | (sol <= e) if s > e else (sol >= s) & (sol <= e)


def crossfit_expand_trajectory(
    families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        "model_order": MODEL_ORDER,
        "conformal_alpha": ALPHA,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "residual_ceiling": RESIDUAL_CEILING,
        "residual_formula": "sqrt((dlon*cos(mean_lat)/2)^2 + (dlat/2)^2 + (dvg/2)^2)",
        "conformal_formula": "(1 + count(source_loo_residual >= target_residual)) / (n_source + 1)",
        "new_members_by_year": {},
        "arc_candidate_pairs_by_year": {},
        "ceiling_rejected_pairs_by_year": {},
        "conformal_rejected_pairs_by_year": {},
        "accepted_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "source_loo_residual_median_by_year": {},
        "source_loo_residual_p95_by_year": {},
        "assigned_residual_median_by_year": {},
        "assigned_p_median_by_year": {},
        "original_seed_events_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "alpha_selected_by_search": False,
        "model_order_selected_by_search": False,
        "activity_padding_selected_by_search": False,
        "residual_ceiling_selected_by_search": False,
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

        best: dict[str, tuple[float, str, float]] = {}
        arc_pairs = ceiling_rejected = conformal_rejected = accepted_pairs = 0
        loo_all: list[float] = []
        for family in families:
            fid = str(family["family_id"])
            source_ids = sorted(original[fid] & set(event_lookup[source_year]))
            v1.require(len(source_ids) >= 4, f"family {fid} has fewer than four other-year original seeds")
            source_events = [event_lookup[source_year][eid] for eid in source_ids]
            model = fit_trajectory(source_events)
            loo = loo_residuals(source_events)
            loo_all.extend(float(x) for x in loo)

            mask = in_activity_arc(target_sol, [float(e["sol"]) for e in source_events])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            residual = trajectory_residuals(model, candidates)
            pvals = conformal_pvalues(residual, loo)
            for i, r, p in zip(idx.tolist(), residual.tolist(), pvals.tolist()):
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                arc_pairs += 1
                if float(r) > RESIDUAL_CEILING + 1e-12:
                    ceiling_rejected += 1
                    continue
                if float(p) <= ALPHA + 1e-15:
                    conformal_rejected += 1
                    continue
                accepted_pairs += 1
                cand = (float(r), fid, float(p))
                old = best.get(event_id)
                if old is None or (cand[0], cand[1]) < (old[0], old[1]):
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_residual: list[float] = []
        assigned_p: list[float] = []
        for eid, (r, fid, p) in best.items():
            by_family[fid].append(eid)
            assigned_residual.append(float(r)); assigned_p.append(float(p))
        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["arc_candidate_pairs_by_year"][str(target_year)] = arc_pairs
        diagnostics["ceiling_rejected_pairs_by_year"][str(target_year)] = ceiling_rejected
        diagnostics["conformal_rejected_pairs_by_year"][str(target_year)] = conformal_rejected
        diagnostics["accepted_pairs_by_year"][str(target_year)] = accepted_pairs
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, accepted_pairs - len(best))
        diagnostics["source_loo_residual_median_by_year"][str(target_year)] = float(np.median(loo_all))
        diagnostics["source_loo_residual_p95_by_year"][str(target_year)] = float(np.quantile(loo_all, 0.95))
        diagnostics["assigned_residual_median_by_year"][str(target_year)] = float(np.median(assigned_residual)) if assigned_residual else None
        diagnostics["assigned_p_median_by_year"][str(target_year)] = float(np.median(assigned_p)) if assigned_p else None
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)

    for before, after in zip(sorted(families, key=lambda x: str(x["family_id"])), sorted(expanded, key=lambda x: str(x["family_id"]))):
        v1.require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in ("years", "year_count", "component_ids", "component_count", "quartet_count", "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids"):
            v1.require(before[field] == after[field], f"expansion changed frozen family field {field}")
        v1.require(set(before["event_ids"]).issubset(set(after["event_ids"])), "seed membership lost")

    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = v1.sha256_json({str(f["family_id"]): f["event_ids"] for f in expanded})
    return expanded, diagnostics, assignments


def main() -> int:
    v1.crossfit_expand = crossfit_expand_trajectory
    v1.CORPUS = "orbittrace-cross-year-trajectory-conformal-expansion-v4-development"
    rc = v1.main()
    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "other-year affine radiant/speed trajectory vs solar longitude; source LOO residual conformal p>0.05; residual<=1.5; source activity arc+/-6deg; exclusive minimum-residual assignment",
        "conformal_alpha": ALPHA,
        "trajectory_model_order": MODEL_ORDER,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "residual_ceiling": RESIDUAL_CEILING,
        "alpha_search": False,
        "trajectory_model_search": False,
        "activity_padding_search": False,
        "residual_ceiling_search": False,
        "v3_predecessor_run": V3_RUN,
        "v3_predecessor_artifact": V3_ARTIFACT,
        "v3_predecessor_artifact_digest": V3_ARTIFACT_DIGEST,
        "v3_source_commit": V3_SOURCE_COMMIT,
    })
    d = result["expansion_diagnostics"]
    ig = result["integrity_gates"]
    ig["exact_affine_model_order_1"] = int(d["model_order"]) == 1
    ig["exact_conformal_alpha_005"] = abs(float(d["conformal_alpha"]) - 0.05) <= 1e-15
    ig["exact_inherited_activity_padding_6deg"] = abs(float(d["activity_padding_deg"]) - 6.0) <= 1e-15
    ig["exact_inherited_residual_ceiling_1_5"] = abs(float(d["residual_ceiling"]) - 1.5) <= 1e-15
    ig["trajectory_parameters_not_selected_by_search"] = all([
        d["alpha_selected_by_search"] is False,
        d["model_order_selected_by_search"] is False,
        d["activity_padding_selected_by_search"] is False,
        d["residual_ceiling_selected_by_search"] is False,
    ])
    result["claim_boundary"] = (
        "Target-excluded v4 development only. Exact v8 discovery families and ranking were frozen before any membership fit. "
        "Each target year used only original other-year v8 seeds to fit an affine radiant/speed trajectory versus solar longitude, "
        "with leave-one-out source residual conformal calibration. No OrbitTrace target information, target-region event, Stage A/B output, "
        "slope/model/alpha/padding/radius search, same-year fit, or literature-benchmark parameter tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = "PASS_CROSS_YEAR_TRAJECTORY_CONFORMAL_EXPANSION_V4_DEVELOPMENT" if passed else "FAIL_CROSS_YEAR_TRAJECTORY_CONFORMAL_EXPANSION_V4_DEVELOPMENT"

    (out / "cross_year_trajectory_conformal_expansion_v4_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_trajectory_conformal_expanded_families.json").write_bytes((out / "cross_year_seed_support_expanded_families.json").read_bytes())
    (out / "cross_year_trajectory_conformal_assignments.json").write_bytes((out / "cross_year_seed_support_assignments.json").read_bytes())
    bm = result["baseline_metrics"]["multiplicity"]; em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace cross-year trajectory-conformal expansion v4 development", "", f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{d['total_new_members']}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**")
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_TRAJECTORY_CONFORMAL_EXPANSION_V4_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
