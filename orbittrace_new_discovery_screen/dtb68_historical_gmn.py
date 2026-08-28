#!/usr/bin/env python3
"""Frozen 2019-2023 GMN characterization of DTb68bb6b678e43478."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_2026_discovery as impl

TRACK: dict[str, Any] = {
    "reference_sol_unwrapped": 316.185573,
    "reference_slon_unwrapped": 144.84784445604302,
    "reference_beta": -53.00940285307881,
    "reference_vg": 14.934766201039407,
    "slopes": {
        "slon_per_sol": -0.5719447594651568,
        "beta_per_sol": 0.37813787817134115,
        "vg_per_sol": -0.33737201749209544,
    },
    # The implementation pads by exactly one degree at each end.
    "solar_min_unwrapped": 314.310424,
    "solar_max_unwrapped": 317.766604,
    "orbit_medoid": [0.601806, 0.947145, 17.518079, 26.456307, 136.215206],
}
YEARS = (2019, 2020, 2021, 2022, 2023)
MONTH = 2


def valid_night_station(frame: pd.DataFrame) -> dict[str, int]:
    parsed = pd.to_datetime(frame["beginning_utc_time"], errors="coerce", utc=True, format="mixed")
    nights = int(parsed.dt.floor("D").nunique(dropna=True))
    stations = set()
    for value in frame["participating_stations"].fillna("").astype(str):
        stations |= base.station_tokens(value)
    return {"nights": nights, "stations": int(len(stations))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    r = requests.get(base.MDC_URL, timeout=90)
    r.raise_for_status()
    mdc = r.json()
    _catalog, current_codes = base.flatten_mdc(mdc)

    results: dict[str, Any] = {}
    pooled_d: list[float] = []
    pooled_ids: list[str] = []
    for year in YEARS:
        print(f"Loading GMN {year}-02", flush=True)
        prepared = impl.prepare_residual(year, MONTH, current_codes)
        selected, d = impl.fixed_track_membership(
            TRACK,
            prepared,
            TRACK["reference_sol_unwrapped"],
            np.asarray(TRACK["orbit_medoid"], dtype=float),
        )
        frame = prepared["data"].loc[selected].reset_index(drop=True)
        ns = valid_night_station(frame)
        ds = d[selected]
        count = int(selected.sum())
        d50 = float(np.median(ds)) if count else None
        d90 = float(np.quantile(ds, 0.90)) if count else None
        strong = bool(
            count >= 8
            and ns["nights"] >= 3
            and ns["stations"] >= 5
            and d50 is not None
            and d50 <= 0.12
        )
        ids = frame["unique_trajectory_identifier"].astype(str).tolist()
        codes = {
            str(k): int(v)
            for k, v in frame["iau_code"].fillna("").astype(str).value_counts().items()
        }
        results[str(year)] = {
            "residual_rows": int(len(prepared["data"])),
            "members": count,
            "nights": ns["nights"],
            "stations": ns["stations"],
            "median_d_sh_to_frozen": d50,
            "q90_d_sh_to_frozen": d90,
            "strong_recurrence": strong,
            "event_ids": ids,
            "selected_residual_code_counts": codes,
        }
        pooled_d.extend(map(float, ds.tolist()))
        pooled_ids.extend(ids)
        print(f"  members={count} nights={ns['nights']} stations={ns['stations']} D50={d50}", flush=True)

    represented = [int(y) for y, x in results.items() if x["members"] > 0]
    years_ge2 = [int(y) for y, x in results.items() if x["members"] >= 2]
    pooled = {
        "members": int(len(pooled_ids)),
        "represented_years": represented,
        "years_with_ge2_members": years_ge2,
        "median_d_sh_to_frozen": float(np.median(pooled_d)) if pooled_d else None,
        "q90_d_sh_to_frozen": float(np.quantile(pooled_d, 0.90)) if pooled_d else None,
    }
    payload = {
        "stage": "dtb68_historical_gmn_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DTB68_HISTORICAL_GMN_PROTOCOL.md",
        "mdc_version": mdc.get("version"),
        "frozen_lead": "DTb68bb6b678e43478",
        "years": results,
        "pooled": pooled,
    }
    (args.out / "dtb68_historical_gmn.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        "# DTb68 historical GMN extension",
        "",
        f"Current MDC residual definition: **{mdc.get('version')}**.",
        "",
        "| year | residual rows | members | nights | stations | D50 | D90 | strong recurrence |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for year in YEARS:
        x = results[str(year)]
        d50 = "—" if x["median_d_sh_to_frozen"] is None else f"{x['median_d_sh_to_frozen']:.4f}"
        d90 = "—" if x["q90_d_sh_to_frozen"] is None else f"{x['q90_d_sh_to_frozen']:.4f}"
        lines.append(
            f"| {year} | {x['residual_rows']} | {x['members']} | {x['nights']} | {x['stations']} | {d50} | {d90} | {x['strong_recurrence']} |"
        )
    lines += ["", f"Pooled: `{pooled}`"]
    md = "\n".join(lines) + "\n"
    (args.out / "DTB68_HISTORICAL_GMN.md").write_text(md, encoding="utf-8")
    print(md, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
