from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import urllib.request
from collections import Counter
from pathlib import Path

URL = "https://zenodo.org/records/18664293/files/SonotaCo_shober_2026_subset.csv?download=1"
EXPECTED_MD5 = "f57a2ac71832ceca9227441c00b8cd58"
OUT = Path("stream_fdr_stage0/results")
DATA = Path("stream_fdr_stage0/data/SonotaCo_shober_2026_subset.csv")
OBLIQUITY_DEG = 23.43928


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


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {}
    def at(p: float) -> float:
        index = p * (len(ordered) - 1)
        lo = int(math.floor(index))
        hi = int(math.ceil(index))
        if lo == hi:
            return ordered[lo]
        fraction = index - lo
        return ordered[lo] * (1.0 - fraction) + ordered[hi] * fraction
    return {str(p): at(p) for p in (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        urllib.request.urlretrieve(URL, DATA)
    digest = hashlib.md5(DATA.read_bytes()).hexdigest()
    if digest != EXPECTED_MD5:
        raise SystemExit(f"MD5 mismatch: expected {EXPECTED_MD5}, got {digest}")

    valid: list[dict[str, float]] = []
    first_rows: list[list[str]] = []
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        for row_index, row in enumerate(reader):
            if row_index < 3:
                first_rows.append([row.get(column, "") for column in header])
            try:
                ls = float(row["LS"])
                ra = float(row["RA"])
                dec = float(row["DECL"])
                vg = float(row["Vg"])
                year = int(float(row["Yr"]))
            except (TypeError, ValueError, KeyError):
                continue
            if not (0.0 <= ls < 360.0 and 0.0 <= ra < 360.0 and -90.0 <= dec <= 90.0 and 5.0 <= vg <= 80.0):
                continue
            ecl_lon, ecl_lat = equatorial_to_ecliptic(ra, dec)
            valid.append({
                "ls": ls,
                "ra": ra,
                "dec": dec,
                "vg": vg,
                "year": float(year),
                "sun_lon": wrap180(ecl_lon - ls),
                "ecl_lat": ecl_lat,
            })

    # Conservative mask for M2026-A1 / removed 87 Virginids in the SonotaCo subset.
    # Shober (2026) reports LS 7.2--18.3 deg, RA 208.4 +/- 3.2 deg,
    # Dec -19.3 +/- 1.6 deg, Vg 29.6 +/- 0.9 km/s, with radiant drift.
    esv_mask = []
    for event in valid:
        ls_delta = wrap180(event["ls"] - 10.2)
        expected_ra = 208.4 + 0.92 * ls_delta
        expected_dec = -19.3 - 0.32 * ls_delta
        is_esv = (
            5.0 <= event["ls"] <= 21.0
            and circular_distance(event["ra"], expected_ra) <= 8.0
            and abs(event["dec"] - expected_dec) <= 5.0
            and abs(event["vg"] - 29.6) <= 3.0
        )
        esv_mask.append(is_esv)

    profile = {
        "url": URL,
        "md5": digest,
        "bytes": DATA.stat().st_size,
        "rows": sum(1 for _ in DATA.open("r", encoding="utf-8-sig", errors="replace")) - 1,
        "valid_rows": len(valid),
        "conservative_esv_mask_count": sum(esv_mask),
        "header": header,
        "first_rows": first_rows,
        "year_counts": dict(sorted(Counter(str(int(row["year"])) for row in valid).items())),
        "quantiles": {
            key: quantiles([row[key] for row in valid])
            for key in ("ls", "ra", "dec", "vg", "sun_lon", "ecl_lat")
        },
        "means": {
            key: statistics.fmean(row[key] for row in valid)
            for key in ("vg", "ecl_lat")
        },
    }
    (OUT / "data_header.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
