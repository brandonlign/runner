#!/usr/bin/env python3
"""Fit the already-selected #839 URC ranker once on all allowed GMN development labels.

This is deployment fitting, not another development comparison. The model complexity, features,
group weighting, candidate universe and diversity rule were already frozen by #839/#842/#848.
No fitted-training performance is computed or used for selection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED_COUNTS = (226, 1075, 3203, 4504)
EXPECTED_ACTIVE_SOURCE_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_SELECTED_ORDER_SHA = "ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449"
EXPECTED_UNION_RESULT_SHA = "e932ad2507f6305a96c9d442a556593e470c966f1adfc2f4f2098adbc8f9dbcd"
EXPECTED_P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
EXPECTED_P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(a: np.ndarray) -> str:
    x = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(str(x.dtype).encode())
    h.update(json.dumps(list(x.shape), separators=(",", ":")).encode())
    h.update(x.tobytes(order="C"))
    return h.hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--active-ranker-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-result-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--union-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(sha(a.active_ranker_source) == EXPECTED_ACTIVE_SOURCE_SHA, "active #839 source changed")
    for path, expected, label in (
        (a.p19_result_json, EXPECTED_P19_RESULT_SHA, "P19 result"),
        (a.p19_prelabel_json, EXPECTED_P19_PRELABEL_SHA, "P19 prelabel"),
        (a.p20_result_json, EXPECTED_P20_RESULT_SHA, "P20 result"),
        (a.p20_prelabel_json, EXPECTED_P20_PRELABEL_SHA, "P20 prelabel"),
        (a.union_result_json, EXPECTED_UNION_RESULT_SHA, "#839 result"),
    ):
        require(sha(path) == expected, f"{label} changed")

    frozen_result = json.loads(a.union_result_json.read_text())
    require(frozen_result["verdict"] == "PASS_URC_UNION_RANKING_FEASIBILITY", "#839 did not pass")
    selected = frozen_result["best_cross_validated"]
    require(float(selected["lambda"]) == 0.8 and float(selected["scale"]) == 1.0, "selected diversity changed")
    require(selected["order_sha256"] == EXPECTED_SELECTED_ORDER_SHA, "selected development order changed")

    urc = load_module(a.active_ranker_source, "orbittrace_active_urc_ranker")
    v1 = urc.v1
    v2 = urc.v2
    p19 = json.loads(a.p19_prelabel_json.read_text())
    p20 = json.loads(a.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    s19 = p19["soft_families"]
    s20 = p20["soft_families"]
    hard_order = [str(x) for x in p19["hard_order"]]
    require(hard == p20["hard_families"], "hard candidate universe differs")
    fams = hard + s19 + s20
    require((len(hard), len(s19), len(s20), len(fams)) == EXPECTED_COUNTS, "union candidate counts changed")
    ids = [str(f["family_id"]) for f in fams]
    require(len(ids) == len(set(ids)), "family IDs collide")
    source = {str(f["family_id"]): "hard" for f in hard}
    source.update({str(f["family_id"]): "p19" for f in s19})
    source.update({str(f["family_id"]): "p20" for f in s20})

    v1.mult.YEARS = YEARS
    v1.mult.MONTH_KEYS = MONTH_KEYS
    v1.mult.TOP_K = 100
    runtime = v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-urc-final-ranker-fit-v1"
    support.RANKING_VARIANTS = ("persistence",)
    require((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, labels, sources = support.parse_catalogue(base)
    require(sorted(scan) == list(YEARS), "GMN development years changed")
    require([x["key"] for x in sources] == list(MONTH_KEYS), "GMN development months changed")

    eligible = v1.eligible_labels(labels)
    by = {str(f["family_id"]): f for f in fams}
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    truths = {fid: v1.family_truth(by[fid], labels, eligible) for fid in ids}
    lookup = v2.event_lookup(scan)
    cm = urc.centroid_matrix(fams)
    nf = urc.neighbor_features(cm)
    rows: list[list[float]] = []
    for i, f in enumerate(fams):
        fid = str(f["family_id"])
        src = source[fid]
        source_feats = [float(src == "hard"), float(src == "p19"), float(src == "p20")]
        p20_feats = [
            float(f.get("p20_cross_year_distance", 0.0)),
            math.log1p(max(int(f.get("p20_min_anchor_count", 0)), 0)),
            float(f.get("p20_min_bin_strength", 0.0)),
            float(f.get("p20_min_quartet_score", 0.0)),
        ]
        rows.append(
            v1.structural_features(f, hard_rank)
            + v2.cohesion_features(f, lookup, support, base)
            + source_feats
            + p20_feats
            + nf[i].tolist()
        )
    X = np.asarray(rows, dtype=np.float64)
    require(X.shape[0] == 4504 and X.ndim == 2 and np.all(np.isfinite(X)), f"invalid training feature matrix {X.shape}")
    target = np.asarray([float(truths[fid]["f1"]) if truths[fid]["positive"] else 0.0 for fid in ids], dtype=np.float64)
    groups = [("SHOWER/" + str(truths[fid]["best_label"])) if truths[fid]["best_label"] is not None else ("NEG/" + fid) for fid in ids]
    weights = urc.grouped_weights(groups)
    require(np.all(np.isfinite(target)) and np.all(np.isfinite(weights)), "invalid target/weights")

    # This is the already-selected estimator fit once to all development candidates.
    model = urc.model()
    model.fit(X, target, sample_weight=weights)
    train_prediction = np.asarray(model.predict(X), dtype=np.float64)
    require(np.all(np.isfinite(train_prediction)), "nonfinite fitted-model predictions")

    model_path = a.output / "urc_final_ranker.joblib"
    joblib.dump(model, model_path, compress=3, protocol=4)
    metadata = {
        "verdict": "FROZEN_FULL_GMN_URC_RANKER_FIT",
        "scientific_source_sha256": EXPECTED_ACTIVE_SOURCE_SHA,
        "training_candidate_counts": {"hard": 226, "p19_soft": 1075, "p20_soft": 3203, "union": 4504},
        "training_years": [2022, 2023],
        "blind_exclusion": [20.0, 55.0],
        "feature_matrix_shape": list(X.shape),
        "feature_matrix_sha256": array_sha(X),
        "target_vector_sha256": array_sha(target),
        "group_weight_sha256": array_sha(np.asarray(weights, dtype=np.float64)),
        "training_prediction_sha256": array_sha(train_prediction),
        "model_joblib_sha256": sha(model_path),
        "model": {
            "class": "ExtraTreesRegressor",
            "n_estimators": 600,
            "max_depth": 4,
            "min_samples_leaf": 5,
            "max_features": None,
            "random_state": 20260809,
            "n_jobs_source_setting": -1,
        },
        "deployment_diversity": {"lambda": 0.8, "scale": 1.0},
        "deployment_rule": "predict fixed structural/cohesion/source/neighbor features on unseen families, then apply exact #839 diversity_order; no test labels or refit",
        "training_performance_computed": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    (a.output / "urc_final_ranker_fit.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": metadata["verdict"],
        "feature_shape": metadata["feature_matrix_shape"],
        "feature_sha256": metadata["feature_matrix_sha256"],
        "target_sha256": metadata["target_vector_sha256"],
        "model_sha256": metadata["model_joblib_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
