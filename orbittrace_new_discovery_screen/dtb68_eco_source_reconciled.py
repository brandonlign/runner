#!/usr/bin/env python3
"""Primary-source ECO representation for the frozen DTb68 continuity audit.

Only the ECO radiant reference solar longitude is changed, from the current
MDC row's 294.1 deg to the 307.1-deg peak explicitly printed in Jenniskens
(2006), Table 7. All empirical-test settings remain frozen and unchanged.
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
target.ECO_REF_SOL = 307.1


if __name__ == "__main__":
    raise SystemExit(target.main())
