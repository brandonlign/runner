#!/usr/bin/env python3
"""Zero-endpoint audit of fields exposed by the exact target-excluded GMN v31 runtime."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
RANKER_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
UNCERTAINTY_NAMES = (
    "ra_sigma", "dec_sigma", "vg_sigma", "num_stat", "fiterr", "qc",
    "ra_sd", "dec_sd", "vg_sd", "ra_error", "dec_error", "vg_error",
    "sigma_ra", "sigma_dec", "sigma_vg", "ncam", "median_fit_err",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ranker-source", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha256(args.ranker_source) == RANKER_SHA, "ranker source changed")
    require(sha256(args.v8_result_json) == V8_SHA, "v8 result changed")

    q = load(args.ranker_source, "frozen_ranker")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = q.v1.mult.MONTH_KEYS
    support.CORPUS = "orbittrace-gmn-v31-event-schema-audit-v1"
    support.RANKING_VARIANTS = ("persistence",)
    require((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "blind interval changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(args)
    scan, _calibration, _labels, _sources = support.parse_catalogue(baseline)
    require(sorted(scan) == list(YEARS), "year set changed")

    by_year: dict[str, Any] = {}
    global_union: set[str] = set()
    global_intersection: set[str] | None = None
    for year in YEARS:
        rows = scan[year]
        require(rows, f"empty scan {year}")
        union: set[str] = set()
        intersection: set[str] | None = None
        blind_hits = 0
        for row in rows:
            keys = set(map(str, row.keys()))
            union |= keys
            intersection = keys if intersection is None else intersection & keys
            sol = float(row["sol"])
            require(math.isfinite(sol), f"nonfinite solar longitude {year}")
            if BLIND[0] <= sol <= BLIND[1]:
                blind_hits += 1
        require(blind_hits == 0, f"protected rows exposed in {year}")
        global_union |= union
        global_intersection = union.copy() if global_intersection is None else global_intersection & union

        field_counts = {
            name: sum(1 for row in rows if name in row and populated(row[name]))
            for name in UNCERTAINTY_NAMES
            if name in union
        }
        by_year[str(year)] = {
            "row_count": len(rows),
            "union_fields": sorted(union),
            "intersection_fields": sorted(intersection or set()),
            "uncertainty_or_quality_field_populated_counts": field_counts,
            "protected_interval_rows": blind_hits,
        }

    result = {
        "verdict": "PASS_GMN_V31_EVENT_SCHEMA_AUDIT",
        "scientific_endpoint_computed": False,
        "candidate_ranking_computed": False,
        "truth_metric_computed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
        "ranker_sha256": sha256(args.ranker_source),
        "v8_sha256": sha256(args.v8_result_json),
        "global_union_fields": sorted(global_union),
        "global_intersection_fields": sorted(global_intersection or set()),
        "by_year": by_year,
    }
    out = args.output / "GMN_V31_EVENT_SCHEMA_AUDIT_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
