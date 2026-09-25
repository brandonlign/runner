#!/usr/bin/env python3
from authorize_final_test_v1 import (
    AUTHORIZED,
    INVALID_FIREWALL,
    NOT_READY_COMPARATORS,
    NOT_READY_EVALUATOR,
    NOT_READY_EXTERNAL,
    NOT_READY_GENERATOR,
    NOT_READY_RANKER,
    adjudicate,
)


def valid_manifest():
    return {
        "firewall": {
            "target_information_access": False,
            "target_region_access": False,
            "sonotaco_scientific_access_already_occurred": False,
            "maarsy_scientific_access_already_occurred": False,
        },
        "generator_equivalence": {
            "verdict": "PASS_URC_PAIR_PORTABLE_GENERATOR_GMN_OPERATIONAL_EQUIVALENCE",
            "pr_number": 862,
            "source_commit": "1" * 40,
            "run_id": 1,
            "artifact_id": 1,
            "artifact_digest": "sha256:" + "2" * 64,
            "hard_count": 226,
            "p19_soft_count": 1075,
            "p20_soft_count": 3203,
            "union_count": 4504,
            "exact_hard_order_match": True,
            "exact_hard_family_match": True,
            "exact_p19_discrete_match": True,
            "p19_numeric_equivalent": True,
            "p19_numeric_atol": 1e-12,
            "p19_numeric_rtol": 1e-12,
            "p19_numeric_max_abs_difference": 5e-15,
            "exact_p20_family_match": True,
            "exact_p20_isolated_quartet_match": True,
            "feature_matrix_numeric_equivalent": True,
            "prediction_max_abs_difference": 0.0,
            "exact_final_application_order_match": True,
            "final_application_order_sha256": "9063270f131b81bb0032026b2742b985ab0f8d5655abb46a1d405d30501b6d7d",
            "performance_metric_computed": False,
            "truth_labels_used_by_generator_or_ranker": False,
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "ranker_equivalence": {
            "model_sha256": "ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909",
            "feature_matrix_sha256": "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1",
            "prediction_sha256": "493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac",
            "feature_count": 34,
            "diversity_lambda": 0.8,
            "diversity_scale": 1.0,
            "truth_labels_accepted": False,
            "exact_gmn_equivalence": True,
        },
        "comparators": {
            "run_id": 31346168826,
            "artifact_id": 9047392743,
            "artifact_digest": "sha256:8acb1986561d44194e2b7ebf5eb725a115eff5ba10b9b5d30a74f63a71a93fbc",
            "sugar_sha256": "5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb",
            "hdbscan_sha256": "a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2",
            "label_free_interfaces": True,
        },
        "evaluator": {
            "source_sha256": "cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c",
            "run_id": 31344796531,
            "artifact_id": 9046953388,
            "artifact_digest": "sha256:315f01965b1fec3820f32ab56cb57d96f7401373e3d2d127c78d7da35808210f",
            "synthetic_audit_pass": True,
        },
        "external_gate": {
            "merge_commit": "45428174b36b8a5207951bc2c046ced3aa2e9781",
            "scored_year": 2022,
            "support_year": 2021,
            "support_truth_forbidden": True,
            "pass_token": "PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION",
            "source_audit_pass": True,
        },
    }


def test_authorized_shape_only():
    out = adjudicate(valid_manifest())
    assert out["state"] == AUTHORIZED
    assert out["sonotaco_2013_2014_scientific_access_authorized"] is True
    assert out["target_access_authorized"] is False


def test_generator_fail_closed():
    p = valid_manifest(); p["generator_equivalence"]["verdict"] = "FAIL"
    assert adjudicate(p)["state"] == NOT_READY_GENERATOR


def test_generator_numeric_ceiling_fail_closed():
    p = valid_manifest(); p["generator_equivalence"]["p19_numeric_max_abs_difference"] = 1.0001e-12
    assert adjudicate(p)["state"] == NOT_READY_GENERATOR


def test_generator_tolerance_drift_fail_closed():
    p = valid_manifest(); p["generator_equivalence"]["p19_numeric_atol"] = 1e-9
    assert adjudicate(p)["state"] == NOT_READY_GENERATOR


def test_generator_order_drift_fail_closed():
    p = valid_manifest(); p["generator_equivalence"]["final_application_order_sha256"] = "0" * 64
    assert adjudicate(p)["state"] == NOT_READY_GENERATOR


def test_ranker_fail_closed():
    p = valid_manifest(); p["ranker_equivalence"]["feature_count"] = 33
    assert adjudicate(p)["state"] == NOT_READY_RANKER


def test_comparator_fail_closed():
    p = valid_manifest(); p["comparators"]["artifact_id"] += 1
    assert adjudicate(p)["state"] == NOT_READY_COMPARATORS


def test_evaluator_fail_closed():
    p = valid_manifest(); p["evaluator"]["synthetic_audit_pass"] = False
    assert adjudicate(p)["state"] == NOT_READY_EVALUATOR


def test_external_gate_fail_closed():
    p = valid_manifest(); p["external_gate"]["scored_year"] = 2021
    assert adjudicate(p)["state"] == NOT_READY_EXTERNAL


def test_firewall_precedes_everything():
    p = valid_manifest(); p["firewall"]["target_information_access"] = True
    out = adjudicate(p)
    assert out["state"] == INVALID_FIREWALL
    assert out["sonotaco_2013_2014_scientific_access_authorized"] is False
    assert out["target_access_authorized"] is False


if __name__ == "__main__":
    test_authorized_shape_only()
    test_generator_fail_closed()
    test_generator_numeric_ceiling_fail_closed()
    test_generator_tolerance_drift_fail_closed()
    test_generator_order_drift_fail_closed()
    test_ranker_fail_closed()
    test_comparator_fail_closed()
    test_evaluator_fail_closed()
    test_external_gate_fail_closed()
    test_firewall_precedes_everything()
    print("PASS_FINAL_SONOTACO_AUTHORIZATION_SYNTHETIC_TESTS")
