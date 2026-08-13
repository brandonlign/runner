#!/usr/bin/env python3
"""Target-excluded GMN v31 successor: class-conditional nearest-distance calibration."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import run_urc_union_ranker as q

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
# Preserve the exact parent support-wrapper corpus identity so representation/input
# behavior cannot drift merely because this is a successor branch.
CORPUS = "orbittrace-gmn-v31-principle-local-geometry-oof-v1"
EXPECTED_HARD = 226
FEATURE_DIM = 23
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
PARENT_FEATURE_SHA = "fd45e842e3b49dc86a0a727006bd0cc82a440a363b60ff52dcebc669d389c5cb"
PARENT_PRELABEL_SHA = "b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "quality_source",
        "support_source_parts",
        "candidate_payload",
        "baseline_payload",
        "scorer_parts",
        "v8_result_json",
        "p19_prelabel_json",
        "parent_result_json",
        "output",
    ):
        p.add_argument("--" + name.replace("_", "-"), dest=name, type=Path, required=True)
    return p.parse_args()


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode())
    h.update(str(tuple(arr.shape)).encode())
    h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(map(str, order)).encode()).hexdigest()


def event_sol(row: dict[str, Any]) -> float:
    for key in ("sol", "solar_longitude", "solar_lon", "sol_lon"):
        if key in row and row[key] is not None:
            value = float(row[key]) % 360.0
            req(math.isfinite(value), f"nonfinite solar longitude for event {row.get('id')}")
            req(not (BLIND[0] <= value <= BLIND[1]), f"protected-region event reached development: {row.get('id')}")
            return value
    raise RuntimeError(f"event lacks solar-longitude field: {row.get('id')}")


def intrinsic_features(
    family: dict[str, Any],
    hard_rank: dict[str, int],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
    neighbor_row: np.ndarray,
) -> list[float]:
    structural = q.v1.structural_features(family, hard_rank)
    req(len(structural) == 14, "URC structural feature dimension changed")
    intrinsic_structural = [float(x) for x in structural[1:11]]
    cohesion = [float(x) for x in q.v2.cohesion_features(family, lookup, support, base)]
    req(len(cohesion) == 7, "URC cohesion feature dimension changed")
    neighbor = [float(x) for x in np.asarray(neighbor_row, dtype=float).tolist()]
    req(len(neighbor) == 6, "active neighbor feature dimension changed")
    row = intrinsic_structural + cohesion + neighbor
    req(len(row) == FEATURE_DIM and all(math.isfinite(x) for x in row), "invalid intrinsic feature row")
    return row


def equal_rank_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
    req(len(hard_order) == len(local_order) and set(hard_order) == set(local_order), "rank universe mismatch")
    h = {fid: i + 1 for i, fid in enumerate(hard_order)}
    l = {fid: i + 1 for i, fid in enumerate(local_order)}
    return sorted(hard_order, key=lambda fid: (h[fid] + l[fid], h[fid], fid))


def metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def class_group_excluded_nn_distances(
    z_class: np.ndarray,
    class_groups: list[str],
    class_name: str,
) -> np.ndarray:
    """Nearest same-class distance for each training row, excluding its entire strict group."""
    z = np.asarray(z_class, dtype=float)
    req(z.ndim == 2 and z.shape[0] == len(class_groups) and z.shape[0] >= 2, f"invalid {class_name} calibration matrix")
    req(np.isfinite(z).all(), f"nonfinite {class_name} calibration matrix")
    d = np.linalg.norm(z[:, None, :] - z[None, :, :], axis=2)
    req(d.shape == (len(class_groups), len(class_groups)) and np.isfinite(d).all(), f"invalid {class_name} pair distances")
    out = np.empty(len(class_groups), dtype=float)
    for i, group in enumerate(class_groups):
        eligible = np.asarray([g != group for g in class_groups], dtype=bool)
        req(eligible.any(), f"{class_name} calibration row {i} has no different-group same-class reference")
        out[i] = float(np.min(d[i, eligible]))
    req(np.isfinite(out).all(), f"nonfinite {class_name} calibration distances")
    return out


def conformity(calibration: np.ndarray, query_distance: float) -> float:
    cal = np.asarray(calibration, dtype=float)
    req(cal.ndim == 1 and len(cal) > 0 and np.isfinite(cal).all(), "invalid class calibration vector")
    req(math.isfinite(query_distance) and query_distance >= 0.0, "invalid query nearest-class distance")
    # Conservative split-conformal-style empirical tail probability, frozen in protocol.
    return float((1 + int(np.sum(cal >= query_distance))) / (len(cal) + 1))


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == QUALITY_SHA, "active GMN ranker source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "v8 result changed")
    req(sha(a.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 hard-family prelabel changed")

    parent = json.loads(a.parent_result_json.read_text())
    req(parent["verdict"] == "PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF", "exact parent did not reproduce")
    req(parent["candidate_count"] == EXPECTED_HARD and parent["feature_dimension"] == FEATURE_DIM, "parent universe changed")
    req(parent["prelabel_sha256"] == PARENT_PRELABEL_SHA, "parent prelabel hash changed")
    req(parent["feature_matrix_sha256"] == PARENT_FEATURE_SHA, "parent feature matrix hash changed")
    req(parent["strict_whole_shower_oof"] is True and parent["fold_count"] == 5, "parent fold semantics changed")
    req(parent["nearest_k"] == 1 and parent["distance"] == "ordinary Euclidean after fold-training z-score", "parent nearest-distance semantics changed")
    req(parent["margin"] == "d_nonpositive-d_positive", "parent margin changed")
    req(parent["diversity"] == {"lambda": 0.8, "scale": 1.0}, "parent diversity changed")
    pm = parent["equal_rank_fusion"]
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(pm[key]) == int(PARENT_CONTROL[key]), f"parent {key} changed: {pm[key]}")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(pm[key], PARENT_CONTROL[key]), f"parent {key} changed: {pm[key]}")

    payload = json.loads(a.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    req(len(hard) == EXPECTED_HARD and len(hard_order) == EXPECTED_HARD, "hard family count changed")
    ids = [str(f["family_id"]) for f in hard]
    req(len(set(ids)) == EXPECTED_HARD and set(ids) == set(hard_order), "hard family identity changed")
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    req(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan_by_year, _calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    req(sorted(scan_by_year) == list(YEARS), "GMN year universe changed")
    req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month panel changed")

    # Fail closed on the protected interval before representation or truth interpretation.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = event_sol(row)
    for family in hard:
        for year in YEARS:
            centroid = family.get("centroids", {}).get(str(year))
            req(centroid is not None, f"missing centroid for {family['family_id']} {year}")
            csol = float(centroid["sol"]) % 360.0
            req(not (BLIND[0] <= csol <= BLIND[1]), f"protected centroid reached development: {family['family_id']} {year}")

    lookup = q.v2.event_lookup(scan_by_year)
    cm = q.centroid_matrix(hard)
    req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "centroid matrix changed")
    nf = q.neighbor_features(cm)
    req(nf.shape == (EXPECTED_HARD, 6) and np.isfinite(nf).all(), "neighbor matrix changed")
    X = np.asarray([
        intrinsic_features(family, hard_rank, lookup, support, base, nf[i])
        for i, family in enumerate(hard)
    ], dtype=float)
    req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "intrinsic feature matrix invalid")
    req(array_sha(X) == parent["feature_matrix_sha256"] == PARENT_FEATURE_SHA, "candidate feature representation differs from parent")

    # Seal the exact parent-equivalent label-free representation before truth.
    np.save(a.output / "GMN_V31_CLASS_CONDITIONAL_INTRINSIC_FEATURES.npy", X, allow_pickle=False)
    prelabel = {
        "scope": "GMN 2022/2023 target-excluded hard-family intrinsic geometry",
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "feature_matrix_sha256": array_sha(X),
        "hard_order_sha256": order_sha(hard_order),
        "feature_definition": {
            "intrinsic_structural": 10,
            "cohesion": 7,
            "centroid_neighbor": 6,
            "explicit_hard_rank_feature_excluded": True,
            "source_soft_metadata_excluded": True,
            "p20_only_features_excluded": True,
        },
        "truth_interpreted_for_feature_construction": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GMN_V31_CLASS_CONDITIONAL_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)
    req(prelabel_sha == parent["prelabel_sha256"] == PARENT_PRELABEL_SHA, "candidate prelabel differs from parent")

    # Development truth begins only after representation is sealed.
    eligible = q.v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in ids}
    y = np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)
    req(y.any() and (~y).any(), "recoverability reference target is degenerate")

    groups: list[str] = []
    for fid in ids:
        label = truths[fid]["best_label"]
        groups.append(("SHOWER/" + str(label)) if label is not None else ("NEG/" + fid))
    folds = np.asarray([q.v1.deterministic_fold(group) for group in groups], dtype=int)
    req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")

    scores = np.zeros(EXPECTED_HARD, dtype=float)
    p_positive = np.zeros(EXPECTED_HARD, dtype=float)
    p_nonpositive = np.zeros(EXPECTED_HARD, dtype=float)
    d_positive = np.zeros(EXPECTED_HARD, dtype=float)
    d_nonpositive = np.zeros(EXPECTED_HARD, dtype=float)
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_indices = np.where(train)[0]
        test_indices = np.where(test)[0]
        train_groups = [groups[i] for i in train_indices.tolist()]
        test_groups = {groups[i] for i in test_indices.tolist()}
        req(set(train_groups).isdisjoint(test_groups), f"group leakage fold {fold}")
        req(y[train].any() and (~y[train]).any(), f"fold {fold} lacks both reference classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        req(np.isfinite(Ztr).all() and np.isfinite(Zte).all(), f"nonfinite standardized fold {fold}")

        ytr = y[train]
        pos_mask = ytr
        neg_mask = ~ytr
        P = Ztr[pos_mask]
        N = Ztr[neg_mask]
        pos_groups = [train_groups[i] for i in np.where(pos_mask)[0].tolist()]
        neg_groups = [train_groups[i] for i in np.where(neg_mask)[0].tolist()]
        req(len(P) == len(pos_groups) and len(N) == len(neg_groups), f"fold {fold} class/group alignment changed")

        cal_pos = class_group_excluded_nn_distances(P, pos_groups, f"fold{fold}/positive")
        cal_neg = class_group_excluded_nn_distances(N, neg_groups, f"fold{fold}/nonpositive")
        req(len(cal_pos) == len(P) and len(cal_neg) == len(N), f"fold {fold} calibration cardinality changed")

        for j, global_i in enumerate(test_indices.tolist()):
            dp = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
            dn = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
            pp = conformity(cal_pos, dp)
            pn = conformity(cal_neg, dn)
            d_positive[global_i] = dp
            d_nonpositive[global_i] = dn
            p_positive[global_i] = pp
            p_nonpositive[global_i] = pn
            scores[global_i] = pp - pn

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos_mask.sum()),
            "nonpositive_references": int(neg_mask.sum()),
            "positive_strict_groups": len(set(pos_groups)),
            "nonpositive_strict_groups": len(set(neg_groups)),
            "heldout_positive": int(y[test].sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(set(train_groups)),
            "test_group_count": len(test_groups),
            "positive_calibration_min": float(np.min(cal_pos)),
            "positive_calibration_median": float(np.median(cal_pos)),
            "positive_calibration_max": float(np.max(cal_pos)),
            "nonpositive_calibration_min": float(np.min(cal_neg)),
            "nonpositive_calibration_median": float(np.median(cal_neg)),
            "nonpositive_calibration_max": float(np.max(cal_neg)),
        })

    for name, arr in (
        ("score", scores), ("p_positive", p_positive), ("p_nonpositive", p_nonpositive),
        ("d_positive", d_positive), ("d_nonpositive", d_nonpositive),
    ):
        req(arr.shape == (EXPECTED_HARD,) and np.isfinite(arr).all(), f"invalid {name} vector")
    req(np.all((p_positive > 0.0) & (p_positive <= 1.0)), "positive conformity outside (0,1]")
    req(np.all((p_nonpositive > 0.0) & (p_nonpositive <= 1.0)), "nonpositive conformity outside (0,1]")

    tie = [(hard_rank[fid], fid) for fid in ids]
    diversified_idx = q.diversity_order(scores, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in diversified_idx]
    fused_order = equal_rank_fusion(hard_order, local_order)

    baseline = q.v1.monotone_metrics(hard, hard_order, truths, eligible)
    local_metrics = q.v1.monotone_metrics(hard, local_order, truths, eligible)
    fused = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    req(int(baseline["qualified_matches"]) == PARENT_CONTROL["qualified_matches"], "hard-order qualified universe changed")
    req(int(local_metrics["qualified_matches"]) == PARENT_CONTROL["qualified_matches"], "local order changed qualified universe")
    req(int(fused["qualified_matches"]) == PARENT_CONTROL["qualified_matches"], "fusion changed qualified universe")
    # The immutable hard-order baseline must also match the exact parent run.
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(baseline[key]) == int(parent["baseline"][key]), f"hard baseline {key} differs from parent")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(baseline[key], parent["baseline"][key]), f"hard baseline {key} differs from parent")

    gates = {
        "recovered_at_100_strictly_better_than_parent": int(fused["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(fused["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(fused["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(fused["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(fused["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(fused["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_CLASS_CONDITIONAL_DISTANCE_V1" if passed else "FAIL_GMN_V31_CLASS_CONDITIONAL_DISTANCE_V1"

    evidence = {
        "candidate_count": EXPECTED_HARD,
        "score_sha256": array_sha(scores),
        "positive_conformity_sha256": array_sha(p_positive),
        "nonpositive_conformity_sha256": array_sha(p_nonpositive),
        "positive_distance_sha256": array_sha(d_positive),
        "nonpositive_distance_sha256": array_sha(d_nonpositive),
        "rows": [
            {
                "family_id": ids[i],
                "fold": int(folds[i]),
                "d_positive": float(d_positive[i]),
                "d_nonpositive": float(d_nonpositive[i]),
                "p_positive": float(p_positive[i]),
                "p_nonpositive": float(p_nonpositive[i]),
                "class_conformity_score": float(scores[i]),
            }
            for i in range(EXPECTED_HARD)
        ],
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    (a.output / "GMN_V31_CLASS_CONDITIONAL_DISTANCE_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "prelabel_sha256": prelabel_sha,
        "feature_matrix_sha256": array_sha(X),
        "hard_order_sha256": order_sha(hard_order),
        "class_conformity_score_sha256": array_sha(scores),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "parent_control": PARENT_CONTROL,
        "parent_reproduced_metrics": pm,
        "baseline": metric_subset(baseline),
        "class_conditional_local_only": metric_subset(local_metrics),
        "class_conditional_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "reference_definition": parent["reference_definition"],
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "nearest_k": 1,
        "distance": "ordinary Euclidean after fold-training z-score",
        "training_calibration": "within each outer training fold, nearest same-class reference excluding entire strict group",
        "class_conformity": "(1 + count(training group-excluded same-class NN distance >= query nearest-class distance))/(class_reference_count + 1)",
        "local_score": "p_positive-p_nonpositive",
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "pvalue_threshold_search": False,
        "pvalue_transform_search": False,
        "pseudocount_search": False,
        "calibration_pool_search": False,
        "class_prior_correction": False,
        "class_weight_search": False,
        "k_search": False,
        "metric_search": False,
        "feature_search": False,
        "scaling_search": False,
        "fold_search": False,
        "reference_definition_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "post_result_second_search": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_benchmark_authorized_by_this_result": bool(passed),
        "claim_boundary": "GMN development only; PASS authorizes only a separately frozen one-shot exposed SonotaCo comparison.",
    }
    out = a.output / "GMN_V31_CLASS_CONDITIONAL_DISTANCE_V1_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
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
        "score_sha256": array_sha(scores),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
