from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_exact_sharded_acceleration.common import (
    REPAIRED_V6_SHA256,
    load_sidecar_pickle,
    SHARD_COUNT,
    proposal_anchor_ids,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--shard", required=True, type=int, choices=tuple(range(SHARD_COUNT)))
    p.add_argument("--catalogue-cache", required=True, type=Path)
    p.add_argument("--prepare", required=True, type=Path)
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
    prep, prep_sha = load_sidecar_pickle(args.prepare)
    require(prep["year"] == args.year, "prepare year mismatch")
    require(prep["scan_rows_sha256"] == cache["hashes"][str(args.year)]["scan"], "scan cache changed")
    require(prep["calibration_rows_sha256"] == cache["hashes"][str(args.year)]["calibration"], "calibration cache changed")
    records_by_center = prep["records_by_center"]
    require(len(prep["shard_plan"]) == SHARD_COUNT, "prepare shard plan changed")
    require([int(row["shard"]) for row in prep["shard_plan"]] == list(range(SHARD_COUNT)), "prepare shard ids changed")
    centers = [str(key) for key in prep["shard_plan"][args.shard]["centers"]]
    events = cache["scan_by_year"][args.year]
    require(event_rows_sha256(events) == prep["scan_rows_sha256"], "exact shard scan rows changed")

    v6 = load_module(args.repaired_source, f"orbittrace_v6_accel_exact_{args.year}_{args.shard}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    del candidate, scorer
    event_lookup = {str(event["id"]): event for event in events}

    exact_by_center: dict[str, list[dict]] = {}
    print(
        f"V6_ACCEL_EXACT_SHARD_START year={args.year} shard={args.shard}/{SHARD_COUNT} "
        f"centers={len(centers)} proposals={sum(len(records_by_center[key]) for key in centers)}",
        flush=True,
    )
    for ordinal, key in enumerate(centers, start=1):
        center = float(key)
        records = [dict(row) for row in records_by_center[key]]
        require(proposal_anchor_ids(records) == sorted(proposal_anchor_ids(records)), f"prepare record order changed center={key}")
        window_events = old.window_events_for_center(events, center, base)
        output = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
        require(len(output) == len(records), f"exact output count mismatch center={key}")
        require(proposal_anchor_ids(output) == proposal_anchor_ids(records), f"exact output order mismatch center={key}")
        exact_by_center[key] = output
        print(
            f"V6_ACCEL_EXACT_CENTER_DONE year={args.year} shard={args.shard} "
            f"center={key} ordinal={ordinal}/{len(centers)} proposals={len(records)}",
            flush=True,
        )

    payload = {
        "format": "orbittrace-v6-exact-shard-result-v1",
        "year": args.year,
        "shard": args.shard,
        "shard_count": SHARD_COUNT,
        "centers": centers,
        "proposal_count": sum(len(records_by_center[key]) for key in centers),
        "exact_by_center": exact_by_center,
        "prepare_sha256": prep_sha,
        "catalogue_cache_sha256": cache_sha,
        "repaired_v6_sha256": REPAIRED_V6_SHA256,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_loaded": True,
            "original_exact_rescore_function_used_unchanged": True,
        },
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    out = args.output / f"exact_year_{args.year}_shard_{args.shard}.pkl"
    out.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / f"exact_year_{args.year}_shard_{args.shard}.sha256").write_text(digest + "\n")
    manifest = {k: payload[k] for k in ("year", "shard", "shard_count", "centers", "proposal_count", "prepare_sha256", "catalogue_cache_sha256", "repaired_v6_sha256", "firewall")}
    manifest["checkpoint_sha256"] = digest
    (args.output / f"exact_year_{args.year}_shard_{args.shard}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"V6_ACCEL_EXACT_SHARD_DONE year={args.year} shard={args.shard} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
