#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SUPPORT_SHA = "4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6"
BIF_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def membership(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def support_membership_hash(row: dict[str, Any]) -> str:
    # Support-cut family_hash is inherited; identity is verified by exact event tuple uniqueness instead.
    return hashlib.sha256(("\n".join(sorted(str(x) for x in row["event_ids"])) + "\n").encode()).hexdigest()


def internal_mass(srow: dict[str, Any], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    s = membership(srow)
    req(len(s) == int(srow["member_count"]) and len(s) >= MIN_SUPPORT, "bad support-cut membership")
    weighted = 0.0
    component_count = 0
    raw_area = 0.0
    for brow in bif_rows:
        b = membership(brow)
        req(len(b) == int(brow["member_count"]) and len(b) >= MIN_SUPPORT, "bad bifiltration membership")
        area = float(brow["persistence_area"])
        req(area > 0.0, "nonpositive bifiltration persistence area")
        if b.issubset(s):
            weighted += (len(b) / len(s)) * area
            raw_area += area
            component_count += 1
    return float(weighted), int(component_count), float(raw_area)


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    sets = [membership(r) for r in rows]
    return all(not a.intersection(b) for i, a in enumerate(sets) for b in sets[i + 1 :])


def restrict_and_dedupe(rows: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    seen: set[frozenset[str]] = set()
    out: list[frozenset[str]] = []
    for row in rows:
        s = frozenset(x for x in membership(row) if x in universe)
        if len(s) < MIN_SUPPORT or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def mean_best_jaccard(fine_rows: list[dict[str, Any]], coarse_rows: list[dict[str, Any]], fine_universe: set[str]) -> float:
    fine = [membership(r) for r in fine_rows]
    coarse = restrict_and_dedupe(coarse_rows, fine_universe)
    if not fine:
        return 0.0
    vals: list[float] = []
    for a in fine:
        best = 0.0
        for b in coarse:
            inter = len(a.intersection(b))
            if inter:
                best = max(best, inter / len(a.union(b)))
        vals.append(float(best))
    return float(sum(vals) / len(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--support-prelabel", type=Path, required=True)
    ap.add_argument("--bif-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.support_prelabel) == SUPPORT_SHA, "support-cut prelabel changed")
    req(sha256(a.bif_prelabel) == BIF_SHA, "bifiltration prelabel changed")
    support = json.loads(a.support_prelabel.read_text())
    bif = json.loads(a.bif_prelabel.read_text())
    req(support.get("scientific_role") == "PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1", "wrong support-cut role")
    req(bif.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong bif role")
    for payload in (support, bif):
        req(payload.get("shower_truth_used") is False, "truth present in input")
        req(payload.get("target_information_access") is False and payload.get("target_region_events_accessed") is False, "target firewall flag")
        req(payload.get("sonotaco_2013_2014_access") is False, "SonotaCo flag")
        req(payload.get("amos_scientific_access") is False and payload.get("maarsy_scientific_access") is False and payload.get("dms_scientific_access") is False, "protected external flag")

    sm = {(int(s["denominator"]), int(s["bucket"])): s for s in support["subsets"]}
    bm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    expected_keys = {(d, b) for d in DENOMINATORS for b in BUCKETS}
    req(set(sm) == set(bm) == expected_keys, "panel set changed")

    ranked: dict[tuple[int, int], list[dict[str, Any]]] = {}
    recurrent: dict[tuple[int, int], list[dict[str, Any]]] = {}
    universes: dict[tuple[int, int], set[str]] = {}
    panels: list[dict[str, Any]] = []

    for key in sorted(expected_keys):
        ss, bb = sm[key], bm[key]
        k = int(ss["equal_budget_k"])
        req(k == int(bb["equal_budget_k"]) and k > 0, "recurrent budget mismatch")
        support_rows = list(ss["successor_candidates"])
        bif_rows = list(bb["bifiltration_candidates"])
        recurrent_rows = list(ss["recurrent_candidates"])
        req(len(recurrent_rows) >= k and len(support_rows) >= k, "candidate capacity mismatch")
        req(pairwise_disjoint(support_rows), "support-cut disjointness changed")

        universe: set[str] = set()
        for vals in bb["annual_event_ids"].values():
            universe.update(str(x) for x in vals)
        req(len(universe) == int(bb["event_count"]) == int(ss["events_total"]), "panel event count changed")
        req(all(membership(r).issubset(universe) for r in support_rows), "support candidate outside panel universe")
        req(all(membership(r).issubset(universe) for r in bif_rows), "bif candidate outside panel universe")

        enriched: list[dict[str, Any]] = []
        seen_support: set[frozenset[str]] = set()
        for row in support_rows:
            m = membership(row)
            req(m not in seen_support, "duplicate support-cut membership")
            seen_support.add(m)
            score, component_count, raw_area = internal_mass(row, bif_rows)
            out = dict(row)
            out["internal_2d_mass"] = score
            out["internal_bif_component_count"] = component_count
            out["internal_bif_raw_area_sum"] = raw_area
            enriched.append(out)
        enriched.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
        for rank, row in enumerate(enriched, 1):
            row["internal_mass_rank"] = rank
        req({membership(r) for r in enriched} == {membership(r) for r in support_rows}, "candidate membership changed")
        req(pairwise_disjoint(enriched), "ranked candidate disjointness changed")

        ranked[key] = enriched
        recurrent[key] = recurrent_rows
        universes[key] = universe
        positive_count = sum(float(r["internal_2d_mass"]) > 0.0 for r in enriched)
        panels.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": len(universe),
            "equal_budget_k": k,
            "candidate_count": len(enriched),
            "positive_internal_mass_count": positive_count,
            "positive_internal_mass_topk_count": sum(float(r["internal_2d_mass"]) > 0.0 for r in enriched[:k]),
            "pairwise_disjoint": True,
            "topk_family_hashes": [str(r["family_hash"]) for r in enriched[:k]],
            "topk_internal_2d_mass": [float(r["internal_2d_mass"]) for r in enriched[:k]],
        })

    cross_scale: list[dict[str, Any]] = []
    for bucket in BUCKETS:
        fine_key, coarse_key = (1024, bucket), (128, bucket)
        fine_k = int(sm[fine_key]["equal_budget_k"])
        coarse_k = int(sm[coarse_key]["equal_budget_k"])
        fine_universe = universes[fine_key]
        req(fine_universe.issubset(universes[coarse_key]), "fine universe not nested in coarse")
        successor_j = mean_best_jaccard(ranked[fine_key][:fine_k], ranked[coarse_key][:coarse_k], fine_universe)
        recurrent_j = mean_best_jaccard(recurrent[fine_key][:fine_k], recurrent[coarse_key][:coarse_k], fine_universe)
        cross_scale.append({
            "bucket": bucket,
            "internal_mass_mean_best_jaccard": successor_j,
            "recurrent_mean_best_jaccard": recurrent_j,
            "nonlower": successor_j >= recurrent_j,
        })

    successor_mean = sum(float(x["internal_mass_mean_best_jaccard"]) for x in cross_scale) / 4.0
    recurrent_mean = sum(float(x["recurrent_mean_best_jaccard"]) for x in cross_scale) / 4.0
    nonlower = sum(bool(x["nonlower"]) for x in cross_scale)
    gates = {
        "candidate_capacity_all_8": all(int(p["candidate_count"]) >= int(p["equal_budget_k"]) for p in panels),
        "pairwise_disjoint_all_8": all(bool(p["pairwise_disjoint"]) for p in panels),
        "positive_internal_mass_all_8": all(int(p["positive_internal_mass_count"]) > 0 for p in panels),
        "cross_scale_mean_not_lower_than_recurrent": successor_mean >= recurrent_mean,
        "cross_scale_nonlower_4_of_4": nonlower == 4,
        "immutable_membership_and_budget_audit": True,
    }
    verdict = "PASS_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_STRUCTURAL" if all(gates.values()) else "FAIL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_STRUCTURAL"

    prelabel_subsets = []
    for key in sorted(expected_keys):
        ss, bb = sm[key], bm[key]
        prelabel_subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(bb["event_count"]),
            "annual_event_ids": bb["annual_event_ids"],
            "equal_budget_k": int(ss["equal_budget_k"]),
            "recurrent_candidates": ss["recurrent_candidates"],
            "successor_candidates": ranked[key],
        })
    prelabel = {
        "schema": "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL",
        "scientific_role": "PRELABEL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1",
        "support_prelabel_sha256": SUPPORT_SHA,
        "bif_prelabel_sha256": BIF_SHA,
        "configuration": {
            "score": "sum_over_bif_B_subset_S_of_member_fraction_times_persistence_area",
            "formula": "M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)",
            "ranking": ["internal_2d_mass_desc", "modal_contrast_desc", "family_hash_asc"],
            "equal_budget": "stored_recurrent_candidate_count_per_panel",
        },
        "subsets": prelabel_subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    prelabel_path = a.output / "SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256(prelabel_path)

    result = {
        "schema": "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_STRUCTURAL",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_REPRODUCTION_GATE",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "support_prelabel_sha256": SUPPORT_SHA,
        "bif_prelabel_sha256": BIF_SHA,
        "panels": panels,
        "cross_scale": cross_scale,
        "aggregate": {
            "internal_mass_cross_scale_mean": successor_mean,
            "recurrent_cross_scale_mean": recurrent_mean,
            "nonlower_buckets": nonlower,
        },
        "gates": gates,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    result_path = a.output / "SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_STRUCTURAL.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "aggregate": result["aggregate"], "gates": gates, "cross_scale": cross_scale, "panels": panels}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
