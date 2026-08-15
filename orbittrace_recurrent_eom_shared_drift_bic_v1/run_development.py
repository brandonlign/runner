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

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes
from shared_drift_bic import (
    aggregate_tree_stats,
    physical_predictor_and_response,
    shared_drift_stability,
)

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_PRELABEL_SHA256 = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
PARENT_RESULT_SHA256 = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def signature(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [tuple(str(x) for x in row["event_ids"]) for row in rows]


def make_successor_candidates(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
    evidence: dict[int, Any],
    parent: Any,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact shared-drift labels do not map to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        ev = evidence[int(node)]
        out.append({
            "family_id": parent.member_hash("REOMBIC1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
            "recurrent_stability": float(recurrent[float(node)]),
            "drift_identifiable": bool(ev.identifiable),
            "drift_year_counts": list(ev.n_years),
            "bic_shared": ev.bic_shared,
            "bic_separate": ev.bic_separate,
            "delta_bic": ev.delta_bic,
            "shared_drift_weight": float(ev.shared_weight),
        })
    out.sort(key=lambda f: (
        -f["recurrent_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


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

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "binding recurrent prelabel changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "binding recurrent result changed")

    parent = load_module(a.parent_runner, "reom_parent_runner_exact_shared_drift")
    binding_prelabel = json.loads(a.parent_prelabel_json.read_text())
    binding_parent_candidates = list(binding_prelabel["successor_candidates"])
    binding_parent_nodes = tuple(int(x) for x in binding_prelabel["successor_selected_nodes"])
    req(len(binding_parent_candidates) == 2097, "binding recurrent candidate count changed")

    qmod = parent.load_module(a.quality_source, "shared_drift_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-shared-drift-bic-v1-development-2022-2023-target-excluded"
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
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == 738682, f"pooled accessible event count changed: {len(events)}")
    req(sum(int(e["year"]) == 2022 for e in events) == 315024, "2022 accessible event count changed")
    req(sum(int(e["year"]) == 2023 for e in events) == 423658, "2023 accessible event count changed")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate pooled accessible event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent.geo_matrix(events)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
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
    ordinary = compute_stability(tree)
    recurrent, annual = recurrent_stability(tree, years)
    parent_labels = eom_labels(tree, recurrent)
    parent_nodes = selected_eom_nodes(tree, recurrent)
    parent_candidates = parent.candidates_from_labels(parent_labels, parent_nodes, events, ordinary, recurrent, True)

    # Normal HDBSCAN refit must exactly reconstruct the original recurrent-EOM
    # binding prelabel before the physical successor is allowed to proceed.
    req(parent_nodes == binding_parent_nodes, "fresh normal HDBSCAN fit changed recurrent selected-node set")
    req(len(parent_candidates) == 2097, f"fresh recurrent candidate count changed: {len(parent_candidates)}")
    req(signature(parent_candidates) == signature(binding_parent_candidates),
        "fresh recurrent candidate membership/order differs from binding prelabel")

    sol = np.asarray([float(e["sol"]) for e in events], dtype=np.float64)
    sun_lon = np.asarray([float(e["sun_lon"]) for e in events], dtype=np.float64)
    ecl_lat = np.asarray([float(e["ecl_lat"]) for e in events], dtype=np.float64)
    vg = np.asarray([float(e["vg"]) for e in events], dtype=np.float64)
    u, Y = physical_predictor_and_response(sol, sun_lon, ecl_lat, vg)
    stats = aggregate_tree_stats(tree, years, u, Y)

    # Independent aggregation identity on every binding selected node.
    binding_by_node = {int(row["node_id"]): row for row in binding_parent_candidates}
    for node in binding_parent_nodes:
        i = stats.index(node)
        counted = int(stats.n[i].sum())
        req(counted == int(binding_by_node[node]["member_count"]),
            f"bottom-up physical descendant count mismatch at recurrent node {node}: {counted}")

    shared_stability, evidence = shared_drift_stability(recurrent, stats)
    successor_labels = eom_labels(tree, shared_stability)
    successor_nodes = selected_eom_nodes(tree, shared_stability)
    successor_candidates = make_successor_candidates(
        successor_labels, successor_nodes, events, ordinary, recurrent, evidence, parent
    )
    mechanism_active = successor_nodes != parent_nodes

    identifiable = [ev for ev in evidence.values() if ev.identifiable]
    deltas = [float(ev.delta_bic) for ev in identifiable if ev.delta_bic is not None]
    weights = [float(ev.shared_weight) for ev in evidence.values()]
    evidence_summary = {
        "cluster_nodes": len(evidence),
        "identifiable_nodes": len(identifiable),
        "unidentifiable_nodes": len(evidence) - len(identifiable),
        "shared_weight_min": float(min(weights)),
        "shared_weight_median": float(np.median(weights)),
        "shared_weight_mean": float(np.mean(weights)),
        "shared_weight_max": float(max(weights)),
        "delta_bic_min_identifiable": float(min(deltas)) if deltas else None,
        "delta_bic_median_identifiable": float(np.median(deltas)) if deltas else None,
        "delta_bic_max_identifiable": float(max(deltas)) if deltas else None,
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECURRENT_EOM_SHARED_DRIFT_BIC_V1",
        "events_total": len(events),
        "events_by_year": {"2022": 315024, "2023": 423658},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "mechanism_active": bool(mechanism_active),
        "evidence_summary": evidence_summary,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual.items())},
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_SHARED_DRIFT_BIC_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Shower truth and the truth-bearing parent result are consumed only after
    # the complete successor catalogue/order has been persisted.
    binding_result = json.loads(a.parent_result_json.read_text())
    req(binding_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT",
        "wrong binding recurrent parent result")
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),
        "shower truth contains ID outside accessible pooled events")

    parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(parent_metrics == binding_result["successor_metrics"],
        "fresh recurrent parent metrics failed exact binding reproduction")

    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "mechanism_active": bool(mechanism_active),
        "strict_recovered_at_100_improvement_some_year": bool(strict_100),
        "evidence_summary": evidence_summary,
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
        "physical_model": {
            "response": ["radiant_unit_x", "radiant_unit_y", "radiant_unit_z", "log_vg"],
            "predictor": "((sol-55) mod 360)/10",
            "mean_model": "intercept+linear_solar_longitude",
            "bic_shared_parameter_count": 12,
            "bic_separate_parameter_count": 20,
            "shared_weight": "logistic((BIC_separate-BIC_shared)/2)",
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    def compact(m: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in m.items() if k != "first_rank_by_label"}

    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "evidence_summary": evidence_summary,
        "parent": {y: compact(m) for y, m in parent_metrics.items()},
        "successor": {y: compact(m) for y, m in successor_metrics.items()},
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
