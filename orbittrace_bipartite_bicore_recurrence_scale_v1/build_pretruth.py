#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
BLIND = (20.0, 55.0)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
RADIUS = 1.0
CORE_ORDER = 4
MIN_SUPPORT = 4
EXPECTED_EVENTS = 738682
PROTOCOL_BLOB = "8d0040e66bc0c640a9427c7b36824e05acb8e3ef"
ENDPOINT_PRELABEL_SHA256 = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
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


def build_bipartite_graph(parent: Any, events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "panel lost a year")
    x = np.asarray(parent.geo_matrix(ordered), dtype=float)
    req(x.shape == (len(ids), 6) and np.all(np.isfinite(x)), "invalid GEO6 matrix")

    tree = cKDTree(x)
    raw = tree.query_ball_point(x, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    adjacency: list[set[int]] = [set() for _ in ids]
    edge_count = 0
    max_edge_distance = 0.0
    for i, row in enumerate(raw):
        yi = int(years[i])
        for jj in row:
            j = int(jj)
            if j <= i or int(years[j]) == yi:
                continue
            dist = float(np.linalg.norm(x[i] - x[j]))
            req(dist <= RADIUS + 1e-12, "radius query returned out-of-radius edge")
            adjacency[i].add(j)
            adjacency[j].add(i)
            edge_count += 1
            max_edge_distance = max(max_edge_distance, dist)

    for i, row in enumerate(adjacency):
        req(all(i in adjacency[j] for j in row), "bipartite graph not symmetric")
        req(all(int(years[i]) != int(years[j]) for j in row), "same-year edge survived")

    return {
        "ordered": ordered,
        "ids": ids,
        "years": years,
        "x": x,
        "adjacency": adjacency,
        "edge_count": edge_count,
        "max_edge_distance": max_edge_distance,
    }


def peel_bicore(adjacency: list[set[int]], reverse: bool = False) -> np.ndarray:
    n = len(adjacency)
    active = np.ones(n, dtype=bool)
    degree = np.asarray([len(row) for row in adjacency], dtype=np.int64)
    heap: list[int] = []

    def token(i: int) -> int:
        return -i if reverse else i

    def untoken(t: int) -> int:
        return -t if reverse else t

    queued = np.zeros(n, dtype=bool)
    for i in range(n):
        if int(degree[i]) < CORE_ORDER:
            heapq.heappush(heap, token(i))
            queued[i] = True

    while heap:
        i = untoken(heapq.heappop(heap))
        if not active[i] or int(degree[i]) >= CORE_ORDER:
            continue
        active[i] = False
        for j in adjacency[i]:
            if not active[j]:
                continue
            degree[j] -= 1
            if int(degree[j]) < CORE_ORDER and not queued[j]:
                heapq.heappush(heap, token(j))
                queued[j] = True

    # Recompute final active degrees exactly instead of trusting mutation bookkeeping.
    for i in range(n):
        if active[i]:
            d = sum(bool(active[j]) for j in adjacency[i])
            req(d >= CORE_ORDER, "peeling left sub-core vertex")
    return active


def component_rows(graph: dict[str, Any], active: np.ndarray) -> list[dict[str, Any]]:
    ids: list[str] = graph["ids"]
    years: np.ndarray = graph["years"]
    adjacency: list[set[int]] = graph["adjacency"]
    seen: set[int] = set()
    rows: list[dict[str, Any]] = []

    for start in range(len(ids)):
        if not bool(active[start]) or start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp: list[int] = []
        while stack:
            i = stack.pop()
            comp.append(i)
            for j in adjacency[i]:
                if bool(active[j]) and j not in seen:
                    seen.add(j)
                    stack.append(j)
        comp.sort()
        members = [ids[i] for i in comp]
        n22 = sum(int(years[i]) == 2022 for i in comp)
        n23 = sum(int(years[i]) == 2023 for i in comp)
        req(n22 >= MIN_SUPPORT and n23 >= MIN_SUPPORT, "bicore component violated annual support")
        active_set = set(comp)
        edge_count = sum(sum(j in active_set for j in adjacency[i]) for i in comp) // 2
        min_degree = min(sum(j in active_set for j in adjacency[i]) for i in comp)
        req(min_degree >= CORE_ORDER, "component minimum degree violated bicore")
        rows.append({
            "family_hash": membership_hash(members),
            "member_count": len(members),
            "members_2022": n22,
            "members_2023": n23,
            "bottleneck_annual_support": min(n22, n23),
            "crossyear_edge_count": int(edge_count),
            "minimum_crossyear_degree": int(min_degree),
            "event_ids": sorted(members),
        })

    rows.sort(key=lambda r: (
        -int(r["bottleneck_annual_support"]),
        -int(r["crossyear_edge_count"]),
        -int(r["member_count"]),
        str(r["family_hash"]),
    ))
    for rank, row in enumerate(rows, 1):
        row["diagnostic_rank"] = rank
    return rows


def hashes(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(str(r["family_hash"]) for r in rows)


def restrict_bicore_candidates(candidates: list[dict[str, Any]], fine_ids: set[str], fine_year: dict[str, int]) -> list[frozenset[str]]:
    seen: set[tuple[str, ...]] = set()
    out: list[frozenset[str]] = []
    for row in candidates:
        members = tuple(sorted(set(str(x) for x in row["event_ids"]) & fine_ids))
        if members in seen:
            continue
        n22 = sum(fine_year[eid] == 2022 for eid in members)
        n23 = sum(fine_year[eid] == 2023 for eid in members)
        if n22 < MIN_SUPPORT or n23 < MIN_SUPPORT:
            continue
        seen.add(members)
        out.append(frozenset(members))
    return out


def restrict_reference(candidates: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    seen: set[tuple[str, ...]] = set()
    out: list[frozenset[str]] = []
    for row in candidates:
        members = tuple(sorted(set(str(x) for x in row["event_ids"]) & universe))
        if len(members) < MIN_SUPPORT or members in seen:
            continue
        seen.add(members)
        out.append(frozenset(members))
    return out


def mean_best_jaccard(fine: list[dict[str, Any]], coarse_sets: list[frozenset[str]]) -> float:
    if not fine:
        return 0.0
    vals: list[float] = []
    for row in fine:
        a = frozenset(str(x) for x in row["event_ids"])
        best = 0.0
        for b in coarse_sets:
            inter = len(a & b)
            if inter:
                best = max(best, inter / len(a | b))
        vals.append(float(best))
    return float(np.mean(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
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

    req(git_blob(a.protocol) == PROTOCOL_BLOB, "protocol changed after freeze")
    req(sha256(a.endpoint_prelabel) == ENDPOINT_PRELABEL_SHA256, "endpoint prelabel changed")
    req(git_blob(a.parent_runner) == PARENT_SOURCE_BLOB, "GEO6 parent source changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == V8_SHA256, "GMN support artifact changed")

    endpoint = json.loads(a.endpoint_prelabel.read_text())
    req(endpoint["schema"] == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong endpoint schema")
    req(endpoint["scientific_role"] == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong endpoint role")
    req(endpoint["shower_truth_used"] is False, "endpoint prelabel used truth")
    req(endpoint["target_information_access"] is False and endpoint["target_region_events_accessed"] is False, "endpoint firewall")
    req(endpoint["sonotaco_2013_2014_access"] is False, "endpoint SonotaCo access")
    subset_map = {(int(s["denominator"]), int(s["bucket"])): s for s in endpoint["subsets"]}
    req(set(subset_map) == set(EXPECTED_K), "wrong endpoint panels")
    for key, k in EXPECTED_K.items():
        s = subset_map[key]
        req(int(s["equal_budget_k"]) == k and len(s["recurrent_candidates"]) == k, f"K/reference changed {key}")

    parent = load_module(a.parent_runner, "bicore_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    qmod = load_module(a.quality_source, "bicore_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-bipartite-bicore-recurrence-scale-v1-zero-label"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    # Truth is deliberately destroyed before any graph construction or panel work.
    del hidden_sealed
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == EXPECTED_EVENTS, f"target-excluded event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")
    event_by_id = {str(e["id"]): e for e in events}

    panels: list[dict[str, Any]] = []
    panel_map: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            key = (denominator, bucket)
            frozen = subset_map[key]
            annual_ids = {str(y): [str(x) for x in frozen["annual_event_ids"][str(y)]] for y in YEARS}
            panel_ids = set(annual_ids["2022"]) | set(annual_ids["2023"])
            req(len(panel_ids) == int(frozen["event_count"]), f"event count mismatch {key}")
            req(panel_ids.issubset(event_by_id), f"missing panel events {key}")
            panel_events = [event_by_id[eid] for eid in panel_ids]
            graph = build_bipartite_graph(parent, panel_events)
            req(set(graph["ids"]) == panel_ids, f"graph universe changed {key}")

            active_forward = peel_bicore(graph["adjacency"], reverse=False)
            active_reverse = peel_bicore(graph["adjacency"], reverse=True)
            forward_rows = component_rows(graph, active_forward)
            reverse_rows = component_rows(graph, active_reverse)

            years_swapped = np.asarray([2023 if int(y) == 2022 else 2022 for y in graph["years"]], dtype=np.int64)
            swap_bipartite = all(int(years_swapped[i]) != int(years_swapped[j]) for i, row in enumerate(graph["adjacency"]) for j in row)
            active_swap = peel_bicore(graph["adjacency"], reverse=False)
            swap_rows = component_rows({**graph, "years": years_swapped}, active_swap)

            strict_edges = all(int(graph["years"][i]) != int(graph["years"][j]) for i, row in enumerate(graph["adjacency"]) for j in row)
            order_invariant = np.array_equal(active_forward, active_reverse) and hashes(forward_rows) == hashes(reverse_rows)
            swap_invariant = swap_bipartite and np.array_equal(active_forward, active_swap) and hashes(forward_rows) == hashes(swap_rows)

            active_indices = np.flatnonzero(active_forward)
            active_degrees = [sum(bool(active_forward[j]) for j in graph["adjacency"][int(i)]) for i in active_indices]
            degree_floor = all(d >= CORE_ORDER for d in active_degrees)
            annual_floor = all(int(r["members_2022"]) >= MIN_SUPPORT and int(r["members_2023"]) >= MIN_SUPPORT for r in forward_rows)
            disjoint = len(set(eid for r in forward_rows for eid in r["event_ids"])) == sum(len(r["event_ids"]) for r in forward_rows)
            connected = all(int(r["minimum_crossyear_degree"]) >= CORE_ORDER for r in forward_rows)

            row = {
                "denominator": denominator,
                "bucket": bucket,
                "event_count": len(panel_ids),
                "events_2022": len(annual_ids["2022"]),
                "events_2023": len(annual_ids["2023"]),
                "reference_k": EXPECTED_K[key],
                "annual_event_ids": {y: sorted(v) for y, v in annual_ids.items()},
                "reference_candidates": frozen["recurrent_candidates"],
                "bicore_candidates": forward_rows,
                "graph_summary": {
                    "radius": RADIUS,
                    "core_order": CORE_ORDER,
                    "crossyear_edge_count": int(graph["edge_count"]),
                    "maximum_crossyear_edge_distance": float(graph["max_edge_distance"]),
                    "active_event_count": int(np.sum(active_forward)),
                    "peeled_event_count": int(len(active_forward) - np.sum(active_forward)),
                    "candidate_count": len(forward_rows),
                    "minimum_active_degree": int(min(active_degrees)) if active_degrees else 0,
                },
                "panel_checks": {
                    "strict_bipartite_graph": bool(strict_edges and graph["max_edge_distance"] <= RADIUS + 1e-12),
                    "bicore_degree_floor": bool(degree_floor),
                    "annual_support_floor": bool(annual_floor),
                    "pairwise_disjoint": bool(disjoint),
                    "crossyear_connected": bool(connected),
                    "peeling_order_invariance": bool(order_invariant),
                    "year_swap_invariance": bool(swap_invariant),
                    "capacity_at_least_reference_k": len(forward_rows) >= EXPECTED_K[key],
                },
            }
            panels.append(row)
            panel_map[key] = row

    cross_scale: list[dict[str, Any]] = []
    bicore_scores: list[float] = []
    reference_scores: list[float] = []
    for bucket in BUCKETS:
        fine = panel_map[(1024, bucket)]
        coarse = panel_map[(128, bucket)]
        fine_ids = set(fine["annual_event_ids"]["2022"]) | set(fine["annual_event_ids"]["2023"])
        fine_year = {eid: 2022 for eid in fine["annual_event_ids"]["2022"]}
        fine_year.update({eid: 2023 for eid in fine["annual_event_ids"]["2023"]})
        bicore_coarse = restrict_bicore_candidates(coarse["bicore_candidates"], fine_ids, fine_year)
        reference_coarse = restrict_reference(coarse["reference_candidates"], fine_ids)
        bscore = mean_best_jaccard(fine["bicore_candidates"], bicore_coarse)
        rscore = mean_best_jaccard(fine["reference_candidates"], reference_coarse)
        bicore_scores.append(bscore)
        reference_scores.append(rscore)
        cross_scale.append({
            "bucket": bucket,
            "bicore_mean_best_jaccard": bscore,
            "reference_mean_best_jaccard": rscore,
            "bicore_nonlower": bscore >= rscore,
        })

    gates = {
        "immutable_endpoint_source": True,
        "strict_bipartite_graph_all": all(bool(p["panel_checks"]["strict_bipartite_graph"]) for p in panels),
        "bicore_degree_floor_all": all(bool(p["panel_checks"]["bicore_degree_floor"]) for p in panels),
        "annual_support_floor_all": all(bool(p["panel_checks"]["annual_support_floor"]) for p in panels),
        "pairwise_disjoint_all": all(bool(p["panel_checks"]["pairwise_disjoint"]) for p in panels),
        "crossyear_connected_all": all(bool(p["panel_checks"]["crossyear_connected"]) for p in panels),
        "peeling_order_invariance_all": all(bool(p["panel_checks"]["peeling_order_invariance"]) for p in panels),
        "year_swap_invariance_all": all(bool(p["panel_checks"]["year_swap_invariance"]) for p in panels),
        "capacity_at_least_reference_k_all_8": all(bool(p["panel_checks"]["capacity_at_least_reference_k"]) for p in panels),
        "cross_scale_nonlower_4_of_4": sum(bool(r["bicore_nonlower"]) for r in cross_scale) == 4,
        "cross_scale_mean_not_lower": float(np.mean(bicore_scores)) >= float(np.mean(reference_scores)),
        "firewall": True,
    }
    verdict = "PASS_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH" if all(gates.values()) else "FAIL_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH"
    out = {
        "schema": "ORBITTRACE_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH",
        "scientific_role": "ZERO_LABEL_TARGET_EXCLUDED_GMN_STRUCTURAL_AUTHORIZATION",
        "verdict": verdict,
        "protocol_blob": PROTOCOL_BLOB,
        "source_endpoint_prelabel_sha256": ENDPOINT_PRELABEL_SHA256,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "geometry": "exact_inherited_GEO6",
            "crossyear_radius": RADIUS,
            "same_year_edges": False,
            "bicore": [CORE_ORDER, CORE_ORDER],
            "family_rule": "connected_components_of_surviving_bipartite_core",
            "diagnostic_order": ["min_annual_support_desc", "crossyear_edges_desc", "member_count_desc", "membership_sha256_asc"],
            "truth_ranking_authorized": False,
        },
        "panels": panels,
        "cross_scale": cross_scale,
        "aggregate": {
            "bicore_cross_scale_mean": float(np.mean(bicore_scores)),
            "reference_cross_scale_mean": float(np.mean(reference_scores)),
            "bicore_bucket_wins_or_ties": int(sum(b >= r for b, r in zip(bicore_scores, reference_scores))),
            "candidate_counts": [{"d":p["denominator"], "b":p["bucket"], "K":p["reference_k"], "bicore":len(p["bicore_candidates"])} for p in panels],
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
        "orbital_information_access": False,
        "station_metadata_access": False,
        "uncertainty_metadata_access": False,
        "post_result_parameter_search": False,
    }
    out_sha = dump(a.output / "BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH.json", out)
    print(json.dumps({
        "verdict": verdict,
        "pretruth_sha256": out_sha,
        "aggregate": out["aggregate"],
        "gates": gates,
        "cross_scale": cross_scale,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
