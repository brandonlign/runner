#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using classwise normalized lens depth."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

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
    req(z.ndim == 2 and z.shape[0] >= 2 and np.isfinite(z).all(), "invalid lens reference matrix")
    sq = np.sum(z * z, axis=1)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (z @ z.T)
    d2 = np.maximum(d2, 0.0)
    d = np.sqrt(d2)
    req(d.shape == (len(z), len(z)) and np.isfinite(d).all(), "invalid pairwise reference distances")
    return d


def normalized_lens_depth(query: np.ndarray, refs: np.ndarray, ref_pair_d: np.ndarray) -> tuple[float, int, int]:
    """Exact complete-information lens-depth relative frequency under strict JMLR lens definition."""
    x = np.asarray(query, dtype=float)
    R = np.asarray(refs, dtype=float)
    D = np.asarray(ref_pair_d, dtype=float)
    m = len(R)
    req(R.ndim == 2 and m >= 2 and R.shape[1] == len(x), "invalid lens class geometry")
    req(D.shape == (m, m) and np.isfinite(D).all(), "invalid lens pair-distance matrix")
    qd = np.linalg.norm(R - x[None, :], axis=1)
    req(qd.shape == (m,) and np.isfinite(qd).all(), "invalid query-to-class distances")
    i, j = np.triu_indices(m, k=1)
    pair_count = len(i)
    req(pair_count == m * (m - 1) // 2 and pair_count > 0, "invalid lens pair count")
    # Exact source definition: max(d(x,a), d(x,b)) < d(a,b); equality is not membership.
    inside = (qd[i] < D[i, j]) & (qd[j] < D[i, j])
    count = int(np.sum(inside))
    depth = float(count / pair_count)
    req(math.isfinite(depth) and 0.0 <= depth <= 1.0, "invalid normalized lens depth")
    return depth, count, pair_count


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(file_sha(a.package_manifest) == PACKAGE_MANIFEST_SHA, "offline package manifest changed")
    manifest = json.loads(a.package_manifest.read_text())
    X = np.load(a.features, allow_pickle=False)
    cm = np.load(a.centroids, allow_pickle=False)

    # Exact authoritative development-package provenance and firewall.
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
    scores = np.zeros(EXPECTED_N, dtype=float)
    depth_pos = np.zeros(EXPECTED_N, dtype=float)
    depth_neg = np.zeros(EXPECTED_N, dtype=float)
    count_pos = np.zeros(EXPECTED_N, dtype=np.int64)
    count_neg = np.zeros(EXPECTED_N, dtype=np.int64)
    pair_count_pos = np.zeros(EXPECTED_N, dtype=np.int64)
    pair_count_neg = np.zeros(EXPECTED_N, dtype=np.int64)
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

        P = Ztr[ytr]
        N = Ztr[~ytr]
        req(len(P) >= 2 and len(N) >= 2, f"fold {fold} lacks two references in a class")
        DP = pairwise_distances(P)
        DN = pairwise_distances(N)
        p_pairs_expected = len(P) * (len(P) - 1) // 2
        n_pairs_expected = len(N) * (len(N) - 1) // 2

        fold_pos_depths: list[float] = []
        fold_neg_depths: list[float] = []
        for j, global_i in enumerate(test_indices.tolist()):
            ldp, cp, pp = normalized_lens_depth(Zte[j], P, DP)
            ldn, cn, pn = normalized_lens_depth(Zte[j], N, DN)
            req(pp == p_pairs_expected and pn == n_pairs_expected, "lens denominator changed")
            margin = ldp - ldn
            req(math.isfinite(margin) and -1.0 <= margin <= 1.0, "invalid lens-depth margin")
            depth_pos[global_i] = ldp
            depth_neg[global_i] = ldn
            count_pos[global_i] = cp
            count_neg[global_i] = cn
            pair_count_pos[global_i] = pp
            pair_count_neg[global_i] = pn
            scores[global_i] = margin
            fold_pos_depths.append(ldp)
            fold_neg_depths.append(ldn)

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(ytr.sum()),
            "nonpositive_references": int((~ytr).sum()),
            "positive_reference_pairs": int(p_pairs_expected),
            "nonpositive_reference_pairs": int(n_pairs_expected),
            "heldout_positive": int(y[test].sum()),
            "zero_variance_parent_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "positive_depth_min": float(np.min(fold_pos_depths)),
            "positive_depth_median": float(np.median(fold_pos_depths)),
            "positive_depth_max": float(np.max(fold_pos_depths)),
            "positive_depth_zero_count": int(np.sum(np.asarray(fold_pos_depths) == 0.0)),
            "nonpositive_depth_min": float(np.min(fold_neg_depths)),
            "nonpositive_depth_median": float(np.median(fold_neg_depths)),
            "nonpositive_depth_max": float(np.max(fold_neg_depths)),
            "nonpositive_depth_zero_count": int(np.sum(np.asarray(fold_neg_depths) == 0.0)),
        })

    for name, arr in (("lens margin", scores), ("positive depth", depth_pos), ("nonpositive depth", depth_neg)):
        req(arr.shape == (EXPECTED_N,) and np.isfinite(arr).all(), f"invalid {name} vector")
    req(np.all((depth_pos >= 0.0) & (depth_pos <= 1.0)) and np.all((depth_neg >= 0.0) & (depth_neg <= 1.0)), "lens depths outside [0,1]")
    req(np.all(pair_count_pos > 0) and np.all(pair_count_neg > 0), "missing lens denominators")

    tie = [(hard_rank[fid], fid) for fid in ids]
    local_idx = q.diversity_order(scores, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
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
    verdict = "PASS_GMN_V31_LENS_DEPTH_MARGIN_V1" if passed else "FAIL_GMN_V31_LENS_DEPTH_MARGIN_V1"

    evidence = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_CLASSWISE_LENS_DEPTH_EVIDENCE",
        "candidate_count": EXPECTED_N,
        "lens_margin_sha256": array_sha(scores),
        "positive_depth_sha256": array_sha(depth_pos),
        "nonpositive_depth_sha256": array_sha(depth_neg),
        "rows": [
            {
                "family_id": ids[i],
                "fold": int(folds[i]),
                "positive_lens_count": int(count_pos[i]),
                "positive_pair_count": int(pair_count_pos[i]),
                "positive_normalized_lens_depth": float(depth_pos[i]),
                "nonpositive_lens_count": int(count_neg[i]),
                "nonpositive_pair_count": int(pair_count_neg[i]),
                "nonpositive_normalized_lens_depth": float(depth_neg[i]),
                "lens_depth_margin": float(scores[i]),
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
    (a.output / "GMN_V31_LENS_DEPTH_MARGIN_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n")

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_N,
        "feature_dimension": EXPECTED_D,
        "feature_matrix_sha256": array_sha(X),
        "centroid_matrix_sha256": array_sha(cm),
        "package_manifest_sha256": file_sha(a.package_manifest),
        "parent_prelabel_sha256": manifest["parent_prelabel_sha256"],
        "parent_margin_sha256": manifest["parent_margin_sha256"],
        "lens_margin_sha256": array_sha(scores),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "hard_control": HARD_CONTROL,
        "parent_control": PARENT_CONTROL,
        "hard_reproduced_metrics": metric_subset(hard_metrics),
        "lens_depth_local_only": metric_subset(local_metrics),
        "lens_depth_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "parent_standardization": "fold-training mean/population-standard-deviation z-score",
        "metric": "ordinary Euclidean in standardized 23D parent representation",
        "lens_definition": "max(d(x,a),d(x,b)) < d(a,b), strict inequality",
        "lens_depth": "complete normalized same-class pair count: contained_lenses/choose(class_reference_count,2)",
        "local_score": "positive_normalized_lens_depth-minus-nonpositive_normalized_lens_depth",
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "k_parameter_used": False,
        "weighted_lens_depth": False,
        "local_or_trimmed_lens": False,
        "pair_subsampling": False,
        "downstream_depth_classifier": False,
        "class_prior_weighting": False,
        "depth_transform_search": False,
        "v31_margin_blend_search": False,
        "reference_deletion": False,
        "reference_relabeling": False,
        "reference_weighting": False,
        "feature_search": False,
        "metric_search": False,
        "scaling_search": False,
        "fold_search": False,
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
    (a.output / "GMN_V31_LENS_DEPTH_MARGIN_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
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
        "lens_margin_sha256": array_sha(scores),
        "positive_zero_depth_count": int(np.sum(depth_pos == 0.0)),
        "nonpositive_zero_depth_count": int(np.sum(depth_neg == 0.0)),
        "positive_depth_median": float(np.median(depth_pos)),
        "nonpositive_depth_median": float(np.median(depth_neg)),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
