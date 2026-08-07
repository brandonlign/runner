"""Frozen OrbitTrace v4 reporting decision.

Continuous ranking is the frozen v3 multi-anchor wavelet energy. This module
contains only the independently calibrated two-channel reporting thresholds.
"""
from __future__ import annotations

METHOD_ID = "orbittrace_fpr_budgeted_dual_channel_v4"
CALIBRATION_DENOMINATOR = 129
V3_MAX_RANK = 3
FIXED4_MAX_RANK = 4
V3_THRESHOLD = V3_MAX_RANK / CALIBRATION_DENOMINATOR
FIXED4_THRESHOLD = FIXED4_MAX_RANK / CALIBRATION_DENOMINATOR


def detected(p_v3: float, p_fixed4: float) -> bool:
    return float(p_v3) <= V3_THRESHOLD or float(p_fixed4) <= FIXED4_THRESHOLD


def self_test() -> dict[str, bool]:
    return {
        "frozen_denominator": CALIBRATION_DENOMINATOR == 129,
        "frozen_v3_rank": V3_MAX_RANK == 3,
        "frozen_fixed4_rank": FIXED4_MAX_RANK == 4,
        "or_rule": (
            detected(3 / 129, 1.0)
            and detected(1.0, 4 / 129)
            and not detected(4 / 129, 5 / 129)
        ),
    }
