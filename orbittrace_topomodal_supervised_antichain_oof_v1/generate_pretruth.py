#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

from orbittrace_topomodal_support_resolved_cut_v1 import generate_prelabel as cutbase

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D, FINE_D = 128, 1024
BUCKETS = (0, 1, 2, 3)
RADIUS = 1.0
MIN_SUPPORT = 4
FEATURE_NAMES = (
    "log1p_support",
    "support_fraction",
    "log1p_min_annual_support",
    "annual_balance",
    "min_annual_fraction",
    "active_mode_peak",
    "outside_merge_level",
    "modal_contrast",
    "relative_modal_contrast",
    "mean_member_rho",
    "median_member_rho",
    "is_root",
    "is_leaf",
    "normalized_depth",
    "child_balance",
    "child_min_fraction",
)


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


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + eid).encode()).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def family_id(members: tuple[str, ...]) -> str:
    return hashlib.sha256(("TSAOOF1|" + "|".join(members)).encode()).hexdigest()[:20]


def diagram_sorted(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return np.empty((0, 2), dtype=float)
    req(a.ndim == 2 and a.shape[1] == 2 and np.all(np.isfinite(a)), "invalid persistence diagram")
    return a[np.lexsort((a[:, 1], a[:, 0]))]


def hierarchy_candidates(structural: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    id_to_index = {eid: i for i, eid in enumerate(ids)}
    req(len(id_to_index) == len(ids), "duplicate panel event IDs")

    Z = structural.physical_embedding(ordered)
    neighbors = [
        list(map(int, row))
        for row in cKDTree(Z).query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    ]
    req(len(neighbors) == len(ids), "radius graph row count changed")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(row.count(i) == 1 and all(0 <= j < len(ids) for j in row), f"invalid radius graph row {i}")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")
    rho = np.asarray([len(row) for row in neighbors], dtype=np.float64) / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid radius-count density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    leaf_count = int(model.n_leaves_)
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(
        leaf_labels.shape == (len(ids),)
        and leaf_count >= 1
        and int(leaf_labels.min()) >= 0
        and int(leaf_labels.max()) + 1 == leaf_count,
        "invalid ToMATo leaves",
    )
    req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic changed")

    diagram = np.asarray(model.diagram_, dtype=float)
    diagram_ref = diagram_sorted(diagram)
    persistence = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0)
    req(
        len(persistence) == len(children) == len(diagram_ref) and np.all(persistence >= -1e-15),
        "invalid finite persistence",
    )
    persistence = np.maximum(persistence, 0.0)

    node_count = leaf_count + len(children)
    members: list[frozenset[str] | None] = [None] * node_count
    parent = np.full(node_count, -1, dtype=np.int64)
    kids: list[tuple[int, int] | None] = [None] * node_count
    active_peak = np.full(node_count, np.nan, dtype=np.float64)
    active_key: list[str | None] = [None] * node_count
    merge_level = np.full(node_count, np.nan, dtype=np.float64)

    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty leaf {leaf}")
        members[leaf] = frozenset(ids[int(i)] for i in ix)
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        req(bool(keys), f"no active-mode key for leaf {leaf}")
        active_peak[leaf] = peak
        active_key[leaf] = keys[0]

    reconstructed: list[list[float]] = []
    dying: set[int] = set()
    for offset, pair in enumerate(children):
        node = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid hierarchy children at {node}")
        req(parent[a] == -1 and parent[b] == -1, "hierarchy node has multiple parents")
        ma, mb = members[a], members[b]
        req(ma is not None and mb is not None and ma.isdisjoint(mb), "invalid child memberships")
        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        if pa > pb or (pa == pb and ka < kb):
            winner, loser = a, b
        else:
            winner, loser = b, a
        members[node] = frozenset(ma.union(mb))
        kids[node] = (a, b)
        parent[a] = node
        parent[b] = node
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])
        req(loser not in dying, "active mode died twice")
        dying.add(loser)
        death = float(active_peak[loser]) - float(persistence[offset])
        merge_level[node] = death
        reconstructed.append([float(active_peak[loser]), death])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "ToMATo root count changed")
    req(sum(len(members[int(r)]) for r in roots if members[int(r)] is not None) == len(ids), "roots do not partition panel")

    reconstructed_diagram = diagram_sorted(np.asarray(reconstructed, dtype=float))
    req(reconstructed_diagram.shape == diagram_ref.shape, "persistence reconstruction shape changed")
    max_diagram_error = float(np.max(np.abs(reconstructed_diagram - diagram_ref))) if reconstructed_diagram.size else 0.0
    req(max_diagram_error <= 1e-12, f"persistence reconstruction mismatch {max_diagram_error}")

    full_candidates, full_summary = structural.topomodal_candidates(ordered)

    depths = np.zeros(node_count, dtype=np.int64)
    for node in range(node_count):
        p = int(parent[node])
        depth = 0
        seen: set[int] = set()
        while p >= 0:
            req(p not in seen, "hierarchy cycle")
            seen.add(p)
            depth += 1
            p = int(parent[p])
        depths[node] = depth
    max_depth = int(np.max(depths)) if len(depths) else 0

    rows: list[dict[str, Any]] = []
    for node in range(node_count):
        m = members[node]
        req(m is not None, f"missing membership {node}")
        if len(m) < MIN_SUPPORT:
            continue
        tup = tuple(sorted(m))
        ix = np.asarray([id_to_index[eid] for eid in tup], dtype=np.int64)
        n = len(tup)
        n22 = int(np.sum(years[ix] == 2022))
        n23 = int(np.sum(years[ix] == 2023))
        req(n22 + n23 == n, "annual support does not sum to node support")

        p = int(parent[node])
        outside = 0.0 if p < 0 else float(merge_level[p])
        req(math.isfinite(outside), f"missing outside merge level node={node}")
        peak = float(active_peak[node])
        contrast = max(0.0, peak - outside)
        req(math.isfinite(peak) and math.isfinite(contrast) and contrast >= 0.0, "invalid modal quantities")

        ch = kids[node]
        if ch is None:
            child_balance = 0.0
            child_min_fraction = 0.0
            eligible_children: list[int] = []
            is_leaf = True
        else:
            a, b = ch
            sa, sb = len(members[a]), len(members[b])
            lo, hi = min(sa, sb), max(sa, sb)
            child_balance = float(lo / hi) if hi > 0 else 0.0
            child_min_fraction = float(lo / n)
            eligible_children = [int(c) for c in (a, b) if len(members[c]) >= MIN_SUPPORT]
            is_leaf = False

        hi_year = max(n22, n23)
        lo_year = min(n22, n23)
        features = [
            math.log1p(n),
            float(n / len(ids)),
            math.log1p(lo_year),
            float(lo_year / hi_year) if hi_year > 0 else 0.0,
            float(lo_year / n),
            peak,
            outside,
            contrast,
            float(contrast / max(peak, 1e-15)),
            float(np.mean(rho[ix])),
            float(np.median(rho[ix])),
            float(p < 0),
            float(is_leaf),
            float(depths[node] / max(max_depth, 1)),
            child_balance,
            child_min_fraction,
        ]
        req(len(features) == len(FEATURE_NAMES) and all(math.isfinite(float(x)) for x in features), "invalid feature row")
        rows.append(
            {
                "family_id": family_id(tup),
                "family_hash": structural.member_hash(m),
                "node": int(node),
                "parent_node": p,
                "eligible_child_nodes": eligible_children,
                "event_ids": list(tup),
                "member_count": n,
                "annual_support": {"2022": n22, "2023": n23},
                "active_mode_peak": peak,
                "outside_merge_level": outside,
                "modal_contrast": contrast,
                "is_root": bool(p < 0),
                "is_leaf": bool(is_leaf),
                "depth": int(depths[node]),
                "features": [float(x) for x in features],
            }
        )

    req(len(rows) == int(full_summary["candidate_count"]) == len(full_candidates), "eligible hierarchy candidate count changed")
    ours_summary = sorted(
        [
            {
                "family_hash": str(r["family_hash"]),
                "member_count": int(r["member_count"]),
                "first_node": int(r["node"]),
                "is_root": bool(r["is_root"]),
            }
            for r in rows
        ],
        key=lambda r: (-r["member_count"], r["family_hash"]),
    )
    req(ours_summary == full_summary["candidate_rows"], "complete #1284 hierarchy identity mismatch")
    req(len({r["node"] for r in rows}) == len(rows), "duplicate eligible node")
    req(len({tuple(r["event_ids"]) for r in rows}) == len(rows), "duplicate eligible membership")

    return rows, {
        "candidate_count": len(rows),
        "candidate_rows": ours_summary,
        "root_count": len(roots),
        "max_depth": max_depth,
        "median_radius_degree": float(np.median(rho * len(ids))),
        "p90_radius_degree": float(np.quantile(rho * len(ids), 0.9)),
        "diagram_reconstruction_max_abs_error": max_diagram_error,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "structural-runner",
        "structural-result-json",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 support artifact changed")
    req(sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "#1284 structural result changed")
    sr = json.loads(a.structural_result_json.read_text())
    req(sr["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 structural prerequisite absent")
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in sr["fits"]}
    req(set(expected) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "structural panel set changed")

    structural = load_module(a.structural_runner, "tsa_structural")
    parent_runner = load_module(a.parent_runner, "tsa_parent")
    req(tuple(structural.BLIND) == BLIND and float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")
    req(tuple(parent_runner.BLIND) == BLIND and int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent constants changed")

    q = load_module(a.quality_source, "tsa_gmn_runtime")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-supervised-antichain-oof-v1-pretruth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_unused, sources = support.parse_catalogue(base)
    del hidden_unused
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source set changed")

    events: list[dict[str, Any]] = []
    for y in YEARS:
        events.extend(parent_runner.normalize_event(row, y) for row in list(scan[y]))
    req(len(events) == 738682 and len({str(e["id"]) for e in events}) == 738682, "pooled target-excluded event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")

    Xfull = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    for d in (COARSE_D, FINE_D):
        for b in BUCKETS:
            ix = selected_indices(hashes, d, b)
            sub = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            print(f"[tsa-pretruth] d={d} b={b} n={len(ids)}", flush=True)

            candidates, hierarchy_summary = hierarchy_candidates(structural, sub)
            recurrent, recurrent_summary = cutbase.recurrent_ranked(parent_runner, X, yrs, ids)
            ex = expected[(d, b)]
            req(ex["topomodal"]["candidate_rows"] == hierarchy_summary["candidate_rows"] and int(ex["topomodal"]["candidate_count"]) == len(candidates), f"#1284 hierarchy mismatch d={d} b={b}")
            req(ex["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"] and int(ex["recurrent_eom"]["candidate_count"]) == len(recurrent), f"recurrent comparator mismatch d={d} b={b}")

            subsets.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(yrs == y)) for y in YEARS},
                    "event_universe_sha256": universe_hash(ids),
                    "hierarchy_summary": hierarchy_summary,
                    "candidates": candidates,
                    "recurrent_summary": recurrent_summary,
                    "recurrent_candidates": recurrent,
                }
            )

    pre = {
        "schema": "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH",
        "scientific_role": "PRETRUTH_FEATURE_AND_MEMBERSHIP_FREEZE",
        "structural_source_run_id": 31955621864,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "feature_names": list(FEATURE_NAMES),
        "feature_dimension": len(FEATURE_NAMES),
        "configuration": {
            "candidate_universe": "all_exact_1284_topomodal_hierarchy_nodes_support_ge_4",
            "feature_map": "fixed_16d_topomodal_native_v1",
            "oof_group_salt": "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1|",
            "min_support": MIN_SUPPORT,
        },
        "subsets": subsets,
        "protocol_sha256": sha256(a.protocol),
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
    out = a.output / "TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    digest = sha256(out)
    print(json.dumps({"pretruth_sha256": digest, "candidate_counts": [{"d": s["denominator"], "b": s["bucket"], "n": len(s["candidates"])} for s in subsets]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
