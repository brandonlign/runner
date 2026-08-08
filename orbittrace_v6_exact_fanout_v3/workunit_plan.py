from __future__ import annotations

from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def build_work_units(pre: dict[str, Any], max_records_per_unit: int) -> list[dict[str, int | float]]:
    """Split each exact center into contiguous proposal-record work units.

    This is scheduling only. Unit boundaries never enter the scientific function;
    each unit is passed to the original exact_rescore_window_v6 and later
    concatenated in the original record order.
    """
    require(max_records_per_unit > 0, "max_records_per_unit must be positive")
    units: list[dict[str, int | float]] = []
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        n_records = len(spec["records"])
        n_window = len(spec["window_event_ids"])
        require(n_records > 0, f"empty exact record set center {center}")
        require(n_window > 0, f"empty exact event window center {center}")
        for start in range(0, n_records, max_records_per_unit):
            stop = min(n_records, start + max_records_per_unit)
            units.append({
                "center": center,
                "start": start,
                "stop": stop,
                "records": stop - start,
                # Exact rescoring compares proposal records against the center's
                # fixed event window. This label-free product is a better compute
                # proxy than proposal count alone and remains scientifically inert.
                "cost": (stop - start) * n_window,
            })
    validate_work_units(pre, units)
    return units


def validate_work_units(pre: dict[str, Any], units: list[dict[str, int | float]]) -> None:
    by_center: dict[float, list[tuple[int, int]]] = {}
    for unit in units:
        center = float(unit["center"])
        start = int(unit["start"])
        stop = int(unit["stop"])
        require(center in pre["centers"], f"unexpected center {center}")
        require(0 <= start < stop <= len(pre["centers"][center]["records"]), f"invalid unit bounds {unit}")
        by_center.setdefault(center, []).append((start, stop))
    expected_centers = [float(value) for value in pre["ordered_centers"]]
    require(set(by_center) == set(expected_centers), "work-unit center coverage changed")
    for center in expected_centers:
        spans = sorted(by_center[center])
        cursor = 0
        for start, stop in spans:
            require(start == cursor, f"work-unit gap/overlap center {center}: expected {cursor}, got {start}")
            cursor = stop
        require(cursor == len(pre["centers"][center]["records"]), f"incomplete work-unit coverage center {center}")


def balanced_unit_shards(
    pre: dict[str, Any],
    shard_count: int,
    max_records_per_unit: int,
) -> tuple[list[list[dict[str, int | float]]], list[int]]:
    require(shard_count > 0, "shard_count must be positive")
    units = build_work_units(pre, max_records_per_unit)
    require(len(units) >= shard_count, "more shards than work units")
    bins: list[list[dict[str, int | float]]] = [[] for _ in range(shard_count)]
    loads = [0 for _ in range(shard_count)]
    for unit in sorted(
        units,
        key=lambda u: (-int(u["cost"]), float(u["center"]), int(u["start"])),
    ):
        target = min(range(shard_count), key=lambda index: (loads[index], index))
        bins[target].append(dict(unit))
        loads[target] += int(unit["cost"])
    require(all(bins), "empty work-unit shard")
    flattened = [
        (float(u["center"]), int(u["start"]), int(u["stop"]))
        for values in bins for u in values
    ]
    expected = [
        (float(u["center"]), int(u["start"]), int(u["stop"]))
        for u in units
    ]
    require(sorted(flattened) == sorted(expected), "balanced work-unit coverage changed")
    return bins, loads
