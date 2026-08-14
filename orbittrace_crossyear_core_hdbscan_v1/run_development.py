#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import compute_stability, condense_tree

from boruvka_adapter import K_INHERITED, exact_crossyear_boruvka_mst


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "orbittrace_recurrent_eom_hdbscan_v1"
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes  # noqa: E402


YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
PARENT_RESULT_SHA256 = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
PARENT_RUNNER_GIT_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
RECURRENT_EOM_GIT_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
BORUVKA_EQUIVALENCE_RUN = 31846997065
BORUVKA_EQUIVALENCE_ARTIFACT = 9236242893
BORUVKA_EQUIVALENCE_DIGEST = "sha256:084483583f08452a455462dd655a4092895332f3d89561686d3556944e10aa19"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha256(a: np.ndarray) -> str:
    x = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(str(x.dtype).encode("utf-8"))
    h.update(b"\0")
    h.update(json.dumps(list(x.shape), separators=(",", ":")).encode("ascii"))
    h.update(b"\0")
    h.update(x.tobytes(order="C"))
    return h.hexdigest()


def load_parent_runner() -> Any:
    path = PARENT_DIR / "run_development.py"
    spec = importlib.util.spec_from_file_location("crossyear_core_frozen_parent_runner", path)
    req(spec is not None and spec.loader is not None, f"cannot import frozen parent runner {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def xy_candidates(
    parent: Any,
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float],
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(selected_nodes))), "cross-year-core compact labels do not map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"cross-year-core selected cluster below minimum: node={node}")
        out.append(
            {
                "family_id": parent.member_hash("XYCORE1", members),
                "node_id": int(node),
                "event_ids": list(members),
                "member_count": len(members),
                "ordinary_stability": float(ordinary[float(node)]),
                "recurrent_stability": float(recurrent[float(node)]),
            }
        )
    out.sort(
        key=lambda f: (
            -f["recurrent_stability"],
            -f["ordinary_stability"],
            -f["member_count"],
            f["family_id"],
        )
    )
    return out


def candidate_membership_signature(candidates: list[dict[str, Any]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted(tuple(str(x) for x in row["event_ids"]) for row in candidates))


def metric_core(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def load_exact_runtime_inputs(a: argparse.Namespace, parent: Any):
    req(sha256_file(a.parent_result_json) == PARENT_RESULT_SHA256, "binding recurrent-EOM parent result bytes changed")
    binding_parent = json.loads(a.parent_result_json.read_text())
    req(binding_parent["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "binding parent is not the promoted recurrent-EOM PASS")

    req(sha256_file(a.quality_source) == parent.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha256_file(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent.load_module(a.quality_source, "xycore_frozen_gmn_utility")
    qmod.v1.mult.YEARS = parent.YEARS
    qmod.v1.mult.MONTH_KEYS = parent.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = parent.YEARS
    support.MONTH_KEYS = parent.MONTH_KEYS
    support.CORPUS = "orbittrace-crossyear-core-hdbscan-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(parent.MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")
    return binding_parent, hidden_sealed, events


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent = load_parent_runner()
    binding_parent, hidden_sealed, events = load_exact_runtime_inputs(a, parent)

    X = parent.geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    event_ids = tuple(str(e["id"]) for e in events)
    input_id_sha = hashlib.sha256(("\n".join(event_ids) + "\n").encode()).hexdigest()
    geo6_sha = array_sha256(X)

    # Reproduce the promoted parent from the identical accessible event universe.
    parent_model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    parent_tree = np.asarray(parent_model.condensed_tree_._raw_tree)
    parent_ordinary = compute_stability(parent_tree)
    parent_recurrent, parent_annual = recurrent_stability(parent_tree, years)
    parent_labels = eom_labels(parent_tree, parent_recurrent)
    parent_nodes = selected_eom_nodes(parent_tree, parent_recurrent)
    req(len(parent_nodes) == len(set(int(x) for x in parent_labels if int(x) >= 0)), "parent selected-node/label count mismatch")
    parent_candidates = parent.candidates_from_labels(
        parent_labels,
        parent_nodes,
        events,
        parent_ordinary,
        parent_recurrent,
        True,
    )

    # Sole successor change: opposite-year core distances -> exact pooled Boruvka MST.
    neighbor_table, xy_mst = exact_crossyear_boruvka_mst(
        X,
        years,
        event_ids,
        k=K_INHERITED,
        leaf_size=40,
    )
    xy_ordered_mst = np.asarray(xy_mst, dtype=np.float64)[np.argsort(xy_mst[:, 2], kind="mergesort")]
    xy_single = np.asarray(label(xy_ordered_mst))
    xy_tree = np.asarray(condense_tree(xy_single, MIN_CLUSTER_SIZE))
    xy_ordinary = compute_stability(xy_tree)
    xy_recurrent, xy_annual = recurrent_stability(xy_tree, years)
    xy_labels = eom_labels(xy_tree, xy_recurrent)
    xy_nodes = selected_eom_nodes(xy_tree, xy_recurrent)
    req(len(xy_nodes) == len(set(int(x) for x in xy_labels if int(x) >= 0)), "cross-year-core selected-node/label count mismatch")
    xy_candidates_rows = xy_candidates(parent, xy_labels, xy_nodes, events, xy_ordinary, xy_recurrent)

    # Persist exact hierarchy evidence before scientific labels are consulted.
    np.save(a.output / "CROSSYEAR_CORE_DISTANCES.npy", neighbor_table.core_distances, allow_pickle=False)
    np.save(a.output / "CROSSYEAR_CORE_MST.npy", xy_mst, allow_pickle=False)
    np.save(a.output / "CROSSYEAR_CORE_SINGLE_LINKAGE.npy", xy_single, allow_pickle=False)
    np.save(a.output / "CROSSYEAR_CORE_CONDENSED_TREE.npy", xy_tree, allow_pickle=False)

    parent_single = np.asarray(parent_model.single_linkage_tree_._raw_tree)
    parent_membership_sig = candidate_membership_signature(parent_candidates)
    xy_membership_sig = candidate_membership_signature(xy_candidates_rows)
    hierarchy_changed = bool(
        array_sha256(parent_single) != array_sha256(xy_single)
        and array_sha256(parent_tree) != array_sha256(xy_tree)
    )
    memberships_changed = parent_membership_sig != xy_membership_sig
    mechanism_active = bool(hierarchy_changed and memberships_changed)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_CROSSYEAR_CORE_HDBSCAN_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "input_event_id_sha256": input_id_sha,
        "geo6_sha256": geo6_sha,
        "crossyear_core_distance_sha256": array_sha256(neighbor_table.core_distances),
        "crossyear_neighbor_index_sha256": array_sha256(neighbor_table.indices),
        "crossyear_mst_sha256": array_sha256(xy_mst),
        "crossyear_single_linkage_sha256": array_sha256(xy_single),
        "crossyear_condensed_tree_sha256": array_sha256(xy_tree),
        "parent_single_linkage_sha256": array_sha256(parent_single),
        "parent_condensed_tree_sha256": array_sha256(parent_tree),
        "parent_selected_nodes": list(parent_nodes),
        "crossyear_selected_nodes": list(xy_nodes),
        "parent_candidates": parent_candidates,
        "crossyear_candidates": xy_candidates_rows,
        "parent_annual_recurrent_stability": {str(k): list(v) for k, v in sorted(parent_annual.items())},
        "crossyear_annual_recurrent_stability": {str(k): list(v) for k, v in sorted(xy_annual.items())},
        "hierarchy_changed": hierarchy_changed,
        "memberships_changed": memberships_changed,
        "mechanism_active": mechanism_active,
        "boruvka_equivalence_run": BORUVKA_EQUIVALENCE_RUN,
        "boruvka_equivalence_artifact": BORUVKA_EQUIVALENCE_ARTIFACT,
        "boruvka_equivalence_digest": BORUVKA_EQUIVALENCE_DIGEST,
        "absolute_engineering_tolerance": 1.0e-12,
        "k_inherited": K_INHERITED,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "CROSSYEAR_CORE_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256_file(prelabel_path)

    # Truth remains logically sealed until the exact hierarchy, memberships and ranks above are persisted.
    hidden = hidden_sealed
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled IDs")

    parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    xy_metrics = {str(y): parent.metrics(xy_candidates_rows, hidden, ids_by_year[y]) for y in YEARS}

    # Exact promoted parent reproduction is mandatory before interpreting the successor.
    for y in YEARS:
        expected = metric_core(binding_parent["successor_metrics"][str(y)])
        observed = metric_core(parent_metrics[str(y)])
        req(observed == expected, f"promoted recurrent-EOM parent failed exact metric reproduction for {y}: {observed} != {expected}")
    req(len(parent_candidates) == int(binding_parent["successor_candidate_count"]), "promoted recurrent-EOM parent candidate count changed")

    annual_gates: dict[str, dict[str, bool]] = {}
    for y in YEARS:
        pm = parent_metrics[str(y)]
        sm = xy_metrics[str(y)]
        annual_gates[str(y)] = {
            "recovered_at_50_not_lower": int(sm["recovered_at_50"]) >= int(pm["recovered_at_50"]),
            "recovered_at_100_not_lower": int(sm["recovered_at_100"]) >= int(pm["recovered_at_100"]),
            "top100_precision_not_lower": float(sm["top100_dominant_precision"]) >= float(pm["top100_dominant_precision"]),
            "mrr_not_lower": float(sm["mrr"]) >= float(pm["mrr"]),
            "fragmentation_not_higher": float(sm["fragmentation_median_top500"]) <= float(pm["fragmentation_median_top500"]),
        }

    strict_100 = any(
        int(xy_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(
        strict_100
        and mechanism_active
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = (
        "PASS_CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(xy_candidates_rows),
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "parent_runner_git_blob": PARENT_RUNNER_GIT_BLOB,
        "recurrent_eom_git_blob": RECURRENT_EOM_GIT_BLOB,
        "hierarchy_changed": hierarchy_changed,
        "memberships_changed": memberships_changed,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": parent_metrics,
        "successor_metrics": xy_metrics,
        "annual_gates": annual_gates,
        "frozen_crossyear_core": {
            "representation": "GEO6",
            "opposite_year_k": K_INHERITED,
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples_inherited": MIN_SAMPLES,
            "metric": "euclidean",
            "mutual_reachability": "max(c_cross_i,c_cross_j,euclidean_distance)",
            "approx_min_span_tree": False,
            "boruvka_n_jobs": 1,
            "recurrent_eom_combiner": "min(normalized_annual_eom_2022,normalized_annual_eom_2023)",
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "mechanism_active": mechanism_active,
                "parent": {y: metric_core(parent_metrics[y]) for y in parent_metrics},
                "successor": {y: metric_core(xy_metrics[y]) for y in xy_metrics},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
