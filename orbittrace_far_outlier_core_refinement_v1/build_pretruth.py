#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

CMR_PRETRUTH_SHA = "8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb"
SUPPORT_PRUNED_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
OUTER_FENCE_MULTIPLIER = 3.0


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mhash(row: dict[str, Any]) -> str:
    return str(row["family_hash"])


def q90(values: list[int]) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), 0.90))


def burden(values: list[int]) -> float:
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
    req(cmr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support parent identity changed")
    req(
        cmr.get("target_information_access") is False
        and cmr.get("target_region_events_accessed") is False
        and cmr.get("orbittrace_reveal_access") is False
        and cmr.get("sonotaco_scientific_access") is False,
        "CMR firewall changed",
    )

    smap = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(smap) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    focr_top_sizes_all: list[int] = []
    support_top_sizes_all: list[int] = []
    cmr_top_sizes_all: list[int] = []
    refined_parent_count = 0
    retained_parent_count = 0
    refined_candidate_count = 0

    for key in sorted(keys):
        s = smap[key]
        parents = list(s["support_pruned_baseline_candidates"])
        cmr_candidates = list(s["cmr_candidates"])
        req(parents and cmr_candidates, "empty candidate catalogue")
        pmap = {mhash(p): p for p in parents}
        req(len(pmap) == len(parents), "duplicate parent hash")
        by_parent: dict[str, list[dict[str, Any]]] = {ph: [] for ph in pmap}
        for row in cmr_candidates:
            ph = str(row["cmr_parent_family_hash"])
            req(ph in by_parent, "CMR parent missing")
            by_parent[ph].append(row)
        req(all(by_parent.values()), "parent lacks CMR representation")

        parent_sizes = np.asarray([int(p["member_count"]) for p in parents], dtype=float)
        q1, q3 = np.quantile(parent_sizes, [0.25, 0.75])
        iqr = float(q3 - q1)
        fence = float(q3 + OUTER_FENCE_MULTIPLIER * iqr)
        req(np.isfinite(fence) and fence >= q3, "bad Tukey outer fence")

        rows: list[dict[str, Any]] = []
        refined_hashes: list[str] = []
        retained_hashes: list[str] = []
        for parent in parents:
            ph = mhash(parent)
            if int(parent["member_count"]) > fence:
                refined_parent_count += 1
                refined_hashes.append(ph)
                kids = by_parent[ph]
                refined_candidate_count += len(kids)
                for child in kids:
                    out = dict(child)
                    out["focr_source"] = "CMR_OUTER_FENCE_REFINEMENT"
                    out["focr_parent_family_hash"] = ph
                    out["focr_parent_member_count"] = int(parent["member_count"])
                    out["focr_outer_fence"] = fence
                    rows.append(out)
            else:
                retained_parent_count += 1
                retained_hashes.append(ph)
                out = dict(parent)
                out["focr_source"] = "SUPPORT_PRUNED_PARENT_RETAINED"
                out["focr_parent_family_hash"] = ph
                out["focr_parent_member_count"] = int(parent["member_count"])
                out["focr_outer_fence"] = fence
                rows.append(out)

        memberships = [tuple(map(str, r["event_ids"])) for r in rows]
        req(len(memberships) == len(set(memberships)), f"duplicate FOCR membership {key}")
        rows.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
        for rank, row in enumerate(rows, 1):
            row["internal_mass_rank"] = rank
            row["rank"] = rank

        k = int(s["equal_budget_k"])
        req(k > 0, "bad budget")
        focr_top = rows[:k]
        support_top = parents[:k]
        cmr_top = cmr_candidates[:k]
        req(focr_top and support_top and cmr_top, "empty top budget")
        fs = [int(r["member_count"]) for r in focr_top]
        ss = [int(r["member_count"]) for r in support_top]
        cs = [int(r["member_count"]) for r in cmr_top]
        focr_top_sizes_all.extend(fs)
        support_top_sizes_all.extend(ss)
        cmr_top_sizes_all.extend(cs)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(s["event_count"]),
            "annual_event_ids": s["annual_event_ids"],
            "equal_budget_k": k,
            "tukey": {
                "q1": float(q1),
                "q3": float(q3),
                "iqr": iqr,
                "outer_fence_multiplier": OUTER_FENCE_MULTIPLIER,
                "outer_upper_fence": fence,
            },
            "refined_parent_hashes": sorted(refined_hashes),
            "retained_parent_hashes": sorted(retained_hashes),
            "focr_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "cmr_reference_candidates": cmr_candidates,
            "capacity": {
                "focr_available": len(rows),
                "support_pruned_available": len(parents),
                "cmr_available": len(cmr_candidates),
                "budget_k": k,
            },
            "top_budget_size": {
                "focr_mean": mean(fs),
                "support_pruned_mean": mean(ss),
                "cmr_mean": mean(cs),
                "focr_p90": q90(fs),
                "support_pruned_p90": q90(ss),
                "cmr_p90": q90(cs),
                "focr_max": max(fs),
                "support_pruned_max": max(ss),
                "cmr_max": max(cs),
            },
        })

    size_summary = {
        "focr_mean_top_budget_member_count": mean(focr_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(support_top_sizes_all),
        "cmr_mean_top_budget_member_count": mean(cmr_top_sizes_all),
        "focr_p90_top_budget_member_count": q90(focr_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(support_top_sizes_all),
        "cmr_p90_top_budget_member_count": q90(cmr_top_sizes_all),
        "focr_max_top_budget_member_count": max(focr_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(support_top_sizes_all),
        "cmr_max_top_budget_member_count": max(cmr_top_sizes_all),
        "focr_size_biased_top_budget_member_burden": burden(focr_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(support_top_sizes_all),
        "cmr_size_biased_top_budget_member_burden": burden(cmr_top_sizes_all),
    }
    structural_gates = {
        "refinement_active": refined_parent_count > 0,
        "refinement_selective": 0 < refined_parent_count < (refined_parent_count + retained_parent_count),
        "mean_below_support_pruned": size_summary["focr_mean_top_budget_member_count"] < size_summary["support_pruned_mean_top_budget_member_count"],
        "p90_below_support_pruned": size_summary["focr_p90_top_budget_member_count"] < size_summary["support_pruned_p90_top_budget_member_count"],
        "max_below_support_pruned": size_summary["focr_max_top_budget_member_count"] < size_summary["support_pruned_max_top_budget_member_count"],
    }
    out = {
        "schema": "ORBITTRACE_FAR_OUTLIER_CORE_REFINEMENT_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_FOCR_V1_DEVELOPMENT_RANKING",
        "development_status": "DESIGNED_AFTER_BWM_AND_CMR_GMN_DEVELOPMENT_RESULTS; GMN_IS_NOT_UNTOUCHED_VALIDATION",
        "configuration": {
            "outer_fence": "Q3 + 3*IQR",
            "quantile_method": "numpy_default_linear",
            "refinement_memberships": "frozen CMR v1 children",
            "retained_memberships": "promoted support-pruned v1 parents",
            "ranking": "exact M2D descending, then membership hash",
            "new_tuned_parameters": [],
        },
        "cmr_pretruth_sha256": CMR_PRETRUTH_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "mechanism_summary": {
            "refined_parent_count": refined_parent_count,
            "retained_parent_count": retained_parent_count,
            "refined_candidate_count": refined_candidate_count,
            "total_parent_count": refined_parent_count + retained_parent_count,
        },
        "size_summary": size_summary,
        "structural_gates": structural_gates,
        "structural_pass": all(structural_gates.values()),
        "subsets": subsets,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "interpretation_boundary": "FOCR is a post-BWM/CMR GMN development successor. GMN quality results are development evidence only. OrbitTrace protected-region information and SonotaCo truth are excluded from construction; any generalization claim requires frozen transfer.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"mechanism_summary": out["mechanism_summary"], "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    print("PASS_FOCR_V1_STRUCTURE" if out["structural_pass"] else "FAIL_FOCR_V1_STRUCTURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
