from __future__ import annotations

import hashlib
import json
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import require

CHUNK_SIZE = 512
GLOBAL_SHARD_COUNT = 16


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def build_tasks(preparations: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    require(set(preparations) == {2022, 2023}, "global planner requires exact 2022/2023 preparations")
    tasks: list[dict[str, Any]] = []
    for year in (2022, 2023):
        prep = preparations[year]
        records_by_center = prep["records_by_center"]
        event_count_by_center = prep["window_event_count_by_center"]
        require(set(records_by_center) == set(event_count_by_center), f"window count coverage changed {year}")
        for center in sorted(records_by_center, key=float):
            count = len(records_by_center[center])
            require(count > 0, f"empty exact center {year} {center}")
            event_count = int(event_count_by_center[center])
            require(event_count > 0, f"empty exact window {year} {center}")
            for start in range(0, count, CHUNK_SIZE):
                stop = min(start + CHUNK_SIZE, count)
                tasks.append({
                    "year": year,
                    "center": str(center),
                    "start": start,
                    "stop": stop,
                    "proposal_count": stop - start,
                    "window_event_count": event_count,
                    "estimated_work": (stop - start) * event_count,
                })
    require(tasks, "no global exact tasks")
    return tasks


def assign_global_shards(tasks: list[dict[str, Any]], shard_count: int = GLOBAL_SHARD_COUNT) -> list[list[dict[str, Any]]]:
    require(shard_count > 0, "invalid global shard count")
    assignments: list[list[dict[str, Any]]] = [[] for _ in range(shard_count)]
    loads = [0 for _ in range(shard_count)]
    ranked = sorted(
        tasks,
        key=lambda task: (
            -int(task["estimated_work"]),
            int(task["year"]),
            float(task["center"]),
            int(task["start"]),
        ),
    )
    for task in ranked:
        shard = min(range(shard_count), key=lambda index: (loads[index], index))
        assignments[shard].append(dict(task))
        loads[shard] += int(task["estimated_work"])
    for rows in assignments:
        rows.sort(key=lambda task: (int(task["year"]), float(task["center"]), int(task["start"])))
    expected = sorted(
        [(int(t["year"]), str(t["center"]), int(t["start"]), int(t["stop"])) for t in tasks]
    )
    observed = sorted(
        [(int(t["year"]), str(t["center"]), int(t["start"]), int(t["stop"])) for rows in assignments for t in rows]
    )
    require(observed == expected, "global shard task coverage mismatch")
    require(len(observed) == len(set(observed)), "duplicate global shard task")
    return assignments


def build_plan(preparations: dict[int, dict[str, Any]], shard_count: int = GLOBAL_SHARD_COUNT) -> dict[str, Any]:
    tasks = build_tasks(preparations)
    assignments = assign_global_shards(tasks, shard_count)
    payload = {
        "format": "orbittrace-v6-global-exact-chunk-plan-v1",
        "chunk_size": CHUNK_SIZE,
        "shard_count": shard_count,
        "task_count": len(tasks),
        "proposal_count": sum(int(task["proposal_count"]) for task in tasks),
        "shards": [
            {
                "shard": index,
                "task_count": len(rows),
                "proposal_count": sum(int(task["proposal_count"]) for task in rows),
                "estimated_work": sum(int(task["estimated_work"]) for task in rows),
                "tasks": rows,
            }
            for index, rows in enumerate(assignments)
        ],
    }
    payload["plan_sha256"] = canonical_sha256({key: value for key, value in payload.items() if key != "plan_sha256"})
    return payload


def validate_center_chunks(tasks: list[dict[str, Any]], record_count: int, year: int, center: str) -> None:
    relevant = sorted(
        [task for task in tasks if int(task["year"]) == year and str(task["center"]) == str(center)],
        key=lambda task: int(task["start"]),
    )
    require(relevant, f"missing center chunks {year} {center}")
    cursor = 0
    for task in relevant:
        require(int(task["start"]) == cursor, f"center chunk gap/overlap {year} {center}")
        require(0 < int(task["stop"]) - int(task["start"]) <= CHUNK_SIZE, f"center chunk size changed {year} {center}")
        cursor = int(task["stop"])
    require(cursor == record_count, f"center chunk coverage incomplete {year} {center}")
