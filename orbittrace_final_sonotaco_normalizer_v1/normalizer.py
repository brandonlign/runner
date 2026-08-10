#!/usr/bin/env python3
"""Label-free SonotaCo annual-row normalizer for the frozen OrbitTrace final pipeline.

This module performs no network access and accepts no truth mapping. It is frozen from already-
spent SonotaCo schema knowledge before either reserved 2013/2014 scientific archive is opened.
The 20°–55° target interval is rejected immediately after solar longitude is decoded and before
RA/Dec/speed/camera values are interpreted. The shower field is never read.
"""
from __future__ import annotations

import csv
import io
import math
import re
from collections import Counter
from typing import Any

BLIND_LOW = 20.0
BLIND_HIGH = 55.0
VG_LOW = 5.0
VG_HIGH = 75.0
MIN_NCAM = 2.0
RAW_HEADER_WIDTH_WITH_TRAILING_EMPTY = 46
EFFECTIVE_HEADER_WIDTH = 45

# Historical validated SonotaCo annual U2 schema (2016 and 2023). The final reserved years must
# match this exact effective schema or fail closed before scientific row retention.
EXPECTED_EFFECTIVE_HEADER = (
    "dayut", "timeut", "mjdday", "soldeg", "radeg", "rasddeg", "dedeg", "desddeg",
    "vgkms", "vgsdkms", "aau", "asdau", "1a1au", "1asd1au", "qau", "qsdau", "e", "esd",
    "perideg", "perisddeg", "nodedeg", "incldeg", "inclsddeg", "amag", "dursec", "lng1mdeg",
    "lat1mdeg", "h1km", "lng2mdeg", "lat2mdeg", "h2km", "lkm", "nrstar", "qcdeg", "ncam",
    "erdeg", "ncamorg", "erorgdeg", "shower", "dr", "dv", "dd", "zf", "nighttimehour", "zhr",
)
REQUIRED_GEOMETRY_HEADERS = {"soldeg", "radeg", "dedeg", "vgkms", "ncam"}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def normalize_header(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


def parse_float(text: str) -> float | None:
    try:
        value = float(text.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def reconcile_header(raw_header: list[str]) -> list[str]:
    normalized = [normalize_header(x) for x in raw_header]
    if len(normalized) == RAW_HEADER_WIDTH_WITH_TRAILING_EMPTY and normalized[-1] == "":
        normalized = normalized[:-1]
    require(len(normalized) == EFFECTIVE_HEADER_WIDTH,
            f"unexpected SonotaCo effective header width: {len(normalized)}")
    require(tuple(normalized) == EXPECTED_EFFECTIVE_HEADER,
            "SonotaCo effective header differs from pre-frozen historical U2 schema")
    require(len(normalized) == len(set(normalized)), "duplicate normalized SonotaCo header")
    require(REQUIRED_GEOMETRY_HEADERS.issubset(set(normalized)), "required label-free geometry field missing")
    return normalized


def normalize_annual_csv(
    payload: bytes,
    *,
    year: int,
    base: Any,
    id_prefix: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return target-excluded normalized events and a structural/quality audit.

    `base` is the already-frozen geometry helper exposing `equatorial_to_ecliptic` and `wrap180`.
    No label/truth field is returned or inspected.
    """
    require(year in {2013, 2014}, f"normalizer is reserved only for SonotaCo 2013/2014, got {year}")
    text = payload.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",")
    try:
        raw_header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("empty SonotaCo annual CSV") from exc
    header = reconcile_header(raw_header)
    index = {field: i for i, field in enumerate(header)}
    prefix = id_prefix if id_prefix is not None else f"SNT{year}"

    events: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    for physical_row, row in enumerate(reader, start=2):
        if not row or (len(row) == 1 and not row[0].strip()):
            counts["blank_rows"] += 1
            continue
        counts["physical_data_rows"] += 1
        if len(row) != EFFECTIVE_HEADER_WIDTH:
            counts["malformed_width"] += 1
            continue

        # Firewall order is intentional and audited: decode ONLY solar longitude first.
        sol_raw = parse_float(row[index["soldeg"]])
        if sol_raw is None:
            counts["invalid_solar"] += 1
            continue
        sol = sol_raw % 360.0
        if BLIND_LOW <= sol <= BLIND_HIGH:
            counts["blind_removed_before_geometry"] += 1
            continue

        # Only after the target interval is removed may remaining candidate geometry be decoded.
        ra = parse_float(row[index["radeg"]])
        dec = parse_float(row[index["dedeg"]])
        vg = parse_float(row[index["vgkms"]])
        ncam = parse_float(row[index["ncam"]])
        if not (
            ra is not None and 0.0 <= ra < 360.0
            and dec is not None and -90.0 <= dec <= 90.0
            and vg is not None and VG_LOW <= vg <= VG_HIGH
            and ncam is not None and ncam >= MIN_NCAM
        ):
            counts["invalid_geometry_or_quality"] += 1
            continue

        ecl_lon, ecl_lat = base.equatorial_to_ecliptic(float(ra), float(dec))
        event_id = f"{prefix}:{physical_row}"
        require(event_id not in seen_ids, f"duplicate generated event ID: {event_id}")
        seen_ids.add(event_id)
        events.append({
            "id": event_id,
            "year": int(year),
            "sol": float(sol),
            "sun_lon": float(base.wrap180(float(ecl_lon) - float(sol))),
            "ecl_lat": float(ecl_lat),
            "vg": float(vg),
            "iau": 0,
            "complex_key": "HIDDEN",
        })
        counts["retained"] += 1

    audit = {
        "year": int(year),
        "raw_header_width": len(raw_header),
        "effective_header_width": len(header),
        "effective_header": header,
        "counts": dict(sorted(counts.items())),
        "filters": {
            "blind_exclusion_closed_deg": [BLIND_LOW, BLIND_HIGH],
            "vg_km_s_inclusive": [VG_LOW, VG_HIGH],
            "minimum_ncam": MIN_NCAM,
            "ra_deg": "0 <= RA < 360",
            "dec_deg": "-90 <= Dec <= 90",
        },
        "shower_column_row_accessed": False,
        "truth_mapping_accessed": False,
        "target_region_geometry_decoded": False,
        "output_fields": ["id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"],
    }
    require(len(events) == len(seen_ids), "normalized event ID collision")
    return events, audit


def _synthetic_base() -> Any:
    class B:
        @staticmethod
        def equatorial_to_ecliptic(ra: float, dec: float) -> tuple[float, float]:
            return (ra + 1.25) % 360.0, dec - 0.5

        @staticmethod
        def wrap180(value: Any) -> Any:
            return (value + 180.0) % 360.0 - 180.0
    return B()


def self_test() -> None:
    header = list(EXPECTED_EFFECTIVE_HEADER) + [""]
    def row(sol: str, ra: str = "100", dec: str = "20", vg: str = "30", ncam: str = "2", shower: str = "SECRET") -> list[str]:
        values = ["0"] * EFFECTIVE_HEADER_WIDTH
        idx = {x: i for i, x in enumerate(EXPECTED_EFFECTIVE_HEADER)}
        values[idx["soldeg"]] = sol
        values[idx["radeg"]] = ra
        values[idx["dedeg"]] = dec
        values[idx["vgkms"]] = vg
        values[idx["ncam"]] = ncam
        values[idx["shower"]] = shower
        return values
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerow(row("10", shower="SHOULD_NOT_BE_READ"))
    # Target-region row deliberately carries invalid geometry. A correct firewall skips it before
    # trying to parse that geometry.
    writer.writerow(row("30", ra="NOT_A_NUMBER", dec="NOT_A_NUMBER", vg="NOT_A_NUMBER", ncam="X", shower="TARGET_SECRET"))
    writer.writerow(row("100", vg="4.9"))
    writer.writerow(row("110", ncam="1"))
    writer.writerow(row("120", ra="200", dec="-10", vg="50", ncam="3"))
    events, audit = normalize_annual_csv(buf.getvalue().encode("utf-8"), year=2013, base=_synthetic_base(), id_prefix="X")
    assert [e["sol"] for e in events] == [10.0, 120.0]
    assert audit["counts"]["blind_removed_before_geometry"] == 1
    assert audit["counts"]["invalid_geometry_or_quality"] == 2
    assert audit["shower_column_row_accessed"] is False
    assert audit["target_region_geometry_decoded"] is False
    assert all(e["complex_key"] == "HIDDEN" and e["iau"] == 0 for e in events)
    assert all(20.0 > e["sol"] or e["sol"] > 55.0 for e in events)


if __name__ == "__main__":
    self_test()
    print("PASS_FINAL_SONOTACO_NORMALIZER_V1_SELF_TEST")
