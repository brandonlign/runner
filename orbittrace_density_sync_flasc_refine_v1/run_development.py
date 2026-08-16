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
from hdbscan.branches import detect_branches_in_clusters

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND
MIN_CLUSTER_SIZE = parent_runner.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent_runner.MIN_SAMPLES
EXPECTED_BASELINE_COUNT = 2094
EXPECTED_BASELINE_ORDER_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_BASELINE = {
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


def unordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    rows = sorted("|".join(sorted(str(x) for x in row["event_ids"])) for row in candidates)
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def sync_candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "density-sync labels no longer compact/contiguous")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"winner family below frozen minimum: node={node}")
        out.append({
            "family_id": parent_runner.member_hash("DSEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def verify_baseline_artifact(winner_prelabel: dict[str, Any], winner_result: dict[str, Any]) -> list[dict[str, Any]]:
    req(int(winner_prelabel["successor_candidate_count"]) == EXPECTED_BASELINE_COUNT, "frozen winner candidate count changed")
    req(winner_prelabel["successor_ordered_membership_sha256"] == EXPECTED_BASELINE_ORDER_SHA, "frozen winner order hash changed")
    req(int(winner_result["successor_candidate_count"]) == EXPECTED_BASELINE_COUNT, "frozen winner result count changed")
    req(winner_result["successor_ordered_membership_sha256"] == EXPECTED_BASELINE_ORDER_SHA, "frozen winner result order hash changed")
    req(winner_result["verdict"] == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "frozen winner verdict changed")
    candidates = list(winner_prelabel["successor_candidates"])
    req(len(candidates) == EXPECTED_BASELINE_COUNT, "frozen winner candidate payload length changed")
    req(ordered_membership_sha(candidates) == EXPECTED_BASELINE_ORDER_SHA, "frozen winner candidate payload order changed")
    for year, expected in EXPECTED_BASELINE.items():
        got = winner_result["successor_metrics"][year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"frozen winner {year} {key} changed")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15), f"frozen winner {year} {key} changed")
    return candidates


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    winner_prelabel = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    frozen_winner_candidates = verify_baseline_artifact(winner_prelabel, winner_result)

    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "density_sync_flasc_v1_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-density-sync-flasc-refine-v1-development-2022-2023-target-excluded"
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
    req(len(events) == 738682, f"accessible event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")

    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")
    X = parent_runner.geo_matrix(events)

    # Same clustering fit, with branch-detection caches enabled only for the frozen post-processing step.
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
        branch_detection_data=True,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    frozen_tree_sha = tree_sha(tree)
    ordinary = compute_stability(tree)
    synchronous, _parent_annual, _annual_reconstructed = density_synchronous_stability(tree, years)
    req(tree_sha(tree) == frozen_tree_sha, "density-synchronous kernel mutated hierarchy")

    # Exact winner reconstruction is mandatory before FLASC can run.
    eom_labels = parent_reom.eom_labels(tree, synchronous)
    eom_nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    eom_candidates = sync_candidates_from_labels(eom_labels, eom_nodes, events, ordinary, synchronous)
    req(len(eom_candidates) == EXPECTED_BASELINE_COUNT, f"reconstructed EOM count {len(eom_candidates)} != frozen {EXPECTED_BASELINE_COUNT}")
    req(ordered_membership_sha(eom_candidates) == EXPECTED_BASELINE_ORDER_SHA, "branch-enabled fit does not reproduce exact frozen 179 winner")
    req(unordered_membership_sha(eom_candidates) == unordered_membership_sha(frozen_winner_candidates), "reconstructed EOM multiset differs from frozen winner")

    cluster_probabilities = np.where(eom_labels >= 0, 1.0, 0.0)
    (
        _flasc_labels,
        _flasc_probabilities,
        returned_cluster_labels,
        _returned_cluster_probabilities,
        branch_labels,
        _branch_probabilities,
        branch_persistences,
        _approximation_graphs,
        _branch_condensed_trees,
        _branch_linkage_trees,
        _centralities,
        _cluster_points,
    ) = detect_branches_in_clusters(
        model,
        cluster_labels=np.asarray(eom_labels, dtype=np.int64),
        cluster_probabilities=cluster_probabilities,
        branch_detection_method="core",
        label_sides_as_branches=False,
        min_cluster_size=MIN_CLUSTER_SIZE,
        max_cluster_size=0,
        allow_single_cluster=False,
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        cluster_selection_persistence=0.0,
    )
    returned_cluster_labels = np.asarray(returned_cluster_labels, dtype=np.int64)
    branch_labels = np.asarray(branch_labels, dtype=np.int64)
    req(np.array_equal(returned_cluster_labels, eom_labels), "FLASC changed overridden parent labels")
    req(len(branch_persistences) == EXPECTED_BASELINE_COUNT, "FLASC branch persistence tuple not aligned to winner labels")

    id_to_index = {str(e["id"]): i for i, e in enumerate(events)}
    successor_candidates: list[dict[str, Any]] = []
    refinement_manifest: list[dict[str, Any]] = []
    refined_parent_count = 0
    promoted_branch_count = 0
    fall_out_event_count = 0

    for parent_rank, parent in enumerate(eom_candidates, start=1):
        first_idx = id_to_index[str(parent["event_ids"][0])]
        parent_label = int(eom_labels[first_idx])
        req(parent_label >= 0, "winner candidate mapped to noise parent label")
        member_indices = np.asarray([id_to_index[str(eid)] for eid in parent["event_ids"]], dtype=np.int64)
        req(np.all(eom_labels[member_indices] == parent_label), "winner family spans multiple compact labels")
        pers = tuple(float(x) for x in branch_persistences[parent_label])

        if len(pers) <= 2:
            successor_candidates.append(dict(parent))
            refinement_manifest.append({
                "parent_rank": parent_rank,
                "parent_label": parent_label,
                "parent_family_id": parent["family_id"],
                "parent_member_count": int(parent["member_count"]),
                "selected_branch_count": len(pers),
                "refined": False,
                "branch_persistences": list(pers),
            })
            continue

        refined_parent_count += 1
        replacement: list[dict[str, Any]] = []
        parent_fall_out = int(np.sum(branch_labels[member_indices] < 0))
        fall_out_event_count += parent_fall_out
        for branch_id, persistence in enumerate(pers):
            idx = member_indices[branch_labels[member_indices] == branch_id]
            members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
            req(len(members) >= MIN_CLUSTER_SIZE, f"FLASC promoted branch below frozen minimum: parent={parent_label} branch={branch_id} size={len(members)}")
            replacement.append({
                "family_id": parent_runner.member_hash("DSFLASC1", members),
                "event_ids": list(members),
                "member_count": len(members),
                "source": "flasc_branch",
                "parent_family_id": parent["family_id"],
                "parent_rank": parent_rank,
                "parent_label": parent_label,
                "branch_id": branch_id,
                "branch_persistence": persistence,
                "parent_synchronous_stability": float(parent["synchronous_stability"]),
            })
        replacement.sort(key=lambda f: (-f["branch_persistence"], -f["member_count"], f["family_id"]))
        req(len(replacement) >= 3, "refined FLASC parent produced fewer than three promoted branches")
        promoted_branch_count += len(replacement)
        successor_candidates.extend(replacement)
        refinement_manifest.append({
            "parent_rank": parent_rank,
            "parent_label": parent_label,
            "parent_family_id": parent["family_id"],
            "parent_member_count": int(parent["member_count"]),
            "selected_branch_count": len(pers),
            "refined": True,
            "branch_persistences": list(pers),
            "promoted_branch_family_ids": [x["family_id"] for x in replacement],
            "promoted_branch_member_counts": [int(x["member_count"]) for x in replacement],
            "branch_fall_out_event_count": parent_fall_out,
        })

    successor_order_sha = ordered_membership_sha(successor_candidates)
    mechanism_active = bool(refined_parent_count > 0 and successor_order_sha != EXPECTED_BASELINE_ORDER_SHA)
    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_DENSITY_SYNC_FLASC_REFINE_V1",
        "sole_change": "selective_flasc_branch_substitution_inside_exact_density_sync_winner_families",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "baseline_candidate_count": len(eom_candidates),
        "baseline_ordered_membership_sha256": ordered_membership_sha(eom_candidates),
        "successor_candidate_count": len(successor_candidates),
        "successor_ordered_membership_sha256": successor_order_sha,
        "refined_parent_count": refined_parent_count,
        "promoted_branch_count": promoted_branch_count,
        "fall_out_event_count": fall_out_event_count,
        "mechanism_active": mechanism_active,
        "flasc_settings": {
            "branch_detection_method": "core",
            "label_sides_as_branches": False,
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "max_cluster_size": 0,
            "allow_single_cluster": False,
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "cluster_selection_persistence": 0.0,
        },
        "refinement_manifest": refinement_manifest,
        "successor_candidates": successor_candidates,
        "known_shower_labels_indexed": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "DENSITY_SYNC_FLASC_REFINE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth use begins only after the complete refined catalogue/order is frozen.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    baseline_metrics = winner_result["successor_metrics"]
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent_runner.annual_gate(baseline_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    baseline_total = sum(int(baseline_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(baseline_total == 179, f"baseline total changed: {baseline_total}")
    gain = successor_total - baseline_total
    structural_gates = {
        "exact_baseline_reproduced": ordered_membership_sha(eom_candidates) == EXPECTED_BASELINE_ORDER_SHA,
        "at_least_one_parent_refined": refined_parent_count > 0,
        "at_least_three_branches_promoted": promoted_branch_count >= 3,
        "mechanism_active": mechanism_active,
        "prelabel_written_before_truth_use": True,
    }
    passed = bool(
        successor_total >= 184
        and all(structural_gates.values())
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_DENSITY_SYNC_FLASC_REFINE_V1_GMN_DEVELOPMENT" if passed else "FAIL_DENSITY_SYNC_FLASC_REFINE_V1_GMN_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "sole_change": "selective_flasc_branch_substitution_inside_exact_density_sync_winner_families",
        "prelabel_sha256": prelabel_sha,
        "baseline_candidate_count": len(eom_candidates),
        "successor_candidate_count": len(successor_candidates),
        "refined_parent_count": refined_parent_count,
        "promoted_branch_count": promoted_branch_count,
        "fall_out_event_count": fall_out_event_count,
        "baseline_total_recovered_at_100": baseline_total,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": 184,
        "required_gain": 5,
        "baseline_metrics": baseline_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "structural_gates": structural_gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "DENSITY_SYNC_FLASC_REFINE_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "baseline_total_at100": baseline_total,
        "successor_total_at100": successor_total,
        "gain": gain,
        "baseline_candidate_count": len(eom_candidates),
        "successor_candidate_count": len(successor_candidates),
        "refined_parent_count": refined_parent_count,
        "promoted_branch_count": promoted_branch_count,
        "fall_out_event_count": fall_out_event_count,
        "2022": {k: v for k, v in successor_metrics["2022"].items() if k != "first_rank_by_label"},
        "2023": {k: v for k, v in successor_metrics["2023"].items() if k != "first_rank_by_label"},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
