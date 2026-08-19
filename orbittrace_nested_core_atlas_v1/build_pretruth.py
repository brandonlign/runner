#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

CMR_PRETRUTH_SHA = "8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb"
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


def q90(values: list[int]) -> float:
    req(bool(values), "empty size list")
    return float(np.quantile(np.asarray(values, dtype=float), 0.90))


def burden(values: list[int]) -> float:
    req(bool(values) and all(v > 0 for v in values), "bad size list")
    return float(sum(v * v for v in values) / sum(values))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmr-pretruth", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.cmr_pretruth) == CMR_PRETRUTH_SHA, "frozen CMR pretruth changed")
    cmr = json.loads(a.cmr_pretruth.read_text())
    req(cmr.get("schema") == "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_PRETRUTH", "wrong CMR schema")
    req(cmr.get("scientific_role") == "TARGET_EXCLUDED_GMN_CMR_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH", "wrong CMR role")
    req(cmr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned source changed")
    req(
        cmr.get("shower_truth_used") is False
        and cmr.get("target_information_access") is False
        and cmr.get("target_region_events_accessed") is False
        and cmr.get("orbittrace_reveal_access") is False
        and cmr.get("sonotaco_scientific_access") is False,
        "CMR source firewall",
    )

    subsets_in = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(subsets_in) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    top_envelope_sizes: list[int] = []
    top_primary_sizes: list[int] = []
    top_seed_sizes: list[int] = []
    total_parents = 0
    total_branches = 0
    strict_primary_shrink_parents = 0
    strict_seed_shrink_parents = 0
    multi_branch_parents = 0

    for key in sorted(keys):
        src = subsets_in[key]
        parents = list(src["support_pruned_baseline_candidates"])
        cmr_rows = list(src["cmr_candidates"])
        seed_rows = list(src["bwm_seed_candidates"])
        req(parents and cmr_rows and seed_rows, f"empty source catalogue {key}")
        pmap = {str(p["family_hash"]): p for p in parents}
        smap = {str(s["family_hash"]): s for s in seed_rows}
        req(len(pmap) == len(parents) and len(smap) == len(seed_rows), "duplicate source hash")

        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for core in cmr_rows:
            ph = str(core["cmr_parent_family_hash"])
            req(ph in pmap, "CMR parent missing")
            sh = str(core["cmr_seed_family_hash"])
            req(sh in smap, "CMR seed missing")
            req(str(smap[sh]["bwm_parent_family_hash"]) == ph, "seed/core parent mismatch")
            by_parent[ph].append(core)
        req(set(by_parent) == set(pmap), "not every envelope has nested branches")

        atlas_entries: list[dict[str, Any]] = []
        for parent in parents:
            total_parents += 1
            ph = str(parent["family_hash"])
            envelope = members(parent)
            req(len(envelope) == int(parent["member_count"]) >= MIN_SUPPORT, "bad envelope")
            cores = sorted(by_parent[ph], key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
            if len(cores) > 1:
                multi_branch_parents += 1
            branches: list[dict[str, Any]] = []
            seen_core: set[str] = set()
            for local_rank, core in enumerate(cores, 1):
                ch = str(core["family_hash"])
                req(ch not in seen_core, "duplicate CMR branch membership")
                seen_core.add(ch)
                seed = smap[str(core["cmr_seed_family_hash"])]
                seed_set = members(seed)
                core_set = members(core)
                req(len(seed_set) == int(seed["member_count"]) >= MIN_SUPPORT, "bad seed")
                req(len(core_set) == int(core["member_count"]) >= MIN_SUPPORT, "bad regrown core")
                req(seed_set.issubset(core_set) and core_set.issubset(envelope), "nested containment failed")
                branches.append({
                    "branch_rank_within_parent": local_rank,
                    "seed_family_hash": str(seed["family_hash"]),
                    "seed_event_ids": sorted(seed_set),
                    "seed_member_count": len(seed_set),
                    "seed_internal_2d_mass": float(seed["internal_2d_mass"]),
                    "regrown_family_hash": ch,
                    "regrown_event_ids": sorted(core_set),
                    "regrown_member_count": len(core_set),
                    "regrown_internal_2d_mass": float(core["internal_2d_mass"]),
                    "added_member_count": int(core["cmr_added_member_count"]),
                    "one_shot": bool(core["cmr_one_shot"]),
                    "strict_majority_regrowth": bool(core["cmr_strict_majority"]),
                })
            req(branches, "envelope without branch")
            primary = branches[0]
            if int(primary["regrown_member_count"]) < len(envelope):
                strict_primary_shrink_parents += 1
            if int(primary["seed_member_count"]) < len(envelope):
                strict_seed_shrink_parents += 1
            total_branches += len(branches)
            atlas_entries.append({
                "envelope_family_hash": ph,
                "envelope_family_id": str(parent["family_id"]),
                "envelope_rank": int(parent["rank"]),
                "envelope_internal_2d_mass": float(parent["internal_2d_mass"]),
                "envelope_modal_contrast": float(parent["modal_contrast"]),
                "envelope_event_ids": sorted(envelope),
                "envelope_member_count": len(envelope),
                "branch_count": len(branches),
                "primary_branch_rule": "highest_frozen_cmr_internal_2d_mass_then_membership_hash",
                "primary_regrown_family_hash": str(primary["regrown_family_hash"]),
                "primary_regrown_member_count": int(primary["regrown_member_count"]),
                "primary_seed_family_hash": str(primary["seed_family_hash"]),
                "primary_seed_member_count": int(primary["seed_member_count"]),
                "branches": branches,
            })

        req([e["envelope_family_hash"] for e in atlas_entries] == [str(p["family_hash"]) for p in parents], "parent order drift")
        k = int(src["equal_budget_k"])
        req(k > 0, "bad budget")
        top_entries = atlas_entries[:k]
        env_sizes = [int(e["envelope_member_count"]) for e in top_entries]
        primary_sizes = [int(e["primary_regrown_member_count"]) for e in top_entries]
        seed_sizes = [int(e["primary_seed_member_count"]) for e in top_entries]
        top_envelope_sizes.extend(env_sizes)
        top_primary_sizes.extend(primary_sizes)
        top_seed_sizes.extend(seed_sizes)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(src["event_count"]),
            "annual_event_ids": src["annual_event_ids"],
            "equal_budget_k": k,
            "envelope_candidates": parents,
            "atlas_entries": atlas_entries,
            "top_budget_structure": {
                "envelope_mean": mean(env_sizes),
                "primary_regrown_mean": mean(primary_sizes),
                "primary_seed_mean": mean(seed_sizes),
                "envelope_p90": q90(env_sizes),
                "primary_regrown_p90": q90(primary_sizes),
                "primary_seed_p90": q90(seed_sizes),
                "envelope_max": max(env_sizes),
                "primary_regrown_max": max(primary_sizes),
                "primary_seed_max": max(seed_sizes),
            },
        })

    structure = {
        "parent_count": total_parents,
        "branch_count": total_branches,
        "multi_branch_parent_count": multi_branch_parents,
        "strict_primary_regrown_shrink_parent_count": strict_primary_shrink_parents,
        "strict_primary_seed_shrink_parent_count": strict_seed_shrink_parents,
        "mean_branches_per_parent": total_branches / total_parents,
        "envelope_mean_top_budget_member_count": mean(top_envelope_sizes),
        "primary_regrown_mean_top_budget_member_count": mean(top_primary_sizes),
        "primary_seed_mean_top_budget_member_count": mean(top_seed_sizes),
        "envelope_p90_top_budget_member_count": q90(top_envelope_sizes),
        "primary_regrown_p90_top_budget_member_count": q90(top_primary_sizes),
        "primary_seed_p90_top_budget_member_count": q90(top_seed_sizes),
        "envelope_max_top_budget_member_count": max(top_envelope_sizes),
        "primary_regrown_max_top_budget_member_count": max(top_primary_sizes),
        "primary_seed_max_top_budget_member_count": max(top_seed_sizes),
        "envelope_size_biased_top_budget_burden": burden(top_envelope_sizes),
        "primary_regrown_size_biased_top_budget_burden": burden(top_primary_sizes),
        "primary_seed_size_biased_top_budget_burden": burden(top_seed_sizes),
    }
    gates = {
        "atlas_active": strict_primary_shrink_parents > 0 and total_branches > total_parents,
        "primary_regrown_mean_smaller_than_envelope": structure["primary_regrown_mean_top_budget_member_count"] < structure["envelope_mean_top_budget_member_count"],
        "primary_regrown_p90_smaller_than_envelope": structure["primary_regrown_p90_top_budget_member_count"] < structure["envelope_p90_top_budget_member_count"],
        "primary_regrown_max_smaller_than_envelope": structure["primary_regrown_max_top_budget_member_count"] < structure["envelope_max_top_budget_member_count"],
        "primary_seed_mean_smaller_than_primary_regrown": structure["primary_seed_mean_top_budget_member_count"] < structure["primary_regrown_mean_top_budget_member_count"],
        "top_level_parent_identity_preserved_by_construction": True,
    }
    out = {
        "schema": "ORBITTRACE_NESTED_CORE_ATLAS_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_PARENT_PRESERVING_NESTED_EXTRACTION_ATLAS_FROZEN_BEFORE_TRUTH",
        "cmr_pretruth_sha256": CMR_PRETRUTH_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "top_level_detection_object": "exact_promoted_support_pruned_parent",
            "top_level_ranking": "exact_promoted_parent_M2D_order",
            "nested_levels": ["BWM_seed", "CMR_one_shot_regrowth"],
            "branch_order_within_parent": ["frozen_CMR_internal_2d_mass_desc", "membership_hash_asc"],
            "primary_branch": "first_in_frozen_within_parent_order",
            "branch_consumes_top_level_capacity": False,
            "new_tuned_parameters": [],
        },
        "subsets": subsets,
        "structure_summary": structure,
        "structural_gates": gates,
        "structural_pass": all(gates.values()),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "GMN 2022/2023 is development-exposed. The atlas preserves promoted parent discovery objects exactly and exposes smaller inherited BWM/CMR structures only as nested extraction branches. A GMN identity pass authorizes frozen SonotaCo transfer; it is not untouched validation and cannot establish a new blind OrbitTrace rediscovery.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"structural_pass": out["structural_pass"], "structure_summary": structure, "structural_gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
