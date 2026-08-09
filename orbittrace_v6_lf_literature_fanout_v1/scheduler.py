from __future__ import annotations

import math
from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def build_slices(pre: dict[str, Any], shard_count: int) -> tuple[list[list[dict[str, Any]]], list[int]]:
    require(shard_count > 0, "shard_count must be positive")
    specs = []
    total_cost = 0
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        nr = len(spec["records"])
        ne = len(spec["window_event_ids"])
        require(nr > 0 and ne > 0, f"empty center {center}")
        cost = nr * ne
        specs.append((center, nr, ne, cost))
        total_cost += cost
    require(total_cost > 0, "zero estimated cost")
    ideal = total_cost / shard_count

    pieces = []
    for center, nr, ne, cost in specs:
        count = max(1, min(nr, int(math.ceil(cost / ideal))))
        q, r = divmod(nr, count)
        start = 0
        for index in range(count):
            n = q + (1 if index < r else 0)
            stop = start + n
            require(stop > start, "empty record slice")
            pieces.append({
                "center": center,
                "slice_index": index,
                "slice_count": count,
                "record_start": start,
                "record_stop": stop,
                "record_count": n,
                "window_event_count": ne,
                "estimated_cost": n * ne,
            })
            start = stop
        require(start == nr, f"slice coverage changed center {center}")

    bins = [[] for _ in range(shard_count)]
    loads = [0] * shard_count
    for piece in sorted(pieces, key=lambda value: (-int(value["estimated_cost"]), float(value["center"]), int(value["record_start"]))):
        target = min(range(shard_count), key=lambda idx: (loads[idx], idx))
        bins[target].append(piece)
        loads[target] += int(piece["estimated_cost"])
    for values in bins:
        values.sort(key=lambda value: (float(value["center"]), int(value["record_start"])))

    for center, nr, _ne, _cost in specs:
        ranges = sorted((int(piece["record_start"]), int(piece["record_stop"])) for values in bins for piece in values if float(piece["center"]) == center)
        cursor = 0
        for start, stop in ranges:
            require(start == cursor and stop > start, f"slice gap/overlap center {center}")
            cursor = stop
        require(cursor == nr, f"incomplete slice coverage center {center}")
    require(sum(loads) == total_cost, "scheduled cost changed")
    return bins, loads
