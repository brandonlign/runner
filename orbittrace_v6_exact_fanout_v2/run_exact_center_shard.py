from __future__ import annotations

import argparse
import json
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


def load_preexact(path: Path, year: int) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), "missing preexact SHA sidecar")
    require(sha256_bytes(raw) == sidecar.read_text().strip().split()[0], "preexact SHA mismatch")
    obj = pickle.loads(raw)
    require(obj["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format mismatch")
    require(int(obj["year"]) == year, "preexact year mismatch")
    require(obj["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(obj["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")
    return obj


def center_work(spec: dict[str, Any]) -> int:
    """Label-free deterministic work proxy for the untouched scalar rescore.

    Each proposal performs full-window geometry passes, so proposal count alone
    underweights dense windows. records × window rows is a substantially closer
    wall-clock proxy while remaining entirely pre-truth and execution-only.
    """
    proposals = len(spec["records"])
    window_rows = len(spec["window_event_ids"])
    require(proposals > 0 and window_rows > 0, "invalid preexact center workload")
    return proposals * window_rows


def balanced_center_shards(pre: dict[str, Any], shard_count: int) -> tuple[list[list[float]], list[int], list[int]]:
    require(shard_count > 0, "shard_count must be positive")
    bins: list[list[float]] = [[] for _ in range(shard_count)]
    work_loads = [0 for _ in range(shard_count)]
    proposal_loads = [0 for _ in range(shard_count)]
    items = []
    for center in pre["ordered_centers"]:
        c = float(center)
        spec = pre["centers"][c]
        proposals = len(spec["records"])
        work = center_work(spec)
        items.append((c, work, proposals))

    # Longest-processing-time scheduling by estimated scalar operations. Tie
    # breaks are deterministic and affect execution placement only, never
    # proposal order, scores, families, rankings, gates, or scientific output.
    for center, work, proposals in sorted(items, key=lambda item: (-item[1], -item[2], item[0])):
        target = min(range(shard_count), key=lambda index: (work_loads[index], proposal_loads[index], index))
        bins[target].append(center)
        work_loads[target] += work
        proposal_loads[target] += proposals
    for values in bins:
        values.sort()
    require(sorted(center for values in bins for center in values) == sorted(center for center, _, _ in items), "balanced shard coverage changed")
    require(sum(proposal_loads) == int(pre["total_records"]), "balanced proposal accounting changed")
    return bins, work_loads, proposal_loads


def main() -> int:
    args = parse_args()
    require(args.shard_count > 0, "shard_count must be positive")
    require(0 <= args.shard_index < args.shard_count, "invalid shard index")
    args.output.mkdir(parents=True, exist_ok=True)
    pre = load_preexact(args.preexact_checkpoint, args.year)

    v6 = load_module(args.repaired_source, f"orbittrace_v6_exact_shard_{args.year}_{args.shard_index}")
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
    shard_centers, shard_work_loads, shard_proposal_loads = balanced_center_shards(pre, args.shard_count)
    selected = shard_centers[args.shard_index]
    require(bool(selected), "empty exact center shard")
    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    print(
        f"V6_FANOUT_COST_BALANCE year={args.year} work_loads={shard_work_loads} "
        f"proposal_loads={shard_proposal_loads} selected_work={shard_work_loads[args.shard_index]}",
        flush=True,
    )

    for center in selected:
        spec = pre["centers"][center]
        records = spec["records"]
        require(canonical_sha(records) == spec["records_sha256"], f"captured record hash mismatch center {center}")
        ids = [str(value) for value in spec["window_event_ids"]]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"captured window hash mismatch center {center}")
        require(all(event_id in event_lookup for event_id in ids), f"captured window event absent center {center}")
        window_events = [event_lookup[event_id] for event_id in ids]
        canonical_window = old.window_events_for_center(scan, center, base)
        require([str(row["id"]) for row in canonical_window] == ids, f"window reconstruction changed center {center}")
        outputs = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
        require([str(row["proposal_anchor_id"]) for row in outputs] == [str(row["proposal_anchor_id"]) for row in records], f"exact output order changed center {center}")
        exact_by_center[center] = outputs
        print(
            f"V6_FANOUT_EXACT_DONE year={args.year} shard={args.shard_index}/{args.shard_count} "
            f"center={center:.1f} records={len(records):,} window_rows={len(ids):,} work={center_work(spec):,}",
            flush=True,
        )

    payload = {
        "format": "orbittrace-v6-exact-center-shard-v2",
        "year": args.year,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "preexact_sha256": sha256_bytes(args.preexact_checkpoint.read_bytes()),
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "centers": selected,
        "scheduled_proposals": shard_proposal_loads[args.shard_index],
        "all_shard_proposal_loads": shard_proposal_loads,
        "scheduled_work_proxy": shard_work_loads[args.shard_index],
        "all_shard_work_loads": shard_work_loads,
        "work_proxy": "proposal_count_times_window_event_count",
        "exact_by_center": exact_by_center,
        "executor": config,
        "firewall": {"target_interval_remains_excluded": True, "labels_not_evaluated": True},
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_exact_{args.year}_shard_{args.shard_index:02d}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    print(
        f"PASS_V6_FANOUT_EXACT_SHARD year={args.year} shard={args.shard_index}/{args.shard_count} "
        f"centers={len(selected)} proposals={shard_proposal_loads[args.shard_index]:,} "
        f"work={shard_work_loads[args.shard_index]:,} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
