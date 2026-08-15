from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

from recurrent_eom import _descendant_year_counts


@dataclass(frozen=True)
class ExposureEvidence:
    year_counts: tuple[int, int]
    global_probability_year0: float
    node_probability_year0: float
    kl_divergence: float
    log_likelihood_ratio: float
    exposure_weight: float


def exposure_weight(counts: tuple[int, int], totals: tuple[int, int]) -> ExposureEvidence:
    n0, n1 = (int(counts[0]), int(counts[1]))
    N0, N1 = (int(totals[0]), int(totals[1]))
    if n0 < 0 or n1 < 0 or N0 <= 0 or N1 <= 0:
        raise ValueError(f"invalid annual counts: node={counts}, totals={totals}")
    n = n0 + n1
    if n <= 0:
        raise ValueError("cluster node must contain descendants")
    N = N0 + N1
    p = float(N0) / float(N)
    phat = float(n0) / float(n)
    if not (0.0 < p < 1.0 and 0.0 <= phat <= 1.0):
        raise RuntimeError(f"invalid exposure probabilities p={p}, phat={phat}")

    d = 0.0
    if phat > 0.0:
        d += phat * math.log(phat / p)
    if phat < 1.0:
        qhat = 1.0 - phat
        q = 1.0 - p
        d += qhat * math.log(qhat / q)
    if not math.isfinite(d) or d < 0.0:
        raise RuntimeError(f"invalid Bernoulli KL divergence: {d}")
    log_lr = -float(n) * d
    weight = math.exp(log_lr)
    if not math.isfinite(log_lr) or not math.isfinite(weight):
        raise RuntimeError(f"non-finite exposure likelihood evidence: logLR={log_lr}, W={weight}")
    if log_lr > 0.0 or not (0.0 <= weight <= 1.0):
        raise RuntimeError(f"exposure likelihood ratio escaped mathematical range: logLR={log_lr}, W={weight}")
    return ExposureEvidence(
        year_counts=(n0, n1),
        global_probability_year0=p,
        node_probability_year0=phat,
        kl_divergence=float(d),
        log_likelihood_ratio=float(log_lr),
        exposure_weight=float(weight),
    )


def exposure_lr_stability(
    tree: np.ndarray,
    years: Iterable[int],
    recurrent_stability: dict[float, float],
) -> tuple[dict[float, float], dict[int, ExposureEvidence]]:
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError("year vector must align exactly with condensed-tree points")
    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(year_values) != 2:
        raise ValueError(f"exactly two observing years required, got {year_values}")
    totals = tuple(int(np.sum(years_arr == y)) for y in year_values)
    counts = _descendant_year_counts(tree, years_arr)

    out: dict[float, float] = {}
    evidence: dict[int, ExposureEvidence] = {}
    for key, rec in recurrent_stability.items():
        node = int(key)
        if node not in counts:
            raise RuntimeError(f"missing descendant annual counts for cluster node {node}")
        c = tuple(int(x) for x in counts[node])
        ev = exposure_weight(c, totals)
        value = float(rec) * float(ev.exposure_weight)
        if not np.isfinite(value) or value < 0.0:
            raise RuntimeError(f"invalid exposure-weighted recurrent stability for node {node}: {value}")
        out[float(node)] = value
        evidence[node] = ev
    return out, evidence
