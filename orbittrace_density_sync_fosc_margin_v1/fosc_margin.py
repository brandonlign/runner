from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np

TOL = 1e-12


def fosc_optimal_values_and_selected_margins(
    tree: np.ndarray,
    stability: Mapping[float, float],
    selected_nodes: Sequence[int],
) -> tuple[dict[int, float], dict[int, float], dict[int, float]]:
    """Return exact FOSC subtree optima and decision margins for selected nodes.

    Parameters
    ----------
    tree
        HDBSCAN condensed-tree raw array.
    stability
        Scalar node objective used by the already-frozen FOSC/EOM extraction.
    selected_nodes
        Final selected-node tuple from that same exact extraction.

    Returns
    -------
    optimal
        O(C)=max(S(C), sum_D O(D)) for every cluster node in the objective map.
    alternative
        For every final selected node C, the best descendant-only objective
        sum_D O(D) obtained when C itself is forbidden.
    margin
        For every final selected node C, S(C)-alternative(C).  This is the
        exact additive objective loss from replacing C by its optimal
        descendant cut while all disjoint selected subtrees remain unchanged.
    """
    raw = {int(k): float(v) for k, v in stability.items()}
    if not raw:
        raise ValueError("stability map is empty")
    if any(not np.isfinite(v) for v in raw.values()):
        raise ValueError("stability map contains non-finite values")

    root = int(tree["parent"].min())
    if root not in raw:
        raise RuntimeError(f"root {root} missing from stability map")

    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    for p_raw, c_raw in zip(cluster_tree["parent"], cluster_tree["child"]):
        p = int(p_raw)
        c = int(c_raw)
        if p not in raw:
            raise RuntimeError(f"cluster parent {p} missing from stability map")
        if c not in raw:
            raise RuntimeError(f"cluster child {c} missing from stability map")
        if c <= p:
            raise RuntimeError(f"condensed-tree cluster order changed: parent={p}, child={c}")
        children[p].append(c)

    # HDBSCAN condensed cluster IDs are topological: children have larger IDs.
    optimal: dict[int, float] = {}
    alternative_all: dict[int, float] = {}
    locally_parent_optimal: dict[int, bool] = {}
    for node in sorted(raw, reverse=True):
        child_sum = float(sum(optimal[ch] for ch in children.get(node, [])))
        alternative_all[node] = child_sum
        own = raw[node]
        # FOSC/HDBSCAN EOM ties go to the parent: only a strictly larger child
        # solution rejects the node.
        parent_wins = not (child_sum > own)
        locally_parent_optimal[node] = parent_wins
        optimal[node] = own if parent_wins else child_sum

    selected = tuple(sorted(int(x) for x in selected_nodes))
    if len(selected) != len(set(selected)):
        raise ValueError("selected_nodes contains duplicates")
    if root in selected:
        raise RuntimeError("root may not be selected when allow_single_cluster=False")

    selected_set = set(selected)
    margins: dict[int, float] = {}
    alternatives: dict[int, float] = {}
    for node in selected:
        if node not in raw:
            raise RuntimeError(f"selected node {node} missing from stability map")
        if not locally_parent_optimal[node]:
            raise RuntimeError(f"selected node {node} is not locally FOSC-optimal")
        alt = alternative_all[node]
        m = raw[node] - alt
        scale = max(1.0, abs(raw[node]), abs(alt))
        if m < -TOL * scale:
            raise RuntimeError(f"negative selected-node FOSC margin for {node}: {m}")
        if m < 0.0:
            m = 0.0
        alternatives[node] = float(alt)
        margins[node] = float(m)

    # Final selected nodes must form an antichain.  This verifies that replacing
    # one selected node by its descendant optimum leaves every other selected
    # subtree disjoint, which gives the exact global-loss interpretation.
    selected_descendant_count = {node: 0 for node in selected}
    for ancestor in selected:
        stack = list(children.get(ancestor, []))
        while stack:
            cur = stack.pop()
            if cur in selected_set:
                selected_descendant_count[ancestor] += 1
            stack.extend(children.get(cur, []))
    bad = [node for node, n in selected_descendant_count.items() if n]
    if bad:
        raise RuntimeError(f"selected FOSC nodes are not an antichain: {bad[:5]}")

    return optimal, alternatives, margins


def rank_candidates_by_margin(
    candidates: Sequence[dict],
    margins: Mapping[int, float],
) -> list[dict]:
    """Reorder exact #1263 candidates by the frozen FOSC decision margin."""
    out: list[dict] = []
    seen_nodes: set[int] = set()
    for row in candidates:
        node = int(row["node_id"])
        if node in seen_nodes:
            raise RuntimeError(f"duplicate candidate node {node}")
        seen_nodes.add(node)
        if node not in margins:
            raise RuntimeError(f"missing FOSC margin for candidate node {node}")
        r = dict(row)
        r["fosc_decision_margin"] = float(margins[node])
        out.append(r)
    if seen_nodes != set(int(k) for k in margins):
        missing = sorted(set(int(k) for k in margins) - seen_nodes)
        raise RuntimeError(f"margin map contains noncandidate selected nodes: {missing[:5]}")

    out.sort(
        key=lambda f: (
            -float(f["fosc_decision_margin"]),
            -float(f["synchronous_stability"]),
            -float(f["ordinary_stability"]),
            -int(f["member_count"]),
            str(f["family_id"]),
        )
    )
    return out
