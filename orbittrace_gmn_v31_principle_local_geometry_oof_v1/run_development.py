#!/usr/bin/env python3
"""Target-excluded GMN diagnostic for the v31 nearest-reference geometry principle."""
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
CORPUS = "orbittrace-gmn-v31-principle-local-geometry-oof-v1"
EXPECTED_HARD = 226
FEATURE_DIM = 23
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"


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
            req(not (BLIND[0] <= value <= BLIND[1]), f"protected-region event reached diagnostic: {row.get('id')}")
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
    # Exact intrinsic structural block: indices 1..10 inclusive. This excludes
    # source/soft metadata and the explicit hard-rank percentile at index 11.
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


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == QUALITY_SHA, "active GMN ranker source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "v8 result changed")
    req(sha(a.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 hard-family prelabel changed")

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

    # Fail closed before constructing any representation or interpreting truth.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = event_sol(row)
    for family in hard:
        for year in YEARS:
            centroid = family.get("centroids", {}).get(str(year))
            req(centroid is not None, f"missing centroid for {family['family_id']} {year}")
            csol = float(centroid["sol"]) % 360.0
            req(not (BLIND[0] <= csol <= BLIND[1]), f"protected centroid reached diagnostic: {family['family_id']} {year}")

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

    # Seal the complete label-free representation before hidden labels are interpreted.
    np.save(a.output / "GMN_V31_PRINCIPLE_INTRINSIC_FEATURES.npy", X, allow_pickle=False)
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
    prelabel_path = a.output / "GMN_V31_PRINCIPLE_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Development truth begins here, after the feature representation is fully sealed.
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

    margins = np.zeros(EXPECTED_HARD, dtype=float)
    fold_diag: list[dict[str, Any]] = []
    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        req(y[train].any() and (~y[train]).any(), f"fold {fold} lacks both reference classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        train_indices = np.where(train)[0]
        test_indices = np.where(test)[0]
        pos = y[train]
        neg = ~pos
        P = Ztr[pos]
        N = Ztr[neg]
        for j, global_i in enumerate(test_indices.tolist()):
            dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
            dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
            margins[global_i] = dneg - dpos
        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "heldout_positive": int(y[test].sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
        })
    req(np.isfinite(margins).all(), "nonfinite OOF geometry margin")

    tie = [(hard_rank[fid], fid) for fid in ids]
    diversified_idx = q.diversity_order(margins, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in diversified_idx]
    fused_order = equal_rank_fusion(hard_order, local_order)

    baseline = q.v1.monotone_metrics(hard, hard_order, truths, eligible)
    local_metrics = q.v1.monotone_metrics(hard, local_order, truths, eligible)
    fused = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    req(int(local_metrics["qualified_matches"]) == int(baseline["qualified_matches"]), "local order changed qualified universe")
    req(int(fused["qualified_matches"]) == int(baseline["qualified_matches"]), "fused order changed qualified universe")

    gates = {
        "recovered_at_100_strictly_better": int(fused["recovered_at_100"]) > int(baseline["recovered_at_100"]),
        "recovered_at_50_not_worse": int(fused["recovered_at_50"]) >= int(baseline["recovered_at_50"]),
        "top100_precision_not_worse": float(fused["top100_dominant_precision"]) >= float(baseline["top100_dominant_precision"]),
        "mrr_not_worse": float(fused["mrr"]) >= float(baseline["mrr"]),
        "qualified_count_identical": int(fused["qualified_matches"]) == int(baseline["qualified_matches"]),
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF" if passed else "FAIL_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_V31_PRINCIPLE_MECHANISM_DIAGNOSTIC_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "prelabel_sha256": prelabel_sha,
        "feature_matrix_sha256": array_sha(X),
        "margin_sha256": array_sha(margins),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "reference_definition": "frozen GMN qualified family: precision>=0.5 and overlap>=4 for best eligible recurrent shower",
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "nearest_k": 1,
        "distance": "ordinary Euclidean after fold-training z-score",
        "margin": "d_nonpositive-d_positive",
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "baseline": metric_subset(baseline),
        "local_geometry_only": metric_subset(local_metrics),
        "equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "fold_diagnostics": fold_diag,
        "k_search": False,
        "metric_search": False,
        "feature_search": False,
        "scaling_search": False,
        "threshold_search": False,
        "weight_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "reference_definition_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "family_deletion": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
        "claim_boundary": "GMN mechanism diagnostic only. PASS may motivate a separately frozen successor; FAIL permanently closes this exact v31-principle GMN mapping and fusion.",
    }
    out = a.output / "GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "baseline100": baseline["recovered_at_100"],
        "fused100": fused["recovered_at_100"],
        "baseline50": baseline["recovered_at_50"],
        "fused50": fused["recovered_at_50"],
        "baseline_precision": baseline["top100_dominant_precision"],
        "fused_precision": fused["top100_dominant_precision"],
        "baseline_mrr": baseline["mrr"],
        "fused_mrr": fused["mrr"],
        "qualified": baseline["qualified_matches"],
        "prelabel_sha256": prelabel_sha,
        "margin_sha256": array_sha(margins),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
