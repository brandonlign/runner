#!/usr/bin/env python3
"""Geometry-only GMN parser for v16 pretruth development.

This parser intentionally has no shower/IAU column lookup and returns no truth mapping. It copies
the frozen GMN geometry selection used by the historical fixed4 scanner: finite sol/lambda/beta/Vg,
0<=sol<360, 0<=lambda<360, -90<=beta<=90, 5<=Vg<=75, duplicate-ID removal, and inclusive
20-55 degree solar-longitude exclusion before canonical rows are emitted.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader

from orbittrace_v15_canonical_events_v1.canonical import BLIND_HIGH, BLIND_LOW, canonical_record


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def pick(columns: list[str], choices: list[tuple[str, ...]]) -> str:
    normalized = {column: norm(column) for column in columns}
    for choice in choices:
        terms = [norm(term) for term in choice]
        found = [column for column, value in normalized.items() if all(term in value for term in terms)]
        if found:
            return min(found, key=len)
    raise KeyError(f"No column matched {choices}; columns={columns}")


def geometry_column_map(frame: pd.DataFrame) -> dict[str, str]:
    cols = list(map(str, frame.columns))
    return {
        "id": pick(cols, [("unique", "trajectory", "identifier"), ("trajectory", "identifier")]),
        "sol": pick(cols, [("sol", "lon", "deg"), ("solar", "longitude")]),
        "lam": pick(cols, [("lamgeo", "deg"), ("geocentric", "ecliptic", "longitude")]),
        "bet": pick(cols, [("betgeo", "deg"), ("geocentric", "ecliptic", "latitude")]),
        "vg": pick(cols, [("vgeo", "km", "s"), ("geocentric", "velocity")]),
    }


def read_gmn_frame(text: str) -> pd.DataFrame:
    original = pd.to_datetime

    def tolerant_to_datetime(arg: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return original(arg, *args, **kwargs)
        except ValueError:
            repaired = dict(kwargs)
            repaired.pop("format", None)
            return original(arg, *args, format="mixed", **repaired)

    pd.to_datetime = tolerant_to_datetime
    try:
        return reader.read_data(text, output_camel_case=True).reset_index(drop=False)
    finally:
        pd.to_datetime = original


def parse_pair(*, years: tuple[int, int], base: Any) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
    require(len(years) == 2 and years[0] != years[1], f"invalid year pair {years}")
    month_keys = tuple(f"{year}-{month:02d}" for year in years for month in range(1, 13))
    scan_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    for key in month_keys:
        year = int(key[:4])
        text = dd.get_monthly_file_content_by_date(key)
        payload = text.encode("utf-8")
        frame = read_gmn_frame(text)
        columns = geometry_column_map(frame)
        data = pd.DataFrame({
            "id": frame[columns["id"]].astype(str),
            "sol": pd.to_numeric(frame[columns["sol"]], errors="coerce"),
            "lam": pd.to_numeric(frame[columns["lam"]], errors="coerce"),
            "bet": pd.to_numeric(frame[columns["bet"]], errors="coerce"),
            "vg": pd.to_numeric(frame[columns["vg"]], errors="coerce"),
        })
        valid = np.isfinite(data[["sol", "lam", "bet", "vg"]]).all(axis=1)
        valid &= data["sol"].between(0.0, 360.0, inclusive="left")
        valid &= data["lam"].between(0.0, 360.0, inclusive="left")
        valid &= data["bet"].between(-90.0, 90.0, inclusive="both")
        valid &= data["vg"].between(5.0, 75.0, inclusive="both")
        valid &= ~data["sol"].between(BLIND_LOW, BLIND_HIGH, inclusive="both")
        selected = data.loc[valid].copy()
        duplicate_rows = int(selected["id"].isin(seen).sum())
        selected = selected.loc[~selected["id"].isin(seen)]
        seen.update(selected["id"].tolist())
        sun_lon = base.wrap180(selected["lam"].to_numpy(float) - selected["sol"].to_numpy(float))
        rows: list[dict[str, Any]] = []
        for event_id, sol, lon, bet, vg in zip(
            selected["id"].tolist(),
            selected["sol"].to_numpy(float),
            np.asarray(sun_lon, dtype=float),
            selected["bet"].to_numpy(float),
            selected["vg"].to_numpy(float),
        ):
            row = canonical_record(
                event_id=str(event_id),
                year=year,
                sol=float(sol),
                sun_lon=float(lon),
                ecl_lat=float(bet),
                vg=float(vg),
            )
            require(not (BLIND_LOW <= row["sol"] <= BLIND_HIGH), "target interval survived geometry parser")
            rows.append(row)
        scan_by_year[year].extend(rows)
        sources.append({
            "key": key,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "raw_rows": int(len(frame)),
            "selected_rows_after_blind_exclusion": len(rows),
            "duplicate_rows_removed": duplicate_rows,
            "geometry_columns": columns,
            "truth_column_resolved": False,
        })

    for year in years:
        require(len(scan_by_year[year]) >= 1000, f"insufficient GMN geometry rows for {year}: {len(scan_by_year[year])}")
    require([row["key"] for row in sources] == list(month_keys), "GMN monthly source universe changed")
    return dict(scan_by_year), sources
