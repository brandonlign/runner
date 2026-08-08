from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, order=True)
class ExactUnit:
    center: float
    start: int
    stop: int
    record_count: int
    window_event_count: int
    cost: int

    @property
    def key(self) -> str:
        return f"{self.center:.1f}:{self.start}:{self.stop}"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_units(pre: dict[str, Any], *, max_records_per_unit: int = 2048) -> list[ExactUnit]:
    """Split immutable pre-exact proposal lists into contiguous compute units.

    This is execution infrastructure only.  Units preserve each center's exact
    proposal order and use only pre-truth quantities already captured before
    exact rescoring: proposal count and window-event count.
    """
    limit = int(max_records_per_unit)
    _require(limit > 0, "max_records_per_unit must be positive")
    units: list[ExactUnit] = []
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        total = len(spec["records"])
        window_count = len(spec["window_event_ids"])
        _require(total > 0, f"empty proposal list for center {center}")
        _require(window_count > 0, f"empty event window for center {center}")
        start = 0
        while start < total:
            stop = min(total, start + limit)
            count = stop - start
            units.append(
                ExactUnit(
                    center=center,
                    start=start,
                    stop=stop,
                    record_count=count,
                    window_event_count=window_count,
                    cost=count * window_count,
                )
            )
            start = stop

    # Prove exact contiguous coverage before any scheduling occurs.
    by_center: dict[float, list[ExactUnit]] = {}
    for unit in units:
        by_center.setdefault(unit.center, []).append(unit)
    expected_centers = [float(value) for value in pre["ordered_centers"]]
    _require(sorted(by_center) == sorted(expected_centers), "unit center coverage changed")
    for center in expected_centers:
        values = sorted(by_center[center], key=lambda unit: unit.start)
        cursor = 0
        for unit in values:
            _require(unit.start == cursor, f"non-contiguous unit coverage center {center}")
            _require(unit.stop > unit.start, f"empty unit center {center}")
            cursor = unit.stop
        _require(cursor == len(pre["centers"][center]["records"]), f"incomplete unit coverage center {center}")
    return units


def balanced_unit_shards(
    pre: dict[str, Any],
    shard_count: int,
    *,
    max_records_per_unit: int = 2048,
) -> tuple[list[list[ExactUnit]], list[int]]:
    """Deterministic LPT scheduling using a pre-truth compute-cost proxy.

    The proxy is proposal_count * center_window_event_count.  It was selected
    solely from execution timing behavior; it contains no shower label, truth,
    score, benchmark result, or target information and never changes which
    scientific records are evaluated or their ordering during replay.
    """
    count = int(shard_count)
    _require(count > 0, "shard_count must be positive")
    units = build_units(pre, max_records_per_unit=max_records_per_unit)
    bins: list[list[ExactUnit]] = [[] for _ in range(count)]
    loads = [0 for _ in range(count)]
    for unit in sorted(units, key=lambda value: (-value.cost, value.center, value.start, value.stop)):
        target = min(range(count), key=lambda index: (loads[index], index))
        bins[target].append(unit)
        loads[target] += unit.cost
    for values in bins:
        values.sort(key=lambda unit: (unit.center, unit.start, unit.stop))

    assigned = sorted((unit.center, unit.start, unit.stop) for values in bins for unit in values)
    expected = sorted((unit.center, unit.start, unit.stop) for unit in units)
    _require(assigned == expected, "scheduled unit coverage changed")
    _require(len(assigned) == len(set(assigned)), "duplicate scheduled unit")
    return bins, loads
