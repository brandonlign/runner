#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
RADIUS = 1.0
MIN_SUPPORT = 4
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


def density_hash(x: np.ndarray) -> str:
    arr = np.asarray(x, dtype="<f8")
    return hashlib.sha256(arr.tobytes(order="C")).hexdigest()


def recurrent_topomodal_ranked(intrinsic: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "both years required for recurrent density")
    totals = {y: int(np.sum(years == y)) for y in YEARS}
    req(all(totals[y] > 0 for y in YEARS), "empty annual recurrent-density panel")

    Z = intrinsic.physical_embedding(ordered)
    tree = cKDTree(Z)
    raw = tree.query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    req(len(neighbors) == len(ids), "radius graph row count")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing from radius graph {i}")
        req(all(0 <= j < len(ids) for j in row), "radius graph index")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")

    d22 = np.fromiter((sum(1 for j in row if years[j] == 2022) for row in neighbors), dtype=np.int64, count=len(ids))
    d23 = np.fromiter((sum(1 for j in row if years[j] == 2023) for row in neighbors), dtype=np.int64, count=len(ids))
    rho22 = d22.astype(float) / float(totals[2022])
    rho23 = d23.astype(float) / float(totals[2023])
    rho = np.minimum(rho22, rho23)
    rho_swap = np.minimum(rho23, rho22)

    req(np.all(np.isfinite(rho22)) and np.all(np.isfinite(rho23)) and np.all(np.isfinite(rho)), "nonfinite recurrent density")
    req(np.all(rho >= 0.0), "negative recurrent density")
    req(np.all(rho <= rho22) and np.all(rho <= rho23), "recurrent minimum identity")
    req(np.array_equal(rho, rho_swap), "year-swap invariance failed")
    eq = rho22 == rho23
    req(np.array_equal(rho[eq], rho22[eq]), "identical annual-density identity failed")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    req(leaf_labels.shape == (len(ids),), "wrong ToMATo leaf-label shape")
    leaf_count = int(model.n_leaves_)
    req(leaf_count >= 1, "no ToMATo leaves")
    req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "noncontiguous ToMATo leaves")

    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic")

    diagram = np.asarray(model.diagram_, dtype=float)
    if diagram.size:
        req(diagram.ndim == 2 and diagram.shape[1] == 2 and np.all(np.isfinite(diagram)), "invalid ToMATo diagram")
        prominences = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float))
    else:
        prominences = np.empty(0, dtype=float)
    req(len(prominences) == len(children), "finite prominence/merge count")
    req(np.all(prominences >= -1e-15), "negative ToMATo prominence")
    prominences = np.maximum(prominences, 0.0)

    for threshold in np.unique(prominences):
        model.merge_threshold_ = float(threshold)
        expected_count = int(np.count_nonzero(prominences > threshold) + roots_expected)
        req(int(model.n_clusters_) == expected_count, f"ToMATo threshold identity failed at {threshold}")

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
        member_ix[leaf] = frozenset(int(i) for i in ix)
    req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(ids), "leaf partition")

    parent = np.full(node_count, -1, dtype=np.int64)
    creation = np.zeros(node_count, dtype=float)
    for off, pair in enumerate(children):
        node = leaf_count + off
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid ToMATo children at {node}")
        req(parent[a] == -1 and parent[b] == -1, "hierarchy node has multiple parents")
        ma, mb = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None and ma.isdisjoint(mb), "child membership invalid")
        member_ix[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node
        creation[node] = float(prominences[off])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root count")
    req(sum(len(member_ix[int(r)]) for r in roots if member_ix[int(r)] is not None) == len(ids), "root partition")

    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    structural_rows: list[dict[str, Any]] = []
    for node, ixset in enumerate(member_ix):
        req(ixset is not None, f"missing hierarchy membership {node}")
        if len(ixset) < MIN_SUPPORT:
            continue
        members = tuple(sorted(ids[i] for i in ixset))
        fh = intrinsic.membership_hash(members)
        is_root = bool(parent[node] == -1)
        ix = np.asarray(sorted(ixset), dtype=np.int64)
        vals = rho[ix]
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
            "family_id": intrinsic.family_id("RDTM1", members),
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
        req(members not in unique, f"duplicate exact hierarchy membership {fh}")
        unique[members] = row
        structural_rows.append({"family_hash": fh, "member_count": len(members), "first_node": int(node), "is_root": is_root})

    def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        if bool(row["is_root"]):
            return (0, -float(row["peak_density"]), -float(row["mean_density"]), -int(row["member_count"]), str(row["family_hash"]))
        return (1, -float(row["prominence_span"]), -float(row["peak_density"]), -float(row["mean_density"]), -int(row["member_count"]), str(row["family_hash"]))

    ranked = sorted(unique.values(), key=sort_key)
    for rank, row in enumerate(ranked, 1):
        row["rank"] = int(rank)
    req([int(r["rank"]) for r in ranked] == list(range(1, len(ranked) + 1)), "rank discontinuity")
    req(len({str(r["family_id"]) for r in ranked}) == len(ranked), "family ID collision")

    structural_rows.sort(key=lambda r: (str(r["family_hash"]), int(r["member_count"]), int(r["first_node"]), bool(r["is_root"])))
    return ranked, {
        "candidate_count": len(ranked),
        "candidate_rows": structural_rows,
        "leaf_count": leaf_count,
        "finite_merge_count": len(children),
        "root_count": len(roots),
        "annual_event_totals": {str(y): totals[y] for y in YEARS},
        "rho_rec_sha256": density_hash(rho),
        "rho22_sha256": density_hash(rho22),
        "rho23_sha256": density_hash(rho23),
        "zero_recurrent_density_count": int(np.sum(rho == 0.0)),
        "positive_recurrent_density_count": int(np.sum(rho > 0.0)),
        "rho_rec_max": float(np.max(rho)),
        "rho_rec_mean": float(np.mean(rho)),
        "median_radius_degree": float(np.median([len(r) for r in neighbors])),
        "p90_radius_degree": float(np.quantile([len(r) for r in neighbors], 0.90)),
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

    intrinsic = load_module(a.intrinsic_runner, "rdtm_intrinsic")
    req(intrinsic.sha256(a.quality_source) == QUALITY_SHA256, "GMN utility hash")
    req(intrinsic.sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 result hash")
    req(intrinsic.sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "structural result hash")
    req(tuple(intrinsic.YEARS) == YEARS and tuple(intrinsic.BLIND) == BLIND, "intrinsic constants")
    req(float(intrinsic.RADIUS) == RADIUS and int(intrinsic.MIN_SUPPORT) == MIN_SUPPORT, "#1284 radius/support changed")

    structural = json.loads(a.structural_result_json.read_text())
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected_fits) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "structural panel set")

    parent = load_module(a.parent_runner, "rdtm_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support")

    q = load_module(a.quality_source, "rdtm_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-density-topomodal-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base_source, _scorer = support.load_sources(a)
    scan, _cal, hidden_unused, sources = support.parse_catalogue(base_source)
    del hidden_unused
    req(sorted(scan) == list(YEARS), "years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        events.extend(parent.normalize_event(row, year) for row in raw)
    req(len(events) == 738682, f"pooled count changed {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived")

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
            print(f"[rdtm-prelabel] d={denominator} b={bucket} n={len(ids)}", flush=True)

            successor, successor_summary = recurrent_topomodal_ranked(intrinsic, sub_events)
            recurrent, recurrent_summary = intrinsic.recurrent_ranked(parent, X, years, ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(ids), "#1284 event count mismatch")
            req({str(k): int(v) for k, v in expected["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, "annual count mismatch")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], "parent membership mismatch")
            req(int(expected["recurrent_eom"]["candidate_count"]) == len(recurrent), "parent count mismatch")
            req(len(successor) >= len(recurrent), f"successor candidate shortage d={denominator} b={bucket}: {len(successor)} < {len(recurrent)}")

            subsets.append({
                "denominator": int(denominator),
                "bucket": int(bucket),
                "events_total": len(ids),
                "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                "event_universe_sha256": intrinsic.universe_hash(ids),
                "equal_budget_k": len(recurrent),
                "successor_summary": successor_summary,
                "recurrent_summary": recurrent_summary,
                "successor_candidates": successor,
                "recurrent_candidates": recurrent,
            })

    pre = {
        "schema": "ORBITTRACE_RECURRENT_DENSITY_TOPOMODAL_V1_PRELABEL",
        "scientific_role": "PRELABEL_RECURRENT_DENSITY_TOPOMODAL_V1",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "intrinsic_source_commit": "312b1b718ae105813de242355142a74e7d377d65",
        "intrinsic_source_blob": INTRINSIC_SOURCE_BLOB,
        "configuration": {
            "graph": "exact_radius_1_physical_embedding_1284",
            "density": "min(radius_year_count_over_year_total_2022,radius_year_count_over_year_total_2023)",
            "candidate_universe": "complete_tomato_hierarchy_support_ge_4",
            "ranking": "exact_1284_native_rule_on_recurrent_density",
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
    out = a.output / "RECURRENT_DENSITY_TOPOMODAL_V1_PRELABEL.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "prelabel_sha256": intrinsic.sha256(out),
        "subsets": [{
            "d": s["denominator"], "b": s["bucket"], "successor": len(s["successor_candidates"]),
            "recurrent": len(s["recurrent_candidates"]), "K": s["equal_budget_k"],
            "positive_density": s["successor_summary"]["positive_recurrent_density_count"],
            "zero_density": s["successor_summary"]["zero_recurrent_density_count"],
        } for s in subsets],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
