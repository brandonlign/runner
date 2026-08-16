#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from sklearn.cluster import AgglomerativeClustering

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
SUBSETS = tuple((d, b) for d in (128, 1024) for b in range(4))
SIZE_BINS = (("4_7", 4, 7), ("8_15", 8, 15), ("16_31", 16, 31), ("32_63", 32, 63))


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash_u64(eid: str) -> int:
    digest = hashlib.sha256((SALT + str(eid)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def sklearn_tree(X: np.ndarray) -> np.ndarray:
    n = len(X)
    m = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.0,
        metric="euclidean",
        linkage="single",
        compute_distances=True,
        compute_full_tree=True,
    ).fit(X)
    sizes = np.ones(2 * n - 1, dtype=np.int64)
    rows = np.empty((n - 1, 4), dtype=float)
    for i, (left, right) in enumerate(m.children_):
        node = n + i
        sizes[node] = sizes[int(left)] + sizes[int(right)]
        rows[i] = (int(left), int(right), float(m.distances_[i]), int(sizes[node]))
    return rows


def hdbscan_tree(X: np.ndarray) -> np.ndarray:
    # min_samples includes the point itself; at 1, core distance is zero and
    # mutual reachability collapses to ordinary Euclidean distance.
    model = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        algorithm="boruvka_kdtree",
        approx_min_span_tree=False,
        gen_min_span_tree=True,
        core_dist_n_jobs=1,
        prediction_data=False,
    ).fit(X)
    return np.asarray(model.single_linkage_tree_.to_numpy(), dtype=float)


def bin_name(size: int) -> str | None:
    for name, lo, hi in SIZE_BINS:
        if lo <= size <= hi:
            return name
    return None


def membership_hashes(tree: np.ndarray, event_ids: list[str]) -> dict[str, list[str]]:
    n = len(event_ids)
    req(tree.shape == (n - 1, 4), f"wrong linkage-tree shape {tree.shape}")
    leaves: list[tuple[int, ...] | None] = [(i,) for i in range(n)] + [None] * (n - 1)
    out: dict[str, list[str]] = {name: [] for name, _lo, _hi in SIZE_BINS}
    for i, row in enumerate(tree):
        left, right, _distance, size_f = row
        left_i, right_i, size = int(left), int(right), int(round(size_f))
        node = n + i
        if size <= 63:
            a, b = leaves[left_i], leaves[right_i]
            req(a is not None and b is not None, "small branch descended from discarded large branch")
            members = tuple(sorted((*a, *b)))
            req(len(members) == size, "linkage size mismatch")
            leaves[node] = members
            name = bin_name(size)
            if name is not None:
                ids = sorted(event_ids[j] for j in members)
                out[name].append(hashlib.sha256("|".join(ids).encode()).hexdigest())
        else:
            leaves[node] = None
    return {k: sorted(v) for k, v in out.items()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent_runner = load_module(a.parent_runner, "singlelink_equiv_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent contract changed")

    qmod = load_module(a.quality_source, "singlelink_equiv_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-singlelink-hdbscan-equivalence-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), "wrong GMN years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        events.extend(parent_runner.normalize_event(row, year) for row in raw)
    req(len(events) == 738682, f"pooled event count changed: {len(events)}")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")
    X_full = parent_runner.geo_matrix(events)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    rows = []
    for d, b in SUBSETS:
        idx = selected_indices(hashes, d, b)
        X = np.asarray(X_full[idx], dtype=float)
        ids = [ids_full[int(i)] for i in idx]
        print(f"[singlelink-equivalence] d={d} b={b} n={len(idx)}", flush=True)
        sk = sklearn_tree(X)
        hd = hdbscan_tree(X)
        req(sk.shape == hd.shape, f"shape mismatch d={d} b={b}: {sk.shape} vs {hd.shape}")
        sk_dist = np.sort(sk[:, 2])
        hd_dist = np.sort(hd[:, 2])
        max_abs = float(np.max(np.abs(sk_dist - hd_dist)))
        distances_equal = bool(np.allclose(sk_dist, hd_dist, rtol=1e-10, atol=1e-12))
        sk_hash = membership_hashes(sk, ids)
        hd_hash = membership_hashes(hd, ids)
        bin_equal = {name: sk_hash[name] == hd_hash[name] for name, _lo, _hi in SIZE_BINS}
        exact_memberships = bool(all(bin_equal.values()))
        row = {
            "denominator": d,
            "bucket": b,
            "events_total": int(len(idx)),
            "distance_multiset_equal": distances_equal,
            "max_abs_distance_difference": max_abs,
            "membership_hashes_equal_by_bin": bin_equal,
            "all_4_63_memberships_equal": exact_memberships,
            "sklearn_branch_counts": {k: len(v) for k, v in sk_hash.items()},
            "hdbscan_branch_counts": {k: len(v) for k, v in hd_hash.items()},
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    exact = all(r["distance_multiset_equal"] and r["all_4_63_memberships_equal"] for r in rows)
    verdict = "PASS_SCALABLE_SINGLELINK_EQUIVALENCE" if exact else "FAIL_SCALABLE_SINGLELINK_EQUIVALENCE"
    result = {
        "schema": "ORBITTRACE_SINGLELINK_HDBSCAN_EQUIVALENCE_V1",
        "role": "IMPLEMENTATION_EQUIVALENCE_ONLY",
        "verdict": verdict,
        "reference": "sklearn AgglomerativeClustering single/euclidean",
        "scalable": {
            "library": "hdbscan 0.8.43",
            "min_samples": 1,
            "min_cluster_size": 2,
            "algorithm": "boruvka_kdtree",
            "approx_min_span_tree": False,
        },
        "subsets": rows,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "external_scientific_access": False,
    }
    out = a.output / "SINGLELINK_HDBSCAN_EQUIVALENCE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
