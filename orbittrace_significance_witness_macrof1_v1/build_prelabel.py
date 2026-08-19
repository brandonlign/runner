#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_PRELABEL_SHA256 = "bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a"
EXPECTED_SCHEMA = "ORBITTRACE_SIGNIFICANCE_PRUNED_TOPOMODAL_V1_PRELABEL"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family_hash(prefix: str, ids: list[str]) -> str:
    payload = prefix + "|" + "|".join(sorted(map(str, ids)))
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def intersection_count(a: list[str], bset: set[str]) -> int:
    return sum(str(x) in bset for x in a)


def build_subset(src: dict[str, Any]) -> dict[str, Any]:
    rec = list(src["recurrent_candidates"])
    sig = list(src["successor_candidates"])
    K = int(src["equal_budget_k"])
    req(len(rec) == K, "source recurrent candidate budget changed")
    req([int(x["rank"]) for x in rec] == list(range(1, len(rec) + 1)), "recurrent rank discontinuity")
    req([int(x["rank"]) for x in sig] == list(range(1, len(sig) + 1)), "significance rank discontinuity")

    rec_sets = [set(map(str, x["event_ids"])) for x in rec]
    sig_sets = [set(map(str, x["event_ids"])) for x in sig]
    for i in range(len(rec_sets)):
        for j in range(i):
            req(not (rec_sets[i] & rec_sets[j]), "source recurrent memberships overlap")
    for i in range(len(sig_sets)):
        for j in range(i):
            req(not (sig_sets[i] & sig_sets[j]), "source significance memberships overlap")

    emitted_sig: set[int] = set()
    out: list[dict[str, Any]] = []
    recurrent_orphans = 0
    witness_rows: list[dict[str, Any]] = []

    for i, r in enumerate(rec):
        rset = rec_sets[i]
        overlaps = [len(rset & sset) for sset in sig_sets]
        best = max(overlaps, default=0)
        if best > 0:
            winners = [j for j, value in enumerate(overlaps) if value == best]
            j = min(winners, key=lambda z: str(sig[z]["family_hash"]))
            emitted = False
            if j not in emitted_sig:
                s = sig[j]
                ids = sorted(map(str, s["event_ids"]))
                out.append({
                    "family_id": "SWMF1" + family_hash("SIG", ids),
                    "event_ids": ids,
                    "member_count": len(ids),
                    "origin": "significance_witness",
                    "source_significance_rank": int(s["rank"]),
                    "source_significance_family_hash": str(s["family_hash"]),
                    "first_recurrent_witness_rank": int(r["rank"]),
                    "first_recurrent_witness_family_hash": str(r["family_hash"]),
                    "witness_overlap_count": int(best),
                })
                emitted_sig.add(j)
                emitted = True
            witness_rows.append({
                "recurrent_rank": int(r["rank"]),
                "recurrent_family_hash": str(r["family_hash"]),
                "max_overlap": int(best),
                "winning_significance_rank": int(sig[j]["rank"]),
                "winning_significance_family_hash": str(sig[j]["family_hash"]),
                "winner_emitted_at_this_rank": emitted,
            })
        else:
            ids = sorted(map(str, r["event_ids"]))
            out.append({
                "family_id": "SWMF1" + family_hash("ORPHAN", ids),
                "event_ids": ids,
                "member_count": len(ids),
                "origin": "recurrent_orphan",
                "source_recurrent_rank": int(r["rank"]),
                "source_recurrent_family_hash": str(r["family_hash"]),
            })
            recurrent_orphans += 1
            witness_rows.append({
                "recurrent_rank": int(r["rank"]),
                "recurrent_family_hash": str(r["family_hash"]),
                "max_overlap": 0,
                "winning_significance_rank": None,
                "winning_significance_family_hash": None,
                "winner_emitted_at_this_rank": True,
            })

    for j, s in enumerate(sig):
        if j in emitted_sig:
            continue
        ids = sorted(map(str, s["event_ids"]))
        out.append({
            "family_id": "SWMF1" + family_hash("SIG", ids),
            "event_ids": ids,
            "member_count": len(ids),
            "origin": "significance_append",
            "source_significance_rank": int(s["rank"]),
            "source_significance_family_hash": str(s["family_hash"]),
        })
        emitted_sig.add(j)

    for rank, row in enumerate(out, 1):
        row["rank"] = rank

    req(len(out) >= K, "successor cannot fill inherited candidate budget")
    out_sets = [set(map(str, x["event_ids"])) for x in out]
    for i in range(len(out_sets)):
        for j in range(i):
            req(not (out_sets[i] & out_sets[j]), f"successor memberships overlap at {j+1}/{i+1}")

    rec_hashes = [hashlib.sha256("|".join(sorted(x)).encode()).hexdigest() for x in rec_sets]
    out_hashes = [hashlib.sha256("|".join(sorted(x)).encode()).hexdigest() for x in out_sets]
    top_overlap = {}
    for q in (10, 20, 25, 50, 100):
        k = min(q, K, len(out), len(rec))
        top_overlap[str(q)] = {
            "effective_k": k,
            "exact_set_overlap": len(set(rec_hashes[:k]) & set(out_hashes[:k])),
            "same_rank_positions": sum(a == b for a, b in zip(rec_hashes[:k], out_hashes[:k])),
        }

    return {
        "denominator": int(src["denominator"]),
        "bucket": int(src["bucket"]),
        "equal_budget_k": K,
        "events_total": int(src["events_total"]),
        "events_by_year": src["events_by_year"],
        "event_universe_sha256": str(src["event_universe_sha256"]),
        "source_recurrent_candidate_count": len(rec),
        "source_significance_candidate_count": len(sig),
        "successor_candidate_count": len(out),
        "recurrent_orphan_count": recurrent_orphans,
        "significance_candidates_emitted": len(sig),
        "mechanism_active": [x["event_ids"] for x in out[:K]] != [x["event_ids"] for x in rec[:K]],
        "pairwise_disjoint": True,
        "topk_overlap_vs_recurrent": top_overlap,
        "witness_map": witness_rows,
        "recurrent_candidates": rec,
        "successor_candidates": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.source_prelabel) == SOURCE_PRELABEL_SHA256, "source significance prelabel SHA changed")
    src = json.loads(a.source_prelabel.read_text())
    req(src.get("schema") == EXPECTED_SCHEMA, "source prelabel schema changed")
    req(src.get("shower_truth_used") is False, "source prelabel is not truth-blind")
    req(src.get("target_information_access") is False and src.get("target_region_events_accessed") is False, "source target firewall changed")
    req(src.get("sonotaco_2013_2014_access") is False, "source prelabel accessed SonotaCo")

    subsets = [build_subset(row) for row in src["subsets"]]
    req(len(subsets) == 8, "unexpected sparse panel count")
    req({(x["denominator"], x["bucket"]) for x in subsets} == {(d, b) for d in (128, 1024) for b in range(4)}, "sparse panel identity changed")
    req(any(x["mechanism_active"] for x in subsets), "significance-witness mechanism inactive")

    result = {
        "schema": "ORBITTRACE_SIGNIFICANCE_WITNESS_MACROF1_V1_PRELABEL",
        "scientific_role": "PRELABEL_SIGNIFICANCE_WITNESS_MACROF1_V1",
        "source_prelabel_sha256": SOURCE_PRELABEL_SHA256,
        "construction": "recurrent_order_max_exact_overlap_significance_witness_then_zero_overlap_recurrent_orphan_then_remaining_significance_native_order",
        "subsets": subsets,
        "candidate_budget_sufficient_all_panels": all(x["successor_candidate_count"] >= x["equal_budget_k"] for x in subsets),
        "pairwise_disjoint_all_panels": all(x["pairwise_disjoint"] for x in subsets),
        "mechanism_active_any_panel": any(x["mechanism_active"] for x in subsets),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_method_change_authorized": False,
    }
    path = a.output / "SIGNIFICANCE_WITNESS_MACROF1_V1_PRELABEL.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "schema": result["schema"],
        "truth": False,
        "panels": [{
            "denominator": x["denominator"],
            "bucket": x["bucket"],
            "K": x["equal_budget_k"],
            "successor_candidates": x["successor_candidate_count"],
            "orphans": x["recurrent_orphan_count"],
            "mechanism_active": x["mechanism_active"],
        } for x in subsets],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
