#!/usr/bin/env python3
"""Coverage-only DMS1991-1998 eligibility audit.

Allowed scientific row values: Yr, Mn, Day, LS only. Every other column is
structurally ignored. Output is aggregate coverage metadata only.
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
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

OFFICIAL_VIDEO_PAGE = "https://ceres.ta3.sk/iaumdcdb/home/catalog/video"
ANCHOR_TEXT = "DMS1991-1998 - ZIP archive"
YEARS = tuple(range(1991, 1999))
OFFICIAL_ORBIT_COUNT = 908
SEALED_LOWER = 20.0
SEALED_UPPER = 55.0
MIN_ROWS = 80
MIN_BINS_10 = 12
MIN_QUADRANTS = 3
USER_AGENT = "OrbitTrace-DMS-coverage-audit/1.0"
HEADER_SCAN_LIMIT = 128
DELIMITERS = (",", ";", "\t")
# Current official MDC parameter ordering begins DB, IC, Ano, Yr, Mn, Day, delta_Day, LS, ...
OFFICIAL_ORDER_INDICES = {"year": 3, "month": 4, "day": 5, "solar_longitude": 7}


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


def parse_header_with_delimiter(line: str, delimiter: str) -> list[str]:
    return next(csv.reader([line], delimiter=delimiter))


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


def find_allowed_header_or_none(text: str) -> tuple[int, str, list[str], dict[str, int]] | None:
    """Find one allowed-field header in an initial metadata/preamble region.

    The scan interprets only column-name strings. It never parses an event-row value.
    """
    lines = text.splitlines()
    matches: list[tuple[int, str, list[str], dict[str, int]]] = []
    for line_index, line in enumerate(lines[:HEADER_SCAN_LIMIT]):
        if not line.strip():
            continue
        for delimiter in DELIMITERS:
            header = parse_header_with_delimiter(line, delimiter)
            if len(header) < 4:
                continue
            try:
                resolved = resolve_allowed_indices(header)
            except RuntimeError:
                continue
            matches.append((line_index, delimiter, header, resolved))
    by_line: dict[int, list[tuple[int, str, list[str], dict[str, int]]]] = {}
    for match in matches:
        by_line.setdefault(match[0], []).append(match)
    if not by_line:
        return None
    require(len(by_line) == 1, f"expected at most one DMS header line with allowed schema, got {len(by_line)}")
    line_matches = next(iter(by_line.values()))
    max_width = max(len(match[2]) for match in line_matches)
    widest = [match for match in line_matches if len(match[2]) == max_width]
    require(len(widest) == 1, "DMS allowed header delimiter is ambiguous")
    return widest[0]


def find_allowed_header(text: str) -> tuple[int, str, list[str], dict[str, int]]:
    """Public helper retained for synthetic named-header tests."""
    found = find_allowed_header_or_none(text)
    require(found is not None, "no DMS named header with allowed schema")
    return found


def finite_float(value: str, concept: str) -> float:
    try:
        number = float(value.strip())
    except ValueError as exc:
        raise RuntimeError(f"invalid {concept} value in coverage-only DMS row") from exc
    require(math.isfinite(number), f"non-finite {concept} value in coverage-only DMS row")
    return number


def parse_allowed_values(row: list[str], indices: dict[str, int], *, require_dms_year: bool) -> tuple[int, int, float, float]:
    """Interpret only Yr/Mn/Day/LS. No other cell is converted or compared."""
    max_index = max(indices.values())
    require(len(row) > max_index, "short DMS row in allowed-field parser")
    year_f = finite_float(row[indices["year"]], "year")
    month_f = finite_float(row[indices["month"]], "month")
    day_f = finite_float(row[indices["day"]], "day")
    ls = finite_float(row[indices["solar_longitude"]], "solar longitude") % 360.0
    year = int(round(year_f))
    require(abs(year_f - year) <= 1e-9, "non-integral DMS year")
    month = int(round(month_f))
    require(abs(month_f - month) <= 1e-9 and 1 <= month <= 12, "invalid DMS month")
    require(0.0 < day_f < 32.0, "invalid DMS day")
    if require_dms_year:
        require(year in YEARS, "headerless official-order row year outside public DMS 1991-1998 span")
    return year, month, day_f, ls


def parse_rows_from_line(text: str, start_line_index: int, delimiter: str) -> list[list[str]]:
    lines = text.splitlines()
    require(0 <= start_line_index <= len(lines), "DMS data-start line out of range")
    data_text = "\n".join(lines[start_line_index:])
    return [row for row in csv.reader(io.StringIO(data_text, newline=""), delimiter=delimiter) if row and any(cell.strip() for cell in row)]


def find_headerless_official_order(text: str) -> tuple[int, str, int, dict[str, int]] | None:
    """Find one headerless official-order table using only row width and allowed fields.

    No non-allowed cell value is interpreted. Exact 908-row cardinality is already-public
    catalogue metadata and is used only as a structural identity check.
    """
    lines = text.splitlines()
    candidates: list[tuple[int, str, int, dict[str, int]]] = []
    max_start = min(HEADER_SCAN_LIMIT, len(lines))
    for start_line_index in range(max_start):
        for delimiter in DELIMITERS:
            rows = parse_rows_from_line(text, start_line_index, delimiter)
            if len(rows) != OFFICIAL_ORBIT_COUNT:
                continue
            widths = {len(row) for row in rows}
            if len(widths) != 1:
                continue
            width = next(iter(widths))
            if width <= max(OFFICIAL_ORDER_INDICES.values()):
                continue
            try:
                for row in rows:
                    parse_allowed_values(row, OFFICIAL_ORDER_INDICES, require_dms_year=True)
            except RuntimeError:
                continue
            candidates.append((start_line_index, delimiter, width, dict(OFFICIAL_ORDER_INDICES)))
    if not candidates:
        return None
    require(len(candidates) == 1, f"headerless official-order DMS schema is ambiguous across {len(candidates)} candidates")
    return candidates[0]


def choose_data_member(archive: bytes) -> dict[str, Any]:
    named_candidates: list[dict[str, Any]] = []
    headerless_candidates: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        for info in zf.infolist():
            if info.is_dir() or info.file_size <= 0:
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".csv", ".txt", ".dat"}:
                continue
            raw = zf.read(info.filename)
            text, encoding = decode_text(raw)
            named = find_allowed_header_or_none(text)
            if named is not None:
                line_index, delimiter, header, resolved = named
                named_candidates.append({
                    "mode": "named_header",
                    "member_name": info.filename,
                    "raw": raw,
                    "encoding": encoding,
                    "data_start_line_index": line_index + 1,
                    "header_line_index": line_index,
                    "delimiter": delimiter,
                    "header": header,
                    "indices": resolved,
                    "row_width": len(header),
                })
                continue
            headerless = find_headerless_official_order(text)
            if headerless is not None:
                start_line_index, delimiter, width, resolved = headerless
                headerless_candidates.append({
                    "mode": "headerless_official_order",
                    "member_name": info.filename,
                    "raw": raw,
                    "encoding": encoding,
                    "data_start_line_index": start_line_index,
                    "header_line_index": None,
                    "delimiter": delimiter,
                    "header": None,
                    "indices": resolved,
                    "row_width": width,
                })
    if named_candidates:
        require(len(named_candidates) == 1, f"expected exactly one DMS named-header data member, got {len(named_candidates)}")
        require(not headerless_candidates, "named-header and headerless DMS candidates coexist ambiguously")
        return named_candidates[0]
    require(len(headerless_candidates) == 1, f"expected exactly one headerless official-order DMS data member, got {len(headerless_candidates)}")
    return headerless_candidates[0]


def parse_coverage(schema: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], int]:
    raw = schema["raw"]
    encoding = schema["encoding"]
    start_line_index = int(schema["data_start_line_index"])
    delimiter = str(schema["delimiter"])
    indices = dict(schema["indices"])
    text = raw.decode(encoding)
    rows = parse_rows_from_line(text, start_line_index, delimiter)
    if schema["mode"] == "headerless_official_order":
        require(len(rows) == OFFICIAL_ORBIT_COUNT, "headerless DMS parsed-row count changed after schema selection")
        require({len(row) for row in rows} == {int(schema["row_width"])}, "headerless DMS row width changed after schema selection")
    counts = {year: 0 for year in YEARS}
    bins = {year: set() for year in YEARS}
    quadrants = {year: set() for year in YEARS}

    for row in rows:
        year, _month, _day, ls = parse_allowed_values(
            row,
            indices,
            require_dms_year=(schema["mode"] == "headerless_official_order"),
        )
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
    return result, len(rows)


def choose_pair(years: dict[int, dict[str, Any]]) -> tuple[int, int] | None:
    candidates: list[tuple[tuple[int, int, int, int, int], tuple[int, int]]] = []
    for first in range(1991, 1998):
        second = first + 1
        if not (years[first]["eligible"] and years[second]["eligible"]):
            continue
        bins1, bins2 = int(years[first]["occupied_10deg_bin_count"]), int(years[second]["occupied_10deg_bin_count"])
        rows1, rows2 = int(years[first]["usable_target_excluded_rows"]), int(years[second]["usable_target_excluded_rows"])
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
    schema = choose_data_member(archive)
    coverage, parsed_row_count = parse_coverage(schema)
    pair = choose_pair(coverage)
    verdict = "ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE" if pair is not None else "INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR"

    if schema["mode"] == "named_header":
        header = schema["header"]
        allowed_fields_resolved = {concept: header[index] for concept, index in sorted(schema["indices"].items())}
        header_physical_line: int | None = int(schema["header_line_index"]) + 1
    else:
        allowed_fields_resolved = {
            "year": "official_parameter_position_4_Yr",
            "month": "official_parameter_position_5_Mn",
            "day": "official_parameter_position_6_Day",
            "solar_longitude": "official_parameter_position_8_LS",
        }
        header_physical_line = None

    output = {
        "verdict": verdict,
        "catalogue": "DMS1991-1998",
        "official_video_page": OFFICIAL_VIDEO_PAGE,
        "official_video_page_sha256": page_sha,
        "archive_sha256": sha256(archive),
        "archive_bytes": len(archive),
        "member_basename": Path(schema["member_name"]).name,
        "member_sha256": sha256(schema["raw"]),
        "member_bytes": len(schema["raw"]),
        "text_encoding": schema["encoding"],
        "schema_mode": schema["mode"],
        "header_physical_line": header_physical_line,
        "row_width": int(schema["row_width"]),
        "parsed_row_count": parsed_row_count,
        "allowed_fields_resolved": allowed_fields_resolved,
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
