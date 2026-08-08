from __future__ import annotations

from orbittrace_v6_label_free_all_event_null import run_development as lf

HOLDOUT_YEARS=(2024,2025)
HOLDOUT_MONTH_KEYS=tuple(f"{year}-{month:02d}" for year in HOLDOUT_YEARS for month in range(1,13))
HOLDOUT_CORPUS="orbittrace-v6-lf-gmn-2024-2025-temporal-holdout"


def activate()->None:
    # Year/corpus transport only. Scientific detector/calibration constants remain in the frozen v6-LF module.
    lf.YEARS=HOLDOUT_YEARS
    lf.MONTH_KEYS=HOLDOUT_MONTH_KEYS


def configure_runtime(v6,old,support)->None:
    activate()
    old.YEARS=HOLDOUT_YEARS
    old.MONTH_KEYS=HOLDOUT_MONTH_KEYS
    old.CORPUS=HOLDOUT_CORPUS
    support.YEARS=HOLDOUT_YEARS
    support.MONTH_KEYS=HOLDOUT_MONTH_KEYS
    support.CORPUS=HOLDOUT_CORPUS
    # The repaired v6 source consumes old.CORPUS when deriving stable null seeds.
    v6.CORPUS=HOLDOUT_CORPUS
