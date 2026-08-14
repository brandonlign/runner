from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np


def _cluster_structure(tree: np.ndarray) -> tuple[int, dict[int, list[int]], dict[int, int], set[int]]:
    root = int(tree["parent"].min())
    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    parent_by_child: dict[int, int] = {}
    cluster_nodes: set[int] = {root}
    for parent, child in zip(cluster_tree["parent"], cluster_tree["child"]):
        p = int(parent)
        c = int(child)
        if c in parent_by_child and parent_by_child[c] != p:
            raise RuntimeError(f"condensed cluster child has multiple parents: {c}")
        parent_by_child[c] = p
        children[p].append(c)
        cluster_nodes.add(p)
        cluster_nodes.add(c)
    return root, children, parent_by_child, cluster_nodes


def _descendants(children: Mapping[int, Sequence[int]], root: int) -> list[int]:
    out: list[int] = []
    stack = [int(root)]
    while stack:
        current = stack.pop()
        out.append(current)
        stack.extend(reversed(tuple(int(x) for x in children.get(current, ()))))
    return out


def consensus_selected_nodes(
    tree: np.ndarray,
    annual_stability: Mapping[int, tuple[float, float]],
) -> tuple[int, ...]:
    """Frozen componentwise two-year EOM node selection.

    A non-root node may replace its effective child solution only if its annual
    normalized EOM is strictly positive in both years and componentwise at least
    as large as the summed effective child vector. Ties favor the parent.
    """
    root, children, _parent_by_child, _cluster_nodes = _cluster_structure(tree)
    annual = {int(k): np.asarray(v, dtype=float) for k, v in annual_stability.items()}
    if root not in annual:
        raise ValueError("root missing from annual stability mapping")
    for node, vec in annual.items():
        if vec.shape != (2,) or not np.all(np.isfinite(vec)) or np.any(vec < 0.0):
            raise ValueError(f"invalid annual stability vector for node {node}: {vec}")

    node_list = sorted((node for node in annual if node != root), reverse=True)
    work = {node: vec.copy() for node, vec in annual.items()}
    is_cluster = {node: True for node in node_list}

    for node in node_list:
        child_nodes = children.get(node, [])
        subtree = np.zeros(2, dtype=float)
        for child in child_nodes:
            if child not in work:
                raise RuntimeError(f"missing effective vector for cluster child {child} of {node}")
            subtree += work[child]

        base = annual[node]
        eligible = bool(np.all(base > 0.0))
        parent_dominates = bool(np.all(base >= subtree))
        if eligible and parent_dominates:
            work[node] = base.copy()
            for sub in _descendants(children, node):
                if sub != node and sub in is_cluster:
                    is_cluster[sub] = False
        else:
            is_cluster[node] = False
            work[node] = subtree

    selected = tuple(sorted(node for node, keep in is_cluster.items() if keep))

    # Structural sanity: selected nodes must be an antichain and recurrently supported.
    selected_set = set(selected)
    for node in selected:
        if not np.all(annual[node] > 0.0):
            raise RuntimeError(f"consensus selected zero-year-support node {node}")
        for sub in _descendants(children, node):
            if sub != node and sub in selected_set:
                raise RuntimeError(f"consensus selected ancestor/descendant pair: {node}, {sub}")
    return selected


def labels_from_selected_nodes(tree: np.ndarray, selected_nodes: Sequence[int]) -> np.ndarray:
    """Assign compact labels by first selected condensed-tree ancestor.

    This is an implementation bridge only; scientific node selection is supplied
    separately. Labels are compacted in ascending selected-node order.
    """
    root = int(tree["parent"].min())
    n_points = root
    selected = tuple(sorted(int(x) for x in selected_nodes))
    if root in selected:
        raise ValueError("root selection is forbidden by allow_single_cluster=False")
    if len(selected) != len(set(selected)):
        raise ValueError("duplicate selected node")
    label_by_node = {node: lab for lab, node in enumerate(selected)}

    parent_by_child: dict[int, int] = {}
    for parent, child in zip(tree["parent"], tree["child"]):
        p = int(parent)
        c = int(child)
        if c in parent_by_child and parent_by_child[c] != p:
            raise RuntimeError(f"condensed-tree child has multiple parents: {c}")
        parent_by_child[c] = p

    labels = np.full(n_points, -1, dtype=np.int64)
    for point in range(n_points):
        current = point
        seen: set[int] = set()
        while current in parent_by_child:
            if current in seen:
                raise RuntimeError(f"cycle in condensed-tree ancestry at {current}")
            seen.add(current)
            parent = parent_by_child[current]
            if parent in label_by_node:
                labels[point] = int(label_by_node[parent])
                break
            current = parent
    return labels


def consensus_labels(
    tree: np.ndarray,
    annual_stability: Mapping[int, tuple[float, float]],
) -> tuple[np.ndarray, tuple[int, ...]]:
    selected = consensus_selected_nodes(tree, annual_stability)
    return labels_from_selected_nodes(tree, selected), selected
