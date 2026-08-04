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
from collections import Counter
from pathlib import Path, PurePosixPath

import requests

BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
DEVELOPMENT = {
    2011: ("de2af15ccdee9836912c1efb9fba9bdcf47e3b9d2fa7374244dc6ac69f82c118", "iaumdcCAMSv3_2011.csv", 44_998),
    2012: ("040b853d6fbcd5dfc9ef3f76be553624a9893ab9b1aac709ccebcc2498c73cb3", "iaumdcCAMSv3_2012.csv", 53_401),
    2013: ("895f58c985f730976ef6e3ca3c89cd947bd248b419101eba163eef77e951e56a", "iaumdcCAMSv3_2013.csv", 76_213),
    2014: ("0d9ba75256577e9b008786054ea13c4fa6b755d42ae65031f311bae8a0b3a928", "iaumdcCAMSv3_2014.csv", 83_336),
    2015: ("aa9a04b206e1927d7a8cb401ef22baae20061c9827dec0133e42b11790fcf61d", "iaumdcCAMSv3_2015.csv", 100_700),
}
RESERVED_YEAR = 2016
REQUIRED = {
    "LS", "RA", "DECL", "Vg", "delta_RA", "delta_DECL", "delta_Vg", "sh"
}
ALNUM_TOKEN = re.compile(r"^[A-Z0-9_-]{1,32}$")
NUMERIC_TOKEN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def parse_float(value: str) -> float | None:
    try:
        result = float(value.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p90": None, "p99": None}
    ordered = sorted(values)

    def nearest(probability: float) -> float:
        index = max(0, min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1))
        return float(ordered[index])

    return {"median": nearest(0.5), "p90": nearest(0.9), "p99": nearest(0.99)}


def token_class(token: str) -> str:
    if token == "":
        return "blank"
    if NUMERIC_TOKEN.fullmatch(token):
        return "numeric"
    if ALNUM_TOKEN.fullmatch(token):
        return "bounded_alphanumeric"
    return "other"


def download_member(year: int) -> tuple[bytes, str]:
    expected_hash, basename, _ = DEVELOPMENT[year]
    url = f"{BASE}/iaumdcCAMSv3_{year}.csv.zip"
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_hash:
        raise RuntimeError(f"{year}: archive hash mismatch {digest}")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f"{year}: CRC failure")
        matches = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv") and PurePosixPath(name).name == basename
        ]
        if len(matches) != 1:
            raise RuntimeError(f"{year}: expected one exact basename, found {matches}")
        return archive.read(matches[0]), matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    malformed_rows = 0
    invalid_solar_rows = 0
    blind_rows_removed = 0
    nonblind_rows = 0
    geometry_ready = 0
    uncertainty_complete = 0
    label_counts: Counter[str] = Counter()
    token_classes: Counter[str] = Counter()
    bounded_printable_nonblank = 0
    nonblank_label_rows = 0
    uncertainty_values = {
        "delta_RA": [],
        "delta_DECL": [],
        "delta_Vg": [],
    }
    annual: dict[str, dict] = {}
    canonical_header: list[str] | None = None

    for year in sorted(DEVELOPMENT):
        _, _, expected_rows = DEVELOPMENT[year]
        payload, member = download_member(year)
        reader = csv.reader(
            io.StringIO(payload.decode("utf-8-sig"), newline=""),
            delimiter=";",
        )
        header = [field.lstrip("\ufeff").strip() for field in next(reader)]
        if canonical_header is None:
            canonical_header = header
        elif header != canonical_header:
            raise RuntimeError(f"{year}: header differs from prior development years")
        if not REQUIRED.issubset(set(header)):
            raise RuntimeError(f"{year}: required fields absent")
        index = {field: position for position, field in enumerate(header)}

        year_total = 0
        year_blind = 0
        year_nonblind = 0
        year_geometry = 0
        year_uncertainty = 0

        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            total_rows += 1
            year_total += 1
            if len(row) != len(header):
                malformed_rows += 1
                continue

            solar = parse_float(row[index["LS"]])
            if solar is None:
                invalid_solar_rows += 1
                continue
            solar %= 360.0
            if 20.0 <= solar <= 55.0:
                blind_rows_removed += 1
                year_blind += 1
                continue

            nonblind_rows += 1
            year_nonblind += 1
            ra = parse_float(row[index["RA"]])
            dec = parse_float(row[index["DECL"]])
            vg = parse_float(row[index["Vg"]])
            geometry = (
                0.0 <= solar < 360.0
                and ra is not None and 0.0 <= ra < 360.0
                and dec is not None and -90.0 <= dec <= 90.0
                and vg is not None and 0.0 < vg < 100.0
            )
            if geometry:
                geometry_ready += 1
                year_geometry += 1

            token = row[index["sh"]].strip().upper()
            label_counts[token] += 1
            category = token_class(token)
            token_classes[category] += 1
            if token:
                nonblank_label_rows += 1
                if token.isascii() and len(token) <= 32 and all(ch.isprintable() for ch in token):
                    bounded_printable_nonblank += 1

            uncertainties: dict[str, float | None] = {}
            for field in uncertainty_values:
                value = parse_float(row[index[field]])
                uncertainties[field] = value
                if value is not None and value >= 0.0:
                    uncertainty_values[field].append(value)
            complete = geometry and all(
                value is not None and value >= 0.0 for value in uncertainties.values()
            )
            if complete:
                uncertainty_complete += 1
                year_uncertainty += 1

        if year_total != expected_rows:
            raise RuntimeError(f"{year}: row count {year_total} != {expected_rows}")
        annual[str(year)] = {
            "member": member,
            "rows": year_total,
            "blind_rows_removed": year_blind,
            "nonblind_rows": year_nonblind,
            "geometry_ready": year_geometry,
            "uncertainty_complete": year_uncertainty,
        }

    geometry_fraction = geometry_ready / nonblind_rows if nonblind_rows else 0.0
    uncertainty_fraction = (
        uncertainty_complete / geometry_ready if geometry_ready else 0.0
    )
    bounded_fraction = (
        bounded_printable_nonblank / nonblank_label_rows
        if nonblank_label_rows else 0.0
    )
    gates = {
        "exact_total_development_rows": total_rows == sum(item[2] for item in DEVELOPMENT.values()),
        "zero_malformed_rows": malformed_rows == 0,
        "valid_solar_longitude_fraction_at_least_0_99": (
            (total_rows - invalid_solar_rows) / total_rows >= 0.99
        ),
        "geometry_completeness_at_least_0_98": geometry_fraction >= 0.98,
        "uncertainty_completeness_at_least_0_90": uncertainty_fraction >= 0.90,
        "nonblank_label_rows_at_least_10000": nonblank_label_rows >= 10_000,
        "unique_nonblank_labels_at_least_20": (
            len([token for token in label_counts if token]) >= 20
        ),
        "bounded_printable_nonblank_fraction_at_least_0_99": bounded_fraction >= 0.99,
        "reserved_2016_not_accessed": RESERVED_YEAR not in DEVELOPMENT,
    }
    verdict = (
        "PASS_CAMSV3_2011_2015_AGGREGATE_AUDIT"
        if all(gates.values())
        else "KILL_CAMSV3_2011_2015_AGGREGATE_AUDIT"
    )
    result = {
        "method": "CAMSv3 2011-2015 aggregate-only label and uncertainty audit",
        "development_years": sorted(DEVELOPMENT),
        "reserved_year": RESERVED_YEAR,
        "annual": annual,
        "counts": {
            "total_rows": total_rows,
            "malformed_rows": malformed_rows,
            "invalid_solar_rows": invalid_solar_rows,
            "blind_rows_removed": blind_rows_removed,
            "nonblind_rows": nonblind_rows,
            "geometry_ready": geometry_ready,
            "uncertainty_complete": uncertainty_complete,
            "nonblank_label_rows": nonblank_label_rows,
            "unique_label_tokens": len(label_counts),
            "unique_nonblank_label_tokens": len([token for token in label_counts if token]),
        },
        "fractions": {
            "geometry_completeness": geometry_fraction,
            "uncertainty_completeness": uncertainty_fraction,
            "bounded_printable_nonblank": bounded_fraction,
        },
        "token_class_counts": dict(sorted(token_classes.items())),
        "top_label_tokens": label_counts.most_common(100),
        "uncertainty_quantiles": {
            field: quantiles(values) for field, values in uncertainty_values.items()
        },
        "gates": gates,
        "verdict": verdict,
        "event_rows_retained": False,
        "detector_scores_computed": False,
        "reserved_2016_values_read": False,
        "ghoststream_values_used": False,
    }
    (output / "camsv3_aggregate_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    report = [
        "# CAMSv3 2011-2015 aggregate-only audit",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- total rows: **{total_rows:,}**",
        f"- blind rows removed: **{blind_rows_removed:,}**",
        f"- nonblind rows: **{nonblind_rows:,}**",
        f"- geometry completeness: **{geometry_fraction:.6f}**",
        f"- uncertainty completeness: **{uncertainty_fraction:.6f}**",
        f"- nonblank label rows: **{nonblank_label_rows:,}**",
        f"- unique nonblank label tokens: **{len([token for token in label_counts if token])}**",
        f"- bounded printable nonblank fraction: **{bounded_fraction:.6f}**",
        "",
        "CAMSv3 2016 was not downloaded or read.",
    ]
    (output / "RESULT.md").write_text("\n".join(report) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict != "PASS_CAMSV3_2011_2015_AGGREGATE_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
