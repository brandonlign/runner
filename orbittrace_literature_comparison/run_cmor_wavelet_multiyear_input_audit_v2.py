#!/usr/bin/env python3
"""Schema-reconciled execution wrapper for the frozen CMOR multiyear input audit.

The scientific audit, thresholds, year set, filters, and decisions remain in
``run_cmor_wavelet_multiyear_input_audit`` unchanged. This wrapper replaces only
the annual CSV loader so the documented pre-2025 trailing-empty-header form is
reconciled exactly as in the validated SonotaCo 2023 parser.
"""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Any

import run_cmor_wavelet_multiyear_input_audit as frozen


def load_year_reconciled(archive_path: Path, year: int) -> tuple[list[int], dict[str, Any]]:
    archive_payload = archive_path.read_bytes()
    archive_sha = frozen.sha256_bytes(archive_payload)
    with zipfile.ZipFile(io.BytesIO(archive_payload)) as handle:
        member = frozen.select_annual_member(handle, year)
        member_payload = handle.read(member)
    member_sha = frozen.sha256_bytes(member_payload)

    reader = csv.reader(io.StringIO(member_payload.decode("utf-8-sig"), newline=""))
    raw_header = [field.strip() for field in next(reader)]
    trailing_empty_header = bool(raw_header) and raw_header[-1] == ""
    header = raw_header[:-1] if trailing_empty_header else raw_header
    if not header or any(not field for field in header):
        raise RuntimeError(f"year {year}: invalid effective header")
    if len(set(header)) != len(header):
        raise RuntimeError(f"year {year}: duplicate effective header")
    index = {field: position for position, field in enumerate(header)}
    required = ("sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)")
    missing = [field for field in required if field not in index]
    if missing:
        raise RuntimeError(f"year {year}: missing fields {missing}")

    counts = [0] * 360
    audit: dict[str, Any] = {
        "year": year,
        "archive_file": archive_path.name,
        "archive_bytes": len(archive_payload),
        "archive_sha256": archive_sha,
        "member": member,
        "member_bytes": len(member_payload),
        "member_sha256": member_sha,
        "raw_header_fields": len(raw_header),
        "effective_header_fields": len(header),
        "header_fields": len(header),
        "trailing_empty_header_reconciled": trailing_empty_header,
        "raw_header_sha256": frozen.sha256_bytes("\n".join(raw_header).encode()),
        "header_sha256": frozen.sha256_bytes("\n".join(header).encode()),
        "fields_read": list(required),
        "shower_label_field_read": False,
        "raw_rows": 0,
        "malformed_rows": 0,
        "nonfinite_rows": 0,
        "failed_convergence": 0,
        "failed_speed": 0,
        "failed_speed_uncertainty": 0,
        "blind_rows_removed": 0,
        "retained_rows": 0,
    }
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        audit["raw_rows"] += 1
        if len(row) != len(header):
            audit["malformed_rows"] += 1
            continue
        try:
            sol = frozen.finite_float(row[index["sol(deg)"]]) % 360.0
            vg = frozen.finite_float(row[index["vg(km/s)"]])
            vg_sd = frozen.finite_float(row[index["vg sd(km/s)"]])
            convergence = frozen.finite_float(row[index["Qc(deg)"]])
        except (ValueError, IndexError):
            audit["nonfinite_rows"] += 1
            continue
        if not convergence > 15.0:
            audit["failed_convergence"] += 1
            continue
        if not 0.0 < vg <= 75.0:
            audit["failed_speed"] += 1
            continue
        if not 0.0 <= vg_sd <= 0.10 * vg + 1.0:
            audit["failed_speed_uncertainty"] += 1
            continue
        if frozen.in_blind_interval(sol):
            audit["blind_rows_removed"] += 1
            continue
        counts[int(frozen.math.floor(sol)) % 360] += 1
        audit["retained_rows"] += 1

    if sum(counts) != audit["retained_rows"]:
        raise RuntimeError(f"year {year}: retained count mismatch")
    return counts, audit


def main() -> None:
    frozen.load_year = load_year_reconciled
    frozen.main()


if __name__ == "__main__":
    main()
