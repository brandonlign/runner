#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import run_development as parent_runner

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
WEIGHT_THRESHOLD = 1.0
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WEIGHTS_SHA = "648b88efc09192738dcce8eb2af15e215676dd62451a88cd9230337d80fd5347"
WINNER_ORDERED_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_PARENT_COUNT = 2094
EXPECTED_PARENT_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def successor_hash(candidates: list[dict]) -> str:
    h = hashlib.sha256()
    for rank, row in enumerate(candidates, 1):
        h.update(str(rank).encode())
        h.update(b"\0")
        h.update(str(row["family_id"]).encode())
        h.update(b"\0")
        for eid in row["event_ids"]:
            h.update(str(eid).encode())
            h.update(b"\0")
        h.update(b"\n")
    return h.hexdigest()


def annual_gate(parent: dict, successor: dict) -> dict[str, bool]:
    return {
        "recovered_at_50_not_lower": int(successor["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(successor["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": float(successor["top100_dominant_precision"]) >= float(parent["top100_dominant_precision"]),
        "mrr_not_lower": float(successor["mrr"]) >= float(parent["mrr"]),
        "fragmentation_not_higher": float(successor["fragmentation_median_top500"]) <= float(parent["fragmentation_median_top500"]),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--weights-npy", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "frozen winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "frozen winner result changed")
    req(sha(a.weights_npy) == WEIGHTS_SHA, "frozen sporadic weights changed")

    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    req(winner_pre["successor_candidate_count"] == EXPECTED_PARENT_COUNT, "winner candidate count changed")
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_ORDERED_MEMBERSHIP_SHA, "winner ordered membership changed")
    req(winner_result["successor_candidate_count"] == EXPECTED_PARENT_COUNT, "winner result candidate count changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_ORDERED_MEMBERSHIP_SHA, "winner result membership hash changed")
    req(winner_result["verdict"] == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "input is not binding winner")
    parent_metrics = winner_result["successor_metrics"]
    req(sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS) == EXPECTED_PARENT_TOTAL_AT100, "winner @100 total changed")

    # Load the exact target-excluded GMN event stream only to align frozen event-indexed weights
    # and to obtain the already-sealed development labels after pretruth persistence.
    qmod = parent_runner.load_module(a.quality_source, "denoise_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-sporadic-member-denoise-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == int(winner_pre["events_total"]) == 738682, "pooled event count changed")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    weights = np.load(a.weights_npy, allow_pickle=False)
    req(weights.shape == (len(events),), f"weight shape changed: {weights.shape}")
    req(np.all(np.isfinite(weights)), "non-finite frozen weights")
    req(np.all((weights > 0.0) & (weights < 2.0)), "frozen weight domain changed")
    weight_by_id = {str(e["id"]): float(weights[i]) for i, e in enumerate(events)}
    req(len(weight_by_id) == len(events), "event-to-weight map collision")

    parent_candidates = winner_pre["successor_candidates"]
    req(len(parent_candidates) == EXPECTED_PARENT_COUNT, "parent candidate list length changed")
    all_parent_ids = {str(eid) for row in parent_candidates for eid in row["event_ids"]}
    req(all(eid in weight_by_id for eid in all_parent_ids), "winner member missing from frozen weight event stream")

    successor_candidates: list[dict] = []
    removed_members = 0
    dropped_families = 0
    changed_families = 0
    for row in parent_candidates:
        original = [str(x) for x in row["event_ids"]]
        surviving = [eid for eid in original if weight_by_id[eid] > WEIGHT_THRESHOLD]
        removed_members += len(original) - len(surviving)
        if surviving != original:
            changed_families += 1
        if len(surviving) < MIN_CLUSTER_SIZE:
            dropped_families += 1
            continue
        new_id = hashlib.sha256(("SMD1|" + "|".join(surviving)).encode()).hexdigest()[:20]
        successor_candidates.append({
            "family_id": new_id,
            "parent_family_id": str(row["family_id"]),
            "node_id": int(row["node_id"]),
            "event_ids": surviving,
            "member_count": len(surviving),
            "parent_member_count": len(original),
            "parent_rank": len(successor_candidates) + dropped_families + 1,
        })

    mechanism_active = changed_families > 0
    req(mechanism_active, "member-denoise mechanism inactive")
    successor_membership_sha = successor_hash(successor_candidates)

    # Persist exact memberships/order BEFORE using hidden shower labels.
    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_SPORADIC_MEMBER_DENOISE_V1",
        "parent_run": 31852836840,
        "parent_artifact": 9238142199,
        "parent_candidate_count": EXPECTED_PARENT_COUNT,
        "parent_ordered_membership_sha256": WINNER_ORDERED_MEMBERSHIP_SHA,
        "weights_run": 31912528972,
        "weights_artifact": 9254119364,
        "weights_sha256": WEIGHTS_SHA,
        "weight_threshold": WEIGHT_THRESHOLD,
        "threshold_semantics": "retain iff frozen local density contrast > 1 versus seasonal controls",
        "minimum_surviving_members": MIN_CLUSTER_SIZE,
        "ranking_changed": False,
        "hdbscan_recomputed": False,
        "successor_candidate_count": len(successor_candidates),
        "successor_ordered_membership_sha256": successor_membership_sha,
        "changed_families": changed_families,
        "dropped_families": dropped_families,
        "removed_members": removed_members,
        "successor_candidates": successor_candidates,
        "events_total": len(events),
        "events_by_year": {str(y): sum(int(e["year"]) == y for e in events) for y in YEARS},
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
    prelabel_path = a.output / "SPORADIC_MEMBER_DENOISE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Hidden labels are used only after the successor memberships and inherited order are durable.
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled event IDs")

    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    successor_total_at100 = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total_at100 - EXPECTED_PARENT_TOTAL_AT100
    passed = bool(
        mechanism_active
        and successor_total_at100 >= REQUIRED_TOTAL_AT100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_SPORADIC_MEMBER_DENOISE_V1_GMN_DEVELOPMENT" if passed else "FAIL_SPORADIC_MEMBER_DENOISE_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "parent_candidate_count": EXPECTED_PARENT_COUNT,
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": WINNER_ORDERED_MEMBERSHIP_SHA,
        "successor_ordered_membership_sha256": successor_membership_sha,
        "mechanism_active": mechanism_active,
        "changed_families": changed_families,
        "dropped_families": dropped_families,
        "removed_members": removed_members,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "parent_total_recovered_at_100": EXPECTED_PARENT_TOTAL_AT100,
        "successor_total_recovered_at_100": successor_total_at100,
        "recovered_at_100_gain": gain,
        "required_gain": REQUIRED_TOTAL_AT100 - EXPECTED_PARENT_TOTAL_AT100,
        "weight_threshold": WEIGHT_THRESHOLD,
        "ranking_changed": False,
        "hdbscan_recomputed": False,
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
    (a.output / "SPORADIC_MEMBER_DENOISE_V1_GMN_DEVELOPMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "parent_total_at100": EXPECTED_PARENT_TOTAL_AT100,
        "successor_total_at100": successor_total_at100,
        "gain": gain,
        "changed_families": changed_families,
        "dropped_families": dropped_families,
        "removed_members": removed_members,
        "successor_candidate_count": len(successor_candidates),
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
