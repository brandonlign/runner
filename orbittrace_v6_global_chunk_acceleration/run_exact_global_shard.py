from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_exact_sharded_acceleration.common import REPAIRED_V6_SHA256, load_sidecar_pickle, proposal_anchor_ids
from orbittrace_v6_global_chunk_acceleration.common import GLOBAL_SHARD_COUNT, build_plan


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--shard", required=True, type=int, choices=tuple(range(GLOBAL_SHARD_COUNT)))
    p.add_argument("--catalogue-cache", required=True, type=Path)
    p.add_argument("--prepare-2022", required=True, type=Path)
    p.add_argument("--prepare-2023", required=True, type=Path)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_bytes(args.repaired_source.read_bytes()) == REPAIRED_V6_SHA256, "repaired source hash changed")
    cache, cache_sha = load_sidecar_pickle(args.catalogue_cache)
    prep22, prep22_sha = load_sidecar_pickle(args.prepare_2022)
    prep23, prep23_sha = load_sidecar_pickle(args.prepare_2023)
    preparations = {2022: prep22, 2023: prep23}
    prep_shas = {"2022": prep22_sha, "2023": prep23_sha}
    for year, prep in preparations.items():
        require(prep["year"] == year, f"prepare year changed {year}")
        require(prep["catalogue_cache_sha256"] == cache_sha, f"prepare cache binding changed {year}")
        require(prep["scan_rows_sha256"] == cache["hashes"][str(year)]["scan"], f"scan cache changed {year}")
        require(prep["calibration_rows_sha256"] == cache["hashes"][str(year)]["calibration"], f"calibration cache changed {year}")

    plan = build_plan(preparations)
    shard = plan["shards"][args.shard]
    require(int(shard["shard"]) == args.shard, "global shard identity changed")

    v6 = load_module(args.repaired_source, f"orbittrace_v6_global_exact_{args.shard}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    del candidate, scorer

    event_lookup_by_year: dict[int, dict[str, dict[str, Any]]] = {}
    for year in (2022, 2023):
        events = cache["scan_by_year"][year]
        require(event_rows_sha256(events) == preparations[year]["scan_rows_sha256"], f"global exact scan rows changed {year}")
        event_lookup_by_year[year] = {str(event["id"]): event for event in events}

    results: list[dict[str, Any]] = []
    print(
        f"V6_GLOBAL_EXACT_SHARD_START shard={args.shard}/{GLOBAL_SHARD_COUNT} "
        f"tasks={shard['task_count']} proposals={shard['proposal_count']} work={shard['estimated_work']}",
        flush=True,
    )
    for ordinal, task in enumerate(shard["tasks"], start=1):
        year = int(task["year"])
        center = str(task["center"])
        start = int(task["start"])
        stop = int(task["stop"])
        prep = preparations[year]
        full_records = prep["records_by_center"][center]
        records = [dict(row) for row in full_records[start:stop]]
        require(len(records) == stop - start, f"chunk slice changed {year} {center} {start}:{stop}")
        require(proposal_anchor_ids(records) == proposal_anchor_ids(full_records)[start:stop], f"chunk input order changed {year} {center} {start}:{stop}")
        events = cache["scan_by_year"][year]
        window_events = old.window_events_for_center(events, float(center), base)
        require(len(window_events) == int(task["window_event_count"]), f"window event count changed {year} {center}")
        output = v6.exact_rescore_window_v6(
            old,
            records,
            window_events,
            event_lookup_by_year[year],
            support,
            base,
        )
        require(len(output) == len(records), f"chunk exact count mismatch {year} {center} {start}:{stop}")
        require(proposal_anchor_ids(output) == proposal_anchor_ids(records), f"chunk exact order mismatch {year} {center} {start}:{stop}")
        results.append({
            "year": year,
            "center": center,
            "start": start,
            "stop": stop,
            "proposal_count": len(records),
            "window_event_count": len(window_events),
            "exact_rows": output,
        })
        print(
            f"V6_GLOBAL_EXACT_TASK_DONE shard={args.shard} ordinal={ordinal}/{shard['task_count']} "
            f"year={year} center={center} range={start}:{stop}",
            flush=True,
        )

    payload = {
        "format": "orbittrace-v6-global-exact-chunk-result-v1",
        "shard": args.shard,
        "shard_count": GLOBAL_SHARD_COUNT,
        "plan_sha256": plan["plan_sha256"],
        "catalogue_cache_sha256": cache_sha,
        "prepare_sha256": prep_shas,
        "repaired_v6_sha256": REPAIRED_V6_SHA256,
        "tasks": results,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_loaded": True,
            "original_exact_rescore_function_used_unchanged": True,
            "contiguous_record_chunks_only": True,
        },
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"global_exact_shard_{args.shard}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / f"global_exact_shard_{args.shard}.sha256").write_text(digest + "\n")
    manifest = {key: payload[key] for key in ("shard", "shard_count", "plan_sha256", "catalogue_cache_sha256", "prepare_sha256", "repaired_v6_sha256", "firewall")}
    manifest.update({"task_count": len(results), "proposal_count": sum(row["proposal_count"] for row in results), "checkpoint_sha256": digest})
    (args.output / f"global_exact_shard_{args.shard}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"V6_GLOBAL_EXACT_SHARD_DONE shard={args.shard} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
