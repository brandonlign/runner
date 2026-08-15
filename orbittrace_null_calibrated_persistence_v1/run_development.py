#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np

import recurrent_eom as reom
from density_synchronous_eom import density_synchronous_stability
from null_calibration import (
    NULL_REPLICATES,
    calibrate_candidates,
    permuted_solar_longitude_matrix,
)

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
EXPECTED_PARENT_COUNT = 2094
REQUIRED_TOTAL_AT100_GAIN = 5
PARENT_PRELABEL_SHA256 = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
PARENT_RESULT_SHA256 = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
EXPECTED_PARENT = {
    "2022": {
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7873334042799703,
        "mrr": 0.022505373166085363,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "recovered_at_50": 46,
        "recovered_at_100": 90,
        "top100_dominant_precision": 0.7898245986099988,
        "mrr": 0.02203028490649908,
        "fragmentation_median_top500": 1.0,
    },
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_parent_candidates(rows: Any, accessible_ids: set[str] | None = None) -> list[dict[str, Any]]:
    req(isinstance(rows, list), "frozen parent candidates are not a list")
    req(len(rows) == EXPECTED_PARENT_COUNT, f"frozen parent candidate count changed: {len(rows)}")
    out: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    for i, raw in enumerate(rows):
        req(isinstance(raw, dict), f"parent candidate {i} is not an object")
        for key in ("family_id", "event_ids", "member_count", "synchronous_stability", "ordinary_stability"):
            req(key in raw, f"parent candidate {i} missing {key}")
        family_id = str(raw["family_id"])
        req(family_id not in seen_families, f"duplicate frozen parent family ID {family_id}")
        seen_families.add(family_id)
        ids = [str(x) for x in raw["event_ids"]]
        req(ids == sorted(ids), f"parent candidate {family_id} event IDs are not frozen-sorted")
        req(len(ids) == len(set(ids)), f"parent candidate {family_id} repeats an event ID")
        req(int(raw["member_count"]) == len(ids), f"parent candidate {family_id} member count mismatch")
        req(len(ids) >= MIN_CLUSTER_SIZE, f"parent candidate {family_id} below frozen minimum")
        s = float(raw["synchronous_stability"])
        o = float(raw["ordinary_stability"])
        req(np.isfinite(s) and s >= 0.0, f"parent candidate {family_id} has invalid synchronous stability")
        req(np.isfinite(o) and o >= 0.0, f"parent candidate {family_id} has invalid ordinary stability")
        if accessible_ids is not None:
            missing = [eid for eid in ids if eid not in accessible_ids]
            req(not missing, f"parent candidate {family_id} contains IDs outside accessible GMN: {missing[:3]}")
        out.append({
            "family_id": family_id,
            "node_id": int(raw["node_id"]) if "node_id" in raw else None,
            "event_ids": ids,
            "member_count": len(ids),
            "synchronous_stability": s,
            "ordinary_stability": o,
        })
    return out


def null_rows_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    synchronous: dict[float, float],
) -> list[tuple[int, float]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "null compact labels no longer map contiguously to nodes")
    rows: list[tuple[int, float]] = []
    for lab, node in enumerate(selected_nodes):
        n = int(np.sum(labels == lab))
        req(n >= MIN_CLUSTER_SIZE, f"null selected cluster below minimum: node={node}")
        s = float(synchronous[float(node)])
        req(np.isfinite(s) and s >= 0.0, f"invalid null synchronous stability: node={node}, s={s}")
        rows.append((n, s))
    return rows


def verify_parent_metrics(metrics: dict[str, dict[str, Any]], frozen_result: dict[str, Any]) -> None:
    req(frozen_result.get("verdict") == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "frozen #1263 result verdict changed")
    req(int(frozen_result.get("successor_candidate_count", -1)) == EXPECTED_PARENT_COUNT, "frozen #1263 result candidate count changed")
    frozen_metrics = frozen_result.get("successor_metrics")
    req(isinstance(frozen_metrics, dict), "frozen #1263 result lacks successor metrics")
    for year, expected in EXPECTED_PARENT.items():
        got = metrics[year]
        archived = frozen_metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}")
            req(int(got[key]) == int(archived[key]), f"reevaluated parent {year} {key} differs from frozen result")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)), f"#1263 parent {year} {key} changed: {got[key]} != {expected[key]}")
            req(bool(np.isclose(float(got[key]), float(archived[key]), rtol=0.0, atol=1e-15)), f"reevaluated parent {year} {key} differs from frozen result")


def fit_hdbscan(X: np.ndarray) -> hdbscan.HDBSCAN:
    return hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent_runner = load_module(a.parent_runner, "ncp_frozen_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(parent_runner.MIN_CLUSTER_SIZE == MIN_CLUSTER_SIZE, "parent min_cluster_size changed")
    req(parent_runner.MIN_SAMPLES == MIN_SAMPLES, "parent min_samples changed")
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "exact #1263 parent prelabel hash changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "exact #1263 parent result hash changed")

    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    parent_result = json.loads(a.parent_result_json.read_text())
    req(parent_prelabel.get("scientific_role") == "PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1", "wrong #1263 parent prelabel role")
    req(int(parent_prelabel.get("successor_candidate_count", -1)) == EXPECTED_PARENT_COUNT, "wrong #1263 parent prelabel candidate count")
    req(parent_prelabel.get("blind_exclusion") == [20.0, 55.0], "#1263 parent prelabel blind interval changed")
    for obj in (parent_prelabel, parent_result):
        for key in ("target_information_access", "target_region_events_accessed", "sonotaco_2013_2014_access", "asfn_access", "efn_access", "amos_access", "maarsy_scientific_access", "dms_scientific_access"):
            req(obj.get(key) is False, f"frozen parent artifact firewall changed: {key}")
    parent_candidates_archived = validate_parent_candidates(parent_prelabel.get("successor_candidates"))
    parent_order_sha = ordered_membership_sha(parent_candidates_archived)
    req(parent_order_sha == str(parent_prelabel.get("successor_ordered_membership_sha256")), "frozen #1263 parent order hash does not self-verify")

    qmod = parent_runner.load_module(a.quality_source, "ncp_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = parent_runner.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = parent_runner.MONTH_KEYS
    support.CORPUS = "orbittrace-null-calibrated-persistence-v1-development-2022-2023-target-excluded"
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
    sols = np.asarray([e["sol"] for e in events], dtype=float)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")
    accessible_ids = {str(e["id"]) for e in events}
    parent_candidates = validate_parent_candidates(parent_candidates_archived, accessible_ids)
    req(ordered_membership_sha(parent_candidates) == parent_order_sha, "frozen parent order changed after accessible-ID verification")

    # Survey-preserving coherence-destroying null ensemble. The real parent
    # catalogue is not recomputed: exact #1263 binding memberships/stabilities
    # are rehydrated above from the pinned prelabel artifact.
    null_replicates: list[list[tuple[int, float]]] = []
    null_reports: list[dict[str, Any]] = []
    for rep in range(NULL_REPLICATES):
        Xnull, perm_report = permuted_solar_longitude_matrix(X, sols, years, rep)
        null_model = fit_hdbscan(Xnull)
        null_tree = null_model.condensed_tree_._raw_tree
        null_sync, _null_annual, _null_reconstructed = density_synchronous_stability(null_tree, years)
        null_labels = reom.eom_labels(null_tree, null_sync)
        null_nodes = reom.selected_eom_nodes(null_tree, null_sync)
        rows = null_rows_from_labels(null_labels, null_nodes, null_sync)
        req(len(rows) > 0, f"null replicate {rep} selected zero candidates")
        null_replicates.append(rows)
        null_reports.append({
            **perm_report,
            "candidate_count": len(rows),
            "condensed_tree_sha256": tree_sha(null_tree),
            "max_member_count": max(int(n) for n, _s in rows),
            "max_synchronous_stability": max(float(s) for _n, s in rows),
            "candidates": [{"member_count": int(n), "synchronous_stability": float(s)} for n, s in rows],
        })
        print(json.dumps({
            "null_replicate": rep,
            "candidate_count": len(rows),
            "moved_2022": perm_report["years"]["2022"]["moved_fraction"],
            "moved_2023": perm_report["years"]["2023"]["moved_fraction"],
        }, sort_keys=True), flush=True)
        del Xnull, null_model, null_tree, null_sync, null_labels, null_nodes, rows
        gc.collect()

    successor_candidates = calibrate_candidates(parent_candidates, null_replicates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(successor_order_sha != parent_order_sha)
    parent_universe = {tuple(c["event_ids"]) for c in parent_candidates}
    successor_universe = {tuple(c["event_ids"]) for c in successor_candidates}
    req(parent_universe == successor_universe, "null calibration changed real candidate memberships")

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_SURVEY_NULL_CALIBRATED_PERSISTENCE_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "parent_source": {
            "binding_run": 31852836840,
            "artifact": 9238142199,
            "prelabel_sha256": PARENT_PRELABEL_SHA256,
            "result_sha256": PARENT_RESULT_SHA256,
        },
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "membership_universe_identical": True,
        "mechanism_active": mechanism_active,
        "null_replicates": NULL_REPLICATES,
        "null_candidate_counts": [len(x) for x in null_replicates],
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_AT100_GAIN,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "null_evidence": null_reports,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "truth_evaluated_when_written": False,
    }
    prelabel_path = a.output / "NULL_CALIBRATED_PERSISTENCE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Hidden known-shower labels are first used here, after the complete null
    # ensemble and successor order are persisted above.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled IDs")
    parent_metrics = {str(y): parent_runner.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    verify_parent_metrics(parent_metrics, parent_result)
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent_runner.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    parent_total = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total == 179, f"#1263 parent total changed: {parent_total}")
    total_gain = successor_total - parent_total
    strong_gain = bool(total_gain >= REQUIRED_TOTAL_AT100_GAIN)
    passed = bool(mechanism_active and strong_gain and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT" if passed else "FAIL_NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_source": prelabel["parent_source"],
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "membership_universe_identical": True,
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "null_replicates": NULL_REPLICATES,
        "null_candidate_counts": [len(x) for x in null_replicates],
        "parent_total_recovered_at_100": parent_total,
        "successor_total_recovered_at_100": successor_total,
        "total_recovered_at_100_gain": total_gain,
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_AT100_GAIN,
        "strong_gain_gate": strong_gain,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "sole_successor_objective": "mean_empirical_pareto_tail_rate_under_16_within_year_solar_longitude_permutation_nulls",
        "post_result_parameter_search": False,
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
    result_path = a.output / "NULL_CALIBRATED_PERSISTENCE_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "gain": total_gain,
        "parent_total": parent_total,
        "successor_total": successor_total,
        "null_candidate_counts": result["null_candidate_counts"],
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
