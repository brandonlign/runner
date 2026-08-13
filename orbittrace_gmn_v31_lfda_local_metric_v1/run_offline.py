#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using full-dimensional LFDA local metric."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import eigh

import run_urc_union_ranker as q

EXPECTED_N = 226
EXPECTED_D = 23
EXPECTED_CM_D = 8
BLIND = [20.0, 55.0]
PACKAGE_MANIFEST_SHA = "16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7"
FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
CENTROID_SHA = "a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f"
PARENT_PRELABEL_SHA = "b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09"
PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
LOCAL_SCALING_K = 7
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
HARD_CONTROL = {
    "recovered_at_25": 21,
    "recovered_at_50": 38,
    "recovered_at_100": 59,
    "top100_dominant_precision": 0.6884631112636006,
    "mrr": 0.046734076055452344,
    "qualified_matches": 95,
}
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--package-manifest", type=Path, required=True)
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--centroids", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode())
    h.update(str(tuple(arr.shape)).encode())
    h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def equal_rank_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
    req(len(hard_order) == len(local_order) and set(hard_order) == set(local_order), "rank universe mismatch")
    h = {fid: i + 1 for i, fid in enumerate(hard_order)}
    l = {fid: i + 1 for i, fid in enumerate(local_order)}
    return sorted(hard_order, key=lambda fid: (h[fid] + l[fid], h[fid], fid))


def pairwise_distances(Z: np.ndarray) -> np.ndarray:
    z = np.asarray(Z, dtype=float)
    req(z.ndim == 2 and z.shape[0] >= 2 and np.isfinite(z).all(), "invalid pairwise matrix")
    sq = np.sum(z * z, axis=1)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (z @ z.T)
    # Numerical cancellation can make tiny negative entries.
    d2 = np.maximum(d2, 0.0)
    d = np.sqrt(d2)
    req(np.isfinite(d).all(), "nonfinite pairwise distances")
    return d


def lfda_full_transform(Z: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Sugiyama LFDA with classwise local scaling K=7 and r=d, no regularization."""
    z = np.asarray(Z, dtype=float)
    labels = np.asarray(y, dtype=bool)
    n, d = z.shape
    req(d == EXPECTED_D and labels.shape == (n,), "LFDA training shape changed")
    req(np.isfinite(z).all() and labels.any() and (~labels).any(), "invalid LFDA training set")

    A = np.zeros((n, n), dtype=float)
    class_diag: dict[str, Any] = {}
    for cls, name in ((False, "nonpositive"), (True, "positive")):
        idx = np.where(labels == cls)[0]
        m = len(idx)
        req(m >= LOCAL_SCALING_K + 1, f"LFDA class {name} has fewer than 8 rows")
        C = z[idx]
        D = pairwise_distances(C)
        D_other = D.copy()
        np.fill_diagonal(D_other, np.inf)
        # 7th nearest OTHER same-class sample => zero-based order statistic 6.
        sigma = np.partition(D_other, LOCAL_SCALING_K - 1, axis=1)[:, LOCAL_SCALING_K - 1]
        req(sigma.shape == (m,) and np.isfinite(sigma).all() and np.all(sigma > 0.0), f"invalid LFDA local scale for {name}")
        denom = sigma[:, None] * sigma[None, :]
        req(np.isfinite(denom).all() and np.all(denom > 0.0), f"invalid LFDA affinity denominator for {name}")
        Ac = np.exp(-(D * D) / denom)
        np.fill_diagonal(Ac, 1.0)
        req(np.isfinite(Ac).all() and np.all(Ac > 0.0) and np.all(Ac <= 1.0), f"invalid LFDA affinity for {name}")
        A[np.ix_(idx, idx)] = Ac
        class_diag[name] = {
            "count": int(m),
            "sigma_min": float(np.min(sigma)),
            "sigma_median": float(np.median(sigma)),
            "sigma_max": float(np.max(sigma)),
            "affinity_offdiag_min": float(np.min(Ac[~np.eye(m, dtype=bool)])),
            "affinity_offdiag_median": float(np.median(Ac[~np.eye(m, dtype=bool)])),
            "affinity_offdiag_max": float(np.max(Ac[~np.eye(m, dtype=bool)])),
        }

    Ww = np.zeros((n, n), dtype=float)
    Wb = np.full((n, n), 1.0 / n, dtype=float)
    for cls in (False, True):
        idx = np.where(labels == cls)[0]
        nc = len(idx)
        Ac = A[np.ix_(idx, idx)]
        Ww[np.ix_(idx, idx)] = Ac / nc
        Wb[np.ix_(idx, idx)] = Ac * (1.0 / n - 1.0 / nc)

    req(np.allclose(Ww, Ww.T, rtol=0.0, atol=1e-14), "LFDA within weights not symmetric")
    req(np.allclose(Wb, Wb.T, rtol=0.0, atol=1e-14), "LFDA between weights not symmetric")

    Lw = np.diag(np.sum(Ww, axis=1)) - Ww
    Lb = np.diag(np.sum(Wb, axis=1)) - Wb
    Sw = z.T @ Lw @ z
    Sb = z.T @ Lb @ z
    Sw = 0.5 * (Sw + Sw.T)
    Sb = 0.5 * (Sb + Sb.T)
    req(Sw.shape == (d, d) and Sb.shape == (d, d), "LFDA scatter shape changed")
    req(np.isfinite(Sw).all() and np.isfinite(Sb).all(), "nonfinite LFDA scatter")

    sw_eval = np.linalg.eigvalsh(Sw)
    sb_eval = np.linalg.eigvalsh(Sb)
    req(np.isfinite(sw_eval).all() and np.isfinite(sb_eval).all(), "nonfinite LFDA scatter eigenvalues")
    req(float(np.min(sw_eval)) > 0.0, "LFDA within scatter is not positive definite; no regularization rescue allowed")

    # scipy.linalg.eigh solves Sb v = lambda Sw v and returns Sw-normalized eigenvectors.
    vals, vecs = eigh(Sb, Sw, check_finite=True, driver="gvd")
    req(vals.shape == (d,) and vecs.shape == (d, d), "LFDA generalized eigensystem shape changed")
    req(np.isfinite(vals).all() and np.isfinite(vecs).all(), "nonfinite LFDA generalized eigensystem")
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    req(np.all(vals > 0.0), "LFDA generalized eigenvalue is nonpositive; full-r=23 frozen method cannot proceed")

    gram = vecs.T @ Sw @ vecs
    req(np.allclose(gram, np.eye(d), rtol=1e-8, atol=1e-8), "LFDA generalized eigenvectors not Sw-normalized")
    T = vecs * np.sqrt(vals)[None, :]
    req(T.shape == (d, d) and np.isfinite(T).all(), "invalid LFDA transform")
    svals = np.linalg.svd(T, compute_uv=False)
    req(np.isfinite(svals).all() and np.all(svals > 0.0), "LFDA full transform not invertible")

    diag = {
        "local_scaling_k": LOCAL_SCALING_K,
        "class_diagnostics": class_diag,
        "sw_eigen_min": float(np.min(sw_eval)),
        "sw_eigen_max": float(np.max(sw_eval)),
        "sw_condition": float(np.max(sw_eval) / np.min(sw_eval)),
        "sb_eigen_min": float(np.min(sb_eval)),
        "sb_eigen_max": float(np.max(sb_eval)),
        "generalized_eigen_min": float(np.min(vals)),
        "generalized_eigen_median": float(np.median(vals)),
        "generalized_eigen_max": float(np.max(vals)),
        "transform_singular_min": float(np.min(svals)),
        "transform_singular_max": float(np.max(svals)),
        "transform_condition": float(np.max(svals) / np.min(svals)),
    }
    return T, diag


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(file_sha(a.package_manifest) == PACKAGE_MANIFEST_SHA, "offline package manifest changed")
    manifest = json.loads(a.package_manifest.read_text())
    X = np.load(a.features, allow_pickle=False)
    cm = np.load(a.centroids, allow_pickle=False)

    req(manifest["verdict"] == "PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1", "offline package not authoritative PASS")
    req(manifest["scientific_role"] == "ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED", "offline package role changed")
    req(manifest["development_role"] == "GMN_2022_2023_TARGET_EXCLUDED_ONLY", "development role changed")
    req(manifest["candidate_count"] == EXPECTED_N and manifest["feature_dimension"] == EXPECTED_D and manifest["centroid_dimension"] == EXPECTED_CM_D, "package dimensions changed")
    req(X.shape == (EXPECTED_N, EXPECTED_D) and np.isfinite(X).all(), "invalid offline X")
    req(cm.shape == (EXPECTED_N, EXPECTED_CM_D) and np.isfinite(cm).all(), "invalid offline centroids")
    req(array_sha(X) == manifest["feature_matrix_sha256"] == FEATURE_SHA, "offline X hash changed")
    req(array_sha(cm) == manifest["centroid_matrix_sha256"] == CENTROID_SHA, "offline centroid hash changed")
    req(manifest["parent_prelabel_sha256"] == PARENT_PRELABEL_SHA, "parent prelabel provenance changed")
    req(manifest["parent_margin_sha256"] == PARENT_MARGIN_SHA, "parent margin provenance changed")
    req(manifest["blind_exclusion"] == BLIND, "blind interval changed")
    for key in (
        "raw_event_rows_exported", "raw_event_ids_exported", "raw_hidden_label_mapping_exported",
        "new_feature_or_score_created", "new_rank_evaluated", "successor_selected",
        "sonotaco_2013_2014_access", "target_information_access", "target_region_events_accessed",
        "maarsy_scientific_access", "dms_scientific_access",
    ):
        req(manifest[key] is False, f"package firewall/provenance changed: {key}")

    ids = [str(x) for x in manifest["family_input_order"]]
    hard_order = [str(x) for x in manifest["hard_order"]]
    rows = manifest["rows"]
    eligible_labels = [str(x) for x in manifest["eligible_labels"]]
    req(len(ids) == EXPECTED_N and len(set(ids)) == EXPECTED_N, "family input order changed")
    req(len(hard_order) == EXPECTED_N and len(set(hard_order)) == EXPECTED_N and set(hard_order) == set(ids), "hard order changed")
    req(len(rows) == EXPECTED_N and [str(r["family_id"]) for r in rows] == ids, "row/input alignment changed")
    req(len(eligible_labels) == 355 and len(set(eligible_labels)) == 355, "eligible-label universe changed")

    truths = {str(r["family_id"]): r["truth"] for r in rows}
    groups = [str(r["strict_group"]) for r in rows]
    folds = np.asarray([int(r["fold"]) for r in rows], dtype=int)
    y = np.asarray([bool(r["truth"]["positive"]) for r in rows], dtype=bool)
    req(set(folds.tolist()) == set(range(5)), "five-fold universe changed")
    req(int(y.sum()) == 111 and int((~y).sum()) == 115, "positive/nonpositive family counts changed")

    families = [{"family_id": fid} for fid in ids]
    eligible = {label: None for label in eligible_labels}
    hard_metrics = q.v1.monotone_metrics(families, hard_order, truths, eligible)
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(hard_metrics[key]) == int(HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch: {hard_metrics[key]}")
        req(int(manifest["parent_baseline_metrics"][key]) == int(HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(hard_metrics[key], HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch: {hard_metrics[key]}")
        req(metric_close(manifest["parent_baseline_metrics"][key], HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(manifest["parent_fused_metrics"][key]) == int(PARENT_CONTROL[key]), f"recorded parent {key} changed")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(manifest["parent_fused_metrics"][key], PARENT_CONTROL[key]), f"recorded parent {key} changed")

    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    margins = np.zeros(EXPECTED_N, dtype=float)
    nearest_pos: list[str | None] = [None] * EXPECTED_N
    nearest_neg: list[str | None] = [None] * EXPECTED_N
    dpos_vec = np.zeros(EXPECTED_N, dtype=float)
    dneg_vec = np.zeros(EXPECTED_N, dtype=float)
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_indices = np.where(train)[0]
        test_indices = np.where(test)[0]
        train_groups = {groups[i] for i in train_indices.tolist()}
        test_groups = {groups[i] for i in test_indices.tolist()}
        req(train_groups.isdisjoint(test_groups), f"strict group leakage fold {fold}")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        ytr = y[train]
        req(np.isfinite(Ztr).all() and np.isfinite(Zte).all() and ytr.any() and (~ytr).any(), f"invalid standardized fold {fold}")

        T, lfda_diag = lfda_full_transform(Ztr, ytr)
        Utr = Ztr @ T
        Ute = Zte @ T
        req(np.isfinite(Utr).all() and np.isfinite(Ute).all(), f"nonfinite LFDA embedding fold {fold}")

        pos_mask = ytr
        neg_mask = ~ytr
        P = Utr[pos_mask]
        N = Utr[neg_mask]
        train_ids = [ids[i] for i in train_indices.tolist()]
        pos_ids = [train_ids[i] for i in np.where(pos_mask)[0].tolist()]
        neg_ids = [train_ids[i] for i in np.where(neg_mask)[0].tolist()]
        req(len(P) == len(pos_ids) and len(N) == len(neg_ids) and len(P)>0 and len(N)>0, f"class reference alignment changed fold {fold}")

        for j, global_i in enumerate(test_indices.tolist()):
            dp = np.linalg.norm(P - Ute[j][None, :], axis=1)
            dn = np.linalg.norm(N - Ute[j][None, :], axis=1)
            req(np.isfinite(dp).all() and np.isfinite(dn).all(), "nonfinite LFDA nearest-reference distances")
            ip = min(range(len(pos_ids)), key=lambda k: (float(dp[k]), hard_rank[pos_ids[k]], pos_ids[k]))
            inn = min(range(len(neg_ids)), key=lambda k: (float(dn[k]), hard_rank[neg_ids[k]], neg_ids[k]))
            d_p = float(dp[ip]); d_n = float(dn[inn])
            margin = d_n - d_p
            req(math.isfinite(margin), "nonfinite LFDA margin")
            dpos_vec[global_i] = d_p
            dneg_vec[global_i] = d_n
            margins[global_i] = margin
            nearest_pos[global_i] = pos_ids[ip]
            nearest_neg[global_i] = neg_ids[inn]

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos_mask.sum()),
            "nonpositive_references": int(neg_mask.sum()),
            "heldout_positive": int(y[test].sum()),
            "zero_variance_parent_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "lfda": lfda_diag,
        })

    req(np.isfinite(margins).all() and np.isfinite(dpos_vec).all() and np.isfinite(dneg_vec).all(), "invalid full LFDA score vectors")
    req(all(x is not None for x in nearest_pos) and all(x is not None for x in nearest_neg), "missing LFDA nearest reference identity")

    tie = [(hard_rank[fid], fid) for fid in ids]
    local_idx = q.diversity_order(margins, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in local_idx]
    fused_order = equal_rank_fusion(hard_order, local_order)
    local_metrics = q.v1.monotone_metrics(families, local_order, truths, eligible)
    fused = q.v1.monotone_metrics(families, fused_order, truths, eligible)
    req(int(local_metrics["qualified_matches"]) == 95 and int(fused["qualified_matches"]) == 95, "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_better_than_parent": int(fused["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(fused["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(fused["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(fused["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(fused["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(fused["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_LFDA_LOCAL_METRIC_V1" if passed else "FAIL_GMN_V31_LFDA_LOCAL_METRIC_V1"

    evidence = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_LFDA_LOCAL_METRIC_EVIDENCE",
        "candidate_count": EXPECTED_N,
        "lfda_margin_sha256": array_sha(margins),
        "positive_distance_sha256": array_sha(dpos_vec),
        "nonpositive_distance_sha256": array_sha(dneg_vec),
        "rows": [
            {
                "family_id": ids[i],
                "fold": int(folds[i]),
                "nearest_positive_family_id": str(nearest_pos[i]),
                "nearest_nonpositive_family_id": str(nearest_neg[i]),
                "d_positive_lfda": float(dpos_vec[i]),
                "d_nonpositive_lfda": float(dneg_vec[i]),
                "lfda_margin": float(margins[i]),
            }
            for i in range(EXPECTED_N)
        ],
        "raw_event_rows_accessed": False,
        "raw_event_ids_accessed": False,
        "raw_hidden_label_mapping_accessed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": BLIND,
    }
    (a.output / "GMN_V31_LFDA_LOCAL_METRIC_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n")

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_N,
        "feature_dimension": EXPECTED_D,
        "lfda_output_dimension": EXPECTED_D,
        "feature_matrix_sha256": array_sha(X),
        "centroid_matrix_sha256": array_sha(cm),
        "package_manifest_sha256": file_sha(a.package_manifest),
        "parent_prelabel_sha256": manifest["parent_prelabel_sha256"],
        "parent_margin_sha256": manifest["parent_margin_sha256"],
        "lfda_margin_sha256": array_sha(margins),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "hard_control": HARD_CONTROL,
        "parent_control": PARENT_CONTROL,
        "hard_reproduced_metrics": metric_subset(hard_metrics),
        "lfda_local_only": metric_subset(local_metrics),
        "lfda_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "parent_standardization": "fold-training mean/population-standard-deviation z-score",
        "lfda_local_scaling_k": LOCAL_SCALING_K,
        "lfda_affinity": "classwise exp(-squared_euclidean/(sigma_i*sigma_j)); sigma=7th nearest other same-class distance",
        "lfda_scatter": "Sugiyama 2007 pairwise local within/between scatter weights",
        "lfda_generalized_eigenproblem": "Sb phi=lambda Sw phi; no regularization; all 23 eigenvectors",
        "lfda_eigenvector_weighting": "sqrt(generalized_eigenvalue)",
        "nearest_k": 1,
        "local_score": "nearest_nonpositive_distance_minus_nearest_positive_distance_in_full_23D_LFDA_embedding",
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "local_scaling_k_search": False,
        "output_dimension_search": False,
        "eigenvalue_cutoff_search": False,
        "regularization_or_shrinkage": False,
        "kernel_lfda": False,
        "semi_supervised_lfda": False,
        "affinity_search": False,
        "metric_blend_search": False,
        "nearest_k_search": False,
        "feature_search": False,
        "scaling_search": False,
        "fold_search": False,
        "reference_definition_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "post_result_second_search": False,
        "raw_event_rows_accessed": False,
        "raw_event_ids_accessed": False,
        "raw_hidden_label_mapping_accessed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": BLIND,
        "sonotaco_benchmark_authorized_by_this_result": bool(passed),
        "claim_boundary": "GMN development only; PASS authorizes only a separately frozen one-shot exposed SonotaCo comparison.",
    }
    (a.output / "GMN_V31_LFDA_LOCAL_METRIC_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: fused[k] for k in (
            "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500",
            "top100_dominant_precision", "mrr", "qualified_matches"
        )},
        "local_only": {k: local_metrics[k] for k in (
            "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500",
            "top100_dominant_precision", "mrr", "qualified_matches"
        )},
        "gates": gates,
        "lfda_margin_sha256": array_sha(margins),
        "fold_lfda_condition": [fd["lfda"]["transform_condition"] for fd in fold_diag],
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
