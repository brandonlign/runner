from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import require, sha256_bytes
from orbittrace_v6_exact_sharded_acceleration.common import (
    REPAIRED_V6_SHA256,
    SHARD_COUNT,
    load_sidecar_pickle,
    proposal_anchor_ids,
)
from orbittrace_v6_global_chunk_acceleration.common import (
    GLOBAL_SHARD_COUNT,
    build_plan,
    validate_center_chunks,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--catalogue-cache", required=True, type=Path)
    p.add_argument("--prepare-2022", required=True, type=Path)
    p.add_argument("--prepare-2023", required=True, type=Path)
    p.add_argument("--global-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cache, cache_sha = load_sidecar_pickle(args.catalogue_cache)
    prep22, prep22_sha = load_sidecar_pickle(args.prepare_2022)
    prep23, prep23_sha = load_sidecar_pickle(args.prepare_2023)
    preparations = {2022: prep22, 2023: prep23}
    prep_shas = {"2022": prep22_sha, "2023": prep23_sha}
    plan = build_plan(preparations)

    observed_task_keys: set[tuple[int, str, int, int]] = set()
    task_rows: list[dict[str, Any]] = []
    global_digests: dict[str, str] = {}
    for shard in range(GLOBAL_SHARD_COUNT):
        path = args.global_dir / f"global_exact_shard_{shard}.pkl"
        payload, digest = load_sidecar_pickle(path)
        require(payload["format"] == "orbittrace-v6-global-exact-chunk-result-v1", "global exact format changed")
        require(payload["shard"] == shard and payload["shard_count"] == GLOBAL_SHARD_COUNT, "global shard identity changed")
        require(payload["plan_sha256"] == plan["plan_sha256"], "global shard plan binding changed")
        require(payload["catalogue_cache_sha256"] == cache_sha, "global shard cache binding changed")
        require(payload["prepare_sha256"] == prep_shas, "global shard prepare binding changed")
        require(payload["repaired_v6_sha256"] == REPAIRED_V6_SHA256, "global shard source binding changed")
        require(payload["firewall"]["original_exact_rescore_function_used_unchanged"] is True, "global shard exact-function firewall failed")
        require(payload["firewall"]["contiguous_record_chunks_only"] is True, "global shard chunk firewall failed")
        for task in payload["tasks"]:
            key = (int(task["year"]), str(task["center"]), int(task["start"]), int(task["stop"]))
            require(key not in observed_task_keys, f"duplicate global task {key}")
            observed_task_keys.add(key)
            task_rows.append(task)
        global_digests[str(shard)] = digest

    expected_task_keys = {
        (int(task["year"]), str(task["center"]), int(task["start"]), int(task["stop"]))
        for shard in plan["shards"] for task in shard["tasks"]
    }
    require(observed_task_keys == expected_task_keys, "global chunk task coverage mismatch")

    prep = preparations[args.year]
    exact_by_center: dict[str, list[dict[str, Any]]] = {}
    for center in sorted(prep["records_by_center"], key=float):
        original = prep["records_by_center"][center]
        validate_center_chunks(
            [task for shard in plan["shards"] for task in shard["tasks"]],
            len(original),
            args.year,
            center,
        )
        chunks = sorted(
            [task for task in task_rows if int(task["year"]) == args.year and str(task["center"]) == center],
            key=lambda task: int(task["start"]),
        )
        cursor = 0
        combined: list[dict[str, Any]] = []
        for task in chunks:
            require(int(task["start"]) == cursor, f"observed chunk gap/overlap {args.year} {center}")
            require(len(task["exact_rows"]) == int(task["stop"]) - int(task["start"]), f"observed chunk output size changed {args.year} {center}")
            require(
                proposal_anchor_ids(task["exact_rows"]) == proposal_anchor_ids(original)[int(task["start"]):int(task["stop"])],
                f"observed chunk output order changed {args.year} {center}",
            )
            combined.extend(task["exact_rows"])
            cursor = int(task["stop"])
        require(cursor == len(original), f"observed center coverage incomplete {args.year} {center}")
        require(proposal_anchor_ids(combined) == proposal_anchor_ids(original), f"assembled center order changed {args.year} {center}")
        exact_by_center[center] = combined

    # Repackage into the already-source-audited eight center-shard format so the
    # existing replay_year.py remains unchanged. This is an implementation bridge,
    # not a scientific transformation.
    require(len(prep["shard_plan"]) == SHARD_COUNT, "center-shard replay plan changed")
    for center_shard in range(SHARD_COUNT):
        centers = [str(center) for center in prep["shard_plan"][center_shard]["centers"]]
        payload = {
            "format": "orbittrace-v6-exact-shard-result-v1",
            "year": args.year,
            "shard": center_shard,
            "shard_count": SHARD_COUNT,
            "centers": centers,
            "proposal_count": sum(len(prep["records_by_center"][center]) for center in centers),
            "exact_by_center": {center: exact_by_center[center] for center in centers},
            "prepare_sha256": prep_shas[str(args.year)],
            "catalogue_cache_sha256": cache_sha,
            "repaired_v6_sha256": REPAIRED_V6_SHA256,
            "firewall": {
                "target_interval_remains_excluded": True,
                "hidden_labels_not_loaded": True,
                "original_exact_rescore_function_used_unchanged": True,
                "assembled_from_verified_contiguous_chunks": True,
            },
            "global_chunk_provenance": {
                "plan_sha256": plan["plan_sha256"],
                "global_shard_sha256": global_digests,
            },
        }
        raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
        path = args.output / f"exact_year_{args.year}_shard_{center_shard}.pkl"
        path.write_bytes(raw)
        digest = sha256_bytes(raw)
        (args.output / f"exact_year_{args.year}_shard_{center_shard}.sha256").write_text(digest + "\n")
        (args.output / f"exact_year_{args.year}_shard_{center_shard}.json").write_text(
            json.dumps({
                "year": args.year,
                "shard": center_shard,
                "centers": centers,
                "proposal_count": payload["proposal_count"],
                "checkpoint_sha256": digest,
                "global_chunk_provenance": payload["global_chunk_provenance"],
            }, indent=2, sort_keys=True) + "\n"
        )
    print(
        f"PASS_V6_GLOBAL_CHUNKS_ASSEMBLED year={args.year} centers={len(exact_by_center)} "
        f"proposals={sum(len(rows) for rows in exact_by_center.values())} plan={plan['plan_sha256']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
