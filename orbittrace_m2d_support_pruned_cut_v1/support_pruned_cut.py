#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

RADIUS = 1.0
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def family_id(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def diagram_sorted(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return np.empty((0, 2), dtype=float)
    req(a.ndim == 2 and a.shape[1] == 2 and np.all(np.isfinite(a)), "invalid diagram")
    return a[np.lexsort((a[:, 1], a[:, 0]))]


def support_pruned_cut(structural: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Exact parent support-resolved hierarchy reconstruction with one frozen cut-rule change.

    A sub-support immediate child (<4 events) no longer forces its reportable sibling
    to remain merged into the parent. The sub-support child becomes noise and recursion
    continues down the reportable sibling. No threshold beyond the inherited support=4
    is introduced.
    """
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = structural.physical_embedding(ordered)
    neigh = [list(map(int, r)) for r in cKDTree(Z).query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)]
    adj = [set(r) for r in neigh]
    req(len(neigh) == len(ids), "graph row count")
    for i, r in enumerate(neigh):
        req(r.count(i) == 1 and all(0 <= j < len(ids) for j in r), f"bad graph row {i}")
    req(all(i in adj[j] for i, r in enumerate(neigh) for j in r), "graph asymmetric")
    deg = np.asarray([len(r) for r in neigh], dtype=float)
    rho = deg / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0), "bad density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neigh, weights=rho)
    labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    L = int(model.n_leaves_)
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(labels.shape == (len(ids),) and L >= 1 and int(labels.min()) >= 0 and int(labels.max()) + 1 == L, "bad leaves")
    req(L - len(children) == roots_expected, "leaf/merge/root arithmetic")
    diagram = np.asarray(model.diagram_, dtype=float)
    ds = diagram_sorted(diagram)
    P = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0, dtype=float)
    req(len(P) == len(children) == len(ds) and np.all(P >= -1e-15), "bad finite persistence")
    P = np.maximum(P, 0.0)

    N = L + len(children)
    members: list[Any] = [None] * N
    parent = np.full(N, -1, dtype=np.int64)
    kids: list[Any] = [None] * N
    active_peak = np.full(N, np.nan, dtype=float)
    active_key: list[Any] = [None] * N
    merge_level = np.full(N, np.nan, dtype=float)
    for leaf in range(L):
        ix = np.flatnonzero(labels == leaf)
        req(len(ix) > 0, f"empty leaf {leaf}")
        members[leaf] = frozenset(ids[int(i)] for i in ix)
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        req(bool(keys), "no peak key")
        active_peak[leaf] = peak
        active_key[leaf] = keys[0]

    reconstructed: list[list[float]] = []
    dying: set[int] = set()
    for off, pair in enumerate(children):
        node = L + off
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b and parent[a] == -1 and parent[b] == -1, "bad hierarchy")
        ma, mb = members[a], members[b]
        req(ma is not None and mb is not None and ma.isdisjoint(mb), "bad child membership")
        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        if pa > pb or (pa == pb and ka < kb):
            winner, loser = a, b
        else:
            winner, loser = b, a
        members[node] = frozenset(ma.union(mb))
        kids[node] = (a, b)
        parent[a] = node
        parent[b] = node
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])
        req(loser not in dying, "mode died twice")
        dying.add(loser)
        death = float(active_peak[loser]) - float(P[off])
        merge_level[node] = death
        reconstructed.append([float(active_peak[loser]), death])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root count")
    req(sum(len(members[int(r)]) for r in roots) == len(ids), "roots do not partition")
    rec = diagram_sorted(np.asarray(reconstructed, dtype=float))
    req(rec.shape == ds.shape, "diagram shape")
    req(np.allclose(rec, ds, rtol=0.0, atol=1e-12), "diagram reconstruction mismatch")
    for t in np.unique(P):
        model.merge_threshold_ = float(t)
        req(int(model.n_clusters_) == int(np.count_nonzero(P > t) + roots_expected), f"threshold invariant {t}")

    full_candidates, full_summary = structural.topomodal_candidates(ordered)
    full_member_set = {tuple(sorted(str(x) for x in m)) for m in full_candidates}

    selected_nodes: list[int] = []
    discarded_nodes: list[int] = []

    def cut(node: int) -> None:
        m = members[node]
        req(m is not None, "missing node")
        ch = kids[node]
        if ch is None:
            if len(m) >= MIN_SUPPORT:
                selected_nodes.append(node)
            else:
                discarded_nodes.append(node)
            return
        a, b = ch
        sa, sb = len(members[a]), len(members[b])
        if sa >= MIN_SUPPORT and sb >= MIN_SUPPORT:
            cut(a)
            cut(b)
        elif sa >= MIN_SUPPORT and sb < MIN_SUPPORT:
            discarded_nodes.append(b)
            cut(a)
        elif sb >= MIN_SUPPORT and sa < MIN_SUPPORT:
            discarded_nodes.append(a)
            cut(b)
        elif len(m) >= MIN_SUPPORT:
            selected_nodes.append(node)
        else:
            discarded_nodes.append(node)

    for r in roots:
        cut(int(r))

    req(len(selected_nodes) == len(set(selected_nodes)), "duplicate selected node")
    req(len(discarded_nodes) == len(set(discarded_nodes)), "duplicate discarded node")
    selected_sets = [members[n] for n in selected_nodes]
    discarded_sets = [members[n] for n in discarded_nodes]
    req(all(m is not None and len(m) >= MIN_SUPPORT for m in selected_sets), "sub-support selected")
    req(all(m is not None and len(m) < MIN_SUPPORT for m in discarded_sets), "reportable node discarded")
    all_terminal = selected_sets + discarded_sets
    for i, a in enumerate(all_terminal):
        for b in all_terminal[i + 1 :]:
            req(a.isdisjoint(b), "terminal sets overlap")
    terminal_union = frozenset().union(*all_terminal) if all_terminal else frozenset()
    req(terminal_union == frozenset(ids), "selected+noise do not partition universe")
    req(all(tuple(sorted(m)) in full_member_set for m in selected_sets), "cut node absent from frozen hierarchy")

    rows: list[dict[str, Any]] = []
    for node, m in zip(selected_nodes, selected_sets):
        p = int(parent[node])
        outside = 0.0 if p == -1 else float(merge_level[p])
        req(np.isfinite(outside), f"missing outside merge {node}")
        contrast = float(active_peak[node]) - outside
        req(contrast >= -1e-12 and np.isfinite(contrast), f"bad contrast {node} {contrast}")
        contrast = max(contrast, 0.0)
        tup = tuple(sorted(str(x) for x in m))
        rows.append({
            "family_id": family_id("TSPC1", tup),
            "family_hash": structural.member_hash(m),
            "event_ids": list(tup),
            "member_count": len(tup),
            "node": int(node),
            "is_root": bool(p == -1),
            "active_mode_peak": float(active_peak[node]),
            "active_mode_key": str(active_key[node]),
            "outside_merge_level": outside,
            "modal_contrast": contrast,
        })
    rows.sort(key=lambda r: (-float(r["modal_contrast"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    discarded_event_count = sum(len(m) for m in discarded_sets)
    return rows, {
        "full_candidate_count": int(full_summary["candidate_count"]),
        "full_candidate_rows": full_summary["candidate_rows"],
        "cut_candidate_count": len(rows),
        "root_count": len(roots),
        "selected_root_count": sum(bool(r["is_root"]) for r in rows),
        "pairwise_disjoint": True,
        "selected_plus_noise_partition": True,
        "discarded_subsupport_node_count": len(discarded_nodes),
        "discarded_subsupport_event_count": int(discarded_event_count),
        "covered_event_count": int(len(ids) - discarded_event_count),
        "coverage_fraction": float((len(ids) - discarded_event_count) / len(ids)) if ids else 0.0,
        "max_selected_member_count": max((len(m) for m in selected_sets), default=0),
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(rec - ds))) if rec.size else 0.0,
        "median_radius_degree": float(np.median(deg)),
        "p90_radius_degree": float(np.quantile(deg, 0.9)),
        "cut_rule": "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport",
    }
