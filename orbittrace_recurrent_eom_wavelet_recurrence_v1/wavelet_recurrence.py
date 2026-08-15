from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

METHOD_ID = "orbittrace_recurrent_eom_wavelet_recurrence_v1"
YEARS = (2022, 2023)
MIN_ANNUAL_MEMBERS = 4


@dataclass(frozen=True)
class WaveletRecurrenceStat:
    annual_energy_2022: float
    annual_energy_2023: float
    recurrence_score: float
    annual_count_2022: int
    annual_count_2023: int


def _annual_energy(rows: list[dict[str, Any]], v3: Any) -> float:
    if len(rows) < MIN_ANNUAL_MEMBERS:
        return 0.0

    class Episode:
        pass

    episode = Episode()
    episode.sun_lon = np.asarray([float(row["sun_lon"]) for row in rows], dtype=np.float64)
    episode.ecl_lat = np.asarray([float(row["ecl_lat"]) for row in rows], dtype=np.float64)
    episode.vg = np.asarray([float(row["vg"]) for row in rows], dtype=np.float64)
    if not (
        np.all(np.isfinite(episode.sun_lon))
        and np.all(np.isfinite(episode.ecl_lat))
        and np.all(np.isfinite(episode.vg))
        and np.all(episode.vg > 0.0)
    ):
        raise ValueError("invalid annual candidate geometry")
    score = float(v3.multi_anchor_energy_episode_score(episode))
    if not np.isfinite(score) or score < 0.0:
        raise ValueError("invalid annual v3 wavelet energy")
    return score


def candidate_wavelet_recurrence(rows: Iterable[dict[str, Any]], v3: Any) -> WaveletRecurrenceStat:
    rows = list(rows)
    by_year = {year: [] for year in YEARS}
    for row in rows:
        year = int(row["year"])
        if year not in by_year:
            raise ValueError(f"unexpected year {year}")
        by_year[year].append(row)

    e22 = _annual_energy(by_year[2022], v3)
    e23 = _annual_energy(by_year[2023], v3)
    recurrence = float(min(e22, e23))
    if not np.isfinite(recurrence) or recurrence < 0.0:
        raise ValueError("invalid wavelet recurrence score")
    return WaveletRecurrenceStat(
        annual_energy_2022=float(e22),
        annual_energy_2023=float(e23),
        recurrence_score=recurrence,
        annual_count_2022=len(by_year[2022]),
        annual_count_2023=len(by_year[2023]),
    )
