#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import recurrent_eom
from fosc_margin import fosc_optimal_values_and_selected_margins, rank_candidates_by_margin

DTYPE = np.dtype([
    ("parent", np.intp),
    ("child", np.intp),
    ("lambda_val", float),
    ("child_size", np.intp),
])


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def synthetic_tree() -> np.ndarray:
    # n_points == root == 10.  Cluster IDs increase down the hierarchy exactly
    # as HDBSCAN condensed trees do.
    rows = [
        (10, 11, 1.0, 4),
        (10, 12, 1.0, 4),
        (10, 8, 0.5, 1),
        (10, 9, 0.5, 1),
        (11, 13, 2.0, 2),
        (11, 14, 2.0, 2),
        (12, 15, 2.0, 2),
        (12, 16, 2.0, 2),
        (13, 0, 3.0, 1),
        (13, 1, 3.0, 1),
        (14, 2, 3.0, 1),
        (14, 3, 3.0, 1),
        (15, 4, 3.0, 1),
        (15, 5, 3.0, 1),
        (16, 6, 3.0, 1),
        (16, 7, 3.0, 1),
    ]
    return np.asarray(rows, dtype=DTYPE)


def cluster_children(tree: np.ndarray) -> dict[int, list[int]]:
    out: dict[int, list[int]] = defaultdict(list)
    for p, c, size in zip(tree["parent"], tree["child"], tree["child_size"]):
        if int(size) > 1:
            out[int(p)].append(int(c))
    return out


def brute_best(
    node: int,
    stability: dict[float, float],
    children: dict[int, list[int]],
    forbidden: int | None = None,
) -> float:
    child_total = sum(brute_best(ch, stability, children, forbidden) for ch in children.get(node, []))
    own_allowed = node != forbidden
    own = float(stability[float(node)]) if own_allowed else float("-inf")
    return max(own, child_total)


def main() -> int:
    tree = synthetic_tree()
    stability = {
        10.0: 0.0,
        11.0: 10.0,
        12.0: 10.0,
        13.0: 4.0,
        14.0: 5.0,
        15.0: 6.0,
        16.0: 5.0,
    }
    selected = recurrent_eom.selected_eom_nodes(tree, stability)
    req(selected == (11, 15, 16), f"unexpected exact FOSC selection: {selected}")

    optimal, alternatives, margins = fosc_optimal_values_and_selected_margins(tree, stability, selected)
    req(optimal[11] == 10.0 and alternatives[11] == 9.0 and margins[11] == 1.0, "node 11 margin wrong")
    req(optimal[12] == 11.0, "node 12 descendant optimum wrong")
    req(margins == {11: 1.0, 15: 6.0, 16: 5.0}, f"unexpected margins: {margins}")

    children = cluster_children(tree)
    # allow_single_cluster=False means the root itself is excluded; the global
    # optimum is the sum of optimal solutions in its immediate cluster subtrees.
    root_children = children[10]
    global_best = sum(brute_best(ch, stability, children) for ch in root_children)
    req(global_best == 21.0, f"unexpected synthetic global optimum: {global_best}")
    brute_losses: dict[int, float] = {}
    for node in selected:
        forced = sum(brute_best(ch, stability, children, node) for ch in root_children)
        loss = global_best - forced
        brute_losses[node] = loss
        req(abs(loss - margins[node]) <= 1e-12, f"global-loss theorem failed for node {node}: {loss} != {margins[node]}")

    # Exact tie semantics: parent wins when own == optimal descendant sum, and
    # its decision margin is exactly zero.
    tie = dict(stability)
    tie[11.0] = 9.0
    tie_selected = recurrent_eom.selected_eom_nodes(tree, tie)
    req(tie_selected == (11, 15, 16), f"FOSC tie did not go to parent: {tie_selected}")
    _o2, alt2, margin2 = fosc_optimal_values_and_selected_margins(tree, tie, tie_selected)
    req(alt2[11] == 9.0 and margin2[11] == 0.0, "zero-margin tie semantics failed")

    # Positive scaling of the complete objective scales every margin and leaves
    # the selected node set and margin order unchanged.
    scaled = {k: 7.0 * v for k, v in stability.items()}
    scaled_selected = recurrent_eom.selected_eom_nodes(tree, scaled)
    req(scaled_selected == selected, "positive objective scaling changed FOSC selection")
    _o3, _a3, margin3 = fosc_optimal_values_and_selected_margins(tree, scaled, scaled_selected)
    for node in selected:
        req(abs(margin3[node] - 7.0 * margins[node]) <= 1e-12, f"margin scaling failed at {node}")

    # Ranking changes only order, not candidate identity/membership fields.
    candidates = [
        {"family_id": "A", "node_id": 11, "event_ids": ["a", "b"], "member_count": 2, "synchronous_stability": 10.0, "ordinary_stability": 12.0},
        {"family_id": "B", "node_id": 15, "event_ids": ["c", "d"], "member_count": 2, "synchronous_stability": 6.0, "ordinary_stability": 7.0},
        {"family_id": "C", "node_id": 16, "event_ids": ["e", "f"], "member_count": 2, "synchronous_stability": 5.0, "ordinary_stability": 6.0},
    ]
    ranked = rank_candidates_by_margin(candidates, margins)
    req([r["node_id"] for r in ranked] == [15, 16, 11], "margin order fixture failed")
    req({r["family_id"] for r in ranked} == {r["family_id"] for r in candidates}, "candidate identities changed")
    original_members = {r["family_id"]: tuple(r["event_ids"]) for r in candidates}
    ranked_members = {r["family_id"]: tuple(r["event_ids"]) for r in ranked}
    req(original_members == ranked_members, "candidate memberships changed")

    # A selected-node descendant is invalid and must fail closed.
    antichain_rejected = False
    try:
        fosc_optimal_values_and_selected_margins(tree, stability, (11, 13, 15, 16))
    except RuntimeError:
        antichain_rejected = True
    req(antichain_rejected, "non-antichain selected-node set did not fail closed")

    result = {
        "schema": "DENSITY_SYNC_FOSC_MARGIN_V1_SYNTHETIC_AUDIT",
        "verdict": "PASS_DENSITY_SYNC_FOSC_MARGIN_V1_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "tests": {
            "exact_fosc_selection_fixture": True,
            "recursive_optimum_fixture": True,
            "selected_margin_fixture": True,
            "bruteforce_global_objective_loss_identity": True,
            "tie_goes_to_parent_zero_margin": True,
            "positive_scaling_invariance": True,
            "ranking_only_preserves_candidate_memberships": True,
            "selected_antichain_fail_closed": True,
        },
        "selected_nodes": list(selected),
        "margins": {str(k): v for k, v in margins.items()},
        "bruteforce_global_losses": {str(k): v for k, v in brute_losses.items()},
        "target_information_access": False,
        "target_region_events_accessed": False,
        "gmn_catalogue_accessed": False,
        "scientific_labels_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DENSITY_SYNC_FOSC_MARGIN_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
