from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

METHOD_ID = "ORBITTRACE_NULL_CALIBRATED_PERSISTENCE_V1"
NULL_REPLICATES = 16
YEARS = (2022, 2023)


def replicate_seed(rep: int) -> int:
    if not 0 <= int(rep) < NULL_REPLICATES:
        raise ValueError(f"replicate index out of range: {rep}")
    digest = hashlib.sha256(f"{METHOD_ID}|{int(rep)}".encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def permuted_solar_longitude_matrix(
    base_geo6: np.ndarray,
    solar_longitude_deg: np.ndarray,
    years: np.ndarray,
    rep: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return a deterministic within-year solar-longitude permutation null.

    Only GEO6 columns cos(sol), sin(sol) change. All other coordinates stay
    byte-identical to the real catalogue, while each year's empirical solar-
    longitude multiset is preserved exactly.
    """
    X = np.asarray(base_geo6, dtype=float)
    sols = np.asarray(solar_longitude_deg, dtype=float)
    yy = np.asarray(years, dtype=np.int64)
    if X.ndim != 2 or X.shape[1] != 6:
        raise ValueError(f"expected GEO6 matrix, got {X.shape}")
    if sols.shape != (X.shape[0],) or yy.shape != (X.shape[0],):
        raise ValueError("solar-longitude/year vectors must align with GEO6 rows")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(sols)):
        raise ValueError("non-finite input to survey-null permutation")
    if tuple(sorted(int(v) for v in np.unique(yy))) != YEARS:
        raise ValueError(f"expected exact years {YEARS}, got {tuple(sorted(int(v) for v in np.unique(yy)))}")

    rng = np.random.Generator(np.random.PCG64(replicate_seed(rep)))
    out = X.copy()
    report: dict[str, Any] = {
        "replicate": int(rep),
        "seed_uint64": int(replicate_seed(rep)),
        "years": {},
    }
    for year in YEARS:
        idx = np.flatnonzero(yy == year)
        if idx.size == 0:
            raise ValueError(f"year {year} has no rows")
        original = sols[idx].copy()
        permuted = rng.permutation(original)
        rad = np.radians(permuted)
        out[idx, 0] = np.cos(rad)
        out[idx, 1] = np.sin(rad)
        moved = int(np.sum(permuted != original))
        report["years"][str(year)] = {
            "count": int(idx.size),
            "moved": moved,
            "moved_fraction": float(moved / idx.size),
            "solar_longitude_sum": float(np.sum(original)),
            "solar_longitude_sq_sum": float(np.sum(original * original)),
        }
        # Exact multiset preservation, independent of floating summation.
        if not np.array_equal(np.sort(permuted), np.sort(original)):
            raise RuntimeError(f"solar-longitude multiset changed for {year}")
        if moved <= 0:
            raise RuntimeError(f"null replicate {rep} was identity for {year}")

    if not np.array_equal(out[:, 2:], X[:, 2:]):
        raise RuntimeError("survey-null permutation changed radiant/speed GEO6 columns")
    return out, report


def pareto_tail_rate(
    member_count: int,
    synchronous_stability: float,
    null_candidates: list[tuple[int, float]],
) -> tuple[float, int, int]:
    n = int(member_count)
    s = float(synchronous_stability)
    if n <= 0 or not np.isfinite(s) or s < 0.0:
        raise ValueError("invalid real candidate size/stability")
    m = len(null_candidates)
    dominating = 0
    for nn_raw, ss_raw in null_candidates:
        nn = int(nn_raw)
        ss = float(ss_raw)
        if nn <= 0 or not np.isfinite(ss) or ss < 0.0:
            raise ValueError("invalid null candidate size/stability")
        if nn >= n and ss >= s:
            dominating += 1
    rate = (1.0 + dominating) / (1.0 + m)
    return float(rate), int(dominating), int(m)


def calibrate_candidates(
    candidates: list[dict[str, Any]],
    null_replicates: list[list[tuple[int, float]]],
) -> list[dict[str, Any]]:
    if len(null_replicates) != NULL_REPLICATES:
        raise ValueError(f"expected {NULL_REPLICATES} null replicates, got {len(null_replicates)}")
    out: list[dict[str, Any]] = []
    for row in candidates:
        rates: list[float] = []
        dominance: list[dict[str, Any]] = []
        for rep, null_rows in enumerate(null_replicates):
            rate, dom, total = pareto_tail_rate(
                int(row["member_count"]),
                float(row["synchronous_stability"]),
                null_rows,
            )
            rates.append(rate)
            dominance.append({
                "replicate": rep,
                "dominating_null_candidates": dom,
                "null_candidate_count": total,
                "tail_rate": rate,
            })
        new = dict(row)
        new["null_tail_rate_mean"] = float(np.mean(rates))
        new["null_tail_rate_median"] = float(np.median(rates))
        new["null_tail_rates"] = dominance
        out.append(new)

    out.sort(key=lambda f: (
        f["null_tail_rate_mean"],
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out
