#!/usr/bin/env python3
"""Technical wrapper: reproduce exact 2022/2023 state and make non-finite diagnostic sentinels JSON-safe."""
from __future__ import annotations

import math
from typing import Any

from orbittrace_membership_switch_lab_v1 import run_lab as lab

lab.mult.YEARS = lab.YEARS
lab.mult.MONTH_KEYS = lab.MONTH_KEYS
lab.mult.TOP_K = 100

# The scientific lab deliberately uses +/-inf as grid sentinels for "no bound".
# The completed calculation previously died only when json.dumps(..., allow_nan=False)
# tried to serialize those sentinels. Preserve every ordinary serialization byte-for-byte;
# only on that exact non-finite serialization failure, encode the sentinel as an explicit
# string. No threshold, candidate, metric, selection rule, or scientific calculation changes.
_original_json_dumps = lab.json.dumps


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    return value


def _diagnostic_safe_dumps(value: Any, *args: Any, **kwargs: Any) -> str:
    try:
        return _original_json_dumps(value, *args, **kwargs)
    except ValueError as exc:
        if "Out of range float values are not JSON compliant" not in str(exc):
            raise
        return _original_json_dumps(_json_safe(value), *args, **kwargs)


lab.json.dumps = _diagnostic_safe_dumps

if __name__ == "__main__":
    raise SystemExit(lab.main())
