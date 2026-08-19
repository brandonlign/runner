#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import networkx as nx
import numpy as np

PRE_GZ_SHA = "b1beb3dac03579b2ca2a0f85a2e65213e3a4826dfe0d8f038856f6b227319765"
PRE_INNER_SHA = "75dec41919072681a423d3c37d4565ca5ee19dccf86900b3b39ef5d30153ca0b"
OLD_SCAN_BLOB = "3def559978444e9bde1eab9cf9c3d47b8cbb2944"
REPLAY_BLOB = "de1e28eeb69d199502c1158bc56f32695bb64b2c"
STRUCTURAL_BLOB = "c1efa8da34dea140726a4c2fe4943eb29a304538"
SUPPORT_BLOB = "3712a36033088f1bd486cefdc8dc474c194fc85c"
ANNUAL_BLOB = "d8486a55661bd71e92932b290e0b7550688f3b46"
BWM_BLOB = "703081742f004f8817da050fdf22cf9ecde44dfe"
CMR_BLOB = "d7d0eacfb5fc3f86794fc29898e163d1343d0612"
EXPECTED_EVENT_COUNT = 549636
EXPECTED_CANDIDATE_COUNT = 8884
PARENT_RANK = 82
EXPECTED_PARENT_SIZE = 1708
EXPECTED_PARENT_HASH = "936d785f4c50b5dae659"
EXPECTED_PARENT_M2D = 3.6102249980736316e-10
EXPECTED_INTERNAL_EDGES = 28994
EXPECTED_BOUNDARY_EDGES = 69
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_bytes(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def git_blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def membership_hash(ids: frozenset[str] | set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()


class LocalDSU:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))
        self.sz = [1] * n
        self.bad = [False] * n

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.sz[a] < self.sz[b]:
            a, b = b, a
        self.p[b] = a
        self.sz[a] += self.sz[b]
        self.bad[a] = self.bad[a] or self.bad[b]

    def mark_bad(self, x: int) -> None:
        self.bad[self.find(x)] = True


def edge_transport(
    ids: list[str],
    neighbors: list[list[int]],
    d22: np.ndarray,
    d23: np.ndarray,
    parent_ids: frozenset[str],
) -> tuple[list[int], list[tuple[int, int, int, int]], list[tuple[int, int, int]], dict[str, int]]:
    gindex = {eid: i for i, eid in enumerate(ids)}
    req(parent_ids.issubset(gindex), "parent ID missing from reconstructed universe")
    inds = [gindex[eid] for eid in sorted(parent_ids)]
    local = {g: u for u, g in enumerate(inds)}
    inside: list[tuple[int, int, int, int]] = []
    cross: list[tuple[int, int, int]] = []
    for g in inds:
        u = local[g]
        for j in neighbors[g]:
            if j == g:
                continue
            v = local.get(int(j))
            if v is not None:
                if int(j) > g:
                    inside.append((u, v, min(int(d22[g]), int(d22[j])), min(int(d23[g]), int(d23[j]))))
            else:
                aa = min(int(d22[g]), int(d22[j]))
                bb = min(int(d23[g]), int(d23[j]))
                if aa > 0 and bb > 0:
                    cross.append((u, aa, bb))
    return inds, inside, cross, {"parent_vertices": len(inds), "internal_edges": len(inside), "positive_boundary_edges": len(cross)}


def contained_witnesses(
    ids: list[str],
    d22: np.ndarray,
    d23: np.ndarray,
    inds: list[int],
    inside: list[tuple[int, int, int, int]],
    cross: list[tuple[int, int, int]],
    n22: int,
    n23: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    n = len(inds)
    req(n >= MIN_SUPPORT and n22 > 0 and n23 > 0, "bad candidate/universe size")
    local_ids = [ids[g] for g in inds]
    ld22 = [int(d22[g]) for g in inds]
    ld23 = [int(d23[g]) for g in inds]

    rel22 = sorted({x for x in ld22 if x > 0} | {aa for _, _, aa, _ in inside if aa > 0} | {aa for _, aa, _ in cross if aa > 0}, reverse=True)
    rel23 = sorted({x for x in ld23 if x > 0} | {bb for _, _, _, bb in inside if bb > 0} | {bb for _, _, bb in cross if bb > 0}, reverse=True)
    req(rel22 and rel23, "no positive candidate thresholds")
    w22 = {v: (v - (rel22[i + 1] if i + 1 < len(rel22) else 0)) / n22 for i, v in enumerate(rel22)}
    w23 = {v: (v - (rel23[i + 1] if i + 1 < len(rel23) else 0)) / n23 for i, v in enumerate(rel23)}
    req(all(x > 0 for x in w22.values()) and all(x > 0 for x in w23.values()), "nonpositive compressed cell width")

    by_vertex22: dict[int, list[int]] = defaultdict(list)
    for u, a in enumerate(ld22):
        if a > 0:
            by_vertex22[a].append(u)
    by_inside22: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for u, v, aa, bb in inside:
        if aa > 0 and bb > 0:
            by_inside22[aa].append((u, v, bb))
    by_cross22: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, aa, bb in cross:
        by_cross22[aa].append((u, bb))

    area: dict[tuple[str, ...], float] = defaultdict(float)
    compressed_cells: dict[tuple[str, ...], int] = defaultdict(int)
    reportable_instances = 0
    state_cells = 0
    for k23 in rel23:
        dsu = LocalDSU(n)
        active = [False] * n
        active_list: list[int] = []
        for k22 in rel22:
            for u in by_vertex22.get(k22, []):
                if ld23[u] >= k23:
                    active[u] = True
                    active_list.append(u)
            for u, v, bb in by_inside22.get(k22, []):
                if bb >= k23 and active[u] and active[v]:
                    dsu.union(u, v)
            for u, bb in by_cross22.get(k22, []):
                if bb >= k23 and active[u]:
                    dsu.mark_bad(u)
            state_cells += 1
            if len(active_list) < MIN_SUPPORT:
                continue
            groups: dict[int, list[str]] = defaultdict(list)
            for u in active_list:
                root = dsu.find(u)
                if not dsu.bad[root]:
                    groups[root].append(local_ids[u])
            cell_area = w22[k22] * w23[k23]
            for mem in groups.values():
                if len(mem) < MIN_SUPPORT:
                    continue
                key = tuple(sorted(mem))
                area[key] += cell_area
                compressed_cells[key] += 1
                reportable_instances += 1

    rows: list[dict[str, Any]] = []
    for mem, a in area.items():
        req(a > 0 and math.isfinite(a), "bad contained persistence area")
        rows.append({
            "family_hash": membership_hash(frozenset(mem)),
            "member_count": len(mem),
            "persistence_area": float(a),
            "compressed_state_cell_count": int(compressed_cells[mem]),
            "event_ids": list(mem),
        })
    rows.sort(key=lambda r: (-float(r["persistence_area"]), -int(r["member_count"]), str(r["family_hash"])))
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows, {
        "relevant_rho22_level_count": len(rel22),
        "relevant_rho23_level_count": len(rel23),
        "compressed_state_cell_count": state_cells,
        "reportable_component_instances": reportable_instances,
        "contained_witness_count": len(rows),
    }


def rows_map(rows: list[dict[str, Any]]) -> dict[tuple[str, ...], float]:
    return {tuple(sorted(map(str, r["event_ids"]))): float(r["persistence_area"]) for r in rows}


def synthetic_equivalence(old: Any, replay: Any, structural: Any, annual: Any) -> dict[str, Any]:
    events = old.synthetic_events()
    parents, _, _, _, _, _ = replay.support_pruned_cut_linear(old, structural, events, keep_neighbors=False)
    _sets, global_rows, _summary = annual.bifiltration_candidates(structural, events)
    ids, neighbors, d22, d23, gs = annual.build_fixed_graph(structural, events)
    tests = list(parents[: min(12, len(parents))])
    req(tests, "no synthetic parent tests")
    max_abs = 0.0
    total_expected = 0
    total_actual = 0
    for p in tests:
        pset = frozenset(map(str, p["event_ids"]))
        inds, inside, cross, _ = edge_transport(ids, neighbors, d22, d23, pset)
        got, _ = contained_witnesses(ids, d22, d23, inds, inside, cross, int(gs["events_2022"]), int(gs["events_2023"]))
        expected = [r for r in global_rows if frozenset(map(str, r["event_ids"])).issubset(pset)]
        a, b = rows_map(expected), rows_map(got)
        req(set(a) == set(b), "synthetic contained-witness memberships differ")
        total_expected += len(a); total_actual += len(b)
        for key in a:
            err = abs(a[key] - b[key]); max_abs = max(max_abs, err)
            req(math.isclose(a[key], b[key], rel_tol=1e-12, abs_tol=1e-15), f"synthetic persistence area differs {err}")
    return {
        "verdict": "PASS_EXACT_CONTAINED_BIFILTRATION_EQUIVALENCE",
        "tested_parent_count": len(tests),
        "expected_witness_instances": total_expected,
        "actual_witness_instances": total_actual,
        "max_abs_persistence_area_error": max_abs,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("sealed-pretruth", "old-scan", "support-replay", "blind-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "structural-source", "support-source", "annual-source", "bwm-source", "cmr-source", "output"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    identities = {
        "old_scan_git_blob": (a.old_scan, OLD_SCAN_BLOB),
        "support_replay_git_blob": (a.support_replay, REPLAY_BLOB),
        "structural_source_git_blob": (a.structural_source, STRUCTURAL_BLOB),
        "support_source_git_blob": (a.support_source, SUPPORT_BLOB),
        "annual_source_git_blob": (a.annual_source, ANNUAL_BLOB),
        "bwm_source_git_blob": (a.bwm_source, BWM_BLOB),
        "cmr_source_git_blob": (a.cmr_source, CMR_BLOB),
    }
    for label, (path, expected) in identities.items():
        req(git_blob(path) == expected, f"{label} changed")

    gz = a.sealed_pretruth.read_bytes()
    req(sha256_bytes(gz) == PRE_GZ_SHA, "sealed replay gzip changed")
    raw = gzip.decompress(gz)
    req(sha256_bytes(raw) == PRE_INNER_SHA, "sealed replay inner changed")
    sealed = json.loads(raw)
    req(sealed.get("candidate_count") == EXPECTED_CANDIDATE_COUNT == len(sealed.get("candidates", [])), "sealed candidate count changed")
    req(sealed.get("orbittrace_target_information_access") is False and sealed.get("orbittrace_canonical_members_access") is False and sealed.get("prior_orbittrace_reveal_access") is False, "upstream blind replay firewall changed")
    parent = dict(sealed["candidates"][PARENT_RANK - 1])
    req(int(parent["rank"]) == PARENT_RANK and int(parent["member_count"]) == EXPECTED_PARENT_SIZE, "frozen parent rank/size changed")
    req(str(parent["family_hash"]) == EXPECTED_PARENT_HASH, "frozen parent family changed")
    req(math.isclose(float(parent["internal_2d_mass"]), EXPECTED_PARENT_M2D, rel_tol=0.0, abs_tol=1e-24), "frozen parent M2D changed")
    parent_set = frozenset(map(str, parent["event_ids"]))

    old = load(a.old_scan, "nca_frozen_1378")
    replay = load(a.support_replay, "nca_support_replay")
    structural = load(a.structural_source, "nca_structural")
    support = load(a.support_source, "nca_support")
    annual = load(a.annual_source, "nca_annual")
    bwm = load(a.bwm_source, "nca_bwm")
    cmr = load(a.cmr_source, "nca_cmr")
    req(nx.__version__ == "3.6.1", f"NetworkX version changed {nx.__version__}")

    support_audit = replay.equivalence_audit(old, structural, support)
    req(support_audit.get("verdict") == "PASS_EXACT_SYNTHETIC_SUPPORT_PRUNED_CUT_EQUIVALENCE", "support replay equivalence failed")
    bif_audit = synthetic_equivalence(old, replay, structural, annual)

    blind_path = a.output.parent / "decoded_blind_source.py"
    old.decode_blind_source(a.blind_source_parts, blind_path)
    blind = old.load_module(blind_path, "nca_blind_loader")
    blind.YEARS = old.YEARS
    blind.MONTH_KEYS = old.MONTH_KEYS
    source_args = SimpleNamespace(candidate_payload=a.candidate_payload, baseline_payload=a.baseline_payload, scorer_parts=a.scorer_parts)
    _candidate, base, _scorer = blind.load_sources(source_args)
    by_year, sources = blind.parse_catalogue(base)
    req(sorted(by_year) == list(old.YEARS), "wrong live years")
    req([s["key"] for s in sources] == list(old.MONTH_KEYS), "source sequence changed")
    events: list[dict[str, Any]] = []
    annual_counts: dict[str, int] = {}
    for year in old.YEARS:
        rows = list(by_year[year]); annual_counts[str(year)] = len(rows)
        for r in rows:
            events.append({"id": str(r["id"]), "year": int(year), "sol": float(r["sol"]), "lon": float(r["sun_lon"]), "lat": float(r["ecl_lat"]), "vg": float(r["vg"])})
    req(len(events) == EXPECTED_EVENT_COUNT and len({e["id"] for e in events}) == len(events), "live universe changed")

    candidates, support_summary, neighbors, leaf_labels, leaf_owner, _degrees = replay.support_pruned_cut_linear(old, structural, events, keep_neighbors=True)
    req(neighbors is not None, "live radius graph missing")
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    d22, d23 = old.annual_degrees(neighbors, years)
    recon = [r for r in candidates if frozenset(map(str, r["event_ids"])) == parent_set]
    req(len(recon) == 1 and str(recon[0]["family_hash"]) == EXPECTED_PARENT_HASH, "exact frozen parent not reconstructed")

    inds, inside, cross, transport = edge_transport(ids, neighbors, d22, d23, parent_set)
    req(transport == {"parent_vertices": EXPECTED_PARENT_SIZE, "internal_edges": EXPECTED_INTERNAL_EDGES, "positive_boundary_edges": EXPECTED_BOUNDARY_EDGES}, f"parent edge transport changed: {transport}")
    bif_rows, bif_summary = contained_witnesses(ids, d22, d23, inds, inside, cross, annual_counts["2022"], annual_counts["2023"])
    req(bif_rows, "no contained witnesses for frozen parent")

    parent_for_bwm = {"event_ids": sorted(parent_set), "member_count": len(parent_set), "family_hash": EXPECTED_PARENT_HASH}
    communities, bwm_summary = bwm.witness_partition(parent_for_bwm, bif_rows)
    seed_rows: list[dict[str, Any]] = []
    for community in communities:
        score, count, raw_area = bwm.exact_m2d(community, bif_rows)
        seed_rows.append({
            "family_hash": bwm.member_hash(community), "event_ids": sorted(community), "member_count": len(community),
            "internal_2d_mass": score, "internal_bif_component_count": count, "internal_bif_raw_area_sum": raw_area,
            "bwm_parent_family_hash": EXPECTED_PARENT_HASH,
        })
    seed_rows.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))

    contained = [(frozenset(map(str, r["event_ids"])), float(r["persistence_area"])) for r in bif_rows]
    grown_rows: list[dict[str, Any]] = []
    for seed in seed_rows:
        core = frozenset(map(str, seed["event_ids"]))
        if core == parent_set:
            grown, gs = core, {"seed_member_count": len(core), "grown_member_count": len(core), "added_member_count": 0, "positive_degree_parent_members": len(set().union(*(set(w) for w, _ in contained))) if contained else 0, "witness_degree_mass": None}
        else:
            grown, gs = cmr.regrow_core(core, parent_set, contained)
        score, count, raw_area = cmr.exact_m2d(grown, bif_rows)
        grown_rows.append({
            "family_hash": cmr.member_hash(grown), "event_ids": sorted(grown), "member_count": len(grown),
            "internal_2d_mass": score, "internal_bif_component_count": count, "internal_bif_raw_area_sum": raw_area,
            "cmr_seed_family_hash": str(seed["family_hash"]), "cmr_seed_member_count": len(core),
            "cmr_parent_family_hash": EXPECTED_PARENT_HASH, "cmr_parent_member_count": len(parent_set),
            "cmr_added_member_count": len(grown) - len(core), "cmr_one_shot": True, "cmr_strict_majority": True,
            "growth_summary": gs,
        })
    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in grown_rows:
        key = tuple(row["event_ids"])
        oldrow = unique.get(key)
        if oldrow is None or (float(row["internal_2d_mass"]), str(row["cmr_seed_family_hash"])) > (float(oldrow["internal_2d_mass"]), str(oldrow["cmr_seed_family_hash"])):
            unique[key] = row
    branches = list(unique.values())
    branches.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
    for i, row in enumerate(branches, 1):
        row["branch_rank_within_parent"] = i
    req(branches and all(frozenset(map(str, r["event_ids"])).issubset(parent_set) for r in branches), "invalid NCA branches")

    out = {
        "schema": "ORBITTRACE_NCA_ORBITTRACE_CHARACTERIZATION_V1_PRETRUTH",
        "scientific_role": "POST_REVEAL_PARENT_FIXED_CANONICAL_IDS_UNOPENED_NCA_CHARACTERIZATION",
        "upstream_replay_gzip_sha256": PRE_GZ_SHA,
        "upstream_replay_inner_sha256": PRE_INNER_SHA,
        "parent_selection": "already_published_rank_82_from_exact_sealed_support_pruned_replay",
        "parent": parent,
        "annual_event_counts": annual_counts,
        "event_count": len(events),
        "support_summary": support_summary,
        "edge_transport": transport,
        "support_equivalence": support_audit,
        "contained_bifiltration_equivalence": bif_audit,
        "contained_bifiltration_summary": bif_summary,
        "contained_bifiltration_witnesses": bif_rows,
        "bwm_summary": bwm_summary,
        "bwm_seeds": seed_rows,
        "nca_branches": branches,
        "primary_branch_family_hash": str(branches[0]["family_hash"]),
        "primary_branch_member_count": int(branches[0]["member_count"]),
        "configuration": {
            "parent_changed": False,
            "full_universe_boundary_semantics": True,
            "bwm_resolution": 1.0,
            "cmr_one_shot": True,
            "cmr_strict_majority": True,
            "branch_order": ["internal_2d_mass_desc", "membership_hash_asc"],
            "new_tuned_parameters": [],
        },
        "prior_parent_reveal_used": True,
        "canonical_target_ids_accessed": False,
        "target_overlap_used_for_construction": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "Post-reveal characterization of an unchanged already-discovered parent. Canonical target IDs are unopened in this artifact. NCA branches are frozen before reveal and cannot replace the flagship parent or repair failed ECT/EMCU benchmark gates.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "parent": {"rank": parent["rank"], "member_count": parent["member_count"], "family_hash": parent["family_hash"]},
        "edge_transport": transport,
        "witness_count": len(bif_rows),
        "bwm_seed_count": len(seed_rows),
        "nca_branch_count": len(branches),
        "primary_branch_member_count": len(branches[0]["event_ids"]),
        "equivalence": bif_audit,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
