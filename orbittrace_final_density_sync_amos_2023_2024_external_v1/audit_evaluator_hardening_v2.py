#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_sha(mapping: dict[Any, Any]) -> str:
    payload = {str(k): v for k, v in sorted(mapping.items(), key=lambda kv: int(kv[0]))}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def membership_sha(candidates: list[dict[str, Any]]) -> str:
    rows = ["|".join(map(str, row["event_ids"])) for row in candidates]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def run_evaluator(
    evaluator: Path,
    pretruth: Path,
    pretruth_sha: str,
    labels_2023: Path,
    labels_2024: Path,
    output: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(evaluator.resolve()),
            "--pretruth", str(pretruth.resolve()),
            "--pretruth-sha256", pretruth_sha,
            "--labels-2023", str(labels_2023.resolve()),
            "--labels-2024", str(labels_2024.resolve()),
            "--output", str(output.resolve()),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_prelabel_rejection(
    name: str,
    base: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    expected_error: str,
    evaluator: Path,
    work: Path,
) -> dict[str, Any]:
    obj = copy.deepcopy(base)
    mutate(obj)
    path = work / f"tampered_{name}.json"
    write_json(path, obj)
    nonexistent_2023 = work / "MUST_NOT_OPEN_LABELS_2023.csv"
    nonexistent_2024 = work / "MUST_NOT_OPEN_LABELS_2024.csv"
    proc = run_evaluator(
        evaluator,
        path,
        sha(path),
        nonexistent_2023,
        nonexistent_2024,
        work / f"tampered_out_{name}",
    )
    require(proc.returncode != 0, f"tampered pretruth {name} unexpectedly evaluated")
    combined = proc.stdout + "\n" + proc.stderr
    require(expected_error in combined, f"tamper {name} failed for wrong reason; expected {expected_error!r}; got {combined[-1000:]!r}")
    require("FileNotFoundError" not in combined, f"tamper {name} reached label-file opening")
    require("MUST_NOT_OPEN_LABELS" not in combined, f"tamper {name} referenced nonexistent label path before rejection")
    return {
        "name": name,
        "rejected": True,
        "expected_error": expected_error,
        "label_files_opened": False,
        "returncode": proc.returncode,
        "tampered_pretruth_sha256": sha(path),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--valid-pretruth", type=Path, required=True)
    p.add_argument("--labels-2023", type=Path, required=True)
    p.add_argument("--labels-2024", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.mkdir(parents=True, exist_ok=True)

    base = json.loads(a.valid_pretruth.read_text(encoding="utf-8"))

    # First prove the exact untampered synthetic pretruth still evaluates under the
    # hardened trust boundary with unchanged scientific metrics/gates.
    valid_out = a.work / "valid_hardened_eval"
    valid_proc = run_evaluator(
        a.evaluator,
        a.valid_pretruth,
        sha(a.valid_pretruth),
        a.labels_2023,
        a.labels_2024,
        valid_out,
    )
    require(valid_proc.returncode == 0, f"valid hardened evaluator run failed: {valid_proc.stderr[-1500:]}")
    valid_result_path = valid_out / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    valid_result = json.loads(valid_result_path.read_text(encoding="utf-8"))
    require(valid_result["pretruth_internal_integrity_verified_before_labels"] is True, "hardened valid run did not record pretruth integrity verification")

    tests: list[dict[str, Any]] = []

    tests.append(expect_prelabel_rejection(
        "source_pin",
        base,
        lambda x: x["source_pins"].__setitem__("density_sync_git_blob", "0" * 40),
        "pretruth scientific/transport source pins changed",
        a.evaluator,
        a.work,
    ))

    tests.append(expect_prelabel_rejection(
        "hdbscan_pin",
        base,
        lambda x: x["frozen_hdbscan"].__setitem__("min_samples", 11),
        "frozen HDBSCAN declaration changed",
        a.evaluator,
        a.work,
    ))

    tests.append(expect_prelabel_rejection(
        "order_hash",
        base,
        lambda x: x.__setitem__("ordinary_order_sha256", "0" * 64),
        "ordinary candidate order hash mismatch",
        a.evaluator,
        a.work,
    ))

    def inject_nonretained(x: dict[str, Any]) -> None:
        row = x["ordinary_candidates"][0]
        row["event_ids"] = sorted(list(row["event_ids"]) + ["9999-NONRETAINED-SYNTHETIC"])
        row["member_count"] = len(row["event_ids"])
        x["ordinary_membership_sha256"] = membership_sha(x["ordinary_candidates"])

    tests.append(expect_prelabel_rejection(
        "nonretained_candidate_id",
        base,
        inject_nonretained,
        "contains non-retained event IDs",
        a.evaluator,
        a.work,
    ))

    def inject_overlap(x: dict[str, Any]) -> None:
        require(len(x["ordinary_candidates"]) >= 2, "synthetic fixture lacks two ordinary candidates")
        donor = str(x["ordinary_candidates"][0]["event_ids"][0])
        row = x["ordinary_candidates"][1]
        require(donor not in row["event_ids"], "synthetic fixture already overlaps")
        row["event_ids"] = sorted(list(row["event_ids"]) + [donor])
        row["member_count"] = len(row["event_ids"])
        x["ordinary_membership_sha256"] = membership_sha(x["ordinary_candidates"])

    tests.append(expect_prelabel_rejection(
        "overlapping_flat_membership",
        base,
        inject_overlap,
        "ordinary flat candidate memberships overlap",
        a.evaluator,
        a.work,
    ))

    def duplicate_retained_id(x: dict[str, Any]) -> None:
        ids = list(x["event_ids_by_year"]["2023"])
        ids.append(ids[0])
        x["event_ids_by_year"]["2023"] = sorted(ids)
        x["events_by_year"]["2023"] = len(ids)
        x["events_total"] = int(x["events_total"]) + 1

    tests.append(expect_prelabel_rejection(
        "duplicate_retained_id",
        base,
        duplicate_retained_id,
        "duplicate retained event ID within 2023",
        a.evaluator,
        a.work,
    ))

    def corrupt_annual_map(x: dict[str, Any]) -> None:
        node = sorted(x["recurrent_annual_eom"], key=int)[0]
        vals = list(x["recurrent_annual_eom"][node])
        vals[0] = float(vals[0]) + 0.001
        x["recurrent_annual_eom"][node] = vals
        new_hash = mapping_sha(x["recurrent_annual_eom"])
        x["recurrent_annual_eom_sha256"] = new_hash
        x["density_sync_parent_annual_sha256"] = new_hash

    tests.append(expect_prelabel_rejection(
        "annual_reconstruction",
        base,
        corrupt_annual_map,
        "annual EOM reconstruction mismatch",
        a.evaluator,
        a.work,
    ))

    def falsify_mechanism(x: dict[str, Any]) -> None:
        current = bool(x["mechanism_active"]["ordinary_vs_density_sync"])
        x["mechanism_active"]["ordinary_vs_density_sync"] = not current

    tests.append(expect_prelabel_rejection(
        "mechanism_flag",
        base,
        falsify_mechanism,
        "stored mechanism-active flags do not match selected nodes/orders",
        a.evaluator,
        a.work,
    ))

    audit = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V2",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V2",
        "synthetic_only": True,
        "valid_pretruth_sha256": sha(a.valid_pretruth),
        "valid_result_sha256": sha(valid_result_path),
        "valid_scientific_verdict_reporting_only": valid_result["verdict"],
        "valid_incremental_verdict_reporting_only": valid_result["incremental_density_synchrony_verdict"],
        "tamper_tests": tests,
        "all_tampered_pretruth_rejected_before_labels": all(t["rejected"] and not t["label_files_opened"] for t in tests),
        "tamper_test_count": len(tests),
        "scientific_method_or_gate_changed": False,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V2.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
