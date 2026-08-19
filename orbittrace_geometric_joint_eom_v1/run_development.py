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

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability
from geometric_joint_eom import geometric_joint_stability

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND
MIN_CLUSTER_SIZE = parent_runner.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent_runner.MIN_SAMPLES

EXPECTED_RECURRENT_COUNT = 2097
EXPECTED_CHAMPION_COUNT = 2094
EXPECTED_CHAMPION = {
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


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def candidates_from_nodes(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
    primary: dict[float, float],
    prefix: str,
    primary_name: str,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        row = {
            "family_id": parent_runner.member_hash(prefix, members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            primary_name: float(primary[float(node)]),
            "recurrent_stability": float(recurrent[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        }
        out.append(row)
    out.sort(key=lambda f: (
        -float(f[primary_name]),
        -float(f["recurrent_stability"]),
        -float(f["ordinary_stability"]),
        -int(f["member_count"]),
        str(f["family_id"]),
    ))
    return out


def verify_champion(metrics: dict[str, dict[str, Any]]) -> None:
    for year, expected in EXPECTED_CHAMPION.items():
        got = metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"density-sync champion {year} {key} changed: {got[key]} != {expected[key]}")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15), f"density-sync champion {year} {key} changed: {got[key]} != {expected[key]}")


def annual_gate(champion: dict[str, Any], successor: dict[str, Any]) -> dict[str, bool]:
    return {
        "recovered_at_50_nonregression": int(successor["recovered_at_50"]) >= int(champion["recovered_at_50"]),
        "recovered_at_100_nonregression": int(successor["recovered_at_100"]) >= int(champion["recovered_at_100"]),
        "top100_precision_nonregression": float(successor["top100_dominant_precision"]) >= float(champion["top100_dominant_precision"]),
        "mrr_nonregression": float(successor["mrr"]) >= float(champion["mrr"]),
        "fragmentation_nonregression": float(successor["fragmentation_median_top500"]) <= float(champion["fragmentation_median_top500"]),
    }


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

    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "gjeom_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-geometric-joint-eom-v1-development-2022-2023-target-excluded"
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
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

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
    ordinary = {float(k): float(v) for k, v in compute_stability(tree).items()}

    # Reconstruct the exact current recurrent parent.
    recurrent, annual = parent_reom.recurrent_stability(tree, years)
    recurrent = {float(k): float(v) for k, v in recurrent.items()}
    recurrent_labels = parent_reom.eom_labels(tree, recurrent)
    recurrent_nodes = parent_reom.selected_eom_nodes(tree, recurrent)
    recurrent_candidates = parent_runner.candidates_from_labels(recurrent_labels, recurrent_nodes, events, ordinary, recurrent, True)
    req(len(recurrent_candidates) == EXPECTED_RECURRENT_COUNT, f"recurrent parent candidate count changed: {len(recurrent_candidates)}")

    # Reconstruct the exact density-synchronous GMN champion before successor truth scoring.
    sync, sync_parent_annual, _reconstructed = density_synchronous_stability(tree, years)
    req(sync_parent_annual == annual, "density-sync champion parent annual EOM changed")
    sync = {float(k): float(v) for k, v in sync.items()}
    sync_labels = parent_reom.eom_labels(tree, sync)
    sync_nodes = parent_reom.selected_eom_nodes(tree, sync)
    sync_candidates = candidates_from_nodes(sync_labels, sync_nodes, events, ordinary, recurrent, sync, "DSEOM1", "synchronous_stability")
    req(len(sync_candidates) == EXPECTED_CHAMPION_COUNT, f"density-sync champion candidate count changed: {len(sync_candidates)}")

    # Sole new scientific operation.
    joint, ordinary2, recurrent2, annual2 = geometric_joint_stability(tree, years)
    req(ordinary2 == ordinary, "geometric kernel ordinary stability changed")
    req(recurrent2 == recurrent, "geometric kernel recurrent stability changed")
    req(annual2 == annual, "geometric kernel annual EOM changed")
    req(tree_sha(tree) == frozen_tree_sha, "geometric kernel mutated hierarchy")
    joint_labels = parent_reom.eom_labels(tree, joint)
    joint_nodes = parent_reom.selected_eom_nodes(tree, joint)
    joint_candidates = candidates_from_nodes(joint_labels, joint_nodes, events, ordinary, recurrent, joint, "GJEOM1", "geometric_joint_stability")

    recurrent_sha = ordered_membership_sha(recurrent_candidates)
    champion_sha = ordered_membership_sha(sync_candidates)
    successor_sha = ordered_membership_sha(joint_candidates)
    mechanism_active = bool(tuple(joint_nodes) != tuple(sync_nodes) or successor_sha != champion_sha)

    # Freeze complete method output before sealed known-shower truth is read.
    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_GEOMETRIC_JOINT_EOM_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "recurrent_candidate_count": len(recurrent_candidates),
        "density_sync_champion_candidate_count": len(sync_candidates),
        "successor_candidate_count": len(joint_candidates),
        "recurrent_ordered_membership_sha256": recurrent_sha,
        "density_sync_champion_ordered_membership_sha256": champion_sha,
        "successor_ordered_membership_sha256": successor_sha,
        "density_sync_champion_selected_nodes": list(sync_nodes),
        "successor_selected_nodes": list(joint_nodes),
        "mechanism_active": mechanism_active,
        "successor_candidates": joint_candidates,
        "geometric_joint_stability": {str(int(k)): float(v) for k, v in sorted(joint.items())},
        "ordinary_stability": {str(int(k)): float(v) for k, v in sorted(ordinary.items())},
        "recurrent_stability": {str(int(k)): float(v) for k, v in sorted(recurrent.items())},
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GEOMETRIC_JOINT_EOM_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible IDs")

    champion_metrics = {str(y): parent_runner.metrics(sync_candidates, hidden, ids_by_year[y]) for y in YEARS}
    verify_champion(champion_metrics)
    successor_metrics = {str(y): parent_runner.metrics(joint_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): annual_gate(champion_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(int(successor_metrics[str(y)]["recovered_at_100"]) > int(champion_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_GEOMETRIC_JOINT_EOM_V1_GMN_DEVELOPMENT" if passed else "FAIL_GEOMETRIC_JOINT_EOM_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "density_sync_champion_candidate_count": len(sync_candidates),
        "successor_candidate_count": len(joint_candidates),
        "density_sync_champion_ordered_membership_sha256": champion_sha,
        "successor_ordered_membership_sha256": successor_sha,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "champion_metrics": champion_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "sole_successor_objective": "sqrt(ordinary_eom_stability * recurrent_eom_stability)",
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "GEOMETRIC_JOINT_EOM_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "champion_candidate_count": len(sync_candidates),
        "successor_candidate_count": len(joint_candidates),
        "champion": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in champion_metrics.items()},
        "successor": {y: {k: v for k, v in m.items() if k != "first_rank_by_label"} for y, m in successor_metrics.items()},
        "annual_gates": annual_gates,
        "strict_100": strict_100,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
