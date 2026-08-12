#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Callable


def make_exact_cached_pair_d(mod: Any) -> tuple[Callable[[dict[str, Any], dict[str, Any]], float], dict[str, int]]:
    """Return an exact frozen-form pair_d with per-event singleton unit reuse.

    The first time an event object is seen, its radiant vector is produced by the
    frozen `unit()` on the same singleton arrays used by frozen pair_d. Later
    calls reuse that exact vector and evaluate the identical dot/clip/acos/log/
    hypot expressions. Event objects are immutable during atomization.
    """
    frozen_unit = mod.unit
    unit_by_object: dict[int, Any] = {}
    stats = {"vector_hits": 0, "vector_misses": 0, "pair_calls": 0}

    def event_unit(e: dict[str, Any]):
        key = id(e)
        u = unit_by_object.get(key)
        if u is not None:
            stats["vector_hits"] += 1
            return u
        stats["vector_misses"] += 1
        u = frozen_unit(mod.np.asarray([e["lon"]]), mod.np.asarray([e["lat"]]))[0]
        unit_by_object[key] = u
        return u

    def pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
        stats["pair_calls"] += 1
        ua = event_unit(a)
        ub = event_unit(b)
        theta = mod.angle_deg(ua, ub) / 3.0
        speed = abs(mod.math.log(a["vg"] / b["vg"])) / mod.math.log(1.08)
        return float(mod.math.hypot(theta, speed))

    return pair_d, stats


def assert_pair_equivalence(mod: Any, events: list[dict[str, Any]], sample_count: int = 1024) -> None:
    """Fail closed unless deterministic sampled pair outputs are bit-identical."""
    if len(events) < 2:
        return
    frozen = mod.pair_d
    fast, _stats = make_exact_cached_pair_d(mod)
    n = len(events)
    count = min(sample_count, n - 1)
    for k in range(count):
        i = (k * 7919) % n
        j = (i + 1 + (k * 104729) % (n - 1)) % n
        if j == i:
            j = (j + 1) % n
        a = events[i]
        b = events[j]
        x = frozen(a, b)
        y = fast(a, b)
        if x != y:
            raise RuntimeError(f"exact-pair probe mismatch at sample {k}: {x!r} != {y!r}")
