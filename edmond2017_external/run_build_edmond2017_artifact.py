from __future__ import annotations

import bisect
from typing import Any

from edmond2017_external import build_edmond2017_artifact as builder

_CACHE: dict[int, tuple[list[float], list[float]]] = {}


def exact_cached_local_count(values: list[float], center: float) -> int:
    """Exact circular ±WINDOW count with cached sorted coordinates."""
    key = id(values)
    cached = _CACHE.get(key)
    if cached is None or cached[0] is not values:
        ordered = sorted(float(value) % 360.0 for value in values)
        extended = (
            [value - 360.0 for value in ordered]
            + ordered
            + [value + 360.0 for value in ordered]
        )
        cached = (values, extended)
        _CACHE[key] = cached
    extended = cached[1]
    return bisect.bisect_right(
        extended, center + builder.WINDOW
    ) - bisect.bisect_left(extended, center - builder.WINDOW)


def main() -> None:
    builder.local_count = exact_cached_local_count
    builder.main()


if __name__ == "__main__":
    main()
