from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import (
    FROZEN_V6_SHA256,
    event_rows_sha256,
    load_module,
    require,
    sha256_bytes,
)
from orbittrace_v6_exact_fanout_v3.subcenter_schedule import balanced_unit_shards


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--exact-shards-dir", required=True, type=Path)
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


def load_pickle_with_sidecar(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA sidecar {path.name}")
    digest = sha256_bytes(raw)
    require(digest == sidecar.read_text().strip().split()[0], f"SHA mismatch {path.name}")
    return pickle.loads(raw), digest


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_pickle_with_sidecar(args.preexact_checkpoint)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format changed")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")

    shard_paths = sorted(args.exact_shards_dir.glob(f"v6_exact_units_{args.year}_shard_*.pkl"))
    require(bool(shard_paths), "no exact unit shard files")
    shard_count: int | None = None
    max_records_per_unit: int | None = None
    seen_indices: set[int] = set()
    exact_by_unit: dict[tuple[float, int, int], dict[str, Any]] = {}

    for path in shard_paths:
        shard, _digest = load_pickle_with_sidecar(path)
        require(shard["format"] == "orbittrace-v6-exact-unit-shard-v3", f"exact shard format changed {path.name}")
        require(int(shard["year"]) == args.year, f"exact shard year mismatch {path.name}")
        require(shard["preexact_sha256"] == pre_sha, f"exact shard preexact mismatch {path.name}")
        require(shard["scan_rows_sha256"] == pre["scan_rows_sha256"], f"exact shard scan mismatch {path.name}")
        require(shard["firewall"]["target_interval_remains_excluded"] is True, f"exact shard firewall failed {path.name}")
        require(shard["firewall"]["labels_not_evaluated"] is True, f"exact shard label firewall failed {path.name}")
        current_count = int(shard["shard_count"])
        current_limit = int(shard["max_records_per_unit"])
        shard_count = current_count if shard_count is None else shard_count
        max_records_per_unit = current_limit if max_records_per_unit is None else max_records_per_unit
        require(current_count == shard_count, "mixed exact shard counts")
        require(current_limit == max_records_per_unit, "mixed exact unit sizes")
        index = int(shard["shard_index"])
        require(index not in seen_indices, f"duplicate exact shard index {index}")
        seen_indices.add(index)

        expected_bins, expected_loads = balanced_unit_shards(
            pre,
            current_count,
            max_records_per_unit=current_limit,
        )
        expected = expected_bins[index]
        require(shard["unit_keys"] == [unit.key for unit in expected], f"unit schedule changed {path.name}")
        require(int(shard["scheduled_cost"]) == expected_loads[index], f"unit load changed {path.name}")
        require([int(value) for value in shard["all_shard_costs"]] == expected_loads, f"global unit loads changed {path.name}")
        require(len(shard["exact_units"]) == len(expected), f"unit count changed {path.name}")
        for unit, row in zip(expected, shard["exact_units"], strict=True):
            key = (float(row["center"]), int(row["start"]), int(row["stop"]))
            require(key == (unit.center, unit.start, unit.stop), f"unit metadata changed {path.name}")
            require(key not in exact_by_unit, f"duplicate exact unit {key}")
            records = pre["centers"][unit.center]["records"][unit.start:unit.stop]
            require(row["records_sha256"] == canonical_sha(records), f"unit records changed {key}")
            outputs = row["outputs"]
            require(
                [str(value["proposal_anchor_id"]) for value in outputs]
                == [str(value["proposal_anchor_id"]) for value in records],
                f"unit output order changed {key}",
            )
            exact_by_unit[key] = row

    require(shard_count is not None and max_records_per_unit is not None, "missing shard configuration")
    require(seen_indices == set(range(shard_count)), f"incomplete exact shards: {sorted(seen_indices)} / {shard_count}")
    expected_bins, _expected_loads = balanced_unit_shards(
        pre,
        shard_count,
        max_records_per_unit=max_records_per_unit,
    )
    expected_keys = {
        (unit.center, unit.start, unit.stop)
        for values in expected_bins
        for unit in values
    }
    require(set(exact_by_unit) == expected_keys, "exact unit coverage mismatch")

    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        units = sorted(
            (key, exact_by_unit[key]) for key in expected_keys if key[0] == center
        )
        cursor = 0
        outputs: list[dict[str, Any]] = []
        for (unit_center, start, stop), row in units:
            require(unit_center == center, "center merge changed")
            require(start == cursor and stop > start, f"non-contiguous exact units center {center}")
            outputs.extend(row["outputs"])
            cursor = stop
        require(cursor == len(spec["records"]), f"incomplete exact unit coverage center {center}")
        require(
            [str(row["proposal_anchor_id"]) for row in outputs]
            == [str(row["proposal_anchor_id"]) for row in spec["records"]],
            f"merged exact output order mismatch center {center}",
        )
        exact_by_center[center] = outputs

    repaired_sha = sha256_bytes(args.repaired_source.read_bytes())
    require(repaired_sha == pre["repaired_v6_sha256"], "repaired source mismatch")
    v6 = load_module(args.repaired_source, f"orbittrace_v6_subcenter_replay_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed before replay")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed before replay")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present in replay scan")
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(
        json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    require(source_sha == pre["year_sources_sha256"], "source identity changed before replay")

    original_exact = v6.exact_rescore_window_v6
    replayed: list[float] = []

    def replay_exact(old_arg, records, window_events, event_lookup, support_arg, base_arg):
        del old_arg, event_lookup, support_arg, base_arg
        require(bool(records), "unexpected empty replay exact call")
        center = float(records[0]["window_center"])
        require(center in pre["centers"], f"unexpected replay center {center}")
        require(center not in replayed, f"duplicate replay center {center}")
        spec = pre["centers"][center]
        require(canonical_sha(records) == spec["records_sha256"], f"proposal records changed before replay center {center}")
        ids = [str(row["id"]) for row in window_events]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window events changed before replay center {center}")
        outputs = exact_by_center[center]
        require(
            [str(row["proposal_anchor_id"]) for row in outputs]
            == [str(row["proposal_anchor_id"]) for row in records],
            f"exact output order mismatch center {center}",
        )
        replayed.append(center)
        return outputs

    v6.exact_rescore_window_v6 = replay_exact
    try:
        audit, anchors, components = v6.scan_year_v6(old, args.year, scan, calibration, candidate, base, scorer, support)
    finally:
        v6.exact_rescore_window_v6 = original_exact

    ordered_centers = [float(value) for value in pre["ordered_centers"]]
    require(replayed == ordered_centers, "exact replay center order changed")
    require(int(audit["year"]) == args.year, "year audit mismatch")
    require(int(audit["proposal_cap_per_window"]) == 512, "proposal cap changed")
    require(int(audit["max_primary_proposals_per_year"]) == 36864, "annual proposal budget changed")

    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "calibration_rows_sha256": pre["calibration_rows_sha256"],
        "year_sources_sha256": pre["year_sources_sha256"],
        "execution": {
            "exact_fanout_v3_subcenter": True,
            "exact_shard_count": shard_count,
            "max_records_per_unit": max_records_per_unit,
            "preexact_sha256": pre_sha,
        },
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated_in_year_job": True,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_year_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    (args.output / f"v6_year_{args.year}.json").write_text(
        json.dumps(
            {
                "year": args.year,
                "checkpoint_sha256": digest,
                "anchors": len(anchors),
                "components": len(components),
                "exact_shard_count": shard_count,
                "max_records_per_unit": max_records_per_unit,
                "preexact_sha256": pre_sha,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        f"PASS_V6_SUBCENTER_YEAR_REPLAY year={args.year} anchors={len(anchors)} "
        f"components={len(components)} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
