#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_consensus_eom_hdbscan_v1.consensus_eom import consensus_selected_nodes, labels_from_selected_nodes
from orbittrace_recurrent_eom_hdbscan_v1 import run_development as parent
from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
PROTOCOL_BLOB = "6a2650585a8d92356581d75316f2c92a33b80471"
CONSENSUS_BLOB = "cef79d99bded4f93dfce6a930703b5493fd72fb6"
PARENT_METHOD_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
PARENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
IDENTITY_FREEZE_BLOB = "2df902ca266bc35df3fe5e5c73e0df5553b46bd7"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partition_sha(labels: np.ndarray) -> str:
    payload = [list(group) for group in parent.canonical_partition(labels)]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def consensus_candidates(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "consensus compact labels do not map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"consensus cluster below frozen support: node={node}")
        out.append({
            "family_id": parent.member_hash("CEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
            "recurrent_stability": float(recurrent[float(node)]),
        })
    out.sort(key=lambda f: (-f["recurrent_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
    return out


def recurrent_parent_candidates(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
) -> list[dict[str, Any]]:
    # Exact parent construction/ranking from recurrent-EOM v1.
    return parent.candidates_from_labels(labels, selected_nodes, events, ordinary, recurrent, True)


def main() -> int:
    p = argparse.ArgumentParser()
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
    qmod = parent.load_module(a.quality_source, "consensus_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-consensus-eom-hdbscan-v1-development-2022-2023-target-excluded"
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
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

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
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)

    # Engineering/provenance identity on the binding GMN hierarchy before truth use.
    vanilla_labels = eom_labels(tree, ordinary)
    req(parent.canonical_partition(model.labels_) == parent.canonical_partition(vanilla_labels), "vanilla custom extraction diverged on binding GMN hierarchy")

    recurrent, annual = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)
    recurrent_custom_labels = labels_from_selected_nodes(tree, recurrent_nodes)
    req(parent.canonical_partition(recurrent_custom_labels) == parent.canonical_partition(recurrent_labels), "consensus ancestor labeller diverged from recurrent parent on binding GMN hierarchy")
    req(partition_sha(recurrent_custom_labels) == partition_sha(recurrent_labels), "recurrent parent partition hash mismatch")

    consensus_nodes = consensus_selected_nodes(tree, annual)
    consensus_labels = labels_from_selected_nodes(tree, consensus_nodes)
    parent_candidates = recurrent_parent_candidates(recurrent_labels, recurrent_nodes, events, ordinary, recurrent)
    successor_candidates = consensus_candidates(consensus_labels, consensus_nodes, events, ordinary, recurrent)
    mechanism_active = consensus_nodes != recurrent_nodes

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_CONSENSUS_EOM_HDBSCAN_V1",
        "events_total": len(events),
        "events_by_year": {"2022": 315024, "2023": 423658},
        "source_pins": {
            "protocol_git_blob": PROTOCOL_BLOB,
            "consensus_selector_git_blob": CONSENSUS_BLOB,
            "recurrent_parent_method_git_blob": PARENT_METHOD_BLOB,
            "recurrent_parent_runner_git_blob": PARENT_RUNNER_BLOB,
            "identity_audit_freeze_git_blob": IDENTITY_FREEZE_BLOB,
        },
        "recurrent_parent_selected_nodes": list(recurrent_nodes),
        "consensus_selected_nodes": list(consensus_nodes),
        "mechanism_active": mechanism_active,
        "recurrent_parent_partition_sha256": partition_sha(recurrent_labels),
        "recurrent_parent_custom_labeller_partition_sha256": partition_sha(recurrent_custom_labels),
        "consensus_partition_sha256": partition_sha(consensus_labels),
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual.items())},
        "parent_ranking": ["recurrent_stability_desc", "ordinary_stability_desc", "member_count_desc", "family_id_asc"],
        "successor_ranking": ["recurrent_stability_desc", "ordinary_stability_desc", "member_count_desc", "family_id_asc"],
        "blind_exclusion": [20.0, 55.0],
        "truth_evaluated_when_written": False,
        "sonotaco_2013_2014_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "CONSENSUS_EOM_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    prelabel_sha = sha(prelabel_path)

    # Only now evaluate the already-sealed GMN shower truth using the exact parent evaluator.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(strict_100 and mechanism_active and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "parent_method": "RECURRENT_EOM_HDBSCAN_V1",
        "successor_method": "CONSENSUS_EOM_HDBSCAN_V1",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
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
            "prediction_data": False,
        },
        "sole_new_mechanism": "componentwise_consensus_EOM_parent_vs_children_decision",
        "ranking_changed_from_recurrent_parent": False,
        "post_result_parameter_search": False,
        "blind_exclusion": [20.0, 55.0],
        "sonotaco_2013_2014_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
        "annual_gates": annual_gates,
        "strict_recovered_at_100_improvement_some_year": strict_100,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
