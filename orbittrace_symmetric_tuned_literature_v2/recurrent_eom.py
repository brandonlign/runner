from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_clusters


def _birth_lambdas(tree: np.ndarray) -> dict[int, float]:
    smallest_cluster = int(tree["parent"].min())
    births: dict[int, float] = {}
    for child, lam in zip(tree["child"], tree["lambda_val"]):
        child = int(child)
        lam = float(lam)
        births[child] = min(births.get(child, lam), lam)
    births[smallest_cluster] = 0.0
    return births


def _descendant_year_counts(tree: np.ndarray, years: np.ndarray) -> dict[int, np.ndarray]:
    root = int(tree["parent"].min())
    n_points = root
    if years.shape != (n_points,):
        raise ValueError(f"years shape {years.shape} does not match condensed-tree point count {n_points}")
    year_values = tuple(sorted(int(y) for y in np.unique(years)))
    if len(year_values) != 2:
        raise ValueError(f"recurrent EOM v1 requires exactly two years, got {year_values}")
    y_index = {y: i for i, y in enumerate(year_values)}
    children: dict[int, list[int]] = defaultdict(list)
    cluster_nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        p = int(parent)
        c = int(child)
        children[p].append(c)
        cluster_nodes.add(p)
        if c >= n_points:
            if c <= p:
                raise RuntimeError(f"HDBSCAN condensed-tree topological order changed: parent={p}, child={c}")
            cluster_nodes.add(c)
    memo: dict[int, np.ndarray] = {}
    for node in sorted(cluster_nodes, reverse=True):
        out = np.zeros(2, dtype=np.int64)
        for child in children.get(node, []):
            if child < n_points:
                out[y_index[int(years[child])]] += 1
            else:
                if child not in memo:
                    raise RuntimeError(f"bottom-up descendant count missing cluster child {child} for parent {node}")
                out += memo[child]
        memo[node] = out
    return memo


def recurrent_stability(tree: np.ndarray, years: Iterable[int]) -> tuple[dict[float, float], dict[int, tuple[float, float]]]:
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError("year vector must align exactly with condensed-tree input points")
    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(year_values) != 2:
        raise ValueError("exactly two observing years are required")
    totals = np.asarray([(years_arr == y).sum() for y in year_values], dtype=float)
    if np.any(totals <= 0):
        raise ValueError("both observing years must contain events")
    births = _birth_lambdas(tree)
    counts = _descendant_year_counts(tree, years_arr)
    parents = sorted(set(int(x) for x in tree["parent"]))
    annual = {p: np.zeros(2, dtype=float) for p in parents}
    for parent, child, lam, child_size in tree:
        p = int(parent)
        c = int(child)
        lam = float(lam)
        if c < root:
            branch_counts = np.asarray([int(years_arr[c] == y) for y in year_values], dtype=np.int64)
        else:
            branch_counts = counts[c]
        if int(branch_counts.sum()) != int(child_size):
            raise RuntimeError(
                f"condensed-tree descendant accounting mismatch for child {c}: "
                f"{int(branch_counts.sum())} != {int(child_size)}"
            )
        annual[p] += (lam - births[p]) * branch_counts
    annual_norm: dict[int, tuple[float, float]] = {}
    recurrent: dict[float, float] = {}
    for p in parents:
        vals = annual[p] / totals
        annual_norm[p] = (float(vals[0]), float(vals[1]))
        recurrent[float(p)] = float(min(vals[0], vals[1]))
    return recurrent, annual_norm


def eom_labels(tree: np.ndarray, stability: dict[float, float]) -> np.ndarray:
    labels, _probabilities, _stabilities = get_clusters(
        tree,
        dict(stability),
        cluster_selection_method="eom",
        allow_single_cluster=False,
        match_reference_implementation=False,
        cluster_selection_epsilon=0.0,
        max_cluster_size=0,
    )
    return np.asarray(labels, dtype=np.int64)


def parent_labels_through_custom_path(tree: np.ndarray) -> np.ndarray:
    return eom_labels(tree, compute_stability(tree))


def selected_eom_nodes(tree: np.ndarray, stability: dict[float, float]) -> tuple[int, ...]:
    work = {int(k): float(v) for k, v in stability.items()}
    node_list = sorted(work.keys(), reverse=True)[:-1]
    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    for parent, child in zip(cluster_tree["parent"], cluster_tree["child"]):
        children[int(parent)].append(int(child))
    is_cluster = {node: True for node in node_list}
    def descendants(root: int) -> list[int]:
        out: list[int] = []
        q = [root]
        while q:
            current = q.pop(0)
            out.append(current)
            q.extend(children.get(current, []))
        return out
    for node in node_list:
        subtree = sum(work[ch] for ch in children.get(node, []))
        if subtree > work[node]:
            is_cluster[node] = False
            work[node] = subtree
        else:
            for sub in descendants(node):
                if sub != node:
                    is_cluster[sub] = False
    return tuple(sorted(node for node, keep in is_cluster.items() if keep))
