#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BUCKETS = (0, 1, 2, 3)
RADIUS = 1.0
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"


def exact_child_merge_level(
    base: Any,
    adjacency: list[set[int]],
    rho: np.ndarray,
    ia: frozenset[int],
    ib: frozenset[int],
) -> float:
    """Highest density superlevel at which the two fixed child memberships connect.

    This is an implementation of the already-frozen 'density-level lifetime'
    definition. It does not use shower truth, labels, comparator results, or any
    tunable parameter.
    """
    # Iterate the smaller child only; graph is verified symmetric.
    left, right = (ia, ib) if len(ia) <= len(ib) else (ib, ia)
    best = -np.inf
    for i in left:
        for j in adjacency[int(i)]:
            if j in right:
                level = min(float(rho[int(i)]), float(rho[int(j)]))
                if level > best:
                    best = level
    base.req(np.isfinite(best), "ToMATo merge children have no cross edge")
    return float(best)


def lineage_ranked(base: Any, structural: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = structural.physical_embedding(ordered)

    raw = cKDTree(Z).query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    adjacency = [set(row) for row in neighbors]
    base.req(len(neighbors) == len(ids), "radius graph row count")
    base.req(all(i in adjacency[i] for i in range(len(ids))), "radius graph self edge")
    base.req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph symmetry")

    degrees = np.asarray([len(row) for row in neighbors], dtype=float)
    rho = degrees / float(len(ids))
    base.req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid radius density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    L = int(model.n_leaves_)
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    base.req(L - len(children) == roots_expected, "root arithmetic")

    diagram = np.asarray(model.diagram_, dtype=float)
    diagram_sorted = base.diagram_sorted(diagram)
    base.req(len(diagram_sorted) == len(children), "persistence count")

    N = L + len(children)
    members: list[frozenset[str] | None] = [None] * N
    member_ix: list[frozenset[int] | None] = [None] * N
    parent = np.full(N, -1, dtype=np.int64)
    active_peak = np.full(N, np.nan, dtype=float)
    active_key: list[str | None] = [None] * N
    merge_level = np.full(N, np.nan, dtype=float)

    for leaf in range(L):
        ix = np.flatnonzero(labels == leaf)
        base.req(len(ix) > 0, f"empty leaf {leaf}")
        ixset = frozenset(int(i) for i in ix)
        member_ix[leaf] = ixset
        members[leaf] = frozenset(ids[int(i)] for i in ix)
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        base.req(bool(keys), f"leaf {leaf} missing peak")
        active_peak[leaf] = peak
        active_key[leaf] = keys[0]

    reconstructed_pairs: list[list[float]] = []
    for off, pair in enumerate(children):
        node = L + off
        a, b = int(pair[0]), int(pair[1])
        base.req(0 <= a < node and 0 <= b < node and a != b, f"bad children at {node}")
        ma, mb = members[a], members[b]
        ia, ib = member_ix[a], member_ix[b]
        base.req(
            ma is not None and mb is not None and ia is not None and ib is not None
            and ma.isdisjoint(mb) and ia.isdisjoint(ib)
            and parent[a] == -1 and parent[b] == -1,
            "bad hierarchy",
        )

        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        winner, loser = (a, b) if pa > pb or (pa == pb and ka < kb) else (b, a)

        saddle = exact_child_merge_level(base, adjacency, rho, ia, ib)
        base.req(saddle <= min(pa, pb) + 1e-12, f"merge saddle above child mode at {node}")

        members[node] = frozenset(ma.union(mb))
        member_ix[node] = frozenset(ia.union(ib))
        parent[a] = node
        parent[b] = node
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])
        merge_level[node] = saddle
        reconstructed_pairs.append([float(active_peak[loser]), saddle])

    roots = np.flatnonzero(parent == -1)
    base.req(len(roots) == roots_expected, "root count")
    base.req(sum(len(members[int(r)]) for r in roots if members[int(r)] is not None) == len(ids), "root partition")

    reconstructed_sorted = base.diagram_sorted(np.asarray(reconstructed_pairs, dtype=float))
    base.req(reconstructed_sorted.shape == diagram_sorted.shape, "diagram shape")
    base.req(
        np.allclose(reconstructed_sorted, diagram_sorted, rtol=0.0, atol=1e-12),
        f"exact graph-saddle persistence reconstruction mismatch; max_abs={float(np.max(np.abs(reconstructed_sorted-diagram_sorted))) if reconstructed_sorted.size else 0.0}",
    )

    # Strong monotonicity audit for the exact density-level hierarchy. This is
    # what the original implementation was attempting to test, but it had
    # incorrectly paired sorted persistence values with merge nodes.
    for node in range(N):
        p = int(parent[node])
        if p == -1:
            continue
        formation = float(active_peak[node]) if node < L else float(merge_level[node])
        outside = float(merge_level[p])
        base.req(
            np.isfinite(formation) and np.isfinite(outside) and formation + 1e-12 >= outside,
            f"nonmonotone exact hierarchy lifetime at {node}",
        )

    # Reproduce the complete exact #1284 candidate universe independently.
    full, summary = structural.topomodal_candidates(ordered)
    eligible = {tuple(sorted(str(x) for x in membership)) for membership in full}
    node_by_members: dict[tuple[str, ...], int] = {}
    for node, membership in enumerate(members):
        base.req(membership is not None, f"missing membership {node}")
        tup = tuple(sorted(str(x) for x in membership))
        if tup in eligible and tup not in node_by_members:
            node_by_members[tup] = node
    base.req(set(node_by_members) == eligible, "eligible hierarchy mapping")

    rows: list[dict[str, Any]] = []
    for tup, node in node_by_members.items():
        p = int(parent[node])
        outside = 0.0 if p == -1 else float(merge_level[p])
        formation = float(active_peak[node]) if node < L else float(merge_level[node])
        lifetime = formation - outside
        base.req(np.isfinite(lifetime) and lifetime >= -1e-12, f"bad exact lifetime {node}")
        membership = frozenset(tup)
        rows.append(
            {
                "family_id": base.family_id("TLIN1", tup),
                "family_hash": structural.member_hash(membership),
                "event_ids": list(tup),
                "member_count": len(tup),
                "node": int(node),
                "is_root": bool(p == -1),
                "lineage_key": str(active_key[node]),
                "formation_level": formation,
                "outside_merge_level": outside,
                "level_lifetime": max(0.0, float(lifetime)),
            }
        )

    by_lineage: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_lineage.setdefault(str(row["lineage_key"]), []).append(row)
    for values in by_lineage.values():
        values.sort(key=lambda r: (-float(r["level_lifetime"]), str(r["family_hash"])))
        for k, row in enumerate(values, 1):
            row["lineage_round"] = int(k)

    rows.sort(key=lambda r: (int(r["lineage_round"]), -float(r["level_lifetime"]), str(r["family_hash"])))
    for k, row in enumerate(rows, 1):
        row["rank"] = int(k)

    base.req(len(rows) == int(summary["candidate_count"]), "candidate count")
    base.req([int(r["rank"]) for r in rows] == list(range(1, len(rows) + 1)), "rank continuity")

    return rows, {
        "candidate_count": len(rows),
        "candidate_rows": summary["candidate_rows"],
        "lineage_count": len(by_lineage),
        "max_lineage_round": max((int(r["lineage_round"]) for r in rows), default=0),
        "merge_level_source": "exact_highest_density_cross_edge_between_fixed_children",
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(reconstructed_sorted - diagram_sorted))) if reconstructed_sorted.size else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "support-cut-runner",
        "structural-runner",
        "structural-result-json",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    spec = __import__("importlib.util").util.spec_from_file_location("lin_base", a.support_cut_runner)
    base = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.req(
        base.sha256(a.quality_source) == QUALITY_SHA256
        and base.sha256(a.v8_result_json) == V8_RESULT_SHA256
        and base.sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256,
        "frozen input hash",
    )

    sr = json.loads(a.structural_result_json.read_text())
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in sr["fits"]}
    structural = base.load_module(a.structural_runner, "lin_struct")
    parent = base.load_module(a.parent_runner, "lin_parent")

    q = base.load_module(a.quality_source, "lin_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-lineage-balanced-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    base.req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, baseline_source, _scorer = support.load_sources(a)
    scan, _calibration, hidden_unused, _sources = support.parse_catalogue(baseline_source)
    del hidden_unused
    base.req(sorted(scan) == list(YEARS), "years")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    base.req(
        len(events) == 738682 and all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events),
        "universe/firewall",
    )

    Xfull = parent.geo_matrix(events)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids = [str(e["id"]) for e in events]
    hashes = np.asarray([base.event_hash_u64(eid) for eid in ids], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            ii = base.selected_indices(hashes, denominator, bucket)
            sub = [events[int(i)] for i in ii]
            sx = np.asarray(Xfull[ii])
            sy = np.asarray(years[ii])
            sid = [ids[int(i)] for i in ii]
            print(f"[lineage-prelabel-repair1] d={denominator} b={bucket} n={len(sid)}", flush=True)

            successor, successor_summary = lineage_ranked(base, structural, sub)
            comparator, comparator_summary = base.recurrent_ranked(parent, sx, sy, sid)
            ex = expected[(denominator, bucket)]
            base.req(
                successor_summary["candidate_rows"] == ex["topomodal"]["candidate_rows"]
                and len(successor) == int(ex["topomodal"]["candidate_count"]),
                "#1284 successor mismatch",
            )
            base.req(
                comparator_summary["candidate_rows"] == ex["recurrent_eom"]["candidate_rows"]
                and len(comparator) == int(ex["recurrent_eom"]["candidate_count"]),
                "parent mismatch",
            )
            base.req(len(successor) >= len(comparator), "successor shorter than parent")
            subsets.append(
                {
                    "denominator": denominator,
                    "bucket": bucket,
                    "events_total": len(sid),
                    "events_by_year": {str(y): int(np.sum(sy == y)) for y in YEARS},
                    "event_universe_sha256": base.universe_hash(sid),
                    "equal_budget_k": len(comparator),
                    "lineage_summary": successor_summary,
                    "successor_candidates": successor,
                    "recurrent_candidates": comparator,
                }
            )

    pre = {
        "schema": "ORBITTRACE_TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL",
        "scientific_role": "PRELABEL_TOPOMODAL_LINEAGE_BALANCED_V1",
        "engineering_repair": "repair1_exact_graph_saddle_merge_levels",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "configuration": {
            "candidate_universe": "complete_exact_1284_hierarchy",
            "lineage": "surviving_active_mode_key",
            "node_score": "density_level_lifetime",
            "ranking": "lineage_round_asc_then_lifetime_desc_then_family_hash",
            "equal_budget": "K_equals_recurrent_candidate_count",
        },
        "subsets": subsets,
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
    out = a.output / "TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "prelabel_sha256": base.sha256(out),
                "subsets": [
                    {
                        "d": x["denominator"],
                        "b": x["bucket"],
                        "candidates": len(x["successor_candidates"]),
                        "lineages": x["lineage_summary"]["lineage_count"],
                        "K": x["equal_budget_k"],
                    }
                    for x in subsets
                ],
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
