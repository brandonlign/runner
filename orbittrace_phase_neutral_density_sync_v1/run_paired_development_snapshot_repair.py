#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import run_paired_development as frozen

REQUIRED_KEYS = {"id", "year", "sol", "lon", "lat", "vg"}


def load_normalized_snapshot(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, set[str]]]:
    manifest_path = root / "manifest.json"
    manifest = frozen.json.loads(manifest_path.read_text())
    frozen.req(manifest["schema"] == "ORBITTRACE_PHASE_NEUTRAL_GMN_LABEL_FREE_SNAPSHOT_V1", "wrong snapshot schema")
    frozen.req(manifest["scientific_role"] == "METHOD_INDEPENDENT_TARGET_EXCLUDED_GMN_2022_2023_SNAPSHOT", "wrong snapshot role")
    frozen.req(manifest["years"] == list(frozen.YEARS), "snapshot years changed")
    frozen.req(manifest["blind_exclusion"] == list(frozen.BLIND), "snapshot blind interval changed")
    frozen.req(manifest["event_order_preserved"] is True, "snapshot order not preserved")
    frozen.req(manifest["labels_present"] is False, "label-free snapshot contains labels")
    frozen.req(manifest["hdbscan_fit_executed"] is False and manifest["method_evaluation_executed"] is False, "snapshot already method-bearing")
    for key in ("target_information_access","target_region_events_accessed","sonotaco_access","asfn_access","efn_access","amos_access","maarsy_scientific_access","dms_scientific_access"):
        frozen.req(manifest[key] is False, f"snapshot firewall changed: {key}")

    events: list[dict[str, Any]] = []
    annual_ids: dict[int, set[str]] = {}
    all_ids: set[str] = set()
    for year in frozen.YEARS:
        path = root / manifest["row_files"][str(year)]
        frozen.req(frozen.sha(path) == manifest["row_sha256"][str(year)], f"snapshot row hash changed {year}")
        rows = frozen.read_jsonl_gz(path)
        frozen.req(len(rows) == int(manifest["events_by_year"][str(year)]), f"snapshot row count changed {year}")
        ids: set[str] = set()
        for row in rows:
            frozen.req(set(row) == REQUIRED_KEYS, f"normalized snapshot schema changed: {sorted(row)}")
            frozen.req(int(row["year"]) == year, f"normalized snapshot year changed: {row['id']}")
            eid = str(row["id"])
            sol = float(row["sol"])
            lon = float(row["lon"])
            lat = float(row["lat"])
            vg = float(row["vg"])
            frozen.req(all(math.isfinite(x) for x in (sol, lon, lat, vg)), f"nonfinite normalized snapshot row: {eid}")
            sol %= 360.0
            frozen.req(not (frozen.BLIND[0] <= sol <= frozen.BLIND[1]), f"protected normalized snapshot row: {eid}")
            frozen.req(vg > 0.0, f"nonpositive speed in normalized snapshot row: {eid}")
            # Preserve the frozen snapshot values exactly; modulo is validation only.
            frozen.req(eid not in ids, f"duplicate ID within {year}: {eid}")
            ids.add(eid)
        frozen.req(not (all_ids & ids), f"duplicate IDs across years {year}")
        all_ids |= ids
        annual_ids[year] = ids
        events.extend(rows)

    frozen.req(len(events) == int(manifest["events_total"]), "snapshot total count changed")
    return events, manifest, annual_ids


def main() -> int:
    frozen.load_label_free_snapshot = load_normalized_snapshot
    return frozen.main()


if __name__ == "__main__":
    raise SystemExit(main())
