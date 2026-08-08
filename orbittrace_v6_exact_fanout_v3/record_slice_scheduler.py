from __future__ import annotations

import math
from typing import Any


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_record_slices(pre: dict[str, Any], shard_count: int) -> tuple[list[list[dict[str, Any]]], list[int]]:
    """Partition exact-rescore records into deterministic contiguous slices.

    Cost proxy is exactly `record_count * window_event_count`, the dominant
    label-free geometry work in exact_rescore_window_v6. A center is split only
    when its estimated work exceeds one ideal shard's share. This changes only
    execution partitioning: each slice is a contiguous subsequence of the exact
    captured proposal list for one immutable center.
    """
    require(shard_count > 0, "shard_count must be positive")
    centers = [float(c) for c in pre["ordered_centers"]]
    require(bool(centers), "no preexact centers")

    center_specs: list[tuple[float, int, int, int]] = []
    total_cost = 0
    for center in centers:
        spec = pre["centers"][center]
        record_count = len(spec["records"])
        event_count = len(spec["window_event_ids"])
        require(record_count > 0 and event_count > 0, f"empty center {center}")
        cost = record_count * event_count
        center_specs.append((center, record_count, event_count, cost))
        total_cost += cost
    require(total_cost > 0, "zero estimated work")

    ideal_cost = total_cost / shard_count
    slices: list[dict[str, Any]] = []
    for center, record_count, event_count, center_cost in center_specs:
        slice_count = max(1, int(math.ceil(center_cost / ideal_cost)))
        slice_count = min(slice_count, record_count)
        q, r = divmod(record_count, slice_count)
        start = 0
        for slice_index in range(slice_count):
            count = q + (1 if slice_index < r else 0)
            stop = start + count
            require(stop > start, "empty record slice")
            slices.append({
                "center": center,
                "slice_index": slice_index,
                "slice_count": slice_count,
                "record_start": start,
                "record_stop": stop,
                "record_count": count,
                "window_event_count": event_count,
                "estimated_cost": count * event_count,
            })
            start = stop
        require(start == record_count, f"slice coverage changed center {center}")

    # Longest-processing-time scheduling using the more faithful exact-geometry
    # cost proxy. Tie breaks are deterministic and independent of science.
    bins: list[list[dict[str, Any]]] = [[] for _ in range(shard_count)]
    loads = [0 for _ in range(shard_count)]
    ordered = sorted(
        slices,
        key=lambda s: (-int(s["estimated_cost"]), float(s["center"]), int(s["record_start"])),
    )
    for record_slice in ordered:
        target = min(range(shard_count), key=lambda index: (loads[index], index))
        bins[target].append(record_slice)
        loads[target] += int(record_slice["estimated_cost"])

    for values in bins:
        values.sort(key=lambda s: (float(s["center"]), int(s["record_start"])))

    # Prove every proposal index of every center appears exactly once.
    rebuilt: dict[float, list[tuple[int, int]]] = {center: [] for center in centers}
    for values in bins:
        for record_slice in values:
            rebuilt[float(record_slice["center"])].append(
                (int(record_slice["record_start"]), int(record_slice["record_stop"]))
            )
    for center, record_count, _event_count, _cost in center_specs:
        ranges = sorted(rebuilt[center])
        cursor = 0
        for start, stop in ranges:
            require(start == cursor and stop > start, f"record-slice gap/overlap center {center}")
            cursor = stop
        require(cursor == record_count, f"record-slice incomplete center {center}")

    require(sum(loads) == total_cost, "scheduled cost changed")
    return bins, loads
