#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

BIF_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
BASELINE_M2D_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def membership(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    sets = [membership(r) for r in rows]
    return all(not a.intersection(b) for i, a in enumerate(sets) for b in sets[i + 1 :])


def internal_mass(srow: dict[str, Any], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    s = membership(srow)
    req(len(s) == int(srow["member_count"]) and len(s) >= MIN_SUPPORT, "bad refined membership")
    weighted = 0.0
    component_count = 0
    raw_area = 0.0
    for brow in bif_rows:
        b = membership(brow)
        req(len(b) == int(brow["member_count"]) and len(b) >= MIN_SUPPORT, "bad bif membership")
        area = float(brow["persistence_area"])
        req(area > 0.0, "nonpositive bif persistence area")
        if b.issubset(s):
            weighted += (len(b) / len(s)) * area
            raw_area += area
            component_count += 1
    return float(weighted), int(component_count), float(raw_area)


def p90(vals: list[int]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    # deterministic nearest-rank p90, no fitted parameter
    i = max(0, min(len(s) - 1, int((0.9 * len(s) + 0.999999999) // 1) - 1))
    return float(s[i])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--support-prelabel", type=Path, required=True)
    ap.add_argument("--bif-prelabel", type=Path, required=True)
    ap.add_argument("--baseline-m2d-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.bif_prelabel) == BIF_SHA, "bif prelabel changed")
    req(sha(a.baseline_m2d_prelabel) == BASELINE_M2D_SHA, "baseline M2D prelabel changed")
    support = json.loads(a.support_prelabel.read_text())
    bif = json.loads(a.bif_prelabel.read_text())
    base = json.loads(a.baseline_m2d_prelabel.read_text())
    req(support.get("schema") == "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SUPPORT_PRELABEL", "wrong refined support schema")
    req(support.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_CUT_V1", "wrong refined support role")
    req(support.get("shower_truth_used") is False and support.get("target_information_access") is False and support.get("target_region_events_accessed") is False, "refined support firewall")
    req(base.get("schema") == "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL", "wrong baseline schema")

    sm = {(int(s["denominator"]), int(s["bucket"])): s for s in support["subsets"]}
    bm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    om = {(int(s["denominator"]), int(s["bucket"])): s for s in base["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(sm) == set(bm) == set(om) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    all_ref_sizes: list[int] = []
    all_base_sizes: list[int] = []
    discarded_events = 0
    for key in sorted(keys):
        ss, bb, oo = sm[key], bm[key], om[key]
        support_rows = list(ss["successor_candidates"])
        bif_rows = list(bb["bifiltration_candidates"])
        baseline_rows = list(oo["successor_candidates"])
        k = int(oo["equal_budget_k"])
        req(k > 0 and len(baseline_rows) >= k and len(support_rows) >= k, f"capacity shortfall {key}")
        req(pairwise_disjoint(support_rows), f"refined overlap {key}")
        universe = set()
        for vals in bb["annual_event_ids"].values():
            universe.update(str(x) for x in vals)
        req(len(universe) == int(bb["event_count"]) == int(ss["events_total"]), f"universe count drift {key}")
        req(all(membership(r).issubset(universe) for r in support_rows), f"refined candidate outside universe {key}")

        enriched: list[dict[str, Any]] = []
        seen: set[frozenset[str]] = set()
        for row in support_rows:
            m = membership(row)
            req(m not in seen, f"duplicate refined membership {key}")
            seen.add(m)
            score, component_count, raw_area = internal_mass(row, bif_rows)
            out = dict(row)
            out["internal_2d_mass"] = score
            out["internal_bif_component_count"] = component_count
            out["internal_bif_raw_area_sum"] = raw_area
            enriched.append(out)
        enriched.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
        for rank, row in enumerate(enriched, 1):
            row["internal_mass_rank"] = rank
        req(pairwise_disjoint(enriched), f"ranked refined overlap {key}")

        ref_top = enriched[:k]
        base_top = baseline_rows[:k]
        ref_sizes = [int(r["member_count"]) for r in ref_top]
        base_sizes = [int(r["member_count"]) for r in base_top]
        all_ref_sizes.extend(ref_sizes)
        all_base_sizes.extend(base_sizes)
        cs = dict(ss.get("cut_summary", {}))
        discarded_events += int(cs.get("discarded_subsupport_event_count", 0))
        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(bb["event_count"]),
            "annual_event_ids": bb["annual_event_ids"],
            "equal_budget_k": k,
            "refined_candidates": enriched,
            "baseline_candidates": baseline_rows,
            "refined_cut_summary": cs,
            "top_budget_size": {
                "refined_mean": mean(ref_sizes),
                "baseline_mean": mean(base_sizes),
                "refined_p90": p90(ref_sizes),
                "baseline_p90": p90(base_sizes),
                "refined_max": max(ref_sizes),
                "baseline_max": max(base_sizes),
            },
        })

    size_summary = {
        "refined_mean_top_budget_member_count": mean(all_ref_sizes),
        "baseline_mean_top_budget_member_count": mean(all_base_sizes),
        "refined_p90_top_budget_member_count": p90(all_ref_sizes),
        "baseline_p90_top_budget_member_count": p90(all_base_sizes),
        "refined_max_top_budget_member_count": max(all_ref_sizes),
        "baseline_max_top_budget_member_count": max(all_base_sizes),
        "discarded_subsupport_events_across_sparse_fits": int(discarded_events),
    }
    payload = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_RANKING_FROZEN_BEFORE_TRUTH",
        "configuration": {
            "cut_rule": "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport",
            "radius": 1.0,
            "minimum_support": 4,
            "m2d_formula": "M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)",
            "ranking": ["internal_2d_mass_desc", "modal_contrast_desc", "family_hash_asc"],
            "budget": "exact frozen baseline M2D equal_budget_k per sparse panel",
            "new_tuned_parameters": [],
        },
        "baseline_m2d_prelabel_sha256": BASELINE_M2D_SHA,
        "bif_prelabel_sha256": BIF_SHA,
        "support_prelabel_sha256": sha(a.support_prelabel),
        "subsets": subsets,
        "size_summary": size_summary,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH", "size_summary": size_summary, "sha256": sha(a.output)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
