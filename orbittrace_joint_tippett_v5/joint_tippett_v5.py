"""OrbitTrace v5 jointly calibrated Tippett reporting statistic.

This module does not define the continuous ranking. It combines the frozen v3
multi-anchor energy and frozen fixed4 significance channels only for reporting.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

METHOD_ID = "orbittrace_joint_tippett_v5"
COMPONENTS = ("orbittrace_multi_anchor_wavelet_energy_v3", "orbittrace_fixed4")
REPORTING_ALPHA = 0.05


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
    if len(pvalues) != 2 or np.any((pvalues <= 0.0) | (pvalues > 1.0)):
        raise ValueError("exactly two component p-values in (0,1] required")
    return float(-np.log(np.min(pvalues)))


def calibration_joint_statistics(
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> np.ndarray:
    v3 = _finite_vector(v3_calibration, "v3 calibration")
    fixed4 = _finite_vector(fixed4_calibration, "fixed4 calibration")
    if v3.shape != fixed4.shape:
        raise ValueError("component calibration shapes differ")
    v3_p = leave_one_out_survival_pvalues(v3)
    fixed4_p = leave_one_out_survival_pvalues(fixed4)
    statistics = -np.log(np.minimum(v3_p, fixed4_p))
    if not np.all(np.isfinite(statistics)):
        raise ValueError("non-finite joint calibration statistics")
    return statistics.astype(np.float64)


def target_joint_statistic(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> float:
    return tippett_statistic((
        target_survival_pvalue(v3_score, v3_calibration),
        target_survival_pvalue(fixed4_score, fixed4_calibration),
    ))


def final_joint_pvalue(target_statistic: float, calibration_statistics: Sequence[float] | np.ndarray) -> float:
    return target_survival_pvalue(target_statistic, calibration_statistics)


def score_and_pvalue(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> tuple[float, float]:
    null_statistics = calibration_joint_statistics(v3_calibration, fixed4_calibration)
    statistic = target_joint_statistic(v3_score, fixed4_score, v3_calibration, fixed4_calibration)
    return statistic, final_joint_pvalue(statistic, null_statistics)


def detected(joint_pvalue: float) -> bool:
    value = float(joint_pvalue)
    if not np.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError("joint p-value must lie in (0,1]")
    return value <= REPORTING_ALPHA


def self_test() -> dict[str, bool]:
    v3 = np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], dtype=np.float64)
    fixed4 = np.asarray([0.7, 0.5, 0.6, 0.3, 0.4, 0.2, 0.1, 0.0], dtype=np.float64)
    null = calibration_joint_statistics(v3, fixed4)
    strong_v3, p_strong_v3 = score_and_pvalue(2.0, 0.1, v3, fixed4)
    strong_f4, p_strong_f4 = score_and_pvalue(0.1, 2.0, v3, fixed4)
    weak, p_weak = score_and_pvalue(-2.0, -2.0, v3, fixed4)
    perm = np.asarray([7, 1, 5, 3, 0, 6, 4, 2])
    permuted = calibration_joint_statistics(v3[perm], fixed4[perm])
    return {
        "null_finite": bool(np.all(np.isfinite(null))),
        "strong_v3_detected": strong_v3 > weak and p_strong_v3 < p_weak,
        "strong_fixed4_detected": strong_f4 > weak and p_strong_f4 < p_weak,
        "component_exchange_symmetric": np.isclose(strong_v3, strong_f4, atol=0.0, rtol=0.0),
        "paired_permutation_invariant": np.allclose(np.sort(null), np.sort(permuted), atol=0.0, rtol=0.0),
        "no_weights": COMPONENTS == ("orbittrace_multi_anchor_wavelet_energy_v3", "orbittrace_fixed4"),
        "fixed_alpha": REPORTING_ALPHA == 0.05,
        "fixed_identifier": METHOD_ID == "orbittrace_joint_tippett_v5",
    }
