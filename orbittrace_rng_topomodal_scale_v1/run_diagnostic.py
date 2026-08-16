#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.spatial import cKDTree
from gudhi.clustering.tomato import Tomato

MIN_SUPPORT = 4
RADIUS = 1.0
METHOD = "ORBITTRACE_RNG_TOPOMODAL_SCALE_V1"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-runner", type=Path, required=True)
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

    base = load_module(a.base_runner, "rng_topomodal_frozen_base")
    req(int(base.MIN_SUPPORT) == MIN_SUPPORT, "#1284 support changed")
    req(float(base.RADIUS) == RADIUS, "#1284 radius changed")

    def rng_topomodal_candidates(events: list[dict[str, Any]]):
        ordered = sorted(events, key=lambda e: str(e["id"]))
        ids = [str(e["id"]) for e in ordered]
        n = len(ids)
        Z = np.asarray(base.physical_embedding(ordered), dtype=float)
        req(Z.shape == (n, 6) and np.all(np.isfinite(Z)), "invalid physical embedding")

        tree = cKDTree(Z)
        raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
        neighbors = [list(map(int, row)) for row in raw_neighbors]
        req(len(neighbors) == n, "radius graph row count changed")
        adjacency = [set(row) for row in neighbors]
        for i, row in enumerate(neighbors):
            req(i in adjacency[i], f"self missing at {i}")
            for j in row:
                req(0 <= j < n and i in adjacency[j], "radius graph not symmetric")

        # Freeze #1284 density before any graph pruning.
        degrees = np.asarray([len(row) for row in neighbors], dtype=float)
        rho = degrees / float(n)
        req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid frozen radius density")

        # Exact radius-capped relative-neighborhood graph. For every radius
        # edge i-j, a pruning witness must be in both original radius-1
        # neighborhoods because d(i,j) <= 1. Strict inequality preserves
        # exact equal-distance ties as required by the frozen protocol.
        rng_adj: list[set[int]] = [{i} for i in range(n)]
        radius_edge_count = 0
        rng_edge_count = 0
        witness_pruned_count = 0
        for i in range(n):
            zi = Z[i]
            for j in neighbors[i]:
                if j <= i:
                    continue
                radius_edge_count += 1
                delta = zi - Z[j]
                dij2 = float(np.dot(delta, delta))
                req(np.isfinite(dij2) and dij2 >= 0.0 and dij2 <= 1.0 + 1e-12, "invalid radius edge distance")
                common = adjacency[i].intersection(adjacency[j])
                keep = True
                for k in common:
                    if k == i or k == j:
                        continue
                    dik = zi - Z[k]
                    djk = Z[j] - Z[k]
                    if float(np.dot(dik, dik)) < dij2 and float(np.dot(djk, djk)) < dij2:
                        keep = False
                        break
                if keep:
                    rng_adj[i].add(j)
                    rng_adj[j].add(i)
                    rng_edge_count += 1
                else:
                    witness_pruned_count += 1
        req(radius_edge_count == rng_edge_count + witness_pruned_count, "RNG edge accounting failed")
        req(all(i in rng_adj[i] for i in range(n)), "RNG self inclusion failed")
        req(all(i in rng_adj[j] for i, row in enumerate(rng_adj) for j in row), "RNG graph not symmetric")

        rng_neighbors = [sorted(row) for row in rng_adj]
        model = Tomato(graph_type="manual", density_type="manual")
        model.fit(rng_neighbors, weights=rho)
        leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
        req(leaf_labels.shape == (n,), "wrong ToMATo leaf-label shape")
        leaf_count = int(model.n_leaves_)
        req(leaf_count >= 1, "no RNG-ToMATo leaves")
        req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "noncontiguous RNG-ToMATo leaves")

        children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
        node_count = leaf_count + len(children)
        memberships: list[frozenset[str] | None] = [None] * node_count
        for leaf in range(leaf_count):
            ix = np.flatnonzero(leaf_labels == leaf)
            req(len(ix) > 0, f"empty RNG-ToMATo leaf {leaf}")
            memberships[leaf] = frozenset(ids[int(q)] for q in ix)
        req(sum(len(memberships[i]) for i in range(leaf_count) if memberships[i] is not None) == n, "leaf basins do not partition sample")

        parent = np.full(node_count, -1, dtype=np.int64)
        for offset, pair in enumerate(children):
            node = leaf_count + offset
            aa, bb = int(pair[0]), int(pair[1])
            req(0 <= aa < node and 0 <= bb < node and aa != bb, f"invalid ToMATo children at {node}")
            req(parent[aa] == -1 and parent[bb] == -1, "hierarchy node has multiple parents")
            ma, mb = memberships[aa], memberships[bb]
            req(ma is not None and mb is not None and ma.isdisjoint(mb), "invalid child memberships")
            memberships[node] = frozenset(ma.union(mb))
            parent[aa] = node
            parent[bb] = node

        roots = np.flatnonzero(parent == -1)
        req(len(roots) == len(np.asarray(model.max_weight_per_cc_)), "root/component count mismatch")
        req(sum(len(memberships[int(r)]) for r in roots if memberships[int(r)] is not None) == n, "roots do not partition sample")

        unique: dict[frozenset[str], dict[str, Any]] = {}
        for node, members in enumerate(memberships):
            req(members is not None, f"missing membership node {node}")
            if len(members) < MIN_SUPPORT:
                continue
            unique.setdefault(members, {
                "family_hash": base.member_hash(members),
                "member_count": len(members),
                "first_node": int(node),
                "is_root": bool(parent[node] == -1),
            })
        candidates = list(unique.keys())
        counts = sorted((len(c) for c in candidates), reverse=True)
        finite = np.asarray(model.diagram_, dtype=float)
        if finite.size:
            req(finite.ndim == 2 and finite.shape[1] == 2 and np.all(np.isfinite(finite)), "invalid persistence diagram")
        return candidates, {
            "candidate_count": len(candidates),
            "leaf_count": leaf_count,
            "internal_node_count": len(children),
            "root_count": len(roots),
            "finite_persistence_point_count": int(len(finite)),
            "original_radius_edge_count": int(radius_edge_count),
            "rng_edge_count": int(rng_edge_count),
            "rng_pruned_edge_count": int(witness_pruned_count),
            "rng_retained_fraction": float(rng_edge_count / radius_edge_count) if radius_edge_count else 0.0,
            "median_original_radius_degree": float(np.median(degrees)),
            "p90_original_radius_degree": float(np.quantile(degrees, 0.90)),
            "median_rng_degree_including_self": float(np.median([len(x) for x in rng_neighbors])),
            "p90_rng_degree_including_self": float(np.quantile([len(x) for x in rng_neighbors], 0.90)),
            "largest_candidate_count": int(counts[0]) if counts else 0,
            "largest_candidate_fraction": float(counts[0] / n) if counts else 0.0,
            "candidate_rows": sorted(unique.values(), key=lambda r: (-r["member_count"], r["family_hash"])),
        }

    # Replace only the graph supplied to ToMATo; parser, physical embedding,
    # radius-count density definition, recurrent comparator, subsets, cross-
    # scale metric, and interpretation gate remain inherited from #1284.
    base.topomodal_candidates = rng_topomodal_candidates

    old_argv = sys.argv[:]
    sys.argv = [
        str(a.base_runner),
        "--parent-runner", str(a.parent_runner),
        "--quality-source", str(a.quality_source),
        "--support-source-parts", str(a.support_source_parts),
        "--candidate-payload", str(a.candidate_payload),
        "--baseline-payload", str(a.baseline_payload),
        "--scorer-parts", str(a.scorer_parts),
        "--v8-result-json", str(a.v8_result_json),
        "--output", str(a.output),
    ]
    try:
        rc = int(base.main())
    finally:
        sys.argv = old_argv
    req(rc == 0, "frozen #1284 diagnostic harness failed")

    legacy = a.output / "TOPOMODAL_HIERARCHY_SCALE_V1.json"
    req(legacy.is_file(), "base result missing")
    d = json.loads(legacy.read_text())
    req(d["scientific_role"] == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "scientific role changed")
    req(d["shower_truth_used"] is False and d["target_information_access"] is False, "firewall changed")

    for row in d["fits"]:
        row["rng_topomodal"] = row.pop("topomodal")
    for pair in d["nested_pairs"]:
        pair["rng_topomodal"] = pair.pop("topomodal")
        pair["rng_topomodal_strict_win"] = pair.pop("topomodal_strict_win")
    s = d["summary"]
    s["rng_topomodal_pooled_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_pooled_fine_to_coarse_mean_best_jaccard")
    s["rng_topomodal_median_bucket_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_median_bucket_fine_to_coarse_mean_best_jaccard")
    s["rng_topomodal_bucket_wins"] = s.pop("topomodal_bucket_wins")
    gate = s["gate"]
    gate["rng_topomodal_nonempty_all_eight"] = gate.pop("topomodal_nonempty_all_eight")
    passed = all(bool(x) for x in gate.values())

    d["schema"] = METHOD
    d["interpretation"] = (
        "SUPPORTS_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE"
        if passed else "REFUTES_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE"
    )
    d["configuration"] = {
        "physical_embedding": "exact_1284_5deg_solar_4deg_radiant_10pct_logspeed",
        "original_graph": "exact_symmetric_radius_1_physical_graph",
        "density": "unchanged_original_radius_degree_over_n_including_self",
        "connectivity": "exact_radius_capped_relative_neighborhood_graph_strict_open_lune",
        "witness_search": "exact_intersection_of_original_radius_1_neighborhoods",
        "tomato": "gudhi_3.12_manual_graph_manual_density_complete_hierarchy",
        "min_candidate_support": MIN_SUPPORT,
        "coarse_denominator": 128,
        "fine_denominator": 1024,
        "buckets": [0, 1, 2, 3],
    }
    d["historical_1284_controls"] = {
        "pooled_fine_to_coarse_mean_best_jaccard": 0.8067062037,
        "median_bucket_fine_to_coarse_mean_best_jaccard": 0.8129624258,
        "strict_wins_vs_recurrent": 4,
    }
    d["method_parameter_selection_from_result"] = False
    out = a.output / "RNG_TOPOMODAL_SCALE_V1.json"
    out.write_text(json.dumps(d, indent=2, sort_keys=True, allow_nan=False) + "\n")
    legacy.unlink()
    print(json.dumps({"interpretation": d["interpretation"], "summary": d["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
