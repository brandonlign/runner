#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as parent_reom

N_FOLDS = 10
YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
EXPECTED = {
    2022: {
        "recovered_at_25": 22,
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7856486012780942,
        "mrr": 0.022498269587309373,
        "qualified_matches": 236,
        "fragmentation_median_top500": 1.0,
    },
    2023: {
        "recovered_at_25": 23,
        "recovered_at_50": 46,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7867680236864514,
        "mrr": 0.0220239288966045,
        "qualified_matches": 244,
        "fragmentation_median_top500": 1.0,
    },
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bucket(event_id: str) -> int:
    digest = hashlib.sha256(str(event_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % N_FOLDS


def membership_signature(candidates: list[dict[str, Any]]) -> str:
    rows = []
    for c in candidates:
        rows.append({
            "family_id": str(c["family_id"]),
            "node_id": int(c["node_id"]),
            "member_count": int(c["member_count"]),
            "event_ids": list(map(str, c["event_ids"])),
        })
    rows.sort(key=lambda x: x["family_id"])
    return canonical_sha(rows)


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(c["family_id"]) for c in candidates).encode()).hexdigest()


def load_fold_prelabels(root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    folds: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for fold in range(N_FOLDS):
        matches = list(root.rglob(f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{fold}_PRELABEL.json"))
        req(len(matches) == 1, f"expected exactly one immutable prelabel for fold {fold}, got {matches}")
        path = matches[0]
        payload = json.loads(path.read_text())
        req(payload.get("scientific_role") == "PRELABEL_DENSITY_SYNC_GMN_TRAIN_CV_V1", f"wrong fold role {fold}")
        req(int(payload.get("fold")) == fold, f"fold identity mismatch {fold}")
        req(payload.get("blind_exclusion") == [20.0, 55.0], f"fold blind mismatch {fold}")
        for key in (
            "target_information_access", "target_region_events_accessed", "sonotaco_2013_2014_access",
            "amos_2023_2024_access", "asfn_access", "efn_access", "maarsy_scientific_access", "dms_scientific_access",
        ):
            req(payload.get(key) is False, f"forbidden fold access {key} in fold {fold}")
        candidates = payload.get("parent_candidates")
        req(isinstance(candidates, list) and candidates, f"missing recurrent parent candidates fold {fold}")
        # Flat EOM memberships must be disjoint; this also makes survival matching deterministic and cheap.
        seen: set[str] = set()
        for c in candidates:
            ids = list(map(str, c["event_ids"]))
            req(len(ids) == int(c["member_count"]), f"fold {fold} member count mismatch")
            req(len(ids) == len(set(ids)), f"duplicate event within fold {fold} candidate")
            req(not (seen & set(ids)), f"overlapping flat recurrent candidates in fold {fold}")
            seen.update(ids)
        # Successor candidates and any truth-informed fold result are intentionally ignored.
        folds.append({
            "fold": fold,
            "parent_candidates": candidates,
            "events_removed_by_year": payload.get("events_removed_by_year"),
            "events_retained_by_year": payload.get("events_retained_by_year"),
        })
        hashes[str(fold)] = sha(path)
    return folds, hashes


def best_fold_jaccard(full_members: set[str], fold: int, fold_candidates: list[dict[str, Any]]) -> float:
    retained = {eid for eid in full_members if bucket(eid) != fold}
    req(retained, f"full candidate became empty in fold {fold}")

    event_owner: dict[str, int] = {}
    candidate_sets: list[set[str]] = []
    for i, c in enumerate(fold_candidates):
        ids = set(map(str, c["event_ids"]))
        candidate_sets.append(ids)
        for eid in ids:
            req(eid not in event_owner, f"fold {fold} event belongs to multiple flat candidates")
            event_owner[eid] = i

    overlaps: Counter[int] = Counter()
    for eid in retained:
        idx = event_owner.get(eid)
        if idx is not None:
            overlaps[idx] += 1
    if not overlaps:
        return 0.0

    best = 0.0
    for idx, ov in overlaps.items():
        other = candidate_sets[idx]
        union = len(retained) + len(other) - ov
        req(union > 0, "invalid Jaccard union")
        best = max(best, ov / union)
    return float(best)


def rerank(parent_candidates: list[dict[str, Any]], folds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    successor: list[dict[str, Any]] = []
    for parent_rank, c in enumerate(parent_candidates, 1):
        full_members = set(map(str, c["event_ids"]))
        req(len(full_members) == int(c["member_count"]), "full parent candidate member count mismatch")
        recurrent = float(c["recurrent_stability"])
        req(math.isfinite(recurrent) and recurrent >= 0.0, "invalid recurrent stability")
        by_fold = [best_fold_jaccard(full_members, f, folds[f]["parent_candidates"]) for f in range(N_FOLDS)]
        survival = float(np.mean(by_fold))
        req(math.isfinite(survival) and 0.0 <= survival <= 1.0, "invalid CV survival")
        x = copy.deepcopy(c)
        x["parent_rank"] = parent_rank
        x["cv_survival_by_fold"] = by_fold
        x["cv_survival"] = survival
        x["cv_survival_score"] = recurrent * survival
        successor.append(x)

    successor.sort(key=lambda c: (
        -float(c["cv_survival_score"]),
        -float(c["recurrent_stability"]),
        -float(c["cv_survival"]),
        -int(c["member_count"]),
        str(c["family_id"]),
    ))
    for rank, c in enumerate(successor, 1):
        c["rank"] = rank
    return successor


def check_parent_metrics(metrics: dict[str, Any], year: int) -> None:
    exp = EXPECTED[year]
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(metrics[key]) == int(exp[key]), f"parent {year} {key} mismatch: {metrics[key]} != {exp[key]}")
    for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
        req(abs(float(metrics[key]) - float(exp[key])) <= 1e-15, f"parent {year} {key} mismatch")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--fold-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent_runner = load_module(a.parent_runner, "cv_survival_exact_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent HDBSCAN support changed")
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN utility changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")

    folds, fold_prelabel_sha = load_fold_prelabels(a.fold_root)

    qmod = parent_runner.load_module(a.quality_source, "cv_survival_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = parent_runner.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = parent_runner.MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-cv-survival-rank-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(parent_runner.MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} count")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent_runner.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    recurrent, annual = parent_reom.recurrent_stability(tree, years)
    labels = parent_reom.eom_labels(tree, recurrent)
    nodes = parent_reom.selected_eom_nodes(tree, recurrent)
    parent_candidates = parent_runner.candidates_from_labels(labels, nodes, events, ordinary, recurrent, True)
    req(len(parent_candidates) == 2097, f"full recurrent parent count changed: {len(parent_candidates)}")

    successor_candidates = rerank(parent_candidates, folds)
    req(membership_signature(successor_candidates) == membership_signature(parent_candidates), "successor changed parent memberships")
    parent_order = order_sha(parent_candidates)
    successor_order = order_sha(successor_candidates)
    req(successor_order != parent_order, "CV survival mechanism did not change order")

    prelabel = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_PRELABEL",
        "scientific_role": "PRELABEL_TARGET_EXCLUDED_GMN_2022_2023_CV_SURVIVAL_RANK_ONLY",
        "parent_method": "recurrent-EOM HDBSCAN v1",
        "score": "recurrent_stability * mean(max-Jaccard across exact ten pre-existing deletion folds)",
        "fold_source_run": 31859724335,
        "fold_prelabel_sha256": fold_prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_membership_sha256": membership_signature(parent_candidates),
        "successor_membership_sha256": membership_signature(successor_candidates),
        "parent_order_sha256": parent_order,
        "successor_order_sha256": successor_order,
        "mechanism_active": successor_order != parent_order,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual.items())},
        "blind_exclusion": list(BLIND),
        "truth_metrics_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after complete successor order is persisted do the already-exposed GMN development labels enter metrics.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    parent_metrics = {str(y): parent_runner.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    for y in YEARS:
        check_parent_metrics(parent_metrics[str(y)], y)

    gates: dict[str, bool] = {
        "membership_universe_identical": membership_signature(successor_candidates) == membership_signature(parent_candidates),
        "order_changed": successor_order != parent_order,
    }
    strict = False
    for y in YEARS:
        pm = parent_metrics[str(y)]
        sm = successor_metrics[str(y)]
        gates[f"{y}_recovered_at_25_not_lower"] = int(sm["recovered_at_25"]) >= int(pm["recovered_at_25"])
        gates[f"{y}_recovered_at_50_not_lower"] = int(sm["recovered_at_50"]) >= int(pm["recovered_at_50"])
        gates[f"{y}_recovered_at_100_not_lower"] = int(sm["recovered_at_100"]) >= int(pm["recovered_at_100"])
        gates[f"{y}_precision_not_lower"] = float(sm["top100_dominant_precision"]) >= float(pm["top100_dominant_precision"])
        gates[f"{y}_mrr_not_lower"] = float(sm["mrr"]) >= float(pm["mrr"])
        gates[f"{y}_fragmentation_not_higher"] = float(sm["fragmentation_median_top500"]) <= float(pm["fragmentation_median_top500"])
        strict = strict or int(sm["recovered_at_100"]) > int(pm["recovered_at_100"])
        strict = strict or float(sm["top100_dominant_precision"]) > float(pm["top100_dominant_precision"])
        strict = strict or float(sm["mrr"]) > float(pm["mrr"])
    gates["strict_improvement_some_year"] = strict
    passed = all(gates.values())
    verdict = "PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_GMN_DEVELOPMENT" if passed else "FAIL_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_GMN_DEVELOPMENT"

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_RESULT",
        "scientific_role": "OWNER_REOPENED_EXPOSED_GMN_DEVELOPMENT_ONLY",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "parent_order_sha256": parent_order,
        "successor_order_sha256": successor_order,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "result_sha256": sha(result_path),
        "parent": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in parent_metrics.items()},
        "successor": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in successor_metrics.items()},
        "gates": gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
