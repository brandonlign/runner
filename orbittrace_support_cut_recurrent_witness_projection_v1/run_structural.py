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
EXPECTED_K = {(128,0):29,(128,1):35,(128,2):38,(128,3):33,(1024,0):8,(1024,1):5,(1024,2):6,(1024,3):9}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    ss = [members(r) for r in rows]
    return all(not a.intersection(b) for i, a in enumerate(ss) for b in ss[i + 1 :])


def witness_projection(support_rows: list[dict[str, Any]], recurrent_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    req(pairwise_disjoint(support_rows), "support-cut input lost pairwise disjointness")
    support_sets = [members(r) for r in support_rows]
    req(len(set(support_sets)) == len(support_sets), "duplicate support membership")
    emitted: set[int] = set()
    output: list[dict[str, Any]] = []
    witness_audit: list[dict[str, Any]] = []

    for fallback_rank, prow in enumerate(recurrent_rows, 1):
        prank = int(prow.get("rank", fallback_rank))
        req(prank == fallback_rank, "recurrent rank/order changed")
        p = members(prow)
        counts = [len(p.intersection(s)) for s in support_sets]
        best = max(counts, default=0)
        if best <= 0:
            witness_audit.append({"recurrent_rank": prank, "recurrent_family_id": str(prow["family_id"]), "max_intersection": 0, "target_family_hash": None, "emitted": False})
            continue
        choices = [i for i, c in enumerate(counts) if c == best]
        winner = min(choices, key=lambda i: str(support_rows[i]["family_hash"]))
        emitted_now = winner not in emitted
        witness_audit.append({
            "recurrent_rank": prank,
            "recurrent_family_id": str(prow["family_id"]),
            "max_intersection": int(best),
            "target_family_hash": str(support_rows[winner]["family_hash"]),
            "emitted": bool(emitted_now),
        })
        if not emitted_now:
            continue
        emitted.add(winner)
        row = dict(support_rows[winner])
        row["witnessed"] = True
        row["earliest_recurrent_witness_rank"] = prank
        row["earliest_recurrent_witness_family_id"] = str(prow["family_id"])
        row["earliest_recurrent_witness_intersection_count"] = int(best)
        output.append(row)

    for i, srow in enumerate(support_rows):
        if i in emitted:
            continue
        row = dict(srow)
        row["witnessed"] = False
        row["earliest_recurrent_witness_rank"] = None
        row["earliest_recurrent_witness_family_id"] = None
        row["earliest_recurrent_witness_intersection_count"] = 0
        output.append(row)

    req(len(output) == len(support_rows), "projection changed candidate count")
    req({members(r) for r in output} == set(support_sets), "projection changed candidate memberships")
    for rank, row in enumerate(output, 1):
        row["witness_projection_rank"] = rank
        if bool(row["witnessed"]):
            req(rank <= int(row["earliest_recurrent_witness_rank"]), "witness rank expanded")
    return output, witness_audit


def restrict_and_dedupe(rows: list[dict[str, Any]], universe: set[str]) -> list[frozenset[str]]:
    out: list[frozenset[str]] = []
    seen: set[frozenset[str]] = set()
    for row in rows:
        s = frozenset(x for x in members(row) if x in universe)
        if len(s) < MIN_SUPPORT or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def mean_best_jaccard(fine_rows: list[dict[str, Any]], coarse_rows: list[dict[str, Any]], fine_universe: set[str]) -> float:
    fine = [members(r) for r in fine_rows]
    coarse = restrict_and_dedupe(coarse_rows, fine_universe)
    if not fine:
        return 0.0
    values: list[float] = []
    for a in fine:
        best = 0.0
        for b in coarse:
            inter = len(a.intersection(b))
            if inter:
                best = max(best, inter / len(a.union(b)))
        values.append(float(best))
    return float(sum(values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--support-prelabel", type=Path, required=True)
    ap.add_argument("--bif-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.support_prelabel) == SUPPORT_SHA, "support-cut prelabel changed")
    req(sha256(a.bif_prelabel) == BIF_SHA, "bifiltration universe prelabel changed")
    support = json.loads(a.support_prelabel.read_text())
    bif = json.loads(a.bif_prelabel.read_text())
    req(support.get("schema") == "ORBITTRACE_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL", "wrong support schema")
    req(support.get("scientific_role") == "PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1", "wrong support role")
    req(bif.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong bif role")
    for payload in (support, bif):
        req(payload.get("shower_truth_used") is False, "truth entered structural input")
        req(payload.get("target_information_access") is False and payload.get("target_region_events_accessed") is False, "target firewall flag")
        req(payload.get("sonotaco_2013_2014_access") is False, "SonotaCo flag")
        req(payload.get("amos_scientific_access") is False and payload.get("maarsy_scientific_access") is False and payload.get("dms_scientific_access") is False, "protected external flag")

    sm = {(int(s["denominator"]), int(s["bucket"])): s for s in support["subsets"]}
    bm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    expected = set(EXPECTED_K)
    req(set(sm) == set(bm) == expected, "panel set changed")

    projected: dict[tuple[int, int], list[dict[str, Any]]] = {}
    recurrent: dict[tuple[int, int], list[dict[str, Any]]] = {}
    universes: dict[tuple[int, int], set[str]] = {}
    panels: list[dict[str, Any]] = []
    frozen_subsets: list[dict[str, Any]] = []

    for key in sorted(expected):
        ss, bb = sm[key], bm[key]
        k = int(ss["equal_budget_k"])
        req(k == EXPECTED_K[key] == int(bb["equal_budget_k"]), f"K changed {key}")
        srows = list(ss["successor_candidates"])
        prows = list(ss["recurrent_candidates"])
        req(len(srows) >= k and len(prows) >= k, f"capacity changed {key}")
        req([int(r["rank"]) for r in srows] == list(range(1, len(srows) + 1)), f"native support order changed {key}")
        req([int(r["rank"]) for r in prows] == list(range(1, len(prows) + 1)), f"recurrent order changed {key}")
        req(pairwise_disjoint(srows), f"support input not disjoint {key}")

        universe: set[str] = set()
        annual = bb["annual_event_ids"]
        req(set(annual) == {"2022", "2023"}, f"annual universe keys changed {key}")
        for vals in annual.values():
            universe.update(str(x) for x in vals)
        req(len(universe) == int(bb["event_count"]) == int(ss["events_total"]), f"event universe changed {key}")
        req(all(members(r).issubset(universe) for r in srows + prows), f"candidate outside universe {key}")

        order, audit = witness_projection(srows, prows)
        projected[key] = order
        recurrent[key] = prows
        universes[key] = universe
        witnessable_topk = sum(int(audit[i]["max_intersection"]) > 0 for i in range(k))
        witnessed_output = sum(bool(r["witnessed"]) for r in order)
        duplicate_witnesses = sum((int(x["max_intersection"]) > 0 and not bool(x["emitted"])) for x in audit)
        panels.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": len(universe),
            "equal_budget_k": k,
            "candidate_count": len(order),
            "pairwise_disjoint": pairwise_disjoint(order),
            "topk_parent_witnessable_count": witnessable_topk,
            "topk_parent_witnessable_fraction": witnessable_topk / k,
            "witnessed_output_candidate_count": witnessed_output,
            "duplicate_recurrent_witness_count": duplicate_witnesses,
            "topk_projection_family_hashes": [str(r["family_hash"]) for r in order[:k]],
        })
        frozen_subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": len(universe),
            "annual_event_ids": annual,
            "equal_budget_k": k,
            "successor_candidates": order,
            "recurrent_candidates": prows,
            "witness_audit": audit,
        })

    cross_scale: list[dict[str, Any]] = []
    for bucket in BUCKETS:
        fk, ck = (1024, bucket), (128, bucket)
        kf, kc = EXPECTED_K[fk], EXPECTED_K[ck]
        fu = universes[fk]
        req(fu.issubset(universes[ck]), f"fine universe not nested b={bucket}")
        pj = mean_best_jaccard(projected[fk][:kf], projected[ck][:kc], fu)
        rj = mean_best_jaccard(recurrent[fk][:kf], recurrent[ck][:kc], fu)
        cross_scale.append({"bucket": bucket, "projection_mean_best_jaccard": pj, "recurrent_mean_best_jaccard": rj, "nonlower": pj >= rj})

    proj_mean = sum(float(x["projection_mean_best_jaccard"]) for x in cross_scale) / 4.0
    rec_mean = sum(float(x["recurrent_mean_best_jaccard"]) for x in cross_scale) / 4.0
    nonlower = sum(bool(x["nonlower"]) for x in cross_scale)
    gates = {
        "candidate_capacity_all_8": all(int(p["candidate_count"]) >= int(p["equal_budget_k"]) for p in panels),
        "pairwise_disjoint_all_8": all(bool(p["pairwise_disjoint"]) for p in panels),
        "topk_parent_witnessable_all_8": all(int(p["topk_parent_witnessable_count"]) == int(p["equal_budget_k"]) for p in panels),
        "witness_rank_nonexpansion_all": all((not bool(r["witnessed"])) or int(r["witness_projection_rank"]) <= int(r["earliest_recurrent_witness_rank"]) for rows in projected.values() for r in rows),
        "cross_scale_mean_not_lower_than_recurrent": proj_mean >= rec_mean,
        "cross_scale_nonlower_4_of_4": nonlower == 4,
        "immutable_membership_budget_order_audit": True,
    }
    verdict = "PASS_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_STRUCTURAL" if all(gates.values()) else "FAIL_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_STRUCTURAL"

    prelabel = {
        "schema": "ORBITTRACE_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_PRELABEL",
        "scientific_role": "PRELABEL_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1",
        "support_prelabel_sha256": SUPPORT_SHA,
        "universe_prelabel_sha256": BIF_SHA,
        "configuration": {
            "candidate_universe": "unchanged_support_resolved_cut",
            "witness_rule": "recurrent_order_max_exact_intersection_count_then_support_family_hash",
            "duplicate_witness_rule": "emit_support_candidate_only_on_first_witness",
            "append_rule": "remaining_support_candidates_in_native_support_order",
            "equal_budget": "stored_recurrent_candidate_count_per_panel",
        },
        "subsets": frozen_subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    prelabel_path = a.output / "SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256(prelabel_path)

    result = {
        "schema": "ORBITTRACE_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_STRUCTURAL",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_GATE",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "support_prelabel_sha256": SUPPORT_SHA,
        "universe_prelabel_sha256": BIF_SHA,
        "panels": panels,
        "cross_scale": cross_scale,
        "aggregate": {"projection_cross_scale_mean": proj_mean, "recurrent_cross_scale_mean": rec_mean, "nonlower_buckets": nonlower},
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
    result_path = a.output / "SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_STRUCTURAL.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "aggregate": result["aggregate"], "gates": gates, "panels": panels, "cross_scale": cross_scale}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
