from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

from orbittrace_v6_checkpointed_fallback.common import load_module, require, sha256_bytes
from orbittrace_v6_exact_sharded_acceleration.common import (
    REPAIRED_V6_SHA256,
    load_sidecar_pickle,
    capture_scan_prefix,
    shard_plan_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--catalogue-cache", required=True, type=Path)
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
    require(cache["format"] == "orbittrace-v6-target-excluded-catalogue-cache-v1", "catalogue cache format changed")
    require(cache["firewall"]["real_hidden_labels_not_serialized"] is True, "catalogue cache firewall failed")
    events = cache["scan_by_year"][args.year]
    calibration = cache["calibration_by_year"][args.year]

    v6 = load_module(args.repaired_source, f"orbittrace_v6_accel_prepare_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    print(f"V6_ACCEL_PREPARE_START year={args.year}", flush=True)
    captured = capture_scan_prefix(v6, old, args.year, events, calibration, candidate, base, scorer, support)
    captured["catalogue_cache_sha256"] = cache_sha
    event_count_by_center = {
        key: len(old.window_events_for_center(events, float(key), base))
        for key in captured["records_by_center"]
    }
    work_by_center = {
        key: len(captured["records_by_center"][key]) * event_count_by_center[key]
        for key in captured["records_by_center"]
    }
    captured["window_event_count_by_center"] = event_count_by_center
    captured["estimated_work_by_center"] = work_by_center
    captured["shard_plan"] = shard_plan_summary(
        captured["records_by_center"], work_by_center=work_by_center, event_count_by_center=event_count_by_center
    )
    raw = pickle.dumps(captured, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"prepare_year_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / f"prepare_year_{args.year}.sha256").write_text(digest + "\n")
    manifest = {
        "year": args.year,
        "checkpoint_sha256": digest,
        "center_count": captured["center_count"],
        "proposal_count": captured["proposal_count"],
        "records_by_center_sha256": captured["records_by_center_sha256"],
        "shard_plan": captured["shard_plan"],
        "scan_rows_sha256": captured["scan_rows_sha256"],
        "calibration_rows_sha256": captured["calibration_rows_sha256"],
        "firewall": captured["firewall"],
    }
    (args.output / f"prepare_year_{args.year}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"V6_ACCEL_PREPARE_DONE year={args.year} centers={captured['center_count']} proposals={captured['proposal_count']}", flush=True)
    print(json.dumps(captured["shard_plan"], indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
