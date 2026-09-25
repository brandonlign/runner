"""Frozen OrbitTrace v5 corroborated sparse-rescue decision."""
from __future__ import annotations

import math

METHOD_ID = "orbittrace_corroborated_sparse_rescue_v5"
CALIBRATION_DENOMINATOR = 129
V3_PRIMARY_MAX_RANK = 4
FIXED4_SPARSE_MAX_RANK = 3
V3_CORROBORATION_MAX_RANK = 40

V3_PRIMARY_THRESHOLD = V3_PRIMARY_MAX_RANK / CALIBRATION_DENOMINATOR
FIXED4_SPARSE_THRESHOLD = FIXED4_SPARSE_MAX_RANK / CALIBRATION_DENOMINATOR
V3_CORROBORATION_THRESHOLD = V3_CORROBORATION_MAX_RANK / CALIBRATION_DENOMINATOR


def detected(p_v3: float, p_fixed4: float) -> bool:
    p_v3 = float(p_v3)
    p_fixed4 = float(p_fixed4)
    if not (math.isfinite(p_v3) and math.isfinite(p_fixed4)):
        raise ValueError("non-finite empirical p-value")
    if not (0.0 <= p_v3 <= 1.0 and 0.0 <= p_fixed4 <= 1.0):
        raise ValueError("empirical p-value outside [0,1]")
    return (
        p_v3 <= V3_PRIMARY_THRESHOLD
        or (
            p_fixed4 <= FIXED4_SPARSE_THRESHOLD
            and p_v3 <= V3_CORROBORATION_THRESHOLD
        )
    )


def self_test() -> dict[str, bool]:
    return {
        "primary_accepts": detected(4 / 129, 1.0),
        "primary_rejects_above": not detected(5 / 129, 1.0),
        "corroborated_rescue_accepts": detected(40 / 129, 3 / 129),
        "rescue_rejects_without_v3_corroboration": not detected(41 / 129, 3 / 129),
        "rescue_rejects_weak_fixed4": not detected(40 / 129, 4 / 129),
        "frozen_ranks": (
            CALIBRATION_DENOMINATOR == 129
            and V3_PRIMARY_MAX_RANK == 4
            and FIXED4_SPARSE_MAX_RANK == 3
            and V3_CORROBORATION_MAX_RANK == 40
        ),
    }
