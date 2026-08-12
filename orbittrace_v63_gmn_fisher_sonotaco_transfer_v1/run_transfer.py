#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_v62_intrinsic_local_geometry_oof_v1 import run_transfer as v62
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
FEATURE_COLUMNS = v62.FEATURE_COLUMNS
FEATURE_DIM = 23
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
EXPECTED_COUNTS = {"sugar": 267, "hdbscan": 229}
EXPECTED_PRETRUTH_SHA = "1988fcb89781a3ba94d19bd7b2e0c058c13b39c73ed020f7931c772952069e64"
EXPECTED_FEATURE_SHA = {
    "sugar": "423c9aef746cd873270cf8950ce79d93620282d12161449ebc99863f748834c7",
    "hdbscan": "e0a8162e2b4d73df68552d56f0f81305e28cda1fc539d9e88943e42fb3394663",
}
EXPECTED_PARENT_ORDER_SHA = {
    "sugar": "5b3d27e11079f36148bbfb8bfdab60882fae380143fcfd84c6dc290c53295aae",
    "hdbscan": "85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d",
}
V31_PARENT_METRICS = {
    ("sugar", 2013): (0.2719801488280529, 16),
    ("sugar", 2014): (0.31529041952487225, 17),
    ("hdbscan", 2013): (0.14888037368183737, 9),
    ("hdbscan", 2014): (0.15198123772301594, 9),
}
GMN_FISHER_PASS = {
    "run_id": 31565972049,
    "job_id": 94017720509,
    "artifact_id": 9129508430,
    "artifact_digest": "sha256:d5338751651c4122dab4f91bc4e2b652b307c0f36d83d1f293fe68f5da8d15df",
    "recovered_at_100": 69,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7677499561973543,
    "mrr": 0.05055989766869564,
    "scaled_score_sha256": "9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(",", ":")).encode())
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(map(str, order)).encode()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def roots_from_args(a: argparse.Namespace) -> dict[str, Path]:
    return {"sugar": a.sugar_root, "hdbscan": a.hdbscan_root}


def fisher_oof(
    xall: np.ndarray,
    positive: np.ndarray,
    groups: list[str],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    folds = np.asarray([v22.v1.deterministic_fold(str(g)) for g in groups], dtype=int)
    require(set(folds.tolist()) == set(range(5)), "strict five-fold assignment changed")
    ref_margin = np.zeros(len(xall), dtype=np.float64)
    fisher = np.zeros(len(xall), dtype=np.float64)
    diagnostics: list[dict[str, Any]] = []

    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(tr)[0]}
        test_groups = {groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        require(positive[tr].any() and (~positive[tr]).any(), f"fold {fold} lacks both recoverability classes")

        mu = np.mean(xall[tr], axis=0)
        sd = np.std(xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (xall[tr] - mu[None, :]) / scale[None, :]
        zte = (xall[te] - mu[None, :]) / scale[None, :]
        require(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        pos = positive[tr]
        neg = ~pos
        P = ztr[pos]
        N = ztr[neg]
        require(len(P) >= 2 and len(N) >= 2, f"insufficient class references fold {fold}")

        mu_pos = np.mean(P, axis=0)
        mu_neg = np.mean(N, axis=0)
        require(np.isfinite(mu_pos).all() and np.isfinite(mu_neg).all(), f"nonfinite class means fold {fold}")

        lw_pos = LedoitWolf(assume_centered=False, store_precision=False).fit(P)
        lw_neg = LedoitWolf(assume_centered=False, store_precision=False).fit(N)
        cov_pos = np.asarray(lw_pos.covariance_, dtype=float)
        cov_neg = np.asarray(lw_neg.covariance_, dtype=float)
        for name, cov, shrink in (
            ("positive", cov_pos, float(lw_pos.shrinkage_)),
            ("nonpositive", cov_neg, float(lw_neg.shrinkage_)),
        ):
            require(cov.shape == (FEATURE_DIM, FEATURE_DIM), f"{name} covariance shape changed fold {fold}")
            require(np.isfinite(cov).all(), f"nonfinite {name} covariance fold {fold}")
            require(np.allclose(cov, cov.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} covariance fold {fold}")
            require(math.isfinite(shrink) and 0.0 <= shrink <= 1.0, f"invalid {name} shrinkage fold {fold}")

        pooled = 0.5 * (cov_pos + cov_neg)
        require(np.isfinite(pooled).all(), f"nonfinite pooled covariance fold {fold}")
        require(np.allclose(pooled, pooled.T, rtol=0.0, atol=1e-12), f"nonsymmetric pooled covariance fold {fold}")
        eigenvalues = np.linalg.eigvalsh(pooled)
        require(np.isfinite(eigenvalues).all() and float(np.min(eigenvalues)) > 0.0, f"pooled covariance not positive definite fold {fold}")

        delta = mu_pos - mu_neg
        direction = np.linalg.solve(pooled, delta)
        midpoint = 0.5 * (mu_pos + mu_neg)
        require(np.isfinite(direction).all() and np.isfinite(midpoint).all(), f"nonfinite Fisher geometry fold {fold}")
        require(float(np.linalg.norm(direction)) > 0.0, f"zero Fisher direction fold {fold}")

        te_idx = np.where(te)[0]
        for j, global_i in enumerate(te_idx.tolist()):
            point = zte[j]
            dpos = float(np.min(np.linalg.norm(P - point[None, :], axis=1)))
            dneg = float(np.min(np.linalg.norm(N - point[None, :], axis=1)))
            ref_margin[global_i] = dneg - dpos
            fisher[global_i] = float(np.dot(point - midpoint, direction))

        diagnostics.append({
            "fold": fold,
            "train_examples": int(tr.sum()),
            "test_examples": int(te.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "train_groups": len(train_groups),
            "test_groups": len(test_groups),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
            "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
            "pooled_min_eigenvalue": float(np.min(eigenvalues)),
            "pooled_max_eigenvalue": float(np.max(eigenvalues)),
            "class_mean_distance": float(np.linalg.norm(delta)),
            "fisher_direction_norm": float(np.linalg.norm(direction)),
        })

    require(np.isfinite(ref_margin).all(), "nonfinite auxiliary reference margin")
    require(np.isfinite(fisher).all(), "nonfinite Fisher OOF score")
    return ref_margin, fisher, diagnostics


def run_evaluate(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    roots = roots_from_args(a)

    overall = json.loads((a.pretruth_root / "V62_INTRINSIC_PRETRUTH.json").read_text())
    require(sha(a.pretruth_root / "V62_INTRINSIC_PRETRUTH.json") == EXPECTED_PRETRUTH_SHA, "v62 pretruth overall seal changed")
    require(overall["truth_accessed"] is False, "v62 pretruth truth flag changed")
    require(overall["selected_zero_based_columns"] == list(FEATURE_COLUMNS) and int(overall["feature_dimension"]) == FEATURE_DIM, "v62 intrinsic columns changed")
    require(overall["feature_search"] is False and overall["column_search"] is False, "v62 pretruth search flag invalid")

    parent = json.loads(a.parent_orders.read_text())
    require(parent["verdict"] == "PASS_EXACT_V31_PARENT_ORDER_RECONSTRUCTION" and parent["scientific_change"] is False, "v31 parent-order provenance invalid")
    for route in ROUTES:
        require(parent["routes"][route]["v31_fused_order_sha256"] == EXPECTED_PARENT_ORDER_SHA[route], f"{route} v31 parent order hash changed")

    truth: dict[tuple[str, int], Any] = {}
    frozen_eval: dict[tuple[str, int], Any] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((a.truth_root / f"truth_{route}_{year}.json").read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f"evaluation_{route}_{year}.json").read_text())

    ranker = v22.load_module(a.ranker_source, "frozen_839_v63_gmn_fisher_transfer")
    route_data: dict[str, Any] = {}
    xs: list[np.ndarray] = []
    positives: list[np.ndarray] = []
    groups: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    target_diag: dict[str, Any] = {}
    cursor = 0

    for route in ROUTES:
        root = roots[route]
        x, meta, memberships, centroids = v62.load_intrinsic(a.pretruth_root, route, root)
        require(array_sha(x) == EXPECTED_FEATURE_SHA[route], f"{route} exact v62 intrinsic feature seal changed")
        ids = list(map(str, meta["family_ids"]))
        fams = memberships["families"]
        require(len(ids) == EXPECTED_COUNTS[route] and [str(f["family_id"]) for f in fams] == ids, f"{route} family universe changed")

        by_year = {year: truth[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden: dict[str, str] = {}
        hidden.update(by_year[2013])
        hidden.update(by_year[2014])
        require(len(hidden) == len(by_year[2013]) + len(by_year[2014]), f"{route} duplicate IDs across years")
        family_truths = [v22.family_truth(f, hidden, eligible) for f in fams]
        y = np.asarray([bool(t["positive"]) for t in family_truths], dtype=bool)
        require(y.any() and (~y).any(), f"{route} recoverability target degenerate")
        route_groups = [
            ("SHOWER/" + str(t["best_label"])) if t["best_label"] is not None else (f"NEG/{route}/" + ids[i])
            for i, t in enumerate(family_truths)
        ]

        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        xs.append(x)
        positives.append(y)
        groups.extend(route_groups)
        route_data[route] = {
            "meta": meta,
            "fams": fams,
            "ids": ids,
            "centroids": centroids,
            "family_truths": family_truths,
            "eligible": eligible,
        }
        target_diag[route] = {
            "families": len(ids),
            "eligible_recurrent_showers": len(eligible),
            "positive_families": int(y.sum()),
            "nonpositive_families": int((~y).sum()),
        }

    xall = np.vstack(xs)
    positive_all = np.concatenate(positives)
    require(xall.shape == (cursor, FEATURE_DIM) and len(positive_all) == len(groups) == cursor, "stacked v63 input mismatch")
    require(cursor == sum(EXPECTED_COUNTS.values()), "stacked v63 candidate count changed")

    ref_margin, fisher_raw, fold_diag = fisher_oof(xall, positive_all, groups)
    ref_scale = float(np.median(np.abs(ref_margin)))
    fisher_scale = float(np.median(np.abs(fisher_raw)))
    require(math.isfinite(ref_scale) and ref_scale > 0.0, "invalid auxiliary reference median absolute margin")
    require(math.isfinite(fisher_scale) and fisher_scale > 0.0, "invalid Fisher median absolute score")
    unit_factor = float(ref_scale / fisher_scale)
    require(math.isfinite(unit_factor) and unit_factor > 0.0, "invalid Fisher unit factor")
    fisher_scaled = fisher_raw * unit_factor
    require(np.isfinite(fisher_scaled).all(), "nonfinite scaled Fisher score")

    variants: dict[str, list[dict[str, Any]]] = {}
    order_diag: dict[str, Any] = {}
    parent_controls: list[dict[str, Any]] = []

    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd["ids"]
        scores = fisher_scaled[lo:hi]
        tie = [(int(rd["meta"]["tie_rank"][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(scores, rd["centroids"], DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
        fisher_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd["meta"]["v19_order"]))
        fused = list(v19.fusion_orders(fisher_order, v19_order)["rank_sum"])
        variants[route] = v22.rerank(rd["fams"], fused)
        order_diag[route] = {
            "auxiliary_overall_reference_margin_sha256": v22.array_sha(ref_margin[lo:hi]),
            "fisher_raw_sha256": v22.array_sha(fisher_raw[lo:hi]),
            "fisher_scaled_sha256": v22.array_sha(scores),
            "local_diversity_order_sha256": order_sha(fisher_order),
            "fused_order_sha256": order_sha(fused),
            "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
            "fusion": "equal rank-sum with exact v19",
        }

        parent_order = list(map(str, parent["routes"][route]["v31_fused_order"]))
        require(order_sha(parent_order) == EXPECTED_PARENT_ORDER_SHA[route], f"{route} parent order payload changed")
        parent_ranked = v22.rerank(rd["fams"], parent_order)
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
            cur = v22.evaluate(parent_ranked, truth[(route, year)], budget)
            exp = V31_PARENT_METRICS[(route, year)]
            require(abs(float(cur["macro_f1"]) - exp[0]) < 1e-12 and int(cur["recovered_f1_gt_0_5"]) == exp[1], f"{route} {year} v31 parent control changed")
            parent_controls.append({"comparator": route, "year": year, **cur})

    panels: list[dict[str, Any]] = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
        cur = v22.evaluate(variants[route], truth[(route, year)], budget)
        lit = frozen_eval[(route, year)]["comparator_summary"]
        cm = float(cur["macro_f1"])
        cr = int(cur["recovered_f1_gt_0_5"])
        lm = float(lit["macro_f1"])
        lr = int(lit["recovered_f1_gt_0_5"])
        panels.append({
            "comparator": route,
            "year": year,
            "budget": budget,
            "candidate_macro_f1": cm,
            "literature_macro_f1": lm,
            "candidate_recovered_f1_gt_0_5": cr,
            "literature_recovered_f1_gt_0_5": lr,
            "parent_v31_macro_f1": V31_PARENT_METRICS[(route, year)][0],
            "parent_v31_recovered_f1_gt_0_5": V31_PARENT_METRICS[(route, year)][1],
            "superiority_pair_pass": bool(cm > lm and cr >= lr),
        })

    wins = sum(int(p["superiority_pair_pass"]) for p in panels)
    passed = wins == 4
    result = {
        "scientific_stage": "EXPOSED_SONOTACO_V63_GMN_BALANCED_SHRINKAGE_FISHER_TRANSFER_V1",
        "verdict": "PASS_V63_GMN_FISHER_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS" if passed else "FAIL_V63_GMN_FISHER_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS",
        "first_valid_outcome_binding": True,
        "scientific_motivation": "binding target-excluded GMN balanced-shrinkage Fisher PASS",
        "gmn_fisher_pass_provenance": GMN_FISHER_PASS,
        "candidate_count": cursor,
        "feature_dimension": FEATURE_DIM,
        "selected_zero_based_columns": list(FEATURE_COLUMNS),
        "pretruth_overall_sha256": sha(a.pretruth_root / "V62_INTRINSIC_PRETRUTH.json"),
        "route_feature_sha256": EXPECTED_FEATURE_SHA,
        "recoverability_target": "combined-two-year family positive iff best eligible recurrent label precision>=0.5 and overlap>=4",
        "annual_fisher_used": False,
        "strict_whole_shower_oof": True,
        "scaling": "fold-training mean and population std; zero std -> 1.0",
        "mechanism": "equal-class Ledoit-Wolf shrinkage Fisher discriminant",
        "positive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "nonpositive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "pooled_covariance": "0.5*Sigma_pos+0.5*Sigma_neg",
        "class_prior_geometry": "equal-prior midpoint",
        "auxiliary_reference_margin": "overall 23D k=1 Euclidean d_nonpositive-d_positive; units only; not evaluated",
        "reference_median_absolute_margin": ref_scale,
        "fisher_median_absolute_score": fisher_scale,
        "unit_factor": unit_factor,
        "fisher_scaled_all_sha256": array_sha(fisher_scaled),
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "one equal rank-sum with exact v19",
        "candidate_membership_changed": False,
        "source_pretruth_payload_immutable": True,
        "panel_wins": wins,
        "panels": panels,
        "v31_parent_controls": parent_controls,
        "target_diagnostics": target_diag,
        "fold_diagnostics": fold_diag,
        "order_diagnostics": order_diag,
        "feature_search": False,
        "column_search": False,
        "class_prior_search": False,
        "covariance_estimator_search": False,
        "covariance_weight_search": False,
        "regularization_search": False,
        "solver_search": False,
        "annual_reference_search": False,
        "annual_combiner_search": False,
        "local_geometry_blend_search": False,
        "route_specific_rule_search": False,
        "scale_statistic_search": False,
        "unit_transform_search": False,
        "threshold_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "source_quota_selected": False,
        "post_result_rescue": False,
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "blind_exclusion": [20.0, 55.0],
    }
    dump(a.output / "V63_GMN_FISHER_SONOTACO_TRANSFER_RESULT.json", result)
    print(json.dumps({
        "verdict": result["verdict"],
        "panel_wins": wins,
        "reference_scale": ref_scale,
        "fisher_scale": fisher_scale,
        "unit_factor": unit_factor,
        "fisher_scaled_all_sha256": result["fisher_scaled_all_sha256"],
        "panels": panels,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth-root", type=Path, required=True)
    p.add_argument("--sugar-root", type=Path, required=True)
    p.add_argument("--hdbscan-root", type=Path, required=True)
    p.add_argument("--truth-root", type=Path, required=True)
    p.add_argument("--ranker-source", type=Path, required=True)
    p.add_argument("--parent-orders", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return run_evaluate(p.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
