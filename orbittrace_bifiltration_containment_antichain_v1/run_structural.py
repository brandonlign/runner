#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
PRELABEL_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def membership_hash(event_ids: list[str]) -> str:
    members = tuple(sorted(str(x) for x in event_ids))
    return hashlib.sha256(("\n".join(members) + "\n").encode()).hexdigest()


def comparable(a: frozenset[str], b: frozenset[str]) -> bool:
    if len(a) < len(b):
        return a.issubset(b)
    if len(b) < len(a):
        return b.issubset(a)
    return False


def greedy_antichain(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    selected_rows: list[dict[str, Any]] = []
    selected_sets: list[frozenset[str]] = []
    rejected = 0
    for row in rows:
        s = frozenset(str(x) for x in row["event_ids"])
        if any(comparable(s, t) for t in selected_sets):
            rejected += 1
            continue
        selected_rows.append(row)
        selected_sets.append(s)
    return selected_rows, rejected


def nested_pairs(rows: list[dict[str, Any]]) -> int:
    sets = [frozenset(str(x) for x in r["event_ids"]) for r in rows]
    total = 0
    for i, a in enumerate(sets):
        for b in sets[i + 1 :]:
            total += int(comparable(a, b))
    return total


def union_count(rows: list[dict[str, Any]]) -> int:
    out: set[str] = set()
    for r in rows:
        out.update(str(x) for x in r["event_ids"])
    return len(out)


def restrict_and_dedupe(rows: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    seen: set[frozenset[str]] = set()
    out: list[frozenset[str]] = []
    for r in rows:
        s = frozenset(str(x) for x in r["event_ids"] if str(x) in universe)
        if len(s) < MIN_SUPPORT or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def mean_best_jaccard(fine_rows: list[dict[str, Any]], coarse_rows: list[dict[str, Any]], fine_universe: set[str]) -> float:
    fine = [frozenset(str(x) for x in r["event_ids"]) for r in fine_rows]
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
    ap.add_argument("--prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.prelabel) == PRELABEL_SHA, "immutable bifiltration prelabel changed")
    pre = json.loads(a.prelabel.read_text())
    req(pre.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong prelabel schema")
    req(pre.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong prelabel role")
    req(pre.get("shower_truth_used") is False, "prelabel truth flag")
    req(pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False, "target firewall flag")
    req(pre.get("sonotaco_2013_2014_access") is False, "SonotaCo entered prelabel")
    req(pre.get("amos_scientific_access") is False and pre.get("maarsy_scientific_access") is False and pre.get("dms_scientific_access") is False, "protected external access flag")

    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre.get("subsets", [])}
    req(set(subsets) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "wrong subset set")

    panels: list[dict[str, Any]] = []
    selected_by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    recurrent_by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    universe_by_key: dict[tuple[int, int], set[str]] = {}

    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            src = subsets[(denominator, bucket)]
            k = int(src["equal_budget_k"])
            req(k > 0, "nonpositive recurrent budget")
            recurrent = list(src["recurrent_candidates"])
            rows = list(src["bifiltration_candidates"])
            req(len(recurrent) == k and len(rows) >= k, "candidate budget mismatch")
            req([int(r["rank"]) for r in rows] == list(range(1, len(rows) + 1)), "raw bif rank discontinuity")
            expected = sorted(rows, key=lambda r: (-float(r["persistence_area"]), -int(r["member_count"]), str(r["family_hash"])))
            req([str(r["family_hash"]) for r in rows] == [str(r["family_hash"]) for r in expected], "frozen persistence order changed")

            all_ids: set[str] = set()
            for vals in src["annual_event_ids"].values():
                all_ids.update(str(x) for x in vals)
            req(len(all_ids) == int(src["event_count"]), "annual universes do not reconstruct pooled subset")
            for row in rows:
                eids = [str(x) for x in row["event_ids"]]
                req(len(eids) == int(row["member_count"]) and len(set(eids)) == len(eids), "bad bif membership")
                req(set(eids).issubset(all_ids), "out-of-universe bif event")
                req(membership_hash(eids) == str(row["family_hash"]), "bif membership hash changed")
                req(float(row["persistence_area"]) > 0.0, "nonpositive persistence area")

            selected, rejected = greedy_antichain(rows)
            selected_by_key[(denominator, bucket)] = selected
            recurrent_by_key[(denominator, bucket)] = recurrent
            universe_by_key[(denominator, bucket)] = all_ids

            selected_top = selected[:k]
            raw_top = rows[:k]
            selected_nested = nested_pairs(selected_top)
            raw_nested = nested_pairs(raw_top)
            selected_coverage = union_count(selected_top)
            raw_coverage = union_count(raw_top)
            panels.append({
                "denominator": denominator,
                "bucket": bucket,
                "event_count": len(all_ids),
                "equal_budget_k": k,
                "raw_candidate_count": len(rows),
                "antichain_candidate_count": len(selected),
                "containment_rejected_count": rejected,
                "raw_topk_nested_pair_count": raw_nested,
                "antichain_topk_nested_pair_count": selected_nested,
                "raw_topk_unique_event_count": raw_coverage,
                "antichain_topk_unique_event_count": selected_coverage,
                "raw_topk_unique_event_fraction": raw_coverage / len(all_ids),
                "antichain_topk_unique_event_fraction": selected_coverage / len(all_ids),
                "antichain_topk_family_hashes": [str(r["family_hash"]) for r in selected_top],
            })

    cross_scale: list[dict[str, Any]] = []
    for bucket in BUCKETS:
        fine_key = (1024, bucket)
        coarse_key = (128, bucket)
        fine_k = int(subsets[fine_key]["equal_budget_k"])
        coarse_k = int(subsets[coarse_key]["equal_budget_k"])
        fine_universe = universe_by_key[fine_key]
        req(fine_universe.issubset(universe_by_key[coarse_key]), f"fine universe not nested in coarse b={bucket}")
        ant = mean_best_jaccard(selected_by_key[fine_key][:fine_k], selected_by_key[coarse_key][:coarse_k], fine_universe)
        rec = mean_best_jaccard(recurrent_by_key[fine_key], recurrent_by_key[coarse_key], fine_universe)
        cross_scale.append({"bucket": bucket, "antichain_mean_best_jaccard": ant, "recurrent_mean_best_jaccard": rec, "nonlower": ant >= rec})

    capacity_all = all(int(p["antichain_candidate_count"]) >= int(p["equal_budget_k"]) for p in panels)
    zero_nested_all = all(int(p["antichain_topk_nested_pair_count"]) == 0 for p in panels)
    coverage_nonlower_all = all(int(p["antichain_topk_unique_event_count"]) >= int(p["raw_topk_unique_event_count"]) for p in panels)
    raw_cov_pooled = sum(int(p["raw_topk_unique_event_count"]) for p in panels)
    ant_cov_pooled = sum(int(p["antichain_topk_unique_event_count"]) for p in panels)
    ant_cross_mean = sum(float(r["antichain_mean_best_jaccard"]) for r in cross_scale) / len(cross_scale)
    rec_cross_mean = sum(float(r["recurrent_mean_best_jaccard"]) for r in cross_scale) / len(cross_scale)
    cross_nonlower = sum(bool(r["nonlower"]) for r in cross_scale)

    gates = {
        "capacity_all_8": capacity_all,
        "zero_nested_topk_all_8": zero_nested_all,
        "topk_event_coverage_nonlower_all_8": coverage_nonlower_all,
        "topk_event_coverage_strict_pooled": ant_cov_pooled > raw_cov_pooled,
        "cross_scale_mean_not_lower_than_recurrent": ant_cross_mean >= rec_cross_mean,
        "cross_scale_nonlower_at_least_3_of_4": cross_nonlower >= 3,
    }
    verdict = "PASS_BIFILTRATION_CONTAINMENT_ANTICHAIN_V1_STRUCTURAL" if all(gates.values()) else "FAIL_BIFILTRATION_CONTAINMENT_ANTICHAIN_V1_STRUCTURAL"
    result = {
        "schema": "ORBITTRACE_BIFILTRATION_CONTAINMENT_ANTICHAIN_V1_STRUCTURAL",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "verdict": verdict,
        "source_prelabel_sha256": PRELABEL_SHA,
        "configuration": {
            "selection": "greedy_exact_strict_containment_antichain_in_frozen_persistence_area_order",
            "future_order_if_authorized": "accepted_candidate_order_unchanged",
            "min_support_for_cross_scale_restriction": MIN_SUPPORT,
        },
        "panels": panels,
        "cross_scale": cross_scale,
        "aggregate": {
            "raw_topk_unique_event_count_sum": raw_cov_pooled,
            "antichain_topk_unique_event_count_sum": ant_cov_pooled,
            "recurrent_cross_scale_mean": rec_cross_mean,
            "antichain_cross_scale_mean": ant_cross_mean,
            "cross_scale_nonlower_buckets": cross_nonlower,
        },
        "gates": gates,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "BIFILTRATION_CONTAINMENT_ANTICHAIN_V1_STRUCTURAL.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "aggregate": result["aggregate"], "gates": gates, "panels": panels, "cross_scale": cross_scale}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
