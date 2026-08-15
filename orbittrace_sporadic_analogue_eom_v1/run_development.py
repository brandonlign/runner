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
from density_synchronous_eom import density_synchronous_stability
from sporadic_analogue_eom import (
    ANALOGUE_OFFSETS_DEG,
    K_NEIGHBOURS,
    compute_sporadic_analogue_weights,
    sporadic_analogue_stability,
)

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
EXPECTED_PARENT_COUNT = 2094
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
PARENT_TOTAL_100 = 179
REQUIRED_GAIN_100 = 5


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def candidates_from_score(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    score: dict[float, float],
    family_prefix: str,
    score_name: str,
    member_hash_fn: Any,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        row = {
            "family_id": member_hash_fn(family_prefix, members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            score_name: float(score[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        }
        out.append(row)
    out.sort(key=lambda f: (
        -f[score_name],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def verify_parent_metrics(metrics: dict[str, dict[str, Any]]) -> None:
    for year, expected in EXPECTED_PARENT.items():
        got = metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"champion {year} {key} changed: {got[key]} != {expected[key]}")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)),
                f"champion {year} {key} changed: {got[key]} != {expected[key]}")


def annual_gate(parent: dict[str, Any], successor: dict[str, Any]) -> dict[str, bool]:
    return {
        "recovered_at_50_not_lower": int(successor["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(successor["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": float(successor["top100_dominant_precision"]) >= float(parent["top100_dominant_precision"]),
        "mrr_not_lower": float(successor["mrr"]) >= float(parent["mrr"]),
        "fragmentation_not_higher": float(successor["fragmentation_median_top500"]) <= float(parent["fragmentation_median_top500"]),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent_runner = load_module(a.parent_runner, "sporadic_analogue_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == MIN_CLUSTER_SIZE, "parent min_cluster_size changed")
    req(int(parent_runner.MIN_SAMPLES) == MIN_SAMPLES, "parent min_samples changed")
    req(K_NEIGHBOURS == MIN_SAMPLES, "analogue k no longer inherits min_samples")
    req(ANALOGUE_OFFSETS_DEG == tuple(float(x) for x in range(60, 301, 10)), "seasonal analogue grid changed")

    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "saeom_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-sporadic-analogue-eom-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == 738682, f"pooled accessible event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent_runner.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")

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

    # Reconstruct exact current champion first on the unchanged hierarchy.
    champion_score, _annual_parent, _annual_reconstructed = density_synchronous_stability(tree, years)
    champion_labels = parent_reom.eom_labels(tree, champion_score)
    champion_nodes = parent_reom.selected_eom_nodes(tree, champion_score)
    champion_candidates = candidates_from_score(
        champion_labels, champion_nodes, events, ordinary, champion_score,
        "DSEOM1", "synchronous_stability", parent_runner.member_hash,
    )
    req(len(champion_candidates) == EXPECTED_PARENT_COUNT,
        f"density-sync champion candidate count changed: {len(champion_candidates)}")

    # Sole successor mechanism: seasonally matched local sporadic contrast enters
    # the alive mass used by the density-synchronous hierarchy objective.
    weights, weight_summary = compute_sporadic_analogue_weights(events, X, years, BLIND)
    req(tree_sha(tree) == frozen_tree_sha, "analogue weighting mutated condensed tree")
    weights_path = a.output / "SPORADIC_ANALOGUE_WEIGHTS.npy"
    np.save(weights_path, weights, allow_pickle=False)
    weights_sha = sha(weights_path)

    successor_score = sporadic_analogue_stability(tree, years, weights)
    req(tree_sha(tree) == frozen_tree_sha, "successor stability mutated condensed tree")
    successor_labels = parent_reom.eom_labels(tree, successor_score)
    successor_nodes = parent_reom.selected_eom_nodes(tree, successor_score)
    successor_candidates = candidates_from_score(
        successor_labels, successor_nodes, events, ordinary, successor_score,
        "SAEOM1", "sporadic_analogue_stability", parent_runner.member_hash,
    )

    parent_order_sha = ordered_membership_sha(champion_candidates)
    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(champion_nodes != successor_nodes or parent_order_sha != successor_order_sha)

    prelabel = {
        "scientific_role": "PRETRUTH_FROZEN_SPORADIC_ANALOGUE_EOM_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "analogue_offsets_deg": list(ANALOGUE_OFFSETS_DEG),
        "knn_k": K_NEIGHBOURS,
        "weight_transform": "2*c/(1+c), c=median_analogue_kdist/actual_kdist",
        "weights_npy_sha256": weights_sha,
        "weight_summary": weight_summary,
        "parent_selected_nodes": list(champion_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "parent_candidate_count": len(champion_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "parent_candidates": champion_candidates,
        "successor_candidates": successor_candidates,
        "truth_evaluated_when_written": False,
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
    prelabel_path = a.output / "SPORADIC_ANALOGUE_EOM_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth opens only after complete successor order/memberships and weight array are persisted.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    parent_metrics = {str(y): parent_runner.metrics(champion_candidates, hidden, ids_by_year[y]) for y in YEARS}
    verify_parent_metrics(parent_metrics)
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}

    parent_total = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total == PARENT_TOTAL_100, f"champion total@100 changed: {parent_total}")
    gain = successor_total - parent_total
    passed = bool(
        mechanism_active
        and gain >= REQUIRED_GAIN_100
        and successor_total >= PARENT_TOTAL_100 + REQUIRED_GAIN_100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_SPORADIC_ANALOGUE_EOM_V1_GMN_DEVELOPMENT" if passed else "FAIL_SPORADIC_ANALOGUE_EOM_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "weights_npy_sha256": weights_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(champion_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "parent_total_recovered_at_100": parent_total,
        "successor_total_recovered_at_100": successor_total,
        "total_recovered_at_100_gain": gain,
        "required_total_recovered_at_100_gain": REQUIRED_GAIN_100,
        "weight_summary": weight_summary,
        "analogue_offsets_deg": list(ANALOGUE_OFFSETS_DEG),
        "knn_k": K_NEIGHBOURS,
        "sole_successor_objective": "density_synchronous_alive_mass_weighted_by_seasonal_sporadic_analogue_local_density_contrast",
        "post_result_parameter_search": False,
        "post_result_rescue_authorized": False,
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
    result_path = a.output / "SPORADIC_ANALOGUE_EOM_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "gain": gain,
        "mechanism_active": mechanism_active,
        "parent_count": len(champion_candidates),
        "successor_count": len(successor_candidates),
        "weight_summary": weight_summary,
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
