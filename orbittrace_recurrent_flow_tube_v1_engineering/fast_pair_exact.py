#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np


def build_exact_fast_pair_d(mod: Any, rows: list[dict[str, Any]]) -> Callable[[dict[str, Any], dict[str, Any]], float]:
    """Return a bit-preserving implementation of frozen ordered RFT pair_d.

    Every cached unit vector is computed once with the exact frozen singleton
    unit() call. No reverse-pair symmetry or altered arithmetic is used.
    """
    unit_by_id: dict[int, np.ndarray] = {}
    for row in rows:
        key = id(row)
        if key in unit_by_id:
            raise RuntimeError('duplicate Python object identity in RFT pair cache input')
        unit_by_id[key] = mod.unit(
            np.asarray([row['lon']]),
            np.asarray([row['lat']]),
        )[0]

    def fast_pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
        try:
            ua = unit_by_id[id(a)]
            ub = unit_by_id[id(b)]
        except KeyError as exc:
            raise RuntimeError('RFT fast pair received event outside frozen cache rows') from exc
        dot = float(np.dot(ua, ub))
        if dot < -1.0:
            dot = -1.0
        elif dot > 1.0:
            dot = 1.0
        theta = math.degrees(math.acos(dot)) / 3.0
        speed = abs(math.log(a['vg'] / b['vg'])) / math.log(1.08)
        return float(math.hypot(theta, speed))

    return fast_pair_d
