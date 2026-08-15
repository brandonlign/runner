#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND
MIN_CLUSTER_SIZE = parent_runner.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent_runner.MIN_SAMPLES

EXPECTED_PARENT = {
    "2022": {
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7856486012780942,
        "mrr": 0.022498269587309373,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "recovered_at_50": 46,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7867680236864514,
        "mrr": 0.0220239288966045,
        "fragmentation_median_top500": 1.0,
    },
}
EXPECTED_PARENT_COUNT = 2097


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def sync_candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"synchronous selected cluster below frozen minimum: node={node}")
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


def verify_exact_parent_metrics(metrics: dict[str, dict[str, Any]]) -> None:
    for year, expected in EXPECTED_PARENT.items():
        got = metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"promoted parent {year} {key} changed: {got[key]} != {expected[key]}")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(
                bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)),
                f"promoted parent {year} {key} changed: {got[key]} != {expected[key]}",
            )


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

    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "dseom_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-density-synchronous-recurrent-eom-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent_runner.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    frozen_tree_sha = tree_sha(tree)
    ordinary = compute_stability(tree)

    # Reconstruct the promoted recurrent-EOM champion first on the unchanged hierarchy.
    parent_recurrent, parent_annual = parent_reom.recurrent_stability(tree, years)
    parent_labels = parent_reom.eom_labels(tree, parent_recurrent)
    parent_nodes = parent_reom.selected_eom_nodes(tree, parent_recurrent)
    req(len(parent_nodes) == len(set(int(x) for x in parent_labels if int(x) >= 0)), "parent selected-node/label count mismatch")
    parent_candidates = parent_runner.candidates_from_labels(
        parent_labels, parent_nodes, events, ordinary, parent_recurrent, True
    )
    req(len(parent_candidates) == EXPECTED_PARENT_COUNT, f"promoted recurrent parent candidate count changed: {len(parent_candidates)}")

    # Sole successor computation: pointwise annual alive-mass minimum integrated over density lambda.
    synchronous, synchronous_parent_annual, annual_reconstructed = density_synchronous_stability(tree, years)
    req(parent_annual == synchronous_parent_annual, "synchronous kernel returned a different promoted-parent annual EOM map")
    req(tree_sha(tree) == frozen_tree_sha, "synchronous kernel mutated the condensed tree")
    successor_labels = parent_reom.eom_labels(tree, synchronous)
    successor_nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    req(len(successor_nodes) == len(set(int(x) for x in successor_labels if int(x) >= 0)), "successor selected-node/label count mismatch")
    successor_candidates = sync_candidates_from_labels(successor_labels, successor_nodes, events, ordinary, synchronous)

    parent_order_sha = ordered_membership_sha(parent_candidates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(parent_nodes != successor_nodes or parent_order_sha != successor_order_sha)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "parent_annual_eom": {str(k): list(v) for k, v in sorted(parent_annual.items())},
        "reconstructed_annual_eom": {str(k): list(v) for k, v in sorted(annual_reconstructed.items())},
        "synchronous_stability": {str(int(k)): float(v) for k, v in sorted(synchronous.items())},
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
    prelabel_path = a.output / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # The complete hierarchy, objective maps, selected nodes, memberships and order are persisted above before truth use.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    parent_metrics = {str(y): parent_runner.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    verify_exact_parent_metrics(parent_metrics)
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {
        str(y): parent_runner.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS
    }
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(strict_100 and mechanism_active and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT"
        if passed else
        "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
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
        "sole_successor_objective": "integral_min_normalized_annual_alive_mass_over_lambda",
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
    result_path = a.output / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT.json"
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
