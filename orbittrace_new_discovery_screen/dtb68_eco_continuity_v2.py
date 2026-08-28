#!/usr/bin/env python3
"""Implementation-only repair for the frozen DTb68/ECO continuity audit.

The frozen model, bins, and thresholds are unchanged. The original runner used
a scalar helper that does not exist in the shared module. This wrapper supplies
that serialization helper and then executes the frozen audit unchanged.
"""
from __future__ import annotations

import math
from typing import Any

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import dtb68_eco_continuity as target


def finite_scalar(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


base.finite = finite_scalar


if __name__ == "__main__":
    raise SystemExit(target.main())
