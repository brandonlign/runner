from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np

TOL = 1e-12


def _hierarchy(
    tree: np.ndarray,
    stability: Mapping[float, float],
) -> tuple[int, dict[int, float], dict[int, list[int]], dict[int, int]]:
    raw = {int(k): float(v) for k, v in stability.items()}
    if not raw:
        raise ValueError("stability map is empty")
    if any(not np.isfinite(v) for v in raw.values()):
        raise ValueError("stability map contains non-finite values")

    root = int(tree["parent"].min())
    if root not in raw:
        raise RuntimeError(f"root {root} missing from stability map")

    children: dict[int, list[int]] = defaultdict(list)
    parent_of: dict[int, int] = {}
    cluster_tree = tree[tree["child_size"] > 1]
    for p_raw, c_raw in zip(cluster_tree["parent"], cluster_tree["child"]):
        p = int(p_raw)
        c = int(c_raw)
        if p not in raw:
            raise RuntimeError(f"cluster parent {p} missing from stability map")
        if c not in raw:
            raise RuntimeError(f"cluster child {c} missing from stability map")
        if c <= p:
            raise RuntimeError(f"condensed-tree cluster order changed: parent={p}, child={c}")
        if c in parent_of:
            raise RuntimeError(f"cluster node {c} has multiple cluster parents")
        children[p].append(c)
        parent_of[c] = p

    # Every non-root objective node must have one unique cluster parent.
    orphan = sorted(node for node in raw if node != root and node not in parent_of)
    if orphan:
        raise RuntimeError(f"objective nodes disconnected from condensed-tree root: {orphan[:5]}")

    return root, raw, children, parent_of


def global_fosc_exclusion_margins(
    tree: np.ndarray,
    stability: Mapping[float, float],
    selected_nodes: Sequence[int],
) -> tuple[dict[int, float], float, dict[int, float], dict[int, float]]:
    """Exact global FOSC objective loss when each selected node is forbidden.

    The HDBSCAN root is excluded exactly as ``allow_single_cluster=False``.
    For each already-selected node C, this function re-optimizes the entire
    hierarchy under the sole additional constraint that C itself cannot be
    selected.  Descendants and previously rejected ancestors remain eligible.

    Returns
    -------
    optimal_subtree:
        Unrestricted O(C)=max(S(C), sum_D O(D)) for every cluster node.
    global_optimum:
        Root-excluded unrestricted FOSC objective.
    forced_global_optimum:
        Mapping selected C -> exact root-excluded optimum when C is forbidden.
    exclusion_margin:
        Mapping selected C -> global_optimum - forced_global_optimum[C].
    """
    root, raw, children, parent_of = _hierarchy(tree, stability)

    optimal: dict[int, float] = {}
    for node in sorted(raw, reverse=True):
        child_sum = float(sum(optimal[ch] for ch in children.get(node, [])))
        own = raw[node]
        # Exact HDBSCAN/FOSC EOM objective semantics: ties favor the parent.
        optimal[node] = own if not (child_sum > own) else child_sum

    root_children = tuple(children.get(root, []))
    global_optimum = float(sum(optimal[ch] for ch in root_children))

    selected = tuple(sorted(int(x) for x in selected_nodes))
    if len(selected) != len(set(selected)):
        raise ValueError("selected_nodes contains duplicates")
    if root in selected:
        raise RuntimeError("root may not be selected when allow_single_cluster=False")
    for node in selected:
        if node not in raw:
            raise RuntimeError(f"selected node {node} missing from stability map")

    # Verify the supplied final selected cut is an antichain and realizes the
    # same root-excluded optimum.  This binds the counterfactual to the exact
    # selected solution, rather than merely to an arbitrary node subset.
    selected_set = set(selected)
    for ancestor in selected:
        stack = list(children.get(ancestor, []))
        while stack:
            cur = stack.pop()
            if cur in selected_set:
                raise RuntimeError(
                    f"selected FOSC nodes are not an antichain: {ancestor} contains selected descendant {cur}"
                )
            stack.extend(children.get(cur, []))

    selected_objective = float(sum(raw[node] for node in selected))
    scale = max(1.0, abs(global_optimum), abs(selected_objective))
    if abs(selected_objective - global_optimum) > TOL * scale:
        raise RuntimeError(
            "selected-node objective does not equal root-excluded FOSC optimum: "
            f"selected={selected_objective} global={global_optimum}"
        )

    forced_global: dict[int, float] = {}
    margins: dict[int, float] = {}

    for forbidden in selected:
        # At the forbidden node itself, its own objective is unavailable; the
        # best permitted solution is therefore its unrestricted descendant cut.
        forced_value = float(sum(optimal[ch] for ch in children.get(forbidden, [])))
        current = forbidden

        while True:
            if current not in parent_of:
                raise RuntimeError(f"selected node {forbidden} has no path to excluded root")
            parent = parent_of[current]
            siblings = children.get(parent, [])
            other_sum = float(sum(optimal[ch] for ch in siblings if ch != current))
            affected_child_sum = forced_value + other_sum

            if parent == root:
                # Root itself is ineligible.  The global forced optimum is the
                # sum of its independently optimized cluster-child branches.
                forced_value = affected_child_sum
                break

            own = raw[parent]
            forced_value = own if not (affected_child_sum > own) else affected_child_sum
            current = parent

        fg = float(forced_value)
        loss = global_optimum - fg
        loss_scale = max(1.0, abs(global_optimum), abs(fg))
        if loss < -TOL * loss_scale:
            raise RuntimeError(
                f"forbidding selected node {forbidden} improved global FOSC objective: "
                f"unrestricted={global_optimum} forced={fg}"
            )
        if loss < 0.0:
            loss = 0.0
        forced_global[forbidden] = fg
        margins[forbidden] = float(loss)

    return optimal, global_optimum, forced_global, margins


def rank_candidates_by_margin(
    candidates: Sequence[dict],
    margins: Mapping[int, float],
) -> list[dict]:
    """Reorder exact #1263 candidates by global FOSC exclusion margin."""
    out: list[dict] = []
    seen_nodes: set[int] = set()
    for row in candidates:
        node = int(row["node_id"])
        if node in seen_nodes:
            raise RuntimeError(f"duplicate candidate node {node}")
        seen_nodes.add(node)
        if node not in margins:
            raise RuntimeError(f"missing global FOSC exclusion margin for candidate node {node}")
        r = dict(row)
        r["global_fosc_exclusion_margin"] = float(margins[node])
        out.append(r)
    margin_nodes = set(int(k) for k in margins)
    if seen_nodes != margin_nodes:
        missing = sorted(margin_nodes - seen_nodes)
        extra = sorted(seen_nodes - margin_nodes)
        raise RuntimeError(
            f"candidate/margin node universe differs: missing_candidates={missing[:5]} missing_margins={extra[:5]}"
        )

    out.sort(
        key=lambda f: (
            -float(f["global_fosc_exclusion_margin"]),
            -float(f["synchronous_stability"]),
            -float(f["ordinary_stability"]),
            -int(f["member_count"]),
            str(f["family_id"]),
        )
    )
    return out
