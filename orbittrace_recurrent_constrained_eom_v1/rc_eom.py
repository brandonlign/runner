from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

MIN_ANNUAL_SUPPORT = 4


def _descendant_year_counts(tree: np.ndarray, years: np.ndarray) -> dict[int, np.ndarray]:
    root = int(tree["parent"].min())
    if years.shape != (root,):
        raise ValueError(f"years shape {years.shape} does not match condensed-tree point count {root}")
    year_values = tuple(sorted(int(y) for y in np.unique(years)))
    if len(year_values) != 2:
        raise ValueError(f"RC-EOM requires exactly two observing years, got {year_values}")
    y_index = {y: i for i, y in enumerate(year_values)}

    children: dict[int, list[int]] = defaultdict(list)
    cluster_nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        p, c = int(parent), int(child)
        children[p].append(c)
        cluster_nodes.add(p)
        if c >= root:
            if c <= p:
                raise RuntimeError(f"condensed-tree topological order changed: parent={p}, child={c}")
            cluster_nodes.add(c)

    memo: dict[int, np.ndarray] = {}
    for node in sorted(cluster_nodes, reverse=True):
        out = np.zeros(2, dtype=np.int64)
        for child in children.get(node, []):
            if child < root:
                out[y_index[int(years[child])]] += 1
            else:
                if child not in memo:
                    raise RuntimeError(f"missing descendant counts for child={child}, parent={node}")
                out += memo[child]
        memo[node] = out
    return memo


def _cluster_children(tree: np.ndarray) -> dict[int, list[int]]:
    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    for parent, child in zip(cluster_tree["parent"], cluster_tree["child"]):
        children[int(parent)].append(int(child))
    return children


def _descendants(children: dict[int, list[int]], root: int) -> list[int]:
    out: list[int] = []
    stack = [root]
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(children.get(node, []))
    return out


def select_eom_nodes(
    tree: np.ndarray,
    stability: dict[float, float],
    eligible: dict[int, bool] | None = None,
) -> tuple[int, ...]:
    """Exact zero-epsilon EOM dynamic program with an optional feasibility constraint.

    With ``eligible=None`` this mirrors ordinary HDBSCAN EOM selection. With an
    eligibility map, an ineligible node cannot be selected; instead the best
    already-computed eligible descendant mass is propagated to its parent.
    """
    work = {int(k): float(v) for k, v in stability.items()}
    node_list = sorted(work.keys(), reverse=True)[:-1]  # root excluded as allow_single_cluster=False
    children = _cluster_children(tree)
    keep = {node: True for node in node_list}

    for node in node_list:
        subtree = float(sum(work[ch] for ch in children.get(node, [])))
        allowed = True if eligible is None else bool(eligible.get(node, False))
        if (not allowed) or subtree > work[node]:
            keep[node] = False
            work[node] = subtree
        else:
            for sub in _descendants(children, node):
                if sub != node:
                    keep[sub] = False
    return tuple(sorted(node for node, yes in keep.items() if yes))


def recurrent_constrained_eom(
    tree: np.ndarray,
    years: Iterable[int],
    min_annual_support: int = MIN_ANNUAL_SUPPORT,
) -> tuple[tuple[int, ...], dict[float, float], dict[int, tuple[int, int]], dict[int, bool]]:
    """Maximize ordinary EOM stability subject to a two-year support constraint.

    The HDBSCAN hierarchy and ordinary EOM stability are unchanged. A cluster
    node is feasible iff it contains at least ``min_annual_support`` descendants
    from each of the two observing years. The flat clustering is the maximum-EOM
    antichain among feasible nodes.
    """
    if int(min_annual_support) != MIN_ANNUAL_SUPPORT:
        raise ValueError(f"frozen RC-EOM annual support is {MIN_ANNUAL_SUPPORT}")
    years_arr = np.asarray(list(years), dtype=np.int64)
    ordinary = compute_stability(tree)
    counts_arr = _descendant_year_counts(tree, years_arr)
    counts = {int(k): (int(v[0]), int(v[1])) for k, v in counts_arr.items()}
    eligible = {
        node: bool(pair[0] >= MIN_ANNUAL_SUPPORT and pair[1] >= MIN_ANNUAL_SUPPORT)
        for node, pair in counts.items()
    }
    nodes = select_eom_nodes(tree, ordinary, eligible)
    if any(not eligible.get(node, False) for node in nodes):
        raise RuntimeError("RC-EOM selected an ineligible node")
    return nodes, ordinary, counts, eligible


def selected_memberships(tree: np.ndarray, nodes: Iterable[int]) -> dict[int, tuple[int, ...]]:
    """Return exact point descendants for selected condensed-tree cluster nodes."""
    root = int(tree["parent"].min())
    children: dict[int, list[int]] = defaultdict(list)
    cluster_nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        p, c = int(parent), int(child)
        children[p].append(c)
        cluster_nodes.add(p)
        if c >= root:
            cluster_nodes.add(c)

    memo: dict[int, tuple[int, ...]] = {}
    for node in sorted(cluster_nodes, reverse=True):
        points: list[int] = []
        for child in children.get(node, []):
            if child < root:
                points.append(child)
            else:
                points.extend(memo[child])
        memo[node] = tuple(sorted(points))

    out: dict[int, tuple[int, ...]] = {}
    seen: set[int] = set()
    for node in nodes:
        node = int(node)
        if node not in memo:
            raise RuntimeError(f"selected node missing descendant membership: {node}")
        members = memo[node]
        if seen.intersection(members):
            raise RuntimeError("RC-EOM selected memberships overlap")
        seen.update(members)
        out[node] = members
    return out
