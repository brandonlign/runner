#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"
PRIMARY_SELECTED_METHOD = "density_synchronous_recurrent_eom_hdbscan_v1_pr1263"
UPSTREAM_EVALUATOR_BLOB = "c45e4739ea68639945b13de54f6e24dc9d870ba3"
RECURRENT_KERNEL_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
RECURRENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
PASS = "PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION"
FAIL = "FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value: Any, name: str) -> float:
    x = float(value)
    require(x == x and abs(x) != float("inf"), f"non-finite {name}")
    return x


def annual_gate(parent: dict[str, Any], recurrent: dict[str, Any]) -> dict[str, bool]:
    return {
        "recovered_at_50_not_lower": int(recurrent["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(recurrent["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": finite_number(recurrent["top100_dominant_precision"], "recurrent top100 precision") >= finite_number(parent["top100_dominant_precision"], "ordinary top100 precision"),
        "mrr_not_lower": finite_number(recurrent["mrr"], "recurrent mrr") >= finite_number(parent["mrr"], "ordinary mrr"),
        "fragmentation_not_higher": finite_number(recurrent["fragmentation_median_top500"], "recurrent fragmentation") <= finite_number(parent["fragmentation_median_top500"], "ordinary fragmentation"),
    }


def validate_metrics(m: dict[str, Any], label: str) -> None:
    required = {
        "eligible_labels",
        "qualified_matches",
        "recovered_at_25",
        "recovered_at_50",
        "recovered_at_100",
        "recovered_at_500",
        "top100_dominant_precision",
        "mrr",
        "fragmentation_median_top500",
    }
    require(required.issubset(m), f"missing {label} metrics: {sorted(required-set(m))}")
    for k in ("eligible_labels", "qualified_matches", "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500"):
        require(int(m[k]) >= 0, f"negative {label} metric {k}")
    for k in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
        finite_number(m[k], f"{label} {k}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    result = json.loads(args.primary_result.read_text(encoding="utf-8"))

    require(result["scientific_role"] == SCIENTIFIC_ROLE, "wrong upstream scientific role")
    require(result["phase"] == "POSTFREEZE_LABEL_EVALUATION", "upstream result not post-freeze label evaluation")
    require(result["selected_final_method"] == PRIMARY_SELECTED_METHOD, "upstream primary method changed")
    require(result["years"] == list(YEARS), "upstream AMOS years changed")
    require(result["blind_exclusion"] == list(BLIND), "upstream blind interval changed")
    require(result["pretruth_internal_integrity_verified_before_labels"] is True, "upstream pretruth integrity was not verified before labels")

    source_pins = result["source_pins"]
    require(source_pins["recurrent_eom_git_blob"] == RECURRENT_KERNEL_BLOB, "recurrent kernel pin changed")
    require(source_pins["recurrent_development_runner_git_blob"] == RECURRENT_RUNNER_BLOB, "recurrent runner pin changed")

    for flag in (
        "candidate_generation_recomputed_after_labels",
        "ranking_changed_after_labels",
        "final_method_switched_after_labels",
        "quality_filter_used",
        "survey_calibration_used",
        "amos_post_result_parameter_search",
        "replacement_external_panel_authorized",
        "sonotaco_access",
        "asfn_access",
        "efn_access",
        "target_information_access",
        "target_region_events_accessed",
        "maarsy_scientific_access",
        "dms_scientific_access",
        "orbittrace_target_access",
    ):
        require(result[flag] is False, f"upstream firewall flag violated: {flag}")

    mechanism = result["mechanism_active"]
    require(isinstance(mechanism, dict), "mechanism_active missing")
    recurrent_active = bool(mechanism["ordinary_vs_recurrent"])

    ordinary = result["ordinary_metrics"]
    recurrent = result["recurrent_metrics"]
    require(set(ordinary) == {"2023", "2024"} and set(recurrent) == {"2023", "2024"}, "annual metric keys changed")

    gates: dict[str, Any] = {}
    passed_count = 0
    for y in YEARS:
        oy = ordinary[str(y)]
        ry = recurrent[str(y)]
        validate_metrics(oy, f"ordinary {y}")
        validate_metrics(ry, f"recurrent {y}")
        require(int(oy["eligible_labels"]) == int(ry["eligible_labels"]), f"eligible-label universe differs in {y}")
        gy = annual_gate(oy, ry)
        gates[str(y)] = gy
        passed_count += sum(bool(v) for v in gy.values())

    strict_at_100 = any(int(recurrent[str(y)]["recovered_at_100"]) > int(ordinary[str(y)]["recovered_at_100"]) for y in YEARS)
    passed_count += int(strict_at_100) + int(recurrent_active)
    total_gates = 12
    external_pass = bool(
        recurrent_active
        and strict_at_100
        and all(all(bool(v) for v in gates[str(y)].values()) for y in YEARS)
    )
    verdict = PASS if external_pass else FAIL

    output = {
        "schema": "ORBITTRACE_RECURRENT_EOM_AMOS_SECONDARY_CHARACTERIZATION_V1_RESULT",
        "verdict": verdict,
        "scientific_role": "SECONDARY_CHARACTERIZATION_FROM_SINGLE_FROZEN_AMOS_ENDPOINT",
        "primary_result_sha256": sha(args.primary_result),
        "upstream_scientific_role": result["scientific_role"],
        "upstream_primary_verdict": result["verdict"],
        "upstream_selected_final_method": result["selected_final_method"],
        "upstream_evaluator_git_blob": UPSTREAM_EVALUATOR_BLOB,
        "recurrent_eom_git_blob": RECURRENT_KERNEL_BLOB,
        "recurrent_development_runner_git_blob": RECURRENT_RUNNER_BLOB,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "passed_gate_count": passed_count,
        "total_gate_count": total_gates,
        "annual_gates": gates,
        "strict_recovered_at_100_improvement_some_year": strict_at_100,
        "recurrent_mechanism_active_vs_ordinary": recurrent_active,
        "ordinary_metrics": ordinary,
        "recurrent_metrics": recurrent,
        "reporting_only": {
            "qualified_matches": {str(y): {"ordinary": int(ordinary[str(y)]["qualified_matches"]), "recurrent": int(recurrent[str(y)]["qualified_matches"])} for y in YEARS},
            "recovered_at_25": {str(y): {"ordinary": int(ordinary[str(y)]["recovered_at_25"]), "recurrent": int(recurrent[str(y)]["recovered_at_25"])} for y in YEARS},
            "recovered_at_500": {str(y): {"ordinary": int(ordinary[str(y)]["recovered_at_500"]), "recurrent": int(recurrent[str(y)]["recovered_at_500"])} for y in YEARS},
        },
        "accepts_geometry_or_labels_directly": False,
        "second_external_chance_created": False,
        "method_selection_changed": False,
        "primary_amos_endpoint_changed": False,
        "post_result_parameter_search": False,
        "replacement_external_survey_authorized": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_new_scientific_access": False,
        "asfn_efn_new_event_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "passed_gate_count": passed_count, "total_gate_count": total_gates, "strict_at_100": strict_at_100, "recurrent_active": recurrent_active, "annual_gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
