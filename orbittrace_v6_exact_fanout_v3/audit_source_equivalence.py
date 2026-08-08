from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from orbittrace_v6_exact_fanout_v3.combine_exact_workunits import canonical_sha, reconstruct_exact_by_center
from orbittrace_v6_exact_fanout_v3.workunit_plan import balanced_unit_shards, build_work_units


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def fake_pre() -> dict[str, Any]:
    # Center 100 intentionally dominates whole-center cost. The audit proves v3
    # splits it into independent execution units instead of leaving one runner as
    # an unavoidable straggler.
    specs = {
        100.0: (1300, 1400),
        200.0: (420, 700),
        300.0: (260, 350),
        340.0: (180, 200),
    }
    centers: dict[float, dict[str, Any]] = {}
    total = 0
    for center, (n_records, n_events) in specs.items():
        records = [
            {
                "proposal_anchor_id": f"{center:.1f}-{index:05d}",
                "window_center": center,
                "payload": index * 17 + int(center),
            }
            for index in range(n_records)
        ]
        ids = [f"event-{center:.1f}-{index:05d}" for index in range(n_events)]
        centers[center] = {
            "records": records,
            "records_sha256": canonical_sha(records),
            "window_event_ids": ids,
            "window_event_ids_sha256": canonical_sha(ids),
        }
        total += n_records
    return {
        "format": "orbittrace-v6-preexact-fanout-v2",
        "year": 2023,
        "ordered_centers": sorted(centers),
        "centers": centers,
        "total_records": total,
        "firewall": {"target_interval_remains_excluded": True, "hidden_labels_not_saved": True},
    }


def fake_exact(records: list[dict[str, Any]], window_size: int) -> list[dict[str, Any]]:
    # Deterministic stand-in used only to test partition/reassembly identity.
    return [
        {
            "proposal_anchor_id": str(row["proposal_anchor_id"]),
            "fake_exact_value": int(row["payload"]) * 31 + window_size,
        }
        for row in records
    ]


def calls_named(tree: ast.AST, name: str) -> list[ast.Call]:
    """Find executable calls by name; comments/provenance strings do not count."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Attribute) and node.func.attr == name)
            or (isinstance(node.func, ast.Name) and node.func.id == name)
        )
    ]


def main() -> int:
    pre = fake_pre()
    max_records = 512
    shard_count = 4

    units = build_work_units(pre, max_records)
    require(all(int(unit["records"]) <= max_records for unit in units), "unit record cap failed")
    dominant = [unit for unit in units if float(unit["center"]) == 100.0]
    require(len(dominant) == 3, f"dominant center was not split as expected: {len(dominant)}")

    bins1, loads1 = balanced_unit_shards(pre, shard_count, max_records)
    bins2, loads2 = balanced_unit_shards(pre, shard_count, max_records)
    require(bins1 == bins2 and loads1 == loads2, "work-unit scheduling is not deterministic")
    dominant_shards = {
        shard_index
        for shard_index, values in enumerate(bins1)
        if any(float(unit["center"]) == 100.0 for unit in values)
    }
    require(len(dominant_shards) >= 2, "dominant center remains runner-indivisible")

    # Materialize fake exact outputs independently by scheduled work unit, then
    # use the production combiner helper to reconstruct the monolithic result.
    unit_outputs: dict[tuple[float, int, int], dict[str, Any]] = {}
    for values in bins1:
        for unit in values:
            center = float(unit["center"])
            start = int(unit["start"])
            stop = int(unit["stop"])
            records = pre["centers"][center]["records"][start:stop]
            key = (center, start, stop)
            unit_outputs[key] = {
                "center": center,
                "start": start,
                "stop": stop,
                "records_sha256": canonical_sha(records),
                "exact": fake_exact(records, len(pre["centers"][center]["window_event_ids"])),
            }
    reconstructed = reconstruct_exact_by_center(pre, unit_outputs)
    monolithic = {
        center: fake_exact(
            pre["centers"][center]["records"],
            len(pre["centers"][center]["window_event_ids"]),
        )
        for center in pre["ordered_centers"]
    }
    require(reconstructed == monolithic, "work-unit reconstruction differs from monolithic output")
    require(
        json.dumps(reconstructed, sort_keys=True, separators=(",", ":"))
        == json.dumps(monolithic, sort_keys=True, separators=(",", ":")),
        "canonical reconstructed bytes differ from monolithic output",
    )

    # Integrity negative control: one reordered unit must be rejected.
    first_key = sorted(unit_outputs)[0]
    corrupted = {key: dict(value) for key, value in unit_outputs.items()}
    corrupted[first_key] = dict(corrupted[first_key])
    corrupted[first_key]["exact"] = list(reversed(corrupted[first_key]["exact"]))
    try:
        reconstruct_exact_by_center(pre, corrupted)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("combiner accepted reordered exact outputs")

    root = Path(__file__).resolve().parent
    runner_path = root / "run_exact_workunit_shard.py"
    combine_path = root / "combine_exact_workunits.py"
    protocol_path = root / "PROTOCOL.md"
    runner_source = runner_path.read_text()
    combine_source = combine_path.read_text()
    protocol = protocol_path.read_text()

    runner_tree = ast.parse(runner_source)
    combine_tree = ast.parse(combine_source)
    exact_calls = calls_named(runner_tree, "exact_rescore_window_v6")
    require(len(exact_calls) == 1, f"runner exact-rescore call count changed: {len(exact_calls)}")
    for forbidden in ("scan_year_v6", "evaluate_order", "evaluate_families_v6"):
        require(not calls_named(runner_tree, forbidden), f"scientific/evaluation call leaked into work-unit runner: {forbidden}")
        require(not calls_named(combine_tree, forbidden), f"scientific/evaluation call leaked into combiner: {forbidden}")
    label_reads = [
        node for node in ast.walk(runner_tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id in {"hidden_labels", "_hidden_labels"}
    ]
    require(not label_reads, "inherited hidden-label object is read by work-unit runner")
    require(not calls_named(combine_tree, "exact_rescore_window_v6"), "combiner recomputes exact science")
    require('"orbittrace-v6-exact-center-shard-v2"' in combine_source, "combiner no longer emits audited v2 replay format")
    require("512 records" in protocol, "frozen execution work-unit cap missing from protocol")
    require("execution equivalence" in protocol.lower(), "equivalence-only claim boundary missing")

    # Load spread is not a scientific gate, but this synthetic case should show
    # the scheduling objective is doing real work rather than merely repartitioning.
    require(max(loads1) < sum(loads1), "scheduler did not distribute work")
    print("PASS_V6_WORKUNIT_FANOUT_V3_SOURCE_EQUIVALENCE_AUDIT")
    print(f"units={len(units)} shard_costs={loads1} dominant_center_shards={sorted(dominant_shards)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
