from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from orbittrace_v6_checkpointed_fallback.common import load_module, require
from orbittrace_v6_checkpointed_fallback.parallel_exact_rescore import install


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--year", type=int, default=2022)
    p.add_argument("--center", type=float, default=140.0)
    p.add_argument("--records", type=int, default=512)
    p.add_argument("--workers", type=int, default=4)
    return p.parse_args()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def main() -> int:
    args = parse_args()
    require(not (20.0 <= args.center <= 55.0), "benchmark center intersects blind interval")
    v6 = load_module(args.repaired_source, "orbittrace_v6_parallel_benchmark")
    require(all(v6.v3.self_test().values()), "v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()), "v3 membership self-test failed")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, _scorer = support.load_sources(args)

    print("V6_PARALLEL_EQUIV_PARSE_START", flush=True)
    scan_by_year, _calibration_by_year, _hidden_labels, _sources = support.parse_catalogue(base)
    events = scan_by_year[args.year]
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in events), "blind interval present in scan")
    window_events = old.window_events_for_center(events, args.center, base)
    require(len(window_events) >= old.EPISODE_SIZE, "benchmark window too small")
    event_lookup = {str(row["id"]): row for row in events}

    anchors = sorted(window_events, key=lambda row: str(row["id"]))[: min(args.records, len(window_events))]
    require(len(anchors) >= 256, "benchmark requires at least 256 anchors")
    records = [
        {
            "year": args.year,
            "proposal_anchor_id": str(row["id"]),
            "window_center": float(args.center),
            "bin": int(float(row["sol"]) // 10.0) % 36,
            "benchmark_only": True,
        }
        for row in anchors
    ]

    original = v6.exact_rescore_window_v6
    t0 = time.perf_counter()
    scalar = original(old, records, window_events, event_lookup, support, base)
    scalar_seconds = time.perf_counter() - t0

    config = install(v6, workers=args.workers, min_parallel_records=1)
    t1 = time.perf_counter()
    parallel = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
    parallel_seconds = time.perf_counter() - t1

    scalar_bytes = canonical(scalar)
    parallel_bytes = canonical(parallel)
    require(scalar_bytes == parallel_bytes, "parallel exact-rescore output differs from scalar output")
    require([row["proposal_anchor_id"] for row in scalar] == [row["proposal_anchor_id"] for row in parallel], "proposal order changed")

    speedup = scalar_seconds / parallel_seconds if parallel_seconds > 0 else float("inf")
    result = {
        "verdict": "PASS_V6_PARALLEL_EXACT_RESCORE_EQUIVALENCE",
        "year": args.year,
        "center": args.center,
        "records": len(records),
        "window_events": len(window_events),
        "scalar_seconds": scalar_seconds,
        "parallel_seconds": parallel_seconds,
        "speedup": speedup,
        "executor": config,
        "blind_interval_absent": True,
        "labels_not_evaluated": True,
    }
    print("V6_PARALLEL_EQUIV_RESULT_BEGIN")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("V6_PARALLEL_EQUIV_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
