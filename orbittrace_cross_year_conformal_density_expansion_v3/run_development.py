#!/usr/bin/env python3
"""One-shot family-density-normalized conformal membership expansion on frozen v8 seeds."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

ALPHA = 0.05
NEIGHBOR_ORDER = 2
V2_RUN = 31234638558
V2_ARTIFACT = 9015207416
V2_ARTIFACT_DIGEST = "sha256:b16a01a154cd43c0a6e6f8af2f013d9ee35260757f6178366f0b2a3643436219"
V2_SOURCE_COMMIT = "5a3cf9b9a4b3b7bc08570cb7346ec1cfce9f5fd0"


def exact_distance_matrix(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> np.ndarray:
    if not left or not right:
        return np.empty((len(left), len(right)), dtype=np.float64)
    rs = np.asarray([float(e["sol"]) for e in right], dtype=np.float64)
    rl = np.asarray([float(e["sun_lon"]) for e in right], dtype=np.float64)
    rb = np.asarray([float(e["ecl_lat"]) for e in right], dtype=np.float64)
    rv = np.asarray([float(e["vg"]) for e in right], dtype=np.float64)
    out = np.empty((len(left), len(right)), dtype=np.float64)
    for lo in range(0, len(left), 1024):
        rows = left[lo : lo + 1024]
        ls = np.asarray([float(e["sol"]) for e in rows])[:, None]
        ll = np.asarray([float(e["sun_lon"]) for e in rows])[:, None]
        lb = np.asarray([float(e["ecl_lat"]) for e in rows])[:, None]
        lv = np.asarray([float(e["vg"]) for e in rows])[:, None]
        dsol = ((ls - rs[None, :] + 180.0) % 360.0 - 180.0) / 4.0
        dlon_raw = ((ll - rl[None, :] + 180.0) % 360.0 - 180.0)
        dlon = dlon_raw * np.cos(np.radians(0.5 * (lb + rb[None, :]))) / 2.0
        dlat = (lb - rb[None, :]) / 2.0
        dvg = (lv - rv[None, :]) / 2.0
        out[lo : lo + len(rows)] = np.sqrt(dsol*dsol + dlon*dlon + dlat*dlat + dvg*dvg)
    return out


def source_leave_one_out_d2(source_events: list[dict[str, Any]]) -> np.ndarray:
    v1.require(len(source_events) >= 4, "conformal source family-year has fewer than four original seeds")
    d = exact_distance_matrix(source_events, source_events)
    np.fill_diagonal(d, np.inf)
    return np.partition(d, 1, axis=1)[:, 1]


def target_d1_d2(target_events: list[dict[str, Any]], source_events: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    d = exact_distance_matrix(target_events, source_events)
    if not len(target_events):
        return np.empty(0), np.empty(0)
    v1.require(d.shape[1] >= 2, "target family support has fewer than two seeds")
    part = np.partition(d, 1, axis=1)
    return part[:, 0], part[:, 1]


def conformal_pvalues(target_d2: np.ndarray, source_loo_d2: np.ndarray) -> np.ndarray:
    ref = np.sort(np.asarray(source_loo_d2, dtype=np.float64))
    n = len(ref)
    ge = n - np.searchsorted(ref, np.asarray(target_d2, dtype=np.float64), side="left")
    return (1.0 + ge.astype(np.float64)) / float(n + 1)


def crossfit_expand_conformal(
    families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        "radius_hard_ceiling": v1.RADIUS,
        "solar_prefilter_deg": v1.SOL_PREFILTER,
        "neighbor_order": NEIGHBOR_ORDER,
        "conformal_alpha": ALPHA,
        "conformal_formula": "(1 + count(source_loo_d2 >= target_d2)) / (n_source + 1)",
        "acceptance_rule": "target_d2 <= 1.5 and conformal_p > 0.05",
        "new_members_by_year": {},
        "two_witness_pairs_by_year": {},
        "conformal_rejected_pairs_by_year": {},
        "conformal_eligible_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "assigned_p_median_by_year": {},
        "assigned_p_min_by_year": {},
        "source_loo_d2_median_by_year": {},
        "source_loo_d2_p95_by_year": {},
        "original_seed_events_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "alpha_selected_by_search": False,
        "neighbor_order_selected_by_search": False,
    }

    for target_year in v1.YEARS:
        source_year = v1.YEARS[1] if target_year == v1.YEARS[0] else v1.YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events])
        source_ids_by_family = {
            fid: sorted(ids & set(event_lookup[source_year])) for fid, ids in original.items()
        }
        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str, float]] = {}
        two_witness_pairs = 0
        conformal_rejected = 0
        conformal_eligible = 0
        source_spacing_values: list[float] = []
        for family in families:
            fid = str(family["family_id"])
            source_ids = source_ids_by_family[fid]
            v1.require(len(source_ids) >= 4, f"family {fid} has fewer than four other-year original seeds")
            source_events = [event_lookup[source_year][eid] for eid in source_ids]
            loo_d2 = source_leave_one_out_d2(source_events)
            source_spacing_values.extend(float(x) for x in loo_d2)

            mask = v1.in_expanded_arc(target_sol, [float(e["sol"]) for e in source_events])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            d1, d2 = target_d1_d2(candidates, source_events)
            pvals = conformal_pvalues(d2, loo_d2)
            for i, nearest, second, p in zip(idx.tolist(), d1.tolist(), d2.tolist(), pvals.tolist()):
                if second > v1.RADIUS + 1e-12:
                    continue
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                two_witness_pairs += 1
                if float(p) <= ALPHA + 1e-15:
                    conformal_rejected += 1
                    continue
                conformal_eligible += 1
                cand = (float(nearest), fid, float(p))
                old = best.get(event_id)
                if old is None or (cand[0], cand[1]) < (old[0], old[1]):
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_p: list[float] = []
        for eid, (_d1, fid, p) in best.items():
            by_family[fid].append(eid)
            assigned_p.append(float(p))
        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["two_witness_pairs_by_year"][str(target_year)] = two_witness_pairs
        diagnostics["conformal_rejected_pairs_by_year"][str(target_year)] = conformal_rejected
        diagnostics["conformal_eligible_pairs_by_year"][str(target_year)] = conformal_eligible
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, conformal_eligible - len(best))
        diagnostics["assigned_p_median_by_year"][str(target_year)] = float(np.median(assigned_p)) if assigned_p else None
        diagnostics["assigned_p_min_by_year"][str(target_year)] = float(min(assigned_p)) if assigned_p else None
        diagnostics["source_loo_d2_median_by_year"][str(target_year)] = float(np.median(source_spacing_values))
        diagnostics["source_loo_d2_p95_by_year"][str(target_year)] = float(np.quantile(source_spacing_values, 0.95))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)

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
    v1.crossfit_expand = crossfit_expand_conformal
    v1.CORPUS = "orbittrace-cross-year-conformal-density-expansion-v3-development"
    rc = v1.main()
    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "other-year second-nearest seed distance <=1.5 plus family-specific leave-one-out d2 conformal p >0.05; exclusive nearest-family assignment",
        "conformal_alpha": ALPHA,
        "neighbor_order": NEIGHBOR_ORDER,
        "alpha_source": "predeclared conventional finite-sample conformal rejection level",
        "alpha_search": False,
        "neighbor_order_source": "inherited v2 two-witness geometry",
        "neighbor_order_search": False,
        "v2_predecessor_run": V2_RUN,
        "v2_predecessor_artifact": V2_ARTIFACT,
        "v2_predecessor_artifact_digest": V2_ARTIFACT_DIGEST,
        "v2_source_commit": V2_SOURCE_COMMIT,
    })
    diag = result["expansion_diagnostics"]
    result["integrity_gates"]["exact_conformal_alpha_005"] = abs(float(diag["conformal_alpha"]) - 0.05) <= 1e-15
    result["integrity_gates"]["exact_second_neighbor_order"] = int(diag["neighbor_order"]) == 2
    result["integrity_gates"]["alpha_not_selected_by_search"] = diag["alpha_selected_by_search"] is False
    result["integrity_gates"]["neighbor_order_not_selected_by_search"] = diag["neighbor_order_selected_by_search"] is False
    result["claim_boundary"] = (
        "Target-excluded v3 development only. Exact v8 families and ranking were frozen before a family-specific "
        "leave-one-out second-neighbor conformal membership gate was applied using only original other-year seeds. "
        "No OrbitTrace target information, target-region event, Stage A/B output, alpha search, neighbor-order search, "
        "radius search, or literature-benchmark parameter tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_CONFORMAL_DENSITY_EXPANSION_V3_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_CONFORMAL_DENSITY_EXPANSION_V3_DEVELOPMENT"
    )

    (out / "cross_year_conformal_density_expansion_v3_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (out / "cross_year_conformal_density_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_conformal_density_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace cross-year conformal-density expansion v3 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- conformal-rejected family-event pairs: **{sum(diag['conformal_rejected_pairs_by_year'].values())}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**")
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_CONFORMAL_DENSITY_EXPANSION_V3_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
