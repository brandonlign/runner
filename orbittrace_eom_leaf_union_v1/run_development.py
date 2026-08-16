#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_cluster_tree_leaves, get_clusters

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent
from recurrent_eom import eom_labels, selected_eom_nodes
from density_synchronous_eom import density_synchronous_stability

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
MIN_CLUSTER_SIZE = parent.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent.MIN_SAMPLES
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WINNER_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
BASELINE_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


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


def membership_key(row: dict[str, Any]) -> tuple[str, ...]:
    members = tuple(str(x) for x in row["event_ids"])
    req(members == tuple(sorted(members)), "candidate membership is not sorted")
    req(len(members) == int(row["member_count"]), "candidate member_count mismatch")
    req(len(set(members)) == len(members), "candidate contains duplicate event IDs")
    return members


def candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
    source: str,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), f"{source}: compact labels no longer map contiguously to sorted selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"{source}: selected cluster below frozen minimum: node={node} size={len(members)}")
        req(float(node) in synchronous, f"{source}: selected node missing synchronous stability: {node}")
        req(float(node) in ordinary, f"{source}: selected node missing ordinary stability: {node}")
        out.append({
            "family_id": parent.member_hash("EOMLEAF1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
            "sources": [source],
        })
    return out


def union_exact_memberships(
    eom: list[dict[str, Any]],
    leaves: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    by_members: dict[tuple[str, ...], dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    leaf_only = 0
    for row in eom:
        key = membership_key(row)
        req(key not in by_members, "same-run EOM source contains exact duplicate membership")
        by_members[key] = dict(row)

    for row in leaves:
        key = membership_key(row)
        if key not in by_members:
            by_members[key] = dict(row)
            leaf_only += 1
            continue
        existing = by_members[key]
        req("eom" in existing["sources"], "leaf exact duplicate unexpectedly collided with non-EOM source")
        req(int(existing["node_id"]) == int(row["node_id"]), "exact EOM/leaf membership duplicate maps to different hierarchy nodes")
        req(
            bool(np.isclose(float(existing["synchronous_stability"]), float(row["synchronous_stability"]), rtol=0.0, atol=1e-12)),
            "exact EOM/leaf duplicate has different synchronous stability",
        )
        req(
            bool(np.isclose(float(existing["ordinary_stability"]), float(row["ordinary_stability"]), rtol=0.0, atol=1e-12)),
            "exact EOM/leaf duplicate has different ordinary stability",
        )
        existing["sources"] = ["eom", "leaf"]
        duplicates.append({
            "family_id": existing["family_id"],
            "node_id": int(existing["node_id"]),
            "member_count": int(existing["member_count"]),
        })

    out = list(by_members.values())
    out.sort(key=lambda r: (
        -float(r["synchronous_stability"]),
        -float(r["ordinary_stability"]),
        -int(r["member_count"]),
        str(r["family_id"]),
    ))
    req(len({membership_key(r) for r in out}) == len(out), "exact membership duplicate survived union")
    return out, duplicates, leaf_only


def proper_subset_overlap_count(
    eom_labels_arr: np.ndarray,
    leaf_labels_arr: np.ndarray,
    eom_candidates: list[dict[str, Any]],
    leaf_candidates: list[dict[str, Any]],
) -> int:
    count = 0
    for leaf_lab, leaf_row in enumerate(leaf_candidates):
        idx = np.flatnonzero(leaf_labels_arr == leaf_lab)
        parent_labs = np.unique(eom_labels_arr[idx])
        positive = [int(x) for x in parent_labs if int(x) >= 0]
        if len(positive) != 1:
            continue
        eom_lab = positive[0]
        # Proper subset requires every leaf member map to the same EOM candidate and that parent be larger.
        if np.all(eom_labels_arr[idx] == eom_lab) and int(eom_candidates[eom_lab]["member_count"]) > int(leaf_row["member_count"]):
            count += 1
    return count


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

    req(sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "binding winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "binding winner result changed")
    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "binding winner membership hash changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "binding winner result membership hash changed")
    baseline = winner_result["successor_metrics"]
    req(int(baseline["2022"]["recovered_at_100"]) == 89, "binding 2022 @100 changed")
    req(int(baseline["2023"]["recovered_at_100"]) == 90, "binding 2023 @100 changed")
    req(sum(int(baseline[str(y)]["recovered_at_100"]) for y in YEARS) == BASELINE_TOTAL_AT100, "binding total changed")

    qmod = parent.load_module(a.quality_source, "eom_leaf_union_v1_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-eom-leaf-union-v1-development-2022-2023-target-excluded"
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
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == 738682, f"accessible pooled event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = np.asarray(parent.geo_matrix(events), dtype=np.float64)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    req(X.shape == (len(events), 6), f"GEO6 shape changed: {X.shape}")
    req(np.all(np.isfinite(X)), "non-finite inherited GEO6")
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
    synchronous, _parent_annual, annual_reconstructed = density_synchronous_stability(tree, years)
    req(tree_sha(tree) == frozen_tree_sha, "density-sync kernel mutated condensed tree")

    # Native/current EOM candidates from this exact tree.
    eom_labels_arr = np.asarray(eom_labels(tree, synchronous), dtype=np.int64)
    eom_nodes = tuple(int(x) for x in selected_eom_nodes(tree, synchronous))
    req(len(eom_nodes) == len(set(int(x) for x in eom_labels_arr if int(x) >= 0)), "EOM selected-node/label count mismatch")
    eom_candidates = candidates_from_labels(eom_labels_arr, eom_nodes, events, ordinary, synchronous, "eom")

    # Native finest leaf candidates from the same tree and stability map.
    cluster_tree = tree[tree["child_size"] > 1]
    leaf_nodes = tuple(sorted(int(x) for x in get_cluster_tree_leaves(cluster_tree)))
    leaf_native_labels, _leaf_prob, _leaf_stab = get_clusters(
        tree,
        dict(synchronous),
        cluster_selection_method="leaf",
        allow_single_cluster=False,
        match_reference_implementation=False,
        cluster_selection_epsilon=0.0,
        max_cluster_size=0,
    )
    leaf_labels_arr = np.asarray(leaf_native_labels, dtype=np.int64)
    leaf_positive = sorted(int(x) for x in np.unique(leaf_labels_arr) if int(x) >= 0)
    req(leaf_positive == list(range(len(leaf_nodes))), "native leaf labels do not map contiguously to sorted native leaf nodes")
    leaf_candidates = candidates_from_labels(leaf_labels_arr, leaf_nodes, events, ordinary, synchronous, "leaf")

    union, exact_duplicates, leaf_only_count = union_exact_memberships(eom_candidates, leaf_candidates)
    proper_subset_count = proper_subset_overlap_count(eom_labels_arr, leaf_labels_arr, eom_candidates, leaf_candidates)
    union_order_sha = ordered_membership_sha(union)
    sizes = [int(r["member_count"]) for r in union]
    source_counts = {
        "eom_only": sum(r["sources"] == ["eom"] for r in union),
        "leaf_only": sum(r["sources"] == ["leaf"] for r in union),
        "eom_and_leaf_exact_duplicate": sum(r["sources"] == ["eom", "leaf"] for r in union),
    }

    structural = {
        "at_least_100_same_run_eom_candidates": len(eom_candidates) >= 100,
        "has_native_leaf_candidates": len(leaf_candidates) >= 1,
        "adds_nonduplicate_leaf_candidate": leaf_only_count >= 1,
        "native_leaf_label_node_count_identity": len(leaf_positive) == len(leaf_nodes) == len(leaf_candidates),
        "no_exact_membership_duplicates_after_union": len({membership_key(r) for r in union}) == len(union),
        "proper_parent_leaf_overlap_active": proper_subset_count >= 1,
        "all_candidates_at_least_10_members": bool(union) and min(sizes) >= MIN_CLUSTER_SIZE,
        "union_differs_from_binding_winner": union_order_sha != WINNER_MEMBERSHIP_SHA,
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_EOM_LEAF_UNION_V1",
        "architecture": "same_tree_density_sync_eom_plus_native_leaf_exact_membership_union",
        "sole_change": "expose_both_eom_and_leaf_resolutions_from_same_hierarchy",
        "representation": "INHERITED_GEO6_UNCHANGED",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "eom_selected_nodes": list(eom_nodes),
        "leaf_selected_nodes": list(leaf_nodes),
        "eom_candidate_count": len(eom_candidates),
        "leaf_candidate_count": len(leaf_candidates),
        "leaf_only_added_count": leaf_only_count,
        "exact_eom_leaf_duplicate_count": len(exact_duplicates),
        "proper_eom_leaf_subset_overlap_count": proper_subset_count,
        "source_counts_after_union": source_counts,
        "union_candidate_count": len(union),
        "smallest_family_members": min(sizes),
        "largest_family_members": max(sizes),
        "union_ordered_membership_sha256": union_order_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "exact_duplicate_audit": exact_duplicates,
        "structural_gates": structural,
        "candidates": union,
        "annual_reconstructed_eom": {str(k): list(v) for k, v in sorted(annual_reconstructed.items())},
        "known_shower_labels_indexed": False,
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
    prelabel_path = a.output / "EOM_LEAF_UNION_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth remains sealed until the complete multi-resolution candidate universe and order are durable.
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    same_run_eom_metrics = {str(y): parent.metrics(eom_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(union, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor_metrics[str(y)]) for y in YEARS}
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    passed = bool(
        all(structural.values())
        and successor_total >= REQUIRED_TOTAL_AT100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_EOM_LEAF_UNION_V1_GMN_DEVELOPMENT" if passed else "FAIL_EOM_LEAF_UNION_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "architecture": prelabel["architecture"],
        "sole_change": prelabel["sole_change"],
        "same_run_eom_candidate_count": len(eom_candidates),
        "leaf_candidate_count": len(leaf_candidates),
        "leaf_only_added_count": leaf_only_count,
        "union_candidate_count": len(union),
        "proper_eom_leaf_subset_overlap_count": proper_subset_count,
        "union_ordered_membership_sha256": union_order_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "structural_gates": structural,
        "baseline_metrics": baseline,
        "same_run_eom_metrics_diagnostic_only": same_run_eom_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "baseline_total_recovered_at_100": BASELINE_TOTAL_AT100,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": REQUIRED_TOTAL_AT100,
        "required_gain": REQUIRED_TOTAL_AT100 - BASELINE_TOTAL_AT100,
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
    (a.output / "EOM_LEAF_UNION_V1_GMN_DEVELOPMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "same_run_eom_candidate_count": len(eom_candidates),
        "leaf_candidate_count": len(leaf_candidates),
        "leaf_only_added_count": leaf_only_count,
        "union_candidate_count": len(union),
        "proper_eom_leaf_subset_overlap_count": proper_subset_count,
        "baseline_total_at100": BASELINE_TOTAL_AT100,
        "same_run_eom_total_at100": sum(int(same_run_eom_metrics[str(y)]["recovered_at_100"]) for y in YEARS),
        "successor_total_at100": successor_total,
        "gain": gain,
        "2022": {k: successor_metrics["2022"][k] for k in ("recovered_at_50", "recovered_at_100", "top100_dominant_precision", "mrr", "fragmentation_median_top500")},
        "2023": {k: successor_metrics["2023"][k] for k in ("recovered_at_50", "recovered_at_100", "top100_dominant_precision", "mrr", "fragmentation_median_top500")},
        "structural_gates": structural,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
