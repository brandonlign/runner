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

from local_bic import INTRINSIC_DIMENSION, local_bic_stability
from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_PRELABEL_SHA256 = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
PARENT_RESULT_SHA256 = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
PARENT_MIN_CLUSTER_SIZE = 10
PARENT_MIN_SAMPLES = 10
SUCCESSOR_MIN_CLUSTER_SIZE = 8
SUCCESSOR_MIN_SAMPLES = 4


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


def membership_signature(rows: list[dict[str, Any]]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(str(x) for x in row["event_ids"]) for row in rows)


def membership_universe(rows: list[dict[str, Any]]) -> frozenset[tuple[str, ...]]:
    return frozenset(tuple(str(x) for x in row["event_ids"]) for row in rows)


def make_successor_candidates(
    labels: np.ndarray,
    nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    evidence: dict[int, Any],
    parent: Any,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(nodes))), "compact local-BIC labels do not map to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= SUCCESSOR_MIN_CLUSTER_SIZE,
            f"selected local-BIC cluster below frozen pooled minimum: node={node} size={len(members)}")
        req(int(node) in evidence, f"selected local-BIC node lacks evidence: {node}")
        ev = evidence[int(node)]
        out.append({
            "family_id": parent.member_hash("RLBIC1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
            "birth_lambda": float(ev.birth_lambda),
            "year_counts": list(ev.year_counts),
            "annual_log_persistence": list(ev.annual_log_persistence),
            "common_log_persistence": float(ev.common_log_persistence),
            "log_likelihood_ratio": float(ev.log_likelihood_ratio),
            "bic_quality": float(ev.bic_quality),
        })
    out.sort(key=lambda f: (
        -f["bic_quality"],
        -f["common_log_persistence"],
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

    parent = load_module(a.parent_runner, "reom_parent_runner_exact_local_bic")
    binding_prelabel = json.loads(a.parent_prelabel_json.read_text())
    binding_candidates = list(binding_prelabel["successor_candidates"])
    binding_nodes = tuple(int(x) for x in binding_prelabel["successor_selected_nodes"])
    req(len(binding_candidates) == 2097, "binding recurrent candidate count changed")

    qmod = parent.load_module(a.quality_source, "local_bic_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-local-bic-hdbscan-v1-development-2022-2023-target-excluded"
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
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent.geo_matrix(events)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)

    # First reproduce the exact binding promoted parent on its original hierarchy.
    parent_model = hdbscan.HDBSCAN(
        min_cluster_size=PARENT_MIN_CLUSTER_SIZE,
        min_samples=PARENT_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    parent_tree = parent_model.condensed_tree_._raw_tree
    parent_ordinary = compute_stability(parent_tree)
    parent_recurrent, _parent_annual = recurrent_stability(parent_tree, years)
    parent_labels = eom_labels(parent_tree, parent_recurrent)
    parent_nodes = selected_eom_nodes(parent_tree, parent_recurrent)
    parent_candidates = parent.candidates_from_labels(
        parent_labels, parent_nodes, events, parent_ordinary, parent_recurrent, True
    )
    req(parent_nodes == binding_nodes, "fresh parent fit changed recurrent selected-node set")
    req(len(parent_candidates) == 2097, f"fresh recurrent candidate count changed: {len(parent_candidates)}")
    req(membership_signature(parent_candidates) == membership_signature(binding_candidates),
        "fresh recurrent membership/order differs from binding prelabel")

    # New low-support hierarchy and frozen scale-invariant local-BIC extraction.
    successor_model = hdbscan.HDBSCAN(
        min_cluster_size=SUCCESSOR_MIN_CLUSTER_SIZE,
        min_samples=SUCCESSOR_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = successor_model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    local_quality, evidence = local_bic_stability(tree, years, INTRINSIC_DIMENSION)
    successor_labels = eom_labels(tree, local_quality)
    successor_nodes = selected_eom_nodes(tree, local_quality)
    successor_candidates = make_successor_candidates(
        successor_labels, successor_nodes, events, ordinary, evidence, parent
    )

    parent_universe = membership_universe(parent_candidates)
    successor_universe = membership_universe(successor_candidates)
    mechanism_active = successor_universe != parent_universe

    q_values = np.asarray([float(ev.bic_quality) for ev in evidence.values()], dtype=float)
    common_values = np.asarray([float(ev.common_log_persistence) for ev in evidence.values()], dtype=float)
    year_supported = sum(int(ev.year_counts[0] > 0 and ev.year_counts[1] > 0) for ev in evidence.values())
    evidence_summary = {
        "cluster_nodes": len(evidence),
        "two_year_supported_nodes": int(year_supported),
        "positive_bic_nodes": int(np.sum(q_values > 0.0)),
        "bic_quality_min": float(np.min(q_values)) if len(q_values) else 0.0,
        "bic_quality_median": float(np.median(q_values)) if len(q_values) else 0.0,
        "bic_quality_mean": float(np.mean(q_values)) if len(q_values) else 0.0,
        "bic_quality_max": float(np.max(q_values)) if len(q_values) else 0.0,
        "common_log_persistence_median": float(np.median(common_values)) if len(common_values) else 0.0,
    }

    evidence_payload = {
        str(node): {
            "birth_lambda": float(ev.birth_lambda),
            "year_counts": list(ev.year_counts),
            "annual_log_persistence": list(ev.annual_log_persistence),
            "common_log_persistence": float(ev.common_log_persistence),
            "log_likelihood_ratio": float(ev.log_likelihood_ratio),
            "bic_quality": float(ev.bic_quality),
        }
        for node, ev in sorted(evidence.items())
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECURRENT_LOCAL_BIC_HDBSCAN_V1",
        "events_total": len(events),
        "events_by_year": {"2022": 315024, "2023": 423658},
        "representation": "GEO6_INTRINSIC_D4",
        "intrinsic_dimension": INTRINSIC_DIMENSION,
        "successor_hdbscan": {
            "min_cluster_size": SUCCESSOR_MIN_CLUSTER_SIZE,
            "min_samples": SUCCESSOR_MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "condensed_tree_sha256": hashlib.sha256(tree.tobytes()).hexdigest(),
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "membership_universe_identical": parent_universe == successor_universe,
        "mechanism_active": bool(mechanism_active),
        "evidence_summary": evidence_summary,
        "node_evidence": evidence_payload,
        "successor_candidates": successor_candidates,
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_LOCAL_BIC_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Hidden truth is first semantically consumed only after complete successor
    # hierarchy, quality, memberships and order have been persisted above.
    binding_result = json.loads(a.parent_result_json.read_text())
    req(binding_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "wrong binding recurrent result")
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),
        "shower truth contains inaccessible ID")
    parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(parent_metrics == binding_result["successor_metrics"], "fresh recurrent parent metrics failed exact reproduction")

    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_RECURRENT_LOCAL_BIC_HDBSCAN_V1_GMN_DEVELOPMENT"
        if passed else "FAIL_RECURRENT_LOCAL_BIC_HDBSCAN_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "intrinsic_dimension": INTRINSIC_DIMENSION,
        "successor_min_cluster_size": SUCCESSOR_MIN_CLUSTER_SIZE,
        "successor_min_samples": SUCCESSOR_MIN_SAMPLES,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "membership_universe_identical": parent_universe == successor_universe,
        "mechanism_active": bool(mechanism_active),
        "strict_recovered_at_100_improvement_some_year": bool(strict_100),
        "evidence_summary": evidence_summary,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "RECURRENT_LOCAL_BIC_HDBSCAN_V1_GMN_DEVELOPMENT.json"
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
