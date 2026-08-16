#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from scipy.stats import ks_2samp

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
SUBSETS = tuple((d, b) for d in (128, 1024) for b in range(4))
SIZE_BINS = (("4_7", 4, 7), ("8_15", 8, 15), ("16_31", 16, 31), ("32_63", 32, 63))
MIN_SUPPORTED = 30
DIMENSION = 6
ALPHA = math.sqrt(2.0)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + str(eid)).encode()).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def bin_name(size: int) -> str | None:
    for name, lo, hi in SIZE_BINS:
        if lo <= size <= hi:
            return name
    return None


def quantiles(x: np.ndarray) -> dict[str, float | int]:
    req(x.ndim == 1 and len(x) > 0 and np.all(np.isfinite(x)), "invalid summary vector")
    return {"count": int(len(x)), "median": float(np.median(x)), "p90": float(np.quantile(x, .9)), "p99": float(np.quantile(x, .99))}


def ordinary_tree(X: np.ndarray) -> np.ndarray:
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


def robust_tree(X: np.ndarray) -> tuple[np.ndarray, int]:
    n = int(len(X))
    k = int(math.ceil(DIMENSION * math.log(n)))
    _labels, tree = hdbscan.robust_single_linkage(
        X,
        cut=0.0,
        k=k,
        alpha=float(ALPHA),
        gamma=1,
        metric="euclidean",
        algorithm="boruvka_kdtree",
        core_dist_n_jobs=1,
    )
    return np.asarray(tree, dtype=float), k


def tree_stats(tree: np.ndarray, n: int) -> dict[str, Any]:
    req(tree.shape == (n - 1, 4), f"wrong linkage shape {tree.shape}")
    children = np.asarray(np.rint(tree[:, :2]), dtype=np.int64)
    distances = np.asarray(tree[:, 2], dtype=float)
    row_sizes = np.asarray(np.rint(tree[:, 3]), dtype=np.int64)
    req(np.all(np.isfinite(distances)) and np.all(distances >= 0.0), "invalid distances")
    req(np.all(np.diff(distances) >= -1e-12), "nonmonotone linkage distances")

    total = 2 * n - 1
    sizes = np.ones(total, dtype=np.int64)
    parent_distance = np.full(total, np.nan, dtype=float)
    for i, (left, right) in enumerate(children):
        node = n + i
        sizes[node] = sizes[int(left)] + sizes[int(right)]
        req(int(sizes[node]) == int(row_sizes[i]), f"size mismatch node {node}")
        if int(left) >= n:
            parent_distance[int(left)] = distances[i]
        if int(right) >= n:
            parent_distance[int(right)] = distances[i]

    root_i = n - 2
    root_left, root_right = children[root_i]
    root_largest_child_fraction = float(max(sizes[int(root_left)], sizes[int(root_right)]) / n)

    imbalance_num = 0.0
    imbalance_den = 0.0
    arrays: dict[str, dict[str, list[float]]] = {
        name: {"log_persistence": [], "log_formation": [], "formation": []}
        for name, _lo, _hi in SIZE_BINS
    }
    for i in range(n - 2):  # exclude root
        node = n + i
        left, right = children[i]
        size = int(sizes[node])
        if size >= 4:
            a, b = int(sizes[int(left)]), int(sizes[int(right)])
            imbalance_num += abs(a - b)
            imbalance_den += a + b
        name = bin_name(size)
        if name is None:
            continue
        d_form = float(distances[i])
        d_parent = float(parent_distance[node])
        if not (math.isfinite(d_form) and math.isfinite(d_parent) and d_form > 0.0 and d_parent > 0.0):
            continue
        req(d_parent + 1e-12 >= d_form, "parent distance precedes formation")
        lp = max(0.0, math.log(d_parent / d_form))
        lf = math.log(d_form)
        req(math.isfinite(lp) and math.isfinite(lf), "invalid branch coordinate")
        arrays[name]["log_persistence"].append(lp)
        arrays[name]["log_formation"].append(lf)
        arrays[name]["formation"].append(d_form)

    req(imbalance_den > 0.0, "no eligible internal imbalance nodes")
    out_arrays = {name: {key: np.asarray(vals, dtype=float) for key, vals in vectors.items()} for name, vectors in arrays.items()}
    return {
        "root_largest_child_fraction": root_largest_child_fraction,
        "mass_weighted_internal_split_imbalance": float(imbalance_num / imbalance_den),
        "arrays": out_arrays,
        "internal_node_count": n - 1,
    }


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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen support artifact changed")
    parent_runner = load_module(a.parent_runner, "theory_rsl_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")

    qmod = load_module(a.quality_source, "theory_rsl_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-theory-rsl-chain-scale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), "wrong GMN years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), "normalization count changed")
        events.extend(norm)
    req(len(events) == 738682, f"pooled count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived")

    X_full = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids], dtype=np.uint64)

    pooled = {d: {name: {"log_persistence": [], "log_formation": [], "formation": []} for name, _lo, _hi in SIZE_BINS} for d in (128, 1024)}
    subset_rows = []
    root_wins = 0
    imbalance_wins = 0
    ordinary_roots, robust_roots = [], []
    ordinary_imbalances, robust_imbalances = [], []

    for denominator, bucket in SUBSETS:
        idx = selected_indices(hashes, denominator, bucket)
        X = np.asarray(X_full[idx], dtype=float)
        years = years_full[idx]
        req(all(np.any(years == y) for y in YEARS), "subset lost a year")
        n = int(len(X))
        print(f"[theory-rsl] d={denominator} b={bucket} n={n}", flush=True)
        ot = ordinary_tree(X)
        rt, k = robust_tree(X)
        os = tree_stats(ot, n)
        rs = tree_stats(rt, n)

        root_win = rs["root_largest_child_fraction"] < os["root_largest_child_fraction"]
        imb_win = rs["mass_weighted_internal_split_imbalance"] < os["mass_weighted_internal_split_imbalance"]
        root_wins += int(root_win)
        imbalance_wins += int(imb_win)
        ordinary_roots.append(os["root_largest_child_fraction"])
        robust_roots.append(rs["root_largest_child_fraction"])
        ordinary_imbalances.append(os["mass_weighted_internal_split_imbalance"])
        robust_imbalances.append(rs["mass_weighted_internal_split_imbalance"])

        bins = {}
        for name, _lo, _hi in SIZE_BINS:
            arr = rs["arrays"][name]
            if len(arr["log_persistence"]):
                for key in ("log_persistence", "log_formation", "formation"):
                    pooled[denominator][name][key].append(arr[key])
                bins[name] = {
                    "branch_count": int(len(arr["log_persistence"])),
                    "log_persistence": quantiles(arr["log_persistence"]),
                    "formation_distance": quantiles(arr["formation"]),
                }
            else:
                bins[name] = {"branch_count": 0}
        row = {
            "denominator": denominator,
            "bucket": bucket,
            "events_total": n,
            "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
            "rsl_k": k,
            "ordinary_single_link": {
                "root_largest_child_fraction": os["root_largest_child_fraction"],
                "mass_weighted_internal_split_imbalance": os["mass_weighted_internal_split_imbalance"],
            },
            "robust_single_link": {
                "root_largest_child_fraction": rs["root_largest_child_fraction"],
                "mass_weighted_internal_split_imbalance": rs["mass_weighted_internal_split_imbalance"],
                "root_strict_win": bool(root_win),
                "imbalance_strict_win": bool(imb_win),
                "size_bins": bins,
            },
        }
        subset_rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    comparisons = {}
    supported = 0
    scale_wins = 0
    for name, lo, hi in SIZE_BINS:
        merged = {}
        for denominator in (128, 1024):
            merged[denominator] = {}
            for key in ("log_persistence", "log_formation", "formation"):
                pieces = pooled[denominator][name][key]
                merged[denominator][key] = np.concatenate(pieces) if pieces else np.asarray([], dtype=float)
        n128 = len(merged[128]["log_persistence"])
        n1024 = len(merged[1024]["log_persistence"])
        ok = n128 >= MIN_SUPPORTED and n1024 >= MIN_SUPPORTED
        comp: dict[str, Any] = {"size_range": [lo, hi], "branch_count_d128": int(n128), "branch_count_d1024": int(n1024), "supported": bool(ok)}
        if ok:
            supported += 1
            p128, p1024 = merged[128]["log_persistence"], merged[1024]["log_persistence"]
            f128, f1024 = merged[128]["log_formation"], merged[1024]["log_formation"]
            ks_p = float(ks_2samp(p128, p1024).statistic)
            ks_f = float(ks_2samp(f128, f1024).statistic)
            med_p = abs(float(np.median(p128)) - float(np.median(p1024)))
            med_f = abs(float(np.median(f128)) - float(np.median(f1024)))
            p90_p = abs(float(np.quantile(p128, .9)) - float(np.quantile(p1024, .9)))
            p90_f = abs(float(np.quantile(f128, .9)) - float(np.quantile(f1024, .9)))
            win = ks_p < ks_f and med_p < med_f and p90_p < p90_f
            scale_wins += int(win)
            comp.update({
                "KS_persistence": ks_p, "KS_formation": ks_f,
                "MED_persistence": med_p, "MED_formation": med_f,
                "P90_persistence": p90_p, "P90_formation": p90_f,
                "strict_scale_normalization_win": bool(win),
                "pooled_d128_log_persistence": quantiles(p128),
                "pooled_d1024_log_persistence": quantiles(p1024),
                "pooled_d128_formation_distance": quantiles(merged[128]["formation"]),
                "pooled_d1024_formation_distance": quantiles(merged[1024]["formation"]),
            })
        comparisons[name] = comp

    med_or = float(np.median(ordinary_roots)); med_rr = float(np.median(robust_roots))
    med_oi = float(np.median(ordinary_imbalances)); med_ri = float(np.median(robust_imbalances))
    gate = {
        "root_strict_wins_at_least_7_of_8": root_wins >= 7,
        "median_root_fraction_strictly_lower": med_rr < med_or,
        "imbalance_strict_wins_at_least_7_of_8": imbalance_wins >= 7,
        "median_internal_imbalance_strictly_lower": med_ri < med_oi,
        "at_least_three_supported_bins": supported >= 3,
        "every_supported_bin_scale_win": supported >= 3 and scale_wins == supported,
    }
    interpretation = "SUPPORTS_THEORY_RSL_CHAIN_AND_SCALE_HYPOTHESIS" if all(gate.values()) else "REFUTES_THEORY_RSL_CHAIN_AND_SCALE_HYPOTHESIS"

    result = {
        "schema": "ORBITTRACE_THEORY_RSL_CHAIN_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_VIABILITY_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "rsl": {"dimension": DIMENSION, "k_rule": "ceil(6*ln(n))", "alpha": ALPHA, "metric": "euclidean", "algorithm": "boruvka_kdtree"},
        "summary": {
            "root_strict_wins": root_wins,
            "imbalance_strict_wins": imbalance_wins,
            "ordinary_median_root_largest_child_fraction": med_or,
            "robust_median_root_largest_child_fraction": med_rr,
            "ordinary_median_mass_weighted_internal_split_imbalance": med_oi,
            "robust_median_mass_weighted_internal_split_imbalance": med_ri,
            "supported_bin_count": supported,
            "strict_scale_win_count": scale_wins,
            "gate": gate,
        },
        "comparisons": comparisons,
        "subsets": sorted(subset_rows, key=lambda r: (r["denominator"], r["bucket"])),
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
    out = a.output / "THEORY_RSL_CHAIN_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "comparisons": comparisons}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
