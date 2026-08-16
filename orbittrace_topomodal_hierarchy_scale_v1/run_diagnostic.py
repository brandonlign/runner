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
from gudhi.clustering.tomato import Tomato

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
RADIUS = 1.0
H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)


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


def physical_embedding(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([float(e["sol"]) for e in events], dtype=float))
    lon = np.radians(np.asarray([float(e["lon"]) for e in events], dtype=float))
    lat = np.radians(np.asarray([float(e["lat"]) for e in events], dtype=float))
    vg = np.asarray([float(e["vg"]) for e in events], dtype=float)
    req(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    clat = np.cos(lat)
    Z = np.column_stack(
        [
            np.cos(sol) / H_SOL,
            np.sin(sol) / H_SOL,
            clat * np.cos(lon) / H_RAD,
            clat * np.sin(lon) / H_RAD,
            np.sin(lat) / H_RAD,
            np.log(vg) / H_LOGV,
        ]
    ).astype(float)
    req(Z.shape == (len(events), 6) and np.all(np.isfinite(Z)), "invalid physical embedding")
    return Z


def topomodal_candidates(events: list[dict[str, Any]]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = physical_embedding(ordered)

    tree = cKDTree(Z)
    raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw_neighbors]
    req(len(neighbors) == len(ids), "radius graph row count changed")
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing from radius graph at {i}")
        for j in row:
            req(0 <= j < len(ids), "radius graph index out of range")
    # cKDTree radius neighborhoods are symmetric at eps=0; verify exactly.
    adjacency = [set(row) for row in neighbors]
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")

    degrees = np.asarray([len(row) for row in neighbors], dtype=float)
    rho = degrees / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid radius-count density")

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
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid ToMATo children at node {node}: {a},{b}")
        req(parent[a] == -1 and parent[b] == -1, "ToMATo hierarchy node has multiple parents")
        ma = memberships[a]
        mb = memberships[b]
        req(ma is not None and mb is not None, "ToMATo child membership missing")
        req(ma.isdisjoint(mb), "ToMATo child memberships overlap")
        memberships[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == len(np.asarray(model.max_weight_per_cc_)), "ToMATo root/component count mismatch")
    req(sum(len(memberships[int(r)]) for r in roots if memberships[int(r)] is not None) == len(ids), "ToMATo roots do not partition sample")

    unique: dict[frozenset[str], dict[str, Any]] = {}
    for node, members in enumerate(memberships):
        req(members is not None, f"missing ToMATo membership node {node}")
        if len(members) < MIN_SUPPORT:
            continue
        unique.setdefault(
            members,
            {
                "family_hash": member_hash(members),
                "member_count": len(members),
                "first_node": int(node),
                "is_root": bool(parent[node] == -1),
            },
        )
    candidates = list(unique.keys())
    counts = sorted((len(c) for c in candidates), reverse=True)
    finite_persistence = np.asarray(model.diagram_, dtype=float)
    if finite_persistence.size:
        req(finite_persistence.ndim == 2 and finite_persistence.shape[1] == 2 and np.all(np.isfinite(finite_persistence)), "invalid ToMATo finite persistence diagram")
    return candidates, {
        "candidate_count": len(candidates),
        "leaf_count": leaf_count,
        "internal_node_count": len(children),
        "root_count": len(roots),
        "finite_persistence_point_count": int(len(finite_persistence)),
        "median_radius_degree": float(np.median(degrees)),
        "p90_radius_degree": float(np.quantile(degrees, 0.90)),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(ids)) if counts else 0.0,
        "candidate_rows": sorted(unique.values(), key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def recurrent_candidates(parent_runner: Any, X: np.ndarray, years: np.ndarray, event_ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
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
        ix = np.flatnonzero(labels == lab)
        members = frozenset(event_ids[int(i)] for i in ix)
        req(len(members) >= 10, "recurrent comparator sub-10 membership")
        candidates.append(members)
        rows.append({"family_hash": member_hash(members), "member_count": len(members)})
    counts = sorted((len(c) for c in candidates), reverse=True)
    return candidates, {
        "candidate_count": len(candidates),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(event_ids)) if counts else 0.0,
        "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def restrict_and_dedupe(coarse: list[frozenset[str]], fine_universe: frozenset[str]) -> list[frozenset[str]]:
    out: list[frozenset[str]] = []
    seen: set[tuple[str, ...]] = set()
    for c in coarse:
        r = frozenset(c.intersection(fine_universe))
        if len(r) < MIN_SUPPORT:
            continue
        key = tuple(sorted(r))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def directional(source: list[frozenset[str]], target: list[frozenset[str]]) -> tuple[list[float], int]:
    vals: list[float] = []
    exact = 0
    for a in source:
        best = 0.0
        exact_here = False
        for b in target:
            inter = len(a.intersection(b))
            if inter:
                best = max(best, float(inter / len(a.union(b))))
            exact_here = exact_here or (a == b)
        vals.append(best)
        exact += int(exact_here)
    return vals, exact


def cross_scale_metrics(coarse: list[frozenset[str]], fine: list[frozenset[str]], fine_universe: frozenset[str]) -> dict[str, Any]:
    restricted = restrict_and_dedupe(coarse, fine_universe)
    fine_scores, fine_exact = directional(fine, restricted)
    reverse_scores, reverse_exact = directional(restricted, fine)
    f = np.asarray(fine_scores, dtype=float)
    r = np.asarray(reverse_scores, dtype=float)
    return {
        "fine_candidate_count": len(fine),
        "restricted_coarse_candidate_count": len(restricted),
        "fine_to_coarse_mean_best_jaccard": float(np.mean(f)) if len(f) else 0.0,
        "fine_to_coarse_median_best_jaccard": float(np.median(f)) if len(f) else 0.0,
        "fine_to_coarse_exact_fraction": float(fine_exact / len(fine)) if fine else 0.0,
        "coarse_to_fine_mean_best_jaccard_reporting": float(np.mean(r)) if len(r) else 0.0,
        "coarse_to_fine_exact_fraction_reporting": float(reverse_exact / len(restricted)) if restricted else 0.0,
        "fine_to_coarse_scores": [float(x) for x in f],
        "coarse_to_fine_scores_reporting": [float(x) for x in r],
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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent_runner = load_module(a.parent_runner, "topomodal_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "topomodal_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-hierarchy-scale-v1-target-excluded"
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
        norm = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    Xfull = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    fits: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[topomodal] d={denominator} b={bucket} n={len(ids)}", flush=True)
            topo, topo_summary = topomodal_candidates(sub_events)
            recurrent, recurrent_summary = recurrent_candidates(parent_runner, X, years, ids)
            fits[(denominator, bucket)] = {
                "ids": frozenset(ids),
                "topo": topo,
                "recurrent": recurrent,
                "row": {
                    "denominator": denominator,
                    "bucket": bucket,
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "topomodal": topo_summary,
                    "recurrent_eom": recurrent_summary,
                },
            }
            print(json.dumps(fits[(denominator, bucket)]["row"], sort_keys=True), flush=True)

    pairs = []
    topo_means: list[float] = []
    recurrent_means: list[float] = []
    topo_all_scores: list[float] = []
    recurrent_all_scores: list[float] = []
    wins = 0
    nonempty_all = True
    noncollapse_all = True

    for bucket in BUCKETS:
        coarse = fits[(COARSE_D, bucket)]
        fine = fits[(FINE_D, bucket)]
        req(fine["ids"].issubset(coarse["ids"]), f"nested subset failed bucket {bucket}")
        tm = cross_scale_metrics(coarse["topo"], fine["topo"], fine["ids"])
        rm = cross_scale_metrics(coarse["recurrent"], fine["recurrent"], fine["ids"])
        ts = float(tm["fine_to_coarse_mean_best_jaccard"])
        rs = float(rm["fine_to_coarse_mean_best_jaccard"])
        topo_means.append(ts)
        recurrent_means.append(rs)
        topo_all_scores.extend(tm["fine_to_coarse_scores"])
        recurrent_all_scores.extend(rm["fine_to_coarse_scores"])
        win = ts > rs
        wins += int(win)
        nonempty = len(coarse["topo"]) > 0 and len(fine["topo"]) > 0
        nonempty_all = nonempty_all and nonempty
        noncollapse = int(tm["fine_candidate_count"]) >= int(rm["fine_candidate_count"])
        noncollapse_all = noncollapse_all and noncollapse
        pairs.append(
            {
                "bucket": bucket,
                "topomodal": tm,
                "recurrent_eom": rm,
                "topomodal_strict_win": bool(win),
                "fine_candidate_noncollapse": bool(noncollapse),
            }
        )

    topo_pool = float(np.mean(np.asarray(topo_all_scores, dtype=float))) if topo_all_scores else 0.0
    recurrent_pool = float(np.mean(np.asarray(recurrent_all_scores, dtype=float))) if recurrent_all_scores else 0.0
    topo_median_bucket = float(np.median(np.asarray(topo_means, dtype=float)))
    recurrent_median_bucket = float(np.median(np.asarray(recurrent_means, dtype=float)))
    gate = {
        "topomodal_nonempty_all_eight": bool(nonempty_all),
        "fine_candidate_noncollapse_all_four": bool(noncollapse_all),
        "pooled_fine_to_coarse_mean_jaccard_strictly_better": topo_pool > recurrent_pool,
        "median_bucket_fine_to_coarse_mean_jaccard_strictly_better": topo_median_bucket > recurrent_median_bucket,
        "bucket_wins_at_least_three_of_four": wins >= 3,
    }
    interpretation = (
        "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE"
        if all(gate.values())
        else "REFUTES_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE"
    )
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_HIERARCHY_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "configuration": {
            "solar_halfwidth_deg": 5.0,
            "radiant_scale_deg": 4.0,
            "speed_multiplicative_scale": 1.1,
            "radius": RADIUS,
            "density": "radius_count_divided_by_subset_n",
            "hierarchy": "complete_tomato_leaf_and_merge_node_memberships",
            "min_candidate_support": MIN_SUPPORT,
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
        },
        "fits": [fits[(d, b)]["row"] for d in (COARSE_D, FINE_D) for b in BUCKETS],
        "nested_pairs": pairs,
        "summary": {
            "topomodal_pooled_fine_to_coarse_mean_best_jaccard": topo_pool,
            "recurrent_eom_pooled_fine_to_coarse_mean_best_jaccard": recurrent_pool,
            "topomodal_median_bucket_fine_to_coarse_mean_best_jaccard": topo_median_bucket,
            "recurrent_eom_median_bucket_fine_to_coarse_mean_best_jaccard": recurrent_median_bucket,
            "topomodal_bucket_wins": wins,
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
    out = a.output / "TOPOMODAL_HIERARCHY_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "pairs": pairs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
