#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WINNER_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
WINNER_CANDIDATE_COUNT = 2094
BASELINE_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def immutable_candidate_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": str(row["family_id"]),
        "node_id": int(row["node_id"]),
        "event_ids": [str(x) for x in row["event_ids"]],
        "member_count": int(row["member_count"]),
        "synchronous_stability": float(row["synchronous_stability"]),
        "ordinary_stability": float(row["ordinary_stability"]),
    }


def candidate_fingerprint(row: dict[str, Any]) -> str:
    payload = json.dumps(immutable_candidate_payload(row), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def unordered_candidate_multiset_sha(candidates: list[dict[str, Any]]) -> str:
    fps = sorted(candidate_fingerprint(row) for row in candidates)
    return hashlib.sha256("\n".join(fps).encode()).hexdigest()


def verify_winner_baseline(winner_pre: dict[str, Any], winner_result: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner prelabel membership hash changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner result membership hash changed")
    candidates = winner_pre["successor_candidates"]
    req(isinstance(candidates, list) and len(candidates) == WINNER_CANDIDATE_COUNT, f"winner candidate count changed: {len(candidates)}")
    req(ordered_membership_sha(candidates) == WINNER_MEMBERSHIP_SHA, "winner candidate payload no longer reproduces binding order hash")
    baseline = winner_result["successor_metrics"]
    req(int(baseline["2022"]["recovered_at_100"]) == 89, "binding 2022 @100 changed")
    req(int(baseline["2023"]["recovered_at_100"]) == 90, "binding 2023 @100 changed")
    req(sum(int(baseline[str(y)]["recovered_at_100"]) for y in YEARS) == BASELINE_TOTAL_AT100, "binding baseline total changed")
    return candidates, baseline


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # The complete successor score/order is built ONLY from the frozen winner artifact.
    # No GMN catalogue or known-shower truth has been loaded at this point.
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "binding winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "binding winner result changed")
    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    winner_candidates, baseline = verify_winner_baseline(winner_pre, winner_result)

    winner_multiset_sha = unordered_candidate_multiset_sha(winner_candidates)
    successor: list[dict[str, Any]] = []
    for raw in winner_candidates:
        row = copy.deepcopy(raw)
        member_count = int(row["member_count"])
        sync = float(row["synchronous_stability"])
        ordinary = float(row["ordinary_stability"])
        req(member_count >= 10, f"winner contains candidate below frozen 10-member floor: {member_count}")
        req(np.isfinite(sync) and sync >= 0.0, "winner contains invalid synchronous stability")
        req(np.isfinite(ordinary) and ordinary >= 0.0, "winner contains invalid ordinary stability")
        score = sync / float(member_count)
        req(np.isfinite(score) and score >= 0.0, "invalid native-normalized recurrent score")
        row["native_normalized_sync_score"] = float(score)
        successor.append(row)

    successor.sort(key=lambda r: (
        -float(r["native_normalized_sync_score"]),
        -float(r["synchronous_stability"]),
        -float(r["ordinary_stability"]),
        -int(r["member_count"]),
        str(r["family_id"]),
    ))

    successor_multiset_sha = unordered_candidate_multiset_sha(successor)
    successor_order_sha = ordered_membership_sha(successor)
    req(len(successor) == WINNER_CANDIDATE_COUNT, "successor candidate count changed")
    req(successor_multiset_sha == winner_multiset_sha, "candidate content/membership multiset changed during rerank")
    req(successor_order_sha != WINNER_MEMBERSHIP_SHA, "native-normalized rank did not change the winner order")

    top_size_before = [int(x["member_count"]) for x in winner_candidates[:20]]
    top_size_after = [int(x["member_count"]) for x in successor[:20]]
    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_NATIVE_NORMALIZED_SYNC_RANK_V1",
        "candidate_source": "exact_frozen_density_synchronous_recurrent_eom_179_winner",
        "candidate_count": len(successor),
        "sole_change": "rank_by_synchronous_stability_divided_by_member_count",
        "rank_equivalence": "hdbscan_native_returned_stability_up_to_common_positive_max_lambda_factor",
        "winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "successor_ordered_membership_sha256": successor_order_sha,
        "winner_unordered_candidate_multiset_sha256": winner_multiset_sha,
        "successor_unordered_candidate_multiset_sha256": successor_multiset_sha,
        "candidate_memberships_unchanged": True,
        "mechanism_active": True,
        "winner_top20_member_counts": top_size_before,
        "successor_top20_member_counts": top_size_after,
        "successor_candidates": successor,
        "known_shower_labels_indexed": False,
        "catalogue_loaded_before_order_freeze": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "NATIVE_NORMALIZED_SYNC_RANK_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after the complete successor order is durable do we load target-excluded GMN
    # and obtain the sealed known-shower labels for evaluation.
    req(sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support result changed")
    qmod = parent.load_module(a.quality_source, "native_normalized_sync_rank_v1_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-native-normalized-sync-rank-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict[str, Any]]] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in rows), f"protected region survived parser in {year}")
        events_by_year[year] = rows
    req(len(events_by_year[2022]) == 315024, "accessible 2022 event count changed")
    req(len(events_by_year[2023]) == 423658, "accessible 2023 event count changed")

    ids_by_year = {y: {str(e["id"]) for e in events_by_year[y]} for y in YEARS}
    hidden = hidden_sealed
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    successor_metrics = {str(y): parent.metrics(successor, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor_metrics[str(y)]) for y in YEARS}
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    structural = {
        "exact_candidate_count": len(successor) == WINNER_CANDIDATE_COUNT,
        "exact_candidate_multiset_unchanged": successor_multiset_sha == winner_multiset_sha,
        "order_changed": successor_order_sha != WINNER_MEMBERSHIP_SHA,
        "prelabel_frozen_before_catalogue_load": True,
    }
    passed = bool(
        all(structural.values())
        and successor_total >= REQUIRED_TOTAL_AT100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_NATIVE_NORMALIZED_SYNC_RANK_V1_GMN_DEVELOPMENT" if passed else "FAIL_NATIVE_NORMALIZED_SYNC_RANK_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "sole_change": prelabel["sole_change"],
        "candidate_count": len(successor),
        "winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "successor_ordered_membership_sha256": successor_order_sha,
        "winner_unordered_candidate_multiset_sha256": winner_multiset_sha,
        "successor_unordered_candidate_multiset_sha256": successor_multiset_sha,
        "structural_gates": structural,
        "baseline_metrics": baseline,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "baseline_total_recovered_at_100": BASELINE_TOTAL_AT100,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": REQUIRED_TOTAL_AT100,
        "required_gain": REQUIRED_TOTAL_AT100 - BASELINE_TOTAL_AT100,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "NATIVE_NORMALIZED_SYNC_RANK_V1_GMN_DEVELOPMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "candidate_count": len(successor),
        "baseline_total_at100": BASELINE_TOTAL_AT100,
        "successor_total_at100": successor_total,
        "gain": gain,
        "winner_top20_member_counts": top_size_before,
        "successor_top20_member_counts": top_size_after,
        "2022": {k: successor_metrics["2022"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
        "2023": {k: successor_metrics["2023"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
        "structural_gates": structural,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
