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
from gudhi.clustering.tomato import Tomato
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
MIN_SUPPORT = 4


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


def diagram_rows_sorted(rows: np.ndarray) -> np.ndarray:
    arr = np.asarray(rows, dtype=float)
    if arr.size == 0:
        return np.empty((0, 2), dtype=float)
    req(arr.ndim == 2 and arr.shape[1] == 2 and np.all(np.isfinite(arr)), "invalid persistence diagram")
    order = np.lexsort((arr[:, 1], arr[:, 0]))
    return arr[order]


def canonical_death_support(structural: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = structural.physical_embedding(ordered)
    tree = cKDTree(Z)
    raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw_neighbors]
    req(len(neighbors) == len(ids), "radius graph row count changed")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(row.count(i) == 1, f"self-neighbor multiplicity changed at {i}")
        req(all(0 <= j < len(ids) for j in row), "radius graph index out of range")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")

    degrees = np.asarray([len(row) for row in neighbors], dtype=float)
    rho = degrees / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid radius-count density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    leaf_count = int(model.n_leaves_)
    req(leaf_labels.shape == (len(ids),), "wrong ToMATo leaf-label shape")
    req(leaf_count >= 1 and int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "invalid ToMATo leaves")

    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic changed")
    diagram = np.asarray(model.diagram_, dtype=float)
    diagram_sorted = diagram_rows_sorted(diagram)
    prominences = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0, dtype=float)
    req(len(prominences) == len(children) == len(diagram_sorted), "finite persistence/merge count mismatch")
    req(np.all(prominences >= -1e-15), "negative ToMATo prominence")
    prominences = np.maximum(prominences, 0.0)

    # Reconstruct complete #1284 hierarchy memberships first.
    node_count = leaf_count + len(children)
    memberships: list[frozenset[str] | None] = [None] * node_count
    member_ix: list[frozenset[int] | None] = [None] * node_count
    parent = np.full(node_count, -1, dtype=np.int64)
    active_peak = np.full(node_count, np.nan, dtype=float)
    active_key: list[str | None] = [None] * node_count

    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
        ixset = frozenset(int(i) for i in ix)
        member_ix[leaf] = ixset
        members = frozenset(ids[int(i)] for i in ix)
        memberships[leaf] = members
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        req(bool(keys), f"leaf {leaf} has no peak key")
        active_peak[leaf] = peak
        active_key[leaf] = keys[0]
    req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(ids), "leaf basins do not partition sample")

    deaths_all: list[dict[str, Any]] = []
    reconstructed_pairs: list[list[float]] = []
    dying_nodes: set[int] = set()
    for offset, pair in enumerate(children):
        node = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid children at node {node}: {a},{b}")
        req(parent[a] == -1 and parent[b] == -1, "hierarchy node has multiple parents")
        ma, mb = memberships[a], memberships[b]
        ia, ib = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None and ia is not None and ib is not None, "missing child membership")
        req(ma.isdisjoint(mb) and ia.isdisjoint(ib), "child memberships overlap")

        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = active_key[a], active_key[b]
        req(np.isfinite(pa) and np.isfinite(pb) and ka is not None and kb is not None, "missing active mode")
        if pa > pb or (pa == pb and str(ka) < str(kb)):
            winner, loser = a, b
        else:
            winner, loser = b, a

        memberships[node] = frozenset(ma.union(mb))
        member_ix[node] = frozenset(ia.union(ib))
        parent[a] = node
        parent[b] = node
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])

        req(loser not in dying_nodes, f"node {loser} died twice")
        dying_nodes.add(loser)
        loser_members = memberships[loser]
        req(loser_members is not None, "dying membership missing")
        persistence = float(prominences[offset])
        birth = float(active_peak[loser])
        death = float(birth - persistence)
        reconstructed_pairs.append([birth, death])
        deaths_all.append(
            {
                "merge_index": int(offset),
                "merge_node": int(node),
                "dying_node": int(loser),
                "surviving_child": int(winner),
                "active_mode_peak": birth,
                "active_mode_key": str(active_key[loser]),
                "persistence": persistence,
                "reconstructed_death_level": death,
                "event_ids": sorted(loser_members),
                "member_count": len(loser_members),
                "family_hash": structural.member_hash(loser_members),
            }
        )

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root/component count mismatch")
    req(sum(len(memberships[int(r)]) for r in roots if memberships[int(r)] is not None) == len(ids), "roots do not partition sample")
    req(len(deaths_all) == len(children), "not exactly one death per finite merge")
    req(len(dying_nodes) == len(children), "finite feature dying nodes not unique")
    req(all(active_key[int(r)] is not None and np.isfinite(active_peak[int(r)]) for r in roots), "root lost active survivor")

    # Full #1284 candidate summary, independent of the death-support subset.
    full_unique: dict[frozenset[str], dict[str, Any]] = {}
    for node, members in enumerate(memberships):
        req(members is not None, f"missing hierarchy membership node {node}")
        if len(members) < MIN_SUPPORT:
            continue
        full_unique.setdefault(
            members,
            {
                "family_hash": structural.member_hash(members),
                "member_count": len(members),
                "first_node": int(node),
                "is_root": bool(parent[node] == -1),
            },
        )
    full_rows = sorted(full_unique.values(), key=lambda r: (-int(r["member_count"]), str(r["family_hash"])))

    # GUDHI threshold-count invariant for the merge/prominence ordering.
    for threshold in np.unique(prominences):
        model.merge_threshold_ = float(threshold)
        expected_count = int(np.count_nonzero(prominences > threshold) + roots_expected)
        req(int(model.n_clusters_) == expected_count, f"ToMATo threshold/merge-count invariant failed at {threshold}")

    # Reconstructed active-mode persistence pairs must be exactly GUDHI's finite diagram.
    rec_sorted = diagram_rows_sorted(np.asarray(reconstructed_pairs, dtype=float))
    req(rec_sorted.shape == diagram_sorted.shape, "reconstructed persistence pair shape mismatch")
    req(np.allclose(rec_sorted, diagram_sorted, rtol=0.0, atol=1e-12), f"active-mode persistence reconstruction disagrees with GUDHI; max_abs={float(np.max(np.abs(rec_sorted-diagram_sorted))) if rec_sorted.size else 0.0}")

    emitted: list[dict[str, Any]] = []
    seen_members: set[tuple[str, ...]] = set()
    full_members = {tuple(sorted(m)) for m in full_unique}
    for row in deaths_all:
        members = tuple(str(x) for x in row["event_ids"])
        if len(members) < MIN_SUPPORT:
            continue
        req(members in full_members, "death-support candidate not present in full #1284 hierarchy")
        req(members not in seen_members, "duplicate death-support membership")
        seen_members.add(members)
        emitted.append(
            {
                "family_id": family_id("TDEATH1", members),
                "family_hash": str(row["family_hash"]),
                "event_ids": list(members),
                "member_count": int(row["member_count"]),
                "merge_index": int(row["merge_index"]),
                "merge_node": int(row["merge_node"]),
                "dying_node": int(row["dying_node"]),
                "active_mode_peak": float(row["active_mode_peak"]),
                "active_mode_key": str(row["active_mode_key"]),
                "persistence": float(row["persistence"]),
                "reconstructed_death_level": float(row["reconstructed_death_level"]),
            }
        )
    emitted.sort(key=lambda r: (-float(r["persistence"]), str(r["family_hash"])))
    for rank, row in enumerate(emitted, 1):
        row["rank"] = int(rank)
    req([int(r["rank"]) for r in emitted] == list(range(1, len(emitted) + 1)), "death-support rank discontinuity")
    req(len({str(r["family_id"]) for r in emitted}) == len(emitted), "death-support family ID collision")

    return emitted, {
        "full_candidate_count": len(full_unique),
        "full_candidate_rows": full_rows,
        "leaf_count": leaf_count,
        "finite_feature_count": len(children),
        "connected_component_root_count": len(roots),
        "finite_support4_candidate_count": len(emitted),
        "sub_support4_finite_feature_count": int(len(children) - len(emitted)),
        "roots_reported_as_candidates": False,
        "median_radius_degree": float(np.median(degrees)),
        "p90_radius_degree": float(np.quantile(degrees, 0.90)),
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(rec_sorted - diagram_sorted))) if rec_sorted.size else 0.0,
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
    rows = sorted(
        [{"family_hash": r["family_hash"], "member_count": int(r["member_count"])} for r in ranked],
        key=lambda r: (-int(r["member_count"]), str(r["family_hash"])),
    )
    return ranked, {"candidate_count": len(ranked), "candidate_rows": rows}


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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    req(sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "authoritative #1284 structural result changed")
    structural_result = json.loads(a.structural_result_json.read_text())
    req(structural_result["scientific_role"] == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "#1284 role changed")
    req(structural_result["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 prerequisite is not positive")
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural_result["fits"]}
    req(set(expected_fits) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "#1284 panel set changed")

    structural = load_module(a.structural_runner, "topomodal_death_structural")
    req(tuple(structural.YEARS) == YEARS and tuple(structural.BLIND) == BLIND, "#1284 constants changed")
    req(int(structural.COARSE_D) == COARSE_D and int(structural.FINE_D) == FINE_D and tuple(structural.BUCKETS) == BUCKETS, "#1284 subset rule changed")
    req(float(structural.RADIUS) == RADIUS and int(structural.MIN_SUPPORT) == MIN_SUPPORT, "#1284 graph/support changed")

    parent_runner = load_module(a.parent_runner, "topomodal_death_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "topomodal_death_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-death-support-v1-target-excluded"
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
            print(f"[topomodal-death-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)

            death_rows, death_summary = canonical_death_support(structural, sub_events)
            recurrent_rows, recurrent_summary = recurrent_ranked(parent_runner, X, years, ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(ids), f"#1284 event count mismatch d={denominator} b={bucket}")
            req({str(k): int(v) for k, v in expected["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, f"#1284 annual count mismatch d={denominator} b={bucket}")
            req(expected["topomodal"]["candidate_rows"] == death_summary["full_candidate_rows"], f"#1284 full hierarchy membership mismatch d={denominator} b={bucket}")
            req(int(expected["topomodal"]["candidate_count"]) == int(death_summary["full_candidate_count"]), f"#1284 full hierarchy candidate count mismatch d={denominator} b={bucket}")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], f"#1284 recurrent membership mismatch d={denominator} b={bucket}")
            req(int(expected["recurrent_eom"]["candidate_count"]) == len(recurrent_rows), f"#1284 recurrent count mismatch d={denominator} b={bucket}")

            K = min(len(death_rows), len(recurrent_rows))
            frozen_subsets.append(
                {
                    "denominator": int(denominator),
                    "bucket": int(bucket),
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "event_universe_sha256": universe_hash(ids),
                    "equal_budget_k": int(K),
                    "death_support_summary": death_summary,
                    "recurrent_summary": recurrent_summary,
                    "death_support_candidates": death_rows,
                    "recurrent_candidates": recurrent_rows,
                }
            )

    prelabel = {
        "schema": "ORBITTRACE_TOPOMODAL_DEATH_SUPPORT_V1_PRELABEL",
        "scientific_role": "PRELABEL_TOPOMODAL_DEATH_SUPPORT_V1",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_source_commit": STRUCTURAL_SOURCE_SHA,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "configuration": {
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
            "radius": RADIUS,
            "min_candidate_support": MIN_SUPPORT,
            "candidate_semantics": "one_dying_child_support_per_finite_tomato_persistence_feature",
            "infinite_root_features_reported": False,
            "survival_rule": "larger_active_mode_peak_then_lexicographically_smaller_mode_key",
            "ranking": "finite_persistence_desc_then_family_hash_asc",
            "equal_budget": "min(successor_candidate_count,recurrent_candidate_count)_both_methods_truncated",
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
    out = a.output / "TOPOMODAL_DEATH_SUPPORT_V1_PRELABEL.json"
    out.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    digest = sha256(out)
    print(f"[topomodal-death] immutable prelabel sha256={digest}", flush=True)
    print(json.dumps({"prelabel_sha256": digest, "subsets": [{"d": r["denominator"], "b": r["bucket"], "death": len(r["death_support_candidates"]), "recurrent": len(r["recurrent_candidates"]), "K": r["equal_budget_k"]} for r in frozen_subsets]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
