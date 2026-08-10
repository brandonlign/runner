#!/usr/bin/env python3
"""Mechanical final GMN M0/M2 adjudicator. No scientific computation or data transport."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

FINAL_846_SOURCE = "e5733a57488b7b8dff26c15ff76f679810efac9c"
FINAL_846_RUN = 31344902186
ORDER_SHA = "ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449"
M0 = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "qualified_matches": 256,
    "mrr": 0.019037817654898162,
    "top100_dominant_precision": 0.7645689180574315,
    "best_membership_macro_f1_all_eligible": 0.17953659309876194,
}
PASS_846 = "PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY"
PASS_850 = "PASS_EVENT_LEVEL_P12_FIXED_GROUP_STRESS"
PASS_852 = "PASS_M2_FULL_URC_PROMOTION_GATE"
FAIL_846 = "FAIL_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY"
FAIL_850 = "FAIL_EVENT_LEVEL_P12_FIXED_GROUP_STRESS"
FAIL_852 = "FAIL_M2_FULL_URC_PROMOTION_GATE"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_optional(path: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    if path is None:
        return None, None
    require(path.is_file(), f"missing input: {path}")
    return json.loads(path.read_text()), sha(path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--m2-feasibility", type=Path)
    p.add_argument("--m2-stress", type=Path)
    p.add_argument("--m2-integration", type=Path)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def selected_policy(feas: dict[str, Any]) -> dict[str, Any]:
    p = feas.get("selected", {}).get("policy")
    require(isinstance(p, dict), "#846 PASS missing selected policy")
    require(p.get("model") in {"ET_d4_l10","ET_d6_l10","ET_d8_l10","ET_d6_l30","ET_d8_l30","HGB_l20","HGB_l50"}, "unexpected #846 model")
    require(float(p.get("threshold")) in {0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90}, "unexpected #846 threshold")
    cap = p.get("cap_ratio")
    require(str(cap) == "Infinity" or float(cap) in {0.5,1.0,2.0,4.0}, "unexpected #846 cap")
    require(int(feas.get("robustness", {}).get("passing_grid_variants", 0)) >= 3, "#846 PASS lacks >=3 passing variants")
    return {"model": p["model"], "threshold": float(p["threshold"]), "cap_ratio": cap}


def decide(feas: dict[str, Any] | None, stress: dict[str, Any] | None, integ: dict[str, Any] | None) -> tuple[str, str, dict[str, Any] | None]:
    if feas is None:
        return "NOT_READY_846", "NONE", None
    v846 = str(feas.get("verdict"))
    require(v846 in {PASS_846, FAIL_846}, f"unexpected #846 verdict {v846}")
    if v846 == FAIL_846:
        require(stress is None and integ is None, "downstream M2 artifact present after #846 FAIL")
        return "FINAL_GMN_METHOD_M0", "M0", None
    policy = selected_policy(feas)
    if stress is None:
        require(integ is None, "#852 present before #850")
        return "NOT_READY_850", "NONE", policy
    v850 = str(stress.get("verdict"))
    require(v850 in {PASS_850, FAIL_850}, f"unexpected #850 verdict {v850}")
    if v850 == FAIL_850:
        require(integ is None, "#852 present after #850 FAIL")
        return "FINAL_GMN_METHOD_M0", "M0", policy
    if integ is None:
        return "NOT_READY_852", "NONE", policy
    v852 = str(integ.get("verdict"))
    require(v852 in {PASS_852, FAIL_852}, f"unexpected #852 verdict {v852}")
    if v852 == FAIL_852:
        return "FINAL_GMN_METHOD_M0", "M0", policy
    return "FINAL_GMN_METHOD_M2", "M2", policy


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    feas, h846 = load_optional(a.m2_feasibility)
    stress, h850 = load_optional(a.m2_stress)
    integ, h852 = load_optional(a.m2_integration)
    state, chosen, policy = decide(feas, stress, integ)
    final = chosen in {"M0", "M2"}
    out = {
        "state": state,
        "chosen_membership": chosen,
        "final": final,
        "immutable_discovery": {
            "candidate_universe": "hard_v8_plus_p19_soft_plus_p20_soft",
            "development_family_count": 4504,
            "ranking": "#839 strict-group ExtraTrees quality regression plus diversity",
            "order_sha256": ORDER_SHA,
        },
        "m0_reference": M0,
        "m2_policy": policy,
        "inputs": {
            "final_846_source_commit": FINAL_846_SOURCE,
            "final_846_run_id": FINAL_846_RUN,
            "m2_feasibility_sha256": h846,
            "m2_stress_sha256": h850,
            "m2_integration_sha256": h852,
        },
        "m1_permanent_no_go": True,
        "gmn_methodology_development_closed": final,
        "sonotaco_2013_2014_scientific_access_authorized": False,
        "maarsy_scientific_access_authorized": False,
        "target_access_authorized": False,
        "next_required_step": (
            "freeze_one_deployable_selected_method_before_sonotaco_access" if final
            else {"NOT_READY_846":"await_final_corrected_846","NOT_READY_850":"execute_exact_prefrozen_850","NOT_READY_852":"execute_exact_prefrozen_852"}[state]
        ),
    }
    (a.output / "final_gmn_adjudication_v1.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"state": state, "chosen_membership": chosen, "final": final}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
