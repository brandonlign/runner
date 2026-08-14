#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS = "PASS_ECDF_RECURRENT_RANK_HDBSCAN_V1_SOURCE_AUDIT"
FAIL = "FAIL_ECDF_RECURRENT_RANK_HDBSCAN_V1_SOURCE_AUDIT"


def unique_line(lines: list[str], needle: str) -> int:
    hits = [i + 1 for i, line in enumerate(lines) if needle in line]
    if len(hits) != 1:
        raise RuntimeError(f"expected one line containing {needle!r}, found {hits}")
    return hits[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", type=Path, required=True)
    ap.add_argument("--ranker", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    runner_text = a.runner.read_text()
    ranker_text = a.ranker.read_text()
    lines = runner_text.splitlines()

    rank_line = unique_line(lines, "successor_candidates = rank_candidates(parent_candidates, annual)")
    prelabel_write_line = unique_line(lines, "prelabel_path.write_text(")
    parent_result_read_line = unique_line(lines, "parent_result = json.loads(a.parent_result_json.read_text())")
    truth_unseal_line = unique_line(lines, "hidden = hidden_sealed")
    successor_metric_line = unique_line(lines, "successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}")

    ordering_ok = rank_line < prelabel_write_line < parent_result_read_line < truth_unseal_line < successor_metric_line

    ranker_forbidden = (
        "hidden_sealed", "parent_result", "eligible_labels", "shower", "SPORADIC",
        "sonotaco", "asfn", "amos", "maarsy", "dms", "target_coordinate",
        "requests", "urllib", "curl", "wget",
    )
    runner_forbidden_network = (
        "requests.", "urllib", "urlopen", "curl ", "wget ", "fireballs.ndc.nasa.gov",
        "astro.sk/iaumdcDB", "OrbitTrace-April", "247.17", "-14.34", "37.62",
    )
    ranker_truth_surface_absent = all(x.lower() not in ranker_text.lower() for x in ranker_forbidden)
    runner_external_network_surface_absent = all(x.lower() not in runner_text.lower() for x in runner_forbidden_network)

    checks = {
        "rank_before_prelabel_write": rank_line < prelabel_write_line,
        "prelabel_before_truth_informed_parent_result_read": prelabel_write_line < parent_result_read_line,
        "prelabel_before_truth_unseal": prelabel_write_line < truth_unseal_line,
        "truth_unseal_before_successor_metrics_only": truth_unseal_line < successor_metric_line,
        "complete_ordering_boundary": ordering_ok,
        "ranker_truth_and_external_surface_absent": ranker_truth_surface_absent,
        "runner_external_network_and_target_surface_absent": runner_external_network_surface_absent,
        "explicit_asfn_spent_flag_false": '"asfn_access": False' in runner_text,
        "explicit_target_flags_false": '"target_information_access": False' in runner_text and '"target_region_events_accessed": False' in runner_text,
        "candidate_identity_guard_present": "canonical_membership(successor_candidates) == canonical_membership(parent_candidates)" in runner_text,
        "parent_metrics_exact_reproduction_guard_present": "promoted recurrent-EOM metrics failed exact reproduction" in runner_text,
    }
    passed = all(checks.values())
    out = {
        "verdict": PASS if passed else FAIL,
        "checks": checks,
        "rank_line": rank_line,
        "prelabel_write_line": prelabel_write_line,
        "parent_result_read_line": parent_result_read_line,
        "truth_unseal_line": truth_unseal_line,
        "successor_metric_line": successor_metric_line,
        "network_access": False,
        "gmn_accessed": False,
        "truth_accessed": False,
        "sonotaco_accessed": False,
        "asfn_accessed": False,
        "amos_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "ECDF_RECURRENT_RANK_HDBSCAN_V1_SOURCE_AUDIT.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
