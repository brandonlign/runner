from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

METHOD_ID = "orbittrace_density_sync_yearshift_v1"
YEARS = (2022, 2023)


@dataclass(frozen=True)
class YearShiftStat:
    n_total: int
    n_2022: int
    n_2023: int
    total_ss: float
    between_year_ss: float
    raw_r2: float
    adjusted_r2: float
    year_shift: float
    overlap: float


def compute_year_shift(rows: Iterable[dict[str, Any]], geo_matrix_fn: Any) -> YearShiftStat:
    rows = list(rows)
    if len(rows) < 3:
        raise ValueError("candidate must contain at least three rows")
    years = np.asarray([int(row["year"]) for row in rows], dtype=np.int64)
    if not np.all(np.isin(years, YEARS)):
        raise ValueError("unexpected year")
    x = np.asarray(geo_matrix_fn(rows), dtype=np.float64)
    if x.shape != (len(rows), 6) or not np.all(np.isfinite(x)):
        raise ValueError("invalid GEO6 matrix")

    n = len(rows)
    mask22 = years == 2022
    mask23 = years == 2023
    n22 = int(mask22.sum())
    n23 = int(mask23.sum())
    if n22 == 0 or n23 == 0:
        return YearShiftStat(n, n22, n23, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0)

    mu = x.mean(axis=0)
    mu22 = x[mask22].mean(axis=0)
    mu23 = x[mask23].mean(axis=0)
    total_ss = float(np.sum((x - mu) ** 2))
    between = float(n22 * np.sum((mu22 - mu) ** 2) + n23 * np.sum((mu23 - mu) ** 2))
    if total_ss <= 0.0:
        raw = 0.0
    else:
        raw = float(np.clip(between / total_ss, 0.0, 1.0))
    adjusted = float(1.0 - (1.0 - raw) * (n - 1.0) / (n - 2.0))
    shift = float(np.clip(max(0.0, adjusted), 0.0, 1.0))
    overlap = float(1.0 - shift)
    return YearShiftStat(n, n22, n23, total_ss, between, raw, adjusted, shift, overlap)


def adjusted_score(synchronous_stability: float, stat: YearShiftStat) -> float:
    s = float(synchronous_stability)
    if not np.isfinite(s) or s < 0.0:
        raise ValueError("invalid synchronous stability")
    score = s * stat.overlap
    if not np.isfinite(score) or score < 0.0:
        raise ValueError("invalid adjusted score")
    return float(score)
