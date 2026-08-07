#!/usr/bin/env python3
"""Frozen pre-scientific UKMON 2020/2021 structure/interface audit.

Only JSON/container structure and record-key membership are inspected. Scientific field
values and opaque identifiers are never read, converted, logged, stored, or compared.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

DATES = ("20200814", "20210814")
BASE = "https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval={}"
REQUIRED = (
    "orbname",
    "_sol",
    "_ra_t",
    "_dc_t",
    "_vg",
    "_q",
    "_e",
    "_incl",
    "_peri",
    "_node",
)


def extract_rows_structure_only(payload):
    if isinstance(payload, list) and all(isinstance(x, dict) for x in payload):
        return payload, "top_level_list"
    if isinstance(payload, dict):
        for key in ("data", "results", "matches", "summary"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(x, dict) for x in value):
                return value, f"dict_list:{key}"
        if payload and all(isinstance(v, dict) for v in payload.values()):
            # The validated 2022 parser maps the outer record key to orbname. For this
            # structure audit we do not inspect that key's value; we only mark that the
            # parser supplies the required orbname field structurally.
            rows = []
            for value in payload.values():
                row = dict(value)
                if "orbname" not in row:
                    row["orbname"] = object()
                rows.append(row)
            return rows, "dict_of_records"
    raise RuntimeError(f"unrecognized summary JSON structure: {type(payload).__name__}")


def audit_date(date: str) -> dict:
    url = BASE.format(date)
    response = requests.get(
        url,
        timeout=120,
        headers={"User-Agent": "OrbitTrace-UKMON-2020-2021-structure-audit/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    rows, shape = extract_rows_structure_only(payload)
    n = len(rows)
    presence_fraction = {
        key: (sum(key in row for row in rows) / n if n else 0.0)
        for key in REQUIRED
    }
    gates = {
        "json_container_recognized": True,
        "rows_at_least_5": n >= 5,
        "all_required_keys_present_95pct": all(v >= 0.95 for v in presence_fraction.values()),
    }
    return {
        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
        "url": url,
        "response_shape": shape,
        "rows_at_least_5": n >= 5,
        "required_key_presence_fraction": presence_fraction,
        "gates": gates,
        "exact_row_count_withheld": True,
        "scientific_field_values_inspected": False,
        "orbname_values_inspected": False,
        "source_label_values_inspected": False,
        "raw_payload_persisted": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--freshness-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    fresh = json.loads(a.freshness_json.read_text())
    assert fresh["verdict"] == "PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION"
    assert fresh["raw_audit_verdict_preserved"] == "FAIL_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    assert fresh["raw_hit_count"] == 1
    assert fresh["additional_hits_forgiven"] == 0
    assert fresh["meteor_api_contacted"] is False
    assert fresh["scientific_value_access_this_adjudication"] is False
    assert fresh["target_information_access"] is False

    results = [audit_date(d) for d in DATES]
    all_gates = all(all(x["gates"].values()) for x in results)
    verdict = (
        "PASS_UKMON_2020_2021_STRUCTURE_AUDIT"
        if all_gates
        else "FAIL_UKMON_2020_2021_STRUCTURE_AUDIT"
    )
    result = {
        "verdict": verdict,
        "dates": ["2020-08-14", "2021-08-14"],
        "date_selection_basis": "same month/day as the UKMON-published and already-validated 2022-08-14 interface example",
        "results": results,
        "scientific_field_values_inspected": False,
        "orbname_values_inspected": False,
        "source_label_values_inspected": False,
        "raw_payload_persisted": False,
        "method_evaluation_performed": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Pre-scientific interface structure only. The audit tests the already-fixed 2022 response-container parser and required-key membership on two prospectively fixed dates. "
            "No meteor scientific field value or opaque orbname value is read, converted, logged, persisted, summarized, or used for a method decision. A pass authorizes protocol freeze, not scientific evaluation."
        ),
    }
    (a.output / "ukmon_2020_2021_structure_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
