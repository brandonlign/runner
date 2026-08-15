#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
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
from null_calibration import (
    NULL_REPLICATES,
    calibrate_candidates,
    permuted_solar_longitude_matrix,
)

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
EXPECTED_PARENT_COUNT = 2094
REQUIRED_TOTAL_AT100_GAIN = 5
EXPECTED_PARENT = {
    "2022": {
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7873334042799703,
        "mrr": 0.022505373166085363,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "recovered_at_50": 46,
        "recovered_at_100": 90,
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


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def sync_candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
    parent_runner: Any,
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        out.append({
            "family_id": parent_runner.member_hash("DSEOM1", members),
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


def null_rows_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    synchronous: dict[float, float],
) -> list[tuple[int, float]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "null compact labels no longer map contiguously to nodes")
    rows: list[tuple[int, float]] = []
    for lab, node in enumerate(selected_nodes):
        n = int(np.sum(labels == lab))
        req(n >= MIN_CLUSTER_SIZE, f"null selected cluster below minimum: node={node}")
        s = float(synchronous[float(node)])
        req(np.isfinite(s) and s >= 0.0, f"invalid null synchronous stability: node={node}, s={s}")
        rows.append((n, s))
    return rows


def verify_parent_metrics(metrics: dict[str, dict[str, Any]]) -> None:
    for year, expected in EXPECTED_PARENT.items():
        got = metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(
                bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)),
                f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}",
            )


def fit_hdbscan(X: np.ndarray) -> hdbscan.HDBSCAN:
    return hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)


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

    parent_runner = load_module(a.parent_runner, "ncp_frozen_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(parent_runner.MIN_CLUSTER_SIZE == MIN_CLUSTER_SIZE, "parent min_cluster_size changed")
    req(parent_runner.MIN_SAMPLES == MIN_SAMPLES, "parent min_samples changed")
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")

    qmod = parent_runner.load_module(a.quality_source, "ncp_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = parent_runner.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = parent_runner.MONTH_KEYS
    support.CORPUS = "orbittrace-null-calibrated-persistence-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(parent_runner.MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} count")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent_runner.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    sols = np.asarray([e["sol"] for e in events], dtype=float)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")

    # Real-data parent catalogue: exact #1263 density-synchronous recurrent-EOM.
    model = fit_hdbscan(X)
    tree = model.condensed_tree_._raw_tree
    real_tree_sha = tree_sha(tree)
    ordinary = compute_stability(tree)
    synchronous, _annual, _reconstructed = density_synchronous_stability(tree, years)
    parent_labels = reom.eom_labels(tree, synchronous)
    parent_nodes = reom.selected_eom_nodes(tree, synchronous)
    parent_candidates = sync_candidates_from_labels(
        parent_labels, parent_nodes, events, ordinary, synchronous, parent_runner
    )
    req(len(parent_candidates) == EXPECTED_PARENT_COUNT, f"#1263 parent candidate count changed: {len(parent_candidates)}")
    parent_order_sha = ordered_membership_sha(parent_candidates)
    del model, tree, ordinary, synchronous, parent_labels, parent_nodes
    gc.collect()

    # Survey-preserving coherence-destroying null ensemble. No truth is touched.
    null_replicates: list[list[tuple[int, float]]] = []
    null_reports: list[dict[str, Any]] = []
    for rep in range(NULL_REPLICATES):
        Xnull, perm_report = permuted_solar_longitude_matrix(X, sols, years, rep)
        null_model = fit_hdbscan(Xnull)
        null_tree = null_model.condensed_tree_._raw_tree
        null_sync, _null_annual, _null_reconstructed = density_synchronous_stability(null_tree, years)
        null_labels = reom.eom_labels(null_tree, null_sync)
        null_nodes = reom.selected_eom_nodes(null_tree, null_sync)
        rows = null_rows_from_labels(null_labels, null_nodes, null_sync)
        req(len(rows) > 0, f"null replicate {rep} selected zero candidates")
        null_replicates.append(rows)
        null_reports.append({
            **perm_report,
            "candidate_count": len(rows),
            "condensed_tree_sha256": tree_sha(null_tree),
            "max_member_count": max(int(n) for n, _s in rows),
            "max_synchronous_stability": max(float(s) for _n, s in rows),
            "candidates": [
                {"member_count": int(n), "synchronous_stability": float(s)}
                for n, s in rows
            ],
        })
        print(json.dumps({
            "null_replicate": rep,
            "candidate_count": len(rows),
            "moved_2022": perm_report["years"]["2022"]["moved_fraction"],
            "moved_2023": perm_report["years"]["2023"]["moved_fraction"],
        }, sort_keys=True), flush=True)
        del Xnull, null_model, null_tree, null_sync, null_labels, null_nodes, rows
        gc.collect()

    # Reconstruct the exact real parent catalogue once more from the unchanged
    # real matrix so the successor prelabel contains complete memberships.
    model2 = fit_hdbscan(X)
    tree2 = model2.condensed_tree_._raw_tree
    req(tree_sha(tree2) == real_tree_sha, "real HDBSCAN hierarchy changed across exact refit")
    ordinary2 = compute_stability(tree2)
    sync2, _annual2, _reconstructed2 = density_synchronous_stability(tree2, years)
    labels2 = reom.eom_labels(tree2, sync2)
    nodes2 = reom.selected_eom_nodes(tree2, sync2)
    parent_candidates2 = sync_candidates_from_labels(labels2, nodes2, events, ordinary2, sync2, parent_runner)
    req(ordered_membership_sha(parent_candidates2) == parent_order_sha, "real #1263 parent order changed across exact refit")

    successor_candidates = calibrate_candidates(parent_candidates2, null_replicates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(successor_order_sha != parent_order_sha)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_SURVEY_NULL_CALIBRATED_PERSISTENCE_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "real_condensed_tree_sha256": real_tree_sha,
        "parent_candidate_count": len(parent_candidates2),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "membership_universe_identical": bool(
            {tuple(c["event_ids"]) for c in parent_candidates2} == {tuple(c["event_ids"]) for c in successor_candidates}
        ),
        "mechanism_active": mechanism_active,
        "null_replicates": NULL_REPLICATES,
        "null_candidate_counts": [len(x) for x in null_replicates],
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_AT100_GAIN,
        "parent_candidates": parent_candidates2,
        "successor_candidates": successor_candidates,
        "null_evidence": null_reports,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "truth_evaluated_when_written": False,
    }
    req(prelabel["membership_universe_identical"] is True, "null calibration changed real candidate memberships")
    prelabel_path = a.output / "NULL_CALIBRATED_PERSISTENCE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Hidden known-shower labels are first used here, after the complete null
    # ensemble and real successor order are persisted above.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled IDs")
    parent_metrics = {str(y): parent_runner.metrics(parent_candidates2, hidden, ids_by_year[y]) for y in YEARS}
    verify_parent_metrics(parent_metrics)
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {
        str(y): parent_runner.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS
    }
    parent_total = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total == 179, f"#1263 parent total changed: {parent_total}")
    total_gain = successor_total - parent_total
    strong_gain = bool(total_gain >= REQUIRED_TOTAL_AT100_GAIN)
    passed = bool(mechanism_active and strong_gain and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT"
        if passed else
        "FAIL_NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates2),
        "successor_candidate_count": len(successor_candidates),
        "membership_universe_identical": True,
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "null_replicates": NULL_REPLICATES,
        "null_candidate_counts": [len(x) for x in null_replicates],
        "parent_total_recovered_at_100": parent_total,
        "successor_total_recovered_at_100": successor_total,
        "total_recovered_at_100_gain": total_gain,
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_AT100_GAIN,
        "strong_gain_gate": strong_gain,
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
        "sole_successor_objective": "mean_empirical_pareto_tail_rate_under_16_within_year_solar_longitude_permutation_nulls",
        "post_result_parameter_search": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "gain": total_gain,
        "parent_total": parent_total,
        "successor_total": successor_total,
        "null_candidate_counts": result["null_candidate_counts"],
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
