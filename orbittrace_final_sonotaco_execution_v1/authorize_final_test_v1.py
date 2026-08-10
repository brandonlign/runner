#!/usr/bin/env python3
"""Fail-closed authorization gate for the one-shot SonotaCo 2013/2014 final test.

No data transport occurs here. The eventual execution workflow supplies immutable provenance
manifests; this script only decides whether all pre-access freezes are satisfied.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

AUTHORIZED = "AUTHORIZED_FINAL_SONOTACO_2013_2014_EXECUTION"
NOT_READY_GENERATOR = "NOT_AUTHORIZED_GENERATOR_EQUIVALENCE"
NOT_READY_RANKER = "NOT_AUTHORIZED_RANKER_IDENTITY"
NOT_READY_COMPARATORS = "NOT_AUTHORIZED_COMPARATOR_IDENTITY"
NOT_READY_EVALUATOR = "NOT_AUTHORIZED_EVALUATOR_IDENTITY"
NOT_READY_EXTERNAL = "NOT_AUTHORIZED_EXTERNAL_GATE_FREEZE"
INVALID_FIREWALL = "NOT_AUTHORIZED_FIREWALL_INTEGRITY"

GENERATOR_PASS = "PASS_URC_PAIR_PORTABLE_GENERATOR_GMN_OPERATIONAL_EQUIVALENCE"
GENERATOR_NUMERIC_ATOL = 1e-12
GENERATOR_NUMERIC_RTOL = 1e-12
GENERATOR_PREDICTION_ATOL = 1e-12
GENERATOR_FINAL_ORDER_SHA = "9063270f131b81bb0032026b2742b985ab0f8d5655abb46a1d405d30501b6d7d"
MODEL_SHA = "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
FEATURE_SHA = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
PREDICTION_SHA = "493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac"
COMPARATOR_RUN = 31346168826
COMPARATOR_ARTIFACT = 9047392743
COMPARATOR_DIGEST = "sha256:8acb1986561d44194e2b7ebf5eb725a115eff5ba10b9b5d30a74f63a71a93fbc"
SUGAR_SHA = "5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb"
HDBSCAN_SHA = "a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2"
EVALUATOR_SHA = "cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c"
EVALUATOR_RUN = 31344796531
EVALUATOR_ARTIFACT = 9046953388
EVALUATOR_DIGEST = "sha256:315f01965b1fec3820f32ab56cb57d96f7401373e3d2d127c78d7da35808210f"
EXTERNAL_GATE_MERGE = "45428174b36b8a5207951bc2c046ced3aa2e9781"
EXTERNAL_PASS = "PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION"


def is_sha(x: Any) -> bool:
    return isinstance(x, str) and re.fullmatch(r"[0-9a-f]{40}", x) is not None


def is_digest(x: Any) -> bool:
    return isinstance(x, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", x) is not None


def exact_float(x: Any, expected: float) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and float(x) == expected


def bounded_nonnegative_float(x: Any, ceiling: float) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and 0.0 <= float(x) <= ceiling


def result(state: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "state": state,
        "sonotaco_2013_2014_scientific_access_authorized": state == AUTHORIZED,
        "maarsy_scientific_access_authorized": False,
        "target_access_authorized": False,
        "details": details or {},
    }


def adjudicate(p: dict[str, Any]) -> dict[str, Any]:
    firewall = p.get("firewall", {})
    required_firewall = {
        "target_information_access": False,
        "target_region_access": False,
        "sonotaco_scientific_access_already_occurred": False,
        "maarsy_scientific_access_already_occurred": False,
    }
    bad = [k for k, v in required_firewall.items() if firewall.get(k) is not v]
    if bad:
        return result(INVALID_FIREWALL, {"failed": bad})

    g = p.get("generator_equivalence", {})
    generator_checks = {
        "verdict": g.get("verdict") == GENERATOR_PASS,
        "pr": g.get("pr_number") == 862,
        "source_commit": is_sha(g.get("source_commit")),
        "run_id": isinstance(g.get("run_id"), int) and g.get("run_id", 0) > 0,
        "artifact_id": isinstance(g.get("artifact_id"), int) and g.get("artifact_id", 0) > 0,
        "artifact_digest": is_digest(g.get("artifact_digest")),
        "hard_count": g.get("hard_count") == 226,
        "p19_soft_count": g.get("p19_soft_count") == 1075,
        "p20_soft_count": g.get("p20_soft_count") == 3203,
        "union_count": g.get("union_count") == 4504,
        "hard_order_exact": g.get("exact_hard_order_match") is True,
        "hard_family_exact": g.get("exact_hard_family_match") is True,
        "p19_discrete_exact": g.get("exact_p19_discrete_match") is True,
        "p19_numeric_equivalent": g.get("p19_numeric_equivalent") is True,
        "p19_atol_frozen": exact_float(g.get("p19_numeric_atol"), GENERATOR_NUMERIC_ATOL),
        "p19_rtol_frozen": exact_float(g.get("p19_numeric_rtol"), GENERATOR_NUMERIC_RTOL),
        "p19_max_abs_bounded": bounded_nonnegative_float(g.get("p19_numeric_max_abs_difference"), GENERATOR_NUMERIC_ATOL),
        "p20_family_exact": g.get("exact_p20_family_match") is True,
        "p20_quartets_exact": g.get("exact_p20_isolated_quartet_match") is True,
        "features_numeric_equivalent": g.get("feature_matrix_numeric_equivalent") is True,
        "prediction_bounded": bounded_nonnegative_float(g.get("prediction_max_abs_difference"), GENERATOR_PREDICTION_ATOL),
        "final_order_exact": g.get("exact_final_application_order_match") is True,
        "final_order_identity": g.get("final_application_order_sha256") == GENERATOR_FINAL_ORDER_SHA,
        "no_performance": g.get("performance_metric_computed") is False,
        "no_truth": g.get("truth_labels_used_by_generator_or_ranker") is False,
        "no_sonotaco": g.get("sonotaco_2013_2014_access") is False,
        "no_maarsy": g.get("maarsy_scientific_access") is False,
        "no_target": g.get("target_information_access") is False,
    }
    if not all(generator_checks.values()):
        return result(NOT_READY_GENERATOR, {"checks": generator_checks})

    r = p.get("ranker_equivalence", {})
    ranker_checks = {
        "model": r.get("model_sha256") == MODEL_SHA,
        "features": r.get("feature_matrix_sha256") == FEATURE_SHA,
        "predictions": r.get("prediction_sha256") == PREDICTION_SHA,
        "feature_count": r.get("feature_count") == 34,
        "lambda": r.get("diversity_lambda") == 0.8,
        "scale": r.get("diversity_scale") == 1.0,
        "no_truth": r.get("truth_labels_accepted") is False,
        "exact_gmn_equivalence": r.get("exact_gmn_equivalence") is True,
    }
    if not all(ranker_checks.values()):
        return result(NOT_READY_RANKER, {"checks": ranker_checks})

    c = p.get("comparators", {})
    comparator_checks = {
        "run": c.get("run_id") == COMPARATOR_RUN,
        "artifact": c.get("artifact_id") == COMPARATOR_ARTIFACT,
        "digest": c.get("artifact_digest") == COMPARATOR_DIGEST,
        "sugar": c.get("sugar_sha256") == SUGAR_SHA,
        "hdbscan": c.get("hdbscan_sha256") == HDBSCAN_SHA,
        "label_free_interfaces": c.get("label_free_interfaces") is True,
    }
    if not all(comparator_checks.values()):
        return result(NOT_READY_COMPARATORS, {"checks": comparator_checks})

    e = p.get("evaluator", {})
    evaluator_checks = {
        "source": e.get("source_sha256") == EVALUATOR_SHA,
        "run": e.get("run_id") == EVALUATOR_RUN,
        "artifact": e.get("artifact_id") == EVALUATOR_ARTIFACT,
        "digest": e.get("artifact_digest") == EVALUATOR_DIGEST,
        "synthetic_audit_pass": e.get("synthetic_audit_pass") is True,
    }
    if not all(evaluator_checks.values()):
        return result(NOT_READY_EVALUATOR, {"checks": evaluator_checks})

    x = p.get("external_gate", {})
    external_checks = {
        "merge": x.get("merge_commit") == EXTERNAL_GATE_MERGE,
        "scored_year": x.get("scored_year") == 2022,
        "support_year": x.get("support_year") == 2021,
        "support_truth_forbidden": x.get("support_truth_forbidden") is True,
        "pass_token": x.get("pass_token") == EXTERNAL_PASS,
        "source_audit_pass": x.get("source_audit_pass") is True,
    }
    if not all(external_checks.values()):
        return result(NOT_READY_EXTERNAL, {"checks": external_checks})

    return result(AUTHORIZED, {
        "final_candidate": "M0/#839",
        "test_years": [2013, 2014],
        "comparators": ["Sugar", "catalogue HDBSCAN"],
        "one_shot": True,
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    payload = json.loads(a.manifest.read_text())
    out = adjudicate(payload)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
