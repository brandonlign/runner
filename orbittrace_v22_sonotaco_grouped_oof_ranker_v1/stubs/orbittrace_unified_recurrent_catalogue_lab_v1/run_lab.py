"""Transport-only stub for importing the exact frozen #839 ranker during v22 training.

Only constants read at import time by the historical v2 module plus the exact deterministic
fold helper are exposed here. No candidate, feature, target, model, ranking, or evaluation
science is implemented by this stub.
"""
from __future__ import annotations

import hashlib

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED_HARD = 226
EXPECTED_SOFT = 1075
EXPECTED_COMBINED = 1301
EXPECTED_P19_RESULT_SHA256 = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA256 = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
FEATURE_NAMES = (
    "is_soft",
    "log_event_count",
    "log_anchor_count",
    "log_quartet_count",
    "log_component_count",
    "best_score",
    "year_strength_min",
    "year_strength_max",
    "year_strength_balance",
    "member_year_balance",
    "centroid_crossyear_distance",
    "hard_rank_percentile",
    "soft_support_fraction",
    "soft_trigger_distance",
)


def deterministic_fold(group: str, folds: int = 5) -> int:
    return int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % folds
