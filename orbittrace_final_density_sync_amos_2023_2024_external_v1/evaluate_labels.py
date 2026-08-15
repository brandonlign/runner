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
LABEL_HEADER = ["event_id", "shower_association"]
SELECTED_FINAL_METHOD = "density_synchronous_recurrent_eom_hdbscan_v1_pr1263"
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"
PRIMARY_PASS = "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
PRIMARY_FAIL = "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
INCREMENT_PASS = "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS"
INCREMENT_NO = "NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS"


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
            label = str(row["shower_association"]).strip()
            require(eid and eid in expected and eid not in out, f"invalid/duplicate AMOS label ID for {year}: {eid!r}")
            require(label, f"blank shower association for retained AMOS event {eid}; use explicit SPORADIC")
            out[eid] = label
    require(set(out) == expected, f"AMOS label map for {year} must cover every retained ID exactly")
    return out


def public_metrics(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


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
    require(pre["scientific_role"] == SCIENTIFIC_ROLE and pre["phase"] == "PRETRUTH_FROZEN", "wrong pretruth role/phase")
    require(pre["selected_final_method"] == SELECTED_FINAL_METHOD, "selected final method changed")
    require(pre["years"] == [2023, 2024] and pre["blind_exclusion"] == [20.0, 55.0], "year/blind freeze changed")
    require(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "pretruth payload is truth-bearing")
    require(pre["amos_orbit_elements_accessed"] is False, "pretruth payload opened orbit elements")
    for k in ("sonotaco_access", "asfn_access", "efn_access", "target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "orbittrace_target_access", "amos_post_result_parameter_search"):
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

    ordinary_candidates = list(pre["ordinary_candidates"])
    recurrent_candidates = list(pre["recurrent_candidates"])
    sync_candidates = list(pre["density_sync_candidates"])
    require(ordinary_candidates and recurrent_candidates and sync_candidates, "pretruth candidate payload is empty")

    ordinary_metrics = {str(y): metrics(ordinary_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    recurrent_metrics = {str(y): metrics(recurrent_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    sync_metrics = {str(y): metrics(sync_candidates, hidden, set(ids_by_year[y])) for y in YEARS}

    ordinary_gates = {str(y): annual_gate(ordinary_metrics[str(y)], sync_metrics[str(y)]) for y in YEARS}
    recurrent_gates = {str(y): annual_gate(recurrent_metrics[str(y)], sync_metrics[str(y)]) for y in YEARS}
    strict_vs_ordinary_100 = any(int(sync_metrics[str(y)]["recovered_at_100"]) > int(ordinary_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    strict_vs_recurrent_100 = any(int(sync_metrics[str(y)]["recovered_at_100"]) > int(recurrent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    active_vs_ordinary = bool(pre["mechanism_active"]["ordinary_vs_density_sync"])
    active_vs_recurrent = bool(pre["mechanism_active"]["recurrent_vs_density_sync"])

    primary_pass = bool(
        strict_vs_ordinary_100
        and active_vs_ordinary
        and all(all(g.values()) for g in ordinary_gates.values())
        and all(all(g.values()) for g in recurrent_gates.values())
    )
    primary_verdict = PRIMARY_PASS if primary_pass else PRIMARY_FAIL

    incremental_pass = bool(
        strict_vs_recurrent_100
        and active_vs_recurrent
        and all(all(g.values()) for g in recurrent_gates.values())
    )
    incremental_verdict = INCREMENT_PASS if incremental_pass else INCREMENT_NO

    result: dict[str, Any] = {
        "verdict": primary_verdict,
        "incremental_density_synchrony_verdict": incremental_verdict,
        "scientific_role": SCIENTIFIC_ROLE,
        "phase": "POSTFREEZE_LABEL_EVALUATION",
        "selected_final_method": SELECTED_FINAL_METHOD,
        "pretruth_sha256": actual_pretruth_sha,
        "years": [2023, 2024],
        "events_by_year": dict(pre["events_by_year"]),
        "label_file_sha256": {"2023": sha(a.labels_2023), "2024": sha(a.labels_2024)},
        "candidate_counts": {
            "ordinary": len(ordinary_candidates),
            "recurrent": len(recurrent_candidates),
            "density_sync": len(sync_candidates),
        },
        "mechanism_active": dict(pre["mechanism_active"]),
        "strict_recovered_at_100_improvement_vs_ordinary_some_year": strict_vs_ordinary_100,
        "strict_recovered_at_100_improvement_vs_recurrent_some_year": strict_vs_recurrent_100,
        "ordinary_metrics": ordinary_metrics,
        "recurrent_metrics": recurrent_metrics,
        "density_sync_metrics": sync_metrics,
        "density_sync_vs_ordinary_annual_gates": ordinary_gates,
        "density_sync_vs_recurrent_annual_gates": recurrent_gates,
        "frozen_hdbscan": dict(pre["frozen_hdbscan"]),
        "source_pins": dict(pre["source_pins"]),
        "blind_exclusion": list(BLIND),
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
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": primary_verdict,
        "incremental": incremental_verdict,
        "ordinary": {y: public_metrics(ordinary_metrics[y]) for y in ordinary_metrics},
        "recurrent": {y: public_metrics(recurrent_metrics[y]) for y in recurrent_metrics},
        "density_sync": {y: public_metrics(sync_metrics[y]) for y in sync_metrics},
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
