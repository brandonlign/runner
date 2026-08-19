#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

EXPECTED_COMMON = {2013: 15988, 2014: 13258}
EXPECTED_POOLED = 29246
BASELINE_SUPPORT_SHA = "19828089363280d37aed17aacc9561e60c185abda61b2b7c0dead0226d2740b9"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def support_event(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(row["id"]),
        "year": int(row["year"]),
        "sol": float(row["sol"]),
        "lon": float(row["sun_lon"]),
        "lat": float(row["ecl_lat"]),
        "vg": float(row["vg"]),
    }
    req(all(math.isfinite(float(out[k])) for k in ("sol", "lon", "lat", "vg")), f"nonfinite row {out['id']}")
    req(out["vg"] > 0.0, f"nonpositive vg {out['id']}")
    return out


def size_summary(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    vals = sorted(int(r["member_count"]) for r in rows)
    req(bool(vals), "empty candidate catalogue")
    p90 = float(np.quantile(np.asarray(vals, dtype=float), 0.9))
    return {
        "candidate_count": len(vals),
        "mean_member_count": float(mean(vals)),
        "median_member_count": float(np.median(vals)),
        "p90_member_count": p90,
        "max_member_count": max(vals),
        "min_member_count": min(vals),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--benchmark-module", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--refined-cut-source", type=Path, required=True)
    ap.add_argument("--baseline-support", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.baseline_support) == BASELINE_SUPPORT_SHA, "baseline support artifact changed")
    benchmark = load_module(a.benchmark_module, "spc_sonotaco_benchmark")
    structural = load_module(a.structural_source, "spc_sonotaco_structural")
    refined = load_module(a.refined_cut_source, "spc_sonotaco_refined")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")
    req(float(refined.RADIUS) == 1.0 and int(refined.MIN_SUPPORT) == 4, "refined constants changed")

    pooled, ids_by_year, universe = benchmark.merge_common_rows(a.rows_root)
    req({int(y): int(universe["common_counts"][str(y)]) for y in (2013, 2014)} == EXPECTED_COMMON, "common universe changed")
    req(len(pooled) == EXPECTED_POOLED, "pooled count changed")
    events = sorted((support_event(r) for r in pooled), key=lambda e: str(e["id"]))
    req(len(events) == EXPECTED_POOLED and len({e["id"] for e in events}) == EXPECTED_POOLED, "event universe invalid")
    req(sum(e["year"] == 2013 for e in events) == EXPECTED_COMMON[2013], "2013 count")
    req(sum(e["year"] == 2014 for e in events) == EXPECTED_COMMON[2014], "2014 count")

    candidates, cut_summary = refined.support_pruned_cut(structural, events)
    seen: set[str] = set()
    for row in candidates:
        ids = set(map(str, row["event_ids"]))
        req(len(ids) == int(row["member_count"]) >= 4, "candidate membership count")
        req(seen.isdisjoint(ids), "candidate overlap")
        seen.update(ids)
    req(bool(candidates) and cut_summary["pairwise_disjoint"] is True and cut_summary["selected_plus_noise_partition"] is True, "cut invariants")

    baseline = json.loads(a.baseline_support.read_text())
    req(baseline.get("truth_used") is False and baseline.get("shower_labels_accessed") is False, "baseline firewall")
    req(int(baseline["candidate_count"]) == 888, "baseline candidate count")
    base_rows = list(baseline["candidates"])
    base_size = size_summary(base_rows)
    ref_size = size_summary(candidates)

    # These are label-free diagnostics only. No truth or target information appears here.
    payload = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_PRETRUTH",
        "scientific_role": "ZERO_LABEL_SUPPORT_PRUNED_SONOTACO_COMMON_UNIVERSE_PRETRUTH",
        "universe": universe,
        "candidate_count": len(candidates),
        "covered_event_count": len(seen),
        "candidates": candidates,
        "cut_summary": cut_summary,
        "size_summary": {
            "baseline_support_resolved": base_size,
            "support_pruned": ref_size,
            "mean_member_count_delta": ref_size["mean_member_count"] - base_size["mean_member_count"],
            "p90_member_count_delta": ref_size["p90_member_count"] - base_size["p90_member_count"],
            "max_member_count_delta": ref_size["max_member_count"] - base_size["max_member_count"],
        },
        "baseline_support_sha256": BASELINE_SUPPORT_SHA,
        "configuration": {
            "radius": 1.0,
            "minimum_support": 4,
            "cut_rule": "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport",
            "new_tuned_parameters": [],
        },
        "truth_used": False,
        "shower_labels_accessed": False,
        "orbittrace_member_ids_accessed": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_PRETRUTH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": "SEALED_AWAITING_SONOTACO_TRUTH",
        "candidate_count": payload["candidate_count"],
        "covered_event_count": payload["covered_event_count"],
        "discarded_subsupport_event_count": cut_summary["discarded_subsupport_event_count"],
        "size_summary": payload["size_summary"],
        "sha256": sha(out),
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
