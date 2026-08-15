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

import recurrent_eom as reom
from density_synchronous_eom import density_synchronous_stability
from stratified_core import K_YEAR, condensed_tree_from_injected_core, stratified_core_distances

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
EXPECTED_PARENT_COUNT = 2094
EXPECTED_PARENT = {
    "2022": {
        "qualified_matches": 236,
        "recovered_at_25": 22,
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "recovered_at_500": 192,
        "top100_dominant_precision": 0.7873334042799703,
        "mrr": 0.022505373166085363,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "qualified_matches": 244,
        "recovered_at_25": 23,
        "recovered_at_50": 46,
        "recovered_at_100": 90,
        "recovered_at_500": 191,
        "top100_dominant_precision": 0.7898245986099988,
        "mrr": 0.02203028490649908,
        "fragmentation_median_top500": 1.0,
    },
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(a: np.ndarray) -> str:
    x = np.asarray(a)
    return hashlib.sha256(x.tobytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return array_sha(tree)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def sync_candidates(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
    base_runner: Any,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        out.append({
            # Keep the exact #1263 content-derived tie breaker; method identity must not alter equal-score ordering.
            "family_id": base_runner.member_hash("DSEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def exact_parent_check(metrics: dict[str, dict[str, Any]]) -> None:
    integer_keys = (
        "qualified_matches", "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500"
    )
    float_keys = ("top100_dominant_precision", "mrr", "fragmentation_median_top500")
    for year, expected in EXPECTED_PARENT.items():
        got = metrics[year]
        for key in integer_keys:
            req(int(got[key]) == int(expected[key]), f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}")
        for key in float_keys:
            req(
                bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)),
                f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}",
            )


def core_summary(core: np.ndarray, annual: dict[str, np.ndarray]) -> dict[str, Any]:
    def one(a: np.ndarray) -> dict[str, Any]:
        a = np.asarray(a, dtype=np.float64)
        return {
            "sha256": array_sha(a),
            "min": float(np.min(a)),
            "median": float(np.median(a)),
            "p90": float(np.quantile(a, 0.9)),
            "p99": float(np.quantile(a, 0.99)),
            "max": float(np.max(a)),
        }
    return {
        "k_year": K_YEAR,
        "core_strat": one(core),
        "d_2022": one(annual["d_2022"]),
        "d_2023": one(annual["d_2023"]),
        "core_is_pointwise_max": bool(np.array_equal(core, np.maximum(annual["d_2022"], annual["d_2023"]))),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    base = load_module(a.parent_runner, "density_sync_stratified_frozen_parent_runner")
    req(tuple(base.YEARS) == YEARS, "parent year domain changed")
    req(tuple(float(x) for x in base.BLIND) == BLIND, "parent blind interval changed")
    req(int(base.MIN_CLUSTER_SIZE) == MIN_CLUSTER_SIZE and int(base.MIN_SAMPLES) == MIN_SAMPLES, "parent HDBSCAN size parameters changed")
    req(sha(a.quality_source) == base.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == base.V8_RESULT_SHA, "frozen GMN support artifact changed")

    qmod = base.load_module(a.quality_source, "dsscore_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = base.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = base.MONTH_KEYS
    support.CORPUS = "orbittrace-density-sync-stratified-core-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, catalogue_base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(catalogue_base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(base.MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [base.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    X = base.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")

    # Reconstruct the exact promoted #1263 proposal on the ordinary pooled hierarchy.
    parent_model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    parent_tree = parent_model.condensed_tree_._raw_tree
    parent_ordinary = compute_stability(parent_tree)
    parent_sync, _parent_annual, _parent_reconstructed = density_synchronous_stability(parent_tree, years)
    parent_labels = reom.eom_labels(parent_tree, parent_sync)
    parent_nodes = reom.selected_eom_nodes(parent_tree, parent_sync)
    parent_candidates = sync_candidates(parent_labels, parent_nodes, events, parent_ordinary, parent_sync, base)
    req(len(parent_candidates) == EXPECTED_PARENT_COUNT, f"#1263 candidate count changed: {len(parent_candidates)}")

    # Sole successor change: balanced annual 5+5 core support before hierarchy construction.
    strat_core, annual_core = stratified_core_distances(X, years)
    successor_tree, _successor_sl, _successor_mst = condensed_tree_from_injected_core(X, strat_core)
    successor_ordinary = compute_stability(successor_tree)
    successor_sync, _successor_annual, _successor_reconstructed = density_synchronous_stability(successor_tree, years)
    successor_labels = reom.eom_labels(successor_tree, successor_sync)
    successor_nodes = reom.selected_eom_nodes(successor_tree, successor_sync)
    successor_candidates = sync_candidates(
        successor_labels, successor_nodes, events, successor_ordinary, successor_sync, base
    )

    parent_order_sha = ordered_membership_sha(parent_candidates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    parent_tree_digest = tree_sha(parent_tree)
    successor_tree_digest = tree_sha(successor_tree)
    mechanism_active = bool(
        parent_tree_digest != successor_tree_digest
        or parent_order_sha != successor_order_sha
        or parent_nodes != successor_nodes
    )

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_DENSITY_SYNC_STRATIFIED_CORE_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "parent_tree_sha256": parent_tree_digest,
        "successor_tree_sha256": successor_tree_digest,
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "stratified_core": core_summary(strat_core, annual_core),
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "successor_synchronous_stability": {str(int(k)): float(v) for k, v in sorted(successor_sync.items())},
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "efn_access": False,
        "asfn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "DENSITY_SYNC_STRATIFIED_CORE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_digest = sha(prelabel_path)

    # Hidden truth is first used only after the full proposal above is fixed on disk.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")
    parent_metrics = {str(y): base.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    exact_parent_check(parent_metrics)
    successor_metrics = {str(y): base.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): base.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT"
        if passed else
        "FAIL_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_digest,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_tree_sha256": parent_tree_digest,
        "successor_tree_sha256": successor_tree_digest,
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "sole_successor_change": "balanced_annual_5_plus_5_stratified_core_before_unchanged_density_synchronous_extraction",
        "k_year": K_YEAR,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "efn_access": False,
        "asfn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
