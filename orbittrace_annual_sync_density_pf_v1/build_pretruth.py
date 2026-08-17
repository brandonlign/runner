#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree
from persistable import FilteredGraph

YEARS = (2022, 2023)
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
BLIND = (20.0, 55.0)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
RADIUS = 1.0
MIN_SUPPORT = 4
EXPECTED_EVENTS = 738682
ENDPOINT_PRELABEL_SHA256 = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
PERSISTABLE_COMMIT = "7eb75b2e8d2fe5a18e49248aa7d1c97f829415be"
PERSISTABLE_SOURCE_BLOB = "f88f64d663862b4577bb40e5796c6dc47391094b"
PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_K = {
    (128, 0): 29, (128, 1): 35, (128, 2): 38, (128, 3): 33,
    (1024, 0): 8, (1024, 1): 5, (1024, 2): 6, (1024, 3): 9,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def membership_hash(ids: list[str] | tuple[str, ...]) -> str:
    vals = tuple(sorted(str(x) for x in ids))
    return hashlib.sha256(("\n".join(vals) + "\n").encode()).hexdigest()


def canonical_clusters(labels: np.ndarray, ids: list[str]) -> list[tuple[str, ...]]:
    out: list[tuple[str, ...]] = []
    labs = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    for lab in labs:
        members = tuple(sorted(ids[i] for i in np.flatnonzero(labels == lab)))
        out.append(members)
    return out


def canonical_hashes(clusters: list[tuple[str, ...]]) -> list[str]:
    return sorted(membership_hash(c) for c in clusters)


def build_graph(parent: Any, events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "panel lost a year")
    x = np.asarray(parent.geo_matrix(ordered), dtype=float)
    req(x.shape == (len(ids), 6) and np.all(np.isfinite(x)), "invalid GEO6 matrix")
    tree = cKDTree(x)
    raw = tree.query_ball_point(x, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing at {i}")
        req(all(i in adjacency[j] for j in row), "radius graph not symmetric")

    n22 = int(np.sum(years == 2022))
    n23 = int(np.sum(years == 2023))
    req(n22 > 0 and n23 > 0, "empty annual panel")
    d22 = np.asarray([sum(years[j] == 2022 for j in row) for row in neighbors], dtype=np.int64)
    d23 = np.asarray([sum(years[j] == 2023 for j in row) for row in neighbors], dtype=np.int64)
    rho22 = d22.astype(float) / float(n22)
    rho23 = d23.astype(float) / float(n23)
    rho_sync = np.minimum(rho22, rho23)
    swapped = np.minimum(rho23, rho22)
    req(np.array_equal(rho_sync, swapped), "year-swap invariance failed at density coordinate")
    vertex_values = -rho_sync

    edge_list: list[tuple[int, int]] = []
    for i, row in enumerate(neighbors):
        for j in row:
            if i < j:
                edge_list.append((i, j))
    edge_list.sort()
    if edge_list:
        edges = np.asarray(edge_list, dtype=np.int64)
        edge_values = np.maximum(vertex_values[edges[:, 0]], vertex_values[edges[:, 1]])
    else:
        edges = np.empty((0, 2), dtype=np.int64)
        edge_values = np.empty((0,), dtype=float)
    req(np.all(np.isfinite(vertex_values)) and np.all(np.isfinite(edge_values)), "nonfinite filtration")
    if len(edges):
        req(np.all(vertex_values[edges[:, 0]] <= edge_values) and np.all(vertex_values[edges[:, 1]] <= edge_values), "invalid filtered graph")
    return {
        "ordered": ordered,
        "ids": ids,
        "years": years,
        "neighbors": neighbors,
        "edges": edges,
        "edge_values": edge_values,
        "vertex_values": vertex_values,
        "rho_sync": rho_sync,
        "n22": n22,
        "n23": n23,
        "d22": d22,
        "d23": d23,
    }


def is_connected(indices: np.ndarray, neighbors: list[list[int]]) -> bool:
    if len(indices) == 0:
        return False
    allowed = set(int(x) for x in indices)
    start = int(indices[0])
    stack = [start]
    seen = {start}
    while stack:
        i = stack.pop()
        for j in neighbors[i]:
            jj = int(j)
            if jj in allowed and jj not in seen:
                seen.add(jj)
                stack.append(jj)
    return len(seen) == len(allowed)


def candidate_rows(labels: np.ndarray, graph: dict[str, Any]) -> list[dict[str, Any]]:
    ids = graph["ids"]
    vv = graph["vertex_values"]
    edges = graph["edges"]
    ev = graph["edge_values"]
    labs = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    boundary: dict[int, float] = {lab: 0.0 for lab in labs}
    has_boundary: dict[int, bool] = {lab: False for lab in labs}
    for k in range(len(edges)):
        i, j = int(edges[k, 0]), int(edges[k, 1])
        li, lj = int(labels[i]), int(labels[j])
        if li == lj:
            continue
        val = float(ev[k])
        if li >= 0:
            if not has_boundary[li] or val < boundary[li]:
                boundary[li] = val
                has_boundary[li] = True
        if lj >= 0:
            if not has_boundary[lj] or val < boundary[lj]:
                boundary[lj] = val
                has_boundary[lj] = True

    rows: list[dict[str, Any]] = []
    for lab in labs:
        ix = np.flatnonzero(labels == lab)
        members = [ids[int(i)] for i in ix]
        birth = float(np.min(vv[ix]))
        death = float(boundary[lab]) if has_boundary[lab] else 0.0
        prominence = float(death - birth)
        req(math.isfinite(birth) and math.isfinite(death) and math.isfinite(prominence), "nonfinite prominence")
        req(prominence >= -1e-15, "negative prominence")
        if prominence < 0.0:
            prominence = 0.0
        rows.append({
            "raw_label": lab,
            "family_hash": membership_hash(members),
            "member_count": len(members),
            "birth_filtration": birth,
            "boundary_filtration": death,
            "prominence": prominence,
            "event_ids": sorted(members),
            "connected": bool(is_connected(ix, graph["neighbors"])),
        })
    rows.sort(key=lambda r: (-float(r["prominence"]), -int(r["member_count"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def restrict_and_dedupe(candidates: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    seen: set[tuple[str, ...]] = set()
    out: list[frozenset[str]] = []
    for row in candidates:
        members = tuple(sorted(set(str(x) for x in row["event_ids"]) & universe))
        if len(members) < MIN_SUPPORT or members in seen:
            continue
        seen.add(members)
        out.append(frozenset(members))
    return out


def mean_best_jaccard(fine: list[dict[str, Any]], coarse: list[dict[str, Any]], fine_universe: set[str]) -> float:
    restricted = restrict_and_dedupe(coarse, fine_universe)
    if not fine:
        return 0.0
    vals: list[float] = []
    for row in fine:
        a = frozenset(str(x) for x in row["event_ids"])
        best = 0.0
        for b in restricted:
            inter = len(a & b)
            if inter:
                best = max(best, inter / len(a | b))
        vals.append(float(best))
    return float(np.mean(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--persistable-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.endpoint_prelabel) == ENDPOINT_PRELABEL_SHA256, "endpoint prelabel changed")
    req(git_blob(a.parent_runner) == PARENT_SOURCE_BLOB, "parent source changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == V8_SHA256, "GMN support artifact changed")
    req(git_blob(a.persistable_source) == PERSISTABLE_SOURCE_BLOB, "Persistable source changed")

    endpoint = json.loads(a.endpoint_prelabel.read_text())
    req(endpoint["schema"] == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong endpoint schema")
    req(endpoint["scientific_role"] == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong endpoint role")
    req(endpoint["shower_truth_used"] is False, "endpoint prelabel used truth")
    req(endpoint["target_information_access"] is False and endpoint["target_region_events_accessed"] is False, "endpoint firewall")
    subset_map = {(int(s["denominator"]), int(s["bucket"])): s for s in endpoint["subsets"]}
    req(set(subset_map) == set(EXPECTED_K), "wrong endpoint panels")
    for key, k in EXPECTED_K.items():
        s = subset_map[key]
        req(int(s["equal_budget_k"]) == k and len(s["recurrent_candidates"]) == k, f"K/comparator changed {key}")

    parent = load_module(a.parent_runner, "sync_pf_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    qmod = load_module(a.quality_source, "sync_pf_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-annual-sync-density-pf-v1-zero-label"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    del hidden_sealed
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source set changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == EXPECTED_EVENTS, "target-excluded event count changed")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")
    event_by_id = {str(e["id"]): e for e in events}

    panel_rows: list[dict[str, Any]] = []
    panel_gate_state: dict[tuple[int, int], dict[str, bool]] = {}

    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            key = (denominator, bucket)
            frozen = subset_map[key]
            k = EXPECTED_K[key]
            annual_ids = {str(y): [str(x) for x in frozen["annual_event_ids"][str(y)]] for y in YEARS}
            panel_ids = set(annual_ids["2022"]) | set(annual_ids["2023"])
            req(len(panel_ids) == int(frozen["event_count"]), f"event count mismatch {key}")
            req(panel_ids.issubset(event_by_id), f"missing panel events {key}")
            panel_events = [event_by_id[eid] for eid in panel_ids]
            graph = build_graph(parent, panel_events)
            req(set(graph["ids"]) == panel_ids, f"graph universe changed {key}")

            fg = FilteredGraph(
                graph["vertex_values"], graph["edges"], graph["edge_values"],
                start=float(np.min(graph["vertex_values"])), end=0.0,
            )
            error: str | None = None
            try:
                labels1 = np.asarray(fg.persistence_based_flattening(k, flattening_mode="conservative", keep_low_persistence_clusters=False), dtype=np.int64)
                labels2 = np.asarray(fg.persistence_based_flattening(k, flattening_mode="conservative", keep_low_persistence_clusters=False), dtype=np.int64)
                swapped_v = -np.minimum(
                    graph["d23"].astype(float) / float(graph["n23"]),
                    graph["d22"].astype(float) / float(graph["n22"]),
                )
                req(np.array_equal(swapped_v, graph["vertex_values"]), "year-swap filtration changed")
                swapped_ev = np.maximum(swapped_v[graph["edges"][:, 0]], swapped_v[graph["edges"][:, 1]]) if len(graph["edges"]) else np.empty((0,), dtype=float)
                fg_swap = FilteredGraph(swapped_v, graph["edges"], swapped_ev, start=float(np.min(swapped_v)), end=0.0)
                labels_swap = np.asarray(fg_swap.persistence_based_flattening(k, flattening_mode="conservative", keep_low_persistence_clusters=False), dtype=np.int64)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                labels1 = np.full(len(graph["ids"]), -1, dtype=np.int64)
                labels2 = labels1.copy()
                labels_swap = labels1.copy()

            clusters1 = canonical_clusters(labels1, graph["ids"])
            clusters2 = canonical_clusters(labels2, graph["ids"])
            clusters_swap = canonical_clusters(labels_swap, graph["ids"])
            rows = candidate_rows(labels1, graph) if error is None else []

            pairwise_disjoint = True
            seen_events: set[str] = set()
            for r in rows:
                m = set(str(x) for x in r["event_ids"])
                if seen_events & m:
                    pairwise_disjoint = False
                    break
                seen_events.update(m)

            gates = {
                "returned_exact_k": error is None and len(rows) == k,
                "support_floor": error is None and len(rows) == k and all(int(r["member_count"]) >= MIN_SUPPORT for r in rows),
                "pairwise_disjoint": error is None and pairwise_disjoint,
                "membership_universe": error is None and all(set(str(x) for x in r["event_ids"]).issubset(panel_ids) for r in rows),
                "graph_connectivity": error is None and all(bool(r["connected"]) for r in rows),
                "deterministic_repeat": error is None and canonical_hashes(clusters1) == canonical_hashes(clusters2),
                "year_swap_invariance": error is None and canonical_hashes(clusters1) == canonical_hashes(clusters_swap),
                "prominence_integrity": error is None and all(math.isfinite(float(r["prominence"])) and float(r["prominence"]) >= 0.0 for r in rows) and [int(r["rank"]) for r in rows] == list(range(1, len(rows) + 1)),
            }
            panel_gate_state[key] = gates
            panel_rows.append({
                "denominator": denominator,
                "bucket": bucket,
                "event_count": len(panel_ids),
                "annual_event_ids": {y: sorted(v) for y, v in annual_ids.items()},
                "equal_budget_k": k,
                "recurrent_candidates": frozen["recurrent_candidates"],
                "pf_candidates": rows,
                "pf_error": error,
                "graph_summary": {
                    "radius": RADIUS,
                    "edge_count": int(len(graph["edges"])),
                    "events_2022": int(graph["n22"]),
                    "events_2023": int(graph["n23"]),
                    "rho_sync_zero_fraction": float(np.mean(graph["rho_sync"] == 0.0)),
                    "rho_sync_median": float(np.median(graph["rho_sync"])),
                    "rho_sync_max": float(np.max(graph["rho_sync"])),
                    "noise_count": int(np.sum(labels1 < 0)),
                    "returned_cluster_count": len(rows),
                },
                "panel_gates": gates,
            })

    panel_lookup = {(int(r["denominator"]), int(r["bucket"])): r for r in panel_rows}
    cross_scale: list[dict[str, Any]] = []
    pf_scores: list[float] = []
    recurrent_scores: list[float] = []
    for bucket in BUCKETS:
        fine = panel_lookup[(1024, bucket)]
        coarse = panel_lookup[(128, bucket)]
        fine_universe = set(fine["annual_event_ids"]["2022"]) | set(fine["annual_event_ids"]["2023"])
        pf_score = mean_best_jaccard(fine["pf_candidates"], coarse["pf_candidates"], fine_universe) if fine["pf_candidates"] and coarse["pf_candidates"] else 0.0
        rec_score = mean_best_jaccard(fine["recurrent_candidates"], coarse["recurrent_candidates"], fine_universe)
        pf_scores.append(pf_score)
        recurrent_scores.append(rec_score)
        cross_scale.append({
            "bucket": bucket,
            "pf_mean_best_jaccard": pf_score,
            "recurrent_mean_best_jaccard": rec_score,
            "pf_nonlower": pf_score >= rec_score,
        })

    gates = {
        "immutable_endpoint_source": True,
        "persistable_source_pin": True,
        "requested_returned_k_all_8": all(g["returned_exact_k"] for g in panel_gate_state.values()),
        "support_floor_all": all(g["support_floor"] for g in panel_gate_state.values()),
        "pairwise_disjoint_all": all(g["pairwise_disjoint"] for g in panel_gate_state.values()),
        "membership_universe_all": all(g["membership_universe"] for g in panel_gate_state.values()),
        "graph_connectivity_all": all(g["graph_connectivity"] for g in panel_gate_state.values()),
        "deterministic_repeat_all": all(g["deterministic_repeat"] for g in panel_gate_state.values()),
        "year_swap_invariance_all": all(g["year_swap_invariance"] for g in panel_gate_state.values()),
        "prominence_integrity_all": all(g["prominence_integrity"] for g in panel_gate_state.values()),
        "cross_scale_nonlower_4_of_4": sum(bool(r["pf_nonlower"]) for r in cross_scale) == 4,
        "cross_scale_mean_not_lower": float(np.mean(pf_scores)) >= float(np.mean(recurrent_scores)),
    }
    verdict = "PASS_ANNUAL_SYNC_DENSITY_PF_V1_PRETRUTH" if all(gates.values()) else "FAIL_ANNUAL_SYNC_DENSITY_PF_V1_PRETRUTH"
    out = {
        "schema": "ORBITTRACE_ANNUAL_SYNC_DENSITY_PF_V1_PRELABEL",
        "scientific_role": "ZERO_LABEL_TARGET_EXCLUDED_GMN_STRUCTURAL_AUTHORIZATION",
        "verdict": verdict,
        "source_endpoint_prelabel_sha256": ENDPOINT_PRELABEL_SHA256,
        "persistable_commit": PERSISTABLE_COMMIT,
        "persistable_source_blob": PERSISTABLE_SOURCE_BLOB,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "radius": RADIUS,
            "annual_density_combiner": "min(d22/N22,d23/N23)",
            "vertex_filtration": "negative_rho_sync",
            "edge_filtration": "max_endpoint_filtration",
            "filtration_end": 0.0,
            "flattening": "conservative",
            "keep_low_persistence_clusters": False,
            "cluster_count": "exact_frozen_recurrent_equal_budget_K",
            "minimum_support": MIN_SUPPORT,
            "ranking": ["prominence_desc", "member_count_desc", "membership_sha256_asc"],
        },
        "panels": panel_rows,
        "cross_scale": cross_scale,
        "aggregate": {
            "pf_cross_scale_mean": float(np.mean(pf_scores)),
            "recurrent_cross_scale_mean": float(np.mean(recurrent_scores)),
            "pf_bucket_wins_or_ties": int(sum(p >= r for p, r in zip(pf_scores, recurrent_scores))),
        },
        "gates": gates,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    out_sha = dump(a.output / "ANNUAL_SYNC_DENSITY_PF_V1_PRELABEL.json", out)
    print(json.dumps({"verdict": verdict, "prelabel_sha256": out_sha, "aggregate": out["aggregate"], "gates": gates, "panel_counts": [{"d":r["denominator"],"b":r["bucket"],"K":r["equal_budget_k"],"returned":len(r["pf_candidates"]),"error":r["pf_error"]} for r in panel_rows]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
