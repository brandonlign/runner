#!/usr/bin/env python3
"""Frozen legacy-CAMS replication of DTb68bb6b678e43478."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from orbittrace_new_discovery_screen import dtb68_external_replication as ext

CAMS_URL = "https://www.astro.sk/~ne/IAUMDC/PhVR2020/CAMS_by_date_v2.1l"


def solar_longitude_approx(dt: datetime) -> float:
    jd = 2440587.5 + dt.timestamp() / 86400.0
    n = jd - 2451545.0
    mean_long = (280.460 + 0.9856474 * n) % 360.0
    mean_anom = math.radians((357.528 + 0.9856003 * n) % 360.0)
    return float((mean_long + 1.915 * math.sin(mean_anom) + 0.020 * math.sin(2.0 * mean_anom)) % 360.0)


def parse_catalog() -> tuple[pd.DataFrame, dict]:
    response = requests.get(CAMS_URL, timeout=240)
    response.raise_for_status()
    rows = []
    for line in response.text.splitlines()[2:]:
        parts = line.split()
        if len(parts) < 13:
            continue
        try:
            rows.append({
                "id": parts[0],
                "year": int(parts[1]),
                "month": int(parts[2]),
                "day": float(parts[3]),
                "q": float(parts[4]),
                "e": float(parts[5]),
                "inc": float(parts[6]),
                "peri": float(parts[7]),
                "node": float(parts[8]),
                "ra": float(parts[9]),
                "dec": float(parts[10]),
                "vg": float(parts[11]),
                "vh": float(parts[12]),
            })
        except ValueError:
            continue
    raw = pd.DataFrame(rows)
    datetimes = []
    for row in raw.itertuples(index=False):
        day_integer = max(1, int(math.floor(row.day)))
        fraction = row.day - math.floor(row.day)
        datetimes.append(datetime(row.year, row.month, 1, tzinfo=timezone.utc) + timedelta(days=day_integer - 1 + fraction))
    sol = [solar_longitude_approx(dt) for dt in datetimes]
    frame, flipped = ext.canonical_frame(
        sol,
        raw["ra"].to_numpy(float), raw["dec"].to_numpy(float), raw["vg"].to_numpy(float),
        raw["e"].to_numpy(float), raw["q"].to_numpy(float), raw["inc"].to_numpy(float),
        raw["peri"].to_numpy(float), raw["node"].to_numpy(float), raw["id"].astype(str).to_numpy(),
        0, "CAMS",
    )
    # canonical_frame accepts a scalar year; restore each event's actual year after seasonal filtering.
    # Match by unique CAMS id to preserve exact rows.
    year_map = dict(zip(raw["id"].astype(str), raw["year"].astype(int)))
    frame["year"] = frame["identifier"].map(year_map).astype(int)
    return frame, {
        "url": CAMS_URL,
        "raw_rows": int(len(raw)),
        "valid_season_rows": int(len(frame)),
        "node_forms_flipped": int(flipped),
        "years": sorted(map(int, frame["year"].unique())) if len(frame) else [],
    }


def main() -> int:
    out = Path("cams_output")
    out.mkdir(parents=True, exist_ok=True)
    frame, meta = parse_catalog()
    result, members = ext.summarize([frame], "CAMS")
    payload = {
        "stage": "dtb68_legacy_cams_replication_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DTB68_CAMS_REPLICATION_PROTOCOL.md",
        "frozen_lead": "DTb68bb6b678e43478",
        "source_result": result,
        "catalog": meta,
    }
    (out / "dtb68_cams.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    if len(members):
        members.to_csv(out / "dtb68_cams_members.csv", index=False)
    md = "\n".join([
        "# DTb68 legacy CAMS replication", "",
        f"Catalog years: `{meta['years']}`; seasonal rows: **{meta['valid_season_rows']}**.",
        f"Strict members: **{result.get('members', 0)}**; formal pass: **{result.get('passed', False)}**.",
        f"Counts by year: `{result.get('member_counts_by_year', {})}`.",
        f"Activity: `{result.get('activity', {})}`.",
        f"Shifted windows: `{result.get('shifted_windows', {})}`.",
        f"Orbit: `{result.get('orbit', {})}`.",
    ]) + "\n"
    (out / "DTB68_CAMS.md").write_text(md)
    print(md, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
