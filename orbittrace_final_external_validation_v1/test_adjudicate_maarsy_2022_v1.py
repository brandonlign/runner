#!/usr/bin/env python3
from copy import deepcopy

from adjudicate_maarsy_2022_v1 import (
    FAIL,
    INCOMPATIBLE,
    INVALID,
    PASS,
    POWER,
    adjudicate,
)


def base_payload():
    return {
        "integrity": {
            "source_identity": True,
            "generator_equivalence": True,
            "ranker_equivalence": True,
            "shared_row_universe": True,
            "pretruth_output_freeze": True,
            "no_2021_truth_access": True,
            "no_target_access": True,
        },
        "architecture_compatible": True,
        "power": {
            "candidate_budget_B": 180,
            "eligible_showers_2022": 60,
            "eligible_sparse_4_24_2022": 20,
        },
        "methods": {
            "hard_v8": {
                "r25": 10,
                "r50": 14,
                "r100": 20,
                "sparse_r100": 6,
                "macro_f1_B": 0.32,
                "qualified_B": 26,
            },
            "urc_839": {
                "r25": 10,
                "r50": 15,
                "r100": 23,
                "sparse_r100": 7,
                "macro_f1_B": 0.31,
                "qualified_B": 28,
            },
        },
        "bootstrap": {
            "replicates": 10000,
            "seed": 20260809,
            "r100_recovery_rate_advantage_lower_95": 0.003,
        },
    }


def test_pass():
    r = adjudicate(base_payload())
    assert r["verdict"] == PASS
    assert r["required_r100_gain"] == 2
    assert r["authorized_target_access"] is True


def test_fail_scientific_gate():
    p = base_payload()
    p["methods"]["urc_839"]["r100"] = 21
    r = adjudicate(p)
    assert r["verdict"] == FAIL
    assert r["scientific_gates"]["r100_meaningful_gain"] is False
    assert r["authorized_target_access"] is False


def test_power_inconclusive():
    p = base_payload()
    p["power"]["eligible_sparse_4_24_2022"] = 9
    p["methods"]["hard_v8"]["sparse_r100"] = 5
    p["methods"]["urc_839"]["sparse_r100"] = 6
    r = adjudicate(p)
    assert r["verdict"] == POWER
    assert r["power_checks"]["eligible_sparse_ge_10"] is False


def test_integrity_precedes_science():
    p = base_payload()
    p["integrity"]["no_2021_truth_access"] = False
    p["methods"]["urc_839"]["r100"] = 60
    r = adjudicate(p)
    assert r["verdict"] == INVALID
    assert "no_2021_truth_access" in r["integrity_failures"]
    assert r["authorized_target_access"] is False


def test_architecture_incompatible():
    p = base_payload()
    p["architecture_compatible"] = False
    r = adjudicate(p)
    assert r["verdict"] == INCOMPATIBLE
    assert r["authorized_target_access"] is False


def test_bootstrap_must_support_gain():
    p = base_payload()
    p["bootstrap"]["r100_recovery_rate_advantage_lower_95"] = 0.0
    r = adjudicate(p)
    assert r["verdict"] == FAIL
    assert r["scientific_gates"]["bootstrap_positive_lower_bound"] is False


if __name__ == "__main__":
    test_pass()
    test_fail_scientific_gate()
    test_power_inconclusive()
    test_integrity_precedes_science()
    test_architecture_incompatible()
    test_bootstrap_must_support_gain()
    print("PASS_FINAL_MAARSY_2022_ADJUDICATOR_SYNTHETIC_TESTS")
