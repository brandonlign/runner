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

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
BUCKETS = (0, 1, 2, 3)
COARSE_D = 128
FINE_D = 1024
MIN_OUTPUT_SUPPORT = 4


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


def member_hash(members: frozenset[str]) -> str:
    return hashlib.sha256("|".join(sorted(members)).encode("utf-8")).hexdigest()[:20]


def scalable_singlelink_tree(X: np.ndarray) -> np.ndarray:
    # min_samples includes the point itself. At 1 the core distance is zero, so
    # mutual reachability is exactly ordinary Euclidean distance. The exact
    # equality to sklearn single linkage on all eight frozen subsets was audited
    # before this diagnostic was implemented.
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
    tree = np.asarray(model.single_linkage_tree_.to_numpy(), dtype=float)
    req(tree.shape == (len(X) - 1, 4), f"wrong single-link tree shape {tree.shape}")
    return tree


def leaves_for_node(node: int, n: int, children: np.ndarray) -> list[int]:
    stack = [int(node)]
    out: list[int] = []
    while stack:
        cur = int(stack.pop())
        if cur < n:
            out.append(cur)
        else:
            row = cur - n
            req(0 <= row < len(children), f"invalid internal node {cur}")
            left, right = children[row]
            stack.append(int(left))
            stack.append(int(right))
    return out


def logmass_fosc_candidates(X: np.ndarray, event_ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    n = int(len(X))
    req(n >= 64, f"unexpectedly small subset {n}")
    tree = scalable_singlelink_tree(X)
    children = np.asarray(np.rint(tree[:, :2]), dtype=np.int64)
    distances = np.asarray(tree[:, 2], dtype=float)
    row_sizes = np.asarray(np.rint(tree[:, 3]), dtype=np.int64)
    req(np.all(np.isfinite(distances)) and np.all(distances >= 0.0), "invalid linkage distances")
    req(np.all(np.diff(distances) >= -1e-12), "single-link distances not monotone")

    total = 2 * n - 1
    sizes = np.ones(total, dtype=np.int64)
    parent_distance = np.full(total, np.nan, dtype=float)
    own_quality = np.zeros(total, dtype=float)
    best_quality = np.zeros(total, dtype=float)
    best_selection: list[tuple[int, ...]] = [tuple() for _ in range(total)]

    # First pass reconstructs sizes and parent merge distances.
    for i, (left, right) in enumerate(children):
        node = n + i
        sizes[node] = sizes[int(left)] + sizes[int(right)]
        req(int(sizes[node]) == int(row_sizes[i]), f"linkage size mismatch at node {node}")
        if int(left) >= n:
            parent_distance[int(left)] = float(distances[i])
        if int(right) >= n:
            parent_distance[int(right)] = float(distances[i])

    root = 2 * n - 2
    quality_rows: list[float] = []

    # Second pass is exact FOSC-style bottom-up optimization. Children always
    # have smaller node IDs than their parent in scipy/HDBSCAN linkage encoding.
    for i, (left, right) in enumerate(children):
        node = n + i
        left_i, right_i = int(left), int(right)
        child_quality = float(best_quality[left_i] + best_quality[right_i])
        child_selection = best_selection[left_i] + best_selection[right_i]

        q = 0.0
        if node != root and int(sizes[node]) >= MIN_OUTPUT_SUPPORT:
            d_form = float(distances[i])
            d_parent = float(parent_distance[node])
            if math.isfinite(d_form) and math.isfinite(d_parent) and d_form > 0.0 and d_parent > 0.0:
                req(d_parent + 1e-12 >= d_form, "parent merge precedes formation")
                lifetime = max(0.0, math.log(d_parent / d_form))
                q = (float(sizes[node]) / float(n)) * lifetime
                req(math.isfinite(q) and q >= 0.0, "invalid log-mass quality")
                quality_rows.append(q)
        own_quality[node] = q

        if node == root:
            best_quality[node] = child_quality
            best_selection[node] = child_selection
        elif int(sizes[node]) >= MIN_OUTPUT_SUPPORT and q >= child_quality:
            # Frozen parsimony tie rule: parent wins ties.
            best_quality[node] = q
            best_selection[node] = (node,)
        else:
            best_quality[node] = child_quality
            best_selection[node] = child_selection

    selected_nodes = best_selection[root]
    req(len(selected_nodes) == len(set(selected_nodes)), "duplicate selected node")
    candidates: list[frozenset[str]] = []
    candidate_rows = []
    seen_ids: set[str] = set()
    for node in selected_nodes:
        idx = leaves_for_node(int(node), n, children)
        members = frozenset(event_ids[j] for j in idx)
        req(len(members) == int(sizes[int(node)]), "selected membership size mismatch")
        req(len(members) >= MIN_OUTPUT_SUPPORT, "selected output below minimum support")
        req(seen_ids.isdisjoint(members), "FOSC selected overlapping branches")
        seen_ids.update(members)
        candidates.append(members)
        candidate_rows.append({
            "family_hash": member_hash(members),
            "member_count": len(members),
            "quality": float(own_quality[int(node)]),
        })

    candidate_rows.sort(key=lambda r: (-r["quality"], -r["member_count"], r["family_hash"]))
    summary = {
        "selected_count": len(candidates),
        "covered_events": len(seen_ids),
        "covered_fraction": float(len(seen_ids) / n),
        "selected_member_counts": sorted(len(c) for c in candidates),
        "candidate_rows": candidate_rows,
        "total_selected_quality": float(best_quality[root]),
        "positive_quality_node_count": int(sum(q > 0.0 for q in quality_rows)),
    }
    return candidates, summary


def recurrent_eom_candidates(parent_runner: Any, X: np.ndarray, years: np.ndarray, event_ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    recurrent, _annual = parent_runner.recurrent_stability(tree, years)
    labels = np.asarray(parent_runner.eom_labels(tree, recurrent), dtype=np.int64)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    candidates: list[frozenset[str]] = []
    rows = []
    for lab in positive:
        idx = np.flatnonzero(labels == lab)
        members = frozenset(event_ids[int(i)] for i in idx)
        req(len(members) >= 10, "recurrent-EOM comparator emitted sub-10 candidate")
        candidates.append(members)
        rows.append({"family_hash": member_hash(members), "member_count": len(members)})
    return candidates, {
        "selected_count": len(candidates),
        "selected_member_counts": sorted(len(c) for c in candidates),
        "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def cross_scale_metrics(coarse: list[frozenset[str]], fine: list[frozenset[str]], fine_universe: frozenset[str]) -> dict[str, Any]:
    restricted: list[frozenset[str]] = []
    for c in coarse:
        r = frozenset(c.intersection(fine_universe))
        if len(r) >= MIN_OUTPUT_SUPPORT:
            restricted.append(r)

    best_rows = []
    weighted_num = 0.0
    weighted_den = 0
    exact = 0
    for f in fine:
        best = 0.0
        exact_here = False
        for c in restricted:
            inter = len(f.intersection(c))
            if inter == 0:
                continue
            union = len(f.union(c))
            j = float(inter / union)
            if j > best:
                best = j
            if f == c:
                exact_here = True
        weighted_num += len(f) * best
        weighted_den += len(f)
        exact += int(exact_here)
        best_rows.append({"member_count": len(f), "best_jaccard": best, "exact_restricted_match": exact_here})

    scores = np.asarray([r["best_jaccard"] for r in best_rows], dtype=float)
    return {
        "fine_candidate_count": len(fine),
        "restricted_coarse_candidate_count": len(restricted),
        "event_weighted_mean_best_jaccard": float(weighted_num / weighted_den) if weighted_den else 0.0,
        "median_best_jaccard": float(np.median(scores)) if len(scores) else 0.0,
        "exact_restricted_match_fraction": float(exact / len(fine)) if fine else 0.0,
        "weighted_event_denominator": int(weighted_den),
        "best_match_rows": best_rows,
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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent_runner = load_module(a.parent_runner, "logmass_fosc_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent HDBSCAN support changed")

    qmod = load_module(a.quality_source, "logmass_fosc_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-singlelink-logmass-fosc-scale-v1-target-excluded"
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

    fits: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            idx = selected_indices(hashes, denominator, bucket)
            X = np.asarray(X_full[idx], dtype=float)
            years = np.asarray(years_full[idx], dtype=np.int64)
            ids = [ids_full[int(i)] for i in idx]
            req(all(np.any(years == y) for y in YEARS), "subset lost one year")
            print(f"[logmass-fosc-scale] d={denominator} b={bucket} n={len(idx)}", flush=True)
            sl_candidates, sl_summary = logmass_fosc_candidates(X, ids)
            re_candidates, re_summary = recurrent_eom_candidates(parent_runner, X, years, ids)
            fits[(denominator, bucket)] = {
                "ids": frozenset(ids),
                "singlelink_candidates": sl_candidates,
                "recurrent_candidates": re_candidates,
                "row": {
                    "denominator": denominator,
                    "bucket": bucket,
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "logmass_fosc": sl_summary,
                    "recurrent_eom": re_summary,
                },
            }
            print(json.dumps(fits[(denominator, bucket)]["row"], sort_keys=True), flush=True)

    pairs = []
    sl_weighted_num = 0.0
    sl_weighted_den = 0
    re_weighted_num = 0.0
    re_weighted_den = 0
    sl_bucket_scores = []
    re_bucket_scores = []
    bucket_wins = 0

    for bucket in BUCKETS:
        coarse = fits[(COARSE_D, bucket)]
        fine = fits[(FINE_D, bucket)]
        req(fine["ids"].issubset(coarse["ids"]), f"nested subset contract failed bucket {bucket}")
        sl = cross_scale_metrics(coarse["singlelink_candidates"], fine["singlelink_candidates"], fine["ids"])
        re = cross_scale_metrics(coarse["recurrent_candidates"], fine["recurrent_candidates"], fine["ids"])
        sl_score = float(sl["event_weighted_mean_best_jaccard"])
        re_score = float(re["event_weighted_mean_best_jaccard"])
        sl_bucket_scores.append(sl_score)
        re_bucket_scores.append(re_score)
        bucket_wins += int(sl_score > re_score)
        sl_weighted_num += sl_score * int(sl["weighted_event_denominator"])
        sl_weighted_den += int(sl["weighted_event_denominator"])
        re_weighted_num += re_score * int(re["weighted_event_denominator"])
        re_weighted_den += int(re["weighted_event_denominator"])
        pairs.append({"bucket": bucket, "logmass_fosc": sl, "recurrent_eom": re, "logmass_strict_win": sl_score > re_score})

    sl_pooled = float(sl_weighted_num / sl_weighted_den) if sl_weighted_den else 0.0
    re_pooled = float(re_weighted_num / re_weighted_den) if re_weighted_den else 0.0
    sl_median = float(np.median(np.asarray(sl_bucket_scores, dtype=float)))
    re_median = float(np.median(np.asarray(re_bucket_scores, dtype=float)))
    all_sl_nonempty = all(len(fits[(d, b)]["singlelink_candidates"]) > 0 for d in (COARSE_D, FINE_D) for b in BUCKETS)

    gate = {
        "singlelink_nonempty_all_eight": bool(all_sl_nonempty),
        "pooled_weighted_jaccard_strictly_better": bool(sl_pooled > re_pooled),
        "median_bucket_weighted_jaccard_strictly_better": bool(sl_median > re_median),
        "wins_at_least_three_of_four_buckets": bool(bucket_wins >= 3),
    }
    supported = all(gate.values())
    interpretation = "SUPPORTS_LOGMASS_FOSC_CROSS_SCALE_PRUNING" if supported else "REFUTES_LOGMASS_FOSC_CROSS_SCALE_PRUNING"

    result = {
        "schema": "ORBITTRACE_SINGLELINK_LOGMASS_FOSC_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_PRUNING_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "configuration": {
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
            "min_output_support": MIN_OUTPUT_SUPPORT,
            "singlelink": {
                "min_samples": 1,
                "min_cluster_size_tree_exposure_only": 2,
                "metric": "euclidean",
                "algorithm": "boruvka_kdtree",
                "approx_min_span_tree": False,
            },
            "quality": "(member_count / sample_count) * log(parent_merge_distance / formation_distance)",
            "fosc_tie_rule": "parent_wins",
        },
        "fits": [fits[(d, b)]["row"] for d in (COARSE_D, FINE_D) for b in BUCKETS],
        "nested_pairs": pairs,
        "summary": {
            "logmass_fosc_pooled_event_weighted_mean_best_jaccard": sl_pooled,
            "recurrent_eom_pooled_event_weighted_mean_best_jaccard": re_pooled,
            "logmass_fosc_median_bucket_weighted_mean_best_jaccard": sl_median,
            "recurrent_eom_median_bucket_weighted_mean_best_jaccard": re_median,
            "logmass_fosc_bucket_wins": bucket_wins,
            "gate": gate,
        },
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
    out = a.output / "SINGLELINK_LOGMASS_FOSC_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
