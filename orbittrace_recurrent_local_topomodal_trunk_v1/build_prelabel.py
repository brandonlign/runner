#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
RADIUS = 1.0
MIN_ANNUAL_SUPPORT = 4
H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)
EXPECTED_EVENTS_TOTAL = 738682
EXPECTED_EVENTS_BY_YEAR = {"2022": 315024, "2023": 423658}
EXPECTED_PARENT_PRELABEL_SHA256 = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
EXPECTED_PARENT_RESULT_SHA256 = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
EXPECTED_PARENT_COUNT = 2094
EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256 = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_PROTOCOL_BLOB = "de8d040a1f9d3b0825ce56532efd5950acefc689"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    hdr = f"blob {len(data)}\0".encode()
    return hashlib.sha1(hdr + data).hexdigest()


def membership_sha(ids: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256("|".join(sorted(str(x) for x in ids)).encode()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def physical_embedding(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([float(e["sol"]) for e in events], dtype=float))
    lon = np.radians(np.asarray([float(e["lon"]) for e in events], dtype=float))
    lat = np.radians(np.asarray([float(e["lat"]) for e in events], dtype=float))
    vg = np.asarray([float(e["vg"]) for e in events], dtype=float)
    req(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    clat = np.cos(lat)
    z = np.column_stack([
        np.cos(sol) / H_SOL,
        np.sin(sol) / H_SOL,
        clat * np.cos(lon) / H_RAD,
        clat * np.sin(lon) / H_RAD,
        np.sin(lat) / H_RAD,
        np.log(vg) / H_LOGV,
    ]).astype(float)
    req(z.shape == (len(events), 6) and np.all(np.isfinite(z)), "invalid physical embedding")
    return z


def local_trunk(parent_ids: list[str], event_by_id: dict[str, dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    ids = sorted(str(x) for x in parent_ids)
    req(len(ids) == len(set(ids)), "duplicate ID inside parent")
    events = [event_by_id[eid] for eid in ids]
    z = physical_embedding(events)
    tree = cKDTree(z)
    raw_neighbors = tree.query_ball_point(z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw_neighbors]
    req(len(neighbors) == len(ids), "radius graph row count changed")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing from radius graph at {i}")
        req(all(0 <= j < len(ids) for j in row), "radius graph index out of range")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")

    degrees = np.asarray([len(row) for row in neighbors], dtype=float)
    rho = degrees / float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), "invalid local density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    req(leaf_labels.shape == (len(ids),), "wrong ToMATo leaf label shape")
    leaf_count = int(model.n_leaves_)
    req(leaf_count >= 1, "no ToMATo leaves")
    req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, "noncontiguous ToMATo leaves")
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(leaf_count - len(children) == roots_expected, "ToMATo leaf/merge/root arithmetic changed")

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f"empty ToMATo leaf {leaf}")
        member_ix[leaf] = frozenset(int(i) for i in ix)
    req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(ids), "leaf basins do not partition parent")

    parent = np.full(node_count, -1, dtype=np.int64)
    for offset, pair in enumerate(children):
        node = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, f"invalid ToMATo children at node {node}: {a},{b}")
        req(parent[a] == -1 and parent[b] == -1, "ToMATo hierarchy node has multiple parents")
        ma, mb = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None, "ToMATo child membership missing")
        req(ma.isdisjoint(mb), "ToMATo child memberships overlap")
        member_ix[node] = frozenset(ma.union(mb))
        parent[a] = node
        parent[b] = node

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "ToMATo root/component count mismatch")
    req(sum(len(member_ix[int(r)]) for r in roots if member_ix[int(r)] is not None) == len(ids), "ToMATo roots do not partition parent")

    max_rho = float(np.max(rho))
    anchor_ix = int(np.flatnonzero(rho == max_rho)[0])
    anchor_event = ids[anchor_ix]
    node = int(leaf_labels[anchor_ix])
    chain_nodes: list[int] = []
    seen_nodes: set[int] = set()
    while True:
        req(node not in seen_nodes, "cycle in ToMATo hierarchy")
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
        req(ixset is not None, f"missing chain membership node={n}")
        members = tuple(sorted(ids[i] for i in ixset))
        if members in seen_memberships:
            continue
        seen_memberships.add(members)
        years = {str(y): 0 for y in YEARS}
        for eid in members:
            years[str(int(event_by_id[eid]["year"]))] += 1
        strict = frozenset(members) != parent_set
        recurrently_reportable = bool(strict and all(years[str(y)] >= MIN_ANNUAL_SUPPORT for y in YEARS))
        row = {
            "chain_index": int(chain_index),
            "node_id": int(n),
            "member_count": len(members),
            "membership_sha256": membership_sha(members),
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
        req(all(m == best[0] for m in best), "nonunique equal-size anchor-chain representation")
        final_ids = list(best[0])
        decision = "LOCAL_TRUNK_REPLACEMENT"
    else:
        final_ids = list(ids)
        decision = "PARENT_FALLBACK_NO_REPORTABLE_STRICT_TRUNK"

    req(set(final_ids).issubset(parent_set), "local trunk escaped parent membership")
    req(len(final_ids) <= len(ids), "local trunk expanded parent membership")
    summary = {
        "parent_member_count": len(ids),
        "radius": RADIUS,
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
        "final_membership_sha256": membership_sha(final_ids),
    }
    return final_ids, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--geometry", type=Path, required=True)
    ap.add_argument("--parent-prelabel", type=Path, required=True)
    ap.add_argument("--parent-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(a.protocol) == EXPECTED_PROTOCOL_BLOB, "frozen protocol blob changed")
    req(sha256(a.parent_prelabel) == EXPECTED_PARENT_PRELABEL_SHA256, "binding parent prelabel changed")
    req(sha256(a.parent_result) == EXPECTED_PARENT_RESULT_SHA256, "binding parent result changed")
    parent_pre = json.loads(a.parent_prelabel.read_text())
    parent_result = json.loads(a.parent_result.read_text())
    req(parent_pre["scientific_role"] == "PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1", "wrong parent prelabel role")
    req(parent_result["verdict"] == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "parent binding verdict is not PASS")
    parents = list(parent_pre["successor_candidates"])
    req(len(parents) == EXPECTED_PARENT_COUNT, f"binding parent candidate count changed: {len(parents)}")
    req(ordered_membership_sha(parents) == EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256, "binding parent order/membership changed")
    req(parent_pre["successor_ordered_membership_sha256"] == EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256, "parent serialized order hash changed")

    geometry = json.loads(a.geometry.read_text())
    req(geometry["schema"] == "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_GEOMETRY", "wrong geometry schema")
    req(geometry["scientific_role"] == "LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY", "geometry is not label-free")
    req(geometry["events_total"] == EXPECTED_EVENTS_TOTAL and geometry["events_by_year"] == EXPECTED_EVENTS_BY_YEAR, "geometry event counts changed")
    req(geometry["blind_exclusion"] == list(BLIND), "geometry firewall changed")
    req(geometry["shower_truth_exported"] is False, "geometry export contains shower truth")
    events = list(geometry["events"])
    req(len(events) == EXPECTED_EVENTS_TOTAL, "geometry event row count changed")
    event_by_id = {str(e["id"]): e for e in events}
    req(len(event_by_id) == len(events), "duplicate geometry event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived geometry export")
    recomputed_universe_sha = hashlib.sha256("\n".join(sorted(event_by_id)).encode()).hexdigest()
    req(recomputed_universe_sha == geometry["event_universe_sha256"], "geometry event-universe hash changed")

    parent_seen: set[str] = set()
    for row in parents:
        mids = [str(x) for x in row["event_ids"]]
        req(mids == sorted(mids), "binding parent membership not sorted")
        req(set(mids).issubset(event_by_id), "binding parent references event outside geometry")
        req(parent_seen.isdisjoint(mids), "binding parent slots overlap")
        parent_seen.update(mids)

    successor: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    final_seen: set[str] = set()
    changed = 0
    for rank, parent_row in enumerate(parents, 1):
        parent_ids = [str(x) for x in parent_row["event_ids"]]
        print(f"[local-trunk] rank={rank}/{len(parents)} n={len(parent_ids)}", flush=True)
        final_ids, topo = local_trunk(parent_ids, event_by_id)
        changed_here = final_ids != parent_ids
        changed += int(changed_here)
        req(set(final_ids).issubset(parent_ids), f"rank {rank} successor not parent subset")
        req(final_seen.isdisjoint(final_ids), f"rank {rank} successor overlaps earlier slot")
        final_seen.update(final_ids)
        successor.append({
            "rank": rank,
            "parent_family_id": str(parent_row["family_id"]),
            "family_id": str(parent_row["family_id"]),
            "parent_node_id": int(parent_row["node_id"]),
            "event_ids": final_ids,
            "member_count": len(final_ids),
            "representation_changed": changed_here,
        })
        diagnostics.append({
            "rank": rank,
            "parent_family_id": str(parent_row["family_id"]),
            "parent_node_id": int(parent_row["node_id"]),
            "parent_event_ids": parent_ids,
            "parent_membership_sha256": membership_sha(parent_ids),
            "topology": topo,
            "final_event_ids": final_ids,
            "final_membership_sha256": membership_sha(final_ids),
            "representation_changed": changed_here,
        })

    req(len(successor) == len(parents), "catalogue slot count changed")
    req([int(r["rank"]) for r in successor] == list(range(1, len(parents) + 1)), "catalogue rank order changed")
    req(len(final_seen) == sum(len(r["event_ids"]) for r in successor), "successor slots not event-disjoint")
    successor_sha = ordered_membership_sha(successor)

    payload = {
        "schema": "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_PRELABEL",
        "scientific_role": "PRELABEL_TARGET_EXCLUDED_FIXED_RANK_MEMBERSHIP_REPRESENTATION",
        "frozen_protocol_blob": EXPECTED_PROTOCOL_BLOB,
        "parent_binding_run_id": 31852836840,
        "parent_binding_artifact_id": 9238142199,
        "parent_binding_artifact_digest": "sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60",
        "parent_prelabel_sha256": EXPECTED_PARENT_PRELABEL_SHA256,
        "parent_result_sha256": EXPECTED_PARENT_RESULT_SHA256,
        "events_total": EXPECTED_EVENTS_TOTAL,
        "events_by_year": EXPECTED_EVENTS_BY_YEAR,
        "event_universe_sha256": geometry["event_universe_sha256"],
        "parent_candidate_count": len(parents),
        "parent_ordered_membership_sha256": EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256,
        "successor_candidate_count": len(successor),
        "successor_ordered_membership_sha256": successor_sha,
        "changed_slot_count": changed,
        "mechanism_active": bool(changed > 0),
        "parent_candidates": [
            {
                "rank": i,
                "family_id": str(r["family_id"]),
                "node_id": int(r["node_id"]),
                "event_ids": [str(x) for x in r["event_ids"]],
                "member_count": len(r["event_ids"]),
            }
            for i, r in enumerate(parents, 1)
        ],
        "successor_candidates": successor,
        "slot_diagnostics": diagnostics,
        "local_topology": {
            "embedding": "physical_topomodal_hsol5_hrad4_hlogv1p1",
            "radius": RADIUS,
            "density": "radius_neighbor_count_divided_by_parent_size",
            "tomato_graph_type": "manual",
            "tomato_density_type": "manual",
            "flat_cut": None,
            "representation_rule": "largest_recurrently_reportable_strict_anchor_chain_membership_else_parent",
            "minimum_annual_support": MIN_ANNUAL_SUPPORT,
        },
        "catalogue_slot_order_unchanged": True,
        "every_successor_subset_of_same_rank_parent": True,
        "successor_slots_pairwise_event_disjoint": True,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbital_information_access": False,
        "station_metadata_access": False,
        "uncertainty_metadata_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "changed_slot_count": changed,
        "mechanism_active": bool(changed),
        "parent_candidate_count": len(parents),
        "successor_candidate_count": len(successor),
        "parent_ordered_membership_sha256": EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256,
        "successor_ordered_membership_sha256": successor_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
