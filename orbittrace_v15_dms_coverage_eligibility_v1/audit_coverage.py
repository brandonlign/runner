#!/usr/bin/env python3
"""Coverage-only DMS1991-1998 eligibility audit.

Allowed scientific row values: Yr, Mn, Day, LS only.  Every other column is
structurally ignored.  Output is aggregate coverage metadata only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.request
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

OFFICIAL_VIDEO_PAGE = "https://ceres.ta3.sk/iaumdcdb/home/catalog/video"
ANCHOR_TEXT = "DMS1991-1998 - ZIP archive"
YEARS = tuple(range(1991, 1999))
SEALED_LOWER = 20.0
SEALED_UPPER = 55.0
MIN_ROWS = 80
MIN_BINS_10 = 12
MIN_QUADRANTS = 3
USER_AGENT = "OrbitTrace-DMS-coverage-audit/1.0"


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append(("".join(self._parts).strip(), self._href))
            self._href = None
            self._parts = []


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        require(200 <= int(response.status) < 300, f"HTTP status {response.status} for {url}")
        return response.read()


def discover_archive_url() -> tuple[str, str]:
    page = fetch(OFFICIAL_VIDEO_PAGE)
    parser = AnchorCollector()
    parser.feed(page.decode("utf-8", errors="strict"))
    matches = [href for text, href in parser.anchors if text == ANCHOR_TEXT]
    require(len(matches) == 1, f"expected exactly one official DMS archive link, got {len(matches)}")
    return urljoin(OFFICIAL_VIDEO_PAGE, matches[0]), sha256(page)


def decode_text(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise RuntimeError("DMS text member has no accepted deterministic encoding")


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def parse_header(line: str) -> tuple[str, list[str]]:
    candidates = (",", ";", "\t")
    parsed = [(delimiter, next(csv.reader([line], delimiter=delimiter))) for delimiter in candidates]
    delimiter, header = max(parsed, key=lambda pair: len(pair[1]))
    require(len(header) >= 4, "DMS text member header is not a supported delimited table")
    return delimiter, header


def resolve_allowed_indices(header: list[str]) -> dict[str, int]:
    aliases = {
        "year": {"yr", "year"},
        "month": {"mn", "month"},
        "day": {"day"},
        "solar_longitude": {"ls", "solarlongitude", "solarlon"},
    }
    normalized = [normalized_header(value) for value in header]
    resolved: dict[str, int] = {}
    for concept, names in aliases.items():
        matches = [index for index, name in enumerate(normalized) if name in names]
        require(len(matches) == 1, f"could not uniquely resolve allowed DMS field {concept}")
        resolved[concept] = matches[0]
    require(len(set(resolved.values())) == 4, "allowed DMS fields do not resolve to four distinct columns")
    return resolved


def choose_data_member(archive: bytes) -> tuple[str, bytes, str, list[str], dict[str, int]]:
    candidates: list[tuple[str, bytes, str, list[str], dict[str, int]]] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        for info in zf.infolist():
            if info.is_dir() or info.file_size <= 0:
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".csv", ".txt", ".dat"}:
                continue
            raw = zf.read(info.filename)
            text, encoding = decode_text(raw)
            first_line = text.splitlines()[0] if text.splitlines() else ""
            if not first_line:
                continue
            try:
                _delimiter, header = parse_header(first_line)
                resolved = resolve_allowed_indices(header)
            except RuntimeError:
                continue
            candidates.append((info.filename, raw, encoding, header, resolved))
    require(len(candidates) == 1, f"expected exactly one DMS tabular member with allowed schema, got {len(candidates)}")
    return candidates[0]


def finite_float(value: str, concept: str) -> float:
    try:
        number = float(value.strip())
    except ValueError as exc:
        raise RuntimeError(f"invalid {concept} value in coverage-only DMS row") from exc
    require(math.isfinite(number), f"non-finite {concept} value in coverage-only DMS row")
    return number


def parse_coverage(raw: bytes, encoding: str, header: list[str], indices: dict[str, int]) -> dict[int, dict[str, Any]]:
    text = raw.decode(encoding)
    first_line = text.splitlines()[0]
    delimiter, parsed_header = parse_header(first_line)
    require(parsed_header == header, "DMS header changed between member selection and parse")
    max_index = max(indices.values())
    counts = {year: 0 for year in YEARS}
    bins = {year: set() for year in YEARS}
    quadrants = {year: set() for year in YEARS}

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    next(reader)
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue
        require(len(row) > max_index, "short DMS row in allowed-field parser")
        # Only the four preregistered coverage fields are interpreted.
        year_f = finite_float(row[indices["year"]], "year")
        month_f = finite_float(row[indices["month"]], "month")
        day_f = finite_float(row[indices["day"]], "day")
        ls = finite_float(row[indices["solar_longitude"]], "solar longitude") % 360.0
        year = int(round(year_f))
        require(abs(year_f - year) <= 1e-9, "non-integral DMS year")
        month = int(round(month_f))
        require(abs(month_f - month) <= 1e-9 and 1 <= month <= 12, "invalid DMS month")
        require(0.0 < day_f < 32.0, "invalid DMS day")
        if year not in counts:
            continue
        if SEALED_LOWER <= ls <= SEALED_UPPER:
            # Intentionally no counter/statistic is updated or emitted for sealed rows.
            continue
        counts[year] += 1
        bins[year].add(int(math.floor(ls / 10.0)) % 36)
        quadrants[year].add(int(math.floor(ls / 90.0)) % 4)

    result: dict[int, dict[str, Any]] = {}
    for year in YEARS:
        row_count = counts[year]
        bin_count = len(bins[year])
        quadrant_count = len(quadrants[year])
        gates = {
            "usable_rows_at_least_80": row_count >= MIN_ROWS,
            "occupied_10deg_bins_at_least_12": bin_count >= MIN_BINS_10,
            "occupied_quadrants_at_least_3": quadrant_count >= MIN_QUADRANTS,
        }
        result[year] = {
            "usable_target_excluded_rows": row_count,
            "occupied_10deg_bin_count": bin_count,
            "occupied_quadrant_count": quadrant_count,
            "gates": gates,
            "eligible": all(gates.values()),
        }
    return result


def choose_pair(years: dict[int, dict[str, Any]]) -> tuple[int, int] | None:
    candidates: list[tuple[tuple[int, int, int, int, int], tuple[int, int]]] = []
    for first in range(1991, 1998):
        second = first + 1
        if not (years[first]["eligible"] and years[second]["eligible"]):
            continue
        bins1, bins2 = int(years[first]["occupied_10deg_bin_count"]), int(years[second]["occupied_10deg_bin_count"])
        rows1, rows2 = int(years[first]["usable_target_excluded_rows"]), int(years[second]["usable_target_excluded_rows"])
        # Maximize the first four quantities; final -first makes earlier pair win exact ties.
        score = (min(bins1, bins2), min(rows1, rows2), bins1 + bins2, rows1 + rows2, -first)
        candidates.append((score, (first, second)))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_url, page_sha = discover_archive_url()
    archive = fetch(archive_url)
    require(archive[:4] == b"PK\x03\x04", "official DMS payload is not a ZIP archive")
    member_name, member_raw, encoding, header, indices = choose_data_member(archive)
    coverage = parse_coverage(member_raw, encoding, header, indices)
    pair = choose_pair(coverage)
    verdict = "ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE" if pair is not None else "INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR"

    output = {
        "verdict": verdict,
        "catalogue": "DMS1991-1998",
        "official_video_page": OFFICIAL_VIDEO_PAGE,
        "official_video_page_sha256": page_sha,
        "archive_sha256": sha256(archive),
        "archive_bytes": len(archive),
        "member_basename": Path(member_name).name,
        "member_sha256": sha256(member_raw),
        "member_bytes": len(member_raw),
        "text_encoding": encoding,
        "allowed_fields_resolved": {
            concept: header[index] for concept, index in sorted(indices.items())
        },
        "year_gates": {
            "minimum_target_excluded_rows": MIN_ROWS,
            "minimum_occupied_10deg_bins": MIN_BINS_10,
            "minimum_occupied_quadrants": MIN_QUADRANTS,
            "consecutive_pair_required": True,
        },
        "years": {str(year): coverage[year] for year in YEARS},
        "reserved_pair": list(pair) if pair is not None else None,
        "sealed_interval": "20deg-55deg inclusive; rows ignored and exclusion count intentionally not emitted",
        "scientific_fields_accessed": False,
        "radiant_accessed": False,
        "velocity_accessed": False,
        "orbital_elements_accessed": False,
        "shower_labels_accessed": False,
        "v15_executed": False,
        "comparators_executed": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "orbittrace_target_information_access": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
