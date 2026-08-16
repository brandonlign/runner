#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BUCKETS = (0, 1, 2, 3)
RADIUS = 1.0
MIN_SUPPORT = 4
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def int_hash(x: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(x, dtype="<i8").tobytes(order="C")).hexdigest()


def float_hash(x: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(x, dtype="<f8").tobytes(order="C")).hexdigest()


def threshold_states(values: np.ndarray) -> list[tuple[int, int]]:
    vals = np.asarray(values, dtype=np.int64)
    req(vals.ndim == 1 and len(vals) > 0 and np.all(vals >= 0), "invalid threshold counts")
    levels = sorted(set(map(int, vals)) | {0}, reverse=True)
    states: list[tuple[int, int]] = []
    for i, level in enumerate(levels):
        if i + 1 < len(levels):
            width = int(level - levels[i + 1])
        else:
            req(level == 0, "final threshold state is not zero")
            width = 1
        req(width >= 1, "nonpositive threshold-state width")
        states.append((int(level), width))
    req(sum(w for _, w in states) == int(np.max(vals)) + 1, "threshold widths do not cover exact integer lattice")
    return states


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = np.full(n, -1, dtype=np.int64)
        self.size = np.zeros(n, dtype=np.int64)
        self.members: dict[int, set[int]] = {}
        self.roots: set[int] = set()

    def active(self, i: int) -> bool:
        return int(self.parent[i]) >= 0

    def find(self, i: int) -> int:
        p = int(self.parent[i])
        req(p >= 0, "find on inactive vertex")
        while p != int(self.parent[p]):
            self.parent[p] = self.parent[int(self.parent[p])]
            p = int(self.parent[p])
        root = p
        p = i
        while p != root:
            nxt = int(self.parent[p])
            self.parent[p] = root
            p = nxt
        return root

    def activate(self, i: int) -> None:
        req(not self.active(i), "double activation")
        self.parent[i] = i
        self.size[i] = 1
        self.members[i] = {i}
        self.roots.add(i)

    def union(self, a: int, b: int) -> int:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if int(self.size[ra]) < int(self.size[rb]) or (int(self.size[ra]) == int(self.size[rb]) and ra > rb):
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.members[ra].update(self.members.pop(rb))
        self.roots.remove(rb)
        return ra


def enumerate_support_sweep(
    ids: list[str], adjacency: list[list[int]], d22: np.ndarray, d23: np.ndarray
) -> tuple[dict[tuple[str, ...], int], dict[str, Any]]:
    n = len(ids)
    req(len(adjacency) == n and d22.shape == (n,) and d23.shape == (n,), "enumeration shape mismatch")
    a_states = threshold_states(d22)
    b_states = threshold_states(d23)
    support: dict[tuple[str, ...], int] = defaultdict(int)
    weighted_component_observations = 0
    raw_component_observations = 0

    # Exact acceleration: topology is constant between observed integer count
    # values; each state carries the number of exact integer thresholds it
    # represents. Every integer lattice cell is still counted exactly once.
    for a_level, a_width in a_states:
        eligible = d22 >= int(a_level)
        buckets: dict[int, list[int]] = defaultdict(list)
        for i in np.flatnonzero(eligible):
            buckets[int(d23[int(i)])].append(int(i))
        dsu = DSU(n)
        for b_level, b_width in b_states:
            for v in buckets.get(int(b_level), []):
                dsu.activate(v)
                for u in adjacency[v]:
                    if dsu.active(int(u)):
                        dsu.union(v, int(u))
            cell_weight = int(a_width * b_width)
            roots = sorted(dsu.roots)
            raw_component_observations += len(roots)
            weighted_component_observations += cell_weight * len(roots)
            for root in roots:
                if int(dsu.size[root]) < MIN_SUPPORT:
                    continue
                members_ix = sorted(dsu.members[root])
                members = tuple(ids[i] for i in members_ix)
                support[members] += cell_weight

    exact_cells = (int(np.max(d22)) + 1) * (int(np.max(d23)) + 1)
    req(sum(w for _, w in a_states) * sum(w for _, w in b_states) == exact_cells, "exact threshold lattice cell count mismatch")
    req(all(v >= 1 for v in support.values()), "nonpositive component support")
    return dict(support), {
        "a_state_count": len(a_states),
        "b_state_count": len(b_states),
        "a_max_count": int(np.max(d22)),
        "b_max_count": int(np.max(d23)),
        "exact_threshold_cell_count": exact_cells,
        "raw_state_pair_count": len(a_states) * len(b_states),
        "weighted_component_observations": int(weighted_component_observations),
        "raw_component_observations": int(raw_component_observations),
    }


def enumerate_support_bruteforce(
    ids: list[str], adjacency: list[list[int]], d22: np.ndarray, d23: np.ndarray
) -> dict[tuple[str, ...], int]:
    """Second exact implementation used only for the smallest-panel audit."""
    n = len(ids)
    out: dict[tuple[str, ...], int] = defaultdict(int)
    for a in range(int(np.max(d22)) + 1):
        for b in range(int(np.max(d23)) + 1):
            active = (d22 >= a) & (d23 >= b)
            seen = np.zeros(n, dtype=bool)
            for start in np.flatnonzero(active):
                s = int(start)
                if seen[s]:
                    continue
                stack = [s]
                seen[s] = True
                comp: list[int] = []
                while stack:
                    v = stack.pop()
                    comp.append(v)
                    for u in adjacency[v]:
                        uu = int(u)
                        if active[uu] and not seen[uu]:
                            seen[uu] = True
                            stack.append(uu)
                if len(comp) >= MIN_SUPPORT:
                    out[tuple(ids[i] for i in sorted(comp))] += 1
    return dict(out)


def build_candidates(intrinsic: Any, events: list[dict[str, Any]], do_bruteforce: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "both years required")
    totals = {y: int(np.sum(years == y)) for y in YEARS}
    req(all(totals[y] > 0 for y in YEARS), "empty annual subset")

    Z = intrinsic.physical_embedding(ordered)
    raw = cKDTree(Z).query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    adjacency = [list(map(int, row)) for row in raw]
    req(len(adjacency) == len(ids), "radius graph row count")
    aset = [set(row) for row in adjacency]
    for i, row in enumerate(adjacency):
        req(row.count(i) == 1, f"self-neighbor multiplicity at {i}")
        req(all(0 <= j < len(ids) for j in row), "radius index")
    req(all(i in aset[j] for i, row in enumerate(adjacency) for j in row), "radius graph asymmetry")

    d22 = np.fromiter((sum(1 for j in row if years[j] == 2022) for row in adjacency), dtype=np.int64, count=len(ids))
    d23 = np.fromiter((sum(1 for j in row if years[j] == 2023) for row in adjacency), dtype=np.int64, count=len(ids))
    req(np.all(d22 >= 0) and np.all(d23 >= 0), "negative annual count")
    req(np.array_equal(d22 + d23, np.asarray([len(row) for row in adjacency], dtype=np.int64)), "annual counts do not sum to radius degree")
    rho22 = d22.astype(float) / float(totals[2022])
    rho23 = d23.astype(float) / float(totals[2023])
    req(np.all(np.isfinite(rho22)) and np.all(np.isfinite(rho23)) and np.all(rho22 >= 0) and np.all(rho23 >= 0), "invalid annual density coordinates")

    support, enum_summary = enumerate_support_sweep(ids, adjacency, d22, d23)
    swapped, swapped_summary = enumerate_support_sweep(ids, adjacency, d23, d22)
    req(support == swapped, "year-axis transpose changed bivariate component support")
    req(enum_summary["exact_threshold_cell_count"] == swapped_summary["exact_threshold_cell_count"], "transpose lattice cell count mismatch")

    brute_ok: bool | None = None
    if do_bruteforce:
        brute = enumerate_support_bruteforce(ids, adjacency, d22, d23)
        req(brute == support, "independent brute-force component support mismatch")
        brute_ok = True

    rows: list[dict[str, Any]] = []
    denom = float(totals[2022] * totals[2023])
    for members, cells in support.items():
        req(len(members) >= MIN_SUPPORT and cells >= 1, "invalid retained membership")
        rows.append({
            "family_id": intrinsic.family_id("BDCP1", members),
            "family_hash": intrinsic.membership_hash(members),
            "event_ids": list(members),
            "member_count": len(members),
            "support_cells": int(cells),
            "support_area": float(cells / denom),
        })
    rows.sort(key=lambda r: (-float(r["support_area"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = int(rank)
    req([int(r["rank"]) for r in rows] == list(range(1, len(rows) + 1)), "rank discontinuity")
    req(len({str(r["family_id"]) for r in rows}) == len(rows), "family ID collision")

    edge_count = int((sum(len(row) for row in adjacency) - len(ids)) // 2)
    return rows, {
        "candidate_count": len(rows),
        "annual_event_totals": {str(y): totals[y] for y in YEARS},
        "d22_sha256": int_hash(d22),
        "d23_sha256": int_hash(d23),
        "rho22_sha256": float_hash(rho22),
        "rho23_sha256": float_hash(rho23),
        "graph_edge_count_excluding_self": edge_count,
        "median_radius_degree": float(np.median([len(r) for r in adjacency])),
        "p90_radius_degree": float(np.quantile([len(r) for r in adjacency], 0.90)),
        "year_axis_transpose_exact": True,
        "independent_bruteforce_exact": brute_ok,
        **enum_summary,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "intrinsic-runner", "parent-runner", "quality-source", "support-source-parts",
        "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "structural-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    intrinsic = load_module(a.intrinsic_runner, "bdcp_intrinsic")
    req(intrinsic.sha256(a.quality_source) == QUALITY_SHA256, "GMN utility hash")
    req(intrinsic.sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 result hash")
    req(intrinsic.sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "#1284 structural result hash")
    req(tuple(intrinsic.YEARS) == YEARS and tuple(intrinsic.BLIND) == BLIND, "intrinsic constants")
    req(float(intrinsic.RADIUS) == RADIUS and int(intrinsic.MIN_SUPPORT) == MIN_SUPPORT, "#1284 radius/support changed")

    structural = json.loads(a.structural_result_json.read_text())
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "#1284 panel set")

    parent = load_module(a.parent_runner, "bdcp_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support")

    q = load_module(a.quality_source, "bdcp_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support_module = runtime.load_support_module(a.support_source_parts)
    support_module.YEARS = YEARS
    support_module.MONTH_KEYS = MONTH_KEYS
    support_module.CORPUS = "orbittrace-bivariate-density-component-persistence-v1-target-excluded"
    support_module.RANKING_VARIANTS = ("persistence",)
    req((float(support_module.BLIND_LOW), float(support_module.BLIND_HIGH)) == BLIND, "firewall")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base_source, _scorer = support_module.load_sources(a)
    scan, _cal, hidden_unused, sources = support_module.parse_catalogue(base_source)
    del hidden_unused
    req(sorted(scan) == list(YEARS), "wrong years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == 738682, f"pooled count changed {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived")

    Xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([intrinsic.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)
    subset_specs: list[tuple[int, int, np.ndarray, list[dict[str, Any]], np.ndarray, np.ndarray, list[str]]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            ii = intrinsic.selected_indices(hashes, denominator, bucket)
            subset_specs.append((denominator, bucket, ii, [events[int(i)] for i in ii], np.asarray(Xfull[ii], dtype=float), np.asarray(years_full[ii], dtype=np.int64), [ids_full[int(i)] for i in ii]))
    smallest_key = min(((len(s[-1]), s[0], s[1]) for s in subset_specs))[1:]

    subsets: list[dict[str, Any]] = []
    shortage = False
    for denominator, bucket, ii, sub_events, X, years, ids in subset_specs:
        print(f"[bdcp-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)
        successor, successor_summary = build_candidates(intrinsic, sub_events, (denominator, bucket) == smallest_key)
        recurrent, recurrent_summary = intrinsic.recurrent_ranked(parent, X, years, ids)
        ex = expected[(denominator, bucket)]
        req(int(ex["events_total"]) == len(ids), "#1284 event count mismatch")
        req({str(k): int(v) for k, v in ex["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, "annual count mismatch")
        req(ex["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], "parent membership mismatch")
        req(int(ex["recurrent_eom"]["candidate_count"]) == len(recurrent), "parent count mismatch")
        sufficient = len(successor) >= len(recurrent)
        shortage = shortage or not sufficient
        subsets.append({
            "denominator": denominator, "bucket": bucket,
            "events_total": len(ids),
            "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
            "event_universe_sha256": intrinsic.universe_hash(ids),
            "equal_budget_k": len(recurrent),
            "candidate_budget_sufficient": sufficient,
            "successor_summary": successor_summary,
            "recurrent_summary": recurrent_summary,
            "successor_candidates": successor,
            "recurrent_candidates": recurrent,
        })

    pre = {
        "schema": "ORBITTRACE_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL",
        "scientific_role": "PRELABEL_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "intrinsic_source_commit": "312b1b718ae105813de242355142a74e7d377d65",
        "intrinsic_source_blob": INTRINSIC_SOURCE_BLOB,
        "configuration": {
            "graph": "exact_radius_1_physical_embedding_1284",
            "annual_coordinates": "radius_year_counts_over_annual_totals_no_scalarization",
            "filtration": "all_integer_count_threshold_pairs",
            "candidate": "every_exact_connected_component_membership_support_ge_4",
            "score": "support_cells_over_N22_times_N23",
            "ranking": "support_area_desc_then_family_hash_asc",
        },
        "candidate_budget_shortage_any_panel": shortage,
        "subsets": subsets,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "prelabel_sha256": intrinsic.sha256(out),
        "candidate_budget_shortage_any_panel": shortage,
        "smallest_panel_bruteforce_key": list(smallest_key),
        "subsets": [{"d":s["denominator"],"b":s["bucket"],"successor":len(s["successor_candidates"]),"recurrent":len(s["recurrent_candidates"]),"cells":s["successor_summary"]["exact_threshold_cell_count"],"states":s["successor_summary"]["raw_state_pair_count"]} for s in subsets],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
