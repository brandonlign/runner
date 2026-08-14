#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

BLIND_LOW = 20.0
BLIND_HIGH = 55.0
ARC_ORIGIN = 55.0
ARC_LENGTH = 325.0


@dataclass(frozen=True)
class PhaseEqualizationResult:
    raw_sol: np.ndarray
    unwrapped_s: np.ndarray
    equalized_sol: np.ndarray


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _as_raw_sol(events: Sequence[dict[str, Any]]) -> np.ndarray:
    raw = np.asarray([float(e["sol"]) % 360.0 for e in events], dtype=np.float64)
    _require(raw.ndim == 1 and raw.size == len(events), "invalid raw solar-longitude vector")
    _require(raw.size > 0, "phase equalization requires nonempty event sample")
    _require(np.all(np.isfinite(raw)), "non-finite raw solar longitude")
    _require(not np.any((raw >= BLIND_LOW) & (raw <= BLIND_HIGH)), "protected solar longitude reached phase equalization")
    return raw


def equalize_phase(events: Sequence[dict[str, Any]]) -> PhaseEqualizationResult:
    """Parameter-free pooled empirical cumulative-intensity warp.

    The input must already have the inclusive [20,55] protected interval removed.
    Only ``event['sol']`` is used to construct the transform.
    """
    raw = _as_raw_sol(events)
    s = np.mod(raw - ARC_ORIGIN, 360.0).astype(np.float64, copy=False)
    _require(np.all(s > 0.0), "accessible phase hit lower arc boundary")
    _require(np.all(s < ARC_LENGTH), "accessible phase hit/entered protected upper arc boundary")

    order = np.argsort(s, kind="mergesort")
    sorted_s = s[order]
    n = int(sorted_s.size)
    u_sorted = np.empty(n, dtype=np.float64)

    start = 0
    while start < n:
        end = start + 1
        value = sorted_s[start]
        while end < n and sorted_s[end] == value:
            end += 1
        # lo=start and hi=end are exact counts below / at-or-below this tied value.
        u = (float(start) + float(end)) / (2.0 * float(n))
        u_sorted[start:end] = u
        start = end

    u = np.empty(n, dtype=np.float64)
    u[order] = u_sorted
    _require(np.all(u > 0.0) and np.all(u < 1.0), "empirical mid-distribution left open unit interval")

    s_eq = ARC_LENGTH * u
    sol_eq = np.mod(ARC_ORIGIN + s_eq, 360.0).astype(np.float64, copy=False)
    _require(np.all(np.isfinite(sol_eq)), "non-finite equalized phase")
    _require(not np.any((sol_eq >= BLIND_LOW) & (sol_eq <= BLIND_HIGH)), "phase equalization entered protected interval")

    return PhaseEqualizationResult(raw_sol=raw, unwrapped_s=s, equalized_sol=sol_eq)


def equalized_events(events: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], PhaseEqualizationResult]:
    result = equalize_phase(events)
    out: list[dict[str, Any]] = []
    for i, event in enumerate(events):
        row = dict(event)
        row["sol"] = float(result.equalized_sol[i])
        out.append(row)
    return out, result
