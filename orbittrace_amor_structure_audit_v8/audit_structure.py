#!/usr/bin/env python3
"""Structure-only audit of official IAU MDC AMOR 1990-1999 annual ZIPs.

This program deliberately never converts a meteor-field token to a number and never
stores a data row. It inspects only transport/archive/schema/record-count metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://ceres.ta3.sk/iaumdcdb/home/catalog/radio"
YEARS = tuple(range(1990, 2000))
KNOWN_HEADER_CODES = {
    "DB", "IC", "#IC", "ANo", "Yr", "Mn", "Day", "LS", "mv", "HB", "HM", "HE",
    "RA", "DEC", "Vi", "Vg", "Vh", "cZ", "Qm", "q", "e", "1/a", "a", "Q", "i",
    "arg", "nod", "pi", "Sh", "Mas", "lgM", "cor", "crh", "mr", "Hrf", "LpA",
    "yr", "mn", "day",
}
TEXT_EXTENSIONS = {".csv", ".txt", ".dat", ".1l", ".d18", ".asc", ".tab"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--freshness-json", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def discover_links(session: requests.Session) -> dict[int, str]:
    response = session.get(INDEX_URL, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    found: dict[int, str] = {}
    for anchor in soup.find_all("a", href=True):
        text = " ".join(anchor.get_text(" ", strip=True).split())
        match = re.fullmatch(r"AMOR\s+(199[0-9])\s+-\s+ZIP\s+archive", text, re.I)
        if not match:
            continue
        year = int(match.group(1))
        found[year] = urljoin(INDEX_URL, str(anchor["href"]))
    require(sorted(found) == list(YEARS), f"official AMOR annual-link set changed: {sorted(found)}")
    return found


def choose_delimiter(line: bytes) -> str:
    if line.count(b",") >= 2:
        return "comma"
    if line.count(b"\t") >= 2:
        return "tab"
    return "whitespace"


def split_tokens(line: bytes, delimiter: str) -> list[bytes]:
    if delimiter == "comma":
        return [x.strip() for x in line.split(b",")]
    if delimiter == "tab":
        return [x.strip() for x in line.split(b"\t")]
    return line.split()


def safe_header_tokens(tokens: list[bytes]) -> list[str] | None:
    decoded = [t.decode("utf-8", errors="replace").strip() for t in tokens]
    recognized = sum(token in KNOWN_HEADER_CODES for token in decoded)
    if len(decoded) >= 4 and recognized >= 4 and recognized / len(decoded) >= 0.40:
        return decoded
    return None


def audit_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    suffix = Path(info.filename).suffix.lower()
    # Unknown extensions are still scanned as opaque text unless they are common binary containers.
    text_like = suffix in TEXT_EXTENSIONS or suffix not in {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}
    if not text_like:
        return {
            "name": info.filename,
            "file_size": int(info.file_size),
            "compress_size": int(info.compress_size),
            "crc": int(info.CRC),
            "text_like": False,
        }

    digest = hashlib.sha256()
    nonempty = 0
    total_lines = 0
    first_nonempty: bytes | None = None
    delimiter: str | None = None
    width_counts: Counter[int] = Counter()
    header_tokens: list[str] | None = None

    with zf.open(info, "r") as fh:
        for raw_line in fh:
            digest.update(raw_line)
            total_lines += 1
            stripped = raw_line.strip()
            if not stripped:
                continue
            nonempty += 1
            if first_nonempty is None:
                first_nonempty = stripped
                delimiter = choose_delimiter(stripped)
                first_tokens = split_tokens(stripped, delimiter)
                header_tokens = safe_header_tokens(first_tokens)
                width_counts[len(first_tokens)] += 1
            else:
                assert delimiter is not None
                width_counts[len(split_tokens(stripped, delimiter))] += 1

    header_lines = 1 if header_tokens is not None and nonempty > 0 else 0
    return {
        "name": info.filename,
        "file_size": int(info.file_size),
        "compress_size": int(info.compress_size),
        "crc": int(info.CRC),
        "text_like": True,
        "sha256": digest.hexdigest(),
        "total_line_count": total_lines,
        "nonempty_line_count": nonempty,
        "header_detected": header_tokens is not None,
        "header_tokens": header_tokens,
        "delimiter_class": delimiter,
        "token_width_counts": {str(k): int(v) for k, v in sorted(width_counts.items())},
        "opaque_data_record_count": max(0, nonempty - header_lines),
        "scientific_token_conversion_performed": False,
        "data_row_content_persisted": False,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(os.environ.get("ALLOW_AMOR_STRUCTURE_AUDIT") == "1", "AMOR structure-audit execution not authorized")

    freshness = json.loads(args.freshness_json.read_text())
    v8 = json.loads(args.v8_result_json.read_text())
    require(freshness["verdict"] == "PASS_AMOR_1990_1999_REPO_SCIENTIFIC_FRESHNESS_AUDIT", "AMOR freshness prerequisite failed")
    require(int(freshness["potential_exposure_hit_count"]) == 0, "AMOR freshness pool is not clean")
    require(v8["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 did not pass; AMOR archive access prohibited")
    require(all(v8["integrity_gates"].values()) and all(v8["scientific_gates"].values()), "v8 gates not all pass")
    require("No OrbitTrace target information" in v8["claim_boundary"], "v8 claim boundary changed")

    session = requests.Session()
    session.headers.update({"User-Agent": "OrbitTrace-structure-audit/1.0"})
    links = discover_links(session)

    archive_rows: list[dict] = []
    for year in YEARS:
        url = links[year]
        response = session.get(url, timeout=180)
        response.raise_for_status()
        payload = response.content
        require(payload, f"empty AMOR archive {year}")
        archive_sha = hashlib.sha256(payload).hexdigest()
        require(zipfile.is_zipfile(io.BytesIO(payload)), f"AMOR {year} is not a ZIP")
        with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
            infos = [info for info in zf.infolist() if not info.is_dir()]
            require(infos, f"AMOR {year} ZIP has no members")
            members = [audit_member(zf, info) for info in infos]
        text_members = [m for m in members if m.get("text_like") and int(m.get("nonempty_line_count", 0)) > 0]
        require(text_members, f"AMOR {year} has no non-empty text-like member")
        record_count = int(sum(int(m.get("opaque_data_record_count", 0)) for m in text_members))
        require(record_count > 0, f"AMOR {year} opaque record count is zero")
        archive_rows.append({
            "year": year,
            "url": url,
            "archive_size": len(payload),
            "archive_sha256": archive_sha,
            "member_count": len(members),
            "members": members,
            "opaque_data_record_count": record_count,
        })
        print(f"AMOR structure {year}: members={len(members)} opaque_records={record_count}", flush=True)

    selected = sorted(archive_rows, key=lambda row: (-int(row["opaque_data_record_count"]), int(row["year"])))[:2]
    selected_years = [int(row["year"]) for row in selected]
    require(len(selected_years) == 2 and selected_years[0] != selected_years[1], "panel selection failed")

    result = {
        "verdict": "PASS_AMOR_1990_1999_STRUCTURE_AUDIT",
        "index_url": INDEX_URL,
        "years": list(YEARS),
        "archives": archive_rows,
        "selection_rule": "two years with largest opaque data-record counts; ties resolved by earlier year",
        "selected_years": selected_years,
        "catalogue_archive_access": True,
        "scientific_value_interpretation": False,
        "scientific_token_conversion_performed": False,
        "data_row_content_persisted": False,
        "detector_or_family_evaluation_performed": False,
        "target_information_access": False,
        "claim_boundary": "Structure-only AMOR transport audit. Archive bytes were opened only to establish immutable transport/schema/record-count metadata. No meteor-field token was converted to a scientific value and no method endpoint was computed.",
    }
    args.output.joinpath("amor_1990_1999_structure_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("AMOR_1990_1999_STRUCTURE_AUDIT.md").write_text(
        "# AMOR 1990–1999 structure-only audit\n\n"
        f"**Verdict:** `{result['verdict']}`\n\n"
        f"Selected panel by frozen opaque-count rule: **{selected_years[0]} + {selected_years[1]}**.\n\n"
        "No meteor scientific value, detector score, or OrbitTrace target information was interpreted.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
