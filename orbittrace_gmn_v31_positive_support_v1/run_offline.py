#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 positive-support successor, offline package execution."""
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


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(file_sha(a.package_manifest) == PACKAGE_MANIFEST_SHA, "offline package manifest changed")
    manifest = json.loads(a.package_manifest.read_text())
    X = np.load(a.features, allow_pickle=False)
    cm = np.load(a.centroids, allow_pickle=False)

    # Authoritative offline-package provenance and firewall.
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
    req(all(groups[i] == (("SHOWER/" + str(rows[i]["truth"]["best_label"])) if rows[i]["truth"]["best_label"] is not None else ("NEG/" + ids[i])) for i in range(EXPECTED_N)), "strict group semantics changed")

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

    # Sole successor science begins here: OOF proximity to positive support only.
    scores = np.zeros(EXPECTED_N, dtype=float)
    nearest_positive_id: list[str | None] = [None] * EXPECTED_N
    nearest_positive_distance = np.zeros(EXPECTED_N, dtype=float)
    fold_diag: list[dict[str, Any]] = []

    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0].tolist()}
        test_groups = {groups[i] for i in np.where(test)[0].tolist()}
        req(train_groups.isdisjoint(test_groups), f"strict group leakage fold {fold}")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        req(np.isfinite(Ztr).all() and np.isfinite(Zte).all(), f"nonfinite standardized fold {fold}")

        train_indices = np.where(train)[0]
        test_indices = np.where(test)[0]
        positive_local_mask = y[train]
        P = Ztr[positive_local_mask]
        pos_global_indices = train_indices[positive_local_mask]
        pos_ids = [ids[i] for i in pos_global_indices.tolist()]
        req(len(P) > 0 and len(P) == len(pos_ids), f"positive support missing fold {fold}")

        for j, global_i in enumerate(test_indices.tolist()):
            d = np.linalg.norm(P - Zte[j][None, :], axis=1)
            req(d.shape == (len(P),) and np.isfinite(d).all(), "invalid positive-support distances")
            # Exact ties: immutable hard rank then family ID, matching deterministic v31 lineage semantics.
            best = min(range(len(pos_ids)), key=lambda k: (float(d[k]), hard_rank[pos_ids[k]], pos_ids[k]))
            dp = float(d[best])
            req(math.isfinite(dp) and dp >= 0.0, "invalid nearest-positive distance")
            nearest_positive_id[global_i] = pos_ids[best]
            nearest_positive_distance[global_i] = dp
            scores[global_i] = -dp

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(positive_local_mask.sum()),
            "nonpositive_references_used_by_local_leg": 0,
            "heldout_positive": int(y[test].sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
        })

    req(np.isfinite(scores).all() and np.isfinite(nearest_positive_distance).all(), "invalid positive-support score vector")
    req(all(x is not None for x in nearest_positive_id), "missing nearest-positive identity")

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
    verdict = "PASS_GMN_V31_POSITIVE_SUPPORT_V1" if passed else "FAIL_GMN_V31_POSITIVE_SUPPORT_V1"

    evidence = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_POSITIVE_SUPPORT_EVIDENCE",
        "candidate_count": EXPECTED_N,
        "score_sha256": array_sha(scores),
        "nearest_positive_distance_sha256": array_sha(nearest_positive_distance),
        "rows": [
            {
                "family_id": ids[i],
                "fold": int(folds[i]),
                "nearest_positive_family_id": str(nearest_positive_id[i]),
                "nearest_positive_distance": float(nearest_positive_distance[i]),
                "positive_support_score": float(scores[i]),
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
    (a.output / "GMN_V31_POSITIVE_SUPPORT_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n")

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
        "positive_support_score_sha256": array_sha(scores),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "hard_control": HARD_CONTROL,
        "parent_control": PARENT_CONTROL,
        "hard_reproduced_metrics": metric_subset(hard_metrics),
        "positive_support_local_only": metric_subset(local_metrics),
        "positive_support_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "fold_count": 5,
        "strict_whole_shower_oof": True,
        "positive_reference_semantics": "exact frozen parent positive family truth",
        "nearest_k": 1,
        "distance": "ordinary Euclidean after fold-training z-score",
        "local_score": "negative nearest-positive distance",
        "nonpositive_reference_geometry_used": False,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "k_search": False,
        "threshold_search": False,
        "radius_search": False,
        "density_normalization_search": False,
        "positive_reference_filtering": False,
        "positive_reference_weighting": False,
        "negative_reference_editing": False,
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
    (a.output / "GMN_V31_POSITIVE_SUPPORT_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
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
        "positive_support_score_sha256": array_sha(scores),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
