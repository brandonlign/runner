#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from mst_year_mixing import cluster_mixing_stats, mixed_score
from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
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


def family_order_signature(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [tuple(str(x) for x in row["event_ids"]) for row in rows]


def make_successor_candidates(
    labels: np.ndarray,
    nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
    mixing: dict[int, Any],
    parent: Any,
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(nodes))), "compact recurrent labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        stat = mixing[lab]
        req(stat.member_count == len(members), f"mixing/member count mismatch for label {lab}")
        rec = float(recurrent[float(node)])
        mix = float(stat.mixing_enrichment)
        score = mixed_score(rec, mix)
        out.append({
            "family_id": parent.member_hash("REOMMST1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
            "recurrent_stability": rec,
            "mst_internal_edges": int(stat.internal_edges),
            "mst_cross_year_edges": int(stat.cross_year_edges),
            "mst_expected_cross_year_edges": float(stat.expected_cross_year_edges),
            "mst_mixing_enrichment": mix,
            "mixed_score": score,
            "year_counts": list(stat.year_counts),
        })
    out.sort(key=lambda f: (
        -f["mixed_score"],
        -f["recurrent_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def exact_parent_metrics_match(current: dict[str, Any], binding: dict[str, Any]) -> bool:
    return current == binding


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
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "binding recurrent prelabel artifact changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "binding recurrent result artifact changed")

    # Git blob identity is enforced independently in the workflow. Loading this
    # exact parent runner supplies only frozen parsing/evaluation helpers.
    parent = load_module(a.parent_runner, "reom_parent_runner_exact")

    qmod = parent.load_module(a.quality_source, "mst_mix_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-mst-year-mixing-v1-development-2022-2023-target-excluded"
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
    req(sum(e["year"] == 2022 for e in events) == 315024, "2022 accessible event count changed")
    req(sum(e["year"] == 2023 for e in events) == 423658, "2023 accessible event count changed")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = parent.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
        gen_min_span_tree=True,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    recurrent, annual_stability = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)
    req(len(recurrent_nodes) == len(set(int(x) for x in recurrent_labels if int(x) >= 0)), "recurrent node/label count mismatch")

    parent_candidates = parent.candidates_from_labels(
        recurrent_labels, recurrent_nodes, events, ordinary, recurrent, True
    )
    req(len(parent_candidates) == 2097, f"recurrent parent candidate count changed: {len(parent_candidates)}")

    # Binding pretruth identity check occurs before any shower truth is opened.
    binding_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(tuple(int(x) for x in binding_prelabel["successor_selected_nodes"]) == recurrent_nodes,
        "gen_min_span_tree=True changed recurrent selected-node identity")
    binding_parent_candidates = list(binding_prelabel["successor_candidates"])
    req(family_order_signature(binding_parent_candidates) == family_order_signature(parent_candidates),
        "gen_min_span_tree=True changed recurrent complete candidate membership/order")

    mst = np.asarray(model.minimum_spanning_tree_.to_numpy())
    req(mst.ndim == 2 and mst.shape[1] >= 3, f"unexpected HDBSCAN MST shape: {mst.shape}")
    req(mst.shape[0] == len(events) - 1, f"pooled HDBSCAN MST edge count changed: {mst.shape[0]}")
    mixing = cluster_mixing_stats(recurrent_labels, years, mst)
    req(sorted(mixing) == list(range(len(recurrent_nodes))), "mixing stats missing recurrent labels")

    successor_candidates = make_successor_candidates(
        recurrent_labels, recurrent_nodes, events, ordinary, recurrent, mixing, parent
    )
    parent_membership_set = {tuple(row["event_ids"]) for row in parent_candidates}
    successor_membership_set = {tuple(row["event_ids"]) for row in successor_candidates}
    req(successor_membership_set == parent_membership_set, "rank-only successor changed recurrent membership universe")
    parent_order_members = family_order_signature(parent_candidates)
    successor_order_members = family_order_signature(successor_candidates)
    mechanism_active = successor_order_members != parent_order_members

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECURRENT_EOM_MST_YEAR_MIXING_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "recurrent_selected_nodes": list(recurrent_nodes),
        "candidate_count": len(parent_candidates),
        "membership_universe_identical": True,
        "mechanism_active": mechanism_active,
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual_stability.items())},
        "mst_edge_count": int(mst.shape[0]),
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_MST_YEAR_MIXING_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after the complete successor order is persisted do we use the sealed
    # GMN shower truth and the binding parent's truth-bearing result artifact.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}

    binding_result = json.loads(a.parent_result_json.read_text())
    req(binding_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "wrong binding recurrent parent result")
    req(exact_parent_metrics_match(parent_metrics, binding_result["successor_metrics"]),
        "current recurrent parent metrics do not exactly reproduce binding result")

    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_RECURRENT_EOM_MST_YEAR_MIXING_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_RECURRENT_EOM_MST_YEAR_MIXING_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "candidate_count": len(parent_candidates),
        "membership_universe_identical": True,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "mixing_summary": {
            "min": float(min(row["mst_mixing_enrichment"] for row in successor_candidates)),
            "median": float(np.median([row["mst_mixing_enrichment"] for row in successor_candidates])),
            "max": float(max(row["mst_mixing_enrichment"] for row in successor_candidates)),
            "zero_internal_edge_candidates": int(sum(row["mst_internal_edges"] == 0 for row in successor_candidates)),
            "zero_annual_support_candidates": int(sum(0 in row["year_counts"] for row in successor_candidates)),
        },
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "gen_min_span_tree": True,
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_MST_YEAR_MIXING_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "mixing_summary": result["mixing_summary"],
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
