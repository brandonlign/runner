#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
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
    return hashlib.sha256(("BLG1|" + "|".join(event_ids)).encode()).hexdigest()[:20]


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
    req(K == 10 and MIN_CLUSTER_SIZE == 10, "frozen inherited k/min-cluster changed")

    qmod = parent.load_module(a.quality_source, "blg1_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-balanced-local-graph-v1-stage0-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict]] = {}
    X_by_year: dict[int, np.ndarray] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"normalization changed event count {year}")
        req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in rows), f"protected event survived {year}")
        req(len({str(e["id"]) for e in rows}) == len(rows), f"duplicate IDs within {year}")
        events_by_year[year] = rows
        X_by_year[year] = parent.geo_matrix(rows)

    e22, e23 = events_by_year[2022], events_by_year[2023]
    X22, X23 = X_by_year[2022], X_by_year[2023]
    n22, n23 = len(e22), len(e23)
    total_n = n22 + n23
    req(total_n == 738682, f"accessible pooled event count changed: {total_n}")
    req(not ({str(e["id"]) for e in e22} & {str(e["id"]) for e in e23}), "cross-year duplicate IDs")

    t22, t23 = cKDTree(X22), cKDTree(X23)
    # Self is the nearest same-year point; column 11 is the 10th other neighbour.
    d22, _ = t22.query(X22, k=[K + 1], workers=-1)
    d23self, _ = t23.query(X23, k=[K + 1], workers=-1)
    r22 = np.asarray(d22[:, 0], dtype=np.float64)
    r23 = np.asarray(d23self[:, 0], dtype=np.float64)
    req(np.all(np.isfinite(r22)) and np.all(r22 > 0.0), "invalid 2022 local scale")
    req(np.all(np.isfinite(r23)) and np.all(r23 > 0.0), "invalid 2023 local scale")

    # Exact ordinary-GEO6 top-k across years in both directions.
    d22to23, i22to23 = t23.query(X22, k=K, workers=-1)
    d23to22, i23to22 = t22.query(X23, k=K, workers=-1)
    d22to23 = np.asarray(d22to23, dtype=np.float64)
    i22to23 = np.asarray(i22to23, dtype=np.int64)
    i23to22 = np.asarray(i23to22, dtype=np.int64)
    req(d22to23.shape == (n22, K) and i22to23.shape == (n22, K), "cross-year 22->23 query shape changed")
    req(i23to22.shape == (n23, K), "cross-year 23->22 query shape changed")

    edge_i_parts: list[np.ndarray] = []
    edge_j_parts: list[np.ndarray] = []
    reciprocal_edges = 0
    retained_edges = 0
    rejected_by_scale = 0
    chunk = 25000
    for start in range(0, n22, chunk):
        stop = min(n22, start + chunk)
        js = i22to23[start:stop]
        ds = d22to23[start:stop]
        ii = np.arange(start, stop, dtype=np.int64)[:, None, None]
        reciprocal = np.any(i23to22[js] == ii, axis=2)
        reciprocal_edges += int(reciprocal.sum())
        scale = np.sqrt(r22[start:stop, None] * r23[js])
        s = ds / scale
        req(np.all(np.isfinite(s)) and np.all(s >= 0.0), "invalid local-scale edge value")
        keep = reciprocal & (s <= 1.0)
        retained_edges += int(keep.sum())
        rejected_by_scale += int((reciprocal & (s > 1.0)).sum())
        if np.any(keep):
            row_local, col_local = np.nonzero(keep)
            edge_i_parts.append((row_local + start).astype(np.int64, copy=False))
            edge_j_parts.append(js[row_local, col_local].astype(np.int64, copy=False))

    req(reciprocal_edges > 0, "no reciprocal cross-year edges")
    req(retained_edges > 0, "no locally retained cross-year edges")
    req(rejected_by_scale > 0, "local-scale gate is vacuous; no reciprocal edge rejected")
    edge_i = np.concatenate(edge_i_parts) if edge_i_parts else np.empty(0, dtype=np.int64)
    edge_j = np.concatenate(edge_j_parts) if edge_j_parts else np.empty(0, dtype=np.int64)
    req(len(edge_i) == retained_edges == len(edge_j), "retained-edge accounting mismatch")

    rows = np.concatenate((edge_i, n22 + edge_j))
    cols = np.concatenate((n22 + edge_j, edge_i))
    data = np.ones(rows.shape[0], dtype=np.uint8)
    graph = coo_matrix((data, (rows, cols)), shape=(total_n, total_n)).tocsr()
    n_components, labels = connected_components(graph, directed=False, return_labels=True)
    labels = np.asarray(labels, dtype=np.int64)
    req(labels.shape == (total_n,), "component label shape changed")

    size = np.bincount(labels, minlength=n_components).astype(np.int64)
    c22 = np.bincount(labels[:n22], minlength=n_components).astype(np.int64)
    c23 = np.bincount(labels[n22:], minlength=n_components).astype(np.int64)
    retained_component_ids = np.flatnonzero(size >= MIN_CLUSTER_SIZE)

    all_events = e22 + e23
    candidates: list[dict] = []
    assigned = 0
    largest = 0
    for cid in retained_component_ids.tolist():
        idx = np.flatnonzero(labels == cid)
        ids = sorted(str(all_events[int(i)]["id"]) for i in idx)
        n_a, n_b = int(c22[cid]), int(c23[cid])
        req(n_a > 0 and n_b > 0, "bipartite retained component lost one year")
        n = len(ids)
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
        })

    candidates.sort(key=lambda f: (
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
        "scale_gate_nonvacuous_retain": retained_edges > 0,
        "scale_gate_nonvacuous_reject": rejected_by_scale > 0,
    }
    passed = all(gates.values())
    verdict = "PASS_BALANCED_LOCAL_GRAPH_V1_STAGE0" if passed else "FAIL_BALANCED_LOCAL_GRAPH_V1_STAGE0"

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
        "local_scale_threshold": 1.0,
        "minimum_cluster_size": MIN_CLUSTER_SIZE,
        "events_total": total_n,
        "events_by_year": {"2022": n22, "2023": n23},
        "reciprocal_edges": reciprocal_edges,
        "retained_edges": retained_edges,
        "rejected_reciprocal_edges_by_scale": rejected_by_scale,
        "raw_graph_component_count": int(n_components),
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
    out = a.output / "BALANCED_LOCAL_GRAPH_V1_STAGE0.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in (
        "verdict", "events_total", "reciprocal_edges", "retained_edges",
        "rejected_reciprocal_edges_by_scale", "raw_graph_component_count",
        "candidate_count", "assigned_candidate_events", "largest_candidate_members",
        "largest_candidate_fraction_all_events", "largest_candidate_fraction_assigned_events",
    )}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
