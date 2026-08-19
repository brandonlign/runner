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


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    req(cmr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned source changed")
    req(
        cmr.get("shower_truth_used") is False
        and cmr.get("target_information_access") is False
        and cmr.get("target_region_events_accessed") is False
        and cmr.get("orbittrace_reveal_access") is False
        and cmr.get("sonotaco_scientific_access") is False,
        "CMR source firewall failed",
    )

    smap = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(smap) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    core_top_sizes_all: list[int] = []
    envelope_top_sizes_all: list[int] = []
    core_strictly_smaller = 0
    total_pairs = 0
    top_core_strictly_smaller = 0
    top_total = 0

    for key in sorted(keys):
        s = smap[key]
        parents = list(s["support_pruned_baseline_candidates"])
        children = list(s["cmr_candidates"])
        req(parents and children, "empty source catalogue")
        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for child in children:
            ph = str(child["cmr_parent_family_hash"])
            by_parent[ph].append(child)
        req(set(by_parent) == {str(p["family_hash"]) for p in parents}, "CMR parent coverage changed")

        pairs: list[dict[str, Any]] = []
        for envelope_rank, parent in enumerate(parents, 1):
            ph = str(parent["family_hash"])
            req(int(parent["internal_mass_rank"]) == envelope_rank, "support-pruned M2D order drift")
            options = sorted(
                by_parent[ph],
                key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])),
            )
            core = options[0]
            envelope_ids = [str(x) for x in parent["event_ids"]]
            core_ids = [str(x) for x in core["event_ids"]]
            req(set(core_ids).issubset(set(envelope_ids)), "core escaped envelope")
            smaller = len(core_ids) < len(envelope_ids)
            total_pairs += 1
            core_strictly_smaller += int(smaller)
            pairs.append({
                "family_id": str(parent["family_id"]),
                "family_hash": ph,
                "event_ids": envelope_ids,
                "member_count": len(envelope_ids),
                "internal_2d_mass": float(parent["internal_2d_mass"]),
                "internal_mass_rank": envelope_rank,
                "rank": envelope_rank,
                "core_event_ids": core_ids,
                "core_member_count": len(core_ids),
                "core_family_hash": str(core["family_hash"]),
                "core_family_id": str(core["family_id"]),
                "core_internal_2d_mass": float(core["internal_2d_mass"]),
                "core_seed_family_hash": str(core["cmr_seed_family_hash"]),
                "core_selection_rule": "highest exact CMR M2D within frozen support-pruned parent; tie membership hash",
                "core_is_strict_subset": smaller,
                "envelope_source": "exact promoted support-pruned TopoModal+M2D parent",
            })

        k = int(s["equal_budget_k"])
        req(k > 0 and len(pairs) >= k, "capacity changed")
        core_sizes = [int(r["core_member_count"]) for r in pairs[:k]]
        env_sizes = [int(r["member_count"]) for r in pairs[:k]]
        core_top_sizes_all.extend(core_sizes)
        envelope_top_sizes_all.extend(env_sizes)
        top_core_strictly_smaller += sum(int(r["core_is_strict_subset"]) for r in pairs[:k])
        top_total += k

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(s["event_count"]),
            "annual_event_ids": s["annual_event_ids"],
            "equal_budget_k": k,
            "envelope_core_candidates": pairs,
            "support_pruned_baseline_candidates": parents,
            "capacity": {"envelope_core_available": len(pairs), "support_pruned_available": len(parents), "budget_k": k},
            "top_budget_size": {
                "core_mean": mean(core_sizes),
                "envelope_mean": mean(env_sizes),
                "core_p90": q90(core_sizes),
                "envelope_p90": q90(env_sizes),
                "core_max": max(core_sizes),
                "envelope_max": max(env_sizes),
                "core_burden": burden(core_sizes),
                "envelope_burden": burden(env_sizes),
            },
        })

    size_summary = {
        "core_mean_top_budget_member_count": mean(core_top_sizes_all),
        "envelope_mean_top_budget_member_count": mean(envelope_top_sizes_all),
        "core_p90_top_budget_member_count": q90(core_top_sizes_all),
        "envelope_p90_top_budget_member_count": q90(envelope_top_sizes_all),
        "core_max_top_budget_member_count": max(core_top_sizes_all),
        "envelope_max_top_budget_member_count": max(envelope_top_sizes_all),
        "core_size_biased_top_budget_member_burden": burden(core_top_sizes_all),
        "envelope_size_biased_top_budget_member_burden": burden(envelope_top_sizes_all),
    }
    mechanism_summary = {
        "total_envelope_core_pairs": total_pairs,
        "strict_subset_core_pairs": core_strictly_smaller,
        "strict_subset_core_fraction": core_strictly_smaller / total_pairs,
        "top_budget_strict_subset_instances": top_core_strictly_smaller,
        "top_budget_total_instances": top_total,
        "top_budget_strict_subset_fraction": top_core_strictly_smaller / top_total,
        "envelope_ranking_changed_from_support_pruned": False,
        "envelope_membership_changed_from_support_pruned": False,
    }
    structural_gates = {
        "mechanism_active": core_strictly_smaller > 0,
        "top_budget_mechanism_active": top_core_strictly_smaller > 0,
        "core_mean_strictly_lower_than_envelope": size_summary["core_mean_top_budget_member_count"] < size_summary["envelope_mean_top_budget_member_count"],
        "core_p90_strictly_lower_than_envelope": size_summary["core_p90_top_budget_member_count"] < size_summary["envelope_p90_top_budget_member_count"],
        "core_max_strictly_lower_than_envelope": size_summary["core_max_top_budget_member_count"] < size_summary["envelope_max_top_budget_member_count"],
        "core_burden_strictly_lower_than_envelope": size_summary["core_size_biased_top_budget_member_burden"] < size_summary["envelope_size_biased_top_budget_member_burden"],
    }
    structural_pass = all(structural_gates.values())

    out = {
        "schema": "ORBITTRACE_ENVELOPE_CORE_TOPOMODAL_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_ECT_V1_HIERARCHICAL_CANDIDATES_FROZEN_BEFORE_CORE_TRUTH_TEST",
        "development_status": "GMN_2022_2023_EXPOSED_DEVELOPMENT_AFTER_BWM_CMR_FOCR_DCR_PADCR; NON_GMN_TRANSFER_REQUIRED_FOR_GENERALIZATION",
        "cmr_pretruth_sha256": CMR_PRETRUTH_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "detection_envelope": "exact promoted support-pruned TopoModal+M2D membership and ordering",
            "extraction_core": "highest exact-M2D frozen CMR child within the envelope; tie membership hash",
            "core_replaces_envelope": False,
            "core_changes_envelope_rank": False,
            "one_core_per_envelope": True,
            "new_tuned_parameters": [],
        },
        "mechanism_summary": mechanism_summary,
        "size_summary": size_summary,
        "structural_gates": structural_gates,
        "structural_pass": structural_pass,
        "subsets": subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "ECT v1 separates detection from extraction after flat hard-refinement failures. Standard literature comparisons apply only to the unchanged envelope; the nested core has its own paired extraction-quality test and cannot be substituted into the flat benchmark post hoc.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"structural_pass": structural_pass, "mechanism_summary": mechanism_summary, "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
