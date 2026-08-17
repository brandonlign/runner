#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
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
from phase_neutral_geometry import phase_neutral_geo_matrix

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


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


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                req(isinstance(obj, dict), f"non-object row in {path}")
                rows.append(obj)
    return rows


def read_json_gz(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def load_label_free_snapshot(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, set[str]]]:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    req(manifest["schema"] == "ORBITTRACE_PHASE_NEUTRAL_GMN_LABEL_FREE_SNAPSHOT_V1", "wrong snapshot schema")
    req(manifest["scientific_role"] == "METHOD_INDEPENDENT_TARGET_EXCLUDED_GMN_2022_2023_SNAPSHOT", "wrong snapshot role")
    req(manifest["years"] == list(YEARS), "snapshot years changed")
    req(manifest["blind_exclusion"] == list(BLIND), "snapshot blind interval changed")
    req(manifest["event_order_preserved"] is True, "snapshot order not preserved")
    req(manifest["labels_present"] is False, "label-free snapshot contains labels")
    req(manifest["hdbscan_fit_executed"] is False and manifest["method_evaluation_executed"] is False, "snapshot already method-bearing")
    for key in ("target_information_access","target_region_events_accessed","sonotaco_access","asfn_access","efn_access","amos_access","maarsy_scientific_access","dms_scientific_access"):
        req(manifest[key] is False, f"snapshot firewall changed: {key}")

    events: list[dict[str, Any]] = []
    annual_ids: dict[int, set[str]] = {}
    all_ids: set[str] = set()
    for year in YEARS:
        path = root / manifest["row_files"][str(year)]
        req(sha(path) == manifest["row_sha256"][str(year)], f"snapshot row hash changed {year}")
        raw_rows = read_jsonl_gz(path)
        req(len(raw_rows) == int(manifest["events_by_year"][str(year)]), f"snapshot row count changed {year}")
        rows = [parent_runner.normalize_event(row, year) for row in raw_rows]
        ids = {str(r["id"]) for r in rows}
        req(len(ids) == len(rows), f"duplicate IDs within {year}")
        req(not (all_ids & ids), f"duplicate IDs across years {year}")
        all_ids |= ids
        annual_ids[year] = ids
        events.extend(rows)
    req(len(events) == int(manifest["events_total"]), "snapshot total count changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event reached paired runner")
    return events, manifest, annual_ids


def sync_candidates(
    prefix: str,
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
) -> list[dict[str, Any]]:
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), "compact labels no longer align with selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below minimum node={node}")
        out.append({
            "family_id": parent_runner.member_hash(prefix, members),
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


def fit_density_sync(events: list[dict[str, Any]], years: np.ndarray, X: np.ndarray, prefix: str, representation: str) -> dict[str, Any]:
    req(X.shape[0] == len(events), f"{representation} row count mismatch")
    req(np.isfinite(X).all(), f"{representation} contains nonfinite coordinates")
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
    ordinary_labels = parent_reom.eom_labels(tree, ordinary)
    req(parent_runner.canonical_partition(model.labels_) == parent_runner.canonical_partition(ordinary_labels), f"{representation} vanilla extraction mismatch")
    synchronous, parent_annual, reconstructed = density_synchronous_stability(tree, years)
    labels = parent_reom.eom_labels(tree, synchronous)
    nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    candidates = sync_candidates(prefix, labels, nodes, events, ordinary, synchronous)
    return {
        "representation": representation,
        "tree_sha256": tree_sha(tree),
        "selected_nodes": list(nodes),
        "candidate_count": len(candidates),
        "ordered_membership_sha256": ordered_membership_sha(candidates),
        "candidates": candidates,
        "annual_eom_sha256": hashlib.sha256(json.dumps({str(k):list(v) for k,v in sorted(parent_annual.items())},sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "reconstructed_annual_eom_sha256": hashlib.sha256(json.dumps({str(k):list(v) for k,v in sorted(reconstructed.items())},sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "synchronous_stability_sha256": hashlib.sha256(json.dumps({str(int(k)):float(v) for k,v in sorted(synchronous.items())},sort_keys=True,separators=(",",":")).encode()).hexdigest(),
    }


def run_pretruth(label_free_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    events, manifest, _annual_ids = load_label_free_snapshot(label_free_root)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    req(set(np.unique(years).tolist()) == set(YEARS), "year vector changed")

    X6 = parent_runner.geo_matrix(events)
    X4 = phase_neutral_geo_matrix(events)
    req(X6.shape == (len(events), 6), "GEO6 shape changed")
    req(X4.shape == (len(events), 4), "GEO4 shape changed")

    champion = fit_density_sync(events, years, X6, "DSEOM6", "GEO6")
    successor = fit_density_sync(events, years, X4, "DSEOM4", "GEO4_PHASE_NEUTRAL")
    mechanism_active = bool(
        champion["tree_sha256"] != successor["tree_sha256"]
        or champion["selected_nodes"] != successor["selected_nodes"]
        or champion["ordered_membership_sha256"] != successor["ordered_membership_sha256"]
    )

    result = {
        "schema": "ORBITTRACE_PHASE_NEUTRAL_DENSITY_SYNC_PRETRUTH_V1",
        "scientific_role": "PRETRUTH_PAIRED_CURRENT_GMN_DEVELOPMENT_SNAPSHOT",
        "snapshot_manifest_sha256": sha(label_free_root / "manifest.json"),
        "snapshot_events_by_year": manifest["events_by_year"],
        "snapshot_events_total": manifest["events_total"],
        "champion": champion,
        "successor": successor,
        "mechanism_active": mechanism_active,
        "frozen_hdbscan": {
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "node_objective": "integral_min_normalized_annual_alive_mass_over_lambda",
        "sole_scientific_change": "remove_cos_solar_longitude_and_sin_solar_longitude_from_clustering_representation",
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "PHASE_NEUTRAL_DENSITY_SYNC_PRETRUTH_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "pretruth_sha256": sha(path),
        "events_by_year": manifest["events_by_year"],
        "champion_candidate_count": champion["candidate_count"],
        "successor_candidate_count": successor["candidate_count"],
        "mechanism_active": mechanism_active,
        "champion_tree": champion["tree_sha256"],
        "successor_tree": successor["tree_sha256"],
    }, indent=2, sort_keys=True))
    return 0


def load_truth(truth_root: Path, accessible_ids: set[str]) -> tuple[dict[str, str], dict[str, Any]]:
    manifest_path = truth_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    req(manifest["schema"] == "ORBITTRACE_PHASE_NEUTRAL_GMN_SEALED_TRUTH_V1", "wrong sealed-truth schema")
    req(manifest["scientific_role"] == "SEALED_TRUTH_FOR_PAIRED_WITHIN_SNAPSHOT_DEVELOPMENT_ONLY", "wrong sealed-truth role")
    req(manifest["blind_exclusion"] == list(BLIND), "sealed-truth blind interval changed")
    req(manifest["method_evaluation_executed"] is False, "truth artifact already method-bearing")
    path = truth_root / manifest["truth_file"]
    req(sha(path) == manifest["truth_sha256"], "sealed truth hash changed")
    rows = read_json_gz(path)
    req(isinstance(rows, list) and len(rows) == int(manifest["truth_entries"]), "truth row count changed")
    hidden = {str(eid):str(label) for eid,label in rows}
    req(len(hidden) == len(rows), "duplicate truth IDs")
    req(all(eid in accessible_ids for eid in hidden), "truth contains inaccessible event")
    return hidden, manifest


def run_evaluate(pretruth_path: Path, label_free_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    pre = json.loads(pretruth_path.read_text())
    req(pre["schema"] == "ORBITTRACE_PHASE_NEUTRAL_DENSITY_SYNC_PRETRUTH_V1", "wrong pretruth schema")
    req(pre["truth_accessed"] is False, "pretruth already truth-bearing")
    events, manifest, annual_ids = load_label_free_snapshot(label_free_root)
    req(sha(label_free_root / "manifest.json") == pre["snapshot_manifest_sha256"], "snapshot manifest changed after pretruth")
    accessible_ids = set().union(*annual_ids.values())
    hidden, truth_manifest = load_truth(truth_root, accessible_ids)

    champion_candidates = pre["champion"]["candidates"]
    successor_candidates = pre["successor"]["candidates"]
    champion_metrics = {str(y): parent_runner.metrics(champion_candidates, hidden, annual_ids[y]) for y in YEARS}
    successor_metrics = {str(y): parent_runner.metrics(successor_candidates, hidden, annual_ids[y]) for y in YEARS}
    annual_gates = {str(y): parent_runner.annual_gate(champion_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(champion_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    mechanism_active = bool(pre["mechanism_active"])
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_PHASE_NEUTRAL_DENSITY_SYNC_V1_GMN_DEVELOPMENT" if passed else "FAIL_PHASE_NEUTRAL_DENSITY_SYNC_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "PAIRED_CURRENT_GMN_2022_2023_EXPOSED_DEVELOPMENT_SNAPSHOT_ONLY",
        "pretruth_sha256": sha(pretruth_path),
        "snapshot_manifest_sha256": pre["snapshot_manifest_sha256"],
        "truth_manifest_sha256": sha(truth_root / "manifest.json"),
        "events_by_year": manifest["events_by_year"],
        "events_total": manifest["events_total"],
        "champion_representation": "GEO6",
        "successor_representation": "GEO4_PHASE_NEUTRAL",
        "champion_candidate_count": pre["champion"]["candidate_count"],
        "successor_candidate_count": pre["successor"]["candidate_count"],
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "champion_metrics": champion_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "primary_gate": "all inherited annual no-regression gates plus strict recovered@100 improvement in at least one year",
        "post_result_parameter_search": False,
        "historical_1263_metrics_used_as_gate": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "PHASE_NEUTRAL_DENSITY_SYNC_GMN_DEVELOPMENT_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events_by_year": manifest["events_by_year"],
        "mechanism_active": mechanism_active,
        "strict_100": strict_100,
        "champion": {y:{k:v for k,v in m.items() if k!="first_rank_by_label"} for y,m in champion_metrics.items()},
        "successor": {y:{k:v for k,v in m.items() if k!="first_rank_by_label"} for y,m in successor_metrics.items()},
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pretruth")
    p.add_argument("--label-free-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    e = sub.add_parser("evaluate")
    e.add_argument("--pretruth", type=Path, required=True)
    e.add_argument("--label-free-root", type=Path, required=True)
    e.add_argument("--truth-root", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.command == "pretruth":
        return run_pretruth(a.label_free_root, a.output)
    return run_evaluate(a.pretruth, a.label_free_root, a.truth_root, a.output)


if __name__ == "__main__":
    raise SystemExit(main())
