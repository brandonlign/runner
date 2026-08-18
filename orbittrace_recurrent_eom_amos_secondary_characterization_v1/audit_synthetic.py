#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADJ = HERE / "adjudicate_primary_result.py"
PASS_TOKEN = "PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION"
FAIL_TOKEN = "FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION"


def metric(*, q: int, r25: int, r50: int, r100: int, r500: int, p: float, mrr: float, frag: float) -> dict:
    return {
        "eligible_labels": 100,
        "qualified_matches": q,
        "recovered_at_25": r25,
        "recovered_at_50": r50,
        "recovered_at_100": r100,
        "recovered_at_500": r500,
        "top100_dominant_precision": p,
        "mrr": mrr,
        "fragmentation_median_top500": frag,
        "first_rank_by_label": {},
    }


def base_result() -> dict:
    ordinary = {
        "2023": metric(q=70, r25=20, r50=40, r100=65, r500=70, p=0.70, mrr=0.020, frag=1.0),
        "2024": metric(q=72, r25=21, r50=41, r100=66, r500=72, p=0.71, mrr=0.021, frag=1.0),
    }
    recurrent = {
        "2023": metric(q=71, r25=20, r50=41, r100=66, r500=71, p=0.71, mrr=0.021, frag=1.0),
        "2024": metric(q=72, r25=22, r50=41, r100=66, r500=72, p=0.72, mrr=0.022, frag=1.0),
    }
    return {
        "verdict": "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
        "scientific_role": "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY",
        "phase": "POSTFREEZE_LABEL_EVALUATION",
        "selected_final_method": "density_synchronous_recurrent_eom_hdbscan_v1_pr1263",
        "years": [2023, 2024],
        "blind_exclusion": [20.0, 55.0],
        "pretruth_internal_integrity_verified_before_labels": True,
        "source_pins": {
            "recurrent_eom_git_blob": "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
            "recurrent_development_runner_git_blob": "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c",
        },
        "candidate_generation_recomputed_after_labels": False,
        "ranking_changed_after_labels": False,
        "final_method_switched_after_labels": False,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "amos_post_result_parameter_search": False,
        "replacement_external_panel_authorized": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
        "mechanism_active": {"ordinary_vs_recurrent": True},
        "ordinary_metrics": ordinary,
        "recurrent_metrics": recurrent,
    }


def run_case(payload: dict, expected: str, expected_gate_count: int) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inp = root / "primary.json"
        out = root / "secondary.json"
        inp.write_text(json.dumps(payload, sort_keys=True) + "\n")
        subprocess.run([sys.executable, str(ADJ), "--primary-result", str(inp), "--output", str(out)], check=True)
        got = json.loads(out.read_text())
        assert got["verdict"] == expected, (got["verdict"], expected)
        assert got["passed_gate_count"] == expected_gate_count, got["passed_gate_count"]
        assert got["total_gate_count"] == 12
        assert got["accepts_geometry_or_labels_directly"] is False
        assert got["second_external_chance_created"] is False
        assert got["method_selection_changed"] is False
        assert got["primary_amos_endpoint_changed"] is False


def main() -> int:
    # Canonical PASS: all 10 annual no-regression booleans plus strict @100
    # improvement and active mechanism.
    good = base_result()
    run_case(good, PASS_TOKEN, 12)

    # Exact-tie annual metrics are not enough: strict @100 is mandatory.
    no_strict = base_result()
    no_strict["recurrent_metrics"]["2023"]["recovered_at_100"] = no_strict["ordinary_metrics"]["2023"]["recovered_at_100"]
    run_case(no_strict, FAIL_TOKEN, 11)

    # A tiny precision regression in either year is binding, mirroring the
    # no-regression philosophy used throughout OrbitTrace.
    precision_fail = base_result()
    precision_fail["recurrent_metrics"]["2024"]["top100_dominant_precision"] = 0.709999
    run_case(precision_fail, FAIL_TOKEN, 11)

    # Mechanism inactivity cannot be called generalization even if the metric
    # table would otherwise pass.
    inactive = base_result()
    inactive["mechanism_active"]["ordinary_vs_recurrent"] = False
    run_case(inactive, FAIL_TOKEN, 11)

    print("PASS_RECURRENT_EOM_AMOS_SECONDARY_SYNTHETIC_AUDIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
