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


def member_hash(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


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

    source = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(source) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    env_top_all: list[int] = []
    union_top_all: list[int] = []
    total_parents = 0
    multi_branch_parents = 0
    strict_shrink_parents = 0
    top_budget_strict_shrink_instances = 0
    top_budget_total_instances = 0

    for key in sorted(keys):
        s = source[key]
        parents = list(s["support_pruned_baseline_candidates"])
        cores = list(s["cmr_candidates"])
        req(parents and cores, f"empty source {key}")
        pmap = {str(p["family_hash"]): p for p in parents}
        req(len(pmap) == len(parents), "duplicate parent hash")
        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for core in cores:
            ph = str(core["cmr_parent_family_hash"])
            req(ph in pmap, "CMR parent missing")
            by_parent[ph].append(core)
        req(set(by_parent) == set(pmap), "not every parent has CMR branch coverage")

        rows: list[dict[str, Any]] = []
        for parent in parents:
            total_parents += 1
            ph = str(parent["family_hash"])
            env = members(parent)
            req(len(env) == int(parent["member_count"]) >= MIN_SUPPORT, "bad envelope")
            branch_rows = by_parent[ph]
            if len(branch_rows) > 1:
                multi_branch_parents += 1
            union_set: set[str] = set()
            branch_hashes: list[str] = []
            for core in branch_rows:
                cset = members(core)
                req(len(cset) == int(core["member_count"]) >= MIN_SUPPORT, "bad CMR branch")
                req(cset.issubset(env), "CMR branch escaped envelope")
                union_set.update(cset)
                branch_hashes.append(str(core["family_hash"]))
            extraction = frozenset(union_set)
            req(len(extraction) >= MIN_SUPPORT and extraction.issubset(env), "invalid multicore union")
            if extraction != env:
                strict_shrink_parents += 1
            out = dict(parent)
            out.update({
                "core_event_ids": sorted(extraction),
                "core_member_count": len(extraction),
                "core_family_hash": member_hash(extraction),
                "multicore_branch_count": len(branch_rows),
                "multicore_branch_family_hashes": sorted(branch_hashes),
                "multicore_union_rule": "set_union_of_all_frozen_CMR_regrown_branches_for_parent",
            })
            rows.append(out)

        req([str(r["family_hash"]) for r in rows] == [str(p["family_hash"]) for p in parents], "envelope order drift")
        req(all(members(r) == members(p) for r, p in zip(rows, parents)), "envelope membership drift")
        k = int(s["equal_budget_k"])
        req(k > 0, "bad budget")
        env_sizes = [int(r["member_count"]) for r in rows[:k]]
        core_sizes = [int(r["core_member_count"]) for r in rows[:k]]
        env_top_all.extend(env_sizes)
        union_top_all.extend(core_sizes)
        top_budget_total_instances += len(core_sizes)
        top_budget_strict_shrink_instances += sum(c < e for c, e in zip(core_sizes, env_sizes))

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(s["event_count"]),
            "annual_event_ids": s["annual_event_ids"],
            "equal_budget_k": k,
            "envelope_core_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "top_budget_size": {
                "envelope_mean": mean(env_sizes),
                "core_mean": mean(core_sizes),
                "envelope_p90": q90(env_sizes),
                "core_p90": q90(core_sizes),
                "envelope_max": max(env_sizes),
                "core_max": max(core_sizes),
            },
        })

    size_summary = {
        "envelope_mean_top_budget_member_count": mean(env_top_all),
        "core_mean_top_budget_member_count": mean(union_top_all),
        "envelope_p90_top_budget_member_count": q90(env_top_all),
        "core_p90_top_budget_member_count": q90(union_top_all),
        "envelope_max_top_budget_member_count": max(env_top_all),
        "core_max_top_budget_member_count": max(union_top_all),
        "envelope_size_biased_top_budget_member_burden": burden(env_top_all),
        "core_size_biased_top_budget_member_burden": burden(union_top_all),
    }
    mechanism_summary = {
        "total_envelope_core_pairs": total_parents,
        "multi_branch_parent_count": multi_branch_parents,
        "strict_subset_core_pairs": strict_shrink_parents,
        "strict_subset_core_fraction": strict_shrink_parents / total_parents,
        "top_budget_total_instances": top_budget_total_instances,
        "top_budget_strict_subset_instances": top_budget_strict_shrink_instances,
        "top_budget_strict_subset_fraction": top_budget_strict_shrink_instances / top_budget_total_instances,
        "envelope_membership_changed_from_support_pruned": False,
        "envelope_ranking_changed_from_support_pruned": False,
    }
    structural_gates = {
        "mechanism_active": top_budget_strict_shrink_instances > 0 and strict_shrink_parents > 0,
        "core_mean_strictly_lower": size_summary["core_mean_top_budget_member_count"] < size_summary["envelope_mean_top_budget_member_count"],
        "core_p90_strictly_lower": size_summary["core_p90_top_budget_member_count"] < size_summary["envelope_p90_top_budget_member_count"],
        "core_max_strictly_lower": size_summary["core_max_top_budget_member_count"] < size_summary["envelope_max_top_budget_member_count"],
        "envelope_membership_unchanged": True,
        "envelope_ranking_unchanged": True,
    }

    out = {
        "schema": "ORBITTRACE_ENVELOPE_MULTICORE_UNION_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_EMCU_V1_HIERARCHICAL_CANDIDATES_FROZEN_BEFORE_CORE_TRUTH_TEST",
        "cmr_pretruth_sha256": CMR_PRETRUTH_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "envelope_detection_object": "exact_promoted_support_pruned_parent",
            "envelope_ranking": "exact_promoted_parent_M2D_order",
            "extraction_rule": "set_union_of_all_frozen_CMR_regrown_branches_for_parent",
            "core_replaces_envelope": False,
            "core_changes_envelope_rank": False,
            "branch_selection": "none_all_branches_included",
            "new_tuned_parameters": [],
        },
        "subsets": subsets,
        "size_summary": size_summary,
        "mechanism_summary": mechanism_summary,
        "structural_gates": structural_gates,
        "structural_pass": all(structural_gates.values()),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "GMN 2022/2023 is development-exposed. EMCU preserves the promoted discovery envelope exactly and uses every frozen CMR mode only for a separate deterministic extraction union. A GMN pass authorizes frozen SonotaCo transfer only.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"structural_pass": out["structural_pass"], "mechanism_summary": mechanism_summary, "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
