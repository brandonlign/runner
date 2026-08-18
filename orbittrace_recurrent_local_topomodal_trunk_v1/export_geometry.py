#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_EVENTS_BY_YEAR = {2022: 315024, 2023: 423658}
EXPECTED_TOTAL = 738682


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent = load_module(a.parent_runner, "local_trunk_geometry_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent firewall constants changed")

    qmod = load_module(a.quality_source, "local_trunk_geometry_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-local-topomodal-trunk-v1-target-excluded-geometry-export"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    counts: dict[int, int] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"normalization count changed {year}")
        counts[year] = len(rows)
        events.extend(rows)
    req(counts == EXPECTED_EVENTS_BY_YEAR, f"accessible annual counts changed: {counts}")
    req(len(events) == EXPECTED_TOTAL, f"pooled event count changed: {len(events)}")
    req(len({str(e['id']) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    rows = [
        {
            "id": str(e["id"]),
            "year": int(e["year"]),
            "sol": float(e["sol"]),
            "lon": float(e["lon"]),
            "lat": float(e["lat"]),
            "vg": float(e["vg"]),
        }
        for e in events
    ]
    rows.sort(key=lambda e: str(e["id"]))
    universe_sha = hashlib.sha256("\n".join(str(e["id"]) for e in rows).encode()).hexdigest()
    payload = {
        "schema": "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_GEOMETRY",
        "scientific_role": "LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY",
        "years": list(YEARS),
        "events_total": len(rows),
        "events_by_year": {str(y): counts[y] for y in YEARS},
        "event_universe_sha256": universe_sha,
        "events": rows,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_exported": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbital_information_access": False,
        "station_metadata_access": False,
        "uncertainty_metadata_access": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("schema", "events_total", "events_by_year", "event_universe_sha256")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
