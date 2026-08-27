from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import statistics
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path("stream_fdr_stage0")
DATA_DIR = ROOT / "data" / "multinetwork"
OUT_DIR = ROOT / "results" / "multinetwork_audit"
OBLIQUITY_DEG = 23.43928
YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")

DATASETS = {
    "CAMS": {
        "url": "https://zenodo.org/records/18664293/files/CAMS_shober_2026_subset.csv?download=1",
        "md5": "65dcaefe0a4a3231388ddeda9b0ed9cf",
    },
    "GMN": {
        "url": "https://zenodo.org/records/18664293/files/GMN_shober_2026_subset.csv?download=1",
        "md5": "a1890dcb0ca11baa0e49c21c2133dc55",
    },
    "EDMOND": {
        "url": "https://zenodo.org/records/18664293/files/EDMOND_shober_2026_subset.csv?download=1",
        "md5": "c5a3ee2c89cdff792bd114a39179350b",
    },
    "SonotaCo": {
        "url": "https://zenodo.org/records/18664293/files/SonotaCo_shober_2026_subset.csv?download=1",
        "md5": "f57a2ac71832ceca9227441c00b8cd58",
    },
}

ALIASES = {
    "year": ["Yr", "year", "Year", "YEAR", "_Y_ut"],
    "datetime": [
        "datetime_utc",
        "date_utc",
        "Beginning_UTC_Time",
        "beginning_utc_time",
        "Beginning_Julian_date",
    ],
    "solar_longitude": [
        "LS",
        "sol_lon_deg",
        "Sol_lon_deg",
        "solar_longitude_deg",
        "sol_lon",
        "lambda_sun",
        "solar_longitude",
        "_sol",
    ],
    "ra_geo": [
        "RA",
        "rageo_deg",
        "RAgeo_deg",
        "ra_geocentric_deg",
        "ra_geo",
        "RAgeo",
        "RA_g",
        "_ra_t",
    ],
    "dec_geo": [
        "DECL",
        "decgeo_deg",
        "DECgeo_deg",
        "dec_geocentric_deg",
        "dec_geo",
        "DECgeo",
        "Dec_g",
        "_dc_t",
    ],
    "vg": [
        "Vg",
        "vgeo_km_s",
        "Vgeo_km_s",
        "v_geocentric_km_s",
        "vg",
        "Vgeo",
        "V_g",
        "_vg",
    ],
    "q": ["q", "q_au", "q_AU", "perihelion_distance", "_q"],
    "e": ["e", "eccentricity", "_e"],
    "inclination": ["i", "i_deg", "inclination", "_incl"],
    "argument_perihelion": [
        "arg",
        "peri_deg",
        "arg_perihelion_deg",
        "omega",
        "argument_perihelion",
        "_peri",
    ],
    "node": ["nod", "node_deg", "Omega", "ascending_node", "_node"],
}

UNCERTAINTY_HINTS = (
    "delta_",
    "sigma",
    "err",
    "uncert",
    "quality",
    "qc",
    "fiterr",
    "num_stat",
)


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    request = urllib.request.Request(url, headers={"User-Agent": "ghoststream-methodology-audit/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def pick_column(header: list[str], aliases: Iterable[str]) -> str | None:
    exact = {name: name for name in header}
    lower = {name.lower(): name for name in header}
    for alias in aliases:
        if alias in exact:
            return exact[alias]
        if alias.lower() in lower:
            return lower[alias.lower()]
    return None


def as_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_year(row: dict[str, str], columns: dict[str, str | None]) -> float | None:
    direct_column = columns.get("year")
    if direct_column:
        direct = as_float(row.get(direct_column, ""))
        if direct is not None:
            return direct

    datetime_column = columns.get("datetime")
    if not datetime_column:
        return None
    text = str(row.get(datetime_column, "")).strip()
    match = YEAR_PATTERN.search(text)
    if not match:
        return None
    return float(match.group(1))


def wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def circular_distance(a: float, b: float) -> float:
    return abs(wrap180(a - b))


def equatorial_to_ecliptic(ra_deg: float, dec_deg: float) -> tuple[float, float]:
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)
    eps = math.radians(OBLIQUITY_DEG)
    x = math.cos(dec) * math.cos(ra)
    y = math.cos(dec) * math.sin(ra) * math.cos(eps) + math.sin(dec) * math.sin(eps)
    z = -math.cos(dec) * math.sin(ra) * math.sin(eps) + math.sin(dec) * math.cos(eps)
    lon = math.degrees(math.atan2(y, x)) % 360.0
    lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    return lon, lat


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lo = int(math.floor(index))
    hi = int(math.ceil(index))
    if lo == hi:
        return ordered[lo]
    fraction = index - lo
    return ordered[lo] * (1.0 - fraction) + ordered[hi] * fraction


def compact_quantiles(values: list[float]) -> dict[str, float | None]:
    return {
        "p01": quantile(values, 0.01),
        "p05": quantile(values, 0.05),
        "p50": quantile(values, 0.50),
        "p95": quantile(values, 0.95),
        "p99": quantile(values, 0.99),
    }


def profile_dataset(name: str, spec: dict[str, str]) -> dict[str, object]:
    filename = f"{name.lower()}_shober_2026_subset.csv"
    path = DATA_DIR / filename
    download(spec["url"], path)
    digest = md5sum(path)
    if digest != spec["md5"]:
        raise RuntimeError(f"{name}: MD5 mismatch; expected {spec['md5']}, got {digest}")

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        columns = {semantic: pick_column(header, aliases) for semantic, aliases in ALIASES.items()}
        uncertainty_columns = [
            column
            for column in header
            if any(hint in column.lower() for hint in UNCERTAINTY_HINTS)
        ]

        total_rows = 0
        valid_core = 0
        esv_mask_count = 0
        year_counts: Counter[str] = Counter()
        core_values: dict[str, list[float]] = {
            "solar_longitude": [],
            "ra_geo": [],
            "dec_geo": [],
            "vg": [],
            "sun_centered_ecliptic_longitude": [],
            "ecliptic_latitude": [],
        }
        missing_core: Counter[str] = Counter()
        first_rows: list[dict[str, str]] = []

        for row_index, row in enumerate(reader):
            total_rows += 1
            if row_index < 2:
                first_rows.append({key: row.get(key, "") for key in header[: min(20, len(header))]})

            parsed: dict[str, float | None] = {"year": parse_year(row, columns)}
            for semantic in ("solar_longitude", "ra_geo", "dec_geo", "vg"):
                column = columns.get(semantic)
                parsed[semantic] = as_float(row.get(column, "")) if column else None

            for semantic in ("year", "solar_longitude", "ra_geo", "dec_geo", "vg"):
                if parsed[semantic] is None:
                    missing_core[semantic] += 1

            year = parsed["year"]
            ls = parsed["solar_longitude"]
            ra = parsed["ra_geo"]
            dec = parsed["dec_geo"]
            vg = parsed["vg"]
            if None in (year, ls, ra, dec, vg):
                continue
            assert year is not None and ls is not None and ra is not None and dec is not None and vg is not None
            if not (1800 <= year <= 2200 and 0.0 <= ls < 360.0 and 0.0 <= ra < 360.0 and -90.0 <= dec <= 90.0 and 5.0 <= vg <= 80.0):
                continue

            valid_core += 1
            year_counts[str(int(year))] += 1
            ecl_lon, ecl_lat = equatorial_to_ecliptic(ra, dec)
            sun_lon = wrap180(ecl_lon - ls)
            core_values["solar_longitude"].append(ls)
            core_values["ra_geo"].append(ra)
            core_values["dec_geo"].append(dec)
            core_values["vg"].append(vg)
            core_values["sun_centered_ecliptic_longitude"].append(sun_lon)
            core_values["ecliptic_latitude"].append(ecl_lat)

            # Conservative M2026-A1 / removed 87 Virginids mask, used only as a
            # shared weak-stream feasibility marker and never as a discovery rule.
            ls_delta = wrap180(ls - 10.2)
            expected_ra = 208.4 + 0.92 * ls_delta
            expected_dec = -19.3 - 0.32 * ls_delta
            if (
                5.0 <= ls <= 21.0
                and circular_distance(ra, expected_ra) <= 8.0
                and abs(dec - expected_dec) <= 5.0
                and abs(vg - 29.6) <= 3.0
            ):
                esv_mask_count += 1

    time_available = bool(columns.get("year") or columns.get("datetime"))
    core_available = time_available and all(
        columns.get(key) for key in ("solar_longitude", "ra_geo", "dec_geo", "vg")
    )
    orbit_available = all(columns.get(key) for key in ("q", "e", "inclination", "argument_perihelion", "node"))
    return {
        "name": name,
        "url": spec["url"],
        "file": str(path),
        "bytes": path.stat().st_size,
        "md5": digest,
        "rows": total_rows,
        "header": header,
        "semantic_columns": columns,
        "time_source": columns.get("year") or columns.get("datetime"),
        "uncertainty_or_quality_columns": uncertainty_columns,
        "core_coordinates_available": core_available,
        "orbit_coordinates_available": orbit_available,
        "valid_core_rows": valid_core,
        "valid_core_fraction": valid_core / total_rows if total_rows else 0.0,
        "missing_core_counts": dict(missing_core),
        "year_counts": dict(sorted(year_counts.items())),
        "year_min": min(map(int, year_counts)) if year_counts else None,
        "year_max": max(map(int, year_counts)) if year_counts else None,
        "conservative_esv_mask_count": esv_mask_count,
        "feature_quantiles": {key: compact_quantiles(values) for key, values in core_values.items()},
        "feature_means": {
            key: statistics.fmean(values) if values else None
            for key, values in core_values.items()
            if key in {"vg", "ecliptic_latitude"}
        },
        "first_rows_first_20_columns": first_rows,
    }


def markdown_report(profiles: list[dict[str, object]]) -> str:
    lines = [
        "# Multi-network event-level feasibility audit",
        "",
        "This audit is executed only in `brandonlign/runner`. It evaluates whether a shared latent-stream / separate-background pilot can be benchmarked without touching GhostStream.",
        "",
        "## Summary",
        "",
        "| Network | Rows | Valid core | Years | Core coordinates | Orbit coordinates | Uncertainty/quality fields | Conservative M2026-A1 mask |",
        "|---|---:|---:|---|---|---|---:|---:|",
    ]
    for profile in profiles:
        years = f"{profile['year_min']}–{profile['year_max']}" if profile["year_min"] is not None else "n/a"
        lines.append(
            f"| {profile['name']} | {profile['rows']:,} | {profile['valid_core_rows']:,} "
            f"| {years} | {'yes' if profile['core_coordinates_available'] else 'no'} "
            f"| {'yes' if profile['orbit_coordinates_available'] else 'no'} "
            f"| {len(profile['uncertainty_or_quality_columns'])} "
            f"| {profile['conservative_esv_mask_count']} |"
        )

    compatible = [p for p in profiles if p["core_coordinates_available"] and p["valid_core_rows"] >= 1000]
    shared_esv = [p for p in compatible if p["conservative_esv_mask_count"] >= 3]
    lines.extend([
        "",
        "## Frozen feasibility decisions",
        "",
        f"- Networks with compatible core coordinates and at least 1,000 valid events: **{len(compatible)}**.",
        f"- Compatible networks with at least three conservative M2026-A1-region events: **{len(shared_esv)}**.",
        "- A full shared-component pilot is permitted only if at least three compatible networks exist.",
        "- M2026-A1-region counts are only a feasibility marker; they are not labels and will not be used to tune the detector.",
        "- If network headers or definitions are incompatible, the model is killed rather than silently harmonizing unlike quantities.",
        "",
        "## Network details",
        "",
    ])
    for profile in profiles:
        lines.extend([
            f"### {profile['name']}",
            "",
            f"- semantic mapping: `{json.dumps(profile['semantic_columns'], sort_keys=True)}`",
            f"- time source: `{profile['time_source']}`",
            f"- valid core fraction: {profile['valid_core_fraction']:.4f}",
            f"- uncertainty/quality candidates: `{', '.join(profile['uncertainty_or_quality_columns'][:20])}`",
            f"- input MD5: `{profile['md5']}`",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profiles = [profile_dataset(name, spec) for name, spec in DATASETS.items()]
    payload = {
        "environment": {
            "python": os.sys.version,
            "cwd": str(Path.cwd()),
        },
        "profiles": profiles,
    }
    (OUT_DIR / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = markdown_report(profiles)
    (OUT_DIR / "AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
