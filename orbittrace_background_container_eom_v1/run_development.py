#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_clusters

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent
from recurrent_eom import eom_labels, selected_eom_nodes
from density_synchronous_eom import density_synchronous_stability

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
MIN_CLUSTER_SIZE = parent.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent.MIN_SAMPLES
MAX_CLUSTER_FRACTION = 0.01
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


def node_sizes(tree: np.ndarray) -> dict[int, int]:
    root = int(tree["parent"].min())
    cluster_tree = tree[tree["child_size"] > 1]
    sizes = {int(c): int(s) for c, s in zip(cluster_tree["child"], cluster_tree["child_size"])}
    # Root is not selectable when allow_single_cluster=False, but keep its size for complete audit.
    sizes[root] = int(root)
    return sizes


def descendants(children: dict[int, list[int]], root: int) -> list[int]:
    out: list[int] = []
    q = [root]
    while q:
        current = q.pop(0)
        out.append(current)
        q.extend(children.get(current, []))
    return out


def selected_eom_nodes_with_cap(
    tree: np.ndarray,
    stability: dict[float, float],
    max_cluster_size: int,
) -> tuple[int, ...]:
    """Pure-Python mirror of native zero-epsilon EOM with max_cluster_size."""
    work = {int(k): float(v) for k, v in stability.items()}
    node_list = sorted(work.keys(), reverse=True)[:-1]  # root excluded exactly as allow_single_cluster=False
    cluster_tree = tree[tree["child_size"] > 1]
    children: dict[int, list[int]] = defaultdict(list)
    sizes: dict[int, int] = {}
    for p, c, s in zip(cluster_tree["parent"], cluster_tree["child"], cluster_tree["child_size"]):
        children[int(p)].append(int(c))
        sizes[int(c)] = int(s)
    is_cluster = {node: True for node in node_list}
    for node in node_list:
        req(node in sizes, f"selectable node missing native cluster-size entry: {node}")
        subtree = sum(work[ch] for ch in children.get(node, []))
        if subtree > work[node] or sizes[node] > max_cluster_size:
            is_cluster[node] = False
            work[node] = subtree
        else:
            for sub in descendants(children, node):
                if sub != node:
                    is_cluster[sub] = False
    return tuple(sorted(node for node, keep in is_cluster.items() if keep))


def candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
    max_cluster_size: int,
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "native capped labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"capped EOM selected cluster below frozen minimum: node={node}")
        req(len(members) <= max_cluster_size, f"native capped EOM emitted oversized family: node={node} size={len(members)}")
        out.append({
            "family_id": parent.member_hash("BGCAP-EOM1", members),
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

    qmod = parent.load_module(a.quality_source, "background_container_eom_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-background-container-eom-v1-development-2022-2023-target-excluded"
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

    max_cluster_size = int(np.floor(MAX_CLUSTER_FRACTION * len(events)))
    req(max_cluster_size == 7386, f"binding 1pct cap changed: {max_cluster_size}")
    frozen_winner_sizes = [int(x["member_count"]) for x in winner_pre["successor_candidates"]]
    frozen_winner_oversized = [s for s in frozen_winner_sizes if s > max_cluster_size]
    req(len(frozen_winner_oversized) > 0, "frozen winner unexpectedly has no oversized background-container candidates")

    X = np.asarray(parent.geo_matrix(events), dtype=np.float64)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    req(X.shape == (len(events), 6), f"GEO6 shape changed: {X.shape}")
    req(np.all(np.isfinite(X)), "non-finite inherited GEO6")
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
    synchronous, _parent_annual, annual_reconstructed = density_synchronous_stability(tree, years)
    req(tree_sha(tree) == frozen_tree_sha, "density-sync kernel mutated the condensed tree")

    # Uncapped same-run selection is pretruth diagnostic only; it proves the cap changes EOM on this exact hierarchy.
    uncapped_labels = eom_labels(tree, synchronous)
    uncapped_nodes = selected_eom_nodes(tree, synchronous)
    req(len(uncapped_nodes) == len(set(int(x) for x in uncapped_labels if int(x) >= 0)), "uncapped selected-node/label mismatch")

    native_labels, _probs, _stab = get_clusters(
        tree,
        dict(synchronous),
        cluster_selection_method="eom",
        allow_single_cluster=False,
        match_reference_implementation=False,
        cluster_selection_epsilon=0.0,
        max_cluster_size=max_cluster_size,
    )
    native_labels = np.asarray(native_labels, dtype=np.int64)
    capped_nodes = selected_eom_nodes_with_cap(tree, synchronous, max_cluster_size)
    req(len(capped_nodes) == len(set(int(x) for x in native_labels if int(x) >= 0)), "capped selected-node/label count mismatch")
    candidates = candidates_from_labels(native_labels, capped_nodes, events, ordinary, synchronous, max_cluster_size)

    current_sizes = node_sizes(tree)
    uncapped_oversized_nodes = [int(n) for n in uncapped_nodes if int(current_sizes.get(int(n), 0)) > max_cluster_size]
    req(len(uncapped_oversized_nodes) > 0, "capped mechanism inactive on reconstructed hierarchy")
    req(all(n not in set(capped_nodes) for n in uncapped_oversized_nodes), "oversized uncapped node survived native max_cluster_size selection")

    candidate_count = len(candidates)
    sizes = [int(x["member_count"]) for x in candidates]
    smallest = min(sizes, default=0)
    largest = max(sizes, default=0)
    membership_sha = ordered_membership_sha(candidates)
    structural = {
        "native_python_capped_node_count_identity": len(capped_nodes) == len(set(int(x) for x in native_labels if int(x) >= 0)),
        "mechanism_active_uncapped_oversized_nodes": len(uncapped_oversized_nodes) > 0,
        "all_successor_families_at_most_cap": bool(candidates) and largest <= max_cluster_size,
        "at_least_100_candidates": candidate_count >= 100,
        "differs_from_binding_winner": membership_sha != WINNER_MEMBERSHIP_SHA,
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_BACKGROUND_CONTAINER_CAPPED_EOM_V1",
        "representation": "INHERITED_GEO6_UNCHANGED",
        "sole_change": "native_eom_max_cluster_size_floor_1pct_accessible_corpus",
        "max_cluster_fraction": MAX_CLUSTER_FRACTION,
        "max_cluster_size": max_cluster_size,
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "condensed_tree_sha256": frozen_tree_sha,
        "uncapped_selected_nodes_same_run": list(uncapped_nodes),
        "uncapped_oversized_nodes_same_run": uncapped_oversized_nodes,
        "capped_selected_nodes": list(capped_nodes),
        "frozen_winner_oversized_candidate_sizes": sorted(frozen_winner_oversized, reverse=True),
        "candidate_count": candidate_count,
        "smallest_family_members": smallest,
        "largest_family_members": largest,
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
    prelabel_path = a.output / "BACKGROUND_CONTAINER_CAPPED_EOM_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth remains sealed until exact capped hierarchy selection, memberships and order are durable.
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")
    successor = {str(y): parent.metrics(candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor[str(y)]) for y in YEARS}
    successor_total = sum(int(successor[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    passed = bool(all(structural.values()) and successor_total >= REQUIRED_TOTAL_AT100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_BACKGROUND_CONTAINER_CAPPED_EOM_V1_GMN_DEVELOPMENT" if passed else "FAIL_BACKGROUND_CONTAINER_CAPPED_EOM_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "sole_change": prelabel["sole_change"],
        "max_cluster_fraction": MAX_CLUSTER_FRACTION,
        "max_cluster_size": max_cluster_size,
        "candidate_count": candidate_count,
        "smallest_family_members": smallest,
        "largest_family_members": largest,
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
    (a.output / "BACKGROUND_CONTAINER_CAPPED_EOM_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "candidate_count": candidate_count,
        "largest_family_members": largest,
        "frozen_winner_oversized_candidate_sizes_top10": sorted(frozen_winner_oversized, reverse=True)[:10],
        "same_run_uncapped_oversized_node_count": len(uncapped_oversized_nodes),
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
