#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

EXPECTED_COMMON = {2013: 15988, 2014: 13258}
EXPECTED_POOLED = 29246


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--benchmark-module", type=Path, required=True)
    ap.add_argument("--support-source", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    benchmark = load_module(a.benchmark_module, "internal_mass_prepare_benchmark")
    support = load_module(a.support_source, "internal_mass_prepare_support")
    structural = load_module(a.structural_source, "internal_mass_prepare_structural")
    req(float(support.RADIUS) == 1.0 and int(support.MIN_SUPPORT) == 4, "support constants changed")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")

    pooled, ids_by_year, universe = benchmark.merge_common_rows(a.rows_root)
    req({int(y): int(universe["common_counts"][str(y)]) for y in (2013, 2014)} == EXPECTED_COMMON, "common universe changed")
    req(len(pooled) == EXPECTED_POOLED, "pooled count changed")
    events = [support_event(r) for r in pooled]
    events = sorted(events, key=lambda e: str(e["id"]))
    req(len({e["id"] for e in events}) == EXPECTED_POOLED, "duplicate IDs")

    print("[prepare] support-resolved catalogue", flush=True)
    candidates, summary = support.support_resolved_cut(structural, events)
    req(len(candidates) == 888, f"fixed candidate count changed: {len(candidates)}")
    all_member_ids: set[str] = set()
    for row in candidates:
        ids = set(map(str, row["event_ids"]))
        req(len(ids) == int(row["member_count"]), "candidate membership count mismatch")
        req(all_member_ids.isdisjoint(ids), "candidate memberships overlap")
        all_member_ids.update(ids)

    print("[prepare] exact fixed graph annual-degree diagnostics", flush=True)
    Z = structural.physical_embedding(events)
    raw = cKDTree(Z).query_ball_point(Z, r=1.0, p=2.0, eps=0.0, return_sorted=False)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int16)
    d13 = np.fromiter((sum(years[j] == 2013 for j in row) for row in raw), dtype=np.int64, count=len(raw))
    d14 = np.fromiter((sum(years[j] == 2014 for j in row) for row in raw), dtype=np.int64, count=len(raw))
    u13 = np.unique(d13[d13 > 0])
    u14 = np.unique(d14[d14 > 0])
    degrees = np.asarray([len(r) for r in raw], dtype=np.int64)
    id_to_candidate: dict[str, int] = {}
    for ci, row in enumerate(candidates):
        for eid in row["event_ids"]:
            id_to_candidate[str(eid)] = ci
    ids = [str(e["id"]) for e in events]
    sid = np.asarray([id_to_candidate.get(eid, -1) for eid in ids], dtype=np.int32)
    internal_edges = 0
    cross_edges = 0
    unlabeled_edges = 0
    for i, nbrs in enumerate(raw):
        for j in nbrs:
            if j <= i:
                continue
            if sid[i] >= 0 and sid[i] == sid[j]:
                internal_edges += 1
            elif sid[i] >= 0 or sid[j] >= 0:
                cross_edges += 1
            else:
                unlabeled_edges += 1

    payload = {
        "schema": "ORBITTRACE_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_PRETRUTH_SUPPORT",
        "scientific_role": "ZERO_LABEL_FIXED_CANDIDATE_AND_GRAPH_FEASIBILITY",
        "universe": universe,
        "candidate_count": len(candidates),
        "covered_event_count": len(all_member_ids),
        "candidates": candidates,
        "support_summary": summary,
        "annual_density_diagnostics": {
            "positive_level_count_2013": len(u13),
            "positive_level_count_2014": len(u14),
            "threshold_cell_count": int(len(u13) * len(u14)),
            "max_degree_2013": int(d13.max()),
            "max_degree_2014": int(d14.max()),
            "median_total_degree": float(np.median(degrees)),
            "p90_total_degree": float(np.quantile(degrees, 0.9)),
            "undirected_nonself_edge_count": int((degrees.sum() - len(degrees)) // 2),
            "within_support_candidate_edge_count": int(internal_edges),
            "candidate_boundary_or_cross_edge_count": int(cross_edges),
            "outside_all_candidates_edge_count": int(unlabeled_edges),
        },
        "truth_used": False,
        "shower_labels_accessed": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_PRETRUTH_SUPPORT.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("candidate_count", "covered_event_count", "annual_density_diagnostics")}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
