#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ALIASES = (
    "sporadic",
    "SpOrAdIc",
    "NONE",
    "none",
    "NULL",
    "NA",
    "N/A",
    "UNKNOWN",
    "UNASSIGNED",
    "NO_SHOWER",
    "NO SHOWER",
    "0",
    "-",
)


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        require(r.fieldnames == ["event_id", "shower_association"], f"unexpected label header: {r.fieldnames}")
        return [dict(row) for row in r]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "shower_association"])
        w.writeheader()
        w.writerows(rows)


def run_eval(evaluator: Path, pretruth: Path, labels23: Path, labels24: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(evaluator.resolve()),
            "--pretruth", str(pretruth.resolve()),
            "--pretruth-sha256", sha(pretruth),
            "--labels-2023", str(labels23.resolve()),
            "--labels-2024", str(labels24.resolve()),
            "--output", str(out.resolve()),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--pretruth", type=Path, required=True)
    p.add_argument("--labels-2023", type=Path, required=True)
    p.add_argument("--labels-2024", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.mkdir(parents=True, exist_ok=True)

    rows23 = read_rows(a.labels_2023)
    rows24 = read_rows(a.labels_2024)
    require(len(rows23) >= 4 and rows24, "synthetic label fixture too small")

    # Exact canonical SPORADIC must be accepted.
    exact_rows = [dict(r) for r in rows23]
    exact_rows[0]["shower_association"] = "SPORADIC"
    exact_path = a.work / "labels23_exact_sporadic.csv"
    write_rows(exact_path, exact_rows)
    exact_out = a.work / "exact_sporadic_out"
    exact_proc = run_eval(a.evaluator, a.pretruth, exact_path, a.labels_2024, exact_out)
    require(exact_proc.returncode == 0, f"exact SPORADIC rejected: {(exact_proc.stdout + exact_proc.stderr)[-1200:]}")

    # A valid mixed-case shower code must survive exactly. Make it eligible with 4 rows,
    # then verify the inherited metrics expose the exact same string as a label key.
    exact_code = "MiXeD-Code_42"
    code_rows = [dict(r) for r in rows23]
    for i in range(4):
        code_rows[i]["shower_association"] = exact_code
    code_path = a.work / "labels23_exact_code.csv"
    write_rows(code_path, code_rows)
    code_out = a.work / "exact_code_out"
    code_proc = run_eval(a.evaluator, a.pretruth, code_path, a.labels_2024, code_out)
    require(code_proc.returncode == 0, f"valid exact shower code rejected: {(code_proc.stdout + code_proc.stderr)[-1200:]}")
    code_result_path = code_out / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    code_result = json.loads(code_result_path.read_text(encoding="utf-8"))
    for method in ("ordinary_metrics", "recurrent_metrics", "density_sync_metrics"):
        first = code_result[method]["2023"]["first_rank_by_label"]
        require(exact_code in first, f"valid shower code was normalized/renamed in {method}: {sorted(first)[:10]}")
    exact_nonbackground_preserved = True

    # Every known ambiguous no-association alias must fail closed.
    alias_results: list[dict[str, Any]] = []
    for i, alias in enumerate(ALIASES):
        bad_rows = [dict(r) for r in rows24]
        bad_rows[0]["shower_association"] = alias
        bad_path = a.work / f"labels24_bad_alias_{i}.csv"
        write_rows(bad_path, bad_rows)
        proc = run_eval(a.evaluator, a.pretruth, a.labels_2023, bad_path, a.work / f"bad_alias_out_{i}")
        combined = proc.stdout + "\n" + proc.stderr
        require(proc.returncode != 0, f"ambiguous alias unexpectedly accepted: {alias!r}")
        if alias.upper() == "SPORADIC":
            require("noncanonical SPORADIC sentinel" in combined, f"SPORADIC case variant failed for wrong reason: {alias!r}")
        else:
            require("ambiguous no-association sentinel" in combined, f"ambiguous alias failed for wrong reason: {alias!r}")
        alias_results.append({"alias": alias, "rejected": True})

    # Surrounding whitespace must be rejected, not silently stripped/normalized.
    whitespace_rows = [dict(r) for r in rows23]
    whitespace_rows[0]["shower_association"] = " MiXeD-Code_42 "
    whitespace_path = a.work / "labels23_whitespace.csv"
    write_rows(whitespace_path, whitespace_rows)
    whitespace_proc = run_eval(a.evaluator, a.pretruth, whitespace_path, a.labels_2024, a.work / "whitespace_out")
    whitespace_combined = whitespace_proc.stdout + "\n" + whitespace_proc.stderr
    require(whitespace_proc.returncode != 0, "association label with surrounding whitespace was silently normalized")
    require("association label contains surrounding whitespace" in whitespace_combined, "whitespace label failed for wrong reason")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_LABEL_TRANSPORT_EXACTNESS_AUDIT_V3",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_LABEL_TRANSPORT_EXACTNESS_AUDIT_V3",
        "synthetic_only": True,
        "exact_sporadic_accepted": True,
        "exact_nonbackground_shower_code": exact_code,
        "exact_nonbackground_shower_code_preserved": exact_nonbackground_preserved,
        "ambiguous_aliases_tested": list(ALIASES),
        "ambiguous_alias_results": alias_results,
        "ambiguous_aliases_all_rejected": all(x["rejected"] for x in alias_results),
        "surrounding_whitespace_rejected_not_normalized": True,
        "valid_code_result_sha256": sha(code_result_path),
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
        "dms_scientific_access": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_LABEL_TRANSPORT_EXACTNESS_AUDIT_V3.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
