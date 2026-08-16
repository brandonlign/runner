#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
STRUCTURAL_SOURCE_SHA = "dc638e1a272c7eb3d6b709f498a345c94950e15e"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
RADIUS = 1.0


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


def family_id(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def entropy_bits(probs: np.ndarray) -> float:
    p = np.asarray(probs, dtype=float)
    req(np.all(np.isfinite(p)) and np.all(p >= -1e-15), "invalid entropy probabilities")
    p = np.maximum(p, 0.0)
    s = float(np.sum(p))
    req(abs(s - 1.0) <= 1e-10, f"entropy probabilities do not sum to 1: {s}")
    nz = p > 0.0
    return float(-np.sum(p[nz] * np.log2(p[nz])))


def module_entropy(node_masses: np.ndarray, exit_mass: float, total_mass: float) -> float:
    if total_mass <= 1e-15:
        req(float(np.sum(node_masses)) <= 1e-12 and abs(exit_mass) <= 1e-12, "zero module has mass")
        return 0.0
    masses = np.concatenate([np.asarray(node_masses, dtype=float), np.asarray([float(exit_mass)])])
    req(abs(float(np.sum(masses)) - total_mass) <= 1e-10, "module mass mismatch")
    return entropy_bits(masses / total_mass)


def map_equation_score(candidate_ix: np.ndarray, neighbors: list[list[int]], pi: np.ndarray, l1: float) -> dict[str, float]:
    n = len(neighbors)
    mask = np.zeros(n, dtype=bool)
    mask[np.asarray(candidate_ix, dtype=np.int64)] = True
    pi_c = float(np.sum(pi[mask]))
    req(-1e-12 <= pi_c <= 1.0 + 1e-12, "candidate stationary mass invalid")
    pi_c = min(1.0, max(0.0, pi_c))

    if pi_c <= 1e-15 or pi_c >= 1.0 - 1e-15:
        return {"compression_gain": 0.0, "l1": float(l1), "l2": float(l1), "pi_c": float(pi_c), "q_c": 0.0}

    D = float(sum(len(row) for row in neighbors))
    req(D > 0.0, "empty graph flow")
    cut_directed = 0
    for i in np.flatnonzero(mask):
        cut_directed += sum(1 for j in neighbors[int(i)] if not mask[int(j)])
    q_c = float(cut_directed / D)
    req(0.0 <= q_c <= min(pi_c, 1.0 - pi_c) + 1e-12, f"invalid exit mass {q_c}")
    q_total = 2.0 * q_c
    p_c = pi_c + q_c
    p_r = (1.0 - pi_c) + q_c

    if q_total > 0.0:
        h_q = entropy_bits(np.asarray([q_c / q_total, q_c / q_total], dtype=float))
    else:
        h_q = 0.0
    h_c = module_entropy(pi[mask], q_c, p_c)
    h_r = module_entropy(pi[~mask], q_c, p_r)
    l2 = float(q_total * h_q + p_c * h_c + p_r * h_r)
    gain = float(l1 - l2)
    req(np.isfinite(l2) and np.isfinite(gain) and l2 >= -1e-12, "invalid map-equation code length")

    # Candidate/complement symmetry is a binding zero-label invariant.
    pi_r = 1.0 - pi_c
    p_r2 = pi_r + q_c
    p_c2 = pi_c + q_c
    h_r2 = module_entropy(pi[~mask], q_c, p_r2)
    h_c2 = module_entropy(pi[mask], q_c, p_c2)
    l2_swap = float(q_total * h_q + p_r2 * h_r2 + p_c2 * h_c2)
    req(abs(l2 - l2_swap) <= 1e-12, "map-equation candidate/complement symmetry failed")
    return {"compression_gain": gain, "l1": float(l1), "l2": l2, "pi_c": float(pi_c), "q_c": float(q_c)}


def synthetic_audit() -> dict[str, Any]:
    neighbors = [[0, 1], [0, 1], [2, 3], [2, 3]]
    degrees = np.asarray([len(x) for x in neighbors], dtype=float)
    pi = degrees / float(np.sum(degrees))
    l1 = entropy_bits(pi)
    block = map_equation_score(np.asarray([0, 1]), neighbors, pi, l1)
    whole = map_equation_score(np.asarray([0, 1, 2, 3]), neighbors, pi, l1)
    req(block["compression_gain"] > 0.0, "synthetic disconnected block must compress")
    req(abs(whole["compression_gain"]) <= 1e-15, "one-module identity must have zero gain")
    return {"l1": l1, "block_gain": block["compression_gain"], "whole_gain": whole["compression_gain"]}


def map_ranked(structural: Any, events: list[dict[str, Any]], candidates: list[frozenset[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    id_to_ix = {eid: i for i, eid in enumerate(ids)}
    req(len(id_to_ix) == len(ids), "duplicate subset IDs")
    Z = structural.physical_embedding(ordered)
    tree = cKDTree(Z)
    raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw_neighbors]
    req(len(neighbors) == len(ids), "map graph row count changed")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(row.count(i) == 1, f"radius graph diagonal multiplicity changed at {i}")
        req(all(0 <= j < len(ids) for j in row), "radius graph index out of range")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "map graph not symmetric")

    degrees = np.asarray([len(row) for row in neighbors], dtype=float)
    req(np.all(degrees >= 1.0), "nonpositive graph degree")
    D = float(np.sum(degrees))
    pi = degrees / D
    req(abs(float(np.sum(pi)) - 1.0) <= 1e-12, "stationary mass does not sum to one")
    invD = 1.0 / D
    for i, row in enumerate(neighbors):
        req(abs(float(np.sum(np.full(len(row), 1.0 / degrees[i]))) - 1.0) <= 1e-12, "row-stochastic invariant failed")
        for j in row:
            req(abs(float(pi[i] / degrees[i]) - float(pi[int(j)] / degrees[int(j)])) <= 1e-15, "detailed-balance invariant failed")
            req(abs(float(pi[i] / degrees[i]) - invD) <= 1e-15, "directed-edge flow is not canonical")
    l1 = entropy_bits(pi)
    req(l1 >= 0.0 and np.isfinite(l1), "invalid one-module code length")

    rows: list[dict[str, Any]] = []
    for members_fs in candidates:
        members = tuple(sorted(str(x) for x in members_fs))
        ix = np.asarray([id_to_ix[eid] for eid in members], dtype=np.int64)
        score = map_equation_score(ix, neighbors, pi, l1)
        rows.append(
            {
                "family_id": family_id("TMAP1", members),
                "family_hash": structural.member_hash(members_fs),
                "event_ids": list(members),
                "member_count": len(members),
                **score,
            }
        )
    rows.sort(key=lambda r: (-float(r["compression_gain"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = int(rank)
    req([int(r["rank"]) for r in rows] == list(range(1, len(rows) + 1)), "map rank discontinuity")
    req(len({str(r["family_id"]) for r in rows}) == len(rows), "map family ID collision")
    return rows, {
        "l1": float(l1),
        "directed_adjacency_entries": int(D),
        "candidate_count": len(rows),
        "positive_gain_count": int(sum(float(r["compression_gain"]) > 0.0 for r in rows)),
        "zero_gain_count": int(sum(abs(float(r["compression_gain"])) <= 1e-15 for r in rows)),
        "negative_gain_count": int(sum(float(r["compression_gain"]) < 0.0 for r in rows)),
    }


def recurrent_ranked(parent_runner: Any, X: np.ndarray, years: np.ndarray, event_ids: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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
    ordinary = compute_stability(tree)
    recurrent, _annual = parent_runner.recurrent_stability(tree, years)
    labels = np.asarray(parent_runner.eom_labels(tree, recurrent), dtype=np.int64)
    nodes = tuple(int(x) for x in parent_runner.selected_eom_nodes(tree, recurrent))
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(nodes))), "recurrent compact labels no longer map to selected nodes")

    ranked: list[dict[str, Any]] = []
    for lab, node in enumerate(nodes):
        ix = np.flatnonzero(labels == lab)
        members = tuple(sorted(event_ids[int(i)] for i in ix))
        req(len(members) >= 10, "recurrent comparator sub-10 membership")
        ranked.append(
            {
                "family_id": family_id("REOM1", members),
                "family_hash": hashlib.sha256("|".join(members).encode()).hexdigest()[:20],
                "event_ids": list(members),
                "member_count": len(members),
                "node_id": int(node),
                "ordinary_stability": float(ordinary[float(node)]),
                "recurrent_stability": float(recurrent[float(node)]),
            }
        )
    ranked.sort(key=lambda r: (-float(r["recurrent_stability"]), -float(r["ordinary_stability"]), -int(r["member_count"]), str(r["family_id"])))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = int(rank)
    summary_rows = sorted(
        [{"family_hash": r["family_hash"], "member_count": int(r["member_count"])} for r in ranked],
        key=lambda r: (-int(r["member_count"]), str(r["family_hash"])),
    )
    return ranked, {"candidate_count": len(ranked), "candidate_rows": summary_rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structural-runner", type=Path, required=True)
    ap.add_argument("--structural-result-json", type=Path, required=True)
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

    audit = synthetic_audit()
    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    req(sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "authoritative #1284 structural result changed")
    structural_result = json.loads(a.structural_result_json.read_text())
    req(structural_result["scientific_role"] == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "#1284 role changed")
    req(structural_result["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 prerequisite is not positive")
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural_result["fits"]}
    req(set(expected_fits) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "#1284 structural panel set changed")

    structural = load_module(a.structural_runner, "topomodal_map_structural")
    req(tuple(structural.YEARS) == YEARS and tuple(structural.BLIND) == BLIND, "#1284 structural constants changed")
    req(int(structural.COARSE_D) == COARSE_D and int(structural.FINE_D) == FINE_D and tuple(structural.BUCKETS) == BUCKETS, "#1284 subset rule changed")
    req(float(structural.RADIUS) == RADIUS and int(structural.MIN_SUPPORT) == 4, "#1284 graph/support changed")

    parent_runner = load_module(a.parent_runner, "topomodal_map_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "topomodal_map_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-map-equation-ranking-v1-target-excluded"
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

    frozen_subsets: list[dict[str, Any]] = []
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[topomodal-map-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)

            topo_candidates, topo_summary = structural.topomodal_candidates(sub_events)
            map_rows, map_summary = map_ranked(structural, sub_events, topo_candidates)
            recurrent_rows, recurrent_summary = recurrent_ranked(parent_runner, X, years, ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(ids), f"#1284 event count mismatch d={denominator} b={bucket}")
            req({str(k): int(v) for k, v in expected["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, f"#1284 annual count mismatch d={denominator} b={bucket}")
            req(expected["topomodal"]["candidate_rows"] == topo_summary["candidate_rows"], f"#1284 topomodal membership mismatch d={denominator} b={bucket}")
            req(int(expected["topomodal"]["candidate_count"]) == len(map_rows), f"#1284 topomodal candidate count mismatch d={denominator} b={bucket}")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], f"#1284 recurrent membership mismatch d={denominator} b={bucket}")
            req(int(expected["recurrent_eom"]["candidate_count"]) == len(recurrent_rows), f"#1284 recurrent candidate count mismatch d={denominator} b={bucket}")
            req(len(map_rows) >= len(recurrent_rows), f"equal-budget topomodal list shorter than comparator d={denominator} b={bucket}")

            frozen_subsets.append(
                {
                    "denominator": int(denominator),
                    "bucket": int(bucket),
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "event_universe_sha256": universe_hash(ids),
                    "map_equation_summary": map_summary,
                    "topomodal_structural_summary": topo_summary,
                    "recurrent_summary": recurrent_summary,
                    "topomodal_candidates": map_rows,
                    "recurrent_candidates": recurrent_rows,
                }
            )

    prelabel = {
        "schema": "ORBITTRACE_TOPOMODAL_MAP_EQUATION_RANKING_V1_PRELABEL",
        "scientific_role": "PRELABEL_TOPOMODAL_MAP_EQUATION_RANKING_V1",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_source_commit": STRUCTURAL_SOURCE_SHA,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "synthetic_map_equation_audit": audit,
        "configuration": {
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
            "radius": RADIUS,
            "min_candidate_support": 4,
            "graph": "exact_symmetric_radius_neighbor_matrix_including_diagonal_self_neighbor",
            "stationary_measure": "degree_over_total_directed_adjacency_entries",
            "score": "binary_two_level_map_equation_compression_gain_L1_minus_L2",
            "ranking": "compression_gain_desc_then_family_hash_asc",
            "teleportation": False,
            "equal_budget": "K_equals_recurrent_candidate_count_per_subset",
        },
        "subsets": frozen_subsets,
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
    out = a.output / "TOPOMODAL_MAP_EQUATION_RANKING_V1_PRELABEL.json"
    out.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    digest = sha256(out)
    print(f"[topomodal-map] immutable prelabel sha256={digest}", flush=True)
    print(json.dumps({"prelabel_sha256": digest, "subsets": [{"d": r["denominator"], "b": r["bucket"], "topomodal": len(r["topomodal_candidates"]), "recurrent": len(r["recurrent_candidates"]), "positive_gain": r["map_equation_summary"]["positive_gain_count"]} for r in frozen_subsets]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())