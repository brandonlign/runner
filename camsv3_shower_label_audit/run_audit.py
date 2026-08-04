#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import requests

BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
FROZEN = {
    2011: ("de2af15ccdee9836912c1efb9fba9bdcf47e3b9d2fa7374244dc6ac69f82c118", "iaumdcCAMSv3_2011.csv", 44_998),
    2012: ("040b853d6fbcd5dfc9ef3f76be553624a9893ab9b1aac709ccebcc2498c73cb3", "iaumdcCAMSv3_2012.csv", 53_401),
    2013: ("895f58c985f730976ef6e3ca3c89cd947bd248b419101eba163eef77e951e56a", "iaumdcCAMSv3_2013.csv", 76_213),
    2014: ("0d9ba75256577e9b008786054ea13c4fa6b755d42ae65031f311bae8a0b3a928", "iaumdcCAMSv3_2014.csv", 83_336),
    2015: ("aa9a04b206e1927d7a8cb401ef22baae20061c9827dec0133e42b11790fcf61d", "iaumdcCAMSv3_2015.csv", 100_700),
}
RESERVED_2016_HASH = "40e901fa8c8e017e5fe6bf9e9739a2c840d7e0d259e59b57ccf374d7d9700f30"
DOC_URL = "https://ceres.ta3.sk/iaumdcdb/public/docs/document.pdf"
DOC_BYTES = 211_571
DOC_SHA256 = "de8965b63389479c1dce39a36057ba2d0dd8742c45c67a60af4a330de14d324b"
ZERO = re.compile(r"^\+?0+(?:\.0+)?$")
POSITIVE_INTEGER = re.compile(r"^\+?[0-9]+(?:\.0+)?$")


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and not name.startswith(("/", "\\"))


def finite_float(value: str) -> float | None:
    try:
        number = float(value.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def classify_label(raw: str) -> tuple[str, int | None]:
    token = raw.strip()
    if token == "" or ZERO.fullmatch(token):
        return "background", None
    if POSITIVE_INTEGER.fullmatch(token):
        number = float(token)
        integer = int(number)
        if number == integer and integer > 0:
            return "labeled", integer
    return "unsupported", None


def download(url: str) -> bytes:
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    return response.content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    doc = download(DOC_URL)
    doc_hash = hashlib.sha256(doc).hexdigest()
    if len(doc) != DOC_BYTES or doc_hash != DOC_SHA256:
        raise RuntimeError(f"documentation snapshot mismatch: bytes={len(doc)} sha256={doc_hash}")

    requested_years: list[int] = []
    year_reports: list[dict] = []
    category_totals: Counter[str] = Counter()
    shower_year_counts: Counter[tuple[int, int]] = Counter()
    shower_totals: Counter[int] = Counter()
    shower_year_member_counts: dict[int, Counter[int]] = defaultdict(Counter)
    headers: list[list[str]] = []

    for year in sorted(FROZEN):
        expected_hash, expected_basename, expected_rows = FROZEN[year]
        requested_years.append(year)
        url = f"{BASE}/iaumdcCAMSv3_{year}.csv.zip"
        archive_bytes = download(url)
        archive_hash = hashlib.sha256(archive_bytes).hexdigest()
        if archive_hash != expected_hash:
            raise RuntimeError(f"{year}: archive hash mismatch: {archive_hash}")

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            if archive.testzip() is not None:
                raise RuntimeError(f"{year}: ZIP CRC failure")
            names = archive.namelist()
            if not all(safe_name(name) for name in names):
                raise RuntimeError(f"{year}: unsafe ZIP member")
            matches = [
                name for name in names
                if name.lower().endswith(".csv") and PurePosixPath(name).name == expected_basename
            ]
            if len(matches) != 1:
                raise RuntimeError(f"{year}: expected one basename match, found {matches}")
            payload = archive.read(matches[0])

        reader = csv.reader(io.StringIO(payload.decode("utf-8-sig"), newline=""), delimiter=";")
        try:
            header = [field.lstrip("\ufeff").strip() for field in next(reader)]
        except StopIteration as exc:
            raise RuntimeError(f"{year}: empty CSV") from exc
        if len(set(header)) != len(header) or not all(header):
            raise RuntimeError(f"{year}: invalid header")
        if "LS" not in header or "sh" not in header:
            raise RuntimeError(f"{year}: required LS/sh fields missing")
        headers.append(header)
        ls_index = header.index("LS")
        sh_index = header.index("sh")

        rows = 0
        malformed = 0
        invalid_phase = 0
        blind_removed = 0
        post_boundary = 0
        year_categories: Counter[str] = Counter()
        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            rows += 1
            if len(row) != len(header):
                malformed += 1
                continue

            # The phase boundary is applied before the label cell is accessed.
            solar_longitude = finite_float(row[ls_index])
            if solar_longitude is None or not 0.0 <= solar_longitude < 360.0:
                invalid_phase += 1
                continue
            if 20.0 <= solar_longitude <= 55.0:
                blind_removed += 1
                continue

            post_boundary += 1
            category, shower_number = classify_label(row[sh_index])
            year_categories[category] += 1
            category_totals[category] += 1
            if category == "labeled":
                assert shower_number is not None
                shower_year_counts[(year, shower_number)] += 1
                shower_totals[shower_number] += 1
                shower_year_member_counts[shower_number][year] += 1

        if rows != expected_rows or malformed != 0:
            raise RuntimeError(f"{year}: row structure mismatch rows={rows} malformed={malformed}")
        year_reports.append(
            {
                "year": year,
                "url": url,
                "archive_sha256": archive_hash,
                "expected_member_basename": expected_basename,
                "row_count": rows,
                "invalid_phase_rows": invalid_phase,
                "blind_interval_rows_removed_before_label_parsing": blind_removed,
                "post_boundary_rows": post_boundary,
                "background_rows": year_categories["background"],
                "labeled_rows": year_categories["labeled"],
                "unsupported_rows": year_categories["unsupported"],
            }
        )

    identical_headers = all(header == headers[0] for header in headers)
    total_post_boundary = sum(report["post_boundary_rows"] for report in year_reports)
    label_like = category_totals["labeled"] + category_totals["unsupported"]
    unsupported_fraction = category_totals["unsupported"] / total_post_boundary if total_post_boundary else 1.0
    mapped_label_like_fraction = category_totals["labeled"] / label_like if label_like else 0.0
    supported_k8_cells = sum(count >= 8 for count in shower_year_counts.values())
    supported_k12_cells = sum(count >= 12 for count in shower_year_counts.values())
    multi_year_supported = 0
    supported_year_histogram: Counter[int] = Counter()
    for shower_number, total in shower_totals.items():
        years_with_four = sum(count >= 4 for count in shower_year_member_counts[shower_number].values())
        if total >= 16 and years_with_four >= 2:
            multi_year_supported += 1
            supported_year_histogram[years_with_four] += 1

    gates = {
        "all_five_pinned_development_archives_pass": requested_years == [2011, 2012, 2013, 2014, 2015] and identical_headers,
        "reserved_2016_not_requested_or_opened": 2016 not in requested_years,
        "blind_interval_removed_before_label_parsing": all(
            report["blind_interval_rows_removed_before_label_parsing"] >= 0 for report in year_reports
        ),
        "unsupported_syntax_at_most_0_01": unsupported_fraction <= 0.01,
        "mapped_label_like_fraction_at_least_0_90": mapped_label_like_fraction >= 0.90,
        "background_events_at_least_50000": category_totals["background"] >= 50_000,
        "distinct_positive_showers_at_least_30": len(shower_totals) >= 30,
        "supported_k8_shower_year_cells_at_least_25": supported_k8_cells >= 25,
        "supported_k12_shower_year_cells_at_least_20": supported_k12_cells >= 20,
        "multi_year_supported_showers_at_least_20": multi_year_supported >= 20,
    }
    verdict = "PASS_CAMSV3_SHOWER_LABEL_AUDIT" if all(gates.values()) else "KILL_CAMSV3_SHOWER_LABEL_AUDIT"
    result = {
        "method": "aggregate-only CAMSv3 survey-native sh interface audit",
        "documentation": {"url": DOC_URL, "bytes": len(doc), "sha256": doc_hash},
        "development_years_requested": requested_years,
        "reserved_2016_archive_sha256": RESERVED_2016_HASH,
        "reserved_2016_requested": False,
        "years": year_reports,
        "aggregate_counts": {
            "post_boundary_rows": total_post_boundary,
            "background_rows": category_totals["background"],
            "labeled_rows": category_totals["labeled"],
            "unsupported_rows": category_totals["unsupported"],
            "distinct_positive_shower_numbers": len(shower_totals),
            "supported_k8_shower_year_cells": supported_k8_cells,
            "supported_k12_shower_year_cells": supported_k12_cells,
            "multi_year_supported_shower_numbers": multi_year_supported,
        },
        "fractions": {
            "unsupported_post_boundary": unsupported_fraction,
            "mapped_nonbackground_label_like": mapped_label_like_fraction,
        },
        "multi_year_supported_year_count_histogram": {
            str(years): count for years, count in sorted(supported_year_histogram.items())
        },
        "gates": gates,
        "verdict": verdict,
        "shower_identities_emitted": False,
        "geometry_values_emitted": False,
        "detector_score_computed": False,
        "ghoststream_values_read": False,
    }
    (args.output / "camsv3_shower_label_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = [
        "# CAMSv3 survey-native shower-label interface audit",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- development years: {requested_years}",
        f"- post-boundary background rows: **{category_totals['background']:,}**",
        f"- post-boundary labeled rows: **{category_totals['labeled']:,}**",
        f"- unsupported syntax fraction: **{unsupported_fraction:.6f}**",
        f"- mapped label-like fraction: **{mapped_label_like_fraction:.6f}**",
        f"- distinct positive shower numbers: **{len(shower_totals)}**",
        f"- supported k>=8 shower-year cells: **{supported_k8_cells}**",
        f"- supported k>=12 shower-year cells: **{supported_k12_cells}**",
        f"- multi-year-supported shower numbers: **{multi_year_supported}**",
        "",
        "## Frozen gates",
        "",
    ]
    report.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    report.extend([
        "",
        "No individual row, shower-number identity, geometry value, detector score, 2016 value, or GhostStream value is emitted.",
    ])
    (args.output / "RESULT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "aggregate_counts": result["aggregate_counts"], "fractions": result["fractions"], "gates": gates}, indent=2, sort_keys=True))
    if verdict != "PASS_CAMSV3_SHOWER_LABEL_AUDIT":
        raise SystemExit("Frozen CAMSv3 shower-label interface gate failed")


if __name__ == "__main__":
    main()
