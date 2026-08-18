#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

import build_prelabel as frozen

DEGREE_BATCH = 512


class LazyRadiusNeighbors:
    """Exact frozen radius graph exposed one row at a time.

    GUDHI Tomato's manual-graph core indexes neighbors[i] during the hierarchy
    sweep. Returning the exact cKDTree radius row lazily changes only storage,
    not graph membership, density, ordering, topology, or scientific outputs.
    """

    def __init__(self, tree: cKDTree, z: np.ndarray):
        self.tree = tree
        self.z = z
        self.n = int(len(z))
        self.rows_served = 0
        self.entries_served = 0

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, i: int):
        i = int(i)
        if i < 0 or i >= self.n:
            raise IndexError(i)
        row = self.tree.query_ball_point(
            self.z[i], r=frozen.RADIUS, p=2.0, eps=0.0, return_sorted=True
        )
        row = [int(x) for x in row]
        frozen.req(i in row, f"self missing from lazy radius graph at {i}")
        frozen.req(all(0 <= j < self.n for j in row), "lazy radius graph index out of range")
        self.rows_served += 1
        self.entries_served += len(row)
        return row


def exact_degrees(tree: cKDTree, z: np.ndarray) -> np.ndarray:
    counts: list[int] = []
    for start in range(0, len(z), DEGREE_BATCH):
        stop = min(len(z), start + DEGREE_BATCH)
        c = tree.query_ball_point(
            z[start:stop], r=frozen.RADIUS, p=2.0, eps=0.0, return_length=True
        )
        counts.extend(int(x) for x in np.asarray(c).reshape(-1))
    degrees = np.asarray(counts, dtype=float)
    frozen.req(degrees.shape == (len(z),), "lazy degree row count changed")
    frozen.req(np.all(degrees >= 1), "lazy radius graph missing self degree")
    return degrees


def local_trunk_lazy(parent_ids: list[str], event_by_id: dict[str, dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    ids = sorted(str(x) for x in parent_ids)
    frozen.req(len(ids) == len(set(ids)), "duplicate ID inside parent")
    events = [event_by_id[eid] for eid in ids]
    z = frozen.physical_embedding(events)
    tree = cKDTree(z)

    # Frozen density is degree / parent size. Compute the exact same degrees
    # without retaining the billion-entry graph in memory.
    degrees = exact_degrees(tree, z)
    rho = degrees / float(len(ids))
    frozen.req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid local density")

    # cKDTree radius membership is symmetric by construction because the frozen
    # graph uses one Euclidean radius, p=2, eps=0 on the same point set. GUDHI's
    # manual hierarchy receives the exact same sorted neighbor row, but lazily.
    neighbors = LazyRadiusNeighbors(tree, z)
    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    frozen.req(neighbors.rows_served == len(ids), "GUDHI did not request exactly one lazy row per point")

    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    frozen.req(leaf_labels.shape == (len(ids),), "wrong ToMATo leaf label shape")
    leaf_count = int(model.n_leaves_)
    frozen.req(leaf_count >= 1, "no ToMATo leaves")
    frozen.req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "noncontiguous ToMATo leaves")
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    frozen.req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic changed")

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        frozen.req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
        member_ix[leaf] = frozenset(int(i) for i in ix)
    frozen.req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(ids), "leaf basins do not partition parent")

    parent = np.full(node_count, -1, dtype=np.int64)
    for offset, pair in enumerate(children):
        node = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        frozen.req(0 <= a < node and 0 <= b < node and a != b, f"invalid ToMATo children at node {node}: {a},{b}")
        frozen.req(parent[a] == -1 and parent[b] == -1, "ToMATo hierarchy node has multiple parents")
        ma, mb = member_ix[a], member_ix[b]
        frozen.req(ma is not None and mb is not None, "ToMATo child membership missing")
        frozen.req(ma.isdisjoint(mb), "ToMATo child memberships overlap")
        member_ix[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node

    roots = np.flatnonzero(parent == -1)
    frozen.req(len(roots) == roots_expected, "ToMATo root/component count mismatch")
    frozen.req(sum(len(member_ix[int(r)]) for r in roots if member_ix[int(r)] is not None) == len(ids), "ToMATo roots do not partition parent")

    max_rho = float(np.max(rho))
    anchor_ix = int(np.flatnonzero(rho == max_rho)[0])
    anchor_event = ids[anchor_ix]
    node = int(leaf_labels[anchor_ix])
    chain_nodes: list[int] = []
    seen_nodes: set[int] = set()
    while True:
        frozen.req(node not in seen_nodes, "cycle in ToMATo hierarchy")
        seen_nodes.add(node)
        chain_nodes.append(node)
        par = int(parent[node])
        if par == -1:
            break
        node = par

    parent_set = frozenset(ids)
    seen_memberships: set[tuple[str, ...]] = set()
    chain_rows: list[dict[str, Any]] = []
    reportable: list[tuple[int, tuple[str, ...]]] = []
    for chain_index, n in enumerate(chain_nodes):
        ixset = member_ix[n]
        frozen.req(ixset is not None, f"missing chain membership node={n}")
        members = tuple(sorted(ids[i] for i in ixset))
        if members in seen_memberships:
            continue
        seen_memberships.add(members)
        years = {str(y): 0 for y in frozen.YEARS}
        for eid in members:
            years[str(int(event_by_id[eid]["year"]))] += 1
        strict = frozenset(members) != parent_set
        recurrently_reportable = bool(strict and all(years[str(y)] >= frozen.MIN_ANNUAL_SUPPORT for y in frozen.YEARS))
        row = {
            "chain_index": int(chain_index),
            "node_id": int(n),
            "member_count": len(members),
            "membership_sha256": frozen.membership_sha(members),
            "events_by_year": years,
            "strict_subset_of_parent": strict,
            "recurrently_reportable": recurrently_reportable,
            "event_ids": list(members),
        }
        chain_rows.append(row)
        if recurrently_reportable:
            reportable.append((len(members), members))

    if reportable:
        best_size = max(size for size, _members in reportable)
        best = [members for size, members in reportable if size == best_size]
        frozen.req(all(m == best[0] for m in best), "nonunique equal-size anchor-chain representation")
        final_ids = list(best[0])
        decision = "LOCAL_TRUNK_REPLACEMENT"
    else:
        final_ids = list(ids)
        decision = "PARENT_FALLBACK_NO_REPORTABLE_STRICT_TRUNK"

    frozen.req(set(final_ids).issubset(parent_set), "local trunk escaped parent membership")
    frozen.req(len(final_ids) <= len(ids), "local trunk expanded parent membership")
    summary = {
        "parent_member_count": len(ids),
        "radius": frozen.RADIUS,
        "radius_degree_median": float(np.median(degrees)),
        "radius_degree_p90": float(np.quantile(degrees, 0.90)),
        "radius_degree_max": int(np.max(degrees)),
        "leaf_count": leaf_count,
        "internal_node_count": len(children),
        "root_count": len(roots),
        "anchor_event_id": anchor_event,
        "anchor_density": max_rho,
        "anchor_leaf_node": int(leaf_labels[anchor_ix]),
        "anchor_root_node": int(chain_nodes[-1]),
        "anchor_chain_unique_membership_count": len(chain_rows),
        "anchor_chain": chain_rows,
        "decision": decision,
        "final_member_count": len(final_ids),
        "removed_member_count": len(ids) - len(final_ids),
        "final_membership_sha256": frozen.membership_sha(final_ids),
    }
    return final_ids, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", type=Path, required=True)
    ap.add_argument("--parent-prelabel", type=Path, required=True)
    ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--compare-original", action="store_true")
    a = ap.parse_args()
    g = json.loads(a.geometry.read_text())
    p = json.loads(a.parent_prelabel.read_text())
    frozen.req(g["events_total"] == frozen.EXPECTED_EVENTS_TOTAL, "geometry count changed")
    frozen.req(p["successor_candidate_count"] == frozen.EXPECTED_PARENT_COUNT, "parent count changed")
    frozen.req(1 <= a.rank <= frozen.EXPECTED_PARENT_COUNT, "rank out of range")
    event_by_id = {str(e["id"]): e for e in g["events"]}
    row = p["successor_candidates"][a.rank - 1]
    parent_ids = [str(x) for x in row["event_ids"]]
    final_ids, summary = local_trunk_lazy(parent_ids, event_by_id)
    out = {"rank": a.rank, "parent_n": len(parent_ids), "final_ids": final_ids, "summary": summary}
    if a.compare_original:
        orig_ids, orig_summary = frozen.local_trunk(parent_ids, event_by_id)
        frozen.req(orig_ids == final_ids, "lazy final membership differs from frozen implementation")
        frozen.req(orig_summary == summary, "lazy diagnostics differ from frozen implementation")
        out["exact_original_equivalence"] = True
    print(json.dumps(out, separators=(",", ":"), sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
