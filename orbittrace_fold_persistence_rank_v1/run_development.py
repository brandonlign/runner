#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
N_FOLDS = 10
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WINNER_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
WINNER_CANDIDATE_COUNT = 2094
CV_RUN_ID = 31859724335
BASELINE_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bucket(event_id: str) -> int:
    digest = hashlib.sha256(str(event_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % N_FOLDS


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


def find_unique(root: Path, pattern: str) -> Path:
    hits = sorted(root.glob(pattern))
    req(len(hits) == 1, f"expected exactly one {pattern}, found {len(hits)}")
    return hits[0]


def load_fold(root: Path, fold: int) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    pre_path = find_unique(root, f"**/DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{fold}_PRELABEL.json")
    res_path = find_unique(root, f"**/DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{fold}.json")
    pre = json.loads(pre_path.read_text())
    res = json.loads(res_path.read_text())
    req(pre["scientific_role"] == "PRELABEL_DENSITY_SYNC_GMN_TRAIN_CV_V1", f"fold {fold} prelabel role changed")
    req(int(pre["fold"]) == fold and int(res["fold"]) == fold, f"fold {fold} identity mismatch")
    req(res["prelabel_sha256"] == sha(pre_path), f"fold {fold} result/prelabel hash mismatch")
    req(pre["fold_rule"] == "uint64_be(sha256(utf8(event_id))[0:8]) mod 10", f"fold {fold} rule changed")
    req(isinstance(pre["successor_candidates"], list) and pre["successor_candidates"], f"fold {fold} has no successor candidates")
    for obj in (pre, res):
        for key in (
            "target_information_access",
            "target_region_events_accessed",
            "sonotaco_2013_2014_access",
            "amos_2023_2024_access",
            "asfn_access",
            "efn_access",
            "maarsy_scientific_access",
            "dms_scientific_access",
        ):
            req(obj[key] is False, f"fold {fold} firewall violation: {key}")
    return pre, res, pre_path, res_path


def build_fold_index(candidates: list[dict[str, Any]], fold: int) -> tuple[dict[str, int], list[int], list[str]]:
    owner: dict[str, int] = {}
    sizes: list[int] = []
    family_ids: list[str] = []
    for idx, row in enumerate(candidates):
        members = [str(x) for x in row["event_ids"]]
        req(int(row["member_count"]) == len(members), f"fold {fold} candidate member_count mismatch")
        req(len(set(members)) == len(members), f"fold {fold} duplicate ID within candidate")
        for eid in members:
            req(bucket(eid) != fold, f"fold {fold} candidate contains removed-bucket event")
            req(eid not in owner, f"fold {fold} selected candidates overlap on event {eid}")
            owner[eid] = idx
        sizes.append(len(members))
        family_ids.append(str(row["family_id"]))
    return owner, sizes, family_ids


def best_jaccard_for_candidate(
    full_members: list[str],
    fold: int,
    owner: dict[str, int],
    fold_sizes: list[int],
    family_ids: list[str],
) -> tuple[float, str | None, int, int]:
    surviving = [eid for eid in full_members if bucket(eid) != fold]
    n_surv = len(surviving)
    if n_surv == 0:
        return 0.0, None, 0, 0
    counts: dict[int, int] = defaultdict(int)
    for eid in surviving:
        idx = owner.get(eid)
        if idx is not None:
            counts[idx] += 1
    if not counts:
        return 0.0, None, n_surv, 0

    best_score = -1.0
    best_family: str | None = None
    best_intersection = 0
    for idx, intersection in counts.items():
        union = n_surv + fold_sizes[idx] - intersection
        req(union > 0, "nonpositive Jaccard union")
        score = float(intersection) / float(union)
        fid = family_ids[idx]
        if score > best_score or (score == best_score and (best_family is None or fid < best_family)):
            best_score = score
            best_family = fid
            best_intersection = intersection
    req(0.0 <= best_score <= 1.0, f"invalid best Jaccard {best_score}")
    return best_score, best_family, n_surv, best_intersection


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--fold-root", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # Build the complete new score/order from already-frozen unlabeled artifacts only.
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "binding winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "binding winner result changed")
    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner prelabel membership hash changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner result membership hash changed")
    winner_candidates = winner_pre["successor_candidates"]
    req(len(winner_candidates) == WINNER_CANDIDATE_COUNT, f"winner candidate count changed: {len(winner_candidates)}")
    req(ordered_membership_sha(winner_candidates) == WINNER_MEMBERSHIP_SHA, "winner candidates no longer reproduce binding order")
    baseline = winner_result["successor_metrics"]
    req(int(baseline["2022"]["recovered_at_100"]) == 89, "binding 2022 @100 changed")
    req(int(baseline["2023"]["recovered_at_100"]) == 90, "binding 2023 @100 changed")
    req(sum(int(baseline[str(y)]["recovered_at_100"]) for y in YEARS) == BASELINE_TOTAL_AT100, "binding total changed")
    winner_multiset_sha = unordered_candidate_multiset_sha(winner_candidates)

    folds: dict[int, dict[str, Any]] = {}
    fold_manifest: dict[str, Any] = {}
    fold_indexes: dict[int, tuple[dict[str, int], list[int], list[str]]] = {}
    for fold in range(N_FOLDS):
        pre, res, pre_path, res_path = load_fold(a.fold_root, fold)
        folds[fold] = pre
        fold_indexes[fold] = build_fold_index(pre["successor_candidates"], fold)
        fold_manifest[str(fold)] = {
            "prelabel_sha256": sha(pre_path),
            "result_sha256": sha(res_path),
            "successor_candidate_count": int(pre["successor_candidate_count"]),
            "events_retained": int(pre["events_retained"]),
            "events_removed": int(pre["events_removed"]),
            "mechanism_active": bool(pre["mechanism_active"]),
        }

    successor: list[dict[str, Any]] = []
    persistence_values: list[float] = []
    for raw in winner_candidates:
        row = copy.deepcopy(raw)
        full_members = [str(x) for x in row["event_ids"]]
        req(int(row["member_count"]) == len(full_members), "winner candidate member_count mismatch")
        fold_scores: list[float] = []
        fold_matches: list[dict[str, Any]] = []
        for fold in range(N_FOLDS):
            owner, sizes, family_ids = fold_indexes[fold]
            score, matched_fid, n_surv, intersection = best_jaccard_for_candidate(
                full_members, fold, owner, sizes, family_ids
            )
            fold_scores.append(score)
            fold_matches.append({
                "fold": fold,
                "jaccard": score,
                "matched_fold_family_id": matched_fid,
                "surviving_full_members": n_surv,
                "intersection_members": intersection,
            })
        persistence = float(np.mean(np.asarray(fold_scores, dtype=np.float64)))
        req(np.isfinite(persistence) and 0.0 <= persistence <= 1.0, "invalid mean fold persistence")
        row["fold_persistence_mean_jaccard"] = persistence
        row["fold_persistence_scores"] = fold_scores
        row["fold_persistence_matches"] = fold_matches
        successor.append(row)
        persistence_values.append(persistence)

    successor.sort(key=lambda r: (
        -float(r["fold_persistence_mean_jaccard"]),
        -float(r["synchronous_stability"]),
        -float(r["ordinary_stability"]),
        -int(r["member_count"]),
        str(r["family_id"]),
    ))

    successor_multiset_sha = unordered_candidate_multiset_sha(successor)
    successor_order_sha = ordered_membership_sha(successor)
    req(len(successor) == WINNER_CANDIDATE_COUNT, "successor candidate count changed")
    req(successor_multiset_sha == winner_multiset_sha, "candidate content/membership multiset changed")
    req(successor_order_sha != WINNER_MEMBERSHIP_SHA, "fold-persistence ranking did not change order")

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_FOLD_PERSISTENCE_RANK_V1",
        "candidate_source": "exact_frozen_density_synchronous_recurrent_eom_179_winner",
        "perturbation_source_run": CV_RUN_ID,
        "fold_rule": "uint64_be(sha256(utf8(event_id))[0:8]) mod 10",
        "n_folds": N_FOLDS,
        "sole_change": "rank_exact_winner_candidates_by_mean_best_jaccard_across_frozen_deletion_folds",
        "candidate_count": len(successor),
        "winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "successor_ordered_membership_sha256": successor_order_sha,
        "winner_unordered_candidate_multiset_sha256": winner_multiset_sha,
        "successor_unordered_candidate_multiset_sha256": successor_multiset_sha,
        "candidate_memberships_unchanged": True,
        "mechanism_active": True,
        "fold_manifest": fold_manifest,
        "persistence_summary": {
            "min": float(np.min(persistence_values)),
            "median": float(np.median(persistence_values)),
            "mean": float(np.mean(persistence_values)),
            "max": float(np.max(persistence_values)),
        },
        "successor_candidates": successor,
        "catalogue_loaded_before_order_freeze": False,
        "known_shower_labels_indexed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "FOLD_PERSISTENCE_RANK_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after the complete successor order is durable do we load target-excluded GMN truth for evaluation.
    req(sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support result changed")
    qmod = parent.load_module(a.quality_source, "fold_persistence_rank_v1_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-fold-persistence-rank-v1-development-2022-2023-target-excluded"
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
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled event IDs")

    successor_metrics = {str(y): parent.metrics(successor, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor_metrics[str(y)]) for y in YEARS}
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    structural = {
        "exact_candidate_count": len(successor) == WINNER_CANDIDATE_COUNT,
        "exact_candidate_multiset_unchanged": successor_multiset_sha == winner_multiset_sha,
        "all_ten_folds_verified": sorted(int(x) for x in fold_manifest) == list(range(N_FOLDS)),
        "all_persistence_scores_bounded": all(0.0 <= x <= 1.0 and np.isfinite(x) for x in persistence_values),
        "order_changed": successor_order_sha != WINNER_MEMBERSHIP_SHA,
        "prelabel_frozen_before_catalogue_load": True,
    }
    passed = bool(
        all(structural.values())
        and successor_total >= REQUIRED_TOTAL_AT100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_FOLD_PERSISTENCE_RANK_V1_GMN_DEVELOPMENT" if passed else "FAIL_FOLD_PERSISTENCE_RANK_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "sole_change": prelabel["sole_change"],
        "candidate_count": len(successor),
        "persistence_summary": prelabel["persistence_summary"],
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
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "FOLD_PERSISTENCE_RANK_V1_GMN_DEVELOPMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "candidate_count": len(successor),
        "persistence_summary": prelabel["persistence_summary"],
        "baseline_total_at100": BASELINE_TOTAL_AT100,
        "successor_total_at100": successor_total,
        "gain": gain,
        "2022": {k: successor_metrics["2022"][k] for k in ("recovered_at_50", "recovered_at_100", "top100_dominant_precision", "mrr", "fragmentation_median_top500")},
        "2023": {k: successor_metrics["2023"][k] for k in ("recovered_at_50", "recovered_at_100", "top100_dominant_precision", "mrr", "fragmentation_median_top500")},
        "structural_gates": structural,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
