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

CMR_PRETRUTH_SHA = "8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb"
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
    return hashlib.sha256(("DCR1|" + "\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmr-pretruth", type=Path, required=True)
    ap.add_argument("--bif-endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.cmr_pretruth) == CMR_PRETRUTH_SHA, "frozen CMR pretruth changed")
    req(sha(a.bif_endpoint_prelabel) == BIF_ENDPOINT_SHA, "frozen bifiltration endpoint changed")
    cmr = json.loads(a.cmr_pretruth.read_text())
    bif = json.loads(a.bif_endpoint_prelabel.read_text())

    req(cmr.get("schema") == "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_PRETRUTH", "wrong CMR schema")
    req(cmr.get("scientific_role") == "TARGET_EXCLUDED_GMN_CMR_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH", "wrong CMR role")
    req(cmr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned source changed")
    req(
        cmr.get("shower_truth_used") is False
        and cmr.get("target_information_access") is False
        and cmr.get("target_region_events_accessed") is False
        and cmr.get("orbittrace_reveal_access") is False
        and cmr.get("sonotaco_scientific_access") is False,
        "CMR source firewall failed",
    )
    req(bif.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong bif schema")
    req(
        bif.get("shower_truth_used") is False
        and bif.get("target_information_access") is False
        and bif.get("target_region_events_accessed") is False
        and bif.get("sonotaco_2013_2014_access") is False,
        "bif source firewall failed",
    )

    cm = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    fm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(cm) == set(fm) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    dcr_top_sizes_all: list[int] = []
    cmr_top_sizes_all: list[int] = []
    baseline_top_sizes_all: list[int] = []
    total_parent_count = 0
    dominant_parent_count = 0
    refined_parent_count = 0
    dominant_unchanged_count = 0
    retained_parent_count = 0
    retained_fraction_values: list[float] = []

    for key in sorted(keys):
        cs, fs = cm[key], fm[key]
        req(int(cs["event_count"]) == int(fs["event_count"]), f"event count mismatch {key}")
        req(
            {str(y): list(map(str, cs["annual_event_ids"][str(y)])) for y in (2022, 2023)}
            == {str(y): list(map(str, fs["annual_event_ids"][str(y)])) for y in (2022, 2023)},
            f"annual universe mismatch {key}",
        )
        bif_rows = list(fs["bifiltration_candidates"])
        parents = list(cs["support_pruned_baseline_candidates"])
        seeds = list(cs["bwm_seed_candidates"])
        cmr_candidates = list(cs["cmr_candidates"])
        req(parents and seeds and cmr_candidates, "empty source catalogue")

        pmap = {str(p["family_hash"]): p for p in parents}
        req(len(pmap) == len(parents), "duplicate parent hash")
        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for seed in seeds:
            ph = str(seed["bwm_parent_family_hash"])
            req(ph in pmap, "BWM seed parent missing")
            by_parent[ph].append(seed)
        req(set(by_parent) == set(pmap), "BWM parent coverage changed")
        cmr_by_seed = {str(c["cmr_seed_family_hash"]): c for c in cmr_candidates}
        req(len(cmr_by_seed) == len(cmr_candidates), "CMR seed mapping not one-to-one")
        req(set(cmr_by_seed) == {str(s["family_hash"]) for s in seeds}, "CMR/BWM seed set changed")

        rows: list[dict[str, Any]] = []
        panel_dominant = 0
        panel_refined = 0
        panel_retained = 0
        panel_dominant_unchanged = 0

        for ph, parent in pmap.items():
            total_parent_count += 1
            parent_set = members(parent)
            parent_n = len(parent_set)
            req(parent_n == int(parent["member_count"]), "parent size mismatch")
            seed_rows = by_parent[ph]
            dominant = [s for s in seed_rows if 2 * int(s["member_count"]) > parent_n]
            req(len(dominant) <= 1, "more than one strict-majority seed")

            source = "SUPPORT_PRUNED_PARENT_RETAINED"
            dominant_seed_hash: str | None = None
            dominant_seed_member_count: int | None = None
            if dominant:
                panel_dominant += 1
                dominant_parent_count += 1
                seed = dominant[0]
                dominant_seed_hash = str(seed["family_hash"])
                dominant_seed_member_count = int(seed["member_count"])
                chosen = cmr_by_seed[dominant_seed_hash]
                chosen_set = members(chosen)
                req(chosen_set.issubset(parent_set), "dominant CMR child escaped parent")
                req(int(chosen["cmr_parent_member_count"]) == parent_n, "CMR parent size mismatch")
                req(str(chosen["cmr_parent_family_hash"]) == ph, "CMR parent hash mismatch")
                req(str(chosen["cmr_seed_family_hash"]) == dominant_seed_hash, "CMR seed hash mismatch")
                req(2 * dominant_seed_member_count > parent_n, "dominance rule changed")
                if chosen_set != parent_set:
                    source = "STRICT_MAJORITY_BWM_SEED_CMR_REGROWTH"
                    panel_refined += 1
                    refined_parent_count += 1
                    retained_fraction_values.append(len(chosen_set) / parent_n)
                else:
                    panel_dominant_unchanged += 1
                    dominant_unchanged_count += 1
            else:
                chosen_set = parent_set

            if chosen_set == parent_set:
                panel_retained += 1
                retained_parent_count += 1

            score, count, raw_area = exact_m2d(chosen_set, bif_rows)
            rows.append({
                "family_id": family_id(chosen_set),
                "family_hash": member_hash(chosen_set),
                "event_ids": sorted(chosen_set),
                "member_count": len(chosen_set),
                "internal_2d_mass": score,
                "internal_bif_component_count": count,
                "internal_bif_raw_area_sum": raw_area,
                "dcr_parent_family_hash": ph,
                "dcr_parent_member_count": parent_n,
                "dcr_source": source,
                "dcr_dominant_seed_family_hash": dominant_seed_hash,
                "dcr_dominant_seed_member_count": dominant_seed_member_count,
                "dcr_strict_majority_seed_rule": True,
                "dcr_uses_frozen_cmr_membership": bool(source == "STRICT_MAJORITY_BWM_SEED_CMR_REGROWTH"),
            })

        req(len(rows) == len(parents), "DCR must emit exactly one candidate per support-pruned parent")
        req(len({tuple(r["event_ids"]) for r in rows}) == len(rows), "unexpected duplicate DCR memberships")
        rows.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
        for rank, row in enumerate(rows, 1):
            row["internal_mass_rank"] = rank
            row["rank"] = rank

        k = int(cs["equal_budget_k"])
        req(k > 0 and len(rows) >= min(k, len(parents)), "DCR capacity collapsed")
        dcr_sizes = [int(r["member_count"]) for r in rows[:k]]
        cmr_sizes = [int(r["member_count"]) for r in cmr_candidates[:k]]
        base_sizes = [int(r["member_count"]) for r in parents[:k]]
        dcr_top_sizes_all.extend(dcr_sizes)
        cmr_top_sizes_all.extend(cmr_sizes)
        baseline_top_sizes_all.extend(base_sizes)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(cs["event_count"]),
            "annual_event_ids": cs["annual_event_ids"],
            "equal_budget_k": k,
            "dcr_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "cmr_reference_candidates": cmr_candidates,
            "bwm_seed_reference_candidates": seeds,
            "mechanism": {
                "parent_count": len(parents),
                "strict_majority_seed_parents": panel_dominant,
                "refined_parents": panel_refined,
                "dominant_but_membership_unchanged": panel_dominant_unchanged,
                "retained_parents": panel_retained,
            },
            "capacity": {
                "dcr_available": len(rows),
                "support_pruned_available": len(parents),
                "cmr_available": len(cmr_candidates),
                "budget_k": k,
            },
            "top_budget_size": {
                "dcr_mean": mean(dcr_sizes),
                "support_pruned_mean": mean(base_sizes),
                "cmr_mean": mean(cmr_sizes),
                "dcr_p90": q90(dcr_sizes),
                "support_pruned_p90": q90(base_sizes),
                "cmr_p90": q90(cmr_sizes),
                "dcr_max": max(dcr_sizes),
                "support_pruned_max": max(base_sizes),
                "cmr_max": max(cmr_sizes),
                "dcr_burden": burden(dcr_sizes),
                "support_pruned_burden": burden(base_sizes),
                "cmr_burden": burden(cmr_sizes),
            },
        })

    size_summary = {
        "dcr_mean_top_budget_member_count": mean(dcr_top_sizes_all),
        "cmr_mean_top_budget_member_count": mean(cmr_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(baseline_top_sizes_all),
        "dcr_p90_top_budget_member_count": q90(dcr_top_sizes_all),
        "cmr_p90_top_budget_member_count": q90(cmr_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(baseline_top_sizes_all),
        "dcr_max_top_budget_member_count": max(dcr_top_sizes_all),
        "cmr_max_top_budget_member_count": max(cmr_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(baseline_top_sizes_all),
        "dcr_size_biased_top_budget_member_burden": burden(dcr_top_sizes_all),
        "cmr_size_biased_top_budget_member_burden": burden(cmr_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(baseline_top_sizes_all),
    }
    mechanism_summary = {
        "total_parent_count": total_parent_count,
        "strict_majority_seed_parent_count": dominant_parent_count,
        "refined_parent_count": refined_parent_count,
        "dominant_but_membership_unchanged_count": dominant_unchanged_count,
        "retained_parent_count": retained_parent_count,
        "refined_mean_retained_fraction": mean(retained_fraction_values) if retained_fraction_values else None,
        "refined_min_retained_fraction": min(retained_fraction_values) if retained_fraction_values else None,
    }
    structural_gates = {
        "mechanism_active": refined_parent_count > 0,
        "mean_size_strictly_lower_than_support_pruned": size_summary["dcr_mean_top_budget_member_count"] < size_summary["support_pruned_mean_top_budget_member_count"],
        "p90_size_strictly_lower_than_support_pruned": size_summary["dcr_p90_top_budget_member_count"] < size_summary["support_pruned_p90_top_budget_member_count"],
        "max_size_strictly_lower_than_support_pruned": size_summary["dcr_max_top_budget_member_count"] < size_summary["support_pruned_max_top_budget_member_count"],
        "size_biased_burden_strictly_lower_than_support_pruned": size_summary["dcr_size_biased_top_budget_member_burden"] < size_summary["support_pruned_size_biased_top_budget_member_burden"],
    }
    structural_pass = all(structural_gates.values())

    out = {
        "schema": "ORBITTRACE_DOMINANT_CORE_REGROWTH_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_DCR_V1_DEVELOPMENT_RANKING",
        "development_status": "GMN_2022_2023_EXPOSED_DEVELOPMENT_AFTER_BWM_CMR_FOCR; NON_GMN_TRANSFER_REQUIRED_FOR_GENERALIZATION",
        "cmr_pretruth_sha256": CMR_PRETRUTH_SHA,
        "bif_endpoint_prelabel_sha256": BIF_ENDPOINT_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "selector": "refine iff exactly one frozen BWM seed has strict member majority within its support-pruned parent",
            "dominance_rule": "2 * seed_member_count > parent_member_count",
            "refinement_membership": "exact already-frozen CMR v1 regrowth associated with the dominant BWM seed",
            "fallback_membership": "exact promoted support-pruned parent",
            "one_candidate_per_parent": True,
            "ranking": "exact M2D descending, then membership hash",
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
        "interpretation_boundary": "DCR v1 is designed after BWM, CMR, and FOCR GMN development outcomes were observed. GMN 2022/2023 is development evidence only; any pass must transfer frozen to non-GMN data before generalization or OrbitTrace characterization.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"structural_pass": structural_pass, "mechanism_summary": mechanism_summary, "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
