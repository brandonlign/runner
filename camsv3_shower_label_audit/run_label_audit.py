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
DOC_URL = "https://ceres.ta3.sk/iaumdcdb/public/docs/document.pdf"
DOC_BYTES = 211_571
DOC_SHA256 = "de8965b63389479c1dce39a36057ba2d0dd8742c45c67a60af4a330de14d324b"
FROZEN = {
    2011: ("de2af15ccdee9836912c1efb9fba9bdcf47e3b9d2fa7374244dc6ac69f82c118", "iaumdcCAMSv3_2011.csv", 44_998),
    2012: ("040b853d6fbcd5dfc9ef3f76be553624a9893ab9b1aac709ccebcc2498c73cb3", "iaumdcCAMSv3_2012.csv", 53_401),
    2013: ("895f58c985f730976ef6e3ca3c89cd947bd248b419101eba163eef77e951e56a", "iaumdcCAMSv3_2013.csv", 76_213),
    2014: ("0d9ba75256577e9b008786054ea13c4fa6b755d42ae65031f311bae8a0b3a928", "iaumdcCAMSv3_2014.csv", 83_336),
    2015: ("aa9a04b206e1927d7a8cb401ef22baae20061c9827dec0133e42b11790fcf61d", "iaumdcCAMSv3_2015.csv", 100_700),
}
RESERVED_YEAR = 2016
ZERO_RE = re.compile(r"^\+?0+(?:\.0+)?$")
INTEGER_RE = re.compile(r"^\+?[0-9]+(?:\.0+)?$")


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and not name.startswith(("/", "\\"))


def classify_label(raw: str) -> tuple[str, int | None]:
    token = raw.strip()
    if token == "" or ZERO_RE.fullmatch(token):
        return "background", None
    if INTEGER_RE.fullmatch(token):
        value = int(token.lstrip("+").split(".", 1)[0])
        if value > 0:
            return "labeled", value
    return "unsupported", None


def fetch_archive(year: int, requested_urls: list[str]) -> tuple[bytes, str, int]:
    expected_hash, expected_basename, expected_rows = FROZEN[year]
    url = f"{BASE}/iaumdcCAMSv3_{year}.csv.zip"
    requested_urls.append(url)
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_hash:
        raise RuntimeError(f"{year}: archive hash mismatch {digest}")
    return raw, expected_basename, expected_rows


def audit_year(
    year: int,
    requested_urls: list[str],
    label_year_counts: dict[int, Counter[int]],
) -> dict:
    raw, expected_basename, expected_rows = fetch_archive(year, requested_urls)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"{year}: ZIP CRC failure in {bad}")
        names = archive.namelist()
        if not all(safe_name(name) for name in names):
            raise RuntimeError(f"{year}: unsafe ZIP member path")
        matches = [
            name
            for name in names
            if name.lower().endswith(".csv") and PurePosixPath(name).name == expected_basename
        ]
        if len(matches) != 1:
            raise RuntimeError(f"{year}: expected one basename match, found {matches}")
        actual_member = matches[0]
        data = archive.read(actual_member)

    text = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", newline="")
    reader = csv.reader(text, delimiter=";")
    try:
        header = [field.lstrip("\ufeff").strip() for field in next(reader)]
    except StopIteration as exc:
        raise RuntimeError(f"{year}: empty CSV") from exc
    if "LS" not in header or "sh" not in header:
        raise RuntimeError(f"{year}: required fields missing")
    ls_index = header.index("LS")
    sh_index = header.index("sh")

    counts = Counter()
    row_count = 0
    malformed = 0
    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue
        row_count += 1
        if len(row) != len(header):
            malformed += 1
            continue
        try:
            phase = float(row[ls_index].strip())
        except (TypeError, ValueError):
            counts["invalid_phase"] += 1
            continue
        if not math.isfinite(phase) or not (0.0 <= phase < 360.0):
            counts["invalid_phase"] += 1
            continue
        if 20.0 <= phase <= 55.0:
            counts["blind_excluded"] += 1
            continue

        counts["post_boundary"] += 1
        category, shower_number = classify_label(row[sh_index])
        counts[category] += 1
        if category == "labeled":
            assert shower_number is not None
            label_year_counts[shower_number][year] += 1

    if row_count != expected_rows:
        raise RuntimeError(f"{year}: row count {row_count} != {expected_rows}")
    if malformed != 0:
        raise RuntimeError(f"{year}: malformed rows {malformed}")

    return {
        "year": year,
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "archive_bytes": len(raw),
        "member_basename": expected_basename,
        "actual_member_path": actual_member,
        "row_count": row_count,
        "invalid_phase_rows": counts["invalid_phase"],
        "blind_interval_rows": counts["blind_excluded"],
        "post_boundary_rows": counts["post_boundary"],
        "background_rows": counts["background"],
        "labeled_rows": counts["labeled"],
        "unsupported_rows": counts["unsupported"],
    }


def build_result() -> dict:
    requested_urls: list[str] = []
    doc_response = requests.get(DOC_URL, timeout=300)
    doc_response.raise_for_status()
    doc_raw = doc_response.content
    doc_hash = hashlib.sha256(doc_raw).hexdigest()
    doc_ok = len(doc_raw) == DOC_BYTES and doc_hash == DOC_SHA256
    if not doc_ok:
        raise RuntimeError(f"documentation snapshot mismatch: bytes={len(doc_raw)} sha256={doc_hash}")

    label_year_counts: dict[int, Counter[int]] = defaultdict(Counter)
    years = [audit_year(year, requested_urls, label_year_counts) for year in sorted(FROZEN)]

    totals = Counter()
    for item in years:
        totals["rows"] += item["row_count"]
        totals["invalid_phase"] += item["invalid_phase_rows"]
        totals["blind_excluded"] += item["blind_interval_rows"]
        totals["post_boundary"] += item["post_boundary_rows"]
        totals["background"] += item["background_rows"]
        totals["labeled"] += item["labeled_rows"]
        totals["unsupported"] += item["unsupported_rows"]

    distinct = len(label_year_counts)
    supported_k8_cells = sum(
        count >= 8 for yearly in label_year_counts.values() for count in yearly.values()
    )
    supported_k12_cells = sum(
        count >= 12 for yearly in label_year_counts.values() for count in yearly.values()
    )
    multi_year_supported = 0
    represented_year_histogram: Counter[int] = Counter()
    for yearly in label_year_counts.values():
        represented = sum(count >= 4 for count in yearly.values())
        total = sum(yearly.values())
        if total >= 16 and represented >= 2:
            multi_year_supported += 1
            represented_year_histogram[represented] += 1

    label_like = totals["labeled"] + totals["unsupported"]
    mapping_fraction = totals["labeled"] / label_like if label_like else 0.0
    unsupported_fraction = totals["unsupported"] / totals["post_boundary"] if totals["post_boundary"] else 1.0
    reserved_requested = any(f"_{RESERVED_YEAR}." in url for url in requested_urls)

    gates = {
        "five_pinned_development_archives_pass": len(years) == 5,
        "reserved_2016_not_requested": not reserved_requested,
        "blind_rows_excluded_before_label_parsing": totals["blind_excluded"] > 0,
        "unsupported_fraction_at_most_0_01": unsupported_fraction <= 0.01,
        "positive_integer_mapping_fraction_at_least_0_90": mapping_fraction >= 0.90,
        "background_at_least_50000": totals["background"] >= 50_000,
        "distinct_positive_shower_numbers_at_least_30": distinct >= 30,
        "supported_k8_shower_year_cells_at_least_25": supported_k8_cells >= 25,
        "supported_k12_shower_year_cells_at_least_20": supported_k12_cells >= 20,
        "multi_year_supported_showers_at_least_20": multi_year_supported >= 20,
        "documentation_snapshot_verified": doc_ok,
    }
    verdict = "PASS_CAMSV3_SHOWER_LABEL_INTERFACE" if all(gates.values()) else "KILL_CAMSV3_SHOWER_LABEL_INTERFACE"
    return {
        "method": "CAMSv3 aggregate-only survey-native shower-label interface audit",
        "development_years": sorted(FROZEN),
        "reserved_untouched_year": RESERVED_YEAR,
        "requested_urls": requested_urls,
        "documentation": {
            "url": DOC_URL,
            "bytes": len(doc_raw),
            "sha256": doc_hash,
            "field": "sh",
            "semantic": "IAU shower number",
        },
        "years": years,
        "totals": {
            "rows": totals["rows"],
            "invalid_phase_rows": totals["invalid_phase"],
            "blind_interval_rows": totals["blind_excluded"],
            "post_boundary_rows": totals["post_boundary"],
            "background_rows": totals["background"],
            "labeled_rows": totals["labeled"],
            "unsupported_rows": totals["unsupported"],
            "unsupported_fraction": unsupported_fraction,
            "positive_integer_mapping_fraction": mapping_fraction,
        },
        "support": {
            "distinct_positive_shower_numbers": distinct,
            "supported_k8_shower_year_cells": supported_k8_cells,
            "supported_k12_shower_year_cells": supported_k12_cells,
            "multi_year_supported_shower_numbers": multi_year_supported,
            "represented_years_histogram_for_multi_year_supported_showers": {
                str(key): represented_year_histogram[key] for key in sorted(represented_year_histogram)
            },
        },
        "identities_emitted": False,
        "geometry_values_read": False,
        "detector_scores_computed": False,
        "sonotaco_2024_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def write_outputs(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "camsv3_shower_label_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    totals = result.get("totals", {})
    support = result.get("support", {})
    report = [
        "# CAMSv3 survey-native shower-label interface audit",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
        f"- development years: {result.get('development_years')}",
        f"- reserved untouched year: {result.get('reserved_untouched_year')}",
        f"- background rows: {totals.get('background_rows')}",
        f"- labeled rows: {totals.get('labeled_rows')}",
        f"- unsupported rows: {totals.get('unsupported_rows')}",
        f"- positive-integer mapping fraction: {totals.get('positive_integer_mapping_fraction')}",
        f"- distinct positive shower numbers: {support.get('distinct_positive_shower_numbers')}",
        f"- k=8 shower-year cells: {support.get('supported_k8_shower_year_cells')}",
        f"- k=12 shower-year cells: {support.get('supported_k12_shower_year_cells')}",
        f"- multi-year supported showers: {support.get('multi_year_supported_shower_numbers')}",
        "",
        "## Frozen gates",
        "",
    ]
    report.extend(f"- {name}: {passed}" for name, passed in result.get("gates", {}).items())
    report.extend(
        [
            "",
            "No shower-number identities, individual rows, geometry values, detector scores, SonotaCo 2024 values, or CAMSv3 2016 values are present in this artifact.",
        ]
    )
    (out / "RESULT.md").write_text("\n".join(report) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    try:
        result = build_result()
    except Exception as exc:
        result = {
            "method": "CAMSv3 aggregate-only survey-native shower-label interface audit",
            "development_years": sorted(FROZEN),
            "reserved_untouched_year": RESERVED_YEAR,
            "error": f"{type(exc).__name__}: {exc}",
            "identities_emitted": False,
            "geometry_values_read": False,
            "detector_scores_computed": False,
            "sonotaco_2024_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_CAMSV3_SHOWER_LABEL_INTERFACE",
        }
    write_outputs(out, result)
    print(json.dumps({"verdict": result["verdict"], "totals": result.get("totals"), "support": result.get("support"), "gates": result.get("gates"), "error": result.get("error")}, indent=2))
    if result["verdict"] != "PASS_CAMSV3_SHOWER_LABEL_INTERFACE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
