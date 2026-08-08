from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_checkpointed_fallback.parallel_exact_rescore import install
from orbittrace_v6_exact_fanout_v3.workunit_plan import balanced_unit_shards


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--shard-index", required=True, type=int)
    p.add_argument("--shard-count", required=True, type=int)
    p.add_argument("--max-records-per-unit", required=True, type=int)
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


def main() -> int:
    args = parse_args()
    require(args.shard_count > 0, "shard_count must be positive")
    require(0 <= args.shard_index < args.shard_count, "invalid shard index")
    require(args.max_records_per_unit > 0, "max_records_per_unit must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_preexact(args.preexact_checkpoint, args.year)

    v6 = load_module(args.repaired_source, f"orbittrace_v6_workunit_{args.year}_{args.shard_index}")
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

    executor = install(v6, workers=args.workers, min_parallel_records=256)
    shard_units, shard_loads = balanced_unit_shards(pre, args.shard_count, args.max_records_per_unit)
    selected = shard_units[args.shard_index]
    print(
        f"V6_WORKUNIT_BALANCE year={args.year} shards={args.shard_count} "
        f"max_records={args.max_records_per_unit} loads={shard_loads} selected_cost={shard_loads[args.shard_index]}",
        flush=True,
    )

    outputs: list[dict[str, Any]] = []
    for ordinal, unit in enumerate(selected, start=1):
        center = float(unit["center"])
        start = int(unit["start"])
        stop = int(unit["stop"])
        spec = pre["centers"][center]
        records = spec["records"]
        require(canonical_sha(records) == spec["records_sha256"], f"captured record hash mismatch center {center}")
        sliced = records[start:stop]
        require(len(sliced) == stop - start, f"work-unit record count mismatch center {center}")
        ids = [str(value) for value in spec["window_event_ids"]]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"captured window hash mismatch center {center}")
        require(all(event_id in event_lookup for event_id in ids), f"captured window event absent center {center}")
        window_events = [event_lookup[event_id] for event_id in ids]
        canonical_window = old.window_events_for_center(scan, center, base)
        require([str(row["id"]) for row in canonical_window] == ids, f"window reconstruction changed center {center}")
        exact = v6.exact_rescore_window_v6(old, sliced, window_events, event_lookup, support, base)
        require(
            [str(row["proposal_anchor_id"]) for row in exact]
            == [str(row["proposal_anchor_id"]) for row in sliced],
            f"exact output order changed center {center} slice {start}:{stop}",
        )
        outputs.append({
            "center": center,
            "start": start,
            "stop": stop,
            "records_sha256": canonical_sha(sliced),
            "exact": exact,
        })
        print(
            f"V6_WORKUNIT_DONE year={args.year} shard={args.shard_index}/{args.shard_count} "
            f"unit={ordinal}/{len(selected)} center={center:.1f} slice={start}:{stop}",
            flush=True,
        )

    payload = {
        "format": "orbittrace-v6-exact-workunit-shard-v3",
        "year": args.year,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "max_records_per_unit": args.max_records_per_unit,
        "preexact_sha256": pre_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "scheduled_cost": shard_loads[args.shard_index],
        "all_shard_costs": shard_loads,
        "units": outputs,
        "executor": executor,
        "firewall": {"target_interval_remains_excluded": True, "labels_not_evaluated": True},
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_workunits_{args.year}_shard_{args.shard_index:02d}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    print(
        f"PASS_V6_WORKUNIT_SHARD year={args.year} shard={args.shard_index}/{args.shard_count} "
        f"units={len(outputs)} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
