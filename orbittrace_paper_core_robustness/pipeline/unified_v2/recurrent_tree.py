"""Exposure-normalized recurrent extraction from one HDBSCAN hierarchy."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import inspect
from typing import Any, Iterable

import hdbscan
import hdbscan.hdbscan_ as hdbscan_internal
import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_clusters
from sklearn.utils import check_array as sklearn_check_array

from .config import V2Config


def _install_hdbscan_compatibility() -> None:
    accepted = set(inspect.signature(sklearn_check_array).parameters)
    def compatible_check_array(*args: Any, **kwargs: Any) -> np.ndarray:
        if "ensure_all_finite" in kwargs and "ensure_all_finite" not in accepted:
            kwargs["force_all_finite"] = kwargs.pop("ensure_all_finite")
        if "force_all_finite" in kwargs and "force_all_finite" not in accepted:
            kwargs["ensure_all_finite"] = kwargs.pop("force_all_finite")
        return sklearn_check_array(*args, **kwargs)
    hdbscan_internal.check_array = compatible_check_array


def _canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(np.flatnonzero(labels == label).tolist()) for label in sorted(int(value) for value in np.unique(labels) if int(value) >= 0)))


def _birth_lambdas(tree: np.ndarray) -> dict[int, float]:
    root = int(tree["parent"].min())
    births: dict[int, float] = {}
    for child, value in zip(tree["child"], tree["lambda_val"]):
        child_id = int(child); lam = float(value)
        births[child_id] = min(births.get(child_id, lam), lam)
    births[root] = 0.0
    return births


def _descendant_year_counts(tree: np.ndarray, years: np.ndarray) -> tuple[tuple[int, ...], dict[int, np.ndarray]]:
    root = int(tree["parent"].min())
    if years.shape != (root,):
        raise ValueError("year vector must align with condensed-tree input points")
    year_values = tuple(sorted(int(value) for value in np.unique(years)))
    if len(year_values) < 2:
        raise ValueError("at least two observing years are required")
    year_index = {year: index for index, year in enumerate(year_values)}
    children: dict[int, list[int]] = defaultdict(list); nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        parent_id = int(parent); child_id = int(child)
        children[parent_id].append(child_id); nodes.add(parent_id)
        if child_id >= root: nodes.add(child_id)
    counts: dict[int, np.ndarray] = {}
    for node in sorted(nodes, reverse=True):
        total = np.zeros(len(year_values), dtype=np.int64)
        for child in children.get(node, []):
            if child < root: total[year_index[int(years[child])]] += 1
            else:
                if child not in counts: raise RuntimeError(f"missing descendant count for cluster child {child}")
                total += counts[child]
        counts[node] = total
    return year_values, counts


def recurrent_stability(tree: np.ndarray, years: Iterable[int], *, recurrence_quantile: float = 0.25, min_year_support_fraction: float = 0.60, min_year_events: int = 1, exposure: dict[int, float] | None = None) -> tuple[dict[float, float], dict[int, tuple[float, ...]], dict[int, tuple[int, ...]], dict[str, Any]]:
    years_array = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_array.shape != (root,): raise ValueError("year vector must align exactly with input points")
    year_values, descendant_counts = _descendant_year_counts(tree, years_array)
    totals = np.asarray([float((years_array == year).sum()) for year in year_values], dtype=float)
    if exposure is not None: totals = np.asarray([float(exposure[year]) for year in year_values], dtype=float)
    if np.any(totals <= 0): raise ValueError("every observing year must have positive exposure")
    if not 0.0 <= recurrence_quantile <= 1.0: raise ValueError("recurrence_quantile must lie in [0, 1]")
    births = _birth_lambdas(tree)
    parents = sorted(set(int(value) for value in tree["parent"]))
    annual_mass = {parent: np.zeros(len(year_values), dtype=float) for parent in parents}
    for parent, child, lam, child_size in tree:
        parent_id = int(parent); child_id = int(child)
        if child_id < root:
            branch = np.asarray([int(years_array[child_id] == year) for year in year_values], dtype=np.int64)
        else: branch = descendant_counts[child_id]
        if int(branch.sum()) != int(child_size): raise RuntimeError("condensed-tree descendant accounting mismatch")
        annual_mass[parent_id] += (float(lam) - births[parent_id]) * branch
    annual_normalized = {parent: tuple((annual_mass[parent] / totals).tolist()) for parent in parents}
    counts = {parent: tuple(int(value) for value in descendant_counts[parent].tolist()) for parent in parents}
    scores: dict[float, float] = {}; support: dict[int, float] = {}
    for parent in parents:
        annual_counts = np.asarray(counts[parent], dtype=int); values = np.asarray(annual_normalized[parent], dtype=float)
        supported = annual_counts >= int(min_year_events); fraction = float(np.mean(supported)); support[parent] = fraction
        if fraction < float(min_year_support_fraction): scores[float(parent)] = 0.0; continue
        try: tail = float(np.quantile(values, recurrence_quantile, method="lower"))
        except TypeError: tail = float(np.quantile(values, recurrence_quantile, interpolation="lower"))
        scores[float(parent)] = max(0.0, tail)
    diagnostics = {"year_values": list(year_values), "exposure": {str(year): float(total) for year, total in zip(year_values, totals)}, "recurrence_quantile": float(recurrence_quantile), "min_year_support_fraction": float(min_year_support_fraction), "min_year_events": int(min_year_events), "node_support_fraction": {str(node): float(value) for node, value in support.items()}}
    return scores, annual_normalized, counts, diagnostics


def _eom_labels(tree: np.ndarray, stability: dict[float, float]) -> np.ndarray:
    labels, _probabilities, _stabilities = get_clusters(tree, dict(stability), cluster_selection_method="eom", allow_single_cluster=False, match_reference_implementation=False, cluster_selection_epsilon=0.0, max_cluster_size=0)
    return np.asarray(labels, dtype=np.int64)


def _leaf_labels(tree: np.ndarray, stability: dict[float, float]) -> tuple[np.ndarray, np.ndarray]:
    labels, probabilities, _stabilities = get_clusters(tree, dict(stability), cluster_selection_method="leaf", allow_single_cluster=False, match_reference_implementation=False, cluster_selection_epsilon=0.0, max_cluster_size=0)
    return np.asarray(labels, dtype=np.int64), np.asarray(probabilities, dtype=float)


def _selected_eom_nodes(tree: np.ndarray, stability: dict[float, float]) -> tuple[int, ...]:
    work = {int(key): float(value) for key, value in stability.items()}
    node_list = sorted(work, reverse=True)[:-1]
    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    for parent, child in zip(cluster_tree["parent"], cluster_tree["child"]): children[int(parent)].append(int(child))
    selected = {node: True for node in node_list}
    def descendants(root: int) -> list[int]:
        output: list[int] = []; queue = [root]
        while queue:
            current = queue.pop(0); output.append(current); queue.extend(children.get(current, []))
        return output
    for node in node_list:
        subtree = sum(work[child] for child in children.get(node, []))
        if subtree > work[node]: selected[node] = False; work[node] = subtree
        else:
            for child in descendants(node):
                if child != node: selected[child] = False
    return tuple(sorted(node for node, keep in selected.items() if keep))


def _family_id(prefix: str, event_ids: Iterable[str]) -> str:
    payload = "|".join(sorted(str(value) for value in event_ids)).encode()
    return prefix + hashlib.sha256(payload).hexdigest()[:20]


def _candidate(prefix: str, method: str, members: np.ndarray, event_ids: np.ndarray, years: np.ndarray, year_values: tuple[int, ...], *, node_id: int | None = None, recurrent_score: float | None = None, ordinary_score: float | None = None, annual_normalized: tuple[float, ...] | None = None, annual_counts: tuple[int, ...] | None = None, membership_probability: float | None = None) -> dict[str, Any]:
    ids = tuple(sorted(str(event_ids[index]) for index in members))
    counts = tuple(int(np.sum(years[members] == year)) for year in year_values) if annual_counts is None else tuple(int(value) for value in annual_counts)
    return {"family_id": _family_id(prefix, ids), "hierarchy_method": method, "node_id": None if node_id is None else int(node_id), "event_ids": list(ids), "members": [int(value) for value in members.tolist()], "member_count": int(len(members)), "year_values": [int(value) for value in year_values], "members_by_year": {str(year): int(count) for year, count in zip(year_values, counts)}, "annual_counts": list(counts), "annual_normalized_stability": None if annual_normalized is None else [float(value) for value in annual_normalized], "recurrent_stability": None if recurrent_score is None else float(recurrent_score), "ordinary_stability": None if ordinary_score is None else float(ordinary_score), "mean_membership_probability": None if membership_probability is None else float(membership_probability)}


def fit_recurrent_hierarchy(matrix: np.ndarray, years: np.ndarray, event_ids: np.ndarray, config: V2Config | None = None, *, include_leaves: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    config = config or V2Config(); _install_hdbscan_compatibility()
    values = np.asarray(matrix, dtype=float); year_values = np.asarray(years, dtype=np.int64); ids = np.asarray(event_ids, dtype=str)
    if values.ndim != 2 or values.shape[0] != len(year_values) or values.shape[0] != len(ids): raise ValueError("matrix, years, and event_ids must have the same row count")
    if values.shape[0] < max(config.min_cluster_size * 2, config.min_samples + 1): raise ValueError("not enough rows for a recurrent hierarchy")
    if len(np.unique(year_values)) < 2: raise ValueError("at least two observing years are required")
    model = hdbscan.HDBSCAN(min_cluster_size=int(config.min_cluster_size), min_samples=int(config.min_samples), metric="euclidean", cluster_selection_method="eom", cluster_selection_epsilon=0.0, allow_single_cluster=False, prediction_data=False, core_dist_n_jobs=int(config.core_dist_n_jobs)).fit(values)
    tree = model.condensed_tree_._raw_tree
    ordinary_stability = compute_stability(tree); ordinary_labels = _eom_labels(tree, ordinary_stability)
    if _canonical_partition(model.labels_) != _canonical_partition(ordinary_labels): raise RuntimeError("ordinary HDBSCAN-EOM path diverged from fitted assignments")
    recurrent, annual_normalized, annual_counts, recurrence_diag = recurrent_stability(tree, year_values, recurrence_quantile=config.recurrence_quantile, min_year_support_fraction=config.min_year_support_fraction, min_year_events=config.min_year_events)
    recurrent_labels = _eom_labels(tree, recurrent); selected_nodes = _selected_eom_nodes(tree, recurrent)
    positive = sorted(int(value) for value in np.unique(recurrent_labels) if int(value) >= 0)
    if positive != list(range(len(selected_nodes))): raise RuntimeError("recurrent EOM labels no longer align with selected nodes")
    parents: list[dict[str, Any]] = []
    year_tuple = tuple(sorted(int(value) for value in np.unique(year_values)))
    for label, node in enumerate(selected_nodes):
        members = np.flatnonzero(recurrent_labels == label)
        if members.size < config.min_cluster_size: continue
        parents.append(_candidate("REOM2", "recurrent_eom", members, ids, year_values, year_tuple, node_id=node, recurrent_score=recurrent[float(node)], ordinary_score=ordinary_stability[float(node)], annual_normalized=annual_normalized[node], annual_counts=annual_counts[node]))
    leaves: list[dict[str, Any]] = []
    if include_leaves:
        leaf_labels, probabilities = _leaf_labels(tree, ordinary_stability); exposure = {year: int(np.sum(year_values == year)) for year in year_tuple}
        for label in sorted(int(value) for value in np.unique(leaf_labels) if int(value) >= 0):
            members = np.flatnonzero(leaf_labels == label)
            if members.size < config.min_cluster_size: continue
            counts = tuple(int(np.sum(year_values[members] == year)) for year in year_tuple); normalized = tuple(count / exposure[year] for count, year in zip(counts, year_tuple))
            leaves.append(_candidate("LEAF2", "leaf", members, ids, year_values, year_tuple, annual_normalized=normalized, annual_counts=counts, membership_probability=float(np.mean(probabilities[members]))))
    parents.sort(key=lambda item: (-float(item["recurrent_stability"] or 0.0), -float(item["ordinary_stability"] or 0.0), -int(item["member_count"]), item["family_id"]))
    leaves.sort(key=lambda item: (-float(np.quantile(item["annual_normalized_stability"], config.recurrence_quantile)), -float(item["mean_membership_probability"] or 0.0), -int(item["member_count"]), item["family_id"]))
    for rank, item in enumerate(parents, start=1): item["rank"] = rank
    for rank, item in enumerate(leaves, start=1): item["rank"] = rank
    diagnostics = {"events": int(values.shape[0]), "dimensions": int(values.shape[1]), "years": sorted(int(value) for value in np.unique(year_values)), "min_cluster_size": int(config.min_cluster_size), "min_samples": int(config.min_samples), "ordinary_candidates": int(len(set(int(value) for value in ordinary_labels if int(value) >= 0))), "recurrent_candidates": int(len(parents)), "leaf_candidates": int(len(leaves)), "mechanism_active": _canonical_partition(ordinary_labels) != _canonical_partition(recurrent_labels), "recurrence": recurrence_diag}
    return parents, leaves, diagnostics


__all__ = ["fit_recurrent_hierarchy", "recurrent_stability"]
