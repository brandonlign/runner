#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

BWM_PRETRUTH_SHA = "2e6eca03f03702c78b36624026e20feb4f081b5d9f9507e0ea3436cc33bb199a"
BIF_ENDPOINT_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
SUPPORT_PRUNED_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def member_hash(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def family_id(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("CMR1|" + "\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def q90(values: list[int]) -> float:
    req(bool(values), "empty size list")
    return float(np.quantile(np.asarray(values, dtype=float), 0.90))


def burden(values: list[int]) -> float:
    req(bool(values) and all(v > 0 for v in values), "bad size list")
    return float(sum(v * v for v in values) / sum(values))


def exact_m2d(candidate: frozenset[str], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    n = len(candidate)
    req(n >= MIN_SUPPORT, "candidate below support")
    weighted = 0.0
    raw_area = 0.0
    count = 0
    for row in bif_rows:
        b = members(row)
        if b.issubset(candidate):
            area = float(row["persistence_area"])
            req(len(b) >= MIN_SUPPORT and area > 0.0 and math.isfinite(area), "bad witness")
            weighted += (len(b) / n) * area
            raw_area += area
            count += 1
    return float(weighted), int(count), float(raw_area)


def regrow_core(
    core: frozenset[str],
    parent: frozenset[str],
    contained: list[tuple[frozenset[str], float]],
) -> tuple[frozenset[str], dict[str, Any]]:
    req(core.issubset(parent) and len(core) >= MIN_SUPPORT, "bad seed core")
    ids = sorted(parent)
    index = {eid: i for i, eid in enumerate(ids)}
    wmat = np.zeros((len(ids), len(ids)), dtype=np.float64)
    expected_degree_mass = 0.0
    for b, area in contained:
        inds = np.fromiter((index[eid] for eid in b), dtype=np.int64)
        per_pair = area / (len(b) - 1)
        req(per_pair > 0.0 and math.isfinite(per_pair), "bad pair weight")
        wmat[np.ix_(inds, inds)] += per_pair
        wmat[inds, inds] -= per_pair
        expected_degree_mass += len(b) * area

    req(np.all(np.isfinite(wmat)) and np.all(wmat >= -1e-18), "invalid witness matrix")
    wmat[wmat < 0.0] = 0.0
    req(np.allclose(wmat, wmat.T, rtol=0.0, atol=1e-15), "witness matrix asymmetric")
    actual_degree_mass = float(wmat.sum())
    if expected_degree_mass > 0.0:
        req(
            math.isclose(actual_degree_mass, expected_degree_mass, rel_tol=1e-11, abs_tol=1e-14),
            "witness degree-mass identity failed",
        )

    degree = wmat.sum(axis=1)
    core_ix = np.fromiter((index[eid] for eid in core), dtype=np.int64)
    to_core = wmat[:, core_ix].sum(axis=1)
    admitted_ix = np.where((degree > 0.0) & ((2.0 * to_core) > degree + 1e-15))[0]
    grown = set(core)
    grown.update(ids[int(i)] for i in admitted_ix)
    grown_set = frozenset(grown)
    req(core.issubset(grown_set) and grown_set.issubset(parent), "regrowth escaped parent")
    added = grown_set - core
    for eid in added:
        i = index[eid]
        req(
            degree[i] > 0.0 and 2.0 * float(to_core[i]) > float(degree[i]) + 1e-15,
            "invalid recruit",
        )
    return grown_set, {
        "seed_member_count": len(core),
        "grown_member_count": len(grown_set),
        "added_member_count": len(added),
        "positive_degree_parent_members": int(np.sum(degree > 0.0)),
        "witness_degree_mass": actual_degree_mass,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bwm-pretruth", type=Path, required=True)
    ap.add_argument("--bif-endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.bwm_pretruth) == BWM_PRETRUTH_SHA, "frozen BWM seed pretruth changed")
    req(sha(a.bif_endpoint_prelabel) == BIF_ENDPOINT_SHA, "frozen bifiltration endpoint changed")
    bwm = json.loads(a.bwm_pretruth.read_text())
    bif = json.loads(a.bif_endpoint_prelabel.read_text())
    req(bwm.get("schema") == "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH", "wrong BWM seed schema")
    req(
        bwm.get("scientific_role") == "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH",
        "wrong BWM seed role",
    )
    req(bwm.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned parent changed")
    req(
        bwm.get("shower_truth_used") is False
        and bwm.get("target_information_access") is False
        and bwm.get("target_region_events_accessed") is False
        and bwm.get("orbittrace_reveal_access") is False
        and bwm.get("sonotaco_scientific_access") is False,
        "BWM seed firewall",
    )
    req(
        bif.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL",
        "wrong bif schema",
    )
    req(
        bif.get("shower_truth_used") is False
        and bif.get("target_information_access") is False
        and bif.get("target_region_events_accessed") is False
        and bif.get("sonotaco_2013_2014_access") is False,
        "bif firewall",
    )

    bm = {(int(s["denominator"]), int(s["bucket"])): s for s in bwm["subsets"]}
    fm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(bm) == set(fm) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    cmr_top_sizes_all: list[int] = []
    bwm_top_sizes_all: list[int] = []
    baseline_top_sizes_all: list[int] = []
    total_seed_cores = 0
    grown_seed_cores = 0
    total_added_membership_instances = 0
    total_overlap_pairs = 0
    total_overlap_event_instances = 0

    for key in sorted(keys):
        bs, fs = bm[key], fm[key]
        req(int(bs["event_count"]) == int(fs["event_count"]), f"event count mismatch {key}")
        req(
            {str(y): list(map(str, bs["annual_event_ids"][str(y)])) for y in (2022, 2023)}
            == {str(y): list(map(str, fs["annual_event_ids"][str(y)])) for y in (2022, 2023)},
            f"annual universe mismatch {key}",
        )
        bif_rows = list(fs["bifiltration_candidates"])
        parents = list(bs["support_pruned_baseline_candidates"])
        seeds = list(bs["bwm_candidates"])
        req(parents and seeds, "empty candidate catalogue")
        pmap = {str(p["family_hash"]): p for p in parents}
        req(len(pmap) == len(parents), "duplicate parent hash")
        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for seed in seeds:
            ph = str(seed["bwm_parent_family_hash"])
            req(ph in pmap, "seed parent missing")
            by_parent[ph].append(seed)
        req(set(by_parent) == set(pmap), "BWM parent coverage changed")

        rows: list[dict[str, Any]] = []
        growth_summaries: list[dict[str, Any]] = []
        for ph, parent in pmap.items():
            parent_set = members(parent)
            contained: list[tuple[frozenset[str], float]] = []
            for row in bif_rows:
                b = members(row)
                if b.issubset(parent_set):
                    area = float(row["persistence_area"])
                    req(len(b) >= MIN_SUPPORT and area > 0.0 and math.isfinite(area), "bad contained witness")
                    contained.append((b, area))

            for seed in by_parent[ph]:
                total_seed_cores += 1
                core = members(seed)
                req(core.issubset(parent_set) and len(core) == int(seed["member_count"]), "bad BWM seed")
                if core == parent_set:
                    grown = core
                    gs = {
                        "seed_member_count": len(core),
                        "grown_member_count": len(core),
                        "added_member_count": 0,
                        "positive_degree_parent_members": len(set().union(*(set(w) for w, _ in contained))) if contained else 0,
                        "witness_degree_mass": None,
                    }
                else:
                    grown, gs = regrow_core(core, parent_set, contained)

                if len(grown) > len(core):
                    grown_seed_cores += 1
                    total_added_membership_instances += len(grown) - len(core)
                score, count, raw_area = exact_m2d(grown, bif_rows)
                rows.append({
                    "family_id": family_id(grown),
                    "family_hash": member_hash(grown),
                    "event_ids": sorted(grown),
                    "member_count": len(grown),
                    "internal_2d_mass": score,
                    "internal_bif_component_count": count,
                    "internal_bif_raw_area_sum": raw_area,
                    "cmr_seed_family_hash": str(seed["family_hash"]),
                    "cmr_seed_member_count": len(core),
                    "cmr_parent_family_hash": ph,
                    "cmr_parent_member_count": len(parent_set),
                    "cmr_added_member_count": len(grown) - len(core),
                    "cmr_one_shot": True,
                    "cmr_strict_majority": True,
                })
                growth_summaries.append({"seed_family_hash": str(seed["family_hash"]), "parent_family_hash": ph, **gs})

        unique: dict[tuple[str, ...], dict[str, Any]] = {}
        for row in rows:
            mk = tuple(row["event_ids"])
            old = unique.get(mk)
            if old is None or (
                float(row["internal_2d_mass"]), str(row["cmr_seed_family_hash"])
            ) > (
                float(old["internal_2d_mass"]), str(old["cmr_seed_family_hash"])
            ):
                unique[mk] = row
        rows = list(unique.values())
        rows.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
        for rank, row in enumerate(rows, 1):
            row["internal_mass_rank"] = rank
            row["rank"] = rank

        sets = [members(r) for r in rows]
        overlap_pairs = 0
        overlap_instances = 0
        for i, x in enumerate(sets):
            for y in sets[i + 1:]:
                ov = len(x.intersection(y))
                if ov:
                    overlap_pairs += 1
                    overlap_instances += ov
        total_overlap_pairs += overlap_pairs
        total_overlap_event_instances += overlap_instances

        k = int(bs["equal_budget_k"])
        req(k > 0 and len(rows) >= min(k, len(seeds)), "candidate capacity unexpectedly collapsed")
        cmr_top = rows[:k]
        bwm_top = seeds[:k]
        base_top = parents[:k]
        cmr_sizes = [int(r["member_count"]) for r in cmr_top]
        bwm_sizes = [int(r["member_count"]) for r in bwm_top]
        base_sizes = [int(r["member_count"]) for r in base_top]
        cmr_top_sizes_all.extend(cmr_sizes)
        bwm_top_sizes_all.extend(bwm_sizes)
        baseline_top_sizes_all.extend(base_sizes)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(bs["event_count"]),
            "annual_event_ids": bs["annual_event_ids"],
            "equal_budget_k": k,
            "cmr_candidates": rows,
            "bwm_seed_candidates": seeds,
            "support_pruned_baseline_candidates": parents,
            "growth_summaries": growth_summaries,
            "capacity": {
                "cmr_available": len(rows),
                "bwm_seed_available": len(seeds),
                "support_pruned_available": len(parents),
                "budget_k": k,
            },
            "top_budget_size": {
                "cmr_mean": mean(cmr_sizes),
                "bwm_seed_mean": mean(bwm_sizes),
                "support_pruned_mean": mean(base_sizes),
                "cmr_p90": q90(cmr_sizes),
                "bwm_seed_p90": q90(bwm_sizes),
                "support_pruned_p90": q90(base_sizes),
                "cmr_max": max(cmr_sizes),
                "bwm_seed_max": max(bwm_sizes),
                "support_pruned_max": max(base_sizes),
                "cmr_burden": burden(cmr_sizes),
                "bwm_seed_burden": burden(bwm_sizes),
                "support_pruned_burden": burden(base_sizes),
            },
            "overlap": {"candidate_pairs": overlap_pairs, "event_instances": overlap_instances},
        })

    size_summary = {
        "cmr_mean_top_budget_member_count": mean(cmr_top_sizes_all),
        "bwm_seed_mean_top_budget_member_count": mean(bwm_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(baseline_top_sizes_all),
        "cmr_p90_top_budget_member_count": q90(cmr_top_sizes_all),
        "bwm_seed_p90_top_budget_member_count": q90(bwm_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(baseline_top_sizes_all),
        "cmr_max_top_budget_member_count": max(cmr_top_sizes_all),
        "bwm_seed_max_top_budget_member_count": max(bwm_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(baseline_top_sizes_all),
        "cmr_size_biased_top_budget_member_burden": burden(cmr_top_sizes_all),
        "bwm_seed_size_biased_top_budget_member_burden": burden(bwm_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(baseline_top_sizes_all),
    }
    structural_gates = {
        "regrowth_active": grown_seed_cores > 0 and total_added_membership_instances > 0,
        "mean_still_below_support_pruned": size_summary["cmr_mean_top_budget_member_count"] < size_summary["support_pruned_mean_top_budget_member_count"],
        "p90_still_below_support_pruned": size_summary["cmr_p90_top_budget_member_count"] < size_summary["support_pruned_p90_top_budget_member_count"],
        "max_still_below_support_pruned": size_summary["cmr_max_top_budget_member_count"] < size_summary["support_pruned_max_top_budget_member_count"],
        "mean_above_bwm_seed": size_summary["cmr_mean_top_budget_member_count"] > size_summary["bwm_seed_mean_top_budget_member_count"],
    }
    out = {
        "schema": "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_CMR_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH",
        "configuration": {
            "seed_method": "BWM_v1_frozen_pretruth",
            "outer_basin": "support_pruned_v1_parent",
            "co_witness_pair_weight": "persistence_area/(witness_member_count-1)",
            "regrowth_rule": "admit v iff 2*weighted_mass(v, ORIGINAL_seed_core) > total_weighted_degree(v)",
            "one_shot": True,
            "newly_admitted_members_can_recruit": False,
            "strict_majority_threshold": "exact logical majority; no fitted scalar",
            "ranking": "exact M2D descending, then membership hash",
            "new_tuned_parameters": [],
            "inherited_bwm_modularity_resolution": 1.0,
            "inherited_bwm_community_passes": 1,
        },
        "bwm_seed_pretruth_sha256": BWM_PRETRUTH_SHA,
        "bif_endpoint_prelabel_sha256": BIF_ENDPOINT_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "size_summary": size_summary,
        "mechanism_summary": {
            "total_seed_cores": total_seed_cores,
            "grown_seed_cores": grown_seed_cores,
            "total_added_membership_instances": total_added_membership_instances,
            "overlapping_candidate_pairs": total_overlap_pairs,
            "overlap_event_instances": total_overlap_event_instances,
        },
        "structural_gates": structural_gates,
        "structural_pass": all(structural_gates.values()),
        "subsets": subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "GMN 2022/2023 panels exclude the protected OrbitTrace interval but are development-exposed. This construction uses only frozen zero-label BWM/bifiltration structure; any later hidden-label result is development evidence, not fresh external validation.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "size_summary": size_summary,
        "mechanism_summary": out["mechanism_summary"],
        "structural_gates": structural_gates,
    }, indent=2, sort_keys=True))
    print("PASS_CORE_MAJORITY_REGROWTH_V1_PRETRUTH" if out["structural_pass"] else "FAIL_CORE_MAJORITY_REGROWTH_V1_STRUCTURAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
