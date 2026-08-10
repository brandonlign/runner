#!/usr/bin/env python3
"""Freeze v15 multiscale-consensus orders from eight label-free multiplicity rankings."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

ALL_CAPS = (16, 24, 32, 48, 64, 72, 96, 128)
NOMINAL_COMPONENTS = {
    128: (128, 96, 64),
    96: (96, 72, 48),
    64: (64, 48, 32),
    32: (32, 24, 16),
}
EXPECTED_FAMILY_COUNT = 92


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def validate_summary(summary: dict[str, Any], cap: int) -> None:
    require(int(summary["stress_cap"]) == cap, f"summary cap mismatch at {cap}")
    require(int(summary["family_count"]) == EXPECTED_FAMILY_COUNT, f"family count mismatch at {cap}")
    require(summary["sonotaco_2013_2014_access"] is False, f"SonotaCo access at cap {cap}")
    require(summary["maarsy_access"] is False, f"MAARSY access at cap {cap}")
    require(summary["target_information_access"] is False, f"target access at cap {cap}")
    if cap in (16, 24, 48, 72):
        require(summary["hidden_label_values_consulted"] is False, f"hidden labels consulted at generated cap {cap}")
        require(summary["postranking_label_evaluator_stubbed_before_catalogue_access"] is True, f"evaluation stub missing at generated cap {cap}")
        require(summary["episode_sizes_observed"] == [cap], f"generated cap {cap} episode size changed")
        require(float(summary["max_brown_equivalence_difference"]) <= 1e-10, f"Brown equivalence failed at generated cap {cap}")
    else:
        require(summary["truth_labels_used_only_after_ranking"] is True, f"existing cap {cap} did not freeze rank before labels")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    orders: dict[int, list[str]] = {}
    universes: dict[int, str] = {}
    order_hashes: dict[int, str] = {}
    for cap in ALL_CAPS:
        root = a.input_root / f"cap{cap}"
        rankings = load(root / "multiplicity_v5_rankings.json")
        summary = load(root / "cap_summary.json")
        validate_summary(summary, cap)
        order = [str(x) for x in rankings["multiplicity"]]
        require(len(order) == EXPECTED_FAMILY_COUNT and len(set(order)) == EXPECTED_FAMILY_COUNT, f"invalid multiplicity order at cap {cap}")
        orders[cap] = order
        universes[cap] = canonical_sha(sorted(order))
        order_hashes[cap] = canonical_sha(order)
        require(summary["family_universe_sha256"] == universes[cap], f"summary universe hash mismatch at cap {cap}")
        require(summary["multiplicity_order_sha256"] == order_hashes[cap], f"summary order hash mismatch at cap {cap}")

    require(len(set(universes.values())) == 1, "eight-cap family universe mismatch")
    universe = set(orders[128])
    results: dict[int, dict[str, Any]] = {}
    for nominal, components in NOMINAL_COMPONENTS.items():
        require(all(set(orders[cap]) == universe for cap in components), f"nominal {nominal} component universe mismatch")
        rank_maps = {cap: {fid: rank for rank, fid in enumerate(orders[cap])} for cap in components}
        rows: list[dict[str, Any]] = []
        for fid in sorted(universe):
            r1, r2, r3 = (int(rank_maps[cap][fid]) for cap in components)
            median_rank = float(statistics.median((r1, r2, r3)))
            require(median_rank in (float(r1), float(r2), float(r3)), f"three-point median identity failed for {fid}")
            rows.append({
                "family_id": fid,
                "component_caps": list(components),
                "component_ranks_zero_based": [r1, r2, r3],
                "v15_median_rank_score": median_rank,
            })
        ordered_rows = sorted(
            rows,
            key=lambda row: (
                float(row["v15_median_rank_score"]),
                int(row["component_ranks_zero_based"][0]),
                int(row["component_ranks_zero_based"][1]),
                int(row["component_ranks_zero_based"][2]),
                str(row["family_id"]),
            ),
        )
        order = [str(row["family_id"]) for row in ordered_rows]
        require(len(order) == EXPECTED_FAMILY_COUNT and set(order) == universe, f"invalid v15 order at nominal cap {nominal}")
        results[nominal] = {
            "nominal_cap": nominal,
            "component_caps": list(components),
            "rule": "median zero-based multiplicity rank across full, three-quarter, half episode caps",
            "family_count": EXPECTED_FAMILY_COUNT,
            "family_universe_sha256": universes[128],
            "component_order_sha256": {str(cap): order_hashes[cap] for cap in components},
            "v15_order_sha256": canonical_sha(order),
            "order": order,
            "rows": ordered_rows,
            "labels_read": False,
            "sonotaco_2013_2014_access": False,
            "maarsy_access": False,
            "target_information_access": False,
        }
        (a.output / f"v15_order_nominal{nominal}.json").write_text(json.dumps(results[nominal], indent=2, sort_keys=True) + "\n")

    audit = {
        "verdict": "PASS_V15_PRETRUTH_CONSENSUS_FREEZE",
        "all_input_caps": list(ALL_CAPS),
        "nominal_components": {str(k): list(v) for k, v in NOMINAL_COMPONENTS.items()},
        "family_count": EXPECTED_FAMILY_COUNT,
        "family_universe_sha256": universes[128],
        "all_component_rankings_frozen_before_v15_consensus": True,
        "all_v15_orders_frozen_before_labels": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }
    (a.output / "v15_pretruth_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
