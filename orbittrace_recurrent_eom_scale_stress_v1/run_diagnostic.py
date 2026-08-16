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
from hdbscan._hdbscan_tree import compute_stability
from sklearn.neighbors import NearestNeighbors

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_KERNEL_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
PARENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
MAIN_DENOMINATORS = (8, 16, 32, 64, 128, 256, 512, 1024)
REPLICATE_DENOMINATORS = (64, 128, 512, 1024)
REPLICATE_BUCKETS = (0, 1, 2, 3)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


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
    req(denominator > 0 and denominator & (denominator - 1) == 0, "denominator must be power of two")
    req(0 <= bucket < denominator, "bucket outside denominator")
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def membership_hashes(labels: np.ndarray, event_ids: list[str]) -> list[str]:
    out: list[str] = []
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    for label in positive:
        members = sorted(event_ids[int(i)] for i in np.flatnonzero(labels == label))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected membership below frozen minimum: label={label}")
        out.append(hashlib.sha256(("|".join(members)).encode("utf-8")).hexdigest())
    return sorted(out)


def fit_one(
    X_full: np.ndarray,
    years_full: np.ndarray,
    ids_full: list[str],
    hashes: np.ndarray,
    denominator: int,
    bucket: int,
    parent_runner: Any,
) -> dict[str, Any]:
    idx = selected_indices(hashes, denominator, bucket)
    X = np.asarray(X_full[idx], dtype=float)
    years = np.asarray(years_full[idx], dtype=np.int64)
    event_ids = [ids_full[int(i)] for i in idx]
    n = int(len(idx))
    counts = {str(y): int(np.sum(years == y)) for y in YEARS}
    req(n > 10, f"subset too small for fixed 10-NN diagnostic: d={denominator} b={bucket} n={n}")
    req(all(counts[str(y)] > 0 for y in YEARS), f"subset lost observing year: d={denominator} b={bucket}")

    # Exact non-self 10-NN distances are a descriptive physical-resolution diagnostic only.
    nn = NearestNeighbors(n_neighbors=11, metric="euclidean", n_jobs=1)
    nn.fit(X)
    distances = nn.kneighbors(X, return_distance=True)[0][:, -1]
    req(np.all(np.isfinite(distances)), "nonfinite 10-NN distance")
    nn_q = {
        "median": float(np.quantile(distances, 0.50)),
        "p90": float(np.quantile(distances, 0.90)),
        "p99": float(np.quantile(distances, 0.99)),
    }

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    req(int(tree["parent"].min()) == n, "condensed-tree root no longer equals point count")

    ordinary = compute_stability(tree)
    ordinary_labels = eom_labels(tree, ordinary)
    req(
        parent_runner.canonical_partition(model.labels_) == parent_runner.canonical_partition(ordinary_labels),
        "custom ordinary-EOM extraction diverged from vanilla HDBSCAN",
    )
    ordinary_nodes = selected_eom_nodes(tree, ordinary)

    recurrent, annual = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)

    ordinary_set = set(int(x) for x in ordinary_nodes)
    recurrent_set = set(int(x) for x in recurrent_nodes)
    node_union = ordinary_set | recurrent_set
    node_intersection = ordinary_set & recurrent_set
    node_symdiff = ordinary_set ^ recurrent_set

    ordinary_memberships = membership_hashes(ordinary_labels, event_ids)
    recurrent_memberships = membership_hashes(recurrent_labels, event_ids)
    ordinary_membership_set = set(ordinary_memberships)
    recurrent_membership_set = set(recurrent_memberships)

    root = n
    cluster_nodes = set(int(x) for x in tree["parent"] if int(x) >= root)
    cluster_nodes.update(int(x) for x in tree["child"] if int(x) >= root)
    positive_recurrent = sum(float(v) > 0.0 for v in recurrent.values())
    positive_both_annual = sum(float(v[0]) > 0.0 and float(v[1]) > 0.0 for v in annual.values())

    return {
        "denominator": int(denominator),
        "bucket": int(bucket),
        "fraction": float(1.0 / denominator),
        "events_total": n,
        "events_by_year": counts,
        "nonself_10nn_distance": nn_q,
        "condensed_tree_rows": int(len(tree)),
        "cluster_node_count": int(len(cluster_nodes)),
        "ordinary_selected_node_count": int(len(ordinary_nodes)),
        "recurrent_selected_node_count": int(len(recurrent_nodes)),
        "selected_node_intersection_count": int(len(node_intersection)),
        "selected_node_symmetric_difference_count": int(len(node_symdiff)),
        "selected_node_jaccard": float(len(node_intersection) / len(node_union)) if node_union else 1.0,
        "mechanism_active": bool(ordinary_set != recurrent_set),
        "ordinary_membership_hashes": ordinary_memberships,
        "recurrent_membership_hashes": recurrent_memberships,
        "exact_membership_intersection_count": int(len(ordinary_membership_set & recurrent_membership_set)),
        "positive_recurrent_quality_node_count": int(positive_recurrent),
        "positive_both_year_annual_contribution_node_count": int(positive_both_annual),
    }


def inactive_rate(rows: list[dict[str, Any]]) -> float:
    req(rows, "cannot summarize empty band")
    return float(sum(not bool(row["mechanism_active"]) for row in rows) / len(rows))


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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")

    parent_runner = load_module(a.parent_runner, "scale_stress_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == MIN_CLUSTER_SIZE, "parent min_cluster_size changed")
    req(int(parent_runner.MIN_SAMPLES) == MIN_SAMPLES, "parent min_samples changed")

    qmod = load_module(a.quality_source, "scale_stress_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-scale-stress-v1-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    # The frozen loader returns the already-exposed GMN development truth object, but this
    # diagnostic never reads, indexes, iterates, hashes, evaluates, or persists it.
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        normalized = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(normalized) == len(raw), f"event normalization changed {year} count")
        events.extend(normalized)
    req(len(events) == 738682, f"accessible pooled event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X_full = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    # Exact nesting assertion for the frozen bucket-0 sequence.
    previous_idx: np.ndarray | None = None
    previous_d: int | None = None
    for d in MAIN_DENOMINATORS:
        idx = selected_indices(hashes, d, 0)
        if previous_idx is not None:
            req(np.all((hashes[idx] % np.uint64(previous_d)) == 0), f"nested subset invariant failed at d={d}")
            req(len(idx) <= len(previous_idx), f"nested subset count increased at d={d}")
        previous_idx = idx
        previous_d = d

    fit_keys: list[tuple[int, int]] = [(d, 0) for d in MAIN_DENOMINATORS]
    for d in REPLICATE_DENOMINATORS:
        for b in (1, 2, 3):
            fit_keys.append((d, b))
    req(len(fit_keys) == 20, f"unexpected frozen fit count: {len(fit_keys)}")
    req(len(set(fit_keys)) == len(fit_keys), "duplicate frozen fit key")

    fits: list[dict[str, Any]] = []
    for d, b in fit_keys:
        print(f"[scale-stress] fitting denominator={d} bucket={b}", flush=True)
        row = fit_one(X_full, years_full, ids_full, hashes, d, b, parent_runner)
        fits.append(row)
        print(
            json.dumps(
                {
                    "d": d,
                    "b": b,
                    "n": row["events_total"],
                    "ordinary": row["ordinary_selected_node_count"],
                    "recurrent": row["recurrent_selected_node_count"],
                    "symdiff": row["selected_node_symmetric_difference_count"],
                    "active": row["mechanism_active"],
                    "median_10nn": row["nonself_10nn_distance"]["median"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    nested = sorted((r for r in fits if int(r["bucket"]) == 0), key=lambda r: int(r["denominator"]))
    base_median = float(nested[0]["nonself_10nn_distance"]["median"])
    req(base_median > 0.0 and math.isfinite(base_median), "invalid base 10-NN median")
    for row in nested:
        row["median_10nn_ratio_vs_denominator_8"] = float(row["nonself_10nn_distance"]["median"] / base_median)

    asfn_band = [r for r in fits if int(r["denominator"]) in (64, 128) and int(r["bucket"]) in REPLICATE_BUCKETS]
    efn_band = [r for r in fits if int(r["denominator"]) == 1024 and int(r["bucket"]) in REPLICATE_BUCKETS]
    req(len(asfn_band) == 8, "ASFN-size band must contain 8 frozen fits")
    req(len(efn_band) == 4, "EFN-size band must contain 4 frozen fits")
    asfn_inactive = inactive_rate(asfn_band)
    efn_inactive = inactive_rate(efn_band)
    if asfn_inactive >= 0.75 and efn_inactive >= 0.75:
        interpretation = "SUPPORTS_FIXED_SCALE_INERTIA_HYPOTHESIS"
    elif asfn_inactive <= 0.25 and efn_inactive <= 0.25:
        interpretation = "REFUTES_FIXED_SCALE_INERTIA_HYPOTHESIS"
    else:
        interpretation = "MIXED_FIXED_SCALE_INERTIA_EVIDENCE"

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_SCALE_STRESS_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "question": "Does fixed HDBSCAN 10/10 make recurrent-EOM extraction increasingly inert as accessible sample size shrinks?",
        "parent": {
            "method": "recurrent-EOM HDBSCAN v1",
            "selected_branch_head_at_creation": "0248177a2b4dc1f7a0969931d835097d3e86c06f",
            "kernel_git_blob": PARENT_KERNEL_BLOB,
            "runner_git_blob": PARENT_RUNNER_BLOB,
            "binding_gmn_run": 31827903547,
            "events_by_year": {"2022": 315024, "2023": 423658},
            "events_total": 738682,
        },
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "sampling": {
            "salt": SALT,
            "hash": "uint64_be(first_8_bytes(SHA256(salt + event_id)))",
            "main_denominators": list(MAIN_DENOMINATORS),
            "replicate_denominators": list(REPLICATE_DENOMINATORS),
            "replicate_buckets": list(REPLICATE_BUCKETS),
            "fit_count": len(fits),
        },
        "band_summary": {
            "ASFN_SIZE_BAND": {
                "denominators": [64, 128],
                "fit_count": len(asfn_band),
                "inactive_count": int(sum(not bool(r["mechanism_active"]) for r in asfn_band)),
                "inactive_rate": asfn_inactive,
            },
            "EFN_SIZE_BAND": {
                "denominators": [1024],
                "fit_count": len(efn_band),
                "inactive_count": int(sum(not bool(r["mechanism_active"]) for r in efn_band)),
                "inactive_rate": efn_inactive,
            },
        },
        "nested_bucket_zero": nested,
        "all_fits": sorted(fits, key=lambda r: (int(r["denominator"]), int(r["bucket"]))),
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
    out = a.output / "RECURRENT_EOM_SCALE_STRESS_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "band_summary": result["band_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
