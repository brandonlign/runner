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
METHOD = "ORBITTRACE_STATION_WEIGHTED_TOPOMODAL_SCALE_V1"


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
    ap.add_argument("--numstat-mapping", type=Path, required=True)
    ap.add_argument("--availability-result", type=Path, required=True)
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

    base = load_module(a.base_runner, "station_weighted_frozen_base")
    req(int(base.MIN_SUPPORT) == MIN_SUPPORT, "#1284 support changed")
    req(float(base.RADIUS) == RADIUS, "#1284 radius changed")

    avail = json.loads(a.availability_result.read_text())
    req(avail["schema"] == "ORBITTRACE_TOPOMODAL_NUMSTAT_AVAILABILITY_V1", "wrong availability schema")
    req(avail["verdict"] == "PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1", "availability prerequisite did not PASS")
    req(avail["blind_exclusion"] == [20.0, 55.0], "availability firewall changed")
    mapping = json.loads(a.numstat_mapping.read_text())
    req(isinstance(mapping, dict) and mapping, "empty num_stat mapping")

    # The frozen structural successor is intentionally stricter than the
    # availability gate: every event actually used in any panel must have an
    # exact integer station count >=2. Missingness is never imputed or dropped.
    def station_topomodal_candidates(events: list[dict[str, Any]]):
        ordered = sorted(events, key=lambda e: str(e["id"]))
        ids = [str(e["id"]) for e in ordered]
        vals = []
        missing = []
        for eid in ids:
            value = mapping.get(eid)
            if not isinstance(value, int) or isinstance(value, bool) or value < 2:
                missing.append(eid)
            else:
                vals.append(int(value))
        if missing:
            raise RuntimeError(
                "BLOCKED_STATION_WEIGHTED_TOPOMODAL_INCOMPLETE_EVENT_WEIGHTS: "
                f"{len(missing)}/{len(ids)} subset events lack usable num_stat"
            )
        w = np.asarray(vals, dtype=float)
        req(w.shape == (len(ids),) and np.all(np.isfinite(w)) and np.all(w >= 2.0), "invalid station weights")
        total_support = float(np.sum(w))
        req(np.isfinite(total_support) and total_support > 0.0, "invalid total station support")

        Z = np.asarray(base.physical_embedding(ordered), dtype=float)
        req(Z.shape == (len(ids), 6) and np.all(np.isfinite(Z)), "invalid physical embedding")
        tree = cKDTree(Z)
        raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
        neighbors = [list(map(int, row)) for row in raw_neighbors]
        req(len(neighbors) == len(ids), "radius graph row count changed")
        adjacency = [set(row) for row in neighbors]
        for i, row in enumerate(neighbors):
            req(i in adjacency[i], f"self missing from radius graph at {i}")
            for j in row:
                req(0 <= j < len(ids) and i in adjacency[j], "radius graph not symmetric")

        degrees = np.asarray([len(row) for row in neighbors], dtype=float)
        ordinary_rho = degrees / float(len(ids))
        station_mass = np.asarray([float(np.sum(w[np.asarray(row, dtype=np.int64)])) for row in neighbors], dtype=float)
        rho = station_mass / total_support
        req(rho.shape == (len(ids),), "wrong station-density shape")
        req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid station-weighted density")

        model = Tomato(graph_type="manual", density_type="manual")
        model.fit(neighbors, weights=rho)
        leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
        req(leaf_labels.shape == (len(ids),), "wrong ToMATo leaf label shape")
        leaf_count = int(model.n_leaves_)
        req(leaf_count >= 1, "no ToMATo leaves")
        req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "noncontiguous ToMATo leaves")

        children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
        node_count = leaf_count + len(children)
        memberships: list[frozenset[str] | None] = [None] * node_count
        for leaf in range(leaf_count):
            ix = np.flatnonzero(leaf_labels == leaf)
            req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
            memberships[leaf] = frozenset(ids[int(i)] for i in ix)
        req(sum(len(memberships[i]) for i in range(leaf_count) if memberships[i] is not None) == len(ids), "leaf basins do not partition sample")

        parent = np.full(node_count, -1, dtype=np.int64)
        for offset, pair in enumerate(children):
            node = leaf_count + offset
            x, y = int(pair[0]), int(pair[1])
            req(0 <= x < node and 0 <= y < node and x != y, f"invalid ToMATo children at node {node}")
            req(parent[x] == -1 and parent[y] == -1, "hierarchy node has multiple parents")
            mx, my = memberships[x], memberships[y]
            req(mx is not None and my is not None and mx.isdisjoint(my), "invalid child memberships")
            memberships[node] = frozenset(mx.union(my))
            parent[x] = node
            parent[y] = node

        roots = np.flatnonzero(parent == -1)
        req(len(roots) == len(np.asarray(model.max_weight_per_cc_)), "root/component count mismatch")
        req(sum(len(memberships[int(r)]) for r in roots if memberships[int(r)] is not None) == len(ids), "roots do not partition sample")

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
            req(finite.ndim == 2 and finite.shape[1] == 2 and np.all(np.isfinite(finite)), "invalid ToMATo finite persistence diagram")

        return candidates, {
            "candidate_count": len(candidates),
            "leaf_count": leaf_count,
            "internal_node_count": len(children),
            "root_count": len(roots),
            "finite_persistence_point_count": int(len(finite)),
            "median_radius_degree": float(np.median(degrees)),
            "p90_radius_degree": float(np.quantile(degrees, 0.90)),
            "station_support_total": total_support,
            "station_support_mean_per_event": float(np.mean(w)),
            "station_support_median_per_event": float(np.median(w)),
            "station_density_min": float(np.min(rho)),
            "station_density_median": float(np.median(rho)),
            "station_density_max": float(np.max(rho)),
            "ordinary_density_median_reporting_only": float(np.median(ordinary_rho)),
            "largest_candidate_count": int(counts[0]) if counts else 0,
            "largest_candidate_fraction": float(counts[0] / len(ids)) if counts else 0.0,
            "candidate_rows": sorted(unique.values(), key=lambda r: (-r["member_count"], r["family_hash"])),
        }

    base.topomodal_candidates = station_topomodal_candidates

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
        row["station_weighted_topomodal"] = row.pop("topomodal")
    for pair in d["nested_pairs"]:
        pair["station_weighted_topomodal"] = pair.pop("topomodal")
        pair["station_weighted_topomodal_strict_win"] = pair.pop("topomodal_strict_win")
    s = d["summary"]
    s["station_weighted_topomodal_pooled_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_pooled_fine_to_coarse_mean_best_jaccard")
    s["station_weighted_topomodal_median_bucket_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_median_bucket_fine_to_coarse_mean_best_jaccard")
    s["station_weighted_topomodal_bucket_wins"] = s.pop("topomodal_bucket_wins")
    gate = s["gate"]
    gate["station_weighted_topomodal_nonempty_all_eight"] = gate.pop("topomodal_nonempty_all_eight")
    passed = all(bool(v) for v in gate.values())

    d["schema"] = METHOD
    d["interpretation"] = (
        "SUPPORTS_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE"
        if passed else "REFUTES_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE"
    )
    d["configuration"] = {
        "physical_embedding": "exact_1284_5deg_solar_4deg_radiant_10pct_logspeed",
        "graph": "exact_symmetric_radius_1_physical_graph_including_self_neighborhood",
        "density": "sum_num_stat_in_radius_neighborhood_over_total_subset_num_stat",
        "station_weight": "exact_integer_num_stat_no_transform_no_cap_no_imputation",
        "tomato": "gudhi_3.12_manual_graph_manual_density_complete_hierarchy",
        "min_candidate_support": MIN_SUPPORT,
        "coarse_denominator": 128,
        "fine_denominator": 1024,
        "buckets": [0, 1, 2, 3],
    }
    d["availability_mapping_sha256"] = avail["audited_mapping_sha256"]
    d["availability_source"] = avail["source"]
    d["station_identity_accessed"] = False
    d["station_geography_accessed"] = False
    d["post_result_parameter_search"] = False
    d["historical_1284_controls"] = {
        "pooled_fine_to_coarse_mean_best_jaccard": 0.8067062037,
        "median_bucket_fine_to_coarse_mean_best_jaccard": 0.8129624258,
        "strict_wins_vs_recurrent": 4,
    }
    out = a.output / "STATION_WEIGHTED_TOPOMODAL_SCALE_V1.json"
    out.write_text(json.dumps(d, indent=2, sort_keys=True, allow_nan=False) + "\n")
    legacy.unlink()
    print(json.dumps({"interpretation": d["interpretation"], "summary": d["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
