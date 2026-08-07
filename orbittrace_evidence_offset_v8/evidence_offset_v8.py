"""OrbitTrace v8 calibrated evidence-offset candidate family.

All candidates combine the same frozen v3 and fixed4 scores. Only the fixed,
preregistered relative log-evidence offset differs. Every candidate receives its
own paired leave-one-out empirical null calibration.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

PRIMARY = "orbittrace_multi_anchor_wavelet_energy_v3"
SPARSE = "orbittrace_fixed4"
REPORTING_ALPHA = 0.05
OFFSETS = (-0.75, -0.50, -0.25, 0.00, 0.25, 0.50)
METHODS = (
    "orbittrace_v3_fixed4_offset_neg075_v8",
    "orbittrace_v3_fixed4_offset_neg050_v8",
    "orbittrace_v3_fixed4_offset_neg025_v8",
    "orbittrace_v3_fixed4_offset_000_v8",
    "orbittrace_v3_fixed4_offset_pos025_v8",
    "orbittrace_v3_fixed4_offset_pos050_v8",
)
METHOD_TO_OFFSET = dict(zip(METHODS, OFFSETS, strict=True))


def _finite(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or len(x) < 2 or not np.all(np.isfinite(x)):
        raise ValueError(f"invalid {name}")
    return x


def target_survival_pvalue(target: float, calibration: Sequence[float] | np.ndarray) -> float:
    x = _finite(calibration, "calibration")
    value = float(target)
    if not math.isfinite(value):
        raise ValueError("target must be finite")
    return float((1.0 + np.count_nonzero(x >= value)) / (len(x) + 1.0))


def leave_one_out_survival_pvalues(calibration: Sequence[float] | np.ndarray) -> np.ndarray:
    x = _finite(calibration, "calibration")
    comparisons = x[None, :] >= x[:, None]
    counts = np.count_nonzero(comparisons, axis=1) - 1
    p = (1.0 + counts.astype(np.float64)) / float(len(x))
    if not np.all((p > 0.0) & (p <= 1.0)):
        raise RuntimeError("invalid LOO p-values")
    return p


def statistic_from_pvalues(p_v3: float, p_fixed4: float, offset: float) -> float:
    a = float(p_v3); b = float(p_fixed4); m = float(offset)
    if not (0.0 < a <= 1.0 and 0.0 < b <= 1.0 and math.isfinite(m)):
        raise ValueError("invalid p-values or offset")
    return float(max(-math.log(a), -math.log(b) - m))


def calibration_statistics(
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
    offset: float,
) -> np.ndarray:
    v3 = _finite(v3_calibration, "v3 calibration")
    fixed4 = _finite(fixed4_calibration, "fixed4 calibration")
    if v3.shape != fixed4.shape:
        raise ValueError("paired calibration shape mismatch")
    p3 = leave_one_out_survival_pvalues(v3)
    p4 = leave_one_out_survival_pvalues(fixed4)
    stats = np.maximum(-np.log(p3), -np.log(p4) - float(offset))
    if not np.all(np.isfinite(stats)):
        raise RuntimeError("invalid null statistics")
    return stats.astype(np.float64, copy=False)


def target_statistic(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
    offset: float,
) -> float:
    return statistic_from_pvalues(
        target_survival_pvalue(v3_score, v3_calibration),
        target_survival_pvalue(fixed4_score, fixed4_calibration),
        offset,
    )


def final_pvalue(target_statistic_value: float, null_statistics: Sequence[float] | np.ndarray) -> float:
    return target_survival_pvalue(target_statistic_value, null_statistics)


def self_test() -> dict[str, bool]:
    v3 = np.asarray([7.,5.,6.,3.,4.,2.,1.,0.])
    fixed4 = np.asarray([0.,1.,2.,3.,4.,5.,6.,7.])
    nulls = {m: calibration_statistics(v3, fixed4, m) for m in OFFSETS}
    equal = {m: statistic_from_pvalues(0.1, 0.1, m) for m in OFFSETS}
    return {
        "offsets_exact": OFFSETS == (-0.75,-0.50,-0.25,0.00,0.25,0.50),
        "methods_exact": len(METHODS) == 6 and len(set(METHODS)) == 6,
        "mapping_exact": tuple(METHOD_TO_OFFSET[m] for m in METHODS) == OFFSETS,
        "paired_nulls_finite": all(np.all(np.isfinite(x)) for x in nulls.values()),
        "negative_offset_favors_sparse": equal[-0.75] > equal[0.0],
        "positive_offset_preserves_primary_at_equal_p": math.isclose(equal[0.25], -math.log(0.1), abs_tol=1e-12, rel_tol=0.0),
        "alpha_fixed": REPORTING_ALPHA == 0.05,
        "components_fixed": PRIMARY == "orbittrace_multi_anchor_wavelet_energy_v3" and SPARSE == "orbittrace_fixed4",
    }
