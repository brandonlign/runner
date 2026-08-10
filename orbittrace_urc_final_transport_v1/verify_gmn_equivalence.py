#!/usr/bin/env python3
"""Implementation equivalence test for generic_two_year_inference on GMN 2022/2023.

This computes no new scientific comparison. It requires the generic transport to reproduce the
already-frozen pretruth hard/P19/P20 family payloads and the exact full-GMN deployment feature and
prediction hashes before the adapter can be used on an unseen dataset.
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

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20

from orbittrace_urc_final_transport_v1 import generic_two_year_inference as generic

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_FEATURE_SHA = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
EXPECTED_PREDICTION_SHA = "493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac"
EXPECTED_MODEL_SHA = "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
EXPECTED_ACTIVE_SOURCE_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"


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


def json_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--active-ranker-source", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
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
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(sha(a.active_ranker_source) == EXPECTED_ACTIVE_SOURCE_SHA, "active URC source changed")
    require(sha(a.model) == EXPECTED_MODEL_SHA, "full-GMN fitted model changed")
    urc = load_module(a.active_ranker_source, "active_urc")

    runtime = v6.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-urc-generic-two-year-inference-gmn-equivalence"
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _calibration, _hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan) == [2022, 2023], "GMN equivalence years changed")
    require([x["key"] for x in sources] == list(MONTH_KEYS), "GMN equivalence months changed")

    generated = generic.generate_union_from_scan(scan, YEARS, runtime, support, base, v6, v8, p19, p20)
    p19_ref = json.loads(a.p19_prelabel_json.read_text())
    p20_ref = json.loads(a.p20_prelabel_json.read_text())

    hard_payload = [p19.structural_family_payload(f) for f in generated["hard_families"]]
    p19_payload = [p19.structural_family_payload(f) for f in generated["p19_soft_families"]]
    p20_hard_payload = [p20.structural_family_payload(f) for f in generated["hard_families"]]
    p20_payload = [p20.structural_family_payload(f) for f in generated["p20_soft_families"]]
    require(generated["hard_order"] == p19_ref["hard_order"] == p20_ref["hard_order"], "hard order transport mismatch")
    require(hard_payload == p19_ref["hard_families"], "P19 hard structural payload mismatch")
    require(p19_payload == p19_ref["soft_families"], "P19 soft structural payload mismatch")
    require(p20_hard_payload == p20_ref["hard_families"], "P20 hard structural payload mismatch")
    require(p20_payload == p20_ref["soft_families"], "P20 soft structural payload mismatch")

    X, cm, ties = generic.feature_matrix_for_union(generated, scan, YEARS, urc, support, base)
    require(array_sha(X) == EXPECTED_FEATURE_SHA, f"feature-matrix transport mismatch: {array_sha(X)}")
    model = joblib.load(a.model)
    pred = np.asarray(model.predict(X), dtype=np.float64)
    require(array_sha(pred) == EXPECTED_PREDICTION_SHA, f"prediction transport mismatch: {array_sha(pred)}")
    ranked = generic.rank_generated_union(generated, scan, YEARS, urc, support, base, model)
    require(np.array_equal(ranked["feature_matrix"], X), "rank feature matrix changed")

    result = {
        "verdict": "PASS_GENERIC_TWO_YEAR_URC_GMN_IMPLEMENTATION_EQUIVALENCE",
        "years": [2022, 2023],
        "candidate_counts": {
            "hard": len(generated["hard_families"]),
            "p19": len(generated["p19_soft_families"]),
            "p20": len(generated["p20_soft_families"]),
            "union": len(generated["families"]),
        },
        "hard_payload_sha256": json_sha(hard_payload),
        "p19_payload_sha256": json_sha(p19_payload),
        "p20_payload_sha256": json_sha(p20_payload),
        "hard_order_sha256": hashlib.sha256("\n".join(generated["hard_order"]).encode()).hexdigest(),
        "feature_matrix_shape": list(X.shape),
        "feature_matrix_sha256": array_sha(X),
        "centroid_matrix_sha256": array_sha(cm),
        "prediction_sha256": array_sha(pred),
        "deployment_rank_sha256": hashlib.sha256("\n".join(ranked["order"]).encode()).hexdigest(),
        "tie_rows": len(ties),
        "scientific_performance_evaluated": False,
        "hidden_labels_used_after_parser": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    (a.output / "generic_two_year_urc_gmn_equivalence.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
