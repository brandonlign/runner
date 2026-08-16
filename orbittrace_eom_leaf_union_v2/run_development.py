#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_clusters

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND
MIN_CLUSTER_SIZE = parent_runner.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent_runner.MIN_SAMPLES
EXPECTED_BASELINE_COUNT = 2094
EXPECTED_BASELINE_ORDER_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_BASELINE = {
    "2022": {
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7873334043,
        "mrr": 0.02250537317,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "recovered_at_50": 46,
        "recovered_at_100": 90,
        "top100_dominant_precision": 0.7898245986,
        "mrr": 0.02203028491,
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


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def unordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    rows = sorted("|".join(sorted(str(x) for x in row["event_ids"])) for row in candidates)
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def selected_leaf_nodes(tree: np.ndarray) -> tuple[int, ...]:
    root = int(tree["parent"].min())
    cluster_tree = tree[tree["child_size"] > 1]
    parents = {int(x) for x in cluster_tree["parent"]}
    children = {int(x) for x in cluster_tree["child"]}
    leaves = sorted(c for c in children if c not in parents)
    if not leaves:
        leaves = [root]
    if root in leaves:
        leaves.remove(root)
    return tuple(leaves)


def sync_candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
    prefix: str,
    source: str,
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), f"{source} compact labels do not map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"{source} selected cluster below frozen minimum: node={node}")
        req(float(node) in synchronous, f"{source} node missing synchronous stability: {node}")
        req(float(node) in ordinary, f"{source} node missing ordinary stability: {node}")
        out.append({
            "family_id": parent_runner.member_hash(prefix, members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
            "source": source,
        })
    out.sort(key=lambda f: (
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def verify_baseline_artifact(winner_prelabel: dict[str, Any], winner_result: dict[str, Any]) -> list[dict[str, Any]]:
    req(int(winner_prelabel["successor_candidate_count"]) == EXPECTED_BASELINE_COUNT, "frozen winner candidate count changed")
    req(winner_prelabel["successor_ordered_membership_sha256"] == EXPECTED_BASELINE_ORDER_SHA, "frozen winner order hash changed")
    req(int(winner_result["successor_candidate_count"]) == EXPECTED_BASELINE_COUNT, "frozen winner result count changed")
    req(winner_result["successor_ordered_membership_sha256"] == EXPECTED_BASELINE_ORDER_SHA, "frozen winner result order hash changed")
    req(winner_result["verdict"] == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "frozen winner verdict changed")
    candidates = list(winner_prelabel["successor_candidates"])
    req(len(candidates) == EXPECTED_BASELINE_COUNT, "frozen winner candidate payload length changed")
    req(ordered_membership_sha(candidates) == EXPECTED_BASELINE_ORDER_SHA, "frozen winner candidate payload order changed")
    for year, expected in EXPECTED_BASELINE.items():
        got = winner_result["successor_metrics"][year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"frozen winner {year} {key} changed")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=5e-10), f"frozen winner {year} {key} changed")
    return candidates


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    winner_prelabel = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    frozen_winner_candidates = verify_baseline_artifact(winner_prelabel, winner_result)

    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "eom_leaf_union_v2_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-eom-leaf-union-v2-development-2022-2023-target-excluded"
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
    req(len(events) == 738682, f"accessible event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")
    X = parent_runner.geo_matrix(events)

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
    synchronous, _parent_annual, _annual_reconstructed = density_synchronous_stability(tree, years)
    req(tree_sha(tree) == frozen_tree_sha, "density-synchronous kernel mutated hierarchy")

    # Reproduce the exact frozen 179 winner before introducing leaf availability.
    eom_labels = parent_reom.eom_labels(tree, synchronous)
    eom_nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    eom_candidates = sync_candidates_from_labels(eom_labels, eom_nodes, events, ordinary, synchronous, "DSEOM1", "eom")
    req(len(eom_candidates) == EXPECTED_BASELINE_COUNT, f"reconstructed EOM count {len(eom_candidates)} != frozen {EXPECTED_BASELINE_COUNT}")
    req(ordered_membership_sha(eom_candidates) == EXPECTED_BASELINE_ORDER_SHA, "reconstructed EOM order does not equal frozen 179 winner")
    req(unordered_membership_sha(eom_candidates) == unordered_membership_sha(frozen_winner_candidates), "reconstructed EOM candidate multiset differs from frozen winner")

    # Sole change: expose the finest HDBSCAN leaf clusters on the same tree under the same synchronous objective.
    leaf_nodes = selected_leaf_nodes(tree)
    leaf_labels, _leaf_probabilities, _leaf_stabilities = get_clusters(
        tree,
        dict(synchronous),
        cluster_selection_method="leaf",
        allow_single_cluster=False,
        match_reference_implementation=False,
        cluster_selection_epsilon=0.0,
        max_cluster_size=0,
    )
    leaf_labels = np.asarray(leaf_labels, dtype=np.int64)
    req(len(set(int(x) for x in leaf_labels if int(x) >= 0)) == len(leaf_nodes), "native leaf labels/node count mismatch")
    leaf_candidates = sync_candidates_from_labels(leaf_labels, leaf_nodes, events, ordinary, synchronous, "DSLEAF2", "leaf")

    eom_memberships = {tuple(row["event_ids"]) for row in eom_candidates}
    duplicate_leaf = [row for row in leaf_candidates if tuple(row["event_ids"]) in eom_memberships]
    novel_leaf = [row for row in leaf_candidates if tuple(row["event_ids"]) not in eom_memberships]
    req(len(leaf_candidates) == len(duplicate_leaf) + len(novel_leaf), "leaf duplicate partition mismatch")

    union_candidates = [dict(row) for row in eom_candidates] + [dict(row) for row in novel_leaf]
    union_candidates.sort(key=lambda f: (
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    req(len({tuple(row["event_ids"]) for row in union_candidates}) == len(union_candidates), "exact duplicate membership survived union")
    union_order_sha = ordered_membership_sha(union_candidates)
    mechanism_active = bool(novel_leaf and (len(union_candidates) != len(eom_candidates) or union_order_sha != EXPECTED_BASELINE_ORDER_SHA))

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_EOM_LEAF_UNION_V2",
        "sole_change": "add_native_leaf_candidates_to_exact_density_sync_eom_winner",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "baseline_candidate_count": len(eom_candidates),
        "baseline_ordered_membership_sha256": ordered_membership_sha(eom_candidates),
        "baseline_unordered_membership_sha256": unordered_membership_sha(eom_candidates),
        "leaf_node_count": len(leaf_nodes),
        "leaf_nodes": list(leaf_nodes),
        "leaf_candidate_count": len(leaf_candidates),
        "duplicate_leaf_membership_count": len(duplicate_leaf),
        "novel_leaf_candidate_count": len(novel_leaf),
        "union_candidate_count": len(union_candidates),
        "union_ordered_membership_sha256": union_order_sha,
        "mechanism_active": mechanism_active,
        "eom_candidates": eom_candidates,
        "leaf_candidates": leaf_candidates,
        "union_candidates": union_candidates,
        "known_shower_labels_indexed": False,
        "catalogue_loaded_before_order_freeze": True,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "EOM_LEAF_UNION_V2_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth use begins only after the complete successor pool/order has been frozen above.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    baseline_metrics = winner_result["successor_metrics"]
    successor_metrics = {str(y): parent_runner.metrics(union_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {
        str(y): parent_runner.annual_gate(baseline_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS
    }
    baseline_total = sum(int(baseline_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(baseline_total == 179, f"baseline total changed: {baseline_total}")
    gain = successor_total - baseline_total
    structural_gates = {
        "exact_baseline_reproduced": ordered_membership_sha(eom_candidates) == EXPECTED_BASELINE_ORDER_SHA,
        "leaf_candidates_exist": len(leaf_candidates) > 0,
        "novel_leaf_candidates_exist": len(novel_leaf) > 0,
        "exact_duplicates_removed_only": len(union_candidates) == len(eom_candidates) + len(novel_leaf),
        "mechanism_active": mechanism_active,
        "prelabel_written_before_truth_use": True,
    }
    passed = bool(
        successor_total >= 184
        and all(structural_gates.values())
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_EOM_LEAF_UNION_V2_GMN_DEVELOPMENT" if passed else "FAIL_EOM_LEAF_UNION_V2_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "sole_change": "add_native_leaf_candidates_to_exact_density_sync_eom_winner",
        "prelabel_sha256": prelabel_sha,
        "baseline_candidate_count": len(eom_candidates),
        "leaf_candidate_count": len(leaf_candidates),
        "duplicate_leaf_membership_count": len(duplicate_leaf),
        "novel_leaf_candidate_count": len(novel_leaf),
        "successor_candidate_count": len(union_candidates),
        "baseline_total_recovered_at_100": baseline_total,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": 184,
        "required_gain": 5,
        "baseline_metrics": baseline_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "structural_gates": structural_gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "EOM_LEAF_UNION_V2_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "baseline_total_at100": baseline_total,
        "successor_total_at100": successor_total,
        "gain": gain,
        "baseline_candidate_count": len(eom_candidates),
        "leaf_candidate_count": len(leaf_candidates),
        "novel_leaf_candidate_count": len(novel_leaf),
        "union_candidate_count": len(union_candidates),
        "2022": {k: v for k, v in successor_metrics["2022"].items() if k != "first_rank_by_label"},
        "2023": {k: v for k, v in successor_metrics["2023"].items() if k != "first_rank_by_label"},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
