"""Frozen null-calibrated Tippett union of fixed4 and wavelet episode scores."""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

COMPONENTS = ("orbittrace_fixed4", "brown2010_wavelet_episode_core")
HYBRID_ID = "fixed4_wavelet_tippett_hybrid"


def _finite_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or not len(array) or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    return array


def target_survival_pvalue(score: float, calibration_scores: Sequence[float] | np.ndarray) -> float:
    calibration = _finite_vector(calibration_scores, "calibration scores")
    value = float(score)
    if not np.isfinite(value):
        raise ValueError("non-finite target score")
    return float((1 + np.sum(calibration >= value)) / (len(calibration) + 1))


def leave_one_out_survival_pvalues(calibration_scores: Sequence[float] | np.ndarray) -> np.ndarray:
    calibration = _finite_vector(calibration_scores, "calibration scores")
    if len(calibration) < 2:
        raise ValueError("leave-one-out calibration requires at least two scores")
    comparison = calibration[None, :] >= calibration[:, None]
    counts_including_self = comparison.sum(axis=1)
    pvalues = counts_including_self / len(calibration)
    if not np.all((pvalues > 0.0) & (pvalues <= 1.0)):
        raise ValueError("invalid leave-one-out p-values")
    return pvalues.astype(np.float64)


def tippett_statistic(component_pvalues: Iterable[float]) -> float:
    pvalues = _finite_vector(list(component_pvalues), "component p-values")
    if np.any((pvalues <= 0.0) | (pvalues > 1.0)):
        raise ValueError("component p-values must lie in (0,1]")
    return float(-np.log(np.min(pvalues)))


def calibration_hybrid_statistics(
    fixed4_calibration: Sequence[float] | np.ndarray,
    wavelet_calibration: Sequence[float] | np.ndarray,
) -> np.ndarray:
    fixed4 = _finite_vector(fixed4_calibration, "fixed4 calibration")
    wavelet = _finite_vector(wavelet_calibration, "wavelet calibration")
    if fixed4.shape != wavelet.shape:
        raise ValueError("component calibration shapes differ")
    fixed4_p = leave_one_out_survival_pvalues(fixed4)
    wavelet_p = leave_one_out_survival_pvalues(wavelet)
    statistics = -np.log(np.minimum(fixed4_p, wavelet_p))
    if not np.all(np.isfinite(statistics)):
        raise ValueError("non-finite hybrid calibration statistics")
    return statistics.astype(np.float64)


def target_hybrid_statistic(
    fixed4_score: float,
    wavelet_score: float,
    fixed4_calibration: Sequence[float] | np.ndarray,
    wavelet_calibration: Sequence[float] | np.ndarray,
) -> float:
    return tippett_statistic(
        (
            target_survival_pvalue(fixed4_score, fixed4_calibration),
            target_survival_pvalue(wavelet_score, wavelet_calibration),
        )
    )


def final_hybrid_pvalue(target_statistic: float, hybrid_calibration_statistics: Sequence[float] | np.ndarray) -> float:
    return target_survival_pvalue(target_statistic, hybrid_calibration_statistics)


def score_and_pvalue(
    fixed4_score: float,
    wavelet_score: float,
    fixed4_calibration: Sequence[float] | np.ndarray,
    wavelet_calibration: Sequence[float] | np.ndarray,
) -> tuple[float, float]:
    null_statistics = calibration_hybrid_statistics(fixed4_calibration, wavelet_calibration)
    statistic = target_hybrid_statistic(
        fixed4_score,
        wavelet_score,
        fixed4_calibration,
        wavelet_calibration,
    )
    return statistic, final_hybrid_pvalue(statistic, null_statistics)


def self_test() -> dict[str, bool]:
    fixed4 = np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], dtype=np.float64)
    wavelet = np.asarray([0.7, 0.5, 0.6, 0.3, 0.4, 0.2, 0.1, 0.0], dtype=np.float64)
    null = calibration_hybrid_statistics(fixed4, wavelet)
    strong_fixed, p_strong_fixed = score_and_pvalue(2.0, 0.1, fixed4, wavelet)
    strong_wavelet, p_strong_wavelet = score_and_pvalue(0.1, 2.0, fixed4, wavelet)
    weak_both, p_weak_both = score_and_pvalue(-2.0, -2.0, fixed4, wavelet)
    perm = np.asarray([7, 1, 5, 3, 0, 6, 4, 2])
    permuted = calibration_hybrid_statistics(fixed4[perm], wavelet[perm])
    return {
        "null_finite": bool(np.all(np.isfinite(null))),
        "strong_fixed_detected": strong_fixed > weak_both and p_strong_fixed < p_weak_both,
        "strong_wavelet_detected": strong_wavelet > weak_both and p_strong_wavelet < p_weak_both,
        "component_exchange_symmetric": np.isclose(strong_fixed, strong_wavelet, atol=0.0, rtol=0.0),
        "paired_permutation_invariant": np.allclose(np.sort(null), np.sort(permuted), atol=0.0, rtol=0.0),
        "no_weights": COMPONENTS == ("orbittrace_fixed4", "brown2010_wavelet_episode_core"),
        "fixed_identifier": HYBRID_ID == "fixed4_wavelet_tippett_hybrid",
    }
