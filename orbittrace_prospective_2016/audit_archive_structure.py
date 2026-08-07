#!/usr/bin/env python3
"""Prospective SonotaCo-2016 transport/schema audit with no scientific-field access."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

YEAR = 2016
EXPECTED_MEMBER_SUFFIX = "/_U2_20160101_S.csv"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    archive_payload = args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive_payload)) as handle:
        names = handle.namelist()
        unsafe = [name for name in names if not safe_member(name)]
        if unsafe:
            raise RuntimeError(f"unsafe ZIP paths: {unsafe[:3]}")
        corrupt = handle.testzip()
        if corrupt is not None:
            raise RuntimeError(f"ZIP CRC failure: {corrupt}")
        candidates = [name for name in names if name.endswith(EXPECTED_MEMBER_SUFFIX)]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one annual member ending {EXPECTED_MEMBER_SUFFIX}, found {candidates}")
        member = candidates[0]
        member_payload = handle.read(member)

    reader = csv.reader(io.StringIO(member_payload.decode("utf-8-sig"), newline=""))
    raw_header = next(reader)
    normalized_header = [normalize(field) for field in raw_header]
    widths: Counter[int] = Counter()
    total_rows = 0
    blank_rows = 0
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            blank_rows += 1
            continue
        total_rows += 1
        widths[len(row)] += 1

    gates = {
        "archive_nonempty": len(archive_payload) > 0,
        "safe_zip_paths": not unsafe,
        "zip_crc_pass": corrupt is None,
        "exact_annual_member_found": bool(member),
        "nonempty_header": len(raw_header) > 0,
        "nonempty_annual_rows": total_rows > 0,
        "bounded_row_width_variants": 1 <= len(widths) <= 2,
    }
    verdict = "PASS_SONOTACO_2016_ARCHIVE_STRUCTURE_AUDIT" if all(gates.values()) else "FAIL_SONOTACO_2016_ARCHIVE_STRUCTURE_AUDIT"
    result = {
        "verdict": verdict,
        "classification": "prospective transport/schema audit only; no label values, coordinates, detector scores, coefficients, AUROC, recall, FPR, or candidate endpoints inspected",
        "year": YEAR,
        "archive": {
            "filename": args.archive.name,
            "bytes": len(archive_payload),
            "sha256": sha256_bytes(archive_payload),
            "zip_member_count": len(names),
        },
        "annual_member": {
            "name": member,
            "bytes": len(member_payload),
            "sha256": sha256_bytes(member_payload),
            "raw_header_width": len(raw_header),
            "normalized_header": normalized_header,
            "trailing_empty_header": bool(normalized_header and normalized_header[-1] == ""),
            "total_nonblank_rows": total_rows,
            "blank_rows": blank_rows,
            "row_width_counts": {str(k): v for k, v in sorted(widths.items())},
        },
        "gates": gates,
        "prohibited_access": {
            "shower_label_values_read": False,
            "radiant_or_speed_values_read": False,
            "orbit_values_read": False,
            "v3_scores_computed": False,
            "fixed4_scores_computed": False,
            "v8_statistics_computed": False,
            "scientific_endpoints_computed": False,
        },
    }
    (args.output / "SONOTACO_2016_ARCHIVE_STRUCTURE_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
