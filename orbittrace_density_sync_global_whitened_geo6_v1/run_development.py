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

import recurrent_eom as parent_reom
import run_development as parent_runner
from density_synchronous_eom import density_synchronous_stability
from whitening import fit_transform

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
PARENT_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
PARENT_TOTAL_100 = 179
REQUIRED_GAIN = 2


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sync_candidates(labels, nodes, events, ordinary, synchronous):
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(nodes))), "compact labels no longer contiguous")
    out = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, "selected cluster below minimum")
        out.append({
            "family_id": parent_runner.member_hash("WGDSEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (-f["synchronous_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
    return out


def membership_universe(rows):
    return {tuple(sorted(str(x) for x in row["event_ids"])) for row in rows}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA, "#1263 binding result changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA, "#1263 binding prelabel changed")

    qmod = parent_runner.load_module(a.quality_source, "whitened_geo6_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-density-sync-global-whitened-geo6-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), "wrong GMN years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN sources changed")

    events = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), "normalization changed event count")
        events.extend(rows)
    req(len(events) == 738682, "pooled event count changed")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived")

    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    req(int(np.sum(years == 2022)) == 315024, "2022 count changed")
    req(int(np.sum(years == 2023)) == 423658, "2023 count changed")
    x = parent_runner.geo_matrix(events)
    z, fit, cov_err = fit_transform(x)
    nonidentity = bool(not np.allclose(fit.matrix, np.eye(6), rtol=0.0, atol=1e-12))
    req(nonidentity, "whitening unexpectedly identity")

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(z)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    synchronous, _parent_annual, _annual_reconstructed = density_synchronous_stability(tree, years)
    labels = parent_reom.eom_labels(tree, synchronous)
    nodes = parent_reom.selected_eom_nodes(tree, synchronous)
    candidates = sync_candidates(labels, nodes, events, ordinary, synchronous)

    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    parent_candidates = list(parent_prelabel["successor_candidates"])
    mechanism_active = bool(membership_universe(candidates) != membership_universe(parent_candidates) or len(candidates) != len(parent_candidates))

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_DENSITY_SYNC_GLOBAL_WHITENED_GEO6_V1",
        "events_total": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "mean": fit.mean.tolist(),
        "covariance": fit.covariance.tolist(),
        "eigenvalues": fit.eigenvalues.tolist(),
        "whitening_matrix": fit.matrix.tolist(),
        "whitened_covariance_max_abs_identity_error": cov_err,
        "whitening_nonidentity": nonidentity,
        "condensed_tree_sha256": tree_sha(tree),
        "selected_nodes": list(nodes),
        "candidate_count": len(candidates),
        "mechanism_active_vs_1263": mechanism_active,
        "successor_candidates": candidates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prepath = a.output / "DENSITY_SYNC_GLOBAL_WHITENED_GEO6_V1_PRELABEL.json"
    prepath.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    pre_sha = sha(prepath)

    # Only after the complete transform/hierarchy/membership/order is persisted do we use truth-derived comparator metrics.
    parent_result = json.loads(a.parent_result_json.read_text())
    parent_metrics = parent_result["successor_metrics"]
    hidden = hidden_sealed
    ids = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    successor_metrics = {str(y): parent_runner.metrics(candidates, hidden, ids[y]) for y in YEARS}
    gates = {str(y): parent_runner.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    parent_total = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total == PARENT_TOTAL_100, "#1263 total @100 changed")
    gain = successor_total - parent_total
    strong = gain >= REQUIRED_GAIN
    passed = bool(nonidentity and cov_err <= 1e-10 and mechanism_active and strong and all(all(g.values()) for g in gates.values()))
    verdict = "PASS_DENSITY_SYNC_GLOBAL_WHITENED_GEO6_V1_GMN_DEVELOPMENT" if passed else "FAIL_DENSITY_SYNC_GLOBAL_WHITENED_GEO6_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": pre_sha,
        "candidate_count": len(candidates),
        "mechanism_active": mechanism_active,
        "whitening_nonidentity": nonidentity,
        "whitened_covariance_max_abs_identity_error": cov_err,
        "parent_total_recovered_at_100": parent_total,
        "successor_total_recovered_at_100": successor_total,
        "total_recovered_at_100_gain": gain,
        "required_total_recovered_at_100_gain": REQUIRED_GAIN,
        "strong_recovery_gate": strong,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "DENSITY_SYNC_GLOBAL_WHITENED_GEO6_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    def compact(m): return {k:v for k,v in m.items() if k != "first_rank_by_label"}
    print(json.dumps({"verdict": verdict, "gain": gain, "candidate_count": len(candidates), "covariance_error": cov_err, "parent": {y: compact(m) for y,m in parent_metrics.items()}, "successor": {y: compact(m) for y,m in successor_metrics.items()}, "annual_gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
