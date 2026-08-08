from __future__ import annotations

import argparse
import json
import math
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_checkpointed_fallback.parallel_exact_rescore import install
from orbittrace_v6_exact_fanout_v2.run_exact_center_shard import balanced_center_assignment

YEAR = 2023
PARENT_SHARD_COUNT = 6
PARENT_SHARD_INDEX = 0


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def build_rescue_bins(pre: dict[str, Any], rescue_count: int) -> tuple[list[list[dict[str, Any]]], list[int]]:
    require(rescue_count > 0, "rescue_count must be positive")
    parent_centers = balanced_center_assignment(pre, PARENT_SHARD_COUNT)[PARENT_SHARD_INDEX]
    total_cost = sum(len(pre["centers"][c]["records"]) * len(pre["centers"][c]["window_event_ids"]) for c in parent_centers)
    ideal = total_cost / rescue_count
    pieces: list[dict[str, Any]] = []
    for center in parent_centers:
        spec = pre["centers"][center]
        nr = len(spec["records"]); ne = len(spec["window_event_ids"]); cost = nr * ne
        count = max(1, min(nr, int(math.ceil(cost / ideal))))
        q, r = divmod(nr, count)
        start = 0
        for piece_index in range(count):
            n = q + (1 if piece_index < r else 0)
            stop = start + n
            pieces.append({"center": center, "record_start": start, "record_stop": stop, "record_count": n, "window_event_count": ne, "estimated_cost": n * ne})
            start = stop
        require(start == nr, f"slice coverage changed center {center}")
    bins = [[] for _ in range(rescue_count)]; loads = [0] * rescue_count
    for piece in sorted(pieces, key=lambda x: (-int(x["estimated_cost"]), float(x["center"]), int(x["record_start"]))):
        target = min(range(rescue_count), key=lambda i: (loads[i], i))
        bins[target].append(piece); loads[target] += int(piece["estimated_cost"])
    for b in bins:
        b.sort(key=lambda x: (float(x["center"]), int(x["record_start"])))
    # exact complete coverage of the original v2 parent-shard centers
    for center in parent_centers:
        ranges = sorted((int(p["record_start"]), int(p["record_stop"])) for b in bins for p in b if float(p["center"]) == center)
        cursor = 0
        for start, stop in ranges:
            require(start == cursor and stop > start, f"rescue gap/overlap center {center}")
            cursor = stop
        require(cursor == len(pre["centers"][center]["records"]), f"rescue coverage incomplete center {center}")
    return bins, loads


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--rescue-index", required=True, type=int)
    p.add_argument("--rescue-count", required=True, type=int)
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


def main() -> int:
    args = parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    raw = args.preexact_checkpoint.read_bytes(); sidecar = args.preexact_checkpoint.with_suffix(".sha256")
    require(sidecar.exists() and sha256_bytes(raw) == sidecar.read_text().strip().split()[0], "preexact SHA mismatch")
    pre = pickle.loads(raw)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2" and int(pre["year"]) == YEAR, "wrong preexact checkpoint")
    require(pre["firewall"]["target_interval_remains_excluded"] is True and pre["firewall"]["hidden_labels_not_saved"] is True, "preexact firewall failed")
    bins, loads = build_rescue_bins(pre, args.rescue_count)
    require(0 <= args.rescue_index < args.rescue_count, "invalid rescue index")
    selected = bins[args.rescue_index]
    require(bool(selected), "empty rescue slice")

    v6 = load_module(args.repaired_source, f"orbittrace_shard0_rescue_{args.rescue_index}")
    require(sha256_bytes(args.repaired_source.read_bytes()) == pre["repaired_v6_sha256"], "repaired source mismatch")
    old = v6.load_base_runner(args.base_runner); support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, _sources = support.parse_catalogue(base)
    scan = scan_by_year[YEAR]; calibration = calibration_by_year[YEAR]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"] and event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "input rows changed")
    require(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan), "blind interval present")
    lookup = {str(e["id"]): e for e in scan}
    config = install(v6, workers=args.workers, min_parallel_records=256)

    out_slices = []
    for piece in selected:
        center = float(piece["center"]); start = int(piece["record_start"]); stop = int(piece["record_stop"])
        spec = pre["centers"][center]; all_records = spec["records"]
        require(canonical_sha(all_records) == spec["records_sha256"], f"records changed center {center}")
        ids = [str(v) for v in spec["window_event_ids"]]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window IDs changed center {center}")
        window_events = [lookup[eid] for eid in ids]
        require([str(e["id"]) for e in old.window_events_for_center(scan, center, base)] == ids, f"window reconstruction changed center {center}")
        records = all_records[start:stop]
        exact = v6.exact_rescore_window_v6(old, records, window_events, lookup, support, base)
        require([str(r["proposal_anchor_id"]) for r in exact] == [str(r["proposal_anchor_id"]) for r in records], f"exact slice order changed center {center}")
        out_slices.append({"center": center, "record_start": start, "record_stop": stop, "records_sha256": canonical_sha(records), "outputs": exact})
        print(f"SHARD0_RESCUE_SLICE_DONE rescue={args.rescue_index}/{args.rescue_count} center={center:.1f} records={len(records):,}", flush=True)

    payload = {"format":"orbittrace-v6-shard0-rescue-slice-v1","year":YEAR,"parent_shard_index":PARENT_SHARD_INDEX,"parent_shard_count":PARENT_SHARD_COUNT,"rescue_index":args.rescue_index,"rescue_count":args.rescue_count,"preexact_sha256":sha256_bytes(raw),"scan_rows_sha256":pre["scan_rows_sha256"],"estimated_loads":loads,"slices":out_slices,"executor":config,"firewall":{"target_interval_remains_excluded":True,"labels_not_evaluated":True}}
    out_raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"shard0_rescue_{args.rescue_index:02d}.pkl"; path.write_bytes(out_raw)
    digest = sha256_bytes(out_raw); path.with_suffix(".sha256").write_text(digest + "\n")
    print(f"PASS_SHARD0_RESCUE_SLICE rescue={args.rescue_index}/{args.rescue_count} load={loads[args.rescue_index]:,} sha={digest}", flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
