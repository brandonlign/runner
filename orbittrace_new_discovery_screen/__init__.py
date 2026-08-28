"""Compute-only mirrors for OrbitTrace raw discovery experiments.

The GMN Python API version used by the frozen discovery runners hard-codes a
fractional-second datetime format.  Older GMN monthly files contain a mixture
of timestamps with and without fractional seconds, and pandas 2.2 rejects the
mixed column under that exact format.  Install a narrow compatibility fallback
for that one parser call.  No trajectory values, candidate rules, thresholds,
or scientific calculations are changed.
"""
from __future__ import annotations

import pandas as pd

_ORIGINAL_TO_DATETIME = pd.to_datetime
_GMN_EXACT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def _gmn_compatible_to_datetime(arg, *args, **kwargs):
    try:
        return _ORIGINAL_TO_DATETIME(arg, *args, **kwargs)
    except ValueError:
        if kwargs.get("format") != _GMN_EXACT_TIMESTAMP_FORMAT:
            raise
        retry = dict(kwargs)
        retry["format"] = "mixed"
        return _ORIGINAL_TO_DATETIME(arg, *args, **retry)


pd.to_datetime = _gmn_compatible_to_datetime
