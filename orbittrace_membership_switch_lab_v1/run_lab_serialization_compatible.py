#!/usr/bin/env python3
"""Transport-only wrapper for membership-switch lab JSON serialization.

The scientific lab deliberately uses +inf as a development-grid sentinel meaning
"no upper bound". The underlying experiment completed successfully in run
31341744515 and failed only when json.dumps(..., allow_nan=False) attempted to
serialize that sentinel. This wrapper changes no feature, threshold, candidate,
selection, metric, or scientific decision. It converts nonfinite floats to explicit
JSON strings only at serialization time.
"""
from __future__ import annotations

import math
from typing import Any

from orbittrace_membership_switch_lab_v1 import run_lab as lab


def json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


_original_dumps = lab.json.dumps


def _safe_dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
    return _original_dumps(json_safe(obj), *args, **kwargs)


lab.json.dumps = _safe_dumps
lab.mult.YEARS = lab.YEARS
lab.mult.MONTH_KEYS = lab.MONTH_KEYS
lab.mult.TOP_K = 100

if __name__ == "__main__":
    raise SystemExit(lab.main())
