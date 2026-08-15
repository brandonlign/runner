#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import recurrent_eom
from fosc_margin import global_fosc_exclusion_margins, rank_candidates_by_margin

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
    # n_points == root == 10. Cluster IDs increase down the hierarchy exactly
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


def cluster_children(tree: np.ndarray) -> tuple[int, dict[int, list[int]]]:
    root = int(tree["parent"].min())
    out: dict[int, list[int]] = defaultdict(list)
    for p, c, size in zip(tree["parent"], tree["child"], tree["child_size"]):
        if int(size) > 1:
            out[int(p)].append(int(c))
    return root, out


def enumerate_subtree_cuts(
    node: int,
    stability: dict[float, float],
    children: dict[int, list[int]],
    forbidden: int | None = None,
) -> list[tuple[float, tuple[int, ...]]]:
    """Exhaustively enumerate every legal antichain cut of a tiny subtree."""
    options: list[tuple[float, tuple[int, ...]]] = []
    if node != forbidden:
        options.append((float(stability[float(node)]), (node,)))

    kids = children.get(node, [])
    if not kids:
        # Selecting nothing is the only descendant solution for a cluster leaf.
        options.append((0.0, ()))
        return options

    child_options = [enumerate_subtree_cuts(ch, stability, children, forbidden) for ch in kids]
    for combo in itertools.product(*child_options):
        value = float(sum(x[0] for x in combo))
        cut = tuple(sorted(n for x in combo for n in x[1]))
        options.append((value, cut))
    return options


def enumerate_root_excluded_cuts(
    tree: np.ndarray,
    stability: dict[float, float],
    forbidden: int | None = None,
) -> list[tuple[float, tuple[int, ...]]]:
    root, children = cluster_children(tree)
    root_kids = children.get(root, [])
    if not root_kids:
        return [(0.0, ())]
    child_options = [enumerate_subtree_cuts(ch, stability, children, forbidden) for ch in root_kids]
    out: list[tuple[float, tuple[int, ...]]] = []
    for combo in itertools.product(*child_options):
        out.append((float(sum(x[0] for x in combo)), tuple(sorted(n for x in combo for n in x[1]))))
    return out


def exact_bruteforce_optimum(
    tree: np.ndarray,
    stability: dict[float, float],
    forbidden: int | None = None,
) -> tuple[float, tuple[int, ...]]:
    cuts = enumerate_root_excluded_cuts(tree, stability, forbidden)
    # Tie convention is irrelevant to the objective value; deterministic cut
    # tie-break is only for audit reporting.
    return max(cuts, key=lambda x: (x[0], tuple(-n for n in x[1])))


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

    optimal, global_best, forced, margins = global_fosc_exclusion_margins(tree, stability, selected)
    req(global_best == 21.0, f"unexpected global optimum: {global_best}")
    req(optimal[11] == 10.0, "node 11 unrestricted optimum wrong")
    req(optimal[12] == 11.0, "node 12 descendant optimum wrong")

    brute_best, brute_cut = exact_bruteforce_optimum(tree, stability)
    req(brute_best == global_best, f"DP global optimum != exhaustive optimum: {global_best} != {brute_best}")
    req(brute_cut == selected, f"exhaustive best cut differs from exact FOSC selected nodes: {brute_cut} != {selected}")

    # This is the exact ancestor-switch counterexample that broke the original
    # local-margin interpretation. Every selected node costs exactly 1 globally.
    expected = {11: 1.0, 15: 1.0, 16: 1.0}
    req(margins == expected, f"repaired global margins wrong: {margins} != {expected}")
    req(forced == {11: 20.0, 15: 20.0, 16: 20.0}, f"forced optima wrong: {forced}")

    brute_losses: dict[int, float] = {}
    brute_forced_cuts: dict[int, tuple[int, ...]] = {}
    for node in selected:
        forced_value, forced_cut = exact_bruteforce_optimum(tree, stability, forbidden=node)
        loss = brute_best - forced_value
        brute_losses[node] = loss
        brute_forced_cuts[node] = forced_cut
        req(abs(forced_value - forced[node]) <= 1e-12, f"forced DP != exhaustive forced optimum for {node}")
        req(abs(loss - margins[node]) <= 1e-12, f"global exclusion loss failed for node {node}: {loss} != {margins[node]}")

    # Critical repaired case: forbidding 15 switches previously rejected ancestor
    # 12 on, so global loss is 1 rather than local leaf gap 6.
    req(brute_forced_cuts[15] == (11, 12), f"ancestor-switch cut wrong for forbidden 15: {brute_forced_cuts[15]}")
    req(margins[15] == 1.0, "ancestor-switch global margin is not 1")

    # Exact tie semantics: parent wins when own == optimal descendant sum. Node 11
    # remains selected with a zero global exclusion margin because its descendants
    # give an equal objective when it is forbidden.
    tie = dict(stability)
    tie[11.0] = 9.0
    tie_selected = recurrent_eom.selected_eom_nodes(tree, tie)
    req(tie_selected == (11, 15, 16), f"FOSC tie did not go to parent: {tie_selected}")
    _ot, tie_best, _ft, tie_margin = global_fosc_exclusion_margins(tree, tie, tie_selected)
    tie_brute, _tie_cut = exact_bruteforce_optimum(tree, tie)
    req(tie_best == tie_brute == 20.0, "tie global optimum wrong")
    req(tie_margin[11] == 0.0, f"tie exclusion margin should be zero: {tie_margin[11]}")

    # Positive scaling must scale exact global losses and preserve selected nodes.
    scaled = {k: 7.0 * v for k, v in stability.items()}
    scaled_selected = recurrent_eom.selected_eom_nodes(tree, scaled)
    req(scaled_selected == selected, "positive objective scaling changed FOSC selection")
    _os, scaled_best, _fs, scaled_margin = global_fosc_exclusion_margins(tree, scaled, scaled_selected)
    req(scaled_best == 7.0 * global_best, "global optimum did not scale")
    for node in selected:
        req(abs(scaled_margin[node] - 7.0 * margins[node]) <= 1e-12, f"global margin scaling failed at {node}")

    # Ranking helper changes only order, not identity/membership. Use a separate
    # deterministic fixture with unequal global margins to prove ordering logic.
    candidates = [
        {"family_id": "A", "node_id": 11, "event_ids": ["a", "b"], "member_count": 2, "synchronous_stability": 10.0, "ordinary_stability": 12.0},
        {"family_id": "B", "node_id": 15, "event_ids": ["c", "d"], "member_count": 2, "synchronous_stability": 6.0, "ordinary_stability": 7.0},
        {"family_id": "C", "node_id": 16, "event_ids": ["e", "f"], "member_count": 2, "synchronous_stability": 5.0, "ordinary_stability": 6.0},
    ]
    rank_fixture = {11: 1.0, 15: 3.0, 16: 2.0}
    ranked = rank_candidates_by_margin(candidates, rank_fixture)
    req([r["node_id"] for r in ranked] == [15, 16, 11], "global-margin order fixture failed")
    req({r["family_id"] for r in ranked} == {r["family_id"] for r in candidates}, "candidate identities changed")
    original_members = {r["family_id"]: tuple(r["event_ids"]) for r in candidates}
    ranked_members = {r["family_id"]: tuple(r["event_ids"]) for r in ranked}
    req(original_members == ranked_members, "candidate memberships changed")

    # A supplied selected-node descendant violates the exact final FOSC cut and
    # must fail closed before any margin is accepted.
    antichain_rejected = False
    try:
        global_fosc_exclusion_margins(tree, stability, (11, 13, 15, 16))
    except RuntimeError:
        antichain_rejected = True
    req(antichain_rejected, "non-antichain selected-node set did not fail closed")

    result = {
        "schema": "DENSITY_SYNC_GLOBAL_FOSC_EXCLUSION_MARGIN_V1_SYNTHETIC_AUDIT",
        "verdict": "PASS_DENSITY_SYNC_FOSC_MARGIN_V1_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "repair_of_run": 31862832013,
        "tests": {
            "exact_fosc_selection_fixture": True,
            "unrestricted_dp_equals_exhaustive_flat_cut_enumeration": True,
            "forced_exclusion_dp_equals_exhaustive_for_every_selected_node": True,
            "ancestor_switch_counterexample_repaired": True,
            "root_exclusion_matches_allow_single_cluster_false": True,
            "tie_goes_to_parent_and_yields_zero_exclusion_margin": True,
            "positive_scaling_invariance": True,
            "ranking_only_preserves_candidate_memberships": True,
            "selected_antichain_fail_closed": True,
        },
        "selected_nodes": list(selected),
        "global_optimum": global_best,
        "global_exclusion_margins": {str(k): v for k, v in margins.items()},
        "bruteforce_global_losses": {str(k): v for k, v in brute_losses.items()},
        "bruteforce_forced_cuts": {str(k): list(v) for k, v in brute_forced_cuts.items()},
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
