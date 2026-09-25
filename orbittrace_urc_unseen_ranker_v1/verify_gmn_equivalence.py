#!/usr/bin/env python3
"""Verify portable unseen-data #839 ranker against frozen #853 GMN identities.

Implementation-equivalence only: no shower-performance metric and no model selection.
The audit now rebuilds the original #839 34-column feature matrix side-by-side with
the portable matrix and writes exact diagnostics before any equivalence assertion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_urc_unseen_ranker_v1 import application

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_FEATURE_SHA = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
HISTORICAL_FIT_PREDICTION_SHA = "493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac"
EXPECTED_MODEL_SHA = "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
EXPECTED_ACTIVE_SOURCE_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_COUNTS = (226, 1075, 3203, 4504)
PREDICTION_EQUIVALENCE_ATOL = 1e-12


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--active-ranker-source", type=Path, required=True)
    p.add_argument("--model-joblib", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def native_feature_matrix(
    urc: Any,
    families: list[dict[str, Any]],
    source: dict[str, str],
    hard_order: list[str],
    scan: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, str]]]:
    """Literal #839 feature construction from the frozen active source."""
    ids = [str(f["family_id"]) for f in families]
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    lookup = urc.v2.event_lookup(scan)
    cm = urc.centroid_matrix(families)
    nf = urc.neighbor_features(cm)
    rows: list[list[float]] = []
    for i, family in enumerate(families):
        fid = str(family["family_id"])
        src = source[fid]
        source_feats = [float(src == "hard"), float(src == "p19"), float(src == "p20")]
        p20_feats = [
            float(family.get("p20_cross_year_distance", 0.0)),
            math.log1p(max(int(family.get("p20_min_anchor_count", 0)), 0)),
            float(family.get("p20_min_bin_strength", 0.0)),
            float(family.get("p20_min_quartet_score", 0.0)),
        ]
        rows.append(
            urc.v1.structural_features(family, hard_rank)
            + urc.v2.cohesion_features(family, lookup, support, base)
            + source_feats
            + p20_feats
            + nf[i].tolist()
        )
    X = np.asarray(rows, dtype=np.float64)
    require(X.shape == (len(families), application.EXPECTED_FEATURES), f"native feature shape changed: {X.shape}")
    require(np.isfinite(X).all(), "native feature matrix contains nonfinite values")
    tie = [(hard_rank.get(fid, 999999), fid) for fid in ids]
    return X, cm, tie


def first_difference(a: np.ndarray, b: np.ndarray) -> dict[str, Any] | None:
    if a.shape != b.shape:
        return {"shape_a": list(a.shape), "shape_b": list(b.shape)}
    mask = a != b
    if not mask.any():
        return None
    row, col = np.argwhere(mask)[0]
    diff = np.abs(a - b)
    max_pos = np.unravel_index(int(np.argmax(diff)), diff.shape)
    return {
        "first_row": int(row),
        "first_col": int(col),
        "native_value": float(a[row, col]),
        "portable_value": float(b[row, col]),
        "first_abs_difference": float(abs(a[row, col] - b[row, col])),
        "max_abs_difference": float(diff[max_pos]),
        "max_row": int(max_pos[0]),
        "max_col": int(max_pos[1]),
        "different_cells": int(mask.sum()),
        "different_rows": int(mask.any(axis=1).sum()),
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha(args.active_ranker_source) == EXPECTED_ACTIVE_SOURCE_SHA, "active ranker source changed")
    require(sha(args.model_joblib) == EXPECTED_MODEL_SHA, "full-GMN serialized model changed")

    urc = load_module(args.active_ranker_source, "frozen_active_urc")
    p19 = json.loads(args.p19_prelabel_json.read_text())
    p20 = json.loads(args.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    s19 = p19["soft_families"]
    s20 = p20["soft_families"]
    require(hard == p20["hard_families"], "hard-family payloads differ")
    families = hard + s19 + s20
    require((len(hard), len(s19), len(s20), len(families)) == EXPECTED_COUNTS, "candidate counts changed")
    ids = [str(f["family_id"]) for f in families]
    hard_order = [str(x) for x in p19["hard_order"]]
    source = {str(f["family_id"]): "hard" for f in hard}
    source.update({str(f["family_id"]): "p19" for f in s19})
    source.update({str(f["family_id"]): "p20" for f in s20})

    urc.v1.mult.YEARS = YEARS
    urc.v1.mult.MONTH_KEYS = MONTH_KEYS
    urc.v1.mult.TOP_K = 100
    runtime = urc.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-urc-unseen-ranker-equivalence-v1"
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _calibration, _hidden_labels_unused, sources = support.parse_catalogue(base)
    require(sorted(scan) == list(YEARS), "GMN year universe changed")
    require([x["key"] for x in sources] == list(MONTH_KEYS), "GMN month universe changed")

    portable = application.score_and_rank(
        model_path=args.model_joblib,
        families=families,
        source_by_id=source,
        hard_order=hard_order,
        scan_by_year=scan,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=urc,
    )
    native_X, native_cm, native_tie = native_feature_matrix(urc, families, source, hard_order, scan, support, base)
    portable_X = np.asarray(portable["feature_matrix"], dtype=np.float64)
    native_feature_sha = application.array_sha256(native_X)
    portable_feature_sha = application.array_sha256(portable_X)
    family_order_sha = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    feature_diag = {
        "expected_feature_sha256": EXPECTED_FEATURE_SHA,
        "native_feature_sha256": native_feature_sha,
        "portable_feature_sha256": portable_feature_sha,
        "family_order_sha256": family_order_sha,
        "native_shape": list(native_X.shape),
        "portable_shape": list(portable_X.shape),
        "difference": first_difference(native_X, portable_X),
    }
    (args.output / "feature_equivalence_diagnostic.json").write_text(json.dumps(feature_diag, indent=2, sort_keys=True) + "\n")
    print(json.dumps(feature_diag, indent=2, sort_keys=True), flush=True)

    # Gate in two stages: first prove the frozen/native reconstruction still equals #853, then
    # prove the portable implementation equals that exact reconstruction cell-for-cell.
    require(native_feature_sha == EXPECTED_FEATURE_SHA, f"native #839 feature reconstruction differs from #853: {native_feature_sha}")
    require(np.array_equal(native_X, portable_X), f"portable feature matrix differs from native #839 matrix: {portable_feature_sha}")

    deterministic_sha = application.array_sha256(portable["prediction"])
    model = joblib.load(args.model_joblib)
    require(int(model.n_features_in_) == application.EXPECTED_FEATURES, "model feature count changed")
    native_prediction = np.asarray(model.predict(native_X), dtype=np.float64)
    native_sha = application.array_sha256(native_prediction)
    if hasattr(model, "set_params"):
        model.set_params(n_jobs=1)
    single_prediction = np.asarray(model.predict(portable_X), dtype=np.float64)
    require(np.array_equal(single_prediction, portable["prediction"]), "application single-thread prediction path differs")
    max_abs = float(np.max(np.abs(native_prediction - single_prediction))) if len(single_prediction) else 0.0
    require(max_abs <= PREDICTION_EQUIVALENCE_ATOL, f"parallel/single prediction difference too large: {max_abs}")

    X2, cm, tie = application.build_feature_matrix(
        families=families,
        source_by_id=source,
        hard_order=hard_order,
        scan_by_year=scan,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=urc,
    )
    require(np.array_equal(X2, portable_X), "feature reconstruction not deterministic")
    require(np.array_equal(native_cm, cm), "portable centroid matrix differs from native #839 matrix")
    require(native_tie == tie, "portable tie semantics differ from native #839")
    native_idx = urc.diversity_order(native_prediction, native_cm, application.DIVERSITY_LAMBDA, application.DIVERSITY_SCALE, native_tie)
    native_order = [ids[i] for i in native_idx]
    require(native_order == portable["order"], "floating accumulation changes final diversity order")

    result = {
        "verdict": "PASS_URC_UNSEEN_RANKER_GMN_EQUIVALENCE",
        "years": list(YEARS),
        "candidate_count": len(families),
        "feature_matrix_shape": list(portable_X.shape),
        "feature_matrix_sha256": portable_feature_sha,
        "native_feature_matrix_sha256": native_feature_sha,
        "model_joblib_sha256": sha(args.model_joblib),
        "deterministic_prediction_sha256": deterministic_sha,
        "native_parallel_prediction_sha256": native_sha,
        "historical_fit_prediction_sha256_diagnostic": HISTORICAL_FIT_PREDICTION_SHA,
        "max_abs_parallel_vs_single_prediction": max_abs,
        "parallel_and_single_diversity_order_identical": True,
        "application_order_sha256": portable["order_sha256"],
        "prediction_n_jobs": 1,
        "truth_labels_used_by_application": False,
        "performance_metric_computed": False,
        "adaptation": "development-year addressing replaced by explicit pair years/event-year map; native #839 matrix and portable matrix must be exactly identical before serialized model application",
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    (args.output / "urc_unseen_ranker_gmn_equivalence_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
