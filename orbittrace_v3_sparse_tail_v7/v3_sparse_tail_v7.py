"""OrbitTrace v7: frozen v3-primary fixed4 sparse-tail augmentation.

The margin 0.25 is inherited from the independently frozen Brown-primary sparse-tail
experiment. v7 changes the primary component to the stronger frozen v3 ranking and
recalibrates the complete max statistic against paired leave-one-out nulls.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

METHOD_ID = "orbittrace_v3_primary_fixed4_margin_025_v7"
PRIMARY = "orbittrace_multi_anchor_wavelet_energy_v3"
SPARSE = "orbittrace_fixed4"
MARGIN = 0.25
REPORTING_ALPHA = 0.05


def _finite_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    return array


def target_survival_pvalue(target: float, calibration: Sequence[float] | np.ndarray) -> float:
    values = _finite_vector(calibration, "calibration")
    value = float(target)
    if not math.isfinite(value):
        raise ValueError("target score must be finite")
    return float((1.0 + np.count_nonzero(values >= value)) / (len(values) + 1.0))


def leave_one_out_survival_pvalues(calibration: Sequence[float] | np.ndarray) -> np.ndarray:
    values = _finite_vector(calibration, "calibration")
    comparisons = values[None, :] >= values[:, None]
    counts_including_self = np.count_nonzero(comparisons, axis=1)
    counts_excluding_self = counts_including_self - 1
    result = (1.0 + counts_excluding_self.astype(np.float64)) / float(len(values))
    if not np.all((result > 0.0) & (result <= 1.0)):
        raise RuntimeError("invalid leave-one-out p-values")
    return result


def statistic_from_pvalues(p_v3: float, p_fixed4: float) -> float:
    primary = float(p_v3)
    sparse = float(p_fixed4)
    if not (0.0 < primary <= 1.0 and 0.0 < sparse <= 1.0):
        raise ValueError("component p-values must lie in (0,1]")
    return float(max(-math.log(primary), -math.log(sparse) - MARGIN))


def calibration_statistics(
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> np.ndarray:
    v3 = _finite_vector(v3_calibration, "v3 calibration")
    fixed4 = _finite_vector(fixed4_calibration, "fixed4 calibration")
    if v3.shape != fixed4.shape:
        raise ValueError("paired calibration vectors must have equal shape")
    p_v3 = leave_one_out_survival_pvalues(v3)
    p_fixed4 = leave_one_out_survival_pvalues(fixed4)
    statistics = np.maximum(-np.log(p_v3), -np.log(p_fixed4) - MARGIN)
    if not np.all(np.isfinite(statistics)):
        raise RuntimeError("non-finite v7 null statistics")
    return statistics.astype(np.float64, copy=False)


def target_statistic(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> float:
    return statistic_from_pvalues(
        target_survival_pvalue(v3_score, v3_calibration),
        target_survival_pvalue(fixed4_score, fixed4_calibration),
    )


def final_pvalue(target_statistic_value: float, null_statistics: Sequence[float] | np.ndarray) -> float:
    return target_survival_pvalue(target_statistic_value, null_statistics)


def score_and_pvalue(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> tuple[float, float]:
    null = calibration_statistics(v3_calibration, fixed4_calibration)
    statistic = target_statistic(v3_score, fixed4_score, v3_calibration, fixed4_calibration)
    return statistic, final_pvalue(statistic, null)


def detected(final_p: float) -> bool:
    value = float(final_p)
    if not math.isfinite(value) or not (0.0 < value <= 1.0):
        raise ValueError("invalid final p-value")
    return value <= REPORTING_ALPHA


def self_test() -> dict[str, bool]:
    fixed4 = np.asarray([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float64)
    v3 = np.asarray([7.0, 5.0, 6.0, 3.0, 4.0, 2.0, 1.0, 0.0], dtype=np.float64)
    null = calibration_statistics(v3, fixed4)
    primary_stat, primary_p = score_and_pvalue(9.0, 0.5, v3, fixed4)
    sparse_stat, sparse_p = score_and_pvalue(0.5, 9.0, v3, fixed4)
    equal = statistic_from_pvalues(0.1, 0.1)
    sparse_better = statistic_from_pvalues(0.1, 0.05)
    perm = np.asarray([7, 1, 5, 3, 0, 6, 4, 2])
    permuted = calibration_statistics(v3[perm], fixed4[perm])
    return {
        "method_id": METHOD_ID == "orbittrace_v3_primary_fixed4_margin_025_v7",
        "components_frozen": PRIMARY == "orbittrace_multi_anchor_wavelet_energy_v3" and SPARSE == "orbittrace_fixed4",
        "margin_inherited": MARGIN == 0.25,
        "reporting_alpha_frozen": REPORTING_ALPHA == 0.05,
        "null_finite": bool(np.all(np.isfinite(null))),
        "primary_signal_increases_statistic": primary_stat > equal and primary_p <= 1.0,
        "sparse_signal_increases_statistic": sparse_stat > equal and sparse_p <= 1.0,
        "v3_primary_at_equal_p": math.isclose(equal, -math.log(0.1), abs_tol=1e-12, rel_tol=0.0),
        "fixed4_requires_margin": sparse_better > -math.log(0.1),
        "paired_permutation_invariant": np.allclose(np.sort(null), np.sort(permuted), atol=0.0, rtol=0.0),
    }
