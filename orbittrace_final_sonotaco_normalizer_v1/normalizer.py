#!/usr/bin/env python3
"""Label-free SonotaCo annual-row normalizer for the frozen OrbitTrace final pipeline.

This module performs no network access and accepts no truth mapping. It is frozen from already-
spent SonotaCo schema knowledge before either reserved 2013/2014 scientific archive is opened.
The 20°–55° target interval is rejected immediately after solar longitude is decoded and before
any other scientific field is interpreted. The shower field is never read.

The shared manifest deliberately carries every raw observable needed by the frozen final methods:
OrbitTrace geometry, Sugar RA/Dec/Vg uncertainties, and the q/e/convergence-angle fields required
by the frozen catalogue-HDBSCAN quality interface. Carrying a field does not select on it; each
method's pairwise eligibility is applied only after the common base manifest is frozen and before
truth is opened.
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

EXPECTED_EFFECTIVE_HEADER = (
    "dayut", "timeut", "mjdday", "soldeg", "radeg", "rasddeg", "dedeg", "desddeg",
    "vgkms", "vgsdkms", "aau", "asdau", "1a1au", "1asd1au", "qau", "qsdau", "e", "esd",
    "perideg", "perisddeg", "nodedeg", "incldeg", "inclsddeg", "amag", "dursec", "lng1mdeg",
    "lat1mdeg", "h1km", "lng2mdeg", "lat2mdeg", "h2km", "lkm", "nrstar", "qcdeg", "ncam",
    "erdeg", "ncamorg", "erorgdeg", "shower", "dr", "dv", "dd", "zf", "nighttimehour", "zhr",
)
REQUIRED_GEOMETRY_HEADERS = {"soldeg", "radeg", "dedeg", "vgkms", "ncam"}
SHARED_NUMERIC_HEADERS = {
    "radeg", "rasddeg", "dedeg", "desddeg", "vgkms", "vgsdkms",
    "qau", "e", "perideg", "nodedeg", "incldeg", "qcdeg", "ncam",
}


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
    require(SHARED_NUMERIC_HEADERS.issubset(set(normalized)), "required shared observable field missing")
    return normalized


def normalize_annual_csv(
    payload: bytes,
    *,
    year: int,
    base: Any,
    id_prefix: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return target-excluded shared rows and a structural/quality audit.

    The common row keeps uncertainty/orbit/quality values even when missing/nonfinite (as None).
    Frozen pairwise adapters apply their own structural eligibility before any truth is opened.
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

        # CRITICAL FIREWALL ORDER: only solar longitude may be decoded before this branch.
        sol_raw = parse_float(row[index["soldeg"]])
        if sol_raw is None:
            counts["invalid_solar"] += 1
            continue
        sol = sol_raw % 360.0
        if BLIND_LOW <= sol <= BLIND_HIGH:
            counts["blind_removed_before_any_other_scientific_field"] += 1
            continue

        # Only now may shared scientific observables be decoded.
        values = {name: parse_float(row[index[name]]) for name in SHARED_NUMERIC_HEADERS}
        ra = values["radeg"]
        dec = values["dedeg"]
        vg = values["vgkms"]
        ncam = values["ncam"]
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
            "ra": float(ra),
            "ra_sd": values["rasddeg"],
            "dec": float(dec),
            "dec_sd": values["desddeg"],
            "vg_sd": values["vgsdkms"],
            "q": values["qau"],
            "e": values["e"],
            "peri": values["perideg"],
            "node": values["nodedeg"],
            "inc": values["incldeg"],
            "qc": values["qcdeg"],
            "ncam": float(ncam),
            "iau": 0,
            "complex_key": "HIDDEN",
        })
        counts["retained"] += 1
        counts["retained_with_positive_sugar_uncertainties"] += int(
            values["rasddeg"] is not None and values["rasddeg"] > 0.0
            and values["desddeg"] is not None and values["desddeg"] > 0.0
            and values["vgsdkms"] is not None and values["vgsdkms"] > 0.0
        )
        counts["retained_with_hdbscan_quality_fields"] += int(
            values["qcdeg"] is not None
            and values["vgsdkms"] is not None
            and values["qau"] is not None
            and values["e"] is not None
        )
        counts["retained_with_complete_orbit"] += int(all(
            values[name] is not None for name in ("qau", "e", "perideg", "nodedeg", "incldeg")
        ))

    output_fields = [
        "id", "year", "sol", "sun_lon", "ecl_lat", "vg",
        "ra", "ra_sd", "dec", "dec_sd", "vg_sd",
        "q", "e", "peri", "node", "inc", "qc", "ncam", "iau", "complex_key",
    ]
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
        "target_region_non_solar_fields_decoded": False,
        "output_fields": output_fields,
        "raw_fields_carried_for_same_information_parity": [
            "ra", "ra_sd", "dec", "dec_sd", "vg", "vg_sd", "q", "e", "peri", "node", "inc", "qc", "ncam"
        ],
    }
    require(len(events) == len(seen_ids), "normalized event ID collision")
    return events, audit


def sugar_pairwise_eligible(event: dict[str, Any]) -> bool:
    """Frozen structural eligibility for the uncertainty-aware Sugar comparator."""
    return all(
        event[name] is not None and math.isfinite(float(event[name])) and float(event[name]) > 0.0
        for name in ("ra_sd", "dec_sd", "vg_sd")
    )


def hdbscan_pairwise_eligible(event: dict[str, Any]) -> bool:
    """Frozen label-free physical eligibility for final catalogue HDBSCAN.

    Base shared-manifest geometry/ncam cuts are already satisfied. This function implements only
    the additional final #820 HDBSCAN requirements and never reads shower truth.
    """
    qc = event.get("qc")
    vg = event.get("vg")
    vg_sd = event.get("vg_sd")
    q = event.get("q")
    ecc = event.get("e")
    if any(value is None for value in (qc, vg, vg_sd, q, ecc)):
        return False
    values = [float(qc), float(vg), float(vg_sd), float(q), float(ecc)]
    if not all(math.isfinite(value) for value in values):
        return False
    qc_f, vg_f, vg_sd_f, q_f, e_f = values
    return (
        qc_f >= 15.0
        and vg_f > 0.0
        and vg_sd_f / vg_f <= 0.10
        and 0.0 <= e_f <= 1.0
        and 0.0 < q_f <= 1.0
    )


def orbit_pairwise_eligible(event: dict[str, Any]) -> bool:
    """Historical structural orbit-completeness helper; unused by final M0/#839."""
    values = [event[name] for name in ("q", "e", "peri", "node", "inc")]
    return all(value is not None and math.isfinite(float(value)) for value in values)


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
    idx = {x: i for i, x in enumerate(EXPECTED_EFFECTIVE_HEADER)}

    def row(
        sol: str,
        ra: str = "100", dec: str = "20", vg: str = "30", ncam: str = "2",
        ra_sd: str = "0.2", dec_sd: str = "0.3", vg_sd: str = "0.4",
        q: str = "0.5", e: str = "0.8", peri: str = "120", node: str = "220", inc: str = "10",
        qc: str = "20", shower: str = "SECRET",
    ) -> list[str]:
        values = ["0"] * EFFECTIVE_HEADER_WIDTH
        for key, value in {
            "soldeg": sol, "radeg": ra, "dedeg": dec, "vgkms": vg, "ncam": ncam,
            "rasddeg": ra_sd, "desddeg": dec_sd, "vgsdkms": vg_sd,
            "qau": q, "e": e, "perideg": peri, "nodedeg": node, "incldeg": inc, "qcdeg": qc,
            "shower": shower,
        }.items():
            values[idx[key]] = value
        return values

    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerow(row("10", shower="SHOULD_NOT_BE_READ"))
    writer.writerow(row(
        "30", ra="NOT_A_NUMBER", dec="NOT_A_NUMBER", vg="NOT_A_NUMBER", ncam="X",
        ra_sd="BAD", dec_sd="BAD", vg_sd="BAD", q="BAD", e="BAD", peri="BAD", node="BAD", inc="BAD",
        qc="BAD", shower="TARGET_SECRET",
    ))
    writer.writerow(row("100", vg="4.9"))
    writer.writerow(row("110", ncam="1"))
    writer.writerow(row("120", ra="200", dec="-10", vg="50", ncam="3", ra_sd="0", vg_sd="6", q="", qc="10"))
    # Base-valid rows that exercise the exact frozen HDBSCAN lower bounds without changing the base manifest.
    writer.writerow(row("130", q="0", e="0.5"))
    writer.writerow(row("140", q="0.5", e="-0.01"))
    events, audit = normalize_annual_csv(buf.getvalue().encode("utf-8"), year=2013, base=_synthetic_base(), id_prefix="X")
    assert [e["sol"] for e in events] == [10.0, 120.0, 130.0, 140.0]
    assert audit["counts"]["blind_removed_before_any_other_scientific_field"] == 1
    assert audit["counts"]["invalid_geometry_or_quality"] == 2
    assert audit["shower_column_row_accessed"] is False
    assert audit["target_region_non_solar_fields_decoded"] is False
    assert sugar_pairwise_eligible(events[0]) is True
    assert hdbscan_pairwise_eligible(events[0]) is True
    assert orbit_pairwise_eligible(events[0]) is True
    assert sugar_pairwise_eligible(events[1]) is False
    assert hdbscan_pairwise_eligible(events[1]) is False
    assert orbit_pairwise_eligible(events[1]) is False
    assert hdbscan_pairwise_eligible(events[2]) is False
    assert hdbscan_pairwise_eligible(events[3]) is False
    assert events[0]["ra_sd"] == 0.2 and events[0]["q"] == 0.5 and events[0]["qc"] == 20.0
    assert all(e["complex_key"] == "HIDDEN" and e["iau"] == 0 for e in events)
    assert all(20.0 > e["sol"] or e["sol"] > 55.0 for e in events)


if __name__ == "__main__":
    self_test()
    print("PASS_FINAL_SONOTACO_SHARED_MANIFEST_V2_SELF_TEST")