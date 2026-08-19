#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

BIF_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
SUPPORT_PRUNED_PRETRUTH_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
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


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    sets = [members(r) for r in rows]
    return all(not a.intersection(b) for i, a in enumerate(sets) for b in sets[i + 1 :])


def internal_mass(row: dict[str, Any], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    s = members(row)
    req(len(s) == int(row["member_count"]) and len(s) >= MIN_SUPPORT, "bad LRB membership")
    weighted = 0.0
    component_count = 0
    raw_area = 0.0
    for brow in bif_rows:
        b = members(brow)
        area = float(brow["persistence_area"])
        req(len(b) == int(brow["member_count"]) >= MIN_SUPPORT and area > 0.0, "bad bif component")
        if b.issubset(s):
            weighted += (len(b) / len(s)) * area
            raw_area += area
            component_count += 1
    return float(weighted), int(component_count), float(raw_area)


def nearest_rank_p90(vals: list[int]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    i = max(0, min(len(s) - 1, int((0.9 * len(s) + 0.999999999) // 1) - 1))
    return float(s[i])


def size_biased_burden(vals: list[int]) -> float:
    req(bool(vals) and all(v > 0 for v in vals), "bad size list")
    return float(sum(v * v for v in vals) / sum(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lrb-prelabel", type=Path, required=True)
    ap.add_argument("--bif-prelabel", type=Path, required=True)
    ap.add_argument("--support-pruned-pretruth", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.bif_prelabel) == BIF_SHA, "bif prelabel changed")
    req(sha(a.support_pruned_pretruth) == SUPPORT_PRUNED_PRETRUTH_SHA, "support-pruned baseline pretruth changed")
    pre = json.loads(a.lrb_prelabel.read_text())
    bif = json.loads(a.bif_prelabel.read_text())
    base = json.loads(a.support_pruned_pretruth.read_text())
    req(pre.get("schema") == "ORBITTRACE_LOCAL_RENORMALIZED_BASIN_V1_PRELABEL", "wrong LRB prelabel schema")
    req(pre.get("scientific_role") == "TARGET_EXCLUDED_GMN_LOCAL_RENORMALIZED_BASIN_V1_FROZEN_BEFORE_M2D_AND_TRUTH", "wrong LRB prelabel role")
    req(pre.get("shower_truth_used") is False and pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False and pre.get("orbittrace_reveal_access") is False, "LRB prelabel firewall")
    req(base.get("schema") == "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH", "wrong support-pruned baseline schema")
    req(base.get("shower_truth_used") is False and base.get("orbittrace_reveal_access") is False, "support-pruned baseline firewall")

    pm = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    bm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    om = {(int(s["denominator"]), int(s["bucket"])): s for s in base["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(pm) == set(bm) == set(om) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    lrb_sizes_all: list[int] = []
    base_sizes_all: list[int] = []
    for key in sorted(keys):
        pp, bb, oo = pm[key], bm[key], om[key]
        rows = list(pp["lrb_candidates"])
        bif_rows = list(bb["bifiltration_candidates"])
        baseline_rows = list(oo["refined_candidates"])
        k = int(oo["equal_budget_k"])
        req(k == int(pp["equal_budget_k"]) > 0, f"budget drift {key}")
        req(pairwise_disjoint(rows), f"LRB overlap {key}")
        universe = set()
        for vals in pp["annual_event_ids"].values():
            universe.update(str(x) for x in vals)
        req(len(universe) == int(pp["event_count"]), f"universe drift {key}")
        req(all(members(r).issubset(universe) for r in rows), f"LRB outside universe {key}")

        enriched: list[dict[str, Any]] = []
        seen: set[frozenset[str]] = set()
        for row in rows:
            m = members(row)
            req(m not in seen, f"duplicate LRB membership {key}")
            seen.add(m)
            score, count, raw_area = internal_mass(row, bif_rows)
            out = dict(row)
            out["internal_2d_mass"] = score
            out["internal_bif_component_count"] = count
            out["internal_bif_raw_area_sum"] = raw_area
            enriched.append(out)
        enriched.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
        for rank, row in enumerate(enriched, 1):
            row["internal_mass_rank"] = rank

        ltop = enriched[:k]
        btop = baseline_rows[:k]
        ls = [int(r["member_count"]) for r in ltop]
        bs = [int(r["member_count"]) for r in btop]
        req(bool(ls) and bool(bs), f"empty top budget {key}")
        lrb_sizes_all.extend(ls)
        base_sizes_all.extend(bs)
        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(pp["event_count"]),
            "annual_event_ids": pp["annual_event_ids"],
            "equal_budget_k": k,
            "lrb_candidates": enriched,
            "support_pruned_baseline_candidates": baseline_rows,
            "lrb_summary": pp["lrb_summary"],
            "capacity": {"lrb_available": len(enriched), "baseline_available": len(baseline_rows), "budget_k": k},
            "top_budget_size": {
                "lrb_mean": mean(ls),
                "baseline_mean": mean(bs),
                "lrb_p90": nearest_rank_p90(ls),
                "baseline_p90": nearest_rank_p90(bs),
                "lrb_max": max(ls),
                "baseline_max": max(bs),
                "lrb_size_biased_burden": size_biased_burden(ls),
                "baseline_size_biased_burden": size_biased_burden(bs),
            },
        })

    size = {
        "lrb_mean_top_budget_member_count": mean(lrb_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(base_sizes_all),
        "lrb_p90_top_budget_member_count": nearest_rank_p90(lrb_sizes_all),
        "support_pruned_p90_top_budget_member_count": nearest_rank_p90(base_sizes_all),
        "lrb_max_top_budget_member_count": max(lrb_sizes_all),
        "support_pruned_max_top_budget_member_count": max(base_sizes_all),
        "lrb_size_biased_top_budget_member_burden": size_biased_burden(lrb_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": size_biased_burden(base_sizes_all),
    }
    payload = {
        "schema": "ORBITTRACE_LOCAL_RENORMALIZED_BASIN_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_LRB_V1_M2D_RANKING_FROZEN_BEFORE_TRUTH",
        "configuration": {
            "parent": "promoted_support_pruned_m2d_v1",
            "radius": 1.0,
            "minimum_support": 4,
            "local_passes": 1,
            "replacement_rule": "replace_parent_iff_local_support_pruned_pass_has_at_least_two_reportable_candidates",
            "m2d_formula": "M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)",
            "ranking": ["internal_2d_mass_desc", "globalized_modal_contrast_desc", "family_hash_asc"],
            "budget": "exact support-pruned frozen equal_budget_k; shortfall scored, never padded",
            "new_tuned_parameters": [],
        },
        "lrb_prelabel_sha256": sha(a.lrb_prelabel),
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_PRETRUTH_SHA,
        "bif_prelabel_sha256": BIF_SHA,
        "mechanism_summary": pre["mechanism_summary"],
        "subsets": subsets,
        "size_summary": size,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_LRB_V1_PRETRUTH", "sha256": sha(a.output), "mechanism_summary": payload["mechanism_summary"], "size_summary": size, "capacities": [{"d":s["denominator"],"b":s["bucket"],**s["capacity"]} for s in subsets]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
