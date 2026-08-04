#!/usr/bin/env python3
"""Parser-v2 data-only audit for the frozen SonotaCo 2024 SNMv3 archive."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

SOURCE_URL = "https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip"
EXPECTED_NAME = "_U2_20240101_S.csv"
EXPECTED_ARCHIVE_SHA256 = "409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f"
EXPECTED_MEMBER_SHA256 = "0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00"
MIN_RECORDS = 30_000
MAX_RECORDS = 50_000
ENCODINGS = ("utf-8-sig", "cp932", "shift_jis", "latin-1")
DELIMITERS = (",", ";", "\t", "|")
REQUIRED_GEOMETRY_HEADERS = {
    "solar_longitude": "soldeg",
    "radiant_ra": "radeg",
    "radiant_dec": "dedeg",
    "geocentric_speed": "vgkms",
    "shower": "shower",
}
REQUIRED_MEASUREMENT_UNCERTAINTIES = ("rasddeg", "desddeg", "vgsdkms")
REQUIRED_MATCH_DIAGNOSTICS = ("dr", "dv", "dd")


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


def decode_csv(payload: bytes) -> tuple[str, str, str]:
    for encoding in ENCODINGS:
        try:
            text = payload.decode(encoding)
        except UnicodeDecodeError:
            continue
        sample = text[:65536]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="".join(DELIMITERS))
        except csv.Error:
            dialect = None
        delimiter = dialect.delimiter if dialect is not None else ","
        return text, delimiter, encoding
    raise RuntimeError("no frozen encoding candidate decoded the CSV")


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def inspect_csv(payload: bytes) -> dict:
    text, delimiter, encoding = decode_csv(payload)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    try:
        raw_header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("CSV is empty") from exc

    width_counts: collections.Counter[int] = collections.Counter()
    record_count = 0
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        record_count += 1
        width_counts[len(row)] += 1

    raw_normalized = [normalize(field) for field in raw_header]
    trailing_blank_reconciled = bool(
        raw_normalized
        and raw_normalized[-1] == ""
        and set(width_counts) == {len(raw_header) - 1}
    )
    effective_header = raw_header[:-1] if trailing_blank_reconciled else raw_header
    normalized_header = [normalize(field) for field in effective_header]
    expected_width = len(effective_header)
    malformed_rows = sum(
        count for width, count in width_counts.items() if width != expected_width
    )
    normalized_set = set(normalized_header)

    semantic_presence = {
        key: value in normalized_set
        for key, value in REQUIRED_GEOMETRY_HEADERS.items()
    }
    uncertainty_presence = {
        name: name in normalized_set for name in REQUIRED_MEASUREMENT_UNCERTAINTIES
    }
    diagnostic_presence = {
        name: name in normalized_set for name in REQUIRED_MATCH_DIAGNOSTICS
    }

    return {
        "encoding": encoding,
        "delimiter": delimiter,
        "raw_field_count": len(raw_header),
        "effective_field_count": len(effective_header),
        "raw_normalized_header": raw_normalized,
        "normalized_header": normalized_header,
        "record_count": record_count,
        "row_width_counts": dict(sorted(width_counts.items())),
        "trailing_blank_reconciled": trailing_blank_reconciled,
        "malformed_rows": malformed_rows,
        "semantic_presence": semantic_presence,
        "uncertainty_presence": uncertainty_presence,
        "diagnostic_presence": diagnostic_presence,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_bytes": len(payload),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    archive_bytes = args.archive.read_bytes()
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if not archive_bytes:
        raise SystemExit("downloaded archive is empty")

    members: list[dict] = []
    selected_reports: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as handle:
        bad_crc = handle.testzip()
        for info in handle.infolist():
            members.append(
                {
                    "name": info.filename,
                    "compressed_bytes": info.compress_size,
                    "uncompressed_bytes": info.file_size,
                    "safe_path": safe_member(info.filename),
                    "is_directory": info.is_dir(),
                }
            )
            if info.is_dir() or PurePosixPath(info.filename).name != EXPECTED_NAME:
                continue
            report = inspect_csv(handle.read(info))
            report["member_name"] = info.filename
            report["member_basename"] = PurePosixPath(info.filename).name
            selected_reports.append(report)

    selected = selected_reports[0] if len(selected_reports) == 1 else None
    normalized = selected["normalized_header"] if selected else []

    gates = {
        "exact_pinned_archive": archive_sha256 == EXPECTED_ARCHIVE_SHA256,
        "safe_members_and_crc": bad_crc is None and all(item["safe_path"] for item in members),
        "exactly_one_required_member": len(selected_reports) == 1,
        "exact_pinned_member": bool(
            selected and selected["payload_sha256"] == EXPECTED_MEMBER_SHA256
        ),
        "record_count_between_30000_and_50000": bool(
            selected and MIN_RECORDS <= selected["record_count"] <= MAX_RECORDS
        ),
        "frozen_encoding_and_delimiter": bool(
            selected
            and selected["encoding"] in ENCODINGS
            and selected["delimiter"] in DELIMITERS
        ),
        "documented_trailing_blank_reconciliation": bool(
            selected and selected["trailing_blank_reconciled"]
        ),
        "effective_header_at_least_40_unique_nonempty_fields": bool(
            selected
            and selected["effective_field_count"] >= 40
            and all(normalized)
            and len(set(normalized)) == len(normalized)
        ),
        "no_malformed_rows_after_documented_reconciliation": bool(
            selected and selected["malformed_rows"] == 0
        ),
        "exact_unit_bearing_geometry_and_label_headers": bool(
            selected and all(selected["semantic_presence"].values())
        ),
        "exact_measurement_uncertainty_headers": bool(
            selected and all(selected["uncertainty_presence"].values())
        ),
        "exact_match_diagnostic_headers": bool(
            selected and all(selected["diagnostic_presence"].values())
        ),
    }

    result = {
        "source": {
            "url": SOURCE_URL,
            "required_member": EXPECTED_NAME,
            "reserved_year": 2024,
            "expected_archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "expected_member_sha256": EXPECTED_MEMBER_SHA256,
        },
        "archive": {
            "sha256": archive_sha256,
            "bytes": len(archive_bytes),
            "members": members,
            "bad_crc_member": bad_crc,
        },
        "selected_report": selected,
        "gates": gates,
        "verdict": (
            "PASS_SONOTACO_2024_CONFIRMATION_FEASIBILITY_V2"
            if all(gates.values())
            else "KILL_SONOTACO_2024_CONFIRMATION_FEASIBILITY_V2"
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "sonotaco_2024_feasibility_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# SonotaCo 2024 untouched-confirmation feasibility v2",
        "",
        f"Verdict: **`{result['verdict']}`**",
        "",
        f"Archive bytes: **{len(archive_bytes):,}**",
        f"Archive SHA-256: `{archive_sha256}`",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in gates.items()
    )
    if selected:
        lines.extend(
            [
                "",
                "## Structural summary",
                "",
                f"- member: `{selected['member_name']}`",
                f"- records: **{selected['record_count']:,}**",
                f"- raw/effective fields: **{selected['raw_field_count']} / {selected['effective_field_count']}**",
                f"- row-width counts: `{selected['row_width_counts']}`",
                f"- trailing blank reconciled: **{selected['trailing_blank_reconciled']}**",
                f"- malformed rows after reconciliation: **{selected['malformed_rows']}**",
                f"- encoding / delimiter: `{selected['encoding']}` / `{selected['delimiter']!r}`",
                f"- member SHA-256: `{selected['payload_sha256']}`",
                f"- semantic presence: `{selected['semantic_presence']}`",
                f"- uncertainty presence: `{selected['uncertainty_presence']}`",
                f"- diagnostic presence: `{selected['diagnostic_presence']}`",
            ]
        )
    (args.output / "SONOTACO_2024_FEASIBILITY_V2.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("frozen SonotaCo 2024 parser-v2 feasibility gate failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"fatal feasibility-v2 error: {exc}", file=sys.stderr)
        raise
