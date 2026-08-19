#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import networkx as nx
import numpy as np

SUPPORT_PRUNED_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
BIF_ENDPOINT_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
BIF_ORIGINAL_SHA = "63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
RESOLUTION = 1.0
NETWORKX_VERSION = "3.6.1"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_set(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def member_hash(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def family_id(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("BWM1|" + "\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def exact_m2d(candidate: frozenset[str], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    n = len(candidate)
    req(n >= MIN_SUPPORT, "candidate below support")
    weighted = 0.0
    raw_area = 0.0
    count = 0
    for row in bif_rows:
        b = member_set(row)
        if b.issubset(candidate):
            area = float(row["persistence_area"])
            req(area > 0.0 and math.isfinite(area), "bad persistence area")
            weighted += (len(b) / n) * area
            raw_area += area
            count += 1
    return float(weighted), int(count), float(raw_area)


def witness_partition(parent: dict[str, Any], bif_rows: list[dict[str, Any]]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    parent_set = member_set(parent)
    req(len(parent_set) == int(parent["member_count"]) >= MIN_SUPPORT, "bad parent")
    contained: list[tuple[frozenset[str], float]] = []
    witness: set[str] = set()
    for row in bif_rows:
        b = member_set(row)
        if b.issubset(parent_set):
            area = float(row["persistence_area"])
            req(len(b) >= MIN_SUPPORT and area > 0.0 and math.isfinite(area), "bad witness")
            contained.append((b, area))
            witness.update(b)

    if not contained or len(witness) < MIN_SUPPORT:
        return [parent_set], {
            "fallback_parent": True,
            "contained_witness_count": len(contained),
            "witness_event_count": len(witness),
            "raw_modularity_community_count": 0,
            "reportable_community_count": 1,
            "dropped_unwitnessed_events": 0,
            "dropped_subsupport_community_events": 0,
            "modularity": None,
        }

    ids = sorted(witness)
    index = {eid: i for i, eid in enumerate(ids)}
    wmat = np.zeros((len(ids), len(ids)), dtype=np.float64)
    total_expected_degree_mass = 0.0
    for b, area in contained:
        inds = np.fromiter((index[eid] for eid in b), dtype=np.int64)
        per_pair = area / (len(b) - 1)
        req(per_pair > 0.0 and math.isfinite(per_pair), "bad pair weight")
        wmat[np.ix_(inds, inds)] += per_pair
        wmat[inds, inds] -= per_pair
        total_expected_degree_mass += len(b) * area

    req(np.all(np.isfinite(wmat)) and np.all(wmat >= -1e-18), "invalid witness matrix")
    wmat[wmat < 0.0] = 0.0
    req(np.allclose(wmat, wmat.T, rtol=0.0, atol=1e-15), "witness matrix asymmetric")
    actual_degree_mass = float(wmat.sum())
    req(math.isclose(actual_degree_mass, total_expected_degree_mass, rel_tol=1e-11, abs_tol=1e-14), "witness degree-mass identity failed")
    req(actual_degree_mass > 0.0, "zero witness graph mass")

    graph = nx.from_numpy_array(wmat)
    graph.remove_edges_from([(u, v) for u, v, d in graph.edges(data=True) if float(d.get("weight", 0.0)) <= 0.0])
    req(graph.number_of_nodes() == len(ids) and graph.number_of_edges() > 0, "empty witness graph")
    req(all(graph.degree(i, weight="weight") > 0.0 for i in graph.nodes), "witness event has zero strength")

    raw = list(nx.algorithms.community.greedy_modularity_communities(
        graph,
        weight="weight",
        resolution=RESOLUTION,
        cutoff=1,
        best_n=None,
    ))
    req(raw and set().union(*(set(c) for c in raw)) == set(range(len(ids))), "modularity partition invalid")
    req(sum(len(c) for c in raw) == len(ids), "modularity communities overlap")
    modularity = float(nx.algorithms.community.modularity(graph, raw, weight="weight", resolution=RESOLUTION))
    req(math.isfinite(modularity), "nonfinite modularity")

    reportable = [frozenset(ids[int(i)] for i in community) for community in raw if len(community) >= MIN_SUPPORT]
    small_events = sum(len(community) for community in raw if len(community) < MIN_SUPPORT)
    if not reportable:
        return [parent_set], {
            "fallback_parent": True,
            "contained_witness_count": len(contained),
            "witness_event_count": len(witness),
            "raw_modularity_community_count": len(raw),
            "reportable_community_count": 1,
            "dropped_unwitnessed_events": 0,
            "dropped_subsupport_community_events": 0,
            "modularity": modularity,
        }

    reportable.sort(key=lambda s: member_hash(s))
    req(all(c.issubset(parent_set) and len(c) >= MIN_SUPPORT for c in reportable), "bad reportable community")
    req(all(not a.intersection(b) for i, a in enumerate(reportable) for b in reportable[i + 1 :]), "reportable communities overlap")
    covered = set().union(*(set(c) for c in reportable))
    return reportable, {
        "fallback_parent": False,
        "contained_witness_count": len(contained),
        "witness_event_count": len(witness),
        "raw_modularity_community_count": len(raw),
        "reportable_community_count": len(reportable),
        "dropped_unwitnessed_events": len(parent_set - witness),
        "dropped_subsupport_community_events": int(small_events),
        "retained_event_count": len(covered),
        "modularity": modularity,
        "witness_degree_mass": actual_degree_mass,
    }


def q90(values: list[int]) -> float:
    req(bool(values), "empty size list")
    return float(np.quantile(np.asarray(values, dtype=float), 0.90))


def burden(values: list[int]) -> float:
    req(bool(values) and all(v > 0 for v in values), "bad size list")
    return float(sum(v * v for v in values) / sum(values))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--support-pruned-pretruth", type=Path, required=True)
    ap.add_argument("--bif-endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(nx.__version__ == NETWORKX_VERSION, f"NetworkX version changed: {nx.__version__}")
    req(sha(a.support_pruned_pretruth) == SUPPORT_PRUNED_SHA, "support-pruned pretruth changed")
    req(sha(a.bif_endpoint_prelabel) == BIF_ENDPOINT_SHA, "bif endpoint prelabel changed")
    support = json.loads(a.support_pruned_pretruth.read_text())
    bif = json.loads(a.bif_endpoint_prelabel.read_text())
    req(support.get("schema") == "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH", "wrong support-pruned schema")
    req(support.get("scientific_role") == "TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_RANKING_FROZEN_BEFORE_TRUTH", "wrong support-pruned role")
    req(support.get("shower_truth_used") is False and support.get("target_information_access") is False and support.get("target_region_events_accessed") is False and support.get("orbittrace_reveal_access") is False, "support-pruned firewall")
    req(bif.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong bif endpoint schema")
    req(bif.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong bif endpoint role")
    req(bif.get("frozen_bif_pretruth_sha256") == BIF_ORIGINAL_SHA, "original bif freeze changed")
    req(bif.get("shower_truth_used") is False and bif.get("target_information_access") is False and bif.get("target_region_events_accessed") is False and bif.get("sonotaco_2013_2014_access") is False, "bif endpoint firewall")

    smap = {(int(s["denominator"]), int(s["bucket"])): s for s in support["subsets"]}
    bmap = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(smap) == set(bmap) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    bwm_top_sizes_all: list[int] = []
    baseline_top_sizes_all: list[int] = []
    total_parents = 0
    refined_parents = 0
    split_parents = 0
    core_shrunk_parents = 0
    dropped_unwitnessed = 0
    dropped_small = 0

    for key in sorted(keys):
        ss, bs = smap[key], bmap[key]
        req(int(ss["event_count"]) == int(bs["event_count"]), f"event count mismatch {key}")
        req({str(y): list(map(str, ss["annual_event_ids"][str(y)])) for y in (2022, 2023)} == {str(y): list(map(str, bs["annual_event_ids"][str(y)])) for y in (2022, 2023)}, f"annual universe mismatch {key}")
        bif_rows = list(bs["bifiltration_candidates"])
        req(all(float(r["persistence_area"]) > 0.0 and int(r["member_count"]) >= MIN_SUPPORT for r in bif_rows), "bad bif witness list")
        parents = list(ss["refined_candidates"])
        req(parents and all(int(r["member_count"]) >= MIN_SUPPORT for r in parents), "bad support-pruned parent list")
        parent_sets = [member_set(r) for r in parents]
        req(all(not x.intersection(y) for i, x in enumerate(parent_sets) for y in parent_sets[i + 1 :]), "support-pruned parents overlap")

        rows: list[dict[str, Any]] = []
        parent_summaries: list[dict[str, Any]] = []
        for parent in parents:
            total_parents += 1
            communities, summary = witness_partition(parent, bif_rows)
            parent_set = member_set(parent)
            if not summary["fallback_parent"]:
                refined_parents += 1
                if len(communities) > 1:
                    split_parents += 1
                if sum(len(c) for c in communities) < len(parent_set):
                    core_shrunk_parents += 1
                dropped_unwitnessed += int(summary["dropped_unwitnessed_events"])
                dropped_small += int(summary["dropped_subsupport_community_events"])
            summary = dict(summary)
            summary.update({"parent_family_hash": str(parent["family_hash"]), "parent_member_count": int(parent["member_count"])})
            parent_summaries.append(summary)

            for community in communities:
                score, count, raw_area = exact_m2d(community, bif_rows)
                rows.append({
                    "family_id": family_id(community),
                    "family_hash": member_hash(community),
                    "event_ids": sorted(community),
                    "member_count": len(community),
                    "internal_2d_mass": score,
                    "internal_bif_component_count": count,
                    "internal_bif_raw_area_sum": raw_area,
                    "bwm_parent_family_hash": str(parent["family_hash"]),
                    "bwm_parent_member_count": int(parent["member_count"]),
                    "bwm_fallback_parent": bool(summary["fallback_parent"]),
                    "bwm_parent_modularity": summary["modularity"],
                })

        sets = [member_set(r) for r in rows]
        req(all(not x.intersection(y) for i, x in enumerate(sets) for y in sets[i + 1 :]), f"BWM outputs overlap {key}")
        req(len(sets) == len({tuple(sorted(s)) for s in sets}), f"duplicate BWM membership {key}")
        rows.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
        for rank, row in enumerate(rows, 1):
            row["internal_mass_rank"] = rank
            row["rank"] = rank

        k = int(ss["equal_budget_k"])
        req(k > 0, "bad frozen budget")
        bwm_top = rows[:k]
        base_top = parents[:k]
        bwm_sizes = [int(r["member_count"]) for r in bwm_top]
        base_sizes = [int(r["member_count"]) for r in base_top]
        req(bwm_sizes and base_sizes, "empty top-budget size list")
        bwm_top_sizes_all.extend(bwm_sizes)
        baseline_top_sizes_all.extend(base_sizes)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(ss["event_count"]),
            "annual_event_ids": ss["annual_event_ids"],
            "equal_budget_k": k,
            "bwm_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "parent_summaries": parent_summaries,
            "capacity": {"bwm_available": len(rows), "support_pruned_available": len(parents), "budget_k": k},
            "top_budget_size": {
                "bwm_mean": mean(bwm_sizes),
                "support_pruned_mean": mean(base_sizes),
                "bwm_p90": q90(bwm_sizes),
                "support_pruned_p90": q90(base_sizes),
                "bwm_max": max(bwm_sizes),
                "support_pruned_max": max(base_sizes),
                "bwm_size_biased_burden": burden(bwm_sizes),
                "support_pruned_size_biased_burden": burden(base_sizes),
            },
        })

    size_summary = {
        "bwm_mean_top_budget_member_count": mean(bwm_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(baseline_top_sizes_all),
        "bwm_p90_top_budget_member_count": q90(bwm_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(baseline_top_sizes_all),
        "bwm_max_top_budget_member_count": max(bwm_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(baseline_top_sizes_all),
        "bwm_size_biased_top_budget_member_burden": burden(bwm_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(baseline_top_sizes_all),
    }
    mechanism_summary = {
        "total_support_pruned_parents": total_parents,
        "refined_parent_count": refined_parents,
        "split_parent_count": split_parents,
        "core_shrunk_parent_count": core_shrunk_parents,
        "dropped_unwitnessed_events": dropped_unwitnessed,
        "dropped_subsupport_community_events": dropped_small,
    }

    out = {
        "schema": "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH",
        "configuration": {
            "parent": "promoted_support_pruned_m2d_v1",
            "witness_source": "frozen_annual_density_bifiltration_components",
            "pair_weight": "persistence_area/(member_count-1)",
            "community_method": "Clauset-Newman-Moore greedy modularity",
            "networkx_version": NETWORKX_VERSION,
            "modularity_resolution": RESOLUTION,
            "minimum_support": MIN_SUPPORT,
            "community_passes": 1,
            "subsupport_communities": "noise",
            "unwitnessed_parent_events": "noise_when_at_least_one_reportable_witness_community_exists",
            "fallback": "retain_parent_only_when_no_reportable_witness_community_exists",
            "m2d_formula": "(1/|C|)*sum_{B subseteq C}|B|*A(B)",
            "ranking": ["internal_2d_mass_desc", "membership_sha256_asc"],
            "new_tuned_parameters": [],
        },
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "bif_endpoint_prelabel_sha256": BIF_ENDPOINT_SHA,
        "bif_original_pretruth_sha256": BIF_ORIGINAL_SHA,
        "mechanism_summary": mechanism_summary,
        "size_summary": size_summary,
        "subsets": subsets,
        "design_stage_label_free_structural_metrics": True,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "BWM_V1_PRETRUTH_SEALED", "pretruth_sha256": sha(a.output), "mechanism_summary": mechanism_summary, "size_summary": size_summary, "capacities": [{"d":s["denominator"],"b":s["bucket"],**s["capacity"]} for s in subsets]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
