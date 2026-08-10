#!/usr/bin/env python3
"""Survey-independent pre-truth event contract for frozen OrbitTrace execution.

No file/network loader lives here. Survey transports must perform their already-frozen
firewalls/cuts and pass only allowed geometry into these pure normalization functions.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

CANONICAL_FIELDS = (
    "id",
    "year",
    "sol",
    "sun_lon",
    "ecl_lat",
    "vg",
    "iau",
    "complex_key",
)
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
MAARSY_FINAL_YEARS = (2021, 2022)

# Exact names that would make a pre-truth canonical input unsafe. `iau` is intentionally
# allowed only as the constant zero placeholder checked below.
FORBIDDEN_TRUTH_KEYS = frozenset({
    "shower",
    "shower_id",
    "iau_shower",
    "truth",
    "truth_id",
    "truth_label",
    "label",
    "known_shower",
    "target_id",
    "target_member",
})


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def finite_float(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} is not numeric") from exc
    require(math.isfinite(out), f"{name} is nonfinite")
    return out


def wrap180(value: Any) -> float:
    x = finite_float(value, "longitude")
    out = (x + 180.0) % 360.0 - 180.0
    # Preserve the exact frozen MAARSY convention at the positive 180-degree boundary.
    return 180.0 if out == -180.0 and x > 0.0 else out


def reject_truth_keys(record: Mapping[str, Any]) -> None:
    present = FORBIDDEN_TRUTH_KEYS.intersection(str(k).lower() for k in record)
    require(not present, f"truth-bearing key(s) reached canonical adapter: {sorted(present)}")


def canonical_record(
    *,
    event_id: Any,
    year: Any,
    sol: Any,
    sun_lon: Any,
    ecl_lat: Any,
    vg: Any,
) -> dict[str, Any]:
    event_id = str(event_id)
    require(bool(event_id), "event id is empty")
    require(isinstance(year, int) and not isinstance(year, bool), "year must be explicit int")
    sol_f = finite_float(sol, "sol")
    sun_lon_f = finite_float(sun_lon, "sun_lon")
    ecl_lat_f = finite_float(ecl_lat, "ecl_lat")
    vg_f = finite_float(vg, "vg")
    require(0.0 <= sol_f < 360.0, "sol outside [0,360)")
    require(-180.0 <= sun_lon_f <= 180.0, "sun_lon outside [-180,180]")
    require(-90.0 <= ecl_lat_f <= 90.0, "ecl_lat outside [-90,90]")
    require(vg_f > 0.0, "vg must be positive")
    return {
        "id": event_id,
        "year": int(year),
        "sol": sol_f,
        "sun_lon": sun_lon_f,
        "ecl_lat": ecl_lat_f,
        "vg": vg_f,
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def project_existing(
    record: Mapping[str, Any],
    *,
    allowed_years: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Validate/project an already-normalized GMN or SonotaCo detector row."""
    reject_truth_keys(record)
    missing = [k for k in ("id", "year", "sol", "sun_lon", "ecl_lat", "vg") if k not in record]
    require(not missing, f"canonical geometry field(s) missing: {missing}")
    require(record.get("iau", 0) == 0, "nonzero IAU value reached pre-truth adapter")
    require(record.get("complex_key", "HIDDEN") == "HIDDEN", "unhidden complex key reached adapter")
    year = record["year"]
    require(isinstance(year, int) and not isinstance(year, bool), "year must be explicit int")
    if allowed_years is not None:
        allowed = tuple(int(y) for y in allowed_years)
        require(year in allowed, f"year {year} outside caller-frozen years {allowed}")
    out = canonical_record(
        event_id=record["id"],
        year=year,
        sol=record["sol"],
        sun_lon=record["sun_lon"],
        ecl_lat=record["ecl_lat"],
        vg=record["vg"],
    )
    require(tuple(out) == CANONICAL_FIELDS, "canonical field order drift")
    return out


def from_gmn(record: Mapping[str, Any], *, allowed_years: Iterable[int]) -> dict[str, Any]:
    """Pure projection of a frozen GMN event; no coordinate recomputation."""
    return project_existing(record, allowed_years=allowed_years)


def from_sonotaco(record: Mapping[str, Any]) -> dict[str, Any]:
    """Pure projection of the frozen final SonotaCo normalizer output."""
    return project_existing(record, allowed_years=(2013, 2014))


def maarsy_keep_from_solar_longitude(sol: Any) -> bool:
    """First-stage firewall decision. Call before reading other MAARSY geometry values."""
    sol_f = finite_float(sol, "MAARSY sun_lon")
    require(0.0 <= sol_f < 360.0, "MAARSY sun_lon outside [0,360)")
    return not (BLIND_LOW <= sol_f <= BLIND_HIGH)


def maarsy_event_id(year: int, archive_member: str, row_index_0based: int) -> str:
    require(year in MAARSY_FINAL_YEARS, "MAARSY year outside fixed 2021-support/2022-scored route")
    require(bool(archive_member), "MAARSY archive member identity missing")
    require(isinstance(row_index_0based, int) and row_index_0based >= 0, "MAARSY row index invalid")
    return f"MAARSY|{year}|{archive_member}|{row_index_0based}"


def from_maarsy_retained_geometry(
    *,
    year: int,
    archive_member: str,
    row_index_0based: int,
    native_sun_lon_deg: Any,
    native_slon_deg: Any,
    native_slat_deg: Any,
    native_vels_km_s: Any,
) -> dict[str, Any]:
    """Map one already-firewalled MAARSY geometry row to the canonical detector record.

    The frozen public RCS HDF5 interface stores `vels` as a one-dimensional row-aligned scalar
    geocentric speed in km/s. The caller must have read native `sun_lon` first and only then read
    `slon`/`slat`/`vels` for rows passing `maarsy_keep_from_solar_longitude`. This function
    independently rejects a blinded row. Survey-specific quality cuts (including the frozen
    MAARSY 5--75 km/s cut) remain upstream and are not redefined here.
    """
    sol = finite_float(native_sun_lon_deg, "MAARSY sun_lon")
    require(maarsy_keep_from_solar_longitude(sol), "blinded MAARSY row reached geometry adapter")
    slon = finite_float(native_slon_deg, "MAARSY slon")
    slat = finite_float(native_slat_deg, "MAARSY slat")
    require(-90.0 <= slat <= 90.0, "MAARSY slat outside [-90,90]")
    speed = finite_float(native_vels_km_s, "MAARSY vels")
    return canonical_record(
        event_id=maarsy_event_id(year, archive_member, row_index_0based),
        year=year,
        sol=sol,
        sun_lon=wrap180(slon),
        ecl_lat=slat,
        vg=speed,
    )


def science_tuple(record: Mapping[str, Any]) -> tuple[float, float, float, float]:
    """Exact survey-independent geometry consumed by the common detector."""
    projected = project_existing(record)
    return (
        projected["sol"],
        projected["sun_lon"],
        projected["ecl_lat"],
        projected["vg"],
    )
