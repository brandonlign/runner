#!/usr/bin/env python3
"""Frozen wavelet-primary fixed4 sparse-tail augmentation."""
from __future__ import annotations

import math

import numpy as np

METHOD_ID = "wavelet_primary_fixed4_margin_025"
MARGIN = 0.25


def _as_finite_vector(values: np.ndarray | list[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 2 or not np.all(np.isfinite(array)):
        raise ValueError("expected a finite one-dimensional calibration vector")
    return array


def target_survival_pvalue(target: float, calibration: np.ndarray | list[float]) -> float:
    values = _as_finite_vector(calibration)
    target_value = float(target)
    if not math.isfinite(target_value):
        raise ValueError("target score must be finite")
    return float((1.0 + np.count_nonzero(values >= target_value)) / (len(values) + 1.0))


def leave_one_out_survival_pvalues(calibration: np.ndarray | list[float]) -> np.ndarray:
    values = _as_finite_vector(calibration)
    comparisons = values[None, :] >= values[:, None]
    counts_including_self = np.count_nonzero(comparisons, axis=1)
    counts_excluding_self = counts_including_self - 1
    return (1.0 + counts_excluding_self.astype(np.float64)) / float(len(values))


def statistic_from_pvalues(p_fixed4: float, p_wavelet: float) -> float:
    fixed4 = float(p_fixed4)
    wavelet = float(p_wavelet)
    if not (0.0 < fixed4 <= 1.0 and 0.0 < wavelet <= 1.0):
        raise ValueError("component p-values must lie in (0, 1]")
    return float(max(-math.log(wavelet), -math.log(fixed4) - MARGIN))


def calibration_statistics(
    fixed4_calibration: np.ndarray | list[float],
    wavelet_calibration: np.ndarray | list[float],
) -> np.ndarray:
    fixed4 = _as_finite_vector(fixed4_calibration)
    wavelet = _as_finite_vector(wavelet_calibration)
    if fixed4.shape != wavelet.shape:
        raise ValueError("paired component calibration vectors must have equal shape")
    p_fixed4 = leave_one_out_survival_pvalues(fixed4)
    p_wavelet = leave_one_out_survival_pvalues(wavelet)
    statistics = np.maximum(-np.log(p_wavelet), -np.log(p_fixed4) - MARGIN)
    if not np.all(np.isfinite(statistics)):
        raise RuntimeError("non-finite sparse-tail calibration statistic")
    return statistics.astype(np.float64, copy=False)


def target_statistic(
    fixed4_score: float,
    wavelet_score: float,
    fixed4_calibration: np.ndarray | list[float],
    wavelet_calibration: np.ndarray | list[float],
) -> float:
    p_fixed4 = target_survival_pvalue(fixed4_score, fixed4_calibration)
    p_wavelet = target_survival_pvalue(wavelet_score, wavelet_calibration)
    return statistic_from_pvalues(p_fixed4, p_wavelet)


def final_pvalue(target_statistic_value: float, null_statistics: np.ndarray | list[float]) -> float:
    return target_survival_pvalue(target_statistic_value, null_statistics)


def self_test() -> dict[str, bool]:
    fixed4 = np.asarray([0.0, 1.0, 2.0, 3.0], dtype=np.float64)
    wavelet = np.asarray([3.0, 2.0, 1.0, 0.0], dtype=np.float64)
    loo = leave_one_out_survival_pvalues(fixed4)
    null = calibration_statistics(fixed4, wavelet)
    target = target_statistic(3.5, 1.5, fixed4, wavelet)
    pvalue = final_pvalue(target, null)
    return {
        "method_id": METHOD_ID == "wavelet_primary_fixed4_margin_025",
        "margin": MARGIN == 0.25,
        "loo_shape": loo.shape == fixed4.shape,
        "loo_bounds": bool(np.all((loo > 0.0) & (loo <= 1.0))),
        "null_finite": bool(np.all(np.isfinite(null))),
        "target_finite": math.isfinite(target),
        "final_pvalue_bounds": 0.0 < pvalue <= 1.0,
        "wavelet_primary_at_equal_p": statistic_from_pvalues(0.1, 0.1) == -math.log(0.1),
        "fixed4_requires_margin": statistic_from_pvalues(0.05, 0.1) > -math.log(0.1),
    }


if __name__ == "__main__":
    checks = self_test()
    if not all(checks.values()):
        raise SystemExit(checks)
    print(checks)
