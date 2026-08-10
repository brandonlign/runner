#!/usr/bin/env python3
"""Operational equivalence proof for pair-portable hard/P19/P20 generation.

Hard-v8 and P20 remain byte-for-byte structural gates. P19 is required to reproduce every
non-floating/discrete field exactly. Derived floating fields are compared under a predeclared
1e-12 absolute/relative tolerance, and that tolerance is accepted only if the exact frozen #839
serialized-ranker deployment produces an equivalent feature matrix/prediction and the identical
final diversity order. No performance metric or truth label is used.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_P19_PRELABEL_FILE_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_PRELABEL_FILE_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED_ACTIVE_RANKER_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_MODEL_SHA = "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
EXPECTED_REFERENCE_FEATURE_SHA = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
EXPECTED_REFERENCE_PREDICTION_SHA = "7b771bef71dcdde86dc44a3a6499185b8865ff9de361c4830907b3a9198d2796"
EXPECTED_REFERENCE_APPLICATION_ORDER_SHA = "9063270f131b81bb0032026b2742b985ab0f8d5655abb46a1d405d30501b6d7d"
NUMERIC_ATOL = 1e-12
NUMERIC_RTOL = 1e-12
PREDICTION_ATOL = 1e-12


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def array_sha(a: np.ndarray) -> str:
    return application.array_sha256(np.asarray(a, dtype=np.float64))


def first_list_difference(left: list[Any], right: list[Any]) -> dict[str, Any]:
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {
                "index": i,
                "left_sha256": canonical_sha(a),
                "right_sha256": canonical_sha(b),
                "left_family_id": a.get("family_id") if isinstance(a, dict) else None,
                "right_family_id": b.get("family_id") if isinstance(b, dict) else None,
            }
    if len(left) != len(right):
        return {"index": min(len(left), len(right)), "left_length": len(left), "right_length": len(right)}
    return {"equal": True}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v8-source", type=Path, required=True)
    p.add_argument("--p19-source", type=Path, required=True)
    p.add_argument("--p20-source", type=Path, required=True)
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


def compare_tree(left: Any, right: Any, path: str = "$") -> dict[str, Any]:
    """Require exact discrete structure and quantify all floating-point differences."""
    stats: dict[str, Any] = {
        "discrete_equal": True,
        "numeric_within_tolerance": True,
        "numeric_leaf_count": 0,
        "numeric_different_leaf_count": 0,
        "max_abs_difference": 0.0,
        "max_relative_difference": 0.0,
        "differing_numeric_paths": [],
        "first_discrete_difference": None,
    }

    def fail_discrete(where: str, kind: str, a: Any, b: Any) -> None:
        if stats["first_discrete_difference"] is None:
            stats["first_discrete_difference"] = {
                "path": where, "kind": kind, "generated": a, "reference": b,
            }
        stats["discrete_equal"] = False

    def visit(a: Any, b: Any, where: str) -> None:
        if isinstance(a, bool) or isinstance(b, bool):
            if type(a) is not type(b) or a != b:
                fail_discrete(where, "bool", a, b)
            return
        if isinstance(a, int) or isinstance(b, int):
            if type(a) is not type(b) or a != b:
                fail_discrete(where, "integer_or_type", a, b)
            return
        if isinstance(a, float) or isinstance(b, float):
            if not isinstance(a, float) or not isinstance(b, float):
                fail_discrete(where, "numeric_type", type(a).__name__, type(b).__name__)
                return
            if not (math.isfinite(a) and math.isfinite(b)):
                fail_discrete(where, "nonfinite_float", a, b)
                return
            stats["numeric_leaf_count"] += 1
            abs_diff = abs(a - b)
            denom = max(abs(a), abs(b), 1e-300)
            rel_diff = abs_diff / denom
            stats["max_abs_difference"] = max(float(stats["max_abs_difference"]), float(abs_diff))
            stats["max_relative_difference"] = max(float(stats["max_relative_difference"]), float(rel_diff))
            if a != b:
                stats["numeric_different_leaf_count"] += 1
                if len(stats["differing_numeric_paths"]) < 100:
                    stats["differing_numeric_paths"].append({
                        "path": where,
                        "generated": a,
                        "reference": b,
                        "abs_difference": abs_diff,
                        "relative_difference": rel_diff,
                    })
            if not math.isclose(a, b, rel_tol=NUMERIC_RTOL, abs_tol=NUMERIC_ATOL):
                stats["numeric_within_tolerance"] = False
            return
        if isinstance(a, dict) or isinstance(b, dict):
            if not isinstance(a, dict) or not isinstance(b, dict):
                fail_discrete(where, "container_type", type(a).__name__, type(b).__name__)
                return
            if set(a) != set(b):
                fail_discrete(where, "dict_keys", sorted(set(a) - set(b)), sorted(set(b) - set(a)))
                return
            for key in sorted(a):
                visit(a[key], b[key], f"{where}.{key}")
            return
        if isinstance(a, list) or isinstance(b, list):
            if not isinstance(a, list) or not isinstance(b, list):
                fail_discrete(where, "container_type", type(a).__name__, type(b).__name__)
                return
            if len(a) != len(b):
                fail_discrete(where, "list_length", len(a), len(b))
                return
            for i, (x, y) in enumerate(zip(a, b)):
                visit(x, y, f"{where}[{i}]")
            return
        if type(a) is not type(b) or a != b:
            fail_discrete(where, "value_or_type", a, b)

    visit(left, right, path)
    return stats


def feature_difference(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    require(a.shape == b.shape, f"feature shapes differ: {a.shape} != {b.shape}")
    diff = np.abs(a - b)
    mask = a != b
    denom = np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-300)
    rel = diff / denom
    return {
        "shape": list(a.shape),
        "different_cells": int(mask.sum()),
        "different_rows": int(mask.any(axis=1).sum()),
        "max_abs_difference": float(diff.max()) if diff.size else 0.0,
        "max_relative_difference": float(rel.max()) if rel.size else 0.0,
        "allclose_atol": NUMERIC_ATOL,
        "allclose_rtol": NUMERIC_RTOL,
        "allclose": bool(np.allclose(a, b, atol=NUMERIC_ATOL, rtol=NUMERIC_RTOL)),
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha(args.p19_prelabel_json) == EXPECTED_P19_PRELABEL_FILE_SHA, "P19 prelabel file changed")
    require(sha(args.p20_prelabel_json) == EXPECTED_P20_PRELABEL_FILE_SHA, "P20 prelabel file changed")
    require(sha(args.active_ranker_source) == EXPECTED_ACTIVE_RANKER_SHA, "active #839 ranker source changed")
    require(sha(args.model_joblib) == EXPECTED_MODEL_SHA, "serialized #853 ranker changed")
    ref19 = json.loads(args.p19_prelabel_json.read_text())
    ref20 = json.loads(args.p20_prelabel_json.read_text())

    v8 = load_module(args.v8_source, "frozen_v8_pair_generator")
    p19 = load_module(args.p19_source, "frozen_p19_pair_generator")
    p20 = load_module(args.p20_source, "frozen_p20_pair_generator")
    urc = load_module(args.active_ranker_source, "frozen_active_urc_pair_generator_audit")
    v6 = p19.v6
    mult = p19.mult
    require(p20.mult is not None, "P20 multiplicity runtime unavailable")

    require(all(mult.v3.self_test().values()), "v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    generators.configure_pair(YEARS, support=support, mult=mult, v6=v6, v8=v8, p19=p19, p20=p20)
    support.CORPUS = p19.CORPUS
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence gate changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal retention changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _calibration, _hidden_labels_unused, sources = support.parse_catalogue(base)
    require(sorted(scan) == list(YEARS), "GMN years changed")
    require([x["key"] for x in sources] == list(MONTH_KEYS), "GMN month universe changed")

    built = generators.build_union_pair(
        years=YEARS,
        scan_by_year=scan,
        support=support,
        base=base,
        runtime=runtime,
        v6=v6,
        v8=v8,
        p19=p19,
        p20=p20,
        mult=mult,
    )

    hard19 = [p19.structural_family_payload(f) for f in built["hard"]["hard_families"]]
    soft19 = [p19.structural_family_payload(f) for f in built["p19_soft"]]
    hard20 = [p20.structural_family_payload(f) for f in built["hard"]["hard_families"]]
    soft20 = [p20.structural_family_payload(f) for f in built["p20"]["soft_families"]]
    quartets20 = {str(year): built["p20"]["quartets_by_year"][year] for year in YEARS}

    p19_numeric = compare_tree(soft19, ref19["soft_families"], "$.p19_soft")
    diagnostics = {
        "hard_order": {
            "generated_sha256": canonical_sha(built["hard_order"]),
            "reference_sha256": canonical_sha(ref19["hard_order"]),
            "equal": built["hard_order"] == ref19["hard_order"] == ref20["hard_order"],
        },
        "hard_p19": {
            "generated_sha256": canonical_sha(hard19),
            "reference_sha256": canonical_sha(ref19["hard_families"]),
            "equal": hard19 == ref19["hard_families"],
        },
        "p19_soft": {
            "generated_count": len(soft19),
            "reference_count": len(ref19["soft_families"]),
            "generated_sha256": canonical_sha(soft19),
            "reference_sha256": canonical_sha(ref19["soft_families"]),
            "byte_exact": soft19 == ref19["soft_families"],
            "discrete_exact": p19_numeric["discrete_equal"],
            "numeric_within_tolerance": p19_numeric["numeric_within_tolerance"],
            "numeric_tolerance": {"absolute": NUMERIC_ATOL, "relative": NUMERIC_RTOL},
            "numeric_diagnostics": p19_numeric,
            "generated_diagnostics": built["p19_diagnostics"],
            "reference_diagnostics": ref19["soft_diagnostics"],
        },
        "p20_soft": {
            "generated_count": len(soft20),
            "reference_count": len(ref20["soft_families"]),
            "generated_sha256": canonical_sha(soft20),
            "reference_sha256": canonical_sha(ref20["soft_families"]),
            "equal": soft20 == ref20["soft_families"],
        },
        "p20_quartets": {
            "generated_sha256": canonical_sha(quartets20),
            "reference_sha256": canonical_sha(ref20["isolated_quartets"]),
            "equal": quartets20 == ref20["isolated_quartets"],
        },
        "p19_support_context": p19.CORPUS,
        "p20_support_context": p20.CORPUS,
        "performance_metric_computed": False,
        "truth_labels_used_by_generator": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }

    require(built["hard_order"] == ref19["hard_order"] == ref20["hard_order"], "hard multiplicity order differs")
    require(hard19 == ref19["hard_families"], "portable hard families differ from P19 prelabel")
    require(hard20 == ref20["hard_families"], "portable hard families differ from P20 prelabel")
    require(bool(p19_numeric["discrete_equal"]), f"portable P19 discrete structure differs: {p19_numeric['first_discrete_difference']}")
    require(bool(p19_numeric["numeric_within_tolerance"]), f"portable P19 floating fields exceed frozen tolerance: {p19_numeric['max_abs_difference']}")
    require(soft20 == ref20["soft_families"], "portable P20 soft families differ")
    require(quartets20 == ref20["isolated_quartets"], "portable P20 isolated quartets differ")
    require(built["p19_diagnostics"] == ref19["soft_diagnostics"], "portable P19 diagnostics differ")
    require(built["p20"]["isolated_audits"] == ref20["isolated_audits"], "portable P20 isolated audits differ")
    require(built["p20"]["soft_diagnostics"] == ref20["soft_diagnostics"], "portable P20 recurrence diagnostics differ")

    # Strong downstream gate: compare the regenerated union to the immutable prelabel union through
    # the exact serialized #853 model and #860 year-portable application, without labels.
    reference_families = ref19["hard_families"] + ref19["soft_families"] + ref20["soft_families"]
    generated_families = hard19 + soft19 + soft20
    reference_ids = [str(f["family_id"]) for f in reference_families]
    generated_ids = [str(f["family_id"]) for f in generated_families]
    require(generated_ids == reference_ids, "generated union family order/IDs differ from frozen reference")
    source_by_id = {str(f["family_id"]): "hard" for f in hard19}
    source_by_id.update({str(f["family_id"]): "p19" for f in soft19})
    source_by_id.update({str(f["family_id"]): "p20" for f in soft20})
    hard_order = [str(x) for x in ref19["hard_order"]]

    reference_rank = application.score_and_rank(
        model_path=args.model_joblib,
        families=reference_families,
        source_by_id=source_by_id,
        hard_order=hard_order,
        scan_by_year=scan,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=urc,
    )
    generated_rank = application.score_and_rank(
        model_path=args.model_joblib,
        families=generated_families,
        source_by_id=source_by_id,
        hard_order=hard_order,
        scan_by_year=scan,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=urc,
    )
    ref_X = np.asarray(reference_rank["feature_matrix"], dtype=np.float64)
    gen_X = np.asarray(generated_rank["feature_matrix"], dtype=np.float64)
    feature_diag = feature_difference(gen_X, ref_X)
    require(array_sha(ref_X) == EXPECTED_REFERENCE_FEATURE_SHA, "reference #839 feature identity changed")
    require(bool(feature_diag["allclose"]), f"generated #839 feature matrix exceeds frozen numeric tolerance: {feature_diag}")

    ref_pred = np.asarray(reference_rank["prediction"], dtype=np.float64)
    gen_pred = np.asarray(generated_rank["prediction"], dtype=np.float64)
    require(array_sha(ref_pred) == EXPECTED_REFERENCE_PREDICTION_SHA, "reference deterministic #839 prediction identity changed")
    pred_max_abs = float(np.max(np.abs(gen_pred - ref_pred))) if len(ref_pred) else 0.0
    require(pred_max_abs <= PREDICTION_ATOL, f"generated #839 predictions differ too much: {pred_max_abs}")
    require(reference_rank["order_sha256"] == EXPECTED_REFERENCE_APPLICATION_ORDER_SHA, "reference deployment order identity changed")
    require(generated_rank["order"] == reference_rank["order"], "generated union changes final #839 diversity order")

    downstream = {
        "reference_feature_sha256": array_sha(ref_X),
        "generated_feature_sha256": array_sha(gen_X),
        "feature_difference": feature_diag,
        "reference_prediction_sha256": array_sha(ref_pred),
        "generated_prediction_sha256": array_sha(gen_pred),
        "prediction_max_abs_difference": pred_max_abs,
        "prediction_tolerance": PREDICTION_ATOL,
        "reference_application_order_sha256": reference_rank["order_sha256"],
        "generated_application_order_sha256": generated_rank["order_sha256"],
        "final_application_order_exact": generated_rank["order"] == reference_rank["order"],
    }
    diagnostics["downstream_ranker_equivalence"] = downstream
    (args.output / "urc_pair_portable_generator_equivalence_diagnostics_v1.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(diagnostics, indent=2, sort_keys=True))

    result = {
        "verdict": "PASS_URC_PAIR_PORTABLE_GENERATOR_GMN_OPERATIONAL_EQUIVALENCE",
        "years": list(YEARS),
        "hard_count": len(hard19),
        "p19_soft_count": len(soft19),
        "p20_soft_count": len(soft20),
        "union_count": len(generated_families),
        "exact_hard_order_match": True,
        "exact_hard_family_match": True,
        "exact_p19_discrete_match": True,
        "p19_numeric_equivalent": True,
        "p19_numeric_atol": NUMERIC_ATOL,
        "p19_numeric_rtol": NUMERIC_RTOL,
        "p19_numeric_max_abs_difference": p19_numeric["max_abs_difference"],
        "p19_numeric_max_relative_difference": p19_numeric["max_relative_difference"],
        "p19_numeric_different_leaf_count": p19_numeric["numeric_different_leaf_count"],
        "exact_p20_family_match": True,
        "exact_p20_isolated_quartet_match": True,
        "reference_feature_matrix_sha256": array_sha(ref_X),
        "generated_feature_matrix_sha256": array_sha(gen_X),
        "feature_matrix_numeric_equivalent": bool(feature_diag["allclose"]),
        "prediction_max_abs_difference": pred_max_abs,
        "exact_final_application_order_match": True,
        "final_application_order_sha256": generated_rank["order_sha256"],
        "performance_metric_computed": False,
        "truth_labels_used_by_generator_or_ranker": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    require((result["hard_count"], result["p19_soft_count"], result["p20_soft_count"], result["union_count"]) == (226, 1075, 3203, 4504), "reference candidate counts changed")
    (args.output / "urc_pair_portable_generator_gmn_equivalence_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
