#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import run_development as parent

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def finite(v: Any) -> bool:
    if v is None:
        return False
    try:
        return math.isfinite(float(v))
    except (TypeError, ValueError):
        return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(parent.sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN runtime utility changed")
    req(parent.sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support artifact changed")

    qmod = parent.load_module(a.quality_source, "gmn_uncertainty_schema_audit_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-gmn-uncertainty-schema-audit-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"unexpected GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    # Schema-only audit: never serialize event values or label values.
    rows_by_year = {y: list(scan[y]) for y in YEARS}
    union_keys = sorted({str(k) for rows in rows_by_year.values() for row in rows for k in row.keys()})
    key_l = {k: k.lower() for k in union_keys}
    relevant = [k for k in union_keys if any(tok in key_l[k] for tok in (
        "err", "error", "sd", "sigma", "unc", "qc", "conv", "ncam",
        "ra", "dec", "vg", "vel", "speed", "radiant"
    ))]

    coverage: dict[str, dict[str, dict[str, int]]] = {}
    for y, rows in rows_by_year.items():
        coverage[str(y)] = {}
        for k in relevant:
            present = sum(k in row and row[k] is not None for row in rows)
            finite_count = sum(k in row and finite(row[k]) for row in rows)
            coverage[str(y)][k] = {"present_nonnull": int(present), "finite_numeric": int(finite_count)}

    result = {
        "verdict": "PASS_GMN_UNCERTAINTY_SCHEMA_AUDIT_V1",
        "scientific_role": "SCHEMA_ONLY_TARGET_EXCLUDED_GMN_2022_2023_NO_TRUTH",
        "years": list(YEARS),
        "events_by_year": {str(y): len(rows_by_year[y]) for y in YEARS},
        "all_field_names": union_keys,
        "uncertainty_quality_related_field_names": relevant,
        "coverage_counts": coverage,
        "event_values_serialized": False,
        "known_shower_labels_indexed": False,
        "known_shower_label_values_serialized": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "GMN_UNCERTAINTY_SCHEMA_AUDIT_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "events_by_year": result["events_by_year"],
        "relevant_fields": relevant,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
