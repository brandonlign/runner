#!/usr/bin/env python3
"""Data-only audit for the frozen SonotaCo 2025 SNMv3 archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_NAME = "_U2_20250101_S.csv"
EXPECTED_ROWS = 36_826
ENCODINGS = ("utf-8-sig", "cp932", "shift_jis", "latin-1")
DELIMITERS = (",", ";", "\t", "|")


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
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("CSV is empty") from exc

    expected_width = len(header)
    row_count = 0
    malformed_rows = 0
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        row_count += 1
        if len(row) != expected_width:
            malformed_rows += 1

    return {
        "encoding": encoding,
        "delimiter": delimiter,
        "header": header,
        "field_count": expected_width,
        "record_count": row_count,
        "malformed_rows": malformed_rows,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_bytes": len(payload),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    archive_bytes = args.archive.read_bytes()
    if not archive_bytes:
        raise SystemExit("downloaded archive is empty")

    members: list[dict] = []
    csv_reports: list[dict] = []
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
            if info.is_dir() or not info.filename.lower().endswith(".csv"):
                continue
            report = inspect_csv(handle.read(info))
            report["member_name"] = info.filename
            report["member_basename"] = PurePosixPath(info.filename).name
            csv_reports.append(report)

    exact_count_members = [
        report for report in csv_reports if report["record_count"] == EXPECTED_ROWS
    ]
    selected = exact_count_members[0] if len(exact_count_members) == 1 else None
    selected_header = selected["header"] if selected else []

    gates = {
        "nonempty_zip_archive": len(archive_bytes) > 0,
        "safe_members_and_crc": bad_crc is None and all(item["safe_path"] for item in members),
        "nonempty_csv_exists": any(report["payload_bytes"] > 0 for report in csv_reports),
        "exactly_one_published_count_csv": len(exact_count_members) == 1,
        "published_csv_basename_matches": bool(
            selected and selected["member_basename"] == EXPECTED_NAME
        ),
        "header_at_least_ten_unique_nonempty_fields": bool(
            selected
            and len(selected_header) >= 10
            and all(field.strip() for field in selected_header)
            and len(set(selected_header)) == len(selected_header)
        ),
        "deterministic_encoding_and_delimiter": bool(
            selected
            and selected["encoding"] in ENCODINGS
            and selected["delimiter"] in DELIMITERS
        ),
        "no_malformed_rows": bool(selected and selected["malformed_rows"] == 0),
    }

    result = {
        "source": {
            "url": "https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip",
            "published_name": EXPECTED_NAME,
            "published_year": 2025,
            "published_orbits": EXPECTED_ROWS,
        },
        "archive": {
            "sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "bytes": len(archive_bytes),
            "members": members,
            "bad_crc_member": bad_crc,
        },
        "csv_reports": csv_reports,
        "gates": gates,
        "verdict": "PASS_SONOTACO_2025_FEASIBILITY"
        if all(gates.values())
        else "KILL_SONOTACO_2025_FEASIBILITY",
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "sonotaco_2025_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    report_lines = [
        "# SonotaCo 2025 external-survey feasibility result",
        "",
        f"Verdict: **`{result['verdict']}`**",
        "",
        f"Archive bytes: **{len(archive_bytes):,}**",
        f"Archive SHA-256: `{result['archive']['sha256']}`",
        f"CSV members: **{len(csv_reports)}**",
        "",
        "## Frozen gates",
        "",
    ]
    report_lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in gates.items()
    )
    if selected:
        report_lines.extend(
            [
                "",
                "## Selected published-count CSV",
                "",
                f"- member: `{selected['member_name']}`",
                f"- records: **{selected['record_count']:,}**",
                f"- fields: **{selected['field_count']}**",
                f"- encoding: `{selected['encoding']}`",
                f"- delimiter repr: `{selected['delimiter']!r}`",
                f"- header: `{selected['header']}`",
                f"- malformed rows: **{selected['malformed_rows']}**",
            ]
        )
    (args.output / "SONOTACO_2025_FEASIBILITY.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("frozen SonotaCo 2025 feasibility gate failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"fatal feasibility error: {exc}", file=sys.stderr)
        raise
