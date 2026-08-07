"""Frozen selected OrbitTrace v8 prospective method.

This module exposes only the two-year-selected +0.50 evidence-offset method. The
other five v8 development candidates are intentionally absent from prospective
scoring.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

import evidence_offset_v8 as family

METHOD_ID = "orbittrace_v3_fixed4_offset_pos050_v8"
PRIMARY = "orbittrace_multi_anchor_wavelet_energy_v3"
SPARSE = "orbittrace_fixed4"
OFFSET = 0.50
REPORTING_ALPHA = 0.05


def calibration_statistics(
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> np.ndarray:
    return family.calibration_statistics(v3_calibration, fixed4_calibration, OFFSET)


def target_statistic(
    v3_score: float,
    fixed4_score: float,
    v3_calibration: Sequence[float] | np.ndarray,
    fixed4_calibration: Sequence[float] | np.ndarray,
) -> float:
    return family.target_statistic(v3_score, fixed4_score, v3_calibration, fixed4_calibration, OFFSET)


def final_pvalue(target_statistic_value: float, null_statistics: Sequence[float] | np.ndarray) -> float:
    return family.final_pvalue(target_statistic_value, null_statistics)


def self_test() -> dict[str, bool]:
    v3 = np.asarray([7., 5., 6., 3., 4., 2., 1., 0.])
    fixed4 = np.asarray([0., 1., 2., 3., 4., 5., 6., 7.])
    null = calibration_statistics(v3, fixed4)
    stat = target_statistic(9.0, 0.5, v3, fixed4)
    p = final_pvalue(stat, null)
    return {
        "selected_id_exact": METHOD_ID == "orbittrace_v3_fixed4_offset_pos050_v8",
        "selected_offset_exact": OFFSET == 0.50,
        "components_exact": PRIMARY == "orbittrace_multi_anchor_wavelet_energy_v3" and SPARSE == "orbittrace_fixed4",
        "reporting_alpha_exact": REPORTING_ALPHA == 0.05,
        "family_mapping_matches_freeze": family.METHOD_TO_OFFSET[METHOD_ID] == OFFSET,
        "null_finite": bool(np.all(np.isfinite(null))),
        "target_finite": bool(np.isfinite(stat) and np.isfinite(p) and 0.0 < p <= 1.0),
    }
