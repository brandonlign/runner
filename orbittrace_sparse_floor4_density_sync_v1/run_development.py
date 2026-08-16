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

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent
from recurrent_eom import eom_labels, selected_eom_nodes
from density_synchronous_eom import density_synchronous_stability

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
SUCCESSOR_MIN_CLUSTER_SIZE = 4
MIN_SAMPLES = 10
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WINNER_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
BASELINE_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


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


def candidates_from_sync(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= SUCCESSOR_MIN_CLUSTER_SIZE, f"selected cluster below frozen floor: node={node} size={len(members)}")
        out.append({
            "family_id": parent.member_hash("FLOOR4-DSEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (
        -float(f["synchronous_stability"]),
        -float(f["ordinary_stability"]),
        -int(f["member_count"]),
        str(f["family_id"]),
    ))
    return out


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

    req(sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support result changed")
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "binding winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "binding winner result changed")
    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner membership hash changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner result membership hash changed")
    baseline = winner_result["successor_metrics"]
    req(sum(int(baseline[str(y)]["recovered_at_100"]) for y in YEARS) == BASELINE_TOTAL_AT100, "binding baseline total changed")
    req(int(baseline["2022"]["recovered_at_100"]) == 89, "binding 2022 @100 changed")
    req(int(baseline["2023"]["recovered_at_100"]) == 90, "binding 2023 @100 changed")

    qmod = parent.load_module(a.quality_source, "sparse_floor4_dseom_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-sparse-floor4-density-sync-v1-development-2022-2023-target-excluded"
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
    req(len(events) == 738682, f"accessible pooled event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    X = np.asarray(parent.geo_matrix(events), dtype=np.float64)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    req(X.shape == (len(events), 6), f"GEO6 shape changed: {X.shape}")
    req(np.all(np.isfinite(X)), "non-finite inherited GEO6")
    req(int(np.sum(years == 2022)) == 315024, "accessible 2022 event count changed")
    req(int(np.sum(years == 2023)) == 423658, "accessible 2023 event count changed")

    model = hdbscan.HDBSCAN(
        min_cluster_size=SUCCESSOR_MIN_CLUSTER_SIZE,
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
    synchronous, _parent_annual, annual_reconstructed = density_synchronous_stability(tree, years)
    req(tree_sha(tree) == frozen_tree_sha, "density-sync kernel mutated floor-4 condensed tree")
    labels = eom_labels(tree, synchronous)
    nodes = selected_eom_nodes(tree, synchronous)
    req(len(nodes) == len(set(int(x) for x in labels if int(x) >= 0)), "selected-node/label count mismatch")
    candidates = candidates_from_sync(labels, nodes, events, ordinary, synchronous)

    candidate_count = len(candidates)
    sizes = [int(x["member_count"]) for x in candidates]
    smallest = min(sizes, default=0)
    largest = max(sizes, default=0)
    sparse_count = sum(4 <= s <= 9 for s in sizes)
    large_count = sum(s >= 10 for s in sizes)
    membership_sha = ordered_membership_sha(candidates)
    structural = {
        "at_least_100_candidates": candidate_count >= 100,
        "all_selected_at_least_4_members": bool(candidates) and smallest >= 4,
        "mechanism_active_has_4_to_9_member_family": sparse_count >= 1,
        "largest_family_at_most_1pct_all_events": largest <= int(np.floor(0.01 * len(events))),
        "differs_from_binding_winner": membership_sha != WINNER_MEMBERSHIP_SHA,
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_SPARSE_FLOOR4_DENSITY_SYNC_V1",
        "representation": "INHERITED_GEO6_UNCHANGED",
        "sole_change": "hdbscan_min_cluster_size_10_to_4",
        "hdbscan": {
            "min_cluster_size": SUCCESSOR_MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "prediction_data": False,
        },
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "selected_density_synchronous_nodes": list(nodes),
        "candidate_count": candidate_count,
        "smallest_family_members": smallest,
        "largest_family_members": largest,
        "families_size_4_to_9": sparse_count,
        "families_size_ge_10": large_count,
        "ordered_membership_sha256": membership_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "structural_gates": structural,
        "candidates": candidates,
        "annual_reconstructed_eom": {str(k): list(v) for k, v in sorted(annual_reconstructed.items())},
        "known_shower_labels_indexed": False,
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
    prelabel_path = a.output / "SPARSE_FLOOR4_DENSITY_SYNC_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")
    successor = {str(y): parent.metrics(candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor[str(y)]) for y in YEARS}
    successor_total = sum(int(successor[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    passed = bool(all(structural.values()) and successor_total >= REQUIRED_TOTAL_AT100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_SPARSE_FLOOR4_DENSITY_SYNC_V1_GMN_DEVELOPMENT" if passed else "FAIL_SPARSE_FLOOR4_DENSITY_SYNC_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "sole_change": prelabel["sole_change"],
        "hdbscan": prelabel["hdbscan"],
        "candidate_count": candidate_count,
        "smallest_family_members": smallest,
        "largest_family_members": largest,
        "families_size_4_to_9": sparse_count,
        "families_size_ge_10": large_count,
        "ordered_membership_sha256": membership_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "structural_gates": structural,
        "baseline_metrics": baseline,
        "successor_metrics": successor,
        "annual_gates": annual_gates,
        "baseline_total_recovered_at_100": BASELINE_TOTAL_AT100,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": REQUIRED_TOTAL_AT100,
        "required_gain": REQUIRED_TOTAL_AT100 - BASELINE_TOTAL_AT100,
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
    (a.output / "SPARSE_FLOOR4_DENSITY_SYNC_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "candidate_count": candidate_count,
        "families_size_4_to_9": sparse_count,
        "smallest_family_members": smallest,
        "largest_family_members": largest,
        "baseline_total_at100": BASELINE_TOTAL_AT100,
        "successor_total_at100": successor_total,
        "gain": gain,
        "2022": {k: successor["2022"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
        "2023": {k: successor["2023"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
        "structural_gates": structural,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
