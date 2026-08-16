#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import ks_2samp
from sklearn.cluster import AgglomerativeClustering

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
SUBSETS = tuple((d, b) for d in (128, 1024) for b in range(4))
SIZE_BINS = (
    ("4_7", 4, 7),
    ("8_15", 8, 15),
    ("16_31", 16, 31),
    ("32_63", 32, 63),
)
MIN_SUPPORTED = 30


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


def bin_name(size: int) -> str | None:
    for name, lo, hi in SIZE_BINS:
        if lo <= size <= hi:
            return name
    return None


def quantiles(values: np.ndarray) -> dict[str, float | int]:
    req(values.ndim == 1 and len(values) > 0, "cannot summarize empty vector")
    req(np.all(np.isfinite(values)), "nonfinite summary vector")
    return {
        "count": int(len(values)),
        "median": float(np.quantile(values, 0.50)),
        "p90": float(np.quantile(values, 0.90)),
        "p99": float(np.quantile(values, 0.99)),
    }


def tree_statistics(X: np.ndarray) -> tuple[dict[str, dict[str, np.ndarray]], int]:
    n = int(len(X))
    req(n >= 64, f"unexpectedly small subset: {n}")
    model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.0,
        metric="euclidean",
        linkage="single",
        compute_distances=True,
        compute_full_tree=True,
    ).fit(X)
    children = np.asarray(model.children_, dtype=np.int64)
    distances = np.asarray(model.distances_, dtype=float)
    req(children.shape == (n - 1, 2), f"unexpected children shape {children.shape}")
    req(distances.shape == (n - 1,), f"unexpected distance shape {distances.shape}")
    req(np.all(np.isfinite(distances)) and np.all(distances >= 0.0), "invalid linkage distances")
    req(np.all(np.diff(distances) >= -1e-12), "single-linkage merge distances are not monotone")

    total_nodes = 2 * n - 1
    sizes = np.ones(total_nodes, dtype=np.int64)
    parent_distance = np.full(total_nodes, np.nan, dtype=float)
    for i, (left, right) in enumerate(children):
        node = n + i
        sizes[node] = sizes[int(left)] + sizes[int(right)]
        if int(left) >= n:
            parent_distance[int(left)] = distances[i]
        if int(right) >= n:
            parent_distance[int(right)] = distances[i]

    by_bin: dict[str, dict[str, list[float]]] = {
        name: {"log_persistence": [], "log_formation": [], "formation": []}
        for name, _lo, _hi in SIZE_BINS
    }
    # Root has no parent and is excluded. Every other internal node represents a branch
    # born at its own merge distance and merged into its parent at parent_distance.
    for i in range(n - 2):
        node = n + i
        size = int(sizes[node])
        name = bin_name(size)
        if name is None:
            continue
        d_form = float(distances[i])
        d_parent = float(parent_distance[node])
        if not (math.isfinite(d_form) and math.isfinite(d_parent) and d_form > 0.0 and d_parent > 0.0):
            continue
        # Monotonic linkage implies d_parent >= d_form, modulo floating arithmetic.
        req(d_parent + 1e-12 >= d_form, "parent merge precedes branch formation")
        log_persistence = math.log(d_parent / d_form)
        log_formation = math.log(d_form)
        req(math.isfinite(log_persistence) and log_persistence >= -1e-12, "invalid log persistence")
        by_bin[name]["log_persistence"].append(max(0.0, log_persistence))
        by_bin[name]["log_formation"].append(log_formation)
        by_bin[name]["formation"].append(d_form)

    arrays: dict[str, dict[str, np.ndarray]] = {}
    for name, vectors in by_bin.items():
        arrays[name] = {key: np.asarray(vals, dtype=float) for key, vals in vectors.items()}
    return arrays, n - 1


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

    parent_runner = load_module(a.parent_runner, "singlelink_scale_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")

    qmod = load_module(a.quality_source, "singlelink_scale_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-singlelink-persistence-scale-v1-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        normalized = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(normalized) == len(raw), f"normalization count changed for {year}")
        events.extend(normalized)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    X_full = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    pooled: dict[int, dict[str, dict[str, list[np.ndarray]]]] = {
        d: {
            name: {"log_persistence": [], "log_formation": [], "formation": []}
            for name, _lo, _hi in SIZE_BINS
        }
        for d in (128, 1024)
    }
    subset_rows: list[dict[str, Any]] = []

    for denominator, bucket in SUBSETS:
        idx = selected_indices(hashes, denominator, bucket)
        X = np.asarray(X_full[idx], dtype=float)
        years = np.asarray(years_full[idx], dtype=np.int64)
        counts = {str(y): int(np.sum(years == y)) for y in YEARS}
        req(all(counts[str(y)] > 0 for y in YEARS), "subset lost one year")
        print(f"[singlelink-scale] d={denominator} b={bucket} n={len(idx)}", flush=True)
        arrays, internal_nodes = tree_statistics(X)
        bin_summaries: dict[str, Any] = {}
        for name, _lo, _hi in SIZE_BINS:
            lp = arrays[name]["log_persistence"]
            lf = arrays[name]["log_formation"]
            form = arrays[name]["formation"]
            if len(lp):
                req(len(lp) == len(lf) == len(form), "branch vector length mismatch")
                pooled[denominator][name]["log_persistence"].append(lp)
                pooled[denominator][name]["log_formation"].append(lf)
                pooled[denominator][name]["formation"].append(form)
                bin_summaries[name] = {
                    "branch_count": int(len(lp)),
                    "log_persistence": quantiles(lp),
                    "formation_distance": quantiles(form),
                }
            else:
                bin_summaries[name] = {"branch_count": 0}
        row = {
            "denominator": int(denominator),
            "bucket": int(bucket),
            "events_total": int(len(idx)),
            "events_by_year": counts,
            "internal_node_count": int(internal_nodes),
            "size_bins": bin_summaries,
        }
        subset_rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    comparisons: dict[str, Any] = {}
    supported = 0
    wins = 0
    for name, lo, hi in SIZE_BINS:
        merged: dict[int, dict[str, np.ndarray]] = {}
        for denominator in (128, 1024):
            merged[denominator] = {}
            for key in ("log_persistence", "log_formation", "formation"):
                pieces = pooled[denominator][name][key]
                merged[denominator][key] = np.concatenate(pieces) if pieces else np.asarray([], dtype=float)
        n128 = int(len(merged[128]["log_persistence"]))
        n1024 = int(len(merged[1024]["log_persistence"]))
        is_supported = n128 >= MIN_SUPPORTED and n1024 >= MIN_SUPPORTED
        comp: dict[str, Any] = {
            "size_range": [lo, hi],
            "branch_count_d128": n128,
            "branch_count_d1024": n1024,
            "supported": bool(is_supported),
        }
        if is_supported:
            supported += 1
            p128 = merged[128]["log_persistence"]
            p1024 = merged[1024]["log_persistence"]
            f128 = merged[128]["log_formation"]
            f1024 = merged[1024]["log_formation"]
            ks_p = float(ks_2samp(p128, p1024, method="auto").statistic)
            ks_f = float(ks_2samp(f128, f1024, method="auto").statistic)
            med_p = abs(float(np.median(p128)) - float(np.median(p1024)))
            med_f = abs(float(np.median(f128)) - float(np.median(f1024)))
            p90_p = abs(float(np.quantile(p128, 0.90)) - float(np.quantile(p1024, 0.90)))
            p90_f = abs(float(np.quantile(f128, 0.90)) - float(np.quantile(f1024, 0.90)))
            win = ks_p < ks_f and med_p < med_f and p90_p < p90_f
            wins += int(win)
            comp.update(
                {
                    "KS_persistence": ks_p,
                    "KS_formation": ks_f,
                    "MED_persistence": med_p,
                    "MED_formation": med_f,
                    "P90_persistence": p90_p,
                    "P90_formation": p90_f,
                    "strict_scale_normalization_win": bool(win),
                    "pooled_d128_log_persistence": quantiles(p128),
                    "pooled_d1024_log_persistence": quantiles(p1024),
                    "pooled_d128_formation_distance": quantiles(merged[128]["formation"]),
                    "pooled_d1024_formation_distance": quantiles(merged[1024]["formation"]),
                }
            )
        comparisons[name] = comp

    if supported >= 3 and wins == supported:
        interpretation = "SUPPORTS_SINGLELINK_PERSISTENCE_SCALE_NORMALIZATION"
    elif supported >= 3 and wins <= 1:
        interpretation = "REFUTES_SINGLELINK_PERSISTENCE_SCALE_NORMALIZATION"
    else:
        interpretation = "MIXED_SINGLELINK_PERSISTENCE_SCALE_EVIDENCE"

    result = {
        "schema": "ORBITTRACE_SINGLELINK_PERSISTENCE_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_FEASIBILITY_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "supported_bin_count": int(supported),
        "strict_win_count": int(wins),
        "question": "Is dimensionless single-link branch persistence empirically less sample-size-sensitive than raw branch formation distance?",
        "tree": {
            "algorithm": "sklearn AgglomerativeClustering",
            "linkage": "single",
            "metric": "euclidean",
            "support_parameter": None,
            "minimum_cluster_condensation": None,
        },
        "sampling": {
            "salt": SALT,
            "denominators": [128, 1024],
            "buckets": [0, 1, 2, 3],
        },
        "size_bins": [{"name": name, "min": lo, "max": hi} for name, lo, hi in SIZE_BINS],
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
    out = a.output / "SINGLELINK_PERSISTENCE_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "comparisons": comparisons}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
