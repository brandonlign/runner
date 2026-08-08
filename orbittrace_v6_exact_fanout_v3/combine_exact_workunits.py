from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import require, sha256_bytes
from orbittrace_v6_exact_fanout_v3.workunit_plan import build_work_units


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--workunit-shards-dir", required=True, type=Path)
    p.add_argument("--max-records-per-unit", required=True, type=int)
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


def main() -> int:
    args = parse_args()
    require(args.max_records_per_unit > 0, "max_records_per_unit must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_pickle_with_sidecar(args.preexact_checkpoint)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format changed")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")

    expected_units = build_work_units(pre, args.max_records_per_unit)
    expected_keys = {
        (float(unit["center"]), int(unit["start"]), int(unit["stop"]))
        for unit in expected_units
    }
    shard_paths = sorted(args.workunit_shards_dir.glob(f"v6_workunits_{args.year}_shard_*.pkl"))
    require(bool(shard_paths), "no work-unit shard files")

    seen_shards: set[int] = set()
    shard_count: int | None = None
    units: dict[tuple[float, int, int], dict[str, Any]] = {}
    for path in shard_paths:
        shard, _digest = load_pickle_with_sidecar(path)
        require(shard["format"] == "orbittrace-v6-exact-workunit-shard-v3", f"work-unit format changed {path.name}")
        require(int(shard["year"]) == args.year, f"work-unit year mismatch {path.name}")
        require(int(shard["max_records_per_unit"]) == args.max_records_per_unit, f"work-unit size changed {path.name}")
        require(shard["preexact_sha256"] == pre_sha, f"preexact identity mismatch {path.name}")
        require(shard["scan_rows_sha256"] == pre["scan_rows_sha256"], f"scan identity mismatch {path.name}")
        require(shard["firewall"]["target_interval_remains_excluded"] is True, f"firewall failed {path.name}")
        require(shard["firewall"]["labels_not_evaluated"] is True, f"label firewall failed {path.name}")
        current_count = int(shard["shard_count"])
        shard_count = current_count if shard_count is None else shard_count
        require(current_count == shard_count, "mixed work-unit shard counts")
        index = int(shard["shard_index"])
        require(index not in seen_shards, f"duplicate work-unit shard index {index}")
        seen_shards.add(index)
        for unit in shard["units"]:
            key = (float(unit["center"]), int(unit["start"]), int(unit["stop"]))
            require(key not in units, f"duplicate work unit {key}")
            units[key] = unit

    require(shard_count is not None, "missing work-unit shard count")
    require(seen_shards == set(range(shard_count)), f"incomplete work-unit shards: {sorted(seen_shards)} / {shard_count}")
    require(set(units) == expected_keys, "work-unit coverage differs from deterministic plan")

    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        records = pre["centers"][center]["records"]
        center_units = sorted(
            (unit for key, unit in units.items() if key[0] == center),
            key=lambda unit: int(unit["start"]),
        )
        cursor = 0
        exact: list[dict[str, Any]] = []
        for unit in center_units:
            start = int(unit["start"])
            stop = int(unit["stop"])
            require(start == cursor, f"work-unit gap/overlap during combine center {center}")
            sliced = records[start:stop]
            require(canonical_sha(sliced) == unit["records_sha256"], f"record slice changed center {center} {start}:{stop}")
            part = list(unit["exact"])
            require(
                [str(row["proposal_anchor_id"]) for row in part]
                == [str(row["proposal_anchor_id"]) for row in sliced],
                f"exact slice order changed center {center} {start}:{stop}",
            )
            exact.extend(part)
            cursor = stop
        require(cursor == len(records), f"incomplete center combine {center}")
        require(
            [str(row["proposal_anchor_id"]) for row in exact]
            == [str(row["proposal_anchor_id"]) for row in records],
            f"full exact output order changed center {center}",
        )
        exact_by_center[center] = exact

    # Emit a synthetic one-shard v2 payload. The already-audited v2 replay stage
    # can consume it unchanged, so no scientific scan/replay code is duplicated.
    payload = {
        "format": "orbittrace-v6-exact-center-shard-v2",
        "year": args.year,
        "shard_index": 0,
        "shard_count": 1,
        "preexact_sha256": pre_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "centers": [float(value) for value in pre["ordered_centers"]],
        "scheduled_proposals": int(pre["total_records"]),
        "all_shard_loads": [int(pre["total_records"])],
        "exact_by_center": exact_by_center,
        "executor": {
            "workunit_fanout_v3": True,
            "source_workunit_shards": shard_count,
            "max_records_per_unit": args.max_records_per_unit,
            "scientific_function": "unchanged exact_rescore_window_v6 on contiguous proposal slices",
        },
        "firewall": {"target_interval_remains_excluded": True, "labels_not_evaluated": True},
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_exact_{args.year}_shard_00.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    print(
        f"PASS_V6_WORKUNIT_COMBINE year={args.year} centers={len(exact_by_center)} "
        f"units={len(units)} synthetic_v2_sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
