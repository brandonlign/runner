from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_checkpointed_fallback.parallel_exact_rescore import install
from orbittrace_v6_exact_fanout_v3.record_slice_scheduler import build_record_slices


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


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.preexact_checkpoint.read_bytes()
    sidecar = args.preexact_checkpoint.with_suffix(".sha256")
    require(sidecar.exists() and sha256_bytes(raw) == sidecar.read_text().strip().split()[0], "preexact SHA mismatch")
    pre = pickle.loads(raw)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format mismatch")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")

    v6 = load_module(args.repaired_source, f"orbittrace_v6_record_slice_{args.year}_{args.shard_index}")
    require(sha256_bytes(args.repaired_source.read_bytes()) == pre["repaired_v6_sha256"], "repaired source mismatch")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, _sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present")
    event_lookup = {str(row["id"]): row for row in scan}

    bins, loads = build_record_slices(pre, args.shard_count)
    require(0 <= args.shard_index < args.shard_count, "invalid shard index")
    selected = bins[args.shard_index]
    require(bool(selected), "empty record-slice shard")
    config = install(v6, workers=args.workers, min_parallel_records=256)
    outputs: list[dict[str, Any]] = []
    for record_slice in selected:
        center = float(record_slice["center"])
        start = int(record_slice["record_start"])
        stop = int(record_slice["record_stop"])
        spec = pre["centers"][center]
        all_records = spec["records"]
        require(canonical_sha(all_records) == spec["records_sha256"], f"captured records changed center {center}")
        ids = [str(v) for v in spec["window_event_ids"]]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window IDs changed center {center}")
        window_events = [event_lookup[event_id] for event_id in ids]
        canonical_window = old.window_events_for_center(scan, center, base)
        require([str(row["id"]) for row in canonical_window] == ids, f"window reconstruction changed center {center}")
        records = all_records[start:stop]
        require(len(records) == int(record_slice["record_count"]), "slice record count changed")
        exact = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
        require([str(r["proposal_anchor_id"]) for r in exact] == [str(r["proposal_anchor_id"]) for r in records], f"slice order changed center {center}")
        outputs.append({
            "center": center,
            "record_start": start,
            "record_stop": stop,
            "records_sha256": canonical_sha(records),
            "outputs": exact,
        })
        print(f"V6_FANOUT_V3_SLICE_DONE year={args.year} shard={args.shard_index}/{args.shard_count} center={center:.1f} range={start}:{stop} records={len(records):,}", flush=True)

    payload = {
        "format": "orbittrace-v6-exact-record-slice-shard-v3",
        "year": args.year,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "preexact_sha256": sha256_bytes(raw),
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "scheduled_estimated_cost": loads[args.shard_index],
        "all_shard_estimated_costs": loads,
        "slices": outputs,
        "executor": config,
        "firewall": {"target_interval_remains_excluded": True, "labels_not_evaluated": True},
    }
    out_raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_exact_v3_{args.year}_shard_{args.shard_index:02d}.pkl"
    path.write_bytes(out_raw)
    digest = sha256_bytes(out_raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    print(f"PASS_V6_FANOUT_V3_RECORD_SLICE_SHARD year={args.year} shard={args.shard_index}/{args.shard_count} slices={len(outputs)} cost={loads[args.shard_index]:,} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
