from __future__ import annotations

import argparse
import json
import math
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_checkpointed_fallback.parallel_exact_rescore import install


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--shard-index", required=True, type=int)
    p.add_argument("--shard-count", required=True, type=int)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def load_preexact(path: Path, year: int) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), "missing preexact SHA sidecar")
    digest = sha256_bytes(raw)
    require(digest == sidecar.read_text().strip().split()[0], "preexact SHA mismatch")
    obj = pickle.loads(raw)
    require(obj["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format mismatch")
    require(int(obj["year"]) == year, "preexact year mismatch")
    require(obj["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(obj["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")
    return obj, digest


def build_tasks(pre: dict[str, Any], shard_count: int) -> tuple[list[dict[str, int | float]], int]:
    """Split only centers that exceed one ideal shard of scalar work.

    Exact proposal calls are independent. A task is a contiguous slice of one
    captured center's immutable proposal list. Slicing changes only where the
    original scalar function executes, never its inputs or floating operations.
    """
    require(shard_count > 0, "shard_count must be positive")
    total_work = sum(
        len(pre["centers"][float(center)]["records"])
        * len(pre["centers"][float(center)]["window_event_ids"])
        for center in pre["ordered_centers"]
    )
    require(total_work > 0, "empty preexact work")
    ideal = int(math.ceil(total_work / shard_count))
    tasks: list[dict[str, int | float]] = []
    for center_value in pre["ordered_centers"]:
        center = float(center_value)
        spec = pre["centers"][center]
        records = spec["records"]
        n = len(records)
        window_rows = len(spec["window_event_ids"])
        require(n > 0 and window_rows > 0, f"empty center work {center}")
        center_work = n * window_rows
        parts = max(1, min(n, int(math.ceil(center_work / ideal))))
        q, r = divmod(n, parts)
        start = 0
        for part in range(parts):
            stop = start + q + (1 if part < r else 0)
            require(stop > start, f"empty task center {center} part {part}")
            tasks.append({
                "center": center,
                "start": start,
                "stop": stop,
                "proposals": stop - start,
                "window_rows": window_rows,
                "work": (stop - start) * window_rows,
            })
            start = stop
        require(start == n, f"task partition incomplete center {center}")
    require(sum(int(t["proposals"]) for t in tasks) == int(pre["total_records"]), "task proposal accounting changed")
    return tasks, ideal


def schedule_tasks(pre: dict[str, Any], shard_count: int) -> tuple[list[list[dict[str, int | float]]], list[int], list[int], int]:
    tasks, ideal = build_tasks(pre, shard_count)
    bins: list[list[dict[str, int | float]]] = [[] for _ in range(shard_count)]
    work_loads = [0 for _ in range(shard_count)]
    proposal_loads = [0 for _ in range(shard_count)]
    for task in sorted(tasks, key=lambda t: (-int(t["work"]), float(t["center"]), int(t["start"]))):
        target = min(range(shard_count), key=lambda i: (work_loads[i], proposal_loads[i], i))
        bins[target].append(task)
        work_loads[target] += int(task["work"])
        proposal_loads[target] += int(task["proposals"])
    for values in bins:
        values.sort(key=lambda t: (float(t["center"]), int(t["start"])))
    flat = [t for values in bins for t in values]
    require(len(flat) == len(tasks), "task count changed during scheduling")
    identities = {(float(t["center"]), int(t["start"]), int(t["stop"])) for t in flat}
    require(len(identities) == len(tasks), "duplicate scheduled task identity")
    return bins, work_loads, proposal_loads, ideal


def main() -> int:
    args = parse_args()
    require(0 <= args.shard_index < args.shard_count, "invalid shard index")
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_preexact(args.preexact_checkpoint, args.year)

    v6 = load_module(args.repaired_source, f"orbittrace_v6_task_shard_{args.year}_{args.shard_index}")
    require(sha256_bytes(args.repaired_source.read_bytes()) == pre["repaired_v6_sha256"], "repaired source mismatch")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, _sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present in scan")
    event_lookup = {str(row["id"]): row for row in scan}

    config = install(v6, workers=args.workers, min_parallel_records=256)
    shard_tasks, work_loads, proposal_loads, ideal = schedule_tasks(pre, args.shard_count)
    selected = shard_tasks[args.shard_index]
    require(bool(selected), "empty task shard")
    outputs: list[dict[str, Any]] = []
    print(
        f"V6_TASK_FANOUT_BALANCE year={args.year} ideal={ideal} work_loads={work_loads} "
        f"proposal_loads={proposal_loads}", flush=True,
    )

    for task in selected:
        center = float(task["center"])
        start = int(task["start"]); stop = int(task["stop"])
        spec = pre["centers"][center]
        full_records = spec["records"]
        require(canonical_sha(full_records) == spec["records_sha256"], f"captured record hash mismatch center {center}")
        records = full_records[start:stop]
        require(len(records) == int(task["proposals"]), f"task slice count changed center {center}")
        ids = [str(value) for value in spec["window_event_ids"]]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"captured window hash mismatch center {center}")
        require(all(event_id in event_lookup for event_id in ids), f"captured window event absent center {center}")
        window_events = [event_lookup[event_id] for event_id in ids]
        canonical_window = old.window_events_for_center(scan, center, base)
        require([str(row["id"]) for row in canonical_window] == ids, f"window reconstruction changed center {center}")
        chunk = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
        require([str(row["proposal_anchor_id"]) for row in chunk] == [str(row["proposal_anchor_id"]) for row in records], f"exact task output order changed center {center} {start}:{stop}")
        outputs.append({
            "center": center,
            "start": start,
            "stop": stop,
            "input_anchor_ids_sha256": canonical_sha([str(row["proposal_anchor_id"]) for row in records]),
            "outputs": chunk,
        })
        print(
            f"V6_TASK_EXACT_DONE year={args.year} shard={args.shard_index}/{args.shard_count} "
            f"center={center:.1f} slice={start}:{stop} proposals={len(records):,} window_rows={len(ids):,}",
            flush=True,
        )

    payload = {
        "format": "orbittrace-v6-exact-task-shard-v4",
        "year": args.year,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "preexact_sha256": pre_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "tasks": [{k: v for k, v in t.items()} for t in selected],
        "task_outputs": outputs,
        "scheduled_proposals": proposal_loads[args.shard_index],
        "scheduled_work_proxy": work_loads[args.shard_index],
        "all_shard_proposal_loads": proposal_loads,
        "all_shard_work_loads": work_loads,
        "ideal_work_proxy": ideal,
        "work_proxy": "proposal_count_times_window_event_count_with_oversized_center_slicing",
        "executor": config,
        "firewall": {"target_interval_remains_excluded": True, "labels_not_evaluated": True},
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_task_{args.year}_shard_{args.shard_index:02d}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    print(
        f"PASS_V6_TASK_FANOUT_SHARD year={args.year} shard={args.shard_index}/{args.shard_count} "
        f"tasks={len(selected)} proposals={proposal_loads[args.shard_index]:,} work={work_loads[args.shard_index]:,} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
