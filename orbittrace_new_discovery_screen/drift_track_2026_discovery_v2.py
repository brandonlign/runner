#!/usr/bin/env python3
"""Implementation-corrected entry point for the frozen 2026 drift-track protocol.

The scientific protocol is unchanged from
``orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_2026_DISCOVERY_PROTOCOL.md``.
This wrapper repairs two implementation details before the discovery lane has
been executed:

1. pseudo-track intercept translation must make the shifted track pass exactly
   through its seed meteor at the shifted reference solar longitude; and
2. unparsable timestamps must not be counted as observing nights.

All thresholds, detector geometry, catalogue rules, validation years, and null
statistics remain exactly as frozen.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_2026_discovery as impl


def night_station_summary_fixed(frame: pd.DataFrame) -> dict[str, Any]:
    parsed = pd.to_datetime(
        frame["beginning_utc_time"], errors="coerce", utc=True, format="mixed"
    )
    nights = parsed.dt.floor("D")
    night_counts = nights.value_counts(dropna=True)
    station_sets = frame["participating_stations"].fillna("").astype(str)
    all_stations = (
        set().union(*(base.station_tokens(value) for value in station_sets))
        if len(frame)
        else set()
    )
    station_set_fraction = (
        float(station_sets.value_counts(normalize=True).iloc[0]) if len(frame) else 1.0
    )
    return {
        "nights": int(nights.nunique(dropna=True)),
        "stations": int(len(all_stations)),
        "max_night_fraction": (
            float(night_counts.iloc[0] / len(frame)) if len(night_counts) else 1.0
        ),
        "max_station_set_fraction": station_set_fraction,
    }


def pseudo_track_null_fixed(
    track: dict[str, Any],
    discovery: dict[str, Any],
    validation: dict[int, dict[str, Any]],
    candidate_validation: dict[str, Any],
) -> dict[str, Any]:
    seeds = impl.local_seed_pool(track, discovery)
    if len(seeds) == 0:
        return {
            "status": "LOCAL_NULL_INSUFFICIENT",
            "pseudo_track_count": 0,
            "pass": False,
        }

    data = discovery["data"]
    sol_u = discovery["sol_unwrapped"]
    candidate_r = min(
        int(candidate_validation["2025"]["members"]),
        int(candidate_validation["2024"]["members"]),
    )
    candidate_t = (
        int(candidate_validation["2025"]["members"])
        + int(candidate_validation["2024"]["members"])
    )

    r_values = np.zeros(len(seeds), dtype=np.int64)
    t_values = np.zeros(len(seeds), dtype=np.int64)
    seed_ids = (
        data.iloc[seeds]["unique_trajectory_identifier"].astype(str).tolist()
    )

    reference_sol = float(track["reference_sol_unwrapped"])
    reference_slon = float(track["reference_slon_unwrapped"])
    reference_beta = float(track["reference_beta"])
    reference_vg = float(track["reference_vg"])

    for j, seed_index in enumerate(seeds):
        seed_sol_u = float(sol_u[seed_index])
        time_shift = seed_sol_u - reference_sol

        # fixed_track_membership shifts the pseudo-track reference longitude by
        # time_shift.  Therefore the shifted track has dx == 0 at the seed.
        # Its translated reference intercept must equal the seed coordinates
        # themselves, not the original track prediction at seed longitude.
        slon_offset = float(
            base.circ_diff(discovery["slon"][seed_index], reference_slon)
        )
        beta_offset = float(discovery["beta"][seed_index] - reference_beta)
        vg_offset = float(discovery["vg"][seed_index] - reference_vg)

        seed_orbit = data.iloc[int(seed_index)][base.ORBIT_COLUMNS].to_numpy(
            dtype=float
        )
        counts: list[int] = []
        for year in impl.VALIDATION_YEARS:
            selected, _d = impl.fixed_track_membership(
                track,
                validation[year],
                float(discovery["sol_reference"]),
                seed_orbit,
                interval_center_shift=time_shift,
                intercept_offsets=(slon_offset, beta_offset, vg_offset),
            )
            counts.append(int(selected.sum()))
        r_values[j] = min(counts)
        t_values[j] = sum(counts)

    q99_r = int(np.quantile(r_values, 0.99, method="higher"))
    tied = t_values[r_values == q99_r]
    q99_t = int(np.quantile(tied, 0.99, method="higher")) if len(tied) else 0
    passed = candidate_r > q99_r or (
        candidate_r == q99_r and candidate_t > q99_t
    )
    order = sorted(
        range(len(seeds)),
        key=lambda idx: (-int(r_values[idx]), -int(t_values[idx]), seed_ids[idx]),
    )[:20]
    return {
        "status": "EXECUTED",
        "pseudo_track_count": int(len(seeds)),
        "candidate_R": int(candidate_r),
        "candidate_T": int(candidate_t),
        "null_R_q99_higher": int(q99_r),
        "null_T_q99_higher_given_R_q99": int(q99_t),
        "null_R_max": int(r_values.max()),
        "null_T_max": int(t_values.max()),
        "pass": bool(passed),
        "top_pseudo_tracks": [
            {
                "seed_event_id": seed_ids[idx],
                "R": int(r_values[idx]),
                "T": int(t_values[idx]),
            }
            for idx in order
        ],
    }


def main() -> int:
    impl.night_station_summary = night_station_summary_fixed
    impl.pseudo_track_null = pseudo_track_null_fixed
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
