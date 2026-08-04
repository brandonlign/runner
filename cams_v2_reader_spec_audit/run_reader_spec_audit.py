#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import requests

URL = "https://www.astro.sk/~ne/IAUMDC/PhV2016/reading.f"
EXPECTED_BYTES = 9_905
EXPECTED_SHA256 = "437d9d8f7d68b824751954b51e2caaec69e379912bce3b924acf2292e89acb1c"
COMMENT_TERMS = ("SHOWER", "STREAM", "IAU", "WORKING LIST", "TAG", "CLASSIFICATION")
DECL_PREFIXES = (
    "INTEGER",
    "REAL",
    "DOUBLE PRECISION",
    "CHARACTER",
    "LOGICAL",
    "DIMENSION",
    "COMMON",
    "PARAMETER",
    "DATA",
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fixed_form_statements(lines: list[str]) -> tuple[list[dict], list[str], list[str]]:
    statements: list[dict] = []
    comments: list[str] = []
    blanks: list[str] = []
    current: dict | None = None

    for line_number, original in enumerate(lines, start=1):
        line = original.expandtabs(8)
        if not line.strip():
            blanks.append(original)
            continue
        first = line[0] if line else " "
        if first in ("C", "c", "*", "!"):
            comments.append(original)
            continue
        padded = line.ljust(72)
        label = padded[:5].strip()
        continuation = padded[5:6] not in ("", " ", "0")
        body = padded[6:72].rstrip()
        if continuation and current is not None:
            current["physical_lines"].append(line_number)
            current["text"] += " " + body.strip()
        else:
            if current is not None:
                statements.append(current)
            current = {
                "label": label,
                "physical_lines": [line_number],
                "text": body.strip(),
            }
    if current is not None:
        statements.append(current)
    return statements, comments, blanks


def identifier_tokens(text: str) -> set[str]:
    return {token.upper() for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text)}


def build_result() -> tuple[dict, bytes]:
    response = requests.get(URL, timeout=300)
    response.raise_for_status()
    raw = response.content
    digest = sha256(raw)
    if len(raw) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise RuntimeError(f"reader source mismatch bytes={len(raw)} sha256={digest}")

    text = raw.decode("latin-1")
    lines = text.splitlines()
    statements, comments, blanks = fixed_form_statements(lines)
    normalized = [item | {"upper": item["text"].upper()} for item in statements]

    reads = [item for item in normalized if re.search(r"\bREAD\s*\(", item["upper"])]
    writes = [item for item in normalized if re.search(r"\bWRITE\s*\(", item["upper"])]
    opens = [item for item in normalized if re.search(r"\bOPEN\s*\(", item["upper"])]
    formats = [
        item
        for item in normalized
        if re.match(r"^FORMAT\s*\(", item["upper"])
        or (item["label"] and "FORMAT" in item["upper"])
    ]
    declarations = [
        item
        for item in normalized
        if any(item["upper"].startswith(prefix) for prefix in DECL_PREFIXES)
    ]
    relevant_comments = [line for line in comments if any(term in line.upper() for term in COMMENT_TERMS)]

    source_upper = text.upper()
    field_groups = {
        "date_or_solar_longitude": any(
            re.search(pattern, source_upper)
            for pattern in (r"SOLAR", r"SUN\s*LONG", r"\bSOL\b", r"\bDATE\b", r"\bYEAR\b", r"\bMONTH\b", r"\bDAY\b", r"JULIAN")
        ),
        "radiant_longitude_or_ra": any(
            re.search(pattern, source_upper)
            for pattern in (r"RIGHT\s+ASCENSION", r"RADIANT", r"\bRA\b", r"ECLIPTIC\s+LONG", r"\bALPHA\b")
        ),
        "radiant_latitude_or_declination": any(
            re.search(pattern, source_upper)
            for pattern in (r"DECLINATION", r"\bDEC\b", r"ECLIPTIC\s+LAT", r"\bBETA\b")
        ),
        "geocentric_speed": any(
            re.search(pattern, source_upper)
            for pattern in (r"GEOCENTRIC", r"\bVG\b", r"V_G", r"SPEED", r"VELOCITY")
        ),
    }

    shower_context = "\n".join(relevant_comments + [item["text"] for item in declarations])
    shower_tokens = identifier_tokens(shower_context)
    stop = {
        "SHOWER", "SHOWERS", "STREAM", "STREAMS", "WORKING", "LIST", "TAG", "TAGS",
        "CLASSIFICATION", "IAU", "THE", "AND", "OR", "OF", "IN", "IS", "ARE", "TO",
        "INTEGER", "REAL", "CHARACTER", "DOUBLE", "PRECISION", "DATA", "COMMON", "FORMAT",
    }
    candidate_tokens = sorted(token for token in shower_tokens - stop if len(token) >= 2)
    read_tokens = set().union(*(identifier_tokens(item["text"]) for item in reads)) if reads else set()
    matching_shower_tokens = sorted(set(candidate_tokens) & read_tokens)
    literal_shower_read = any(
        re.search(r"SHOWER|STREAM|IAU|IAUNO|IAU_NO|SHOWERNO|SHOWER_NO", item["upper"])
        for item in reads
    )

    format_labels = {item["label"] for item in formats if item["label"]}
    read_format_references: list[str] = []
    for item in reads:
        match = re.search(r"READ\s*\([^,]+,\s*([0-9]+)", item["upper"])
        if match:
            read_format_references.append(match.group(1))
    complete_interface = bool(reads and formats) and (
        not read_format_references or all(label in format_labels for label in read_format_references)
    )

    gates = {
        "exact_reader_source_hash_and_size": len(raw) == EXPECTED_BYTES and digest == EXPECTED_SHA256,
        "fortran_read_and_format_present": bool(reads and formats),
        "complete_read_format_interface_identified": complete_interface,
        "required_geometry_field_groups_identified": all(field_groups.values()),
        "native_shower_or_stream_field_read": bool(matching_shower_tokens or literal_shower_read),
        "data_archives_not_requested": True,
        "sonotaco_2024_not_read": True,
        "camsv3_2016_values_not_read": True,
    }
    verdict = "PASS_HISTORICAL_CAMSV2_READER_SPEC" if all(gates.values()) else "KILL_HISTORICAL_CAMSV2_READER_SPEC"
    result = {
        "method": "Historical CAMS Database 2.0 reader-source specification audit",
        "source": {"url": URL, "bytes": len(raw), "sha256": digest, "line_count": len(lines)},
        "fixed_form": {
            "statement_count": len(statements),
            "comment_count": len(comments),
            "blank_count": len(blanks),
        },
        "open_statements": opens,
        "read_statements": reads,
        "write_statements": writes,
        "format_statements": formats,
        "declaration_statements": declarations,
        "relevant_comments": relevant_comments,
        "read_format_references": read_format_references,
        "format_labels": sorted(format_labels),
        "field_groups": field_groups,
        "shower_candidate_tokens_from_context": candidate_tokens,
        "shower_candidate_tokens_present_in_read": matching_shower_tokens,
        "literal_shower_identifier_in_read": literal_shower_read,
        "data_archive_urls_requested": [],
        "meteor_records_read": False,
        "label_values_read": False,
        "scientific_values_read": False,
        "sonotaco_2024_read": False,
        "camsv3_2016_values_read": False,
        "gates": gates,
        "verdict": verdict,
    }
    return result, raw


def write_outputs(out: Path, result: dict, raw: bytes | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (out / "reading.f").write_bytes(raw)
    (out / "reader_spec_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    report = [
        "# Historical CAMS Database 2.0 reader-specification audit",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
        f"- source bytes: {result.get('source', {}).get('bytes')}",
        f"- source SHA-256: `{result.get('source', {}).get('sha256')}`",
        f"- READ statements: {len(result.get('read_statements', []))}",
        f"- FORMAT statements: {len(result.get('format_statements', []))}",
        f"- shower candidates in data READ: {result.get('shower_candidate_tokens_present_in_read')}",
        "",
        "## Frozen gates",
        "",
    ]
    report.extend(f"- {name}: {passed}" for name, passed in result.get("gates", {}).items())
    if result.get("error"):
        report.extend(["", "## Execution error", "", f"`{result['error']}`"])
    report.extend(
        [
            "",
            "The exact public reader source is preserved. No CAMS data archive or meteor record was requested or opened.",
        ]
    )
    (out / "RESULT.md").write_text("\n".join(report) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    raw: bytes | None = None
    try:
        result, raw = build_result()
    except Exception as exc:
        result = {
            "method": "Historical CAMS Database 2.0 reader-source specification audit",
            "error": f"{type(exc).__name__}: {exc}",
            "data_archive_urls_requested": [],
            "meteor_records_read": False,
            "label_values_read": False,
            "scientific_values_read": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_READER_SPEC",
        }
    write_outputs(out, result, raw)
    print(json.dumps({
        "verdict": result["verdict"],
        "gates": result.get("gates"),
        "field_groups": result.get("field_groups"),
        "shower_read_tokens": result.get("shower_candidate_tokens_present_in_read"),
        "error": result.get("error"),
    }, indent=2))
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_READER_SPEC":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
