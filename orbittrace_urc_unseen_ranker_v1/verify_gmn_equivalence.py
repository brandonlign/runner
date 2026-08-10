#!/usr/bin/env python3
"""Verify the portable unseen-data #839 ranker adapter against frozen #853 GMN hashes.

This is an implementation equivalence test only. It computes no shower-performance metric and
performs no model selection. PASS means the year-portable feature builder is exactly identical to
#853 on the original 2022/2023 development pair and the serialized model predictions are exact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_urc_unseen_ranker_v1 import application

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_FEATURE_SHA = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
EXPECTED_PREDICTION_SHA = "493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac"
EXPECTED_MODEL_SHA = "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
EXPECTED_ACTIVE_SOURCE_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_COUNTS = (226, 1075, 3203, 4504)


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
    hard_order = [str(x) for x in p19["hard_order"]]
    source = {str(f["family_id"]): "hard" for f in hard}
    source.update({str(f["family_id"]): "p19" for f in s19})
    source.update({str(f["family_id"]): "p20" for f in s20})

    # Restore the same frozen event representation needed by label-free cohesion features.
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
    feature_sha = application.array_sha256(portable["feature_matrix"])
    prediction_sha = application.array_sha256(portable["prediction"])
    require(feature_sha == EXPECTED_FEATURE_SHA, f"portable feature matrix differs: {feature_sha}")
    require(prediction_sha == EXPECTED_PREDICTION_SHA, f"portable fitted predictions differ: {prediction_sha}")

    # Independent model load guard: no accidental estimator substitution.
    model = joblib.load(args.model_joblib)
    require(int(model.n_features_in_) == application.EXPECTED_FEATURES, "model feature count changed")
    require(np.array_equal(np.asarray(model.predict(portable["feature_matrix"]), dtype=np.float64), portable["prediction"]), "prediction path mismatch")

    result = {
        "verdict": "PASS_URC_UNSEEN_RANKER_GMN_EQUIVALENCE",
        "years": list(YEARS),
        "candidate_count": len(families),
        "feature_matrix_shape": list(portable["feature_matrix"].shape),
        "feature_matrix_sha256": feature_sha,
        "prediction_sha256": prediction_sha,
        "model_joblib_sha256": sha(args.model_joblib),
        "application_order_sha256_diagnostic": portable["order_sha256"],
        "truth_labels_used_by_application": False,
        "performance_metric_computed": False,
        "adaptation": "literal development-year addressing replaced only by explicit pair years/event-year map; exact GMN equivalence required",
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    (args.output / "urc_unseen_ranker_gmn_equivalence_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
