#!/usr/bin/env python3
"""Final one-shot joint density + trajectory conformal membership successor on frozen v8 seeds."""
from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_conformal_density_expansion_v3 import run_development as v3
from orbittrace_cross_year_trajectory_conformal_expansion_v4 import run_development as v4

v1 = v3.v1

ALPHA = 0.05
NEIGHBOR_ORDER = 2
MODEL_ORDER = 1
ACTIVITY_PADDING_DEG = 6.0
DENSITY_CEILING = 1.5
TRAJECTORY_CEILING = 1.5
FISHER_WEIGHTS = (1.0, 1.0)

V3_RUN = 31235705928
V3_ARTIFACT = 9015557724
V3_ARTIFACT_DIGEST = "sha256:f702124b40452624ffc7210e52978e6d9622e60f0a000af3299abda81e3fa7d7"
V3_SOURCE_COMMIT = "c386f1570a82ce0ce9700e962bb650c3ba5af66e"
V4_RUN = 31236717050
V4_ARTIFACT = 9015902170
V4_ARTIFACT_DIGEST = "sha256:394a03e4ba9ef2013adb4e22e3708f7d330fdd80b4ab603a102829afda50287c"
V4_SOURCE_COMMIT = "d178ad4bca2991356bbafcd1b92b233ad2a25f44"


def source_empirical_pvalues(values: np.ndarray) -> np.ndarray:
    """Inclusive empirical upper-tail ranks for source LOO nonconformities."""
    x = np.asarray(values, dtype=np.float64)
    v1.require(x.ndim == 1 and len(x) >= 4 and np.all(np.isfinite(x)), "invalid source empirical reference")
    ordered = np.sort(x)
    ge = len(x) - np.searchsorted(ordered, x, side="left")
    p = ge.astype(np.float64) / float(len(x))
    v1.require(np.all((p > 0.0) & (p <= 1.0)), "invalid source empirical p-value")
    return p


def target_empirical_pvalues(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Conservative finite-sample upper-tail empirical p-values for target values."""
    x = np.asarray(values, dtype=np.float64)
    ref = np.sort(np.asarray(reference, dtype=np.float64))
    v1.require(ref.ndim == 1 and len(ref) >= 4 and np.all(np.isfinite(ref)), "invalid target empirical reference")
    ge = len(ref) - np.searchsorted(ref, x, side="left")
    p = (1.0 + ge.astype(np.float64)) / float(len(ref) + 1)
    v1.require(np.all((p > 0.0) & (p <= 1.0)), "invalid target empirical p-value")
    return p


def fisher_nonconformity(p_density: np.ndarray, p_trajectory: np.ndarray) -> np.ndarray:
    pd = np.asarray(p_density, dtype=np.float64)
    pt = np.asarray(p_trajectory, dtype=np.float64)
    v1.require(pd.shape == pt.shape, "joint p-value arrays differ in shape")
    v1.require(np.all((pd > 0.0) & (pd <= 1.0)) and np.all((pt > 0.0) & (pt <= 1.0)), "invalid Fisher marginal p-value")
    return -2.0 * (np.log(pd) + np.log(pt))


def joint_conformal_pvalues(target_scores: np.ndarray, source_scores: np.ndarray) -> np.ndarray:
    s = np.asarray(target_scores, dtype=np.float64)
    ref = np.sort(np.asarray(source_scores, dtype=np.float64))
    v1.require(ref.ndim == 1 and len(ref) >= 4 and np.all(np.isfinite(ref)), "invalid joint conformal reference")
    ge = len(ref) - np.searchsorted(ref, s, side="left")
    p = (1.0 + ge.astype(np.float64)) / float(len(ref) + 1)
    v1.require(np.all((p > 0.0) & (p <= 1.0)), "invalid joint conformal p-value")
    return p


def crossfit_expand_joint(
    families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}

    diagnostics: dict[str, Any] = {
        "neighbor_order": NEIGHBOR_ORDER,
        "trajectory_model_order": MODEL_ORDER,
        "conformal_alpha": ALPHA,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "density_ceiling": DENSITY_CEILING,
        "trajectory_ceiling": TRAJECTORY_CEILING,
        "fisher_weights": list(FISHER_WEIGHTS),
        "source_density_p_formula": "count(source_loo_d2 >= d2_i) / n",
        "source_trajectory_p_formula": "count(source_loo_residual >= r_i) / n",
        "target_marginal_p_formula": "(1 + count(source_reference >= target_value)) / (n + 1)",
        "fisher_formula": "-2*(log(p_density)+log(p_trajectory))",
        "joint_conformal_formula": "(1 + count(source_fisher >= target_fisher)) / (n + 1)",
        "acceptance_rule": "activity arc +/-6deg AND d2<=1.5 AND residual<=1.5 AND p_joint>0.05",
        "new_members_by_year": {},
        "activity_candidate_pairs_by_year": {},
        "density_ceiling_rejected_pairs_by_year": {},
        "trajectory_ceiling_rejected_pairs_by_year": {},
        "joint_conformal_rejected_pairs_by_year": {},
        "joint_eligible_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "source_density_p_median_by_year": {},
        "source_trajectory_p_median_by_year": {},
        "source_fisher_median_by_year": {},
        "assigned_joint_p_median_by_year": {},
        "assigned_joint_p_min_by_year": {},
        "assigned_fisher_median_by_year": {},
        "assigned_density_d2_median_by_year": {},
        "assigned_trajectory_residual_median_by_year": {},
        "original_seed_events_by_year": {},
        "exclusive_assignment": True,
        "exclusive_assignment_rule": "largest joint conformal p; tie smaller Fisher nonconformity; tie stable family id",
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "joint_rule_selected_by_search": False,
        "fisher_weights_selected_by_search": False,
        "alpha_selected_by_search": False,
        "hard_ceilings_selected_by_search": False,
        "model_or_neighbor_order_selected_by_search": False,
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

        # event -> (joint p, Fisher S, family id, d2, trajectory residual)
        best: dict[str, tuple[float, float, str, float, float]] = {}
        activity_pairs = density_reject = trajectory_reject = joint_reject = joint_eligible = 0
        source_pd_all: list[float] = []
        source_pt_all: list[float] = []
        source_s_all: list[float] = []

        for family in families:
            fid = str(family["family_id"])
            source_ids = sorted(original[fid] & set(event_lookup[source_year]))
            v1.require(len(source_ids) >= 4, f"family {fid} has fewer than four other-year original seeds")
            source_events = [event_lookup[source_year][eid] for eid in source_ids]

            source_d2 = v3.source_leave_one_out_d2(source_events)
            source_r = v4.loo_residuals(source_events)
            v1.require(len(source_d2) == len(source_events) == len(source_r), "source joint reference length mismatch")
            source_pd = source_empirical_pvalues(source_d2)
            source_pt = source_empirical_pvalues(source_r)
            source_s = fisher_nonconformity(source_pd, source_pt)
            source_pd_all.extend(float(x) for x in source_pd)
            source_pt_all.extend(float(x) for x in source_pt)
            source_s_all.extend(float(x) for x in source_s)

            model = v4.fit_trajectory(source_events)
            mask = v4.in_activity_arc(target_sol, [float(e["sol"]) for e in source_events])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            _d1, target_d2 = v3.target_d1_d2(candidates, source_events)
            target_r = v4.trajectory_residuals(model, candidates)
            target_pd = target_empirical_pvalues(target_d2, source_d2)
            target_pt = target_empirical_pvalues(target_r, source_r)
            target_s = fisher_nonconformity(target_pd, target_pt)
            target_joint_p = joint_conformal_pvalues(target_s, source_s)

            for i, d2, residual, fisher_s, p_joint in zip(
                idx.tolist(), target_d2.tolist(), target_r.tolist(), target_s.tolist(), target_joint_p.tolist()
            ):
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                activity_pairs += 1
                if float(d2) > DENSITY_CEILING + 1e-12:
                    density_reject += 1
                    continue
                if float(residual) > TRAJECTORY_CEILING + 1e-12:
                    trajectory_reject += 1
                    continue
                if float(p_joint) <= ALPHA + 1e-15:
                    joint_reject += 1
                    continue
                joint_eligible += 1
                cand = (float(p_joint), float(fisher_s), fid, float(d2), float(residual))
                old = best.get(event_id)
                if old is None or (-cand[0], cand[1], cand[2]) < (-old[0], old[1], old[2]):
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_p: list[float] = []
        assigned_s: list[float] = []
        assigned_d2: list[float] = []
        assigned_r: list[float] = []
        for eid, (p_joint, fisher_s, fid, d2, residual) in best.items():
            by_family[fid].append(eid)
            assigned_p.append(float(p_joint))
            assigned_s.append(float(fisher_s))
            assigned_d2.append(float(d2))
            assigned_r.append(float(residual))

        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        y = str(target_year)
        diagnostics["new_members_by_year"][y] = len(best)
        diagnostics["activity_candidate_pairs_by_year"][y] = activity_pairs
        diagnostics["density_ceiling_rejected_pairs_by_year"][y] = density_reject
        diagnostics["trajectory_ceiling_rejected_pairs_by_year"][y] = trajectory_reject
        diagnostics["joint_conformal_rejected_pairs_by_year"][y] = joint_reject
        diagnostics["joint_eligible_pairs_by_year"][y] = joint_eligible
        diagnostics["conflicted_events_by_year"][y] = max(0, joint_eligible - len(best))
        diagnostics["source_density_p_median_by_year"][y] = float(np.median(source_pd_all))
        diagnostics["source_trajectory_p_median_by_year"][y] = float(np.median(source_pt_all))
        diagnostics["source_fisher_median_by_year"][y] = float(np.median(source_s_all))
        diagnostics["assigned_joint_p_median_by_year"][y] = float(np.median(assigned_p)) if assigned_p else None
        diagnostics["assigned_joint_p_min_by_year"][y] = float(min(assigned_p)) if assigned_p else None
        diagnostics["assigned_fisher_median_by_year"][y] = float(np.median(assigned_s)) if assigned_s else None
        diagnostics["assigned_density_d2_median_by_year"][y] = float(np.median(assigned_d2)) if assigned_d2 else None
        diagnostics["assigned_trajectory_residual_median_by_year"][y] = float(np.median(assigned_r)) if assigned_r else None
        diagnostics["original_seed_events_by_year"][y] = len(target_seed_owner)

    for before, after in zip(
        sorted(families, key=lambda x: str(x["family_id"])),
        sorted(expanded, key=lambda x: str(x["family_id"])),
    ):
        v1.require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in (
            "years", "year_count", "component_ids", "component_count", "quartet_count",
            "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids",
        ):
            v1.require(before[field] == after[field], f"joint expansion changed frozen family field {field}")
        v1.require(set(before["event_ids"]).issubset(set(after["event_ids"])), "seed membership lost")

    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = v1.sha256_json(
        {str(f["family_id"]): f["event_ids"] for f in expanded}
    )
    return expanded, diagnostics, assignments


def main() -> int:
    v1.crossfit_expand = crossfit_expand_joint
    v1.CORPUS = "orbittrace-joint-density-trajectory-conformal-v5-development"
    rc = v1.main()
    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())

    result["configuration"].update({
        "membership_rule": "joint empirically recalibrated equal-weight Fisher conformity over v3 density d2 and v4 trajectory residual, with inherited activity arc and d2/residual ceilings",
        "conformal_alpha": ALPHA,
        "neighbor_order": NEIGHBOR_ORDER,
        "trajectory_model_order": MODEL_ORDER,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "density_ceiling": DENSITY_CEILING,
        "trajectory_ceiling": TRAJECTORY_CEILING,
        "joint_combiner": "equal-weight Fisher nonconformity empirically recalibrated on source seeds",
        "fisher_weights": list(FISHER_WEIGHTS),
        "joint_rule_search": False,
        "weight_search": False,
        "alpha_search": False,
        "neighbor_or_model_order_search": False,
        "ceiling_or_padding_search": False,
        "v3_predecessor_run": V3_RUN,
        "v3_predecessor_artifact": V3_ARTIFACT,
        "v3_predecessor_artifact_digest": V3_ARTIFACT_DIGEST,
        "v3_source_commit": V3_SOURCE_COMMIT,
        "v4_predecessor_run": V4_RUN,
        "v4_predecessor_artifact": V4_ARTIFACT,
        "v4_predecessor_artifact_digest": V4_ARTIFACT_DIGEST,
        "v4_source_commit": V4_SOURCE_COMMIT,
        "development_pass_requires_fresh_prospective_validation_before_any_promotion_claim": True,
    })

    d = result["expansion_diagnostics"]
    ig = result["integrity_gates"]
    ig["exact_joint_alpha_005"] = abs(float(d["conformal_alpha"]) - 0.05) <= 1e-15
    ig["exact_v3_neighbor_order_2"] = int(d["neighbor_order"]) == 2
    ig["exact_v4_model_order_1"] = int(d["trajectory_model_order"]) == 1
    ig["exact_inherited_activity_padding_6deg"] = abs(float(d["activity_padding_deg"]) - 6.0) <= 1e-15
    ig["exact_inherited_density_ceiling_1_5"] = abs(float(d["density_ceiling"]) - 1.5) <= 1e-15
    ig["exact_inherited_trajectory_ceiling_1_5"] = abs(float(d["trajectory_ceiling"]) - 1.5) <= 1e-15
    ig["exact_equal_fisher_weights"] = d["fisher_weights"] == [1.0, 1.0]
    ig["joint_statistic_empirically_recalibrated"] = d["joint_conformal_formula"].startswith("(1 + count(source_fisher")
    ig["no_joint_parameter_search"] = all([
        d["joint_rule_selected_by_search"] is False,
        d["fisher_weights_selected_by_search"] is False,
        d["alpha_selected_by_search"] is False,
        d["hard_ceilings_selected_by_search"] is False,
        d["model_or_neighbor_order_selected_by_search"] is False,
    ])

    result["claim_boundary"] = (
        "Final target-excluded v5 development candidate in this membership chain. Exact v8 discovery families and ranking were frozen first. "
        "Only original other-year v8 seeds supplied the inherited v3 density and v4 trajectory channels; their equal-weight Fisher nonconformity "
        "was empirically recalibrated against source seeds before target-year membership was frozen. No OrbitTrace target information, target-region event, "
        "Stage A/B output, weight/alpha/radius/model/neighbor/combiner search, same-year training, recursive growth, or literature-benchmark tuning entered the method. "
        "Even a development pass authorizes only fresh prospective validation, not method promotion or OrbitTrace reveal."
    )

    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_JOINT_DENSITY_TRAJECTORY_CONFORMAL_V5_DEVELOPMENT"
        if passed else "FAIL_JOINT_DENSITY_TRAJECTORY_CONFORMAL_V5_DEVELOPMENT"
    )
    result["development_chain_decision"] = (
        "FREEZE_AND_REQUIRE_FRESH_PROSPECTIVE_VALIDATION" if passed
        else "CLOSE_POST_DISCOVERY_MEMBERSHIP_DEVELOPMENT_CHAIN"
    )

    (out / "joint_density_trajectory_conformal_v5_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (out / "joint_density_trajectory_conformal_v5_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "joint_density_trajectory_conformal_v5_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace joint density + trajectory conformal v5 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- chain decision: **`{result['development_chain_decision']}`**",
        f"- newly assigned events: **{d['total_new_members']}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**")
    lines += [
        "",
        "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged.",
        "A pass is development-only and requires fresh prospective validation before any promotion or literature claim.",
    ]
    (out / "JOINT_DENSITY_TRAJECTORY_CONFORMAL_V5_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")

    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
