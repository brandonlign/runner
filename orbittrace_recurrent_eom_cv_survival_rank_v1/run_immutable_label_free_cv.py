#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

N_FOLDS = 10
KS = (25, 50, 100)
BLIND = [20.0, 55.0]
FULL_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
FULL_PARENT_COUNT = 2097
FULL_PARENT_ORDERED_MEMBERSHIP_SHA = "b903f2a4b653ef240043d2d6a2cfe6163b62ecf2d837bddf727249e92e467b01"
FOLD_SOURCE_RUN = 31859724335


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def bucket(event_id: str) -> int:
    digest = hashlib.sha256(str(event_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % N_FOLDS


def full_membership_signature(candidates: list[dict[str, Any]]) -> str:
    rows = []
    for c in candidates:
        ids = list(map(str, c["event_ids"]))
        rows.append({
            "family_id": str(c["family_id"]),
            "node_id": int(c["node_id"]),
            "member_count": int(c["member_count"]),
            "event_ids": ids,
        })
    rows.sort(key=lambda x: x["family_id"])
    return canonical_sha(rows)


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(c["family_id"]) for c in candidates).encode()).hexdigest()


def validate_access_false(payload: dict[str, Any], context: str) -> None:
    req(payload.get("blind_exclusion") == BLIND, f"{context}: blind exclusion changed")
    for key in (
        "target_information_access", "target_region_events_accessed", "sonotaco_2013_2014_access",
        "asfn_access", "efn_access", "maarsy_scientific_access", "dms_scientific_access",
    ):
        req(payload.get(key) is False, f"{context}: forbidden access {key}={payload.get(key)!r}")
    amos = payload.get("amos_2023_2024_access", payload.get("amos_access"))
    req(amos is False, f"{context}: AMOS access not false")


def validate_full_parent(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    req(sha(path) == FULL_PRELABEL_SHA, "immutable full-parent prelabel SHA changed")
    payload = json.loads(path.read_text())
    req(payload.get("scientific_role") == "PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1", "wrong full-parent prelabel role")
    validate_access_false(payload, "full parent")
    req(int(payload.get("parent_candidate_count")) == FULL_PARENT_COUNT, "full parent candidate count changed")
    req(payload.get("parent_ordered_membership_sha256") == FULL_PARENT_ORDERED_MEMBERSHIP_SHA, "full parent ordered-membership SHA changed")
    candidates = payload.get("parent_candidates")
    req(isinstance(candidates, list) and len(candidates) == FULL_PARENT_COUNT, "missing immutable full parent candidates")
    seen_ids: set[str] = set()
    seen_families: set[str] = set()
    for c in candidates:
        family_id = str(c["family_id"])
        req(family_id not in seen_families, "duplicate full parent family ID")
        seen_families.add(family_id)
        ids = list(map(str, c["event_ids"]))
        req(len(ids) == int(c["member_count"]) and len(ids) == len(set(ids)), f"full parent membership malformed: {family_id}")
        req(not (seen_ids & set(ids)), "full parent flat memberships overlap")
        seen_ids.update(ids)
        rec = float(c["recurrent_stability"])
        req(math.isfinite(rec) and rec >= 0.0, f"invalid recurrent stability {family_id}")
    return payload, candidates


def load_folds(root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    folds: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for fold in range(N_FOLDS):
        matches = list(root.rglob(f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{fold}_PRELABEL.json"))
        req(len(matches) == 1, f"expected one immutable fold-{fold} prelabel, got {matches}")
        path = matches[0]
        payload = json.loads(path.read_text())
        req(payload.get("scientific_role") == "PRELABEL_DENSITY_SYNC_GMN_TRAIN_CV_V1", f"wrong fold-{fold} role")
        req(int(payload.get("fold")) == fold, f"fold-{fold} identity mismatch")
        validate_access_false(payload, f"fold {fold}")
        candidates = payload.get("parent_candidates")
        req(isinstance(candidates, list) and candidates, f"missing fold-{fold} recurrent parent candidates")
        req(int(payload.get("parent_candidate_count")) == len(candidates), f"fold-{fold} candidate count mismatch")
        event_owner: dict[str, int] = {}
        candidate_sets: list[set[str]] = []
        for i, c in enumerate(candidates):
            ids = set(map(str, c["event_ids"]))
            req(len(ids) == int(c["member_count"]), f"fold-{fold} member count mismatch")
            for eid in ids:
                req(eid not in event_owner, f"fold-{fold} flat parent memberships overlap")
                event_owner[eid] = i
            candidate_sets.append(ids)
        folds.append({
            "fold": fold,
            "candidate_count": len(candidates),
            "event_owner": event_owner,
            "candidate_sets": candidate_sets,
            "events_removed": int(payload["events_removed"]),
            "events_retained": int(payload["events_retained"]),
            "parent_ordered_membership_sha256": str(payload["parent_ordered_membership_sha256"]),
        })
        hashes[str(fold)] = sha(path)
    return folds, hashes


def best_jaccard(full_members: set[str], fold: int, fold_info: dict[str, Any]) -> float:
    retained = {eid for eid in full_members if bucket(eid) != fold}
    req(retained, f"full candidate became empty in deletion fold {fold}")
    overlaps: Counter[int] = Counter()
    event_owner: dict[str, int] = fold_info["event_owner"]
    for eid in retained:
        idx = event_owner.get(eid)
        if idx is not None:
            overlaps[idx] += 1
    if not overlaps:
        return 0.0
    candidate_sets: list[set[str]] = fold_info["candidate_sets"]
    best = 0.0
    for idx, overlap in overlaps.items():
        other = candidate_sets[idx]
        union = len(retained) + len(other) - overlap
        req(union > 0, "invalid Jaccard union")
        value = overlap / union
        if value > best:
            best = value
    req(0.0 <= best <= 1.0 and math.isfinite(best), "invalid held-out Jaccard")
    return float(best)


def ranked_rows(parent_candidates: list[dict[str, Any]], survival: np.ndarray) -> list[dict[str, Any]]:
    req(survival.shape == (len(parent_candidates),), "survival vector shape changed")
    rows = []
    for i, c in enumerate(parent_candidates):
        rec = float(c["recurrent_stability"])
        s = float(survival[i])
        req(math.isfinite(s) and 0.0 <= s <= 1.0, "invalid survival value")
        x = copy.deepcopy(c)
        x["parent_rank"] = i + 1
        x["cv_survival"] = s
        x["cv_survival_score"] = rec * s
        rows.append(x)
    rows.sort(key=lambda c: (
        -float(c["cv_survival_score"]),
        -float(c["recurrent_stability"]),
        -float(c["cv_survival"]),
        -int(c["member_count"]),
        str(c["family_id"]),
    ))
    for rank, c in enumerate(rows, 1):
        c["rank"] = rank
    return rows


def topk_heldout_mean(order_indices: list[int], heldout: np.ndarray, k: int) -> float:
    req(k <= len(order_indices), "K exceeds candidate count")
    vals = [float(heldout[i]) for i in order_indices[:k]]
    return float(np.mean(vals))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--full-parent-prelabel", type=Path, required=True)
    p.add_argument("--fold-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    full_payload, parent_candidates = validate_full_parent(a.full_parent_prelabel)
    folds, fold_prelabel_sha = load_folds(a.fold_root)

    jaccard = np.zeros((len(parent_candidates), N_FOLDS), dtype=np.float64)
    for i, c in enumerate(parent_candidates):
        members = set(map(str, c["event_ids"]))
        for fold in range(N_FOLDS):
            jaccard[i, fold] = best_jaccard(members, fold, folds[fold])

    parent_ids = [str(c["family_id"]) for c in parent_candidates]
    family_to_index = {fid: i for i, fid in enumerate(parent_ids)}
    req(len(family_to_index) == len(parent_ids), "duplicate full parent family IDs")
    parent_order_indices = list(range(len(parent_candidates)))

    fold_rows = []
    top100_wins = 0
    for heldout_fold in range(N_FOLDS):
        training_cols = [f for f in range(N_FOLDS) if f != heldout_fold]
        training_survival = np.mean(jaccard[:, training_cols], axis=1)
        successor_rows = ranked_rows(parent_candidates, training_survival)
        successor_order_indices = [family_to_index[str(c["family_id"])] for c in successor_rows]
        heldout = jaccard[:, heldout_fold]
        parent_k = {str(k): topk_heldout_mean(parent_order_indices, heldout, k) for k in KS}
        successor_k = {str(k): topk_heldout_mean(successor_order_indices, heldout, k) for k in KS}
        delta_k = {str(k): successor_k[str(k)] - parent_k[str(k)] for k in KS}
        if delta_k["100"] > 0.0:
            top100_wins += 1
        fold_rows.append({
            "heldout_fold": heldout_fold,
            "parent_topk_mean_jaccard": parent_k,
            "successor_topk_mean_jaccard": successor_k,
            "delta_topk_mean_jaccard": delta_k,
            "successor_order_sha256": order_sha(successor_rows),
        })

    full_survival = np.mean(jaccard, axis=1)
    full_successor = ranked_rows(parent_candidates, full_survival)
    full_parent_order_sha = order_sha(parent_candidates)
    full_successor_order_sha = order_sha(full_successor)
    req(full_successor_order_sha != full_parent_order_sha, "CV-survival full order is identical to parent")

    mean_parent = {str(k): float(np.mean([r["parent_topk_mean_jaccard"][str(k)] for r in fold_rows])) for k in KS}
    mean_successor = {str(k): float(np.mean([r["successor_topk_mean_jaccard"][str(k)] for r in fold_rows])) for k in KS}
    mean_delta = {str(k): mean_successor[str(k)] - mean_parent[str(k)] for k in KS}
    parent_top100_by_fold = [r["parent_topk_mean_jaccard"]["100"] for r in fold_rows]
    successor_top100_by_fold = [r["successor_topk_mean_jaccard"]["100"] for r in fold_rows]
    median_parent_top100 = float(np.median(parent_top100_by_fold))
    median_successor_top100 = float(np.median(successor_top100_by_fold))

    gates = {
        "exact_parent_count_2097": len(parent_candidates) == FULL_PARENT_COUNT,
        "full_order_changed": full_successor_order_sha != full_parent_order_sha,
        "mean_top25_not_lower": mean_successor["25"] >= mean_parent["25"],
        "mean_top50_not_lower": mean_successor["50"] >= mean_parent["50"],
        "mean_top100_not_lower": mean_successor["100"] >= mean_parent["100"],
        "median_top100_not_lower": median_successor_top100 >= median_parent_top100,
        "top100_strict_fold_wins_at_least_6_of_10": top100_wins >= 6,
        "mean_top100_strictly_higher": mean_successor["100"] > mean_parent["100"],
    }
    passed = all(gates.values())
    verdict = "PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_LABEL_FREE_CV" if passed else "FAIL_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_LABEL_FREE_CV"

    prelabel = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_IMMUTABLE_PRELABEL",
        "scientific_role": "IMMUTABLE_PARENT_PLUS_TEN_FOLD_LABEL_FREE_CV_ONLY",
        "full_parent_prelabel_sha256": FULL_PRELABEL_SHA,
        "full_parent_candidate_count": len(parent_candidates),
        "full_parent_recorded_ordered_membership_sha256": full_payload["parent_ordered_membership_sha256"],
        "full_parent_membership_signature_sha256": full_membership_signature(parent_candidates),
        "full_parent_order_sha256": full_parent_order_sha,
        "fold_source_run": FOLD_SOURCE_RUN,
        "fold_prelabel_sha256": fold_prelabel_sha,
        "fold_metadata": [{k: v for k, v in f.items() if k not in {"event_owner", "candidate_sets"}} for f in folds],
        "score": "recurrent_stability * mean(max retained-membership Jaccard across exact ten deletion folds)",
        "leave_one_fold_out_rule": "heldout fold excluded from survival score used to rank that fold",
        "k_values": list(KS),
        "full_successor_order_sha256": full_successor_order_sha,
        "full_successor_candidates": full_successor,
        "jaccard_matrix_sha256": canonical_sha(jaccard.tolist()),
        "blind_exclusion": BLIND,
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_IMMUTABLE_PRELABEL.json"
    prelabel_sha = dump(prelabel_path, prelabel)

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_LABEL_FREE_CV_RESULT",
        "scientific_role": "OWNER_REOPENED_EXPOSED_METHOD_DEVELOPMENT_LABEL_FREE_ONLY",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "fold_results": fold_rows,
        "mean_parent_topk_heldout_jaccard": mean_parent,
        "mean_successor_topk_heldout_jaccard": mean_successor,
        "mean_delta_topk_heldout_jaccard": mean_delta,
        "median_parent_top100_heldout_jaccard": median_parent_top100,
        "median_successor_top100_heldout_jaccard": median_successor_top100,
        "top100_strict_fold_wins": top100_wins,
        "gates": gates,
        "blind_exclusion": BLIND,
        "post_result_parameter_search": False,
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_LABEL_FREE_CV_RESULT.json"
    result_sha = dump(result_path, result)

    print(json.dumps({
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "result_sha256": result_sha,
        "mean_parent": mean_parent,
        "mean_successor": mean_successor,
        "mean_delta": mean_delta,
        "median_parent_top100": median_parent_top100,
        "median_successor_top100": median_successor_top100,
        "top100_strict_fold_wins": top100_wins,
        "gates": gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
