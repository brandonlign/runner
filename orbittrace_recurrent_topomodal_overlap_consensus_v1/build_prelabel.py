#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_SHA = "278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a"
EXPECTED_K = {
    (128, 0): 29, (128, 1): 35, (128, 2): 38, (128, 3): 33,
    (1024, 0): 8, (1024, 1): 5, (1024, 2): 6, (1024, 3): 9,
}
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4


def req(x: bool, message: str) -> None:
    if not x:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mem(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def disjoint(rows: list[dict[str, Any]]) -> bool:
    sets = [mem(r) for r in rows]
    return all(not a & b for i, a in enumerate(sets) for b in sets[i + 1 :])


def restrict(rows: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    out: list[frozenset[str]] = []
    seen: set[frozenset[str]] = set()
    for row in rows:
        s = frozenset(x for x in mem(row) if x in universe)
        if len(s) >= MIN_SUPPORT and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def mean_best_jaccard(fine: list[dict[str, Any]], coarse: list[dict[str, Any]], universe: set[str]) -> float:
    fine_sets = [mem(r) for r in fine]
    coarse_sets = restrict(coarse, universe)
    if not fine_sets:
        return 0.0
    values = []
    for a in fine_sets:
        best = 0.0
        for b in coarse_sets:
            inter = len(a & b)
            if inter:
                best = max(best, inter / len(a | b))
        values.append(best)
    return sum(values) / len(values)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(sha256(args.source_prelabel) == SOURCE_SHA, "source prelabel changed")
    source = json.loads(args.source_prelabel.read_text())
    req(source["schema"] == "ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL", "wrong source schema")
    req(source["scientific_role"] == "PRELABEL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1", "wrong source role")
    req(source["shower_truth_used"] is False, "source used truth")
    req(source["target_information_access"] is False and source["target_region_events_accessed"] is False, "source firewall")
    req(source["sonotaco_2013_2014_access"] is False, "source SonotaCo access")

    source_map = {(int(r["denominator"]), int(r["bucket"])): r for r in source["subsets"]}
    req(set(source_map) == set(EXPECTED_K), "panel set changed")

    successor_by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    parent_by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    universe_by_key: dict[tuple[int, int], set[str]] = {}
    frozen = []
    panels = []

    for key in sorted(EXPECTED_K):
        src = source_map[key]
        K = EXPECTED_K[key]
        req(int(src["equal_budget_k"]) == K, "equal budget changed")

        parents = list(src["recurrent_candidates"])
        req(len(parents) == K, "parent candidate count changed")
        req([int(r["rank"]) for r in parents] == list(range(1, K + 1)), "parent order changed")
        req(disjoint(parents), "parent candidates overlap")

        support = [
            dict(r)
            for r in src["successor_candidates"]
            if r.get("catalogue_source") in {"support_projection", "support_append"}
        ]
        req(support, "support catalogue empty")
        req(disjoint(support), "support catalogue not disjoint")
        support.sort(key=lambda r: (int(r["rank"]), str(r["family_hash"])))
        support_ranks = [int(r["rank"]) for r in support]
        req(len(set(support_ranks)) == len(support_ranks), "support rank duplicated")
        req(support_ranks == list(range(1, len(support) + 1)), "support rank sequence changed")
        req(len({str(r["family_hash"]) for r in support}) == len(support), "support family hash duplicated")

        universe = set(src["annual_event_ids"]["2022"]) | set(src["annual_event_ids"]["2023"])
        req(len(universe) == int(src["event_count"]), "event universe changed")
        req(all(mem(r).issubset(universe) for r in parents + support), "candidate outside frozen universe")

        retained = []
        discarded = []
        for row in support:
            s = mem(row)
            parent_hits = [i + 1 for i, p in enumerate(parents) if s & mem(p)]
            req(len(parent_hits) <= 1, "support candidate overlaps multiple recurrent parents")
            audit = {
                "family_hash": str(row["family_hash"]),
                "support_rank": int(row["rank"]),
                "member_count": len(s),
                "parent_overlap_count": len(parent_hits),
                "corroborating_parent_rank": parent_hits[0] if parent_hits else None,
            }
            if parent_hits:
                out = dict(row)
                out["native_support_rank"] = int(row["rank"])
                out["corroborating_parent_rank"] = parent_hits[0]
                out["catalogue_source"] = "recurrent_overlap_confirmed_topomodal"
                retained.append(out)
                audit["retained"] = True
            else:
                audit["retained"] = False
            discarded.append(audit)

        retained.sort(
            key=lambda r: (
                int(r["corroborating_parent_rank"]),
                int(r["native_support_rank"]),
                str(r["family_hash"]),
            )
        )
        for rank, row in enumerate(retained, 1):
            row["overlap_consensus_rank"] = rank

        req(len(retained) >= K, "insufficient overlap-confirmed candidate capacity")
        req(disjoint(retained), "retained candidates overlap")
        req(all(len(mem(r)) >= MIN_SUPPORT for r in retained), "retained candidate below support floor")
        req(all(len(mem(r) & mem(parents[int(r["corroborating_parent_rank"]) - 1])) > 0 for r in retained), "retained row lost corroboration")
        req([int(r["overlap_consensus_rank"]) for r in retained] == list(range(1, len(retained) + 1)), "successor rank discontinuity")
        req(all(mem(r) == mem(next(s for s in support if str(s["family_hash"]) == str(r["family_hash"]))) for r in retained), "support membership changed")

        topk_parent_ranks = sorted({int(r["corroborating_parent_rank"]) for r in retained[:K]})
        req(topk_parent_ranks, "top-K has no corroborating parent")

        successor_by_key[key] = retained
        parent_by_key[key] = parents
        universe_by_key[key] = universe
        panels.append({
            "denominator": key[0],
            "bucket": key[1],
            "K": K,
            "support_candidate_count": len(support),
            "retained_candidate_count": len(retained),
            "discarded_zero_overlap_count": len(support) - len(retained),
            "capacity_at_least_k": len(retained) >= K,
            "pairwise_disjoint": disjoint(retained),
            "topk_distinct_parent_count": len(topk_parent_ranks),
            "topk_max_parent_rank": max(topk_parent_ranks),
        })
        frozen.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": len(universe),
            "annual_event_ids": src["annual_event_ids"],
            "equal_budget_k": K,
            "successor_candidates": retained,
            "recurrent_candidates": parents,
            "support_overlap_audit": discarded,
        })

    cross_scale = []
    for bucket in BUCKETS:
        fine_key = (1024, bucket)
        coarse_key = (128, bucket)
        fine_universe = universe_by_key[fine_key]
        req(fine_universe.issubset(universe_by_key[coarse_key]), "fine panel is not nested in coarse panel")
        Kf, Kc = EXPECTED_K[fine_key], EXPECTED_K[coarse_key]
        successor_j = mean_best_jaccard(successor_by_key[fine_key][:Kf], successor_by_key[coarse_key][:Kc], fine_universe)
        parent_j = mean_best_jaccard(parent_by_key[fine_key], parent_by_key[coarse_key], fine_universe)
        cross_scale.append({
            "bucket": bucket,
            "successor_mean_best_jaccard": successor_j,
            "recurrent_mean_best_jaccard": parent_j,
            "nonlower": successor_j >= parent_j,
        })

    successor_mean = sum(r["successor_mean_best_jaccard"] for r in cross_scale) / len(cross_scale)
    parent_mean = sum(r["recurrent_mean_best_jaccard"] for r in cross_scale) / len(cross_scale)
    gates = {
        "immutable_source_and_firewall": True,
        "parent_order_valid_all_8": True,
        "support_order_valid_all_8": True,
        "unique_parent_corroboration_all_retained": True,
        "zero_parent_overlap_all_discarded": True,
        "full_support_membership_preserved_all_retained": True,
        "pairwise_disjoint_all_8": all(p["pairwise_disjoint"] for p in panels),
        "capacity_at_least_k_all_8": all(p["capacity_at_least_k"] for p in panels),
        "topk_has_corroborating_parent_all_8": all(p["topk_distinct_parent_count"] >= 1 for p in panels),
        "deterministic_lexicographic_order_all_8": True,
        "cross_scale_nonlower_4_of_4": all(r["nonlower"] for r in cross_scale),
        "cross_scale_aggregate_nonlower": successor_mean >= parent_mean,
    }
    verdict = "PASS_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH" if all(gates.values()) else "FAIL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH"

    prelabel = {
        "schema": "ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL",
        "scientific_role": "PRELABEL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1",
        "source_prelabel_sha256": SOURCE_SHA,
        "configuration": {
            "retain": "full_topomodal_support_candidate_iff_exact_event_overlap_with_exactly_one_recurrent_parent",
            "discard": "zero_recurrent_parent_overlap",
            "abort": "more_than_one_recurrent_parent_overlap",
            "ranking": "corroborating_parent_rank_then_native_support_rank_then_family_hash",
            "equal_budget": "stored_recurrent_candidate_count_per_panel",
        },
        "subsets": frozen,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    prelabel_path = args.output / "RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256(prelabel_path)

    result = {
        "schema": "ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH",
        "scientific_role": "ZERO_LABEL_PRETRUTH_AUTHORIZATION",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "panels": panels,
        "cross_scale": cross_scale,
        "aggregate": {
            "successor_cross_scale_mean": successor_mean,
            "recurrent_cross_scale_mean": parent_mean,
            "nonlower_buckets": sum(bool(r["nonlower"]) for r in cross_scale),
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
    result_path = args.output / "RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "aggregate": result["aggregate"], "gates": gates, "panels": panels}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
