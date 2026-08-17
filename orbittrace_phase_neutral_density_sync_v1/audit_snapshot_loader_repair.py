#!/usr/bin/env python3
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any

import run_paired_development_snapshot_repair as repaired

YEARS = (2022, 2023)
PASS = "PASS_PHASE_NEUTRAL_SNAPSHOT_LOADER_REPAIR_AUDIT_V1"
SCHEMA = "ORBITTRACE_PHASE_NEUTRAL_SNAPSHOT_LOADER_REPAIR_AUDIT_V1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n" for row in rows).encode()
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(payload)


def base_rows() -> dict[int, list[dict[str, Any]]]:
    # Deliberately synthetic and outside the protected interval. Values are chosen
    # to exercise exact preservation, year separation, wrap validation and order.
    return {
        2022: [
            {"id": "synthetic-22-a", "year": 2022, "sol": 19.5, "lon": -12.25, "lat": 3.5, "vg": 31.125},
            {"id": "synthetic-22-b", "year": 2022, "sol": 359.75, "lon": 181.0, "lat": -7.25, "vg": 71.5},
        ],
        2023: [
            {"id": "synthetic-23-a", "year": 2023, "sol": 55.25, "lon": 42.125, "lat": 12.75, "vg": 18.0},
            {"id": "synthetic-23-b", "year": 2023, "sol": 200.0, "lon": -179.5, "lat": -21.0, "vg": 44.75},
        ],
    }


def write_fixture(root: Path, rows: dict[int, list[dict[str, Any]]], **manifest_overrides: Any) -> dict[str, Any]:
    row_files: dict[str, str] = {}
    row_sha256: dict[str, str] = {}
    events_by_year: dict[str, int] = {}
    for year in YEARS:
        name = f"synthetic-{year}.jsonl.gz"
        path = root / name
        write_jsonl_gz(path, rows[year])
        row_files[str(year)] = name
        row_sha256[str(year)] = sha(path)
        events_by_year[str(year)] = len(rows[year])

    manifest: dict[str, Any] = {
        "schema": "ORBITTRACE_PHASE_NEUTRAL_GMN_LABEL_FREE_SNAPSHOT_V1",
        "scientific_role": "METHOD_INDEPENDENT_TARGET_EXCLUDED_GMN_2022_2023_SNAPSHOT",
        "years": [2022, 2023],
        "blind_exclusion": [20.0, 55.0],
        "event_order_preserved": True,
        "labels_present": False,
        "hdbscan_fit_executed": False,
        "method_evaluation_executed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "row_files": row_files,
        "row_sha256": row_sha256,
        "events_by_year": events_by_year,
        "events_total": sum(events_by_year.values()),
    }
    manifest.update(manifest_overrides)
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def must_fail(rows: dict[int, list[dict[str, Any]]], expected_fragment: str, **manifest_overrides: Any) -> bool:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, rows, **manifest_overrides)
        try:
            repaired.load_normalized_snapshot(root)
        except Exception as exc:  # exact frozen req() exception type is not part of the repair contract
            return expected_fragment in str(exc)
    return False


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}

    rows = base_rows()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, rows)
        events, manifest, annual_ids = repaired.load_normalized_snapshot(root)
        expected_events = rows[2022] + rows[2023]
        tests["accepts_documented_normalized_schema"] = len(events) == 4
        tests["preserves_row_order_and_values_exactly"] = events == expected_events
        tests["preserves_annual_id_partition"] = annual_ids == {
            2022: {"synthetic-22-a", "synthetic-22-b"},
            2023: {"synthetic-23-a", "synthetic-23-b"},
        }
        tests["manifest_returned_without_science_mutation"] = (
            manifest["labels_present"] is False
            and manifest["hdbscan_fit_executed"] is False
            and manifest["method_evaluation_executed"] is False
        )

    bad = base_rows()
    bad[2022][0] = dict(bad[2022][0], extra=1)
    tests["rejects_schema_drift"] = must_fail(bad, "normalized snapshot schema changed")

    bad = base_rows()
    bad[2022][0] = dict(bad[2022][0], sol=20.0)
    tests["rejects_inclusive_protected_lower_boundary"] = must_fail(bad, "protected normalized snapshot row")

    bad = base_rows()
    bad[2023][0] = dict(bad[2023][0], sol=55.0)
    tests["rejects_inclusive_protected_upper_boundary"] = must_fail(bad, "protected normalized snapshot row")

    bad = base_rows()
    bad[2022][0] = dict(bad[2022][0], year=2023)
    tests["rejects_year_mismatch"] = must_fail(bad, "normalized snapshot year changed")

    bad = base_rows()
    bad[2022][0] = dict(bad[2022][0], vg=0.0)
    tests["rejects_nonpositive_speed"] = must_fail(bad, "nonpositive speed")

    bad = base_rows()
    bad[2022][1] = dict(bad[2022][1], id=bad[2022][0]["id"])
    tests["rejects_duplicate_id_within_year"] = must_fail(bad, "duplicate ID within")

    bad = base_rows()
    bad[2023][0] = dict(bad[2023][0], id=bad[2022][0]["id"])
    tests["rejects_duplicate_id_across_years"] = must_fail(bad, "duplicate IDs across years")

    tests["rejects_manifest_firewall_drift"] = must_fail(base_rows(), "snapshot firewall changed", target_information_access=True)
    tests["rejects_manifest_label_leakage"] = must_fail(base_rows(), "label-free snapshot contains labels", labels_present=True)

    # The compatibility module must not patch the frozen runner merely by being imported.
    tests["import_has_no_runner_side_effect"] = repaired.frozen.load_label_free_snapshot is not repaired.load_normalized_snapshot

    verdict = PASS if all(tests.values()) else "FAIL_PHASE_NEUTRAL_SNAPSHOT_LOADER_REPAIR_AUDIT_V1"
    return {
        "schema": SCHEMA,
        "scientific_role": "ZERO_REAL_DATA_COMPATIBILITY_AUDIT_ONLY",
        "verdict": verdict,
        "tests": tests,
        "synthetic_rows_only": True,
        "real_gmn_rows_accessed": False,
        "sealed_truth_accessed": False,
        "hdbscan_fit_executed": False,
        "method_evaluation_executed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["verdict"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
