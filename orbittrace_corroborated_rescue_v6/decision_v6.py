"""Frozen OrbitTrace v6 corroborated sparse-rescue reporting rule."""
from __future__ import annotations

METHOD_ID = "orbittrace_corroborated_rescue_v6"
CALIBRATION_NEGATIVES_PER_BIN = 512
CALIBRATION_DENOMINATOR = 513
PRIMARY_V3_MAX_RANK = 17
FIXED4_MAX_RANK = 15
CORROBORATION_V3_MAX_RANK = 122
PRIMARY_V3_THRESHOLD = PRIMARY_V3_MAX_RANK / CALIBRATION_DENOMINATOR
FIXED4_THRESHOLD = FIXED4_MAX_RANK / CALIBRATION_DENOMINATOR
CORROBORATION_V3_THRESHOLD = CORROBORATION_V3_MAX_RANK / CALIBRATION_DENOMINATOR


def detected(p_v3: float, p_fixed4: float) -> bool:
    p_v3 = float(p_v3)
    p_fixed4 = float(p_fixed4)
    return (
        p_v3 <= PRIMARY_V3_THRESHOLD
        or (p_fixed4 <= FIXED4_THRESHOLD and p_v3 <= CORROBORATION_V3_THRESHOLD)
    )


def self_test() -> dict[str, bool]:
    return {
        "frozen_calibration_count": CALIBRATION_NEGATIVES_PER_BIN == 512,
        "frozen_denominator": CALIBRATION_DENOMINATOR == 513,
        "frozen_primary_rank": PRIMARY_V3_MAX_RANK == 17,
        "frozen_fixed4_rank": FIXED4_MAX_RANK == 15,
        "frozen_corroboration_rank": CORROBORATION_V3_MAX_RANK == 122,
        "primary_boundary": detected(17 / 513, 1.0) and not detected(18 / 513, 1.0),
        "corroborated_rescue_boundary": (
            detected(122 / 513, 15 / 513)
            and not detected(123 / 513, 15 / 513)
            and not detected(122 / 513, 16 / 513)
        ),
    }
