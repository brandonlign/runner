#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def event_field(row: dict[str, Any], names: Iterable[str]) -> float:
    for name in names:
        if name in row and row[name] is not None:
            value = float(row[name])
            if math.isfinite(value):
                return value
    raise RuntimeError(f"event missing required field aliases {tuple(names)}; keys={sorted(row)[:40]}")


def event_id(row: dict[str, Any]) -> str:
    for name in ("id", "event_id", "eventId"):
        if name in row:
            return str(row[name])
    raise RuntimeError("event row lacks ID")


def normalize_event(row: dict[str, Any], year: int) -> dict[str, Any]:
    eid = event_id(row)
    sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
    lon = event_field(row, ("sun_lon", "sun_centered_longitude", "sun_centered_lon", "lam_sce"))
    lat = event_field(row, ("ecl_lat", "ecliptic_latitude", "lat_sce", "beta"))
    vg = event_field(row, ("vg", "v_g", "geocentric_speed", "velocity"))
    req(vg > 0.0, f"nonpositive speed for {eid}")
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected-region event reached dual-year HDBSCAN: {eid}")
    req(str(eid).startswith(str(year)), f"event ID/year mismatch: {eid} vs {year}")
    return {"id": eid, "year": int(year), "sol": sol, "lon": lon, "lat": lat, "vg": vg}


def geo_matrix(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    return np.column_stack((
        np.cos(sol),
        np.sin(sol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat),
        vg / 72.0,
    ))


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def member_hash(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def hdbscan_model(X: np.ndarray) -> hdbscan.HDBSCAN:
    return hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)


def pooled_recurrent_parent(events: list[dict[str, Any]], X: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    model = hdbscan_model(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    parent_labels = eom_labels(tree, ordinary)
    req(canonical_partition(model.labels_) == canonical_partition(parent_labels), "pooled vanilla extraction diverged")
    recurrent, annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, recurrent)
    nodes = selected_eom_nodes(tree, recurrent)
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(nodes))), "pooled recurrent compact labels no longer map to selected nodes")
    out = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(events[int(i)]["id"] for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"pooled recurrent subminimum cluster {node}")
        out.append({
            "family_id": member_hash("REOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "recurrent_stability": float(recurrent[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (-f["recurrent_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
    return out, {
        "selected_nodes": list(nodes),
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in out).encode()).hexdigest(),
        "annual_recurrent_stability_sha256": hashlib.sha256(json.dumps({str(k): list(v) for k, v in sorted(annual.items())}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


def annual_clusters(year: int, events: list[dict[str, Any]], X: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    req(len(events) == X.shape[0] and len(events) > 0, f"bad annual input shape for {year}")
    model = hdbscan_model(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    labels = eom_labels(tree, ordinary)
    req(canonical_partition(model.labels_) == canonical_partition(labels), f"annual vanilla extraction diverged in {year}")
    nodes = selected_eom_nodes(tree, ordinary)
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(nodes))), f"annual compact labels no longer map to selected nodes in {year}")
    rows = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(events[int(i)]["id"] for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"annual subminimum cluster {year} node={node}")
        centroid = np.mean(X[idx], axis=0)
        req(centroid.shape == (6,) and np.all(np.isfinite(centroid)), f"bad centroid {year} node={node}")
        rows.append({
            "year": int(year),
            "node_id": int(node),
            "cluster_id": member_hash(f"DYR{year}", members),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
            "normalized_stability": float(ordinary[float(node)] / len(events)),
            "centroid": [float(x) for x in centroid],
        })
    rows.sort(key=lambda r: (r["node_id"], r["cluster_id"]))
    return rows, {
        "selected_nodes": list(nodes),
        "cluster_count": len(rows),
        "partition_sha256": hashlib.sha256(repr(canonical_partition(labels)).encode()).hexdigest(),
    }


def reciprocal_families(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    req(a and b, "reciprocal matching requires nonempty annual cluster sets")
    ca = np.asarray([r["centroid"] for r in a], dtype=float)
    cb = np.asarray([r["centroid"] for r in b], dtype=float)
    req(ca.ndim == cb.ndim == 2 and ca.shape[1] == cb.shape[1] == 6, "centroid dimension changed")
    # Explicit pairwise Euclidean distances in the inherited GEO6 geometry.
    d2 = np.sum((ca[:, None, :] - cb[None, :, :]) ** 2, axis=2)
    req(np.all(np.isfinite(d2)), "nonfinite cross-year centroid distance")

    a_to_b: list[int] = []
    for i in range(len(a)):
        j = min(range(len(b)), key=lambda x: (float(d2[i, x]), int(b[x]["node_id"]), str(b[x]["cluster_id"])))
        a_to_b.append(int(j))
    b_to_a: list[int] = []
    for j in range(len(b)):
        i = min(range(len(a)), key=lambda x: (float(d2[x, j]), int(a[x]["node_id"]), str(a[x]["cluster_id"])))
        b_to_a.append(int(i))

    out = []
    pairs = []
    for i, j in enumerate(a_to_b):
        if b_to_a[j] != i:
            continue
        left = a[i]
        right = b[j]
        members = tuple(sorted(set(map(str, left["event_ids"])) | set(map(str, right["event_ids"]))))
        req(len(members) == int(left["member_count"]) + int(right["member_count"]), "cross-year member IDs overlap unexpectedly")
        score = min(float(left["normalized_stability"]), float(right["normalized_stability"]))
        distance = math.sqrt(float(d2[i, j]))
        fid = member_hash("DYRHDB1", members)
        row = {
            "family_id": fid,
            "event_ids": list(members),
            "member_count": len(members),
            "score": float(score),
            "centroid_distance": float(distance),
            "year_nodes": {str(left["year"]): int(left["node_id"]), str(right["year"]): int(right["node_id"])},
            "year_cluster_ids": {str(left["year"]): str(left["cluster_id"]), str(right["year"]): str(right["cluster_id"])},
            "year_normalized_stability": {str(left["year"]): float(left["normalized_stability"]), str(right["year"]): float(right["normalized_stability"])},
        }
        out.append(row)
        pairs.append((int(left["node_id"]), int(right["node_id"])))
    out.sort(key=lambda f: (-f["score"], f["centroid_distance"], -f["member_count"], f["family_id"]))
    return out, {
        "reciprocal_pair_count": len(out),
        "reciprocal_node_pairs": [list(x) for x in pairs],
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in out).encode()).hexdigest(),
    }


def eligible_labels(hidden: dict[str, str], annual_ids: set[str]) -> dict[str, int]:
    counts = Counter(label for eid, label in hidden.items() if eid in annual_ids and label != "SPORADIC")
    return {label: n for label, n in counts.items() if n >= 4}


def truth(f: dict[str, Any], hidden: dict[str, str], eligible: dict[str, int]) -> dict[str, Any]:
    ids = [str(x) for x in f["event_ids"]]
    counts = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, total in eligible.items():
        ov = int(counts.get(label, 0))
        if ov <= 0:
            continue
        p = ov / max(len(ids), 1)
        r = ov / total
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        rows.append((f1, p, ov, label, r))
    if not rows:
        return {"positive": False, "best_label": None, "dominant_precision": 0.0}
    f1, p, ov, label, r = max(rows, key=lambda x: (x[0], x[1], x[2], x[3]))
    non = counts.copy()
    non.pop("SPORADIC", None)
    dominant = max(non.values(), default=0) / max(len(ids), 1)
    return {
        "positive": bool(p >= 0.5 and ov >= 4),
        "best_label": label,
        "f1": float(f1),
        "precision": float(p),
        "recall": float(r),
        "overlap": int(ov),
        "dominant_precision": float(dominant),
    }


def metrics(pooled: list[dict[str, Any]], hidden: dict[str, str], annual_ids: set[str]) -> dict[str, Any]:
    eligible = eligible_labels(hidden, annual_ids)
    first: dict[str, int | None] = {label: None for label in eligible}
    fragments: Counter[str] = Counter()
    top_prec: list[float] = []
    for rank, pooled_f in enumerate(pooled, 1):
        annual_f = {
            "family_id": pooled_f["family_id"],
            "event_ids": [eid for eid in pooled_f["event_ids"] if eid in annual_ids],
        }
        t = truth(annual_f, hidden, eligible)
        if rank <= 100:
            top_prec.append(float(t["dominant_precision"]))
        if t["positive"] and t["best_label"] in eligible:
            label = str(t["best_label"])
            fragments[label] += int(rank <= 500)
            if first[label] is None:
                first[label] = rank
    represented = [label for label, rank in first.items() if rank is not None]
    frag = [fragments[label] for label in represented if first[label] is not None and first[label] <= 500]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(represented),
        "recovered_at_25": sum(r is not None and r <= 25 for r in first.values()),
        "recovered_at_50": sum(r is not None and r <= 50 for r in first.values()),
        "recovered_at_100": sum(r is not None and r <= 100 for r in first.values()),
        "recovered_at_500": sum(r is not None and r <= 500 for r in first.values()),
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "mrr": float(np.mean([1.0 / r for r in first.values() if r is not None])) if represented else 0.0,
        "fragmentation_median_top500": float(np.median(frag)) if frag else 0.0,
        "first_rank_by_label": first,
    }


def annual_gate(parent: dict[str, Any], successor: dict[str, Any]) -> dict[str, bool]:
    return {
        "recovered_at_50_not_lower": int(successor["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(successor["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": float(successor["top100_dominant_precision"]) >= float(parent["top100_dominant_precision"]),
        "mrr_not_lower": float(successor["mrr"]) >= float(parent["mrr"]),
        "fragmentation_not_higher": float(successor["fragmentation_median_top500"]) <= float(parent["fragmentation_median_top500"]),
    }


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

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = load_module(a.quality_source, "dyrhdb_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-dual-year-reciprocal-hdbscan-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict[str, Any]]] = {}
    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events_by_year[year] = rows
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    X_by_year = {y: geo_matrix(events_by_year[y]) for y in YEARS}
    X = np.vstack([X_by_year[y] for y in YEARS])

    parent_candidates, parent_diag = pooled_recurrent_parent(events, X)
    annual: dict[int, list[dict[str, Any]]] = {}
    annual_diag: dict[int, dict[str, Any]] = {}
    for y in YEARS:
        annual[y], annual_diag[y] = annual_clusters(y, events_by_year[y], X_by_year[y])
    successor_candidates, successor_diag = reciprocal_families(annual[YEARS[0]], annual[YEARS[1]])

    mechanism_active = bool(
        successor_diag["candidate_order_sha256"] != parent_diag["candidate_order_sha256"]
        or len(successor_candidates) != len(parent_candidates)
    )
    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1",
        "events_total": len(events),
        "events_by_year": {str(y): len(events_by_year[y]) for y in YEARS},
        "parent": {**parent_diag, "candidates": parent_candidates},
        "annual": {str(y): {**annual_diag[y], "clusters": annual[y]} for y in YEARS},
        "successor": {**successor_diag, "candidates": successor_candidates},
        "mechanism_active": mechanism_active,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2020_2021_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Hidden shower map is not inspected until all annual clusters, reciprocal pairs,
    # exact memberships, parent candidates, and both rank orders are persisted above.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events_by_year[y]} for y in YEARS}
    req(all(any(eid in ids_by_year[y] for y in YEARS) for eid in hidden), "label outside pooled accessible event IDs")

    parent_metrics = {str(y): metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(strict_100 and mechanism_active and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(events_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "annual_cluster_counts": {str(y): len(annual[y]) for y in YEARS},
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "frozen_matching": {
            "annual_hierarchies": "independent",
            "centroid_space": "same_GEO6",
            "matching": "reciprocal_nearest_centroid",
            "distance_threshold": None,
            "score": "min(ordinary_stability_2022/N_2022, ordinary_stability_2023/N_2023)",
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2020_2021_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events": result["events_by_year"],
        "annual_cluster_counts": result["annual_cluster_counts"],
        "parent_candidates": len(parent_candidates),
        "successor_candidates": len(successor_candidates),
        "mechanism_active": mechanism_active,
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
