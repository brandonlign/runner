from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import (
    FROZEN_V6_SHA256,
    event_rows_sha256,
    load_module,
    require,
    sha256_bytes,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--exact-shards-dir", required=True, type=Path)
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


def load_pickle_with_sidecar(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA sidecar {path.name}")
    digest = sha256_bytes(raw)
    require(digest == sidecar.read_text().strip().split()[0], f"SHA mismatch {path.name}")
    return pickle.loads(raw), digest


def reconstruct_exact_by_center(pre: dict[str, Any], pre_sha: str, shard_dir: Path, year: int) -> tuple[dict[float, list[dict[str, Any]]], int, dict[str, Any]]:
    shard_paths = sorted(shard_dir.glob(f"v6_task_{year}_shard_*.pkl"))
    require(bool(shard_paths), "no exact task shard files")
    shard_count: int | None = None
    seen_indices: set[int] = set()
    chunks: dict[float, list[tuple[int, int, list[dict[str, Any]]]]] = defaultdict(list)
    total_task_proposals = 0
    scheduler_summary: dict[str, Any] | None = None

    for path in shard_paths:
        shard, _ = load_pickle_with_sidecar(path)
        require(shard["format"] == "orbittrace-v6-exact-task-shard-v4", f"task shard format changed {path.name}")
        require(int(shard["year"]) == year, f"task shard year mismatch {path.name}")
        require(shard["preexact_sha256"] == pre_sha, f"task shard preexact mismatch {path.name}")
        require(shard["scan_rows_sha256"] == pre["scan_rows_sha256"], f"task shard scan mismatch {path.name}")
        require(shard["firewall"]["target_interval_remains_excluded"] is True, f"task shard firewall failed {path.name}")
        require(shard["firewall"]["labels_not_evaluated"] is True, f"task shard label firewall failed {path.name}")
        current_count = int(shard["shard_count"])
        shard_count = current_count if shard_count is None else shard_count
        require(current_count == shard_count, "mixed task shard counts")
        index = int(shard["shard_index"])
        require(index not in seen_indices, f"duplicate task shard index {index}")
        seen_indices.add(index)
        if scheduler_summary is None:
            scheduler_summary = {
                "all_shard_proposal_loads": list(shard["all_shard_proposal_loads"]),
                "all_shard_work_loads": list(shard["all_shard_work_loads"]),
                "ideal_work_proxy": int(shard["ideal_work_proxy"]),
                "work_proxy": str(shard["work_proxy"]),
            }
        else:
            require(list(shard["all_shard_proposal_loads"]) == scheduler_summary["all_shard_proposal_loads"], "task scheduler proposal loads disagree")
            require(list(shard["all_shard_work_loads"]) == scheduler_summary["all_shard_work_loads"], "task scheduler work loads disagree")
        require(len(shard["tasks"]) == len(shard["task_outputs"]), f"task/output count mismatch {path.name}")
        for task, rec in zip(shard["tasks"], shard["task_outputs"]):
            center = float(task["center"]); start = int(task["start"]); stop = int(task["stop"])
            require(float(rec["center"]) == center and int(rec["start"]) == start and int(rec["stop"]) == stop, "task metadata/output mismatch")
            spec = pre["centers"][center]
            original = spec["records"][start:stop]
            require(len(original) == int(task["proposals"]), f"task input count mismatch center {center}")
            require(rec["input_anchor_ids_sha256"] == canonical_sha([str(row["proposal_anchor_id"]) for row in original]), f"task input anchor hash mismatch center {center} {start}:{stop}")
            out = rec["outputs"]
            require([str(row["proposal_anchor_id"]) for row in out] == [str(row["proposal_anchor_id"]) for row in original], f"task output order mismatch center {center} {start}:{stop}")
            chunks[center].append((start, stop, out))
            total_task_proposals += len(out)

    require(shard_count is not None and scheduler_summary is not None, "missing task scheduler metadata")
    require(seen_indices == set(range(shard_count)), f"incomplete task shards: {sorted(seen_indices)} / {shard_count}")
    require(total_task_proposals == int(pre["total_records"]), "task output proposal accounting mismatch")

    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    ordered_centers = [float(c) for c in pre["ordered_centers"]]
    require(set(chunks) == set(ordered_centers), "task center coverage mismatch")
    for center in ordered_centers:
        spec = pre["centers"][center]
        n = len(spec["records"])
        parts = sorted(chunks[center], key=lambda x: (x[0], x[1]))
        cursor = 0
        merged: list[dict[str, Any]] = []
        for start, stop, out in parts:
            require(start == cursor and stop > start, f"task slice gap/overlap center {center}: cursor={cursor} slice={start}:{stop}")
            merged.extend(out)
            cursor = stop
        require(cursor == n, f"task slice incomplete center {center}: {cursor}/{n}")
        original_ids = [str(row["proposal_anchor_id"]) for row in spec["records"]]
        merged_ids = [str(row["proposal_anchor_id"]) for row in merged]
        require(merged_ids == original_ids, f"full reconstructed center order mismatch {center}")
        exact_by_center[center] = merged
    return exact_by_center, shard_count, scheduler_summary


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_pickle_with_sidecar(args.preexact_checkpoint)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format changed")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")

    exact_by_center, shard_count, scheduler_summary = reconstruct_exact_by_center(pre, pre_sha, args.exact_shards_dir, args.year)
    ordered_centers = [float(value) for value in pre["ordered_centers"]]

    repaired_sha = sha256_bytes(args.repaired_source.read_bytes())
    require(repaired_sha == pre["repaired_v6_sha256"], "repaired source mismatch")
    v6 = load_module(args.repaired_source, f"orbittrace_v6_task_replay_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed before replay")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed before replay")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present in replay scan")
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    require(source_sha == pre["year_sources_sha256"], "source identity changed before replay")

    original_exact = v6.exact_rescore_window_v6
    replayed: list[float] = []

    def replay_exact(old_arg, records, window_events, event_lookup, support_arg, base_arg):
        del old_arg, event_lookup, support_arg, base_arg
        require(bool(records), "unexpected empty replay exact call")
        center = float(records[0]["window_center"])
        require(center in pre["centers"], f"unexpected replay center {center}")
        require(center not in replayed, f"duplicate replay center {center}")
        spec = pre["centers"][center]
        require(canonical_sha(records) == spec["records_sha256"], f"proposal records changed before replay center {center}")
        ids = [str(row["id"]) for row in window_events]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window events changed before replay center {center}")
        outputs = exact_by_center[center]
        require([str(row["proposal_anchor_id"]) for row in outputs] == [str(row["proposal_anchor_id"]) for row in records], f"reconstructed exact output order mismatch center {center}")
        replayed.append(center)
        return outputs

    v6.exact_rescore_window_v6 = replay_exact
    try:
        audit, anchors, components = v6.scan_year_v6(old, args.year, scan, calibration, candidate, base, scorer, support)
    finally:
        v6.exact_rescore_window_v6 = original_exact

    require(replayed == ordered_centers, "task replay center order changed")
    require(int(audit["year"]) == args.year, "year audit mismatch")
    require(int(audit["proposal_cap_per_window"]) == 512, "proposal cap changed")
    require(int(audit["max_primary_proposals_per_year"]) == 36864, "annual proposal budget changed")

    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "calibration_rows_sha256": pre["calibration_rows_sha256"],
        "year_sources_sha256": pre["year_sources_sha256"],
        "execution": {
            "exact_fanout_taskbalanced_v4": True,
            "exact_shard_count": shard_count,
            "preexact_sha256": pre_sha,
            **scheduler_summary,
        },
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated_in_year_job": True,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_year_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    (args.output / f"v6_year_{args.year}.json").write_text(json.dumps({
        "year": args.year,
        "checkpoint_sha256": digest,
        "anchors": len(anchors),
        "components": len(components),
        "exact_shard_count": shard_count,
        "preexact_sha256": pre_sha,
        "scheduler": scheduler_summary,
    }, indent=2, sort_keys=True) + "\n")
    print(f"PASS_V6_TASK_FANOUT_YEAR_REPLAY year={args.year} anchors={len(anchors)} components={len(components)} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
