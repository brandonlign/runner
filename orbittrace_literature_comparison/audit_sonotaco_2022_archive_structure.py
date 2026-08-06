#!/usr/bin/env python3
"""Record immutable SonotaCo-2022 transport structure without reading labels or scores."""
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

YEAR = 2022
EXPECTED_MEMBER_SUFFIX = "/_U2_20220101_S.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


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
        if any(not safe_member(name) for name in names):
            raise RuntimeError("unsafe ZIP path")
        if handle.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        candidates = [name for name in names if name.endswith(EXPECTED_MEMBER_SUFFIX)]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one annual member, found {candidates}")
        member = candidates[0]
        member_payload = handle.read(member)

    reader = csv.reader(io.StringIO(member_payload.decode("utf-8-sig"), newline=""))
    raw_header = next(reader)
    normalized_header = [normalize(field) for field in raw_header]
    row_widths: Counter[int] = Counter()
    total_rows = 0
    blank_rows = 0
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            blank_rows += 1
            continue
        total_rows += 1
        row_widths[len(row)] += 1

    result = {
        "verdict": "PASS_SONOTACO_2022_ARCHIVE_STRUCTURE_AUDIT",
        "classification": "transport and schema audit; no shower-label values, coordinates, coefficients, or detector scores inspected",
        "year": YEAR,
        "archive": {
            "filename": args.archive.name,
            "bytes": len(archive_payload),
            "sha256": sha256_bytes(archive_payload),
            "zip_member_count": len(names),
            "crc_pass": True,
            "safe_paths": True
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
            "row_width_counts": {str(width): count for width, count in sorted(row_widths.items())}
        },
        "prohibited_access": {
            "shower_label_values_read": False,
            "candidate_values_read": False,
            "wavelet_coefficients_computed": False,
            "fixed4_scores_computed": False,
            "hybrid_scores_computed": False,
            "positive_or_negative_episode_outcomes_computed": False
        }
    }
    (args.output / "sonotaco_2022_archive_structure_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
