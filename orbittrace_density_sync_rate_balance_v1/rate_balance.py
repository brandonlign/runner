from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

METHOD_ID = "orbittrace_density_sync_rate_balance_v1"
EXPOSURES = {2022: 315_024, 2023: 423_658}


@dataclass(frozen=True)
class RateBalanceStat:
    n_2022: int
    n_2023: int
    rate_2022: float
    rate_2023: float
    balance: float


def compute_rate_balance(rows: Iterable[dict[str, Any]]) -> RateBalanceStat:
    rows = list(rows)
    years = [int(row["year"]) for row in rows]
    if any(year not in EXPOSURES for year in years):
        raise ValueError("unexpected year")
    n22 = sum(year == 2022 for year in years)
    n23 = sum(year == 2023 for year in years)
    r22 = float(n22 / EXPOSURES[2022])
    r23 = float(n23 / EXPOSURES[2023])
    denom = r22 + r23
    balance = 0.0 if denom <= 0.0 else float(2.0 * min(r22, r23) / denom)
    if not np.isfinite(balance) or balance < 0.0 or balance > 1.0 + 1e-15:
        raise ValueError("invalid recurrence balance")
    balance = float(np.clip(balance, 0.0, 1.0))
    return RateBalanceStat(n22, n23, r22, r23, balance)


def adjusted_score(synchronous_stability: float, stat: RateBalanceStat) -> float:
    s = float(synchronous_stability)
    if not np.isfinite(s) or s < 0.0:
        raise ValueError("invalid synchronous stability")
    score = s * stat.balance
    if not np.isfinite(score) or score < 0.0:
        raise ValueError("invalid adjusted score")
    return float(score)
