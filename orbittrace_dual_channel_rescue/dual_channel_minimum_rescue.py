#!/usr/bin/env python3
"""Frozen wavelet-ranking plus minimum-fixed4-rescue decision architecture."""
from __future__ import annotations

from typing import Sequence

import numpy as np

METHOD_ID = "wavelet_rank_plus_minimum_fixed4_rescue"
WAVELET_ID = "brown2010_wavelet_episode_core"
FIXED4_ID = "orbittrace_fixed4"
BASE_ALPHA = 0.05
CALIBRATION_PER_BIN = 128
RESCUE_ALPHA = 1.0 / (CALIBRATION_PER_BIN + 1.0)
DECISION_RULE = "(p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)"


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


def detected(p_wavelet: float, p_fixed4: float) -> bool:
    wavelet = float(p_wavelet)
    fixed4 = float(p_fixed4)
    if not (np.isfinite(wavelet) and np.isfinite(fixed4)):
        raise ValueError("non-finite component p-value")
    if not (0.0 < wavelet <= 1.0 and 0.0 < fixed4 <= 1.0):
        raise ValueError("component p-values must lie in (0,1]")
    return bool(wavelet <= BASE_ALPHA or fixed4 <= RESCUE_ALPHA)


def self_test() -> dict[str, bool]:
    calibration = np.arange(CALIBRATION_PER_BIN, dtype=np.float64)
    minimum = target_survival_pvalue(float(CALIBRATION_PER_BIN + 1), calibration)
    return {
        "fixed_identifier": METHOD_ID == "wavelet_rank_plus_minimum_fixed4_rescue",
        "fixed_components": (WAVELET_ID, FIXED4_ID) == (
            "brown2010_wavelet_episode_core", "orbittrace_fixed4"
        ),
        "fixed_base_alpha": BASE_ALPHA == 0.05,
        "fixed_calibration_count": CALIBRATION_PER_BIN == 128,
        "minimum_p_exact": minimum == 1.0 / 129.0 == RESCUE_ALPHA,
        "wavelet_primary_detection": detected(0.04, 1.0),
        "fixed4_minimum_rescue": detected(1.0, RESCUE_ALPHA),
        "no_looser_fixed4_rescue": not detected(1.0, 2.0 / 129.0),
        "no_detection_when_both_weak": not detected(0.051, 1.0),
        "fixed_rule_text": DECISION_RULE == "(p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)",
    }


if __name__ == "__main__":
    checks = self_test()
    print(checks)
    if not all(checks.values()):
        raise SystemExit("dual-channel self-test failed")
