"""Frozen OrbitTrace v5 high-resolution reporting decision.

The primary and sparse scores are unchanged predecessor functions. This module
freezes only the calibration resolution and reporting thresholds promoted by
the preregistered 2025+2023 development selection.
"""
from __future__ import annotations

METHOD_ID = "orbittrace_highres_dual_channel_v5"
CALIBRATION_NEGATIVES_PER_BIN = 512
CALIBRATION_DENOMINATOR = 513
V3_MAX_RANK = 20
FIXED4_MAX_RANK = 10
V3_THRESHOLD = V3_MAX_RANK / CALIBRATION_DENOMINATOR
FIXED4_THRESHOLD = FIXED4_MAX_RANK / CALIBRATION_DENOMINATOR


def detected(p_v3: float, p_fixed4: float) -> bool:
    return float(p_v3) <= V3_THRESHOLD or float(p_fixed4) <= FIXED4_THRESHOLD


def self_test() -> dict[str, bool]:
    return {
        "frozen_calibration_count": CALIBRATION_NEGATIVES_PER_BIN == 512,
        "frozen_denominator": CALIBRATION_DENOMINATOR == 513,
        "frozen_v3_rank": V3_MAX_RANK == 20,
        "frozen_fixed4_rank": FIXED4_MAX_RANK == 10,
        "or_rule": (
            detected(20 / 513, 1.0)
            and detected(1.0, 10 / 513)
            and not detected(21 / 513, 11 / 513)
        ),
    }
