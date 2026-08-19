#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

DCR_PRETRUTH_SHA = "92e91dfa5fc8557f26d4be0238b3379e49c0845513e7f3e0e9ffc471343813c5"
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
    ap.add_argument("--dcr-pretruth", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.dcr_pretruth) == DCR_PRETRUTH_SHA, "frozen DCR pretruth changed")
    dcr = json.loads(a.dcr_pretruth.read_text())
    req(dcr.get("schema") == "ORBITTRACE_DOMINANT_CORE_REGROWTH_V1_PRETRUTH", "wrong DCR schema")
    req(dcr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned source changed")
    req(
        dcr.get("target_information_access") is False
        and dcr.get("target_region_events_accessed") is False
        and dcr.get("orbittrace_reveal_access") is False
        and dcr.get("sonotaco_scientific_access") is False,
        "DCR source firewall failed",
    )

    smap = {(int(s["denominator"]), int(s["bucket"])): s for s in dcr["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(smap) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    padcr_top_sizes_all: list[int] = []
    baseline_top_sizes_all: list[int] = []
    refined_top_instances = 0
    total_top_instances = 0
    identity_order_checks = 0

    for key in sorted(keys):
        s = smap[key]
        parents = list(s["support_pruned_baseline_candidates"])
        dcr_rows = list(s["dcr_candidates"])
        req(parents and dcr_rows and len(parents) == len(dcr_rows), "catalogue cardinality changed")
        by_parent = {str(r["dcr_parent_family_hash"]): r for r in dcr_rows}
        req(len(by_parent) == len(dcr_rows), "duplicate DCR parent mapping")
        req(set(by_parent) == {str(p["family_hash"]) for p in parents}, "DCR parent coverage changed")

        rows: list[dict[str, Any]] = []
        for parent_rank, parent in enumerate(parents, 1):
            ph = str(parent["family_hash"])
            child = by_parent[ph]
            req(int(parent["internal_mass_rank"]) == parent_rank, "support parent M2D rank drift")
            row = dict(child)
            row["padcr_detection_parent_family_hash"] = ph
            row["padcr_detection_parent_rank"] = parent_rank
            row["padcr_detection_parent_m2d"] = float(parent["internal_2d_mass"])
            row["padcr_extraction_membership_m2d"] = float(child["internal_2d_mass"])
            row["padcr_ranking_rule"] = "exact promoted support-pruned parent M2D order"
            row["internal_mass_rank"] = parent_rank
            row["rank"] = parent_rank
            rows.append(row)
            identity_order_checks += int(str(row["dcr_parent_family_hash"]) == ph)

        k = int(s["equal_budget_k"])
        req(k > 0 and len(rows) >= k, "capacity changed")
        padcr_sizes = [int(r["member_count"]) for r in rows[:k]]
        base_sizes = [int(r["member_count"]) for r in parents[:k]]
        padcr_top_sizes_all.extend(padcr_sizes)
        baseline_top_sizes_all.extend(base_sizes)
        refined_top_instances += sum(str(r["dcr_source"]) == "STRICT_MAJORITY_BWM_SEED_CMR_REGROWTH" for r in rows[:k])
        total_top_instances += k

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(s["event_count"]),
            "annual_event_ids": s["annual_event_ids"],
            "equal_budget_k": k,
            "padcr_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "capacity": {"padcr_available": len(rows), "support_pruned_available": len(parents), "budget_k": k},
            "top_budget_size": {
                "padcr_mean": mean(padcr_sizes),
                "support_pruned_mean": mean(base_sizes),
                "padcr_p90": q90(padcr_sizes),
                "support_pruned_p90": q90(base_sizes),
                "padcr_max": max(padcr_sizes),
                "support_pruned_max": max(base_sizes),
                "padcr_burden": burden(padcr_sizes),
                "support_pruned_burden": burden(base_sizes),
            },
        })

    size_summary = {
        "padcr_mean_top_budget_member_count": mean(padcr_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(baseline_top_sizes_all),
        "padcr_p90_top_budget_member_count": q90(padcr_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(baseline_top_sizes_all),
        "padcr_max_top_budget_member_count": max(padcr_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(baseline_top_sizes_all),
        "padcr_size_biased_top_budget_member_burden": burden(padcr_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(baseline_top_sizes_all),
    }
    mechanism_summary = {
        "catalogue_parent_count": sum(len(s["support_pruned_baseline_candidates"]) for s in dcr["subsets"]),
        "identity_order_checks": identity_order_checks,
        "top_budget_refined_instances": refined_top_instances,
        "top_budget_total_instances": total_top_instances,
        "top_budget_refined_fraction": refined_top_instances / total_top_instances,
        "ranking_changed_from_support_pruned": False,
        "memberships_changed_from_dcr": False,
    }
    structural_gates = {
        "mechanism_active_in_top_budget": refined_top_instances > 0,
        "mean_size_strictly_lower_than_support_pruned": size_summary["padcr_mean_top_budget_member_count"] < size_summary["support_pruned_mean_top_budget_member_count"],
        "p90_size_strictly_lower_than_support_pruned": size_summary["padcr_p90_top_budget_member_count"] < size_summary["support_pruned_p90_top_budget_member_count"],
        "max_size_strictly_lower_than_support_pruned": size_summary["padcr_max_top_budget_member_count"] < size_summary["support_pruned_max_top_budget_member_count"],
        "size_biased_burden_strictly_lower_than_support_pruned": size_summary["padcr_size_biased_top_budget_member_burden"] < size_summary["support_pruned_size_biased_top_budget_member_burden"],
    }
    structural_pass = all(structural_gates.values())

    out = {
        "schema": "ORBITTRACE_PARENT_ANCHORED_DCR_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_PADCR_V1_DEVELOPMENT_RANKING",
        "development_status": "GMN_2022_2023_EXPOSED_DEVELOPMENT_AFTER_DCR; NON_GMN_TRANSFER_REQUIRED_FOR_GENERALIZATION",
        "dcr_pretruth_sha256": DCR_PRETRUTH_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "membership_rule": "exact frozen DCR v1 membership for each support-pruned parent",
            "ranking_rule": "exact promoted support-pruned parent M2D order; child M2D cannot change discovery rank",
            "one_candidate_per_parent": True,
            "new_tuned_parameters": [],
        },
        "mechanism_summary": mechanism_summary,
        "size_summary": size_summary,
        "structural_gates": structural_gates,
        "structural_pass": structural_pass,
        "subsets": subsets,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "PADCR v1 is a direct ablation of the frozen DCR failure: memberships are identical to DCR, while discovery ordering is restored exactly to promoted support-pruned M2D. GMN is exposed development evidence only.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"structural_pass": structural_pass, "mechanism_summary": mechanism_summary, "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
