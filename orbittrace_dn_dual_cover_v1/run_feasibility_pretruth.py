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

import recurrent_eom as reom
from density_synchronous_eom import density_synchronous_stability
from dn_dual_cover import dual_cover, fold_selected_cover_clusters

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
EXPECTED_EVENTS = {2022: 315024, 2023: 423658}
EXPECTED_TOTAL = 738682
EXPECTED_COVER_ROWS = 1477364
PARENT_PRELABEL_SHA256 = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
PARENT_RESULT_SHA256 = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def membership_order_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in c["event_ids"]) for c in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def membership_set_sha(candidates: list[dict[str, Any]]) -> str:
    rows = sorted("|".join(str(x) for x in c["event_ids"]) for c in candidates)
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def validate_parent_pretruth(parent: dict[str, Any], accessible: set[str]) -> list[dict[str, Any]]:
    req(parent.get("scientific_role") == "PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1", "wrong parent prelabel role")
    req(parent.get("blind_exclusion") == [20.0, 55.0], "parent blind interval changed")
    req(int(parent.get("successor_candidate_count", -1)) == 2094, "parent candidate count changed")
    rows = parent.get("successor_candidates")
    req(isinstance(rows, list) and len(rows) == 2094, "parent candidate payload changed")
    out: list[dict[str, Any]] = []
    for raw in rows:
        ids = [str(x) for x in raw["event_ids"]]
        req(ids == sorted(ids), "parent membership not sorted")
        req(len(ids) == len(set(ids)), "parent membership repeats ID")
        req(all(eid in accessible for eid in ids), "parent membership contains inaccessible ID")
        out.append({"event_ids": ids})
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

    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "exact parent prelabel hash changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "exact parent result hash changed")
    parent_result = json.loads(a.parent_result_json.read_text())
    req(parent_result.get("verdict") == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "wrong frozen parent verdict")
    req(int(parent_result.get("successor_candidate_count", -1)) == 2094, "wrong frozen parent result candidate count")
    req(int(parent_result["successor_metrics"]["2022"]["recovered_at_100"]) == 89, "frozen parent 2022 @100 changed")
    req(int(parent_result["successor_metrics"]["2023"]["recovered_at_100"]) == 90, "frozen parent 2023 @100 changed")

    parent_runner = load_module(a.parent_runner, "dn_frozen_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(parent_runner.MIN_CLUSTER_SIZE == MIN_CLUSTER_SIZE, "parent min_cluster_size changed")
    req(parent_runner.MIN_SAMPLES == MIN_SAMPLES, "parent min_samples changed")
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN utility changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")

    qmod = parent_runner.load_module(a.quality_source, "dn_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = parent_runner.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = parent_runner.MONTH_KEYS
    support.CORPUS = "orbittrace-dn-dual-cover-v1-feasibility-pretruth-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    # The frozen parser transports hidden associations as a sealed object. This
    # feasibility runner never inspects, iterates, hashes, serializes, or
    # evaluates that object; delete the local reference immediately.
    del hidden_sealed
    req(sorted(scan) == list(YEARS), f"GMN parser accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(parent_runner.MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} count")
        events.extend(rows)
    ids = [str(e["id"]) for e in events]
    req(len(ids) == EXPECTED_TOTAL and len(set(ids)) == EXPECTED_TOTAL, "accessible physical event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    for year, expected in EXPECTED_EVENTS.items():
        req(int(np.sum(years == year)) == expected, f"accessible {year} count changed")

    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    parent_candidates = validate_parent_pretruth(parent_prelabel, set(ids))
    parent_order_sha = membership_order_sha(parent_candidates)
    parent_set_sha = membership_set_sha(parent_candidates)

    cover, coords = dual_cover(
        [float(e["sol"]) for e in events],
        [float(e["lon"]) for e in events],
        [float(e["lat"]) for e in events],
        [float(e["vg"]) for e in events],
    )
    req(cover.shape == (EXPECTED_COVER_ROWS, 6), f"cover shape changed: {cover.shape}")
    cover_years = np.concatenate((years, years))
    req(cover_years.shape == (EXPECTED_COVER_ROWS,), "cover year vector shape changed")
    req(np.array_equal(cover_years[:EXPECTED_TOTAL], years), "plus-sheet years changed")
    req(np.array_equal(cover_years[EXPECTED_TOTAL:], years), "minus-sheet years changed")
    req(np.all(np.isfinite(cover)), "non-finite D_N dual-cover coordinate")
    req(float(np.min(coords["u"])) > 0.0, "nonpositive normalized D_N speed")

    print(json.dumps({
        "stage": "DN_DUAL_COVER_BUILT",
        "physical_events": EXPECTED_TOTAL,
        "cover_rows": EXPECTED_COVER_ROWS,
        "u_min": float(np.min(coords["u"])),
        "u_max": float(np.max(coords["u"])),
    }, sort_keys=True), flush=True)

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(cover)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    synchronous, _annual, _parent_reconstructed = density_synchronous_stability(tree, cover_years)
    labels = reom.eom_labels(tree, synchronous)
    nodes = reom.selected_eom_nodes(tree, synchronous)
    req(len(nodes) == len(set(int(x) for x in labels if int(x) >= 0)), "selected-node/compact-label count mismatch")

    candidates, fold_audit = fold_selected_cover_clusters(labels, nodes, ids, ordinary, synchronous)
    req(len(candidates) > 0, "D_N dual cover emitted zero valid physical candidates")
    req(fold_audit["physical_candidate_count"] == len(candidates), "fold audit candidate count mismatch")
    req(all(int(c["member_count"]) >= MIN_CLUSTER_SIZE for c in candidates), "emitted candidate below minimum")
    req(all(len(c["event_ids"]) == len(set(c["event_ids"])) for c in candidates), "emitted candidate repeats physical ID")
    req(len({tuple(c["event_ids"]) for c in candidates}) == len(candidates), "mirror duplicate survived folding")
    req(all(eid in set(ids) for c in candidates for eid in c["event_ids"]), "emitted candidate contains inaccessible physical ID")

    successor_order_sha = membership_order_sha(candidates)
    successor_set_sha = membership_set_sha(candidates)
    mechanism_active = bool(successor_order_sha != parent_order_sha or successor_set_sha != parent_set_sha)
    req(mechanism_active, "D_N candidate construction is identical to frozen parent")

    parent_top100 = {tuple(c["event_ids"]) for c in parent_candidates[:100]}
    successor_top100 = {tuple(c["event_ids"]) for c in candidates[:100]}
    top100_overlap = len(parent_top100 & successor_top100)
    parent_universe = {tuple(c["event_ids"]) for c in parent_candidates}
    successor_universe = {tuple(c["event_ids"]) for c in candidates}

    pretruth = {
        "verdict": "PASS_DN_DUAL_COVER_V1_PRETRUTH_FEASIBILITY",
        "scientific_role": "PRETRUTH_GEOMETRY_AND_CANDIDATE_CONSTRUCTION_ONLY",
        "physical_event_count": EXPECTED_TOTAL,
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "cover_row_count": EXPECTED_COVER_ROWS,
        "cover_dimension": 6,
        "cover_sheet_order": "PLUS_ALL_THEN_MINUS_ALL",
        "hdbscan": {
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean_on_exact_DN_dual_cover",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "selected_cover_node_count": len(nodes),
        "fold_audit": fold_audit,
        "parent_candidate_count": len(parent_candidates),
        "physical_candidate_count": len(candidates),
        "parent_ordered_membership_sha256": parent_order_sha,
        "successor_ordered_membership_sha256": successor_order_sha,
        "parent_membership_set_sha256": parent_set_sha,
        "successor_membership_set_sha256": successor_set_sha,
        "mechanism_active": mechanism_active,
        "top100_exact_membership_overlap_with_parent": top100_overlap,
        "full_exact_membership_overlap_with_parent": len(parent_universe & successor_universe),
        "candidates": candidates,
        "hidden_truth_evaluated": False,
        "hidden_truth_iterated": False,
        "hidden_truth_serialized": False,
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
    path = a.output / "DN_DUAL_COVER_V1_PRETRUTH_FEASIBILITY.json"
    path.write_text(json.dumps(pretruth, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": pretruth["verdict"],
        "selected_cover_nodes": len(nodes),
        "physical_candidates": len(candidates),
        "fold_audit": fold_audit,
        "top100_parent_overlap": top100_overlap,
        "full_parent_overlap": pretruth["full_exact_membership_overlap_with_parent"],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
