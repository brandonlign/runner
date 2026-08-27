#!/usr/bin/env python3
"""Mechanical adjudicator for the frozen OrbitTrace MAARSY-2022 external gate.

This module does not read detector data, shower truth, or target information. It consumes
only a precomputed metric summary produced by the separately source-frozen evaluator.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

PASS = "PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION"
FAIL = "FAIL_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION"
POWER = "POWER_INCONCLUSIVE_FINAL_MAARSY_2022"
INCOMPATIBLE = "EXTERNAL_ARCHITECTURE_INCOMPATIBLE_FINAL_MAARSY_2022"
INVALID = "INVALID_FINAL_MAARSY_2022_INTEGRITY"

REQUIRED_INTEGRITY = (
    "source_identity",
    "generator_equivalence",
    "ranker_equivalence",
    "shared_row_universe",
    "pretruth_output_freeze",
    "no_2021_truth_access",
    "no_target_access",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def integer(x: Any, name: str) -> int:
    require(isinstance(x, int) and not isinstance(x, bool), f"{name} must be int")
    require(x >= 0, f"{name} must be >=0")
    return int(x)


def finite(x: Any, name: str) -> float:
    y = float(x)
    require(math.isfinite(y), f"{name} must be finite")
    return y


def validate_method(m: dict[str, Any], eligible: int, sparse_eligible: int, name: str) -> dict[str, Any]:
    out = {
        "r25": integer(m.get("r25"), f"{name}.r25"),
        "r50": integer(m.get("r50"), f"{name}.r50"),
        "r100": integer(m.get("r100"), f"{name}.r100"),
        "sparse_r100": integer(m.get("sparse_r100"), f"{name}.sparse_r100"),
        "macro_f1_B": finite(m.get("macro_f1_B"), f"{name}.macro_f1_B"),
        "qualified_B": integer(m.get("qualified_B"), f"{name}.qualified_B"),
    }
    require(0.0 <= out["macro_f1_B"] <= 1.0, f"{name}.macro_f1_B outside [0,1]")
    require(out["r25"] <= out["r50"] <= out["r100"] <= out["qualified_B"], f"{name} recovery counts not monotone")
    require(out["qualified_B"] <= eligible, f"{name}.qualified_B exceeds eligible showers")
    require(out["sparse_r100"] <= sparse_eligible, f"{name}.sparse_r100 exceeds sparse eligible showers")
    require(out["sparse_r100"] <= out["r100"], f"{name}.sparse_r100 exceeds r100")
    return out


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    integrity = payload.get("integrity")
    require(isinstance(integrity, dict), "missing integrity object")
    integrity_failures = [k for k in REQUIRED_INTEGRITY if integrity.get(k) is not True]
    if integrity_failures:
        return {
            "verdict": INVALID,
            "integrity_failures": integrity_failures,
            "authorized_target_access": False,
        }

    if payload.get("architecture_compatible") is not True:
        return {
            "verdict": INCOMPATIBLE,
            "integrity_failures": [],
            "authorized_target_access": False,
        }

    power = payload.get("power")
    require(isinstance(power, dict), "missing power object")
    B = integer(power.get("candidate_budget_B"), "power.candidate_budget_B")
    eligible = integer(power.get("eligible_showers_2022"), "power.eligible_showers_2022")
    sparse_eligible = integer(power.get("eligible_sparse_4_24_2022"), "power.eligible_sparse_4_24_2022")

    methods = payload.get("methods")
    require(isinstance(methods, dict), "missing methods object")
    require(isinstance(methods.get("hard_v8"), dict), "missing methods.hard_v8")
    require(isinstance(methods.get("urc_839"), dict), "missing methods.urc_839")
    hard = validate_method(methods["hard_v8"], eligible, sparse_eligible, "hard_v8")
    urc = validate_method(methods["urc_839"], eligible, sparse_eligible, "urc_839")

    power_checks = {
        "candidate_budget_B_ge_100": B >= 100,
        "eligible_showers_ge_30": eligible >= 30,
        "eligible_sparse_ge_10": sparse_eligible >= 10,
        "hard_v8_r100_ge_10": hard["r100"] >= 10,
    }
    if not all(power_checks.values()):
        return {
            "verdict": POWER,
            "power_checks": power_checks,
            "authorized_target_access": False,
        }

    bootstrap = payload.get("bootstrap")
    require(isinstance(bootstrap, dict), "missing bootstrap object")
    require(integer(bootstrap.get("replicates"), "bootstrap.replicates") == 10000, "bootstrap.replicates must equal 10000")
    require(integer(bootstrap.get("seed"), "bootstrap.seed") == 20260809, "bootstrap.seed must equal 20260809")
    lower = finite(bootstrap.get("r100_recovery_rate_advantage_lower_95"), "bootstrap.r100_recovery_rate_advantage_lower_95")

    required_gain = max(2, int(math.ceil(0.10 * hard["r100"])))
    gates = {
        "r25_nonregression": urc["r25"] >= hard["r25"],
        "r50_nonregression": urc["r50"] >= hard["r50"],
        "r100_meaningful_gain": urc["r100"] >= hard["r100"] + required_gain,
        "sparse_r100_gain": urc["sparse_r100"] >= hard["sparse_r100"] + 1,
        "macro_f1_nonregression": urc["macro_f1_B"] >= hard["macro_f1_B"] - 0.02,
        "qualified_catalogue_nonregression": urc["qualified_B"] >= hard["qualified_B"],
        "bootstrap_positive_lower_bound": lower > 0.0,
    }
    verdict = PASS if all(gates.values()) else FAIL
    return {
        "verdict": verdict,
        "required_r100_gain": required_gain,
        "power_checks": power_checks,
        "scientific_gates": gates,
        "authorized_target_access": verdict == PASS,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    payload = json.loads(a.metrics.read_text())
    result = adjudicate(payload)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
