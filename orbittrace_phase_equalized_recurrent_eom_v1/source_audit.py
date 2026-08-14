#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS = "PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_SOURCE_AUDIT"
FAIL = "FAIL_PHASE_EQUALIZED_RECURRENT_EOM_V1_SOURCE_AUDIT"


def line_of(lines: list[str], needle: str) -> int:
    hits = [i + 1 for i, line in enumerate(lines) if needle in line]
    if len(hits) != 1:
        raise RuntimeError(f"expected exactly one source hit for {needle!r}, got {hits}")
    return hits[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runner", type=Path, required=True)
    p.add_argument("--transform", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    source = a.runner.read_text()
    lines = source.splitlines()
    transform = a.transform.read_text()

    transform_line = line_of(lines, "eq_events, phase = equalized_events(events)")
    fit_line = line_of(lines, ").fit(eq_geo6)")
    candidates_line = line_of(lines, "successor_candidates = parent.candidates_from_labels")
    prelabel_freeze_line = line_of(lines, "prelabel_path.write_text")
    parent_result_read_line = line_of(lines, "parent_result = json.loads(a.parent_result_json.read_text())")
    parent_prelabel_read_line = line_of(lines, "parent_prelabel = json.loads(a.parent_prelabel_json.read_text())")
    truth_unseal_line = line_of(lines, "hidden = hidden_sealed")
    result_write_line = line_of(lines, "result_path.write_text")

    checks = {
        "transform_before_fit": transform_line < fit_line,
        "fit_before_candidates": fit_line < candidates_line,
        "candidates_before_prelabel_freeze": candidates_line < prelabel_freeze_line,
        "prelabel_before_parent_result_read": prelabel_freeze_line < parent_result_read_line,
        "prelabel_before_parent_prelabel_read": prelabel_freeze_line < parent_prelabel_read_line,
        "prelabel_before_truth_unseal": prelabel_freeze_line < truth_unseal_line,
        "truth_before_result_write": truth_unseal_line < result_write_line,
        "no_network_in_runner": all(x not in source for x in ("requests.", "urllib", "urlopen", "curl ", "http://", "https://")),
        "no_network_in_transform": all(x not in transform for x in ("requests.", "urllib", "urlopen", "curl ", "http://", "https://")),
        "transform_has_no_year_access": '["year"]' not in transform and "['year']" not in transform,
        "transform_has_no_radiant_speed_access": all(x not in transform for x in ('["lon"]', '["lat"]', '["vg"]', "['lon']", "['lat']", "['vg']")),
        "transform_has_no_label_surface": all(x not in transform.lower() for x in ("shower", "label", "truth", "sonotaco", "asfn", "efn", "amos", "maarsy", "dms")),
        "runner_has_no_external_data_read": all(x not in source for x in ("ASFN_", "EFN_", "AMOS_", "SONOTACO_", "MAARSY_", "DMS_")),
        "no_postfit_transform_search": all(x not in source for x in ("bandwidth", "histogram", "spline", "blend_weight", "alpha_grid", "parameter_grid", "GridSearch")),
    }
    passed = all(checks.values())
    result = {
        "verdict": PASS if passed else FAIL,
        "checks": checks,
        "transform_line": transform_line,
        "fit_line": fit_line,
        "candidates_line": candidates_line,
        "prelabel_freeze_line": prelabel_freeze_line,
        "parent_result_read_line": parent_result_read_line,
        "parent_prelabel_read_line": parent_prelabel_read_line,
        "truth_unseal_line": truth_unseal_line,
        "result_write_line": result_write_line,
        "gmn_accessed": False,
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "asfn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "PHASE_EQUALIZED_RECURRENT_EOM_V1_SOURCE_AUDIT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
