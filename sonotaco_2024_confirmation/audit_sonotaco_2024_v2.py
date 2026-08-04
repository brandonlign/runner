#!/usr/bin/env python3
"""Data-only parser-v2 audit for the frozen SonotaCo 2024 SNMv3 archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_NAME = "_U2_20240101_S.csv"
MIN_RECORDS = 30_000
MAX_RECORDS = 50_000
ENCODINGS = ("utf-8-sig", "cp932", "shift_jis", "latin-1")
DELIMITERS = (",", ";", "\t", "|")

SEMANTIC_FIELDS = {
    "solar_longitude": {"sol", "solarlongitude", "ls", "solarlong", "soldeg"},
    "radiant_ra": {"ra", "rao", "rat", "radiant ra", "radiant right ascension", "radeg"},
    "radiant_dec": {"dec", "de", "deo", "det", "radiant dec", "radiant declination", "dedeg"},
    "geocentric_speed": {"vg", "geocentric speed", "geocentric velocity", "vgkms"},
    "shower": {"shower", "stream", "shower code"},
}
UNCERTAINTY_TOKENS = (
    "err", "error", "sigma", "uncert", "sd", "dr", "dv", "dd", "pra", "pde", "quality"
)


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

    row_widths: list[int] = []
    row_count = 0
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        row_count += 1
        row_widths.append(len(row))

    trailing_blank_header = bool(raw_header and not raw_header[-1].strip())
    exact_short_rows = bool(
        row_widths
        and all(width == len(raw_header) - 1 for width in row_widths)
    )
    correction_applied = trailing_blank_header and exact_short_rows
    effective_header = raw_header[:-1] if correction_applied else raw_header
    expected_width = len(effective_header)
    malformed_rows = sum(width != expected_width for width in row_widths)

    normalized = [normalize(field) for field in effective_header]
    normalized_set = set(normalized)
    semantic_presence = {
        key: any(normalize(candidate) in normalized_set for candidate in candidates)
        for key, candidates in SEMANTIC_FIELDS.items()
    }
    uncertainty_present = any(
        any(token in field for token in UNCERTAINTY_TOKENS)
        for field in normalized
    )

    return {
        "encoding": encoding,
        "delimiter": delimiter,
        "raw_header": raw_header,
        "effective_header": effective_header,
        "normalized_header": normalized,
        "raw_field_count": len(raw_header),
        "effective_field_count": expected_width,
        "record_count": row_count,
        "malformed_rows": malformed_rows,
        "trailing_header_correction": {
            "raw_final_header_blank": trailing_blank_header,
            "all_nonempty_rows_exactly_one_short": exact_short_rows,
            "applied": correction_applied,
        },
        "semantic_presence": semantic_presence,
        "uncertainty_present": uncertainty_present,
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
    selected_reports: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as handle:
        bad_crc = handle.testzip()
        for info in handle.infolist():
            members.append({
                "name": info.filename,
                "compressed_bytes": info.compress_size,
                "uncompressed_bytes": info.file_size,
                "safe_path": safe_member(info.filename),
                "is_directory": info.is_dir(),
            })
            if info.is_dir() or PurePosixPath(info.filename).name != EXPECTED_NAME:
                continue
            report = inspect_csv(handle.read(info))
            report["member_name"] = info.filename
            report["member_basename"] = PurePosixPath(info.filename).name
            selected_reports.append(report)

    selected = selected_reports[0] if len(selected_reports) == 1 else None
    effective_header = selected["effective_header"] if selected else []
    normalized = selected["normalized_header"] if selected else []
    correction = selected["trailing_header_correction"] if selected else {}

    gates = {
        "nonempty_zip_archive": len(archive_bytes) > 0,
        "safe_members_and_crc": bad_crc is None and all(item["safe_path"] for item in members),
        "exactly_one_required_member": len(selected_reports) == 1,
        "record_count_between_30000_and_50000": bool(
            selected and MIN_RECORDS <= selected["record_count"] <= MAX_RECORDS
        ),
        "frozen_encoding_and_delimiter": bool(
            selected and selected["encoding"] in ENCODINGS and selected["delimiter"] in DELIMITERS
        ),
        "single_frozen_trailing_header_correction_applied": bool(
            selected
            and correction.get("raw_final_header_blank")
            and correction.get("all_nonempty_rows_exactly_one_short")
            and correction.get("applied")
        ),
        "header_at_least_40_unique_nonempty_fields": bool(
            selected
            and len(effective_header) >= 40
            and all(field.strip() for field in effective_header)
            and len(set(normalized)) == len(normalized)
        ),
        "no_malformed_rows_after_single_correction": bool(
            selected and selected["malformed_rows"] == 0
        ),
        "required_geometry_and_label_headers": bool(
            selected and all(selected["semantic_presence"].values())
        ),
        "reported_uncertainty_header_present": bool(
            selected and selected["uncertainty_present"]
        ),
    }

    result = {
        "source": {
            "url": "https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip",
            "required_member": EXPECTED_NAME,
            "reserved_year": 2024,
            "parser_version": 2,
        },
        "archive": {
            "sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "bytes": len(archive_bytes),
            "members": members,
            "bad_crc_member": bad_crc,
        },
        "selected_report": selected,
        "gates": gates,
        "verdict": (
            "PASS_SONOTACO_2024_CONFIRMATION_PARSER_V2"
            if all(gates.values())
            else "KILL_SONOTACO_2024_CONFIRMATION_PARSER_V2"
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "sonotaco_2024_parser_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# SonotaCo 2024 confirmation parser-v2 feasibility result",
        "",
        f"Verdict: **`{result['verdict']}`**",
        "",
        f"Archive bytes: **{len(archive_bytes):,}**",
        f"Archive SHA-256: `{result['archive']['sha256']}`",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in gates.items()
    )
    if selected:
        lines.extend([
            "",
            "## Selected annual member",
            "",
            f"- member: `{selected['member_name']}`",
            f"- records: **{selected['record_count']:,}**",
            f"- raw/effective fields: **{selected['raw_field_count']} / {selected['effective_field_count']}**",
            f"- encoding: `{selected['encoding']}`",
            f"- delimiter repr: `{selected['delimiter']!r}`",
            f"- trailing-header correction: `{selected['trailing_header_correction']}`",
            f"- malformed rows after correction: **{selected['malformed_rows']}**",
            f"- payload SHA-256: `{selected['payload_sha256']}`",
            f"- semantic presence: `{selected['semantic_presence']}`",
            f"- uncertainty header present: **{selected['uncertainty_present']}**",
        ])
    (args.output / "SONOTACO_2024_PARSER_V2.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("frozen SonotaCo 2024 parser-v2 feasibility gate failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"fatal parser-v2 feasibility error: {exc}", file=sys.stderr)
        raise
