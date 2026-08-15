#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND
MIN_CLUSTER_SIZE = parent_runner.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent_runner.MIN_SAMPLES
N_FOLDS = 10


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bucket(event_id: str) -> int:
    digest = hashlib.sha256(str(event_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % N_FOLDS


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def load_champion_runner(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("density_sync_cv_champion_runner", path)
    req(spec is not None and spec.loader is not None, f"cannot import champion runner {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fold", type=int, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--champion-runner", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    req(0 <= a.fold < N_FOLDS, f"fold must be 0..{N_FOLDS-1}")
    a.output.mkdir(parents=True, exist_ok=True)

    # Immutable GMN runtime support inherited from the promoted parent.
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, f"density_sync_cv_gmn_utility_f{a.fold}")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = f"orbittrace-density-sync-gmn-train-cv-v1-fold-{a.fold}-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    full_events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        full_events.extend(rows)
    req(len({e["id"] for e in full_events}) == len(full_events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in full_events), "protected region survived parser")

    fold_counts_full = {f: 0 for f in range(N_FOLDS)}
    for e in full_events:
        fold_counts_full[bucket(e["id"])] += 1
    req(sum(fold_counts_full.values()) == len(full_events), "hash fold assignment lost events")

    events = [e for e in full_events if bucket(e["id"]) != a.fold]
    removed = [e for e in full_events if bucket(e["id"]) == a.fold]
    req(len(events) + len(removed) == len(full_events), "fold partition mismatch")
    req(not ({e["id"] for e in events} & {e["id"] for e in removed}), "retained/removed overlap")
    req(all(bucket(e["id"]) == a.fold for e in removed), "wrong event in removed fold")
    req(all(bucket(e["id"]) != a.fold for e in events), "held-out fold survived")

    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    counts_by_year = {str(y): int(np.sum(years == y)) for y in YEARS}
    removed_by_year = {str(y): int(sum(1 for e in removed if e["year"] == y)) for y in YEARS}
    req(all(counts_by_year[str(y)] > 0 for y in YEARS), "a year became empty")

    X = parent_runner.geo_matrix(events)
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    frozen_tree_sha = tree_sha(tree)
    ordinary = compute_stability(tree)

    # Exact recurrent-EOM parent on this deterministic training perturbation.
    parent_recurrent, parent_annual = parent_reom.recurrent_stability(tree, years)
    parent_labels = parent_reom.eom_labels(tree, parent_recurrent)
    parent_nodes = parent_reom.selected_eom_nodes(tree, parent_recurrent)
    parent_candidates = parent_runner.candidates_from_labels(
        parent_labels, parent_nodes, events, ordinary, parent_recurrent, True
    )

    # Exact already-promoted density-synchronous champion on the unchanged hierarchy.
    synchronous, synchronous_parent_annual, annual_reconstructed = density_synchronous_stability(tree, years)
    req(parent_annual == synchronous_parent_annual, "density-synchronous kernel changed parent annual map")
    req(tree_sha(tree) == frozen_tree_sha, "density-synchronous kernel mutated hierarchy")
    successor_labels = parent_reom.eom_labels(tree, synchronous)
    successor_nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    champion_runner = load_champion_runner(a.champion_runner)
    successor_candidates = champion_runner.sync_candidates_from_labels(
        successor_labels, successor_nodes, events, ordinary, synchronous
    )

    parent_order_sha = ordered_membership_sha(parent_candidates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(parent_nodes != successor_nodes or parent_order_sha != successor_order_sha)

    # Freeze all scientific output before opening the already-exposed GMN training labels.
    prelabel = {
        "scientific_role": "PRELABEL_DENSITY_SYNC_GMN_TRAIN_CV_V1",
        "fold": a.fold,
        "fold_rule": "uint64_be(sha256(utf8(event_id))[0:8]) mod 10",
        "events_retained": len(events),
        "events_removed": len(removed),
        "events_retained_by_year": counts_by_year,
        "events_removed_by_year": removed_by_year,
        "full_fold_counts": {str(k): v for k, v in fold_counts_full.items()},
        "condensed_tree_sha256": frozen_tree_sha,
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "parent_annual_eom": {str(k): list(v) for k, v in sorted(parent_annual.items())},
        "reconstructed_annual_eom": {str(k): list(v) for k, v in sorted(annual_reconstructed.items())},
        "synchronous_stability": {str(int(k)): float(v) for k, v in sorted(synchronous.items())},
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{a.fold}_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    parent_metrics = {str(y): parent_runner.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}

    result = {
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_TRAIN_ROBUSTNESS_ONLY",
        "fold": a.fold,
        "prelabel_sha256": prelabel_sha,
        "events_retained_by_year": counts_by_year,
        "events_removed_by_year": removed_by_year,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{a.fold}.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "fold": a.fold,
        "mechanism_active": mechanism_active,
        "events_retained_by_year": counts_by_year,
        "parent": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in parent_metrics.items()},
        "successor": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in successor_metrics.items()},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
