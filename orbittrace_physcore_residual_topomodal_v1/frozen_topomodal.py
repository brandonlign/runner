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
from gudhi.clustering.tomato import Tomato
from hdbscan._hdbscan_tree import compute_stability
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
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


def membership_hash(members: tuple[str, ...] | frozenset[str]) -> str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def family_id(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


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


def topomodal_ranked(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = physical_embedding(ordered)

    tree = cKDTree(Z)
    raw_neighbors = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw_neighbors]
    req(len(neighbors) == len(ids), "radius graph row count changed")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing from radius graph at {i}")
        req(all(0 <= j < len(ids) for j in row), "radius graph index out of range")
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
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic changed")

    diagram = np.asarray(model.diagram_, dtype=float)
    if diagram.size:
        req(diagram.ndim == 2 and diagram.shape[1] == 2 and np.all(np.isfinite(diagram)), "invalid ToMATo diagram")
        prominences = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float))
    else:
        prominences = np.empty(0, dtype=float)
    req(len(prominences) == len(children), "finite prominence/merge count mismatch")
    req(np.all(prominences >= -1e-15), "negative ToMATo prominence")
    prominences = np.maximum(prominences, 0.0)

    # Engineering-only invariant: GUDHI's own threshold setter must produce the
    # cluster count implied by the same sorted prominence sequence. No labels are used.
    for threshold in np.unique(prominences):
        model.merge_threshold_ = float(threshold)
        expected_count = int(np.count_nonzero(prominences > threshold) + roots_expected)
        req(int(model.n_clusters_) == expected_count, f"ToMATo threshold/merge-count invariant failed at {threshold}")

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
        member_ix[leaf] = frozenset(int(i) for i in ix)
    req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(ids), "leaf basins do not partition sample")

    parent = np.full(node_count, -1, dtype=np.int64)
    creation = np.zeros(node_count, dtype=float)
    for offset, pair in enumerate(children):
        node = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid ToMATo children at node {node}: {a},{b}")
        req(parent[a] == -1 and parent[b] == -1, "ToMATo hierarchy node has multiple parents")
        ma, mb = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None, "ToMATo child membership missing")
        req(ma.isdisjoint(mb), "ToMATo child memberships overlap")
        member_ix[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node
        creation[node] = float(prominences[offset])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "ToMATo root/component count mismatch")
    req(sum(len(member_ix[int(r)]) for r in roots if member_ix[int(r)] is not None) == len(ids), "ToMATo roots do not partition sample")

    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    structural_rows: list[dict[str, Any]] = []
    for node, ixset in enumerate(member_ix):
        req(ixset is not None, f"missing ToMATo membership node {node}")
        if len(ixset) < MIN_SUPPORT:
            continue
        members = tuple(sorted(ids[i] for i in ixset))
        fh = membership_hash(members)
        is_root = bool(parent[node] == -1)
        vals = rho[np.asarray(sorted(ixset), dtype=np.int64)]
        peak = float(np.max(vals))
        mean = float(np.mean(vals))
        if is_root:
            span: float | None = None
        else:
            par = int(parent[node])
            span_value = float(creation[par] - creation[node])
            req(span_value >= -1e-12, f"negative prominence span node={node}: {span_value}")
            span = max(span_value, 0.0)
        row = {
            "family_id": family_id("TMHSR1", members),
            "family_hash": fh,
            "event_ids": list(members),
            "member_count": len(members),
            "first_node": int(node),
            "is_root": is_root,
            "creation_prominence": float(creation[node]),
            "prominence_span": span,
            "peak_density": peak,
            "mean_density": mean,
        }
        prior = unique.get(members)
        req(prior is None, f"duplicate exact hierarchy membership survived dedupe: {fh}")
        unique[members] = row
        structural_rows.append({"family_hash": fh, "member_count": len(members), "first_node": int(node), "is_root": is_root})

    def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        if bool(row["is_root"]):
            return (0, -float(row["peak_density"]), -float(row["mean_density"]), -int(row["member_count"]), str(row["family_hash"]))
        return (
            1,
            -float(row["prominence_span"]),
            -float(row["peak_density"]),
            -float(row["mean_density"]),
            -int(row["member_count"]),
            str(row["family_hash"]),
        )

    ranked = sorted(unique.values(), key=sort_key)
    for rank, row in enumerate(ranked, 1):
        row["rank"] = int(rank)
    req(len({str(r["family_id"]) for r in ranked}) == len(ranked), "topomodal family ID collision")
    req([int(r["rank"]) for r in ranked] == list(range(1, len(ranked) + 1)), "topomodal rank discontinuity")

    counts = sorted((int(r["member_count"]) for r in ranked), reverse=True)
    return ranked, {
        "candidate_count": len(ranked),
        "leaf_count": leaf_count,
        "internal_node_count": len(children),
        "root_count": len(roots),
        "finite_persistence_point_count": int(len(prominences)),
        "median_radius_degree": float(np.median(degrees)),
        "p90_radius_degree": float(np.quantile(degrees, 0.90)),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(ids)) if counts else 0.0,
        "candidate_rows": sorted(structural_rows, key=lambda r: (-int(r["member_count"]), str(r["family_hash"]))),
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
    structural_rows: list[dict[str, Any]] = []
    for lab, node in enumerate(nodes):
        ix = np.flatnonzero(labels == lab)
        members = tuple(sorted(event_ids[int(i)] for i in ix))
        req(len(members) >= 10, "recurrent comparator sub-10 membership")
        sh = membership_hash(members)
        row = {
            "family_id": family_id("REOM1", members),
            "family_hash": sh,
            "event_ids": list(members),
            "member_count": len(members),
            "node_id": int(node),
            "ordinary_stability": float(ordinary[float(node)]),
            "recurrent_stability": float(recurrent[float(node)]),
        }
        ranked.append(row)
        structural_rows.append({"family_hash": sh, "member_count": len(members)})
    ranked.sort(key=lambda r: (-float(r["recurrent_stability"]), -float(r["ordinary_stability"]), -int(r["member_count"]), str(r["family_id"])))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = int(rank)

    counts = sorted((int(r["member_count"]) for r in ranked), reverse=True)
    return ranked, {
        "candidate_count": len(ranked),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(event_ids)) if counts else 0.0,
        "candidate_rows": sorted(structural_rows, key=lambda r: (-int(r["member_count"]), str(r["family_hash"]))),
    }


def compact_metrics(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], which: str) -> dict[str, Any]:
    vals = [p[which] for p in panels]
    qualified = [int(v["qualified_matches"]) for v in vals]
    return {
        "qualified_total": int(sum(qualified)),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])) if vals else 0.0,
        "precision_mean": float(np.mean([float(v["top100_dominant_precision"]) for v in vals])) if vals else 0.0,
        "fragmentation_mean": float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])) if vals else 0.0,
        "recovered_at_25_total": int(sum(int(v["recovered_at_25"]) for v in vals)),
        "recovered_at_50_total": int(sum(int(v["recovered_at_50"]) for v in vals)),
        "recovered_at_100_total": int(sum(int(v["recovered_at_100"]) for v in vals)),
        "recovered_at_500_total": int(sum(int(v["recovered_at_500"]) for v in vals)),
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
    ap.add_argument("--structural-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    req(sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "authoritative #1284 structural result changed")
    structural = json.loads(a.structural_result_json.read_text())
    req(structural["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 structural prerequisite is not positive")
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected_fits) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "#1284 structural panel set changed")

    parent_runner = load_module(a.parent_runner, "topomodal_sparse_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "topomodal_sparse_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-sparse-recovery-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
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
    runtime_rows: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[topomodal-sparse-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)

            topo, topo_summary = topomodal_ranked(sub_events)
            recurrent, recurrent_summary = recurrent_ranked(parent_runner, X, years, ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(ids), f"#1284 event count mismatch d={denominator} b={bucket}")
            req({str(k): int(v) for k, v in expected["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, f"#1284 annual count mismatch d={denominator} b={bucket}")
            req(expected["topomodal"]["candidate_rows"] == topo_summary["candidate_rows"], f"#1284 topomodal membership mismatch d={denominator} b={bucket}")
            req(int(expected["topomodal"]["candidate_count"]) == len(topo), f"#1284 topomodal candidate count mismatch d={denominator} b={bucket}")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], f"#1284 recurrent membership mismatch d={denominator} b={bucket}")
            req(int(expected["recurrent_eom"]["candidate_count"]) == len(recurrent), f"#1284 recurrent candidate count mismatch d={denominator} b={bucket}")
            req(len(topo) >= len(recurrent) if denominator == FINE_D else True, f"authorized fine candidate noncollapse disappeared d={denominator} b={bucket}")

            row = {
                "denominator": int(denominator),
                "bucket": int(bucket),
                "events_total": len(ids),
                "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                "event_universe_sha256": universe_hash(ids),
                "topomodal_summary": topo_summary,
                "recurrent_summary": recurrent_summary,
                "topomodal_candidates": topo,
                "recurrent_candidates": recurrent,
            }
            frozen_subsets.append(row)
            runtime_rows[(denominator, bucket)] = {
                "ids_by_year": {y: {ids[int(i)] for i in np.flatnonzero(years == y)} for y in YEARS},
                "topomodal": topo,
                "recurrent": recurrent,
            }

    prelabel = {
        "schema": "ORBITTRACE_TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL",
        "scientific_role": "PRELABEL_TOPOMODAL_SPARSE_RECOVERY_V1",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "configuration": {
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
            "radius": RADIUS,
            "min_candidate_support": MIN_SUPPORT,
            "ranking": "roots_first_then_root_peak_density_or_finite_prominence_span_with_density_support_tiebreaks",
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
    prelabel_path = a.output / "TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256(prelabel_path)
    print(f"[topomodal-sparse] immutable prelabel sha256={prelabel_sha}", flush=True)

    # Truth opens only below this line. Candidate construction and ranking are complete and persisted above.
    req(isinstance(hidden_sealed, dict), "hidden truth payload is not the expected event-label mapping")
    panel_results: list[dict[str, Any]] = []
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            fr = runtime_rows[(denominator, bucket)]
            recurrent = fr["recurrent"]
            topo = fr["topomodal"]
            K = len(recurrent)
            req(len(topo) >= K if denominator == FINE_D else True, "fine equal-budget successor list shorter than comparator")
            topo_equal = topo[: min(K, len(topo))]
            req(len(topo_equal) == K, f"topomodal list shorter than recurrent equal budget d={denominator} b={bucket}")
            for year in YEARS:
                annual_ids = set(fr["ids_by_year"][year])
                parent_m = compact_metrics(parent_runner.metrics(recurrent, hidden_sealed, annual_ids))
                succ_m = compact_metrics(parent_runner.metrics(topo_equal, hidden_sealed, annual_ids))
                full_m = compact_metrics(parent_runner.metrics(topo, hidden_sealed, annual_ids))
                panel_results.append(
                    {
                        "denominator": int(denominator),
                        "bucket": int(bucket),
                        "year": int(year),
                        "equal_budget_k": int(K),
                        "parent": parent_m,
                        "topomodal_equal_budget": succ_m,
                        "topomodal_full_diagnostic": full_m,
                        "qualified_nonlower": int(succ_m["qualified_matches"]) >= int(parent_m["qualified_matches"]),
                        "qualified_strict_win": int(succ_m["qualified_matches"]) > int(parent_m["qualified_matches"]),
                    }
                )

    scale_results: dict[str, Any] = {}
    for denominator in (COARSE_D, FINE_D):
        panels = [p for p in panel_results if int(p["denominator"]) == denominator]
        req(len(panels) == 8, f"wrong truth panel count d={denominator}")
        parent_agg = aggregate(panels, "parent")
        succ_agg = aggregate(panels, "topomodal_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in panels)
        wins = sum(bool(p["qualified_strict_win"]) for p in panels)
        scale_results[str(denominator)] = {
            "parent": parent_agg,
            "topomodal_equal_budget": succ_agg,
            "qualified_nonlower_panels": int(nonlower),
            "qualified_strict_win_panels": int(wins),
            "qualified_loss_panels": int(8 - nonlower),
        }

    fine_p = scale_results[str(FINE_D)]["parent"]
    fine_s = scale_results[str(FINE_D)]["topomodal_equal_budget"]
    coarse_p = scale_results[str(COARSE_D)]["parent"]
    coarse_s = scale_results[str(COARSE_D)]["topomodal_equal_budget"]
    gates = {
        "fine_qualified_total_strictly_greater": int(fine_s["qualified_total"]) > int(fine_p["qualified_total"]),
        "fine_qualified_nonlower_at_least_6_of_8": int(scale_results[str(FINE_D)]["qualified_nonlower_panels"]) >= 6,
        "fine_mrr_mean_not_lower": float(fine_s["mrr_mean"]) >= float(fine_p["mrr_mean"]),
        "fine_precision_mean_not_lower": float(fine_s["precision_mean"]) >= float(fine_p["precision_mean"]),
        "fine_fragmentation_mean_not_higher": float(fine_s["fragmentation_mean"]) <= float(fine_p["fragmentation_mean"]),
        "coarse_qualified_total_not_lower": int(coarse_s["qualified_total"]) >= int(coarse_p["qualified_total"]),
        "coarse_qualified_nonlower_at_least_6_of_8": int(scale_results[str(COARSE_D)]["qualified_nonlower_panels"]) >= 6,
        "coarse_mrr_mean_not_lower": float(coarse_s["mrr_mean"]) >= float(coarse_p["mrr_mean"]),
        "coarse_precision_mean_not_lower": float(coarse_s["precision_mean"]) >= float(coarse_p["precision_mean"]),
        "coarse_fragmentation_mean_not_higher": float(coarse_s["fragmentation_mean"]) <= float(coarse_p["fragmentation_mean"]),
    }
    verdict = "PASS_TOPOMODAL_SPARSE_RECOVERY_V1" if all(gates.values()) else "FAIL_TOPOMODAL_SPARSE_RECOVERY_V1"
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_SPARSE_RECOVERY_V1",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "panels": panel_results,
        "scale_aggregates": scale_results,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "TOPOMODAL_SPARSE_RECOVERY_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "scale_aggregates": scale_results, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())