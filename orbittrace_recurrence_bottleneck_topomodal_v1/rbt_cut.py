#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

RADIUS = 1.0
MIN_SUPPORT = 4
YEARS = (2022, 2023)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def family_id(members: tuple[str, ...]) -> str:
    return hashlib.sha256(("RBT1|" + "|".join(members)).encode()).hexdigest()[:20]


def member_hash(members: frozenset[str]) -> str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def diagram_sorted(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return np.empty((0, 2), dtype=float)
    req(a.ndim == 2 and a.shape[1] == 2 and np.all(np.isfinite(a)), "invalid diagram")
    return a[np.lexsort((a[:, 1], a[:, 0]))]


def recurrence_bottleneck_cut(structural: Any, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "panel missing a year")
    n22 = int(np.sum(years == 2022))
    n23 = int(np.sum(years == 2023))
    req(n22 > 0 and n23 > 0, "zero annual sample size")

    z = structural.physical_embedding(ordered)
    raw = cKDTree(z).query_ball_point(z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neigh = [list(map(int, row)) for row in raw]
    req(len(neigh) == len(ids), "radius graph row count")
    adj = [set(row) for row in neigh]
    for i, row in enumerate(neigh):
        req(row.count(i) == 1 and all(0 <= j < len(ids) for j in row), f"bad radius graph row {i}")
    req(all(i in adj[j] for i, row in enumerate(neigh) for j in row), "radius graph asymmetric")

    d22 = np.asarray([sum(years[j] == 2022 for j in row) for row in neigh], dtype=np.int64)
    d23 = np.asarray([sum(years[j] == 2023 for j in row) for row in neigh], dtype=np.int64)
    total_degree = np.asarray([len(row) for row in neigh], dtype=np.int64)
    req(np.all(d22 >= 0) and np.all(d23 >= 0) and np.all(d22 + d23 == total_degree), "annual degree accounting")
    rho22 = d22.astype(float) / float(n22)
    rho23 = d23.astype(float) / float(n23)
    rho = np.minimum(rho22, rho23)
    req(np.all(np.isfinite(rho)) and np.all(rho >= 0.0), "invalid recurrence bottleneck density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neigh, weights=rho)
    labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    L = int(model.n_leaves_)
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(labels.shape == (len(ids),) and L >= 1 and int(labels.min()) >= 0 and int(labels.max()) + 1 == L, "bad ToMATo leaves")
    req(L - len(children) == roots_expected, "leaf/merge/root arithmetic")

    diagram = np.asarray(model.diagram_, dtype=float)
    ds = diagram_sorted(diagram)
    persistence = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0, dtype=float)
    req(len(persistence) == len(children) == len(ds) and np.all(persistence >= -1e-15), "bad finite persistence")
    persistence = np.maximum(persistence, 0.0)

    N = L + len(children)
    members: list[frozenset[str] | None] = [None] * N
    parent = np.full(N, -1, dtype=np.int64)
    kids: list[tuple[int, int] | None] = [None] * N
    active_peak = np.full(N, np.nan, dtype=float)
    active_key: list[str | None] = [None] * N
    merge_level = np.full(N, np.nan, dtype=float)

    for leaf in range(L):
        ix = np.flatnonzero(labels == leaf)
        req(len(ix) > 0, f"empty leaf {leaf}")
        m = frozenset(ids[int(i)] for i in ix)
        members[leaf] = m
        peak = float(np.max(rho[ix]))
        keys = sorted(ids[int(i)] for i in ix if float(rho[int(i)]) == peak)
        req(bool(keys), "no active mode key")
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
        death = float(active_peak[loser]) - float(persistence[off])
        req(np.isfinite(death), "nonfinite merge death")
        merge_level[node] = death
        reconstructed.append([float(active_peak[loser]), death])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root count mismatch")
    req(sum(len(members[int(r)]) for r in roots if members[int(r)] is not None) == len(ids), "roots do not partition panel")
    rec = diagram_sorted(np.asarray(reconstructed, dtype=float))
    req(rec.shape == ds.shape and np.allclose(rec, ds, rtol=0.0, atol=1e-12), "diagram reconstruction mismatch")

    selected_nodes: list[int] = []
    discarded_nodes: list[int] = []

    def cut(node: int) -> None:
        m = members[node]
        req(m is not None, "missing hierarchy node")
        ch = kids[node]
        if ch is None:
            (selected_nodes if len(m) >= MIN_SUPPORT else discarded_nodes).append(node)
            return
        a, b = ch
        ma, mb = members[a], members[b]
        req(ma is not None and mb is not None, "missing child")
        sa, sb = len(ma), len(mb)
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

    for root in roots:
        cut(int(root))

    req(len(selected_nodes) == len(set(selected_nodes)) and len(discarded_nodes) == len(set(discarded_nodes)), "duplicate terminal node")
    selected_sets = [members[n] for n in selected_nodes]
    discarded_sets = [members[n] for n in discarded_nodes]
    req(all(m is not None and len(m) >= MIN_SUPPORT for m in selected_sets), "sub-support candidate selected")
    req(all(m is not None and len(m) < MIN_SUPPORT for m in discarded_sets), "reportable candidate discarded")
    terminals = selected_sets + discarded_sets
    req(all(a is not None and b is not None and a.isdisjoint(b) for i, a in enumerate(terminals) for b in terminals[i + 1 :]), "terminal overlap")
    union = frozenset().union(*(m for m in terminals if m is not None)) if terminals else frozenset()
    req(union == frozenset(ids), "selected plus noise do not partition panel")

    rows: list[dict[str, Any]] = []
    for node, m in zip(selected_nodes, selected_sets):
        req(m is not None, "missing selected membership")
        p = int(parent[node])
        outside = 0.0 if p == -1 else float(merge_level[p])
        req(np.isfinite(outside), "missing outside merge level")
        contrast = max(float(active_peak[node]) - outside, 0.0)
        req(np.isfinite(contrast), "bad modal contrast")
        tup = tuple(sorted(m))
        rows.append({
            "family_id": family_id(tup),
            "family_hash": member_hash(m),
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
        row["structural_rank"] = rank

    discarded_event_count = sum(len(m) for m in discarded_sets if m is not None)
    return rows, {
        "candidate_count": len(rows),
        "leaf_count": L,
        "internal_node_count": len(children),
        "root_count": len(roots),
        "selected_root_count": sum(bool(r["is_root"]) for r in rows),
        "discarded_subsupport_node_count": len(discarded_nodes),
        "discarded_subsupport_event_count": int(discarded_event_count),
        "covered_event_count": int(len(ids) - discarded_event_count),
        "coverage_fraction": float((len(ids) - discarded_event_count) / len(ids)) if ids else 0.0,
        "pairwise_disjoint": True,
        "selected_plus_noise_partition": True,
        "density": "min(radius_degree_2022/n2022, radius_degree_2023/n2023)",
        "zero_bottleneck_fraction": float(np.mean(rho == 0.0)),
        "positive_both_fraction": float(np.mean((d22 > 0) & (d23 > 0))),
        "rho_bottleneck_median": float(np.median(rho)),
        "rho_bottleneck_p90": float(np.quantile(rho, 0.90)),
        "median_total_radius_degree": float(np.median(total_degree)),
        "p90_total_radius_degree": float(np.quantile(total_degree, 0.90)),
        "max_selected_member_count": max((len(m) for m in selected_sets if m is not None), default=0),
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(rec - ds))) if rec.size else 0.0,
        "cut_rule": "support_pruned_terminal_rule_v1",
    }
