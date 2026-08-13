#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using second-nearest class support radii."""
from __future__ import annotations

import argparse
import hashlib
import json
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--package-manifest", type=Path)
    p.add_argument("--features", type=Path)
    p.add_argument("--centroids", type=Path)
    p.add_argument("--output", type=Path)
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


def ordered_distance_indices(dist: np.ndarray, ids: list[str], hard_rank: dict[str, int]) -> list[int]:
    req(dist.ndim == 1 and len(dist) == len(ids), "distance/reference alignment mismatch")
    req(len(ids) >= 2, "support2 requires at least two references")
    req(np.isfinite(dist).all() and np.all(dist >= 0.0), "invalid Euclidean distance")
    return sorted(range(len(ids)), key=lambda i: (float(dist[i]), int(hard_rank[ids[i]]), ids[i]))


def first_second(dist: np.ndarray, ids: list[str], hard_rank: dict[str, int]) -> tuple[float, float, str, str]:
    order = ordered_distance_indices(dist, ids, hard_rank)
    return float(dist[order[0]]), float(dist[order[1]]), ids[order[0]], ids[order[1]]


def run_self_tests() -> int:
    dist = np.asarray([3.0, 1.0, 2.0, 1.0], dtype=float)
    ids = ["d", "b", "c", "a"]
    ranks = {"a": 1, "b": 2, "c": 3, "d": 4}
    d1, d2, i1, i2 = first_second(dist, ids, ranks)
    req(d1 == 1.0 and d2 == 1.0 and i1 == "a" and i2 == "b", "support2 deterministic tie test failed")

    p = np.asarray([1.0, 2.0, 5.0], dtype=float)
    n = np.asarray([3.0, 4.0, 8.0], dtype=float)
    pid = ["p1", "p2", "p3"]
    nid = ["n1", "n2", "n3"]
    hr = {"p1": 1, "p2": 2, "p3": 3, "n1": 4, "n2": 5, "n3": 6}
    p1, p2, _, _ = first_second(p, pid, hr)
    n1, n2, _, _ = first_second(n, nid, hr)
    req((n1 - p1) == 2.0 and (n2 - p2) == 2.0, "analytic support-radius margin test failed")

    # A unique accidental nearest positive can dominate k=1 while support2 still reflects two-reference support.
    p = np.asarray([0.05, 5.0, 6.0], dtype=float)
    n = np.asarray([1.0, 2.0, 3.0], dtype=float)
    p1, p2, _, _ = first_second(p, pid, hr)
    n1, n2, _, _ = first_second(n, nid, hr)
    req((n1 - p1) > 0.0 and (n2 - p2) < 0.0, "single-reference-dependence self-test failed")

    print(json.dumps({
        "verdict": "PASS_SECOND_SUPPORT_RADIUS_ENGINEERING_SELF_TESTS",
        "support_order": 2,
        "k_search": False,
        "deterministic_tie_check": True,
        "single_reference_dependence_check": True,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    a = parse_args()
    if a.self_test:
        return run_self_tests()

    req(a.package_manifest is not None and a.features is not None and a.centroids is not None and a.output is not None,
        "science mode requires package/features/centroids/output")
    a.output.mkdir(parents=True, exist_ok=True)

    req(file_sha(a.package_manifest) == PACKAGE_MANIFEST_SHA, "offline package manifest changed")
    manifest = json.loads(a.package_manifest.read_text())
    X = np.load(a.features, allow_pickle=False)
    cm = np.load(a.centroids, allow_pickle=False)

    req(manifest["verdict"] == "PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1", "offline package not authoritative PASS")
    req(manifest["scientific_role"] == "ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED", "offline package role changed")
    req(manifest["development_role"] == "GMN_2022_2023_TARGET_EXCLUDED_ONLY", "development role changed")
    req(manifest["candidate_count"] == EXPECTED_N and manifest["feature_dimension"] == EXPECTED_D and manifest["centroid_dimension"] == EXPECTED_CM_D,
        "package dimensions changed")
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
        req(int(hard_metrics[key]) == int(HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch")
        req(int(manifest["parent_baseline_metrics"][key]) == int(HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(hard_metrics[key], HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch")
        req(metric_close(manifest["parent_baseline_metrics"][key], HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(manifest["parent_fused_metrics"][key]) == int(PARENT_CONTROL[key]), f"recorded parent {key} changed")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(manifest["parent_fused_metrics"][key], PARENT_CONTROL[key]), f"recorded parent {key} changed")

    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    parent_margin = np.zeros(EXPECTED_N, dtype=float)
    support2_raw = np.zeros(EXPECTED_N, dtype=float)
    evidence_rows: list[dict[str, Any]] = []
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
        req(np.isfinite(Ztr).all() and np.isfinite(Zte).all(), f"invalid standardized fold {fold}")
        req(int(ytr.sum()) >= 2 and int((~ytr).sum()) >= 2, f"support2 class reference count insufficient fold {fold}")

        train_ids = [ids[i] for i in train_indices.tolist()]
        P = Ztr[ytr]
        N = Ztr[~ytr]
        pos_ids = [train_ids[i] for i in np.where(ytr)[0].tolist()]
        neg_ids = [train_ids[i] for i in np.where(~ytr)[0].tolist()]

        fold_parent: list[float] = []
        fold_support2: list[float] = []
        for j, global_i in enumerate(test_indices.tolist()):
            z = Zte[j]
            dpos = np.linalg.norm(P - z[None, :], axis=1)
            dneg = np.linalg.norm(N - z[None, :], axis=1)
            p1, p2, p1id, p2id = first_second(dpos, pos_ids, hard_rank)
            n1, n2, n1id, n2id = first_second(dneg, neg_ids, hard_rank)
            m1 = n1 - p1
            m2 = n2 - p2
            parent_margin[global_i] = m1
            support2_raw[global_i] = m2
            fold_parent.append(m1)
            fold_support2.append(m2)
            evidence_rows.append({
                "family_id": ids[global_i],
                "fold": fold,
                "nearest_positive_family_id": p1id,
                "second_positive_family_id": p2id,
                "nearest_nonpositive_family_id": n1id,
                "second_nonpositive_family_id": n2id,
                "nearest_positive_distance": p1,
                "second_positive_distance": p2,
                "nearest_nonpositive_distance": n1,
                "second_nonpositive_distance": n2,
                "parent_margin": m1,
                "raw_support2_margin": m2,
            })

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(ytr.sum()),
            "nonpositive_references": int((~ytr).sum()),
            "heldout_positive": int(y[test].sum()),
            "zero_variance_parent_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "parent_margin_min": float(np.min(fold_parent)),
            "parent_margin_median": float(np.median(fold_parent)),
            "parent_margin_max": float(np.max(fold_parent)),
            "support2_margin_min": float(np.min(fold_support2)),
            "support2_margin_median": float(np.median(fold_support2)),
            "support2_margin_max": float(np.max(fold_support2)),
        })

    req(parent_margin.shape == (EXPECTED_N,) and np.isfinite(parent_margin).all(), "invalid parent margin vector")
    req(support2_raw.shape == (EXPECTED_N,) and np.isfinite(support2_raw).all(), "invalid support2 margin vector")
    req(array_sha(parent_margin) == PARENT_MARGIN_SHA, "parent Euclidean OOF margin did not reproduce exactly")
    req(len(evidence_rows) == EXPECTED_N and len({r["family_id"] for r in evidence_rows}) == EXPECTED_N,
        "support2 evidence universe changed")

    parent_scale = float(np.median(np.abs(parent_margin)))
    support2_scale = float(np.median(np.abs(support2_raw)))
    req(np.isfinite(parent_scale) and parent_scale > 0.0, "invalid parent median absolute margin")
    req(np.isfinite(support2_scale) and support2_scale > 0.0, "invalid support2 median absolute margin")
    unit_factor = float(parent_scale / support2_scale)
    req(np.isfinite(unit_factor) and unit_factor > 0.0, "invalid support2 unit factor")
    support2_scaled = support2_raw * unit_factor
    req(np.isfinite(support2_scaled).all(), "nonfinite scaled support2 margin")

    tie = [(hard_rank[fid], fid) for fid in ids]
    parent_idx = q.diversity_order(parent_margin, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    parent_local_order = [ids[i] for i in parent_idx]
    parent_fused_order = equal_rank_fusion(hard_order, parent_local_order)
    parent_metrics = q.v1.monotone_metrics(families, parent_fused_order, truths, eligible)
    for key, expected in PARENT_CONTROL.items():
        got = parent_metrics[key]
        if isinstance(expected, float):
            req(metric_close(got, expected), f"parent metric {key} changed: {got}")
        else:
            req(int(got) == expected, f"parent metric {key} changed: {got}")

    local_idx = q.diversity_order(support2_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in local_idx]
    fused_order = equal_rank_fusion(hard_order, local_order)
    local_metrics = q.v1.monotone_metrics(families, local_order, truths, eligible)
    fused = q.v1.monotone_metrics(families, fused_order, truths, eligible)
    req(int(local_metrics["qualified_matches"]) == 95 and int(fused["qualified_matches"]) == 95,
        "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_better_than_parent": int(fused["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(fused["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(fused["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(fused["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(fused["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(fused["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_SECOND_SUPPORT_RADIUS_V1" if passed else "FAIL_GMN_V31_SECOND_SUPPORT_RADIUS_V1"

    evidence = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_SECOND_SUPPORT_RADIUS_EVIDENCE",
        "candidate_count": EXPECTED_N,
        "parent_margin_sha256": array_sha(parent_margin),
        "raw_support2_margin_sha256": array_sha(support2_raw),
        "scaled_support2_margin_sha256": array_sha(support2_scaled),
        "parent_median_absolute_margin": parent_scale,
        "support2_median_absolute_margin": support2_scale,
        "unit_factor": unit_factor,
        "rows": sorted(evidence_rows, key=lambda r: r["family_id"]),
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
    (a.output / "GMN_V31_SECOND_SUPPORT_RADIUS_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

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
        "recomputed_parent_margin_sha256": array_sha(parent_margin),
        "raw_support2_margin_sha256": array_sha(support2_raw),
        "scaled_support2_margin_sha256": array_sha(support2_scaled),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "hard_control": HARD_CONTROL,
        "parent_control": PARENT_CONTROL,
        "hard_reproduced_metrics": metric_subset(hard_metrics),
        "parent_reproduced_metrics": metric_subset(parent_metrics),
        "support2_local_only": metric_subset(local_metrics),
        "support2_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "parent_median_absolute_margin": parent_scale,
        "support2_median_absolute_margin": support2_scale,
        "unit_factor": unit_factor,
        "unit_preservation": "median(abs(parent k1 margin))/median(abs(raw k2-support margin))",
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "parent_standardization": "fold-training mean/population-standard-deviation z-score",
        "metric": "Euclidean L2 in standardized 23D parent representation",
        "support_order": 2,
        "local_score": "second_nonpositive_distance - second_positive_distance, positively rescaled only for inherited diversity units",
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "k_search": False,
        "neighbor_averaging": False,
        "neighbor_weighting": False,
        "adaptive_k": False,
        "class_specific_k": False,
        "metric_search": False,
        "learned_metric": False,
        "feature_search": False,
        "scaling_search": False,
        "reference_deletion": False,
        "reference_relabeling": False,
        "reference_weighting": False,
        "distance_calibration": False,
        "graph_propagation": False,
        "threshold_search": False,
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
    (a.output / "GMN_V31_SECOND_SUPPORT_RADIUS_V1_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    keys = ("recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500",
            "top100_dominant_precision", "mrr", "qualified_matches")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: fused[k] for k in keys},
        "local_only": {k: local_metrics[k] for k in keys},
        "gates": gates,
        "parent_margin_sha256": array_sha(parent_margin),
        "raw_support2_margin_sha256": array_sha(support2_raw),
        "scaled_support2_margin_sha256": array_sha(support2_scaled),
        "parent_median_absolute_margin": parent_scale,
        "support2_median_absolute_margin": support2_scale,
        "unit_factor": unit_factor,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
