#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
DENOMINATORS = (64, 128, 1024)
BUCKETS = (0, 1, 2, 3)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARETO_PRELABEL_SHA256 = "5752ef8b36a5d317455e649723c26692fe2636262dc6d74befbe2ffb95945310"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_set(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def canonical_memberships(rows: Iterable[dict[str, Any]]) -> list[str]:
    return sorted(hashlib.sha256("|".join(sorted(member_set(r))).encode()).hexdigest() for r in rows)


def universe_hash(ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(str(x) for x in ids)).encode()).hexdigest()


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + eid).encode()).digest()[:8], "big")


def disjoint(families: list[frozenset[str]]) -> bool:
    seen: set[str] = set()
    for fam in families:
        if seen.intersection(fam):
            return False
        seen.update(fam)
    return True


def make_dag_atoms(
    topo_rows: list[dict[str, Any]], recurrent_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    topo = [member_set(r) for r in topo_rows]
    recurrent = [member_set(r) for r in recurrent_rows]
    req(disjoint(topo), "TopoModal cut is not internally disjoint")
    req(disjoint(recurrent), "recurrent-EOM catalogue is not internally disjoint")

    recurrent_owner: dict[str, int] = {}
    for j, fam in enumerate(recurrent):
        for eid in fam:
            req(eid not in recurrent_owner, "recurrent ownership duplicate")
            recurrent_owner[eid] = j

    edge_members: dict[tuple[int, int], set[str]] = {}
    for i, fam in enumerate(topo):
        for eid in fam:
            j = recurrent_owner.get(eid)
            if j is not None:
                edge_members.setdefault((i, j), set()).add(eid)

    tdeg = [0] * len(topo)
    rdeg = [0] * len(recurrent)
    adjacency: dict[str, set[str]] = {
        **{f"T:{i}": set() for i in range(len(topo))},
        **{f"R:{j}": set() for j in range(len(recurrent))},
    }
    for i, j in sorted(edge_members):
        tdeg[i] += 1
        rdeg[j] += 1
        a, b = f"T:{i}", f"R:{j}"
        adjacency[a].add(b)
        adjacency[b].add(a)

    component_of: dict[str, int] = {}
    components: list[list[str]] = []
    for start in sorted(adjacency):
        if start in component_of:
            continue
        cid = len(components)
        stack = [start]
        nodes: list[str] = []
        component_of[start] = cid
        while stack:
            node = stack.pop()
            nodes.append(node)
            for nxt in sorted(adjacency[node], reverse=True):
                if nxt not in component_of:
                    component_of[nxt] = cid
                    stack.append(nxt)
        components.append(sorted(nodes))

    atoms: list[dict[str, Any]] = []
    atom_sets: list[frozenset[str]] = []
    for i, j in sorted(edge_members):
        aset = frozenset(edge_members[(i, j)])
        req(bool(aset), "empty DAG edge atom")
        atom_sets.append(aset)
        members = sorted(aset)
        atoms.append(
            {
                "atom_hash": hashlib.sha256("|".join(members).encode()).hexdigest(),
                "event_ids": members,
                "member_count": len(members),
                "topomodal_index": i,
                "recurrent_index": j,
                "topomodal_family_hash": str(topo_rows[i].get("family_hash", topo_rows[i].get("family_id", i))),
                "recurrent_family_hash": str(recurrent_rows[j].get("family_hash", recurrent_rows[j].get("family_id", j))),
                "topomodal_degree": tdeg[i],
                "recurrent_degree": rdeg[j],
                "component_id": component_of[f"T:{i}"],
            }
        )

    req(disjoint(atom_sets), "common-refinement atoms overlap")
    atom_union = frozenset().union(*atom_sets) if atom_sets else frozenset()
    topo_union = frozenset().union(*topo) if topo else frozenset()
    recurrent_union = frozenset().union(*recurrent) if recurrent else frozenset()
    joint = topo_union.intersection(recurrent_union)
    req(atom_union == joint, "atoms do not exactly cover joint parent support")

    edge_components = {component_of[f"T:{i}"] for i, j in edge_members}
    audit = {
        "topomodal_candidate_count": len(topo),
        "recurrent_candidate_count": len(recurrent),
        "atom_count": len(atoms),
        "edge_count": len(edge_members),
        "topomodal_multi_parent_count": sum(d > 1 for d in tdeg),
        "topomodal_multi_parent_fraction": float(sum(d > 1 for d in tdeg) / len(tdeg)) if tdeg else 0.0,
        "recurrent_multi_child_count": sum(d > 1 for d in rdeg),
        "recurrent_multi_child_fraction": float(sum(d > 1 for d in rdeg) / len(rdeg)) if rdeg else 0.0,
        "topomodal_isolated_count": sum(d == 0 for d in tdeg),
        "recurrent_isolated_count": sum(d == 0 for d in rdeg),
        "bipartite_component_count_including_isolates": len(components),
        "edge_component_count": len(edge_components),
        "joint_covered_event_count": len(joint),
        "topomodal_covered_event_count": len(topo_union),
        "recurrent_covered_event_count": len(recurrent_union),
        "atom_union_equals_joint_support": True,
        "atoms_pairwise_disjoint": True,
    }
    return atoms, audit


def project(families: list[frozenset[str]], universe: frozenset[str]) -> list[frozenset[str]]:
    out: list[frozenset[str]] = []
    for fam in families:
        p = fam.intersection(universe)
        if p:
            out.append(frozenset(p))
    req(disjoint(out), "projected family is not disjoint")
    return out


def directional_mean_best_jaccard(
    source: list[frozenset[str]], target: list[frozenset[str]]
) -> float:
    req(bool(source), "empty source family in stability metric")
    denom = sum(len(x) for x in source)
    req(denom > 0, "zero stability denominator")
    if not target:
        return 0.0
    total = 0.0
    for a in source:
        best = 0.0
        for b in target:
            inter = len(a.intersection(b))
            if inter == 0:
                continue
            union = len(a) + len(b) - inter
            j = inter / union
            if j > best:
                best = j
        total += len(a) * best
    return float(total / denom)


def symmetric_stability(
    dense: list[frozenset[str]], sparse: list[frozenset[str]], sparse_universe: frozenset[str]
) -> dict[str, float]:
    dense_projected = project(dense, sparse_universe)
    sparse_projected = project(sparse, sparse_universe)
    req(bool(dense_projected) and bool(sparse_projected), "empty projected representation")
    d2s = directional_mean_best_jaccard(dense_projected, sparse_projected)
    s2d = directional_mean_best_jaccard(sparse_projected, dense_projected)
    return {
        "dense_to_sparse": d2s,
        "sparse_to_dense": s2d,
        "symmetric": float((d2s + s2d) / 2.0),
        "dense_projected_family_count": len(dense_projected),
        "sparse_family_count": len(sparse_projected),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "support-cut-generator",
        "structural-runner",
        "parent-runner",
        "pareto-prelabel",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256_file(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256_file(a.v8_result_json) == V8_RESULT_SHA256, "v8 result changed")
    req(sha256_file(a.pareto_prelabel) == PARETO_PRELABEL_SHA256, "sealed Pareto prelabel changed")

    # The frozen support-cut module supplies the exact reconstruction functions already
    # audited in the predecessor structural work; this diagnostic changes only the
    # cross-hierarchy representation and the zero-label stability measurement.
    import importlib.util

    def load_module(path: Path, name: str) -> Any:
        spec = importlib.util.spec_from_file_location(name, path)
        req(spec is not None and spec.loader is not None, f"cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    cut = load_module(a.support_cut_generator, "src_support_cut")
    structural = load_module(a.structural_runner, "src_structural")
    parent = load_module(a.parent_runner, "src_parent")
    q = load_module(a.quality_source, "src_gmn")

    req(tuple(cut.BLIND) == BLIND and str(cut.SALT) == SALT and int(cut.MIN_SUPPORT) == 4, "support-cut constants changed")
    req(tuple(structural.BLIND) == BLIND and float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "TopoModal constants changed")
    req(tuple(parent.BLIND) == BLIND and int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "recurrent constants changed")

    sealed = json.loads(a.pareto_prelabel.read_text())
    sealed_subsets = {(int(x["denominator"]), int(x["bucket"])): x for x in sealed["subsets"]}
    req(set(sealed_subsets) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "sealed sparse panel set changed")
    req(not bool(sealed.get("shower_truth_used", False)), "sealed Pareto prelabel unexpectedly used truth")

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-crosshierarchy-refinement-dag-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "support firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(a)
    scan, _calibration, hidden_unused, sources = support.parse_catalogue(baseline)
    del hidden_unused
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source set changed")

    events: list[dict[str, Any]] = []
    for y in YEARS:
        events.extend(parent.normalize_event(r, y) for r in list(scan[y]))
    req(len(events) == 738682 and len({str(e["id"]) for e in events}) == 738682, "event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived")

    xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    panel_objects: dict[tuple[int, int], dict[str, Any]] = {}
    panel_records: list[dict[str, Any]] = []
    sparse_rebind_all = True

    for d in DENOMINATORS:
        for b in BUCKETS:
            ix = np.flatnonzero((hashes % np.uint64(d)) == np.uint64(b))
            sub = [events[int(i)] for i in ix]
            x = np.asarray(xfull[ix], dtype=float)
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            print(f"[crosshierarchy] d={d} b={b} n={len(ids)}", flush=True)

            topo_rows, topo_summary = cut.support_resolved_cut(structural, sub)
            recurrent_rows, recurrent_summary = cut.recurrent_ranked(parent, x, yrs, ids)
            topo_sets = [member_set(r) for r in topo_rows]
            recurrent_sets = [member_set(r) for r in recurrent_rows]
            req(disjoint(topo_sets) and disjoint(recurrent_sets), f"parent overlap d={d} b={b}")

            sealed_rebind = None
            if d in (128, 1024):
                old = sealed_subsets[(d, b)]
                sealed_topo = list(old["source_overlap_consensus_candidates"])
                sealed_recurrent = list(old["recurrent_candidates"])
                same_topo = canonical_memberships(topo_rows) == canonical_memberships(sealed_topo)
                same_recurrent = canonical_memberships(recurrent_rows) == canonical_memberships(sealed_recurrent)
                same_count = int(old["event_count"]) == len(ids)
                old_universe = set(str(z) for y in YEARS for z in old["annual_event_ids"][str(y)])
                same_universe = old_universe == set(ids)
                sealed_rebind = {
                    "topomodal_memberships_exact": same_topo,
                    "recurrent_memberships_exact": same_recurrent,
                    "event_count_exact": same_count,
                    "event_universe_exact": same_universe,
                }
                ok = all(sealed_rebind.values())
                sparse_rebind_all = sparse_rebind_all and ok
                req(ok, f"sealed sparse membership rebind failed d={d} b={b}: {sealed_rebind}")

            atoms, dag_audit = make_dag_atoms(topo_rows, recurrent_rows)
            atom_sets = [member_set(r) for r in atoms]
            panel_objects[(d, b)] = {
                "event_ids": frozenset(ids),
                "topomodal": topo_sets,
                "recurrent": recurrent_sets,
                "atoms": atom_sets,
            }
            panel_records.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "event_count": len(ids),
                    "event_universe_sha256": universe_hash(ids),
                    "annual_event_count": {str(y): int(np.count_nonzero(yrs == y)) for y in YEARS},
                    "topomodal_summary": topo_summary,
                    "recurrent_summary": recurrent_summary,
                    "sealed_sparse_rebind": sealed_rebind,
                    "dag_audit": dag_audit,
                    "topomodal_candidates": topo_rows,
                    "recurrent_candidates": recurrent_rows,
                    "atoms": atoms,
                }
            )

    transitions: list[dict[str, Any]] = []
    for b in BUCKETS:
        for dense_d, sparse_d in ((64, 128), (128, 1024)):
            dense = panel_objects[(dense_d, b)]
            sparse = panel_objects[(sparse_d, b)]
            sparse_universe = sparse["event_ids"]
            req(sparse_universe.issubset(dense["event_ids"]), f"nested universe failed {dense_d}->{sparse_d} b={b}")
            scores = {
                name: symmetric_stability(dense[name], sparse[name], sparse_universe)
                for name in ("recurrent", "topomodal", "atoms")
            }
            transitions.append(
                {
                    "bucket": b,
                    "dense_denominator": dense_d,
                    "sparse_denominator": sparse_d,
                    "sparse_event_count": len(sparse_universe),
                    "scores": scores,
                    "atom_strictly_beats_both": bool(
                        scores["atoms"]["symmetric"] > scores["recurrent"]["symmetric"]
                        and scores["atoms"]["symmetric"] > scores["topomodal"]["symmetric"]
                    ),
                }
            )

    vals = {
        name: [float(t["scores"][name]["symmetric"]) for t in transitions]
        for name in ("recurrent", "topomodal", "atoms")
    }
    means = {name: float(np.mean(v)) for name, v in vals.items()}
    medians = {name: float(median(v)) for name, v in vals.items()}
    strict_both = sum(bool(t["atom_strictly_beats_both"]) for t in transitions)
    dense_multi_parent = any(
        int(r["dag_audit"]["topomodal_multi_parent_count"]) > 0
        for r in panel_records
        if int(r["denominator"]) == 64
    )

    gates = {
        "exact_12_panel_universes_and_firewall": len(panel_records) == 12,
        "sealed_d128_d1024_parent_memberships_exact": bool(sparse_rebind_all),
        "atoms_valid_disjoint_exact_joint_support": all(
            bool(r["dag_audit"]["atoms_pairwise_disjoint"])
            and bool(r["dag_audit"]["atom_union_equals_joint_support"])
            for r in panel_records
        ),
        "d64_multi_parent_topology_active": bool(dense_multi_parent),
        "pooled_mean_atoms_gt_recurrent": means["atoms"] > means["recurrent"],
        "pooled_mean_atoms_gt_topomodal": means["atoms"] > means["topomodal"],
        "median_atoms_gt_recurrent": medians["atoms"] > medians["recurrent"],
        "median_atoms_gt_topomodal": medians["atoms"] > medians["topomodal"],
        "atoms_strictly_beat_both_at_least_5_of_8": strict_both >= 5,
    }
    verdict = (
        "SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1"
        if all(gates.values())
        else "REFUTES_CROSSHIERARCHY_REFINEMENT_DAG_V1"
    )

    prelabel = {
        "schema": "ORBITTRACE_CROSSHIERARCHY_REFINEMENT_DAG_V1_PRELABEL",
        "scientific_role": "ZERO_LABEL_CROSS_HIERARCHY_COMMON_REFINEMENT",
        "configuration": {
            "salt": SALT,
            "denominators": list(DENOMINATORS),
            "buckets": list(BUCKETS),
            "edge_rule": "nonempty_exact_event_intersection",
            "atom_rule": "exact_topomodal_intersection_recurrent",
            "overlap_threshold": None,
            "atom_size_threshold": None,
            "ranking": None,
        },
        "panels": panel_records,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    prelabel_path = a.output / "CROSSHIERARCHY_REFINEMENT_DAG_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256_file(prelabel_path)

    result = {
        "schema": "ORBITTRACE_CROSSHIERARCHY_REFINEMENT_DAG_V1_RESULT",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "gates": gates,
        "aggregate": {
            "pooled_mean_symmetric_stability": means,
            "median_symmetric_stability": medians,
            "atom_strict_wins_over_both": strict_both,
            "transition_count": len(transitions),
        },
        "transitions": transitions,
        "panel_audit": [
            {
                "denominator": r["denominator"],
                "bucket": r["bucket"],
                "event_count": r["event_count"],
                "event_universe_sha256": r["event_universe_sha256"],
                "sealed_sparse_rebind": r["sealed_sparse_rebind"],
                "dag_audit": r["dag_audit"],
            }
            for r in panel_records
        ],
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "external_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "CROSSHIERARCHY_REFINEMENT_DAG_V1_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "PRELABEL_SHA256.txt").write_text(prelabel_sha + "\n")
    (a.output / "RESULT_SHA256.txt").write_text(sha256_file(result_path) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
