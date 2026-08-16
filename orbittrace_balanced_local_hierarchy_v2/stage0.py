#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_linkage import label as linkage_label
from hdbscan.hdbscan_ import _tree_to_labels
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree
from scipy.spatial import cKDTree

import run_development as parent

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
K = 10
MIN_CLUSTER_SIZE = 10
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family_id(event_ids: list[str]) -> str:
    return hashlib.sha256(("BLH2|" + "|".join(event_ids)).encode()).hexdigest()[:20]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support result changed")
    req(K == 10 and MIN_CLUSTER_SIZE == 10, "inherited constants changed")

    qmod = parent.load_module(a.quality_source, "blh2_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-balanced-local-hierarchy-v2-stage0-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict]] = {}
    X_by_year: dict[int, np.ndarray] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year}")
        req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in rows), f"protected event survived {year}")
        req(len({str(e["id"]) for e in rows}) == len(rows), f"duplicate IDs {year}")
        events_by_year[year] = rows
        X_by_year[year] = parent.geo_matrix(rows)

    e22, e23 = events_by_year[2022], events_by_year[2023]
    X22, X23 = X_by_year[2022], X_by_year[2023]
    n22, n23 = len(e22), len(e23)
    total_n = n22 + n23
    req(total_n == 738682, f"accessible event count changed: {total_n}")
    all_events = e22 + e23

    t22, t23 = cKDTree(X22), cKDTree(X23)
    d22, _ = t22.query(X22, k=[K + 1], workers=1)
    d23, _ = t23.query(X23, k=[K + 1], workers=1)
    r22 = np.asarray(d22[:, 0], dtype=np.float64)
    r23 = np.asarray(d23[:, 0], dtype=np.float64)
    req(np.all(np.isfinite(r22)) and np.all(r22 > 0.0), "invalid 2022 local scale")
    req(np.all(np.isfinite(r23)) and np.all(r23 > 0.0), "invalid 2023 local scale")

    d22to23, i22to23 = t23.query(X22, k=K, workers=1)
    _d23to22, i23to22 = t22.query(X23, k=K, workers=1)
    d22to23 = np.asarray(d22to23, dtype=np.float64)
    i22to23 = np.asarray(i22to23, dtype=np.int64)
    i23to22 = np.asarray(i23to22, dtype=np.int64)
    req(d22to23.shape == (n22, K) and i22to23.shape == (n22, K), "22->23 query shape changed")
    req(i23to22.shape == (n23, K), "23->22 query shape changed")

    edge_i_parts: list[np.ndarray] = []
    edge_j_parts: list[np.ndarray] = []
    edge_s_parts: list[np.ndarray] = []
    reciprocal_edges = 0
    chunk = 25000
    for start in range(0, n22, chunk):
        stop = min(n22, start + chunk)
        js = i22to23[start:stop]
        ds = d22to23[start:stop]
        ii3 = np.arange(start, stop, dtype=np.int64)[:, None, None]
        reciprocal = np.any(i23to22[js] == ii3, axis=2)
        reciprocal_edges += int(reciprocal.sum())
        scale = np.sqrt(r22[start:stop, None] * r23[js])
        s = ds / scale
        req(np.all(np.isfinite(s)) and np.all(s > 0.0), "invalid reciprocal local-scale distance")
        if np.any(reciprocal):
            rr, cc = np.nonzero(reciprocal)
            edge_i_parts.append((rr + start).astype(np.int64, copy=False))
            edge_j_parts.append(js[rr, cc].astype(np.int64, copy=False))
            edge_s_parts.append(s[rr, cc].astype(np.float64, copy=False))

    req(reciprocal_edges > 0, "no reciprocal cross-year edges")
    edge_i = np.concatenate(edge_i_parts)
    edge_j = np.concatenate(edge_j_parts)
    edge_s = np.concatenate(edge_s_parts)
    req(len(edge_i) == reciprocal_edges == len(edge_j) == len(edge_s), "reciprocal edge accounting mismatch")
    req(np.all(np.isfinite(edge_s)) and np.all(edge_s > 0.0), "invalid stored edge distances")

    rows = np.concatenate((edge_i, n22 + edge_j))
    cols = np.concatenate((n22 + edge_j, edge_i))
    vals = np.concatenate((edge_s, edge_s))
    graph = coo_matrix((vals, (rows, cols)), shape=(total_n, total_n)).tocsr()
    raw_components, raw_labels = connected_components(graph, directed=False, return_labels=True)
    raw_labels = np.asarray(raw_labels, dtype=np.int64)
    req(raw_components >= 2, "reciprocal graph unexpectedly single-component")

    forest = minimum_spanning_tree(graph).tocoo()
    mst_u = np.asarray(forest.row, dtype=np.int64)
    mst_v = np.asarray(forest.col, dtype=np.int64)
    mst_w = np.asarray(forest.data, dtype=np.float64)
    req(len(mst_u) == total_n - raw_components, f"MST forest edge count changed: {len(mst_u)} vs {total_n-raw_components}")
    req(np.all(np.isfinite(mst_w)) and np.all(mst_w > 0.0), "invalid finite MST weights")

    # Deterministic virtual lambda=0 joins between disconnected reciprocal components.
    reps = np.full(raw_components, total_n, dtype=np.int64)
    np.minimum.at(reps, raw_labels, np.arange(total_n, dtype=np.int64))
    req(np.all(reps < total_n), "missing reciprocal-component representative")
    reps.sort()
    virt_u = reps[:-1]
    virt_v = reps[1:]
    virt_w = np.full(raw_components - 1, np.inf, dtype=np.float64)

    u = np.concatenate((mst_u, virt_u))
    v = np.concatenate((mst_v, virt_v))
    w = np.concatenate((mst_w, virt_w))
    req(len(u) == total_n - 1, "global spanning edge list is not N-1")
    lo = np.minimum(u, v)
    hi = np.maximum(u, v)
    order = np.lexsort((hi, lo, w))
    edge_list = np.column_stack((lo[order], hi[order], w[order])).astype(np.float64, copy=False)

    single_linkage = linkage_label(edge_list)
    req(single_linkage.shape == (total_n - 1, 4), f"single-linkage shape changed: {single_linkage.shape}")
    labels, _probs, cluster_persistence, _condensed, _single = _tree_to_labels(
        np.empty((total_n, 1), dtype=np.float64),
        single_linkage,
        min_cluster_size=MIN_CLUSTER_SIZE,
        cluster_selection_method="eom",
        allow_single_cluster=False,
        match_reference_implementation=False,
        cluster_selection_epsilon=0.0,
        cluster_selection_persistence=0.0,
        max_cluster_size=0,
        cluster_selection_epsilon_max=float("inf"),
    )
    labels = np.asarray(labels, dtype=np.int64)
    cluster_persistence = np.asarray(cluster_persistence, dtype=np.float64)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(cluster_persistence))), "flat cluster labels/persistence no longer contiguous")
    req(np.all(np.isfinite(cluster_persistence)) and np.all(cluster_persistence >= 0.0), "invalid cluster persistence")

    candidates: list[dict] = []
    assigned = 0
    largest = 0
    for lab in positive:
        idx = np.flatnonzero(labels == lab)
        req(len(idx) >= MIN_CLUSTER_SIZE, "selected cluster below frozen min size")
        ids = sorted(str(all_events[int(i)]["id"]) for i in idx)
        n_a = int(np.sum(idx < n22))
        n_b = len(idx) - n_a
        req(n_a > 0 and n_b > 0, "selected cluster lacks cross-year recurrence")
        n = len(idx)
        assigned += n
        largest = max(largest, n)
        balance = 2.0 * min(n_a, n_b) / n
        candidates.append({
            "family_id": family_id(ids),
            "event_ids": ids,
            "member_count": n,
            "n_2022": n_a,
            "n_2023": n_b,
            "min_year_support": min(n_a, n_b),
            "cross_year_balance": balance,
            "cluster_persistence": float(cluster_persistence[lab]),
        })

    candidates.sort(key=lambda f: (
        -float(f["cluster_persistence"]),
        -int(f["min_year_support"]),
        -float(f["cross_year_balance"]),
        -int(f["member_count"]),
        str(f["family_id"]),
    ))
    candidate_count = len(candidates)
    largest_fraction_all = largest / total_n if total_n else 1.0
    largest_fraction_assigned = largest / assigned if assigned else 1.0
    gates = {
        "at_least_100_candidates": candidate_count >= 100,
        "largest_at_most_1pct_all_events": largest_fraction_all <= 0.01,
        "largest_at_most_5pct_assigned_events": largest_fraction_assigned <= 0.05,
        "finite_reciprocal_edges_present": reciprocal_edges > 0,
        "multiple_raw_reciprocal_components": raw_components >= 2,
    }
    passed = all(gates.values())
    verdict = "PASS_BALANCED_LOCAL_HIERARCHY_V2_STAGE0" if passed else "FAIL_BALANCED_LOCAL_HIERARCHY_V2_STAGE0"

    ordered_hash = hashlib.sha256()
    for rank, f in enumerate(candidates, 1):
        ordered_hash.update(str(rank).encode())
        ordered_hash.update(b"\0")
        ordered_hash.update(str(f["family_id"]).encode())
        ordered_hash.update(b"\0")
        for eid in f["event_ids"]:
            ordered_hash.update(str(eid).encode())
            ordered_hash.update(b"\0")
        ordered_hash.update(b"\n")

    result = {
        "verdict": verdict,
        "scientific_role": "LABEL_FREE_TARGET_EXCLUDED_GMN_STAGE0_ONLY",
        "k": K,
        "minimum_cluster_size": MIN_CLUSTER_SIZE,
        "hard_local_scale_edge_threshold": None,
        "eom_selection": True,
        "allow_single_cluster": False,
        "events_total": total_n,
        "events_by_year": {"2022": n22, "2023": n23},
        "reciprocal_edges": reciprocal_edges,
        "raw_reciprocal_graph_components": int(raw_components),
        "finite_mst_forest_edges": int(len(mst_u)),
        "virtual_infinite_root_edges": int(len(virt_u)),
        "candidate_count": candidate_count,
        "assigned_candidate_events": assigned,
        "largest_candidate_members": largest,
        "largest_candidate_fraction_all_events": largest_fraction_all,
        "largest_candidate_fraction_assigned_events": largest_fraction_assigned,
        "ordered_membership_sha256": ordered_hash.hexdigest(),
        "structural_gates": gates,
        "candidates": candidates,
        "known_shower_labels_indexed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "BALANCED_LOCAL_HIERARCHY_V2_STAGE0.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({k: result[k] for k in (
        "verdict", "events_total", "reciprocal_edges", "raw_reciprocal_graph_components",
        "finite_mst_forest_edges", "virtual_infinite_root_edges", "candidate_count",
        "assigned_candidate_events", "largest_candidate_members",
        "largest_candidate_fraction_all_events", "largest_candidate_fraction_assigned_events",
    )}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
