#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
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
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assign_lineages(intrinsic: Any, events: list[dict[str, Any]], ranked: list[dict[str, Any]]) -> dict[str, Any]:
    """Assign each exact #1284 candidate to its surviving ToMATo density-mode lineage.

    Candidate priority is not recomputed here. `ranked` is the exact output of the
    previously frozen intrinsic sparse-recovery implementation. This function only
    adds deterministic lineage identities from the same graph/hierarchy.
    """
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = intrinsic.physical_embedding(ordered)
    raw = cKDTree(Z).query_ball_point(Z, r=float(intrinsic.RADIUS), p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    req(len(neighbors) == len(ids), "lineage radius graph row count")
    adjacency = [set(row) for row in neighbors]
    req(all(i in adjacency[i] for i in range(len(ids))), "lineage radius graph self edge")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "lineage radius graph symmetry")

    rho = np.asarray([len(row) for row in neighbors], dtype=float) / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid lineage density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    leaf_count = int(model.n_leaves_)
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(leaf_count - len(children) == roots_expected, "lineage ToMATo arithmetic")

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    parent = np.full(node_count, -1, dtype=np.int64)
    active_peak = np.full(node_count, np.nan, dtype=float)
    active_key: list[str | None] = [None] * node_count
    leaf_mode_keys: set[str] = set()

    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty lineage leaf {leaf}")
        member_ix[leaf] = frozenset(int(i) for i in ix)
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        req(bool(keys), f"missing lineage mode key leaf {leaf}")
        active_peak[leaf] = peak
        active_key[leaf] = keys[0]
        req(keys[0] not in leaf_mode_keys, "duplicate leaf mode key")
        leaf_mode_keys.add(keys[0])

    for off, pair in enumerate(children):
        node = leaf_count + off
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid lineage children node={node}")
        req(parent[a] == -1 and parent[b] == -1, "lineage node multiple parents")
        ma, mb = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None and ma.isdisjoint(mb), "lineage child membership")
        member_ix[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node
        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        winner = a if pa > pb or (pa == pb and ka < kb) else b
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "lineage root count")
    req(sum(len(member_ix[int(r)]) for r in roots if member_ix[int(r)] is not None) == len(ids), "lineage root partition")

    annotated: list[dict[str, Any]] = []
    seen_nodes: set[int] = set()
    for row in ranked:
        node = int(row["first_node"])
        req(0 <= node < node_count and node not in seen_nodes, "invalid/duplicate intrinsic first_node")
        seen_nodes.add(node)
        ixset = member_ix[node]
        req(ixset is not None, "candidate first_node missing membership")
        node_members = tuple(sorted(ids[int(i)] for i in ixset))
        req(node_members == tuple(map(str, row["event_ids"])), "intrinsic membership / lineage node mismatch")
        key = active_key[node]
        req(key is not None and str(key) in leaf_mode_keys, "candidate lineage is not an actual leaf mode")
        x = dict(row)
        x["intrinsic_rank"] = int(row["rank"])
        x["lineage_key"] = str(key)
        annotated.append(x)

    req([int(r["intrinsic_rank"]) for r in annotated] == list(range(1, len(annotated) + 1)), "intrinsic rank changed")

    by_lineage: dict[str, list[dict[str, Any]]] = {}
    for row in annotated:
        by_lineage.setdefault(str(row["lineage_key"]), []).append(row)
    for rows in by_lineage.values():
        rows.sort(key=lambda r: int(r["intrinsic_rank"]))
        for k, row in enumerate(rows, 1):
            row["lineage_round"] = int(k)

    final = sorted(annotated, key=lambda r: (int(r["lineage_round"]), int(r["intrinsic_rank"])))
    for rank, row in enumerate(final, 1):
        row["rank"] = int(rank)

    req(len(final) == len(ranked), "lineage interleaving changed candidate count")
    req({str(r["family_id"]) for r in final} == {str(r["family_id"]) for r in ranked}, "lineage interleaving changed candidate set")
    req([int(r["rank"]) for r in final] == list(range(1, len(final) + 1)), "lineage rank discontinuity")
    req([str(r["family_id"]) for r in final] == [str(r["family_id"]) for r in sorted(final, key=lambda r: (int(r["lineage_round"]), int(r["intrinsic_rank"])))], "lineage final order mismatch")

    first_round = [r for r in final if int(r["lineage_round"]) == 1]
    req(len(first_round) == len(by_lineage), "round 1 does not represent every lineage once")
    req(len({str(r["lineage_key"]) for r in first_round}) == len(first_round), "duplicate lineage in round 1")

    return {
        "candidates": final,
        "lineage_count": len(by_lineage),
        "leaf_count": leaf_count,
        "root_count": len(roots),
        "max_lineage_round": max((int(r["lineage_round"]) for r in final), default=0),
        "first_round_count": len(first_round),
        "intrinsic_order_sha256": intrinsic.hashlib.sha256("\n".join(str(r["family_id"]) for r in ranked).encode()).hexdigest(),
        "final_order_sha256": intrinsic.hashlib.sha256("\n".join(str(r["family_id"]) for r in final).encode()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "intrinsic-runner",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
        "structural-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    intrinsic = load_module(a.intrinsic_runner, "lineage_v2_intrinsic")
    req(intrinsic.sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN utility changed")
    req(intrinsic.sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen v8 artifact changed")
    req(intrinsic.sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "#1284 structural artifact changed")
    req(tuple(intrinsic.YEARS) == YEARS and tuple(intrinsic.BLIND) == BLIND, "intrinsic source constants changed")
    req(int(intrinsic.COARSE_D) == 128 and int(intrinsic.FINE_D) == 1024 and tuple(intrinsic.BUCKETS) == BUCKETS, "intrinsic sparse panels changed")

    structural = json.loads(a.structural_result_json.read_text())
    req(structural["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 prerequisite changed")
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected_fits) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "#1284 panel set changed")

    parent = load_module(a.parent_runner, "lineage_v2_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support changed")

    q = load_module(a.quality_source, "lineage_v2_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-lineage-interleaved-v2-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base_source, _scorer = support.load_sources(a)
    scan, _cal, hidden_unused, sources = support.parse_catalogue(base_source)
    del hidden_unused
    req(sorted(scan) == list(YEARS), "wrong GMN years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")

    Xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([intrinsic.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            ii = intrinsic.selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ii]
            X = np.asarray(Xfull[ii], dtype=float)
            years = np.asarray(years_full[ii], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ii]
            print(f"[lineage-v2-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)

            intrinsic_ranked, topo_summary = intrinsic.topomodal_ranked(sub_events)
            recurrent, recurrent_summary = intrinsic.recurrent_ranked(parent, X, years, ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(ids), "#1284 event count mismatch")
            req({str(k): int(v) for k, v in expected["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, "#1284 annual count mismatch")
            req(expected["topomodal"]["candidate_rows"] == topo_summary["candidate_rows"], "#1284 topomodal membership mismatch")
            req(int(expected["topomodal"]["candidate_count"]) == len(intrinsic_ranked), "#1284 topomodal count mismatch")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], "#1284 recurrent membership mismatch")
            req(int(expected["recurrent_eom"]["candidate_count"]) == len(recurrent), "#1284 recurrent count mismatch")
            req(len(intrinsic_ranked) >= len(recurrent), "successor shorter than comparator")

            lineage = assign_lineages(intrinsic, sub_events, intrinsic_ranked)
            successor = lineage.pop("candidates")
            req(len(successor) == len(intrinsic_ranked), "lineage candidate count mismatch")
            req([int(r["intrinsic_rank"]) for r in sorted(successor, key=lambda r: int(r["intrinsic_rank"]))] == list(range(1, len(successor) + 1)), "intrinsic rank permutation changed")

            subsets.append(
                {
                    "denominator": int(denominator),
                    "bucket": int(bucket),
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "event_universe_sha256": intrinsic.universe_hash(ids),
                    "equal_budget_k": len(recurrent),
                    "topomodal_summary": topo_summary,
                    "recurrent_summary": recurrent_summary,
                    "lineage_summary": lineage,
                    "successor_candidates": successor,
                    "recurrent_candidates": recurrent,
                }
            )

    pre = {
        "schema": "ORBITTRACE_TOPOMODAL_LINEAGE_INTERLEAVED_V2_PRELABEL",
        "scientific_role": "PRELABEL_TOPOMODAL_LINEAGE_INTERLEAVED_V2",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "intrinsic_source_commit": "312b1b718ae105813de242355142a74e7d377d65",
        "intrinsic_source_blob": INTRINSIC_SOURCE_BLOB,
        "configuration": {
            "candidate_universe": "complete_exact_1284_hierarchy",
            "intrinsic_order": "exact_topomodal_sparse_recovery_v1_order",
            "lineage": "surviving_mode_peak_then_event_id_tie_break",
            "ranking": "lineage_round_asc_then_intrinsic_rank_asc",
            "equal_budget": "K_equals_recurrent_candidate_count_per_subset",
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
    out = a.output / "TOPOMODAL_LINEAGE_INTERLEAVED_V2_PRELABEL.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "prelabel_sha256": intrinsic.sha256(out),
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
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
