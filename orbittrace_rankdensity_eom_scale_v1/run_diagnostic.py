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
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
MIN_OUTPUT_SUPPORT = 4


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


def member_hash(members: frozenset[str]) -> str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def density_percentiles(X: np.ndarray, event_ids: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(X)
    req(n > 64 and X.shape == (n, 6), "invalid GEO6 subset")
    tree = cKDTree(X)
    d, _idx = tree.query(X, k=4, workers=1)
    d = np.asarray(d, dtype=float)
    req(d.shape == (n, 4), "wrong 3NN query shape")
    req(np.all(np.abs(d[:, 0]) <= 1e-14), "self neighbor is not first")
    r3 = np.asarray(d[:, 3], dtype=float)
    req(np.all(np.isfinite(r3)) and np.all(r3 > 0.0), "invalid third-neighbor radius")

    # Deterministic unique ordinal density rank: ascending r3 = denser.
    ids = np.asarray(event_ids, dtype=str)
    order = np.lexsort((ids, r3))
    ranks = np.empty(n, dtype=np.int64)
    ranks[order] = np.arange(1, n + 1, dtype=np.int64)
    q = 1.0 - ranks.astype(float) / float(n + 1)
    req(np.all(q > 0.0) and np.all(q < 1.0), "rank percentile outside (0,1)")
    req(len(np.unique(q)) == n, "density percentiles not unique")
    return r3, ranks, q


def euclidean_mst(X: np.ndarray) -> np.ndarray:
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
    mst = np.asarray(model.minimum_spanning_tree_.to_numpy(), dtype=float)
    req(mst.shape == (len(X) - 1, 3), f"wrong MST shape {mst.shape}")
    req(np.all(np.isfinite(mst)), "nonfinite MST")
    return mst


def rankdensity_candidates(X: np.ndarray, event_ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    n = len(X)
    r3, ranks, q = density_percentiles(X, event_ids)
    mst = euclidean_mst(X)
    endpoints = np.asarray(np.rint(mst[:, :2]), dtype=np.int64)
    req(np.all((endpoints >= 0) & (endpoints < n)), "MST endpoint outside event range")

    # Edge activation level is min(q_u,q_v), equivalently max(ordinal rank_u, rank_v).
    edge_level_rank = np.maximum(ranks[endpoints[:, 0]], ranks[endpoints[:, 1]])
    edge_order = np.lexsort((np.maximum(endpoints[:, 0], endpoints[:, 1]), np.minimum(endpoints[:, 0], endpoints[:, 1]), edge_level_rank))
    endpoints = endpoints[edge_order]
    edge_level_rank = edge_level_rank[edge_order]

    # Merge-tree node arrays. Leaves 0..n-1; parents appended as simultaneous edge-level merges occur.
    node_birth: list[float] = [float(x) for x in q]
    node_size: list[int] = [1] * n
    node_children: list[tuple[int, ...]] = [tuple() for _ in range(n)]
    node_parent: list[int] = [-1] * n

    uf_parent = np.arange(n, dtype=np.int64)
    current_node = np.arange(n, dtype=np.int64)

    def find(x: int) -> int:
        x = int(x)
        while int(uf_parent[x]) != x:
            uf_parent[x] = uf_parent[int(uf_parent[x])]
            x = int(uf_parent[x])
        return x

    pos = 0
    while pos < len(endpoints):
        level_rank = int(edge_level_rank[pos])
        end = pos + 1
        while end < len(endpoints) and int(edge_level_rank[end]) == level_rank:
            end += 1

        # Snapshot current components before any same-level merge; merge all connected
        # components at this level simultaneously rather than imposing binary ordering.
        adj: dict[int, set[int]] = {}
        for ei in range(pos, end):
            u, v = int(endpoints[ei, 0]), int(endpoints[ei, 1])
            ru, rv = find(u), find(v)
            if ru == rv:
                continue
            adj.setdefault(ru, set()).add(rv)
            adj.setdefault(rv, set()).add(ru)

        seen: set[int] = set()
        groups: list[list[int]] = []
        for root in sorted(adj):
            if root in seen:
                continue
            stack = [root]
            seen.add(root)
            group = []
            while stack:
                cur = stack.pop()
                group.append(cur)
                for nb in adj.get(cur, ()):
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
            if len(group) >= 2:
                groups.append(sorted(group))

        birth = 1.0 - float(level_rank) / float(n + 1)
        for roots in groups:
            child_nodes = tuple(sorted(int(current_node[r]) for r in roots))
            req(len(set(child_nodes)) == len(child_nodes), "duplicate child in simultaneous merge")
            new_node = len(node_birth)
            node_birth.append(birth)
            node_size.append(sum(node_size[c] for c in child_nodes))
            node_children.append(child_nodes)
            node_parent.append(-1)
            for c in child_nodes:
                req(node_parent[c] == -1, "merge-tree child already has parent")
                node_parent[c] = new_node

            canon = min(roots)
            for r in roots:
                uf_parent[r] = canon
            uf_parent[canon] = canon
            current_node[canon] = new_node
        pos = end

    roots = sorted({find(i) for i in range(n)})
    req(len(roots) == 1, f"MST merge tree did not connect: {len(roots)} roots")
    root_node = int(current_node[roots[0]])
    req(node_size[root_node] == n, "root membership size mismatch")
    req(node_parent[root_node] == -1, "root unexpectedly has parent")

    total_nodes = len(node_birth)
    quality = np.zeros(total_nodes, dtype=float)
    best = np.zeros(total_nodes, dtype=float)
    choose_self = np.zeros(total_nodes, dtype=bool)
    positive_eligible = 0

    # Nodes were appended only after all their children, so ascending node ID is postorder.
    for node in range(total_nodes):
        children = node_children[node]
        child_sum = float(sum(best[c] for c in children))
        if node == root_node:
            best[node] = child_sum
            continue
        parent = node_parent[node]
        req(parent >= 0, "nonroot node missing parent")
        birth_level = float(node_birth[node])
        death_level = float(node_birth[parent])
        req(birth_level + 1e-15 >= death_level, "rank-density branch has negative lifetime")
        lifetime = max(0.0, birth_level - death_level)
        qown = (float(node_size[node]) / float(n)) * lifetime if node_size[node] >= MIN_OUTPUT_SUPPORT else 0.0
        req(math.isfinite(qown) and qown >= 0.0, "invalid branch quality")
        quality[node] = qown
        if qown > 0.0:
            positive_eligible += 1
        if node_size[node] >= MIN_OUTPUT_SUPPORT and qown > child_sum:
            choose_self[node] = True
            best[node] = qown
        else:
            best[node] = child_sum

    selected_nodes: list[int] = []
    def collect(node: int) -> None:
        if node != root_node and choose_self[node]:
            selected_nodes.append(node)
            return
        for c in node_children[node]:
            collect(c)
    collect(root_node)
    req(len(selected_nodes) == len(set(selected_nodes)), "duplicate selected rank-density node")

    def leaves(node: int) -> list[int]:
        stack = [node]
        out: list[int] = []
        while stack:
            cur = stack.pop()
            if cur < n:
                out.append(cur)
            else:
                stack.extend(node_children[cur])
        return out

    candidates: list[frozenset[str]] = []
    rows = []
    covered: set[str] = set()
    for node in selected_nodes:
        idx = leaves(node)
        members = frozenset(event_ids[i] for i in idx)
        req(len(members) == node_size[node] and len(members) >= MIN_OUTPUT_SUPPORT, "selected membership mismatch")
        req(covered.isdisjoint(members), "selected rank-density branches overlap")
        covered.update(members)
        parent = node_parent[node]
        lifetime = float(node_birth[node] - node_birth[parent])
        candidates.append(members)
        rows.append({
            "family_hash": member_hash(members),
            "member_count": len(members),
            "birth_percentile": float(node_birth[node]),
            "death_percentile": float(node_birth[parent]),
            "percentile_lifetime": lifetime,
            "quality": float(quality[node]),
        })
    rows.sort(key=lambda r: (-r["quality"], -r["member_count"], r["family_hash"]))
    return candidates, {
        "selected_count": len(candidates),
        "covered_events": len(covered),
        "covered_fraction": float(len(covered) / n),
        "positive_eligible_branch_count": positive_eligible,
        "merge_tree_node_count": total_nodes,
        "median_r3": float(np.median(r3)),
        "candidate_rows": rows,
    }


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
    candidates = []
    rows = []
    for lab in positive:
        idx = np.flatnonzero(labels == lab)
        members = frozenset(event_ids[int(i)] for i in idx)
        candidates.append(members)
        rows.append({"family_hash": member_hash(members), "member_count": len(members)})
    return candidates, {"selected_count": len(candidates), "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"]))}


def cross_scale_metrics(coarse: list[frozenset[str]], fine: list[frozenset[str]], fine_universe: frozenset[str]) -> dict[str, Any]:
    restricted = []
    for c in coarse:
        r = frozenset(c.intersection(fine_universe))
        if len(r) >= MIN_OUTPUT_SUPPORT:
            restricted.append(r)
    weighted_num = 0.0
    weighted_den = 0
    scores = []
    exact = 0
    for f in fine:
        best_j = 0.0
        exact_here = False
        for c in restricted:
            inter = len(f.intersection(c))
            if not inter:
                continue
            j = float(inter / len(f.union(c)))
            best_j = max(best_j, j)
            exact_here = exact_here or (f == c)
        scores.append(best_j)
        weighted_num += len(f) * best_j
        weighted_den += len(f)
        exact += int(exact_here)
    arr = np.asarray(scores, dtype=float)
    return {
        "fine_candidate_count": len(fine),
        "restricted_coarse_candidate_count": len(restricted),
        "event_weighted_mean_best_jaccard": float(weighted_num / weighted_den) if weighted_den else 0.0,
        "median_best_jaccard": float(np.median(arr)) if len(arr) else 0.0,
        "exact_restricted_match_fraction": float(exact / len(fine)) if fine else 0.0,
        "weighted_event_denominator": int(weighted_den),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen support artifact changed")
    parent_runner = load_module(a.parent_runner, "rankdensity_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "rankdensity_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-rankdensity-eom-scale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), "wrong years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list changed")

    events = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), "normalization count changed")
        events.extend(norm)
    req(len(events) == 738682, f"pooled count changed {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived")

    Xfull = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    fits: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[rankdensity-eom] d={denominator} b={bucket} n={len(ids)}", flush=True)
            rd_candidates, rd_summary = rankdensity_candidates(X, ids)
            re_candidates, re_summary = recurrent_eom_candidates(parent_runner, X, years, ids)
            fits[(denominator, bucket)] = {
                "ids": frozenset(ids),
                "rankdensity_candidates": rd_candidates,
                "recurrent_candidates": re_candidates,
                "row": {
                    "denominator": denominator,
                    "bucket": bucket,
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "rankdensity_eom": rd_summary,
                    "recurrent_eom": re_summary,
                },
            }
            print(json.dumps(fits[(denominator, bucket)]["row"], sort_keys=True), flush=True)

    pairs = []
    rd_num = rd_den = re_num = re_den = 0.0
    rd_bucket = []
    re_bucket = []
    wins = 0
    for bucket in BUCKETS:
        coarse = fits[(COARSE_D, bucket)]
        fine = fits[(FINE_D, bucket)]
        req(fine["ids"].issubset(coarse["ids"]), "nested subset failed")
        rd = cross_scale_metrics(coarse["rankdensity_candidates"], fine["rankdensity_candidates"], fine["ids"])
        re = cross_scale_metrics(coarse["recurrent_candidates"], fine["recurrent_candidates"], fine["ids"])
        rd_score = float(rd["event_weighted_mean_best_jaccard"])
        re_score = float(re["event_weighted_mean_best_jaccard"])
        rd_bucket.append(rd_score); re_bucket.append(re_score)
        wins += int(rd_score > re_score)
        rd_num += rd_score * rd["weighted_event_denominator"]; rd_den += rd["weighted_event_denominator"]
        re_num += re_score * re["weighted_event_denominator"]; re_den += re["weighted_event_denominator"]
        pairs.append({"bucket": bucket, "rankdensity_eom": rd, "recurrent_eom": re, "rankdensity_strict_win": rd_score > re_score})

    rd_pooled = float(rd_num / rd_den) if rd_den else 0.0
    re_pooled = float(re_num / re_den) if re_den else 0.0
    rd_med = float(np.median(np.asarray(rd_bucket)))
    re_med = float(np.median(np.asarray(re_bucket)))
    nonempty = all(len(fits[(d,b)]["rankdensity_candidates"]) > 0 for d in (COARSE_D,FINE_D) for b in BUCKETS)
    gate = {
        "rankdensity_nonempty_all_eight": bool(nonempty),
        "pooled_weighted_jaccard_strictly_better": rd_pooled > re_pooled,
        "median_bucket_weighted_jaccard_strictly_better": rd_med > re_med,
        "wins_at_least_three_of_four_buckets": wins >= 3,
    }
    interpretation = "SUPPORTS_RANKDENSITY_EOM_CROSS_SCALE_COHERENCE" if all(gate.values()) else "REFUTES_RANKDENSITY_EOM_CROSS_SCALE_COHERENCE"
    result = {
        "schema": "ORBITTRACE_RANKDENSITY_EOM_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "configuration": {
            "density_neighbor_index": 3,
            "total_density_support": 4,
            "percentile": "1-rank/(n+1), rank by ascending (r3,event_id)",
            "connectivity": "exact Euclidean MST",
            "edge_activation": "min(endpoint density percentiles)",
            "quality": "(branch_mass/n)*(birth_percentile-death_percentile)",
            "min_output_support": 4,
            "eom_tie_rule": "children_on_equality",
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
        },
        "fits": [fits[(d,b)]["row"] for d in (COARSE_D,FINE_D) for b in BUCKETS],
        "nested_pairs": pairs,
        "summary": {
            "rankdensity_eom_pooled_event_weighted_mean_best_jaccard": rd_pooled,
            "recurrent_eom_pooled_event_weighted_mean_best_jaccard": re_pooled,
            "rankdensity_eom_median_bucket_weighted_mean_best_jaccard": rd_med,
            "recurrent_eom_median_bucket_weighted_mean_best_jaccard": re_med,
            "rankdensity_eom_bucket_wins": wins,
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
    out = a.output / "RANKDENSITY_EOM_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "pairs": pairs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
