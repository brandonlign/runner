#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_recurrent_eom_hdbscan_v1.run_development import annual_gate, metrics

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
LABEL_HEADER = ["event_id", "shower_code"]


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_labels(path: Path, expected_ids: list[str], year: int) -> dict[str, str]:
    expected = set(map(str, expected_ids))
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        require(r.fieldnames == LABEL_HEADER, f"wrong AMOS label header for {year}")
        for row in r:
            eid = str(row["event_id"]).strip()
            label = str(row["shower_code"]).strip()
            require(eid and eid in expected and eid not in out, f"invalid/duplicate AMOS label ID for {year}: {eid!r}")
            require(label, f"blank shower_code for retained AMOS event {eid}; use explicit SPORADIC")
            out[eid] = label
    require(set(out) == expected, f"AMOS label map for {year} must cover every retained ID exactly")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth", type=Path, required=True)
    p.add_argument("--pretruth-sha256", type=str, required=True)
    p.add_argument("--labels-2023", type=Path, required=True)
    p.add_argument("--labels-2024", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    actual_pretruth_sha = sha(a.pretruth)
    require(actual_pretruth_sha == a.pretruth_sha256.strip().lower(), "pretruth payload hash changed before label evaluation")
    pre = json.loads(a.pretruth.read_text(encoding="utf-8"))
    require(pre["scientific_role"] == "PRISTINE_EXTERNAL_AMOS_2023_2024_VALIDATION_PRETRUTH", "wrong pretruth role")
    require(pre["years"] == [2023, 2024] and pre["blind_exclusion"] == [20.0, 55.0], "year/blind freeze changed")
    require(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "pretruth payload is truth-bearing")
    require(pre["amos_orbit_elements_accessed"] is False, "pretruth payload opened orbit elements")
    for k in ("target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "orbittrace_target_access"):
        require(pre[k] is False, f"firewall flag violated in pretruth: {k}")

    ids_by_year = {y: list(map(str, pre["event_ids_by_year"][str(y)])) for y in YEARS}
    labels_by_year = {
        2023: load_labels(a.labels_2023, ids_by_year[2023], 2023),
        2024: load_labels(a.labels_2024, ids_by_year[2024], 2024),
    }
    hidden: dict[str, str] = {}
    for y in YEARS:
        require(set(hidden).isdisjoint(labels_by_year[y]), "event ID reused across AMOS label years")
        hidden.update(labels_by_year[y])

    parent_candidates = list(pre["parent_candidates"])
    successor_candidates = list(pre["successor_candidates"])
    parent_metrics = {str(y): metrics(parent_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    successor_metrics = {str(y): metrics(successor_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    annual_gates = {str(y): annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    mechanism_active = bool(pre["mechanism_active"])
    passed = bool(strict_100 and mechanism_active and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION" if passed else "FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION"

    result: dict[str, Any] = {
        "verdict": verdict,
        "scientific_role": "PRISTINE_EXTERNAL_AMOS_2023_2024_VALIDATION_ONLY",
        "pretruth_sha256": actual_pretruth_sha,
        "years": [2023, 2024],
        "events_by_year": dict(pre["events_by_year"]),
        "label_file_sha256": {"2023": sha(a.labels_2023), "2024": sha(a.labels_2024)},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "frozen_hdbscan": dict(pre["frozen_hdbscan"]),
        "source_pins": dict(pre["source_pins"]),
        "blind_exclusion": list(BLIND),
        "candidate_generation_recomputed_after_labels": False,
        "ranking_changed_after_labels": False,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "amos_post_result_parameter_search": False,
        "sonotaco_used_for_tuning": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = a.output / "RECURRENT_EOM_AMOS_2023_2024_EXTERNAL_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "mechanism_active": mechanism_active, "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics}, "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics}}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
