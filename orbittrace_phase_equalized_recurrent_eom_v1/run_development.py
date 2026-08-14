#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_phase_equalized_recurrent_eom_v1.phase_equalization import equalized_events

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_RESULT_SHA = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
PARENT_PRELABEL_SHA = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
SYNTHETIC_AUDIT_RESULT_SHA = "f4092490dc8cc1b00e028fb09887a59d42cb7e45ed91021bb5684d07eba2070f"
SYNTHETIC_AUDIT_RUN = 31851092633
SYNTHETIC_AUDIT_ARTIFACT = 9237533545
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


def req(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_f64_sha(array: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(array, dtype="<f8"))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def ordered_ids_sha(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()


def load_parent_helpers() -> Any:
    root = Path(__file__).resolve().parents[1]
    parent_dir = root / "orbittrace_recurrent_eom_hdbscan_v1"
    runner = parent_dir / "run_development.py"
    req(runner.exists(), "promoted recurrent-EOM runner missing")
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    spec = importlib.util.spec_from_file_location("phase_eq_parent_helpers", runner)
    req(spec is not None and spec.loader is not None, "cannot load promoted recurrent-EOM runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def metric_core(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "first_rank_by_label"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--synthetic-audit-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent = load_parent_helpers()
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent year/firewall pins drift")
    req(parent.MIN_CLUSTER_SIZE == MIN_CLUSTER_SIZE and parent.MIN_SAMPLES == MIN_SAMPLES, "parent HDBSCAN size pins drift")
    req(parent.QUALITY_SHA == QUALITY_SHA and parent.V8_RESULT_SHA == V8_RESULT_SHA, "parent input pins drift")

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.synthetic_audit_json) == SYNTHETIC_AUDIT_RESULT_SHA, "synthetic audit receipt changed")
    audit = json.loads(a.synthetic_audit_json.read_text())
    req(audit["verdict"] == "PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_SYNTHETIC_AUDIT", "synthetic audit did not pass")
    req(all(audit["checks"].values()), "synthetic audit contains failed invariant")
    req(audit["gmn_accessed"] is False and audit["truth_accessed"] is False, "synthetic audit crossed GMN/truth boundary")

    qmod = parent.load_module(a.quality_source, "phase_eq_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-phase-equalized-recurrent-eom-v1-development-2022-2023-target-excluded"
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
        req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in rows), f"protected region survived parser in {year}")
        events.extend(rows)
    req(len({e["id"] for e in events}) == len(events), "duplicate pooled event IDs")

    ids = [str(e["id"]) for e in events]
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}

    raw_geo6 = parent.geo_matrix(events)
    eq_events, phase = equalized_events(events)
    eq_geo6 = parent.geo_matrix(eq_events)
    req(np.array_equal(raw_geo6[:, 2:], eq_geo6[:, 2:]), "phase equalization altered non-phase GEO6 coordinates")
    phase_nonidentity = bool(not np.array_equal(phase.raw_sol, phase.equalized_sol))
    req(phase_nonidentity, "phase equalization unexpectedly identity on GMN input")
    req(not np.any((phase.equalized_sol >= BLIND[0]) & (phase.equalized_sol <= BLIND[1])), "equalized phase entered protected interval")

    # Build the complete successor hierarchy/candidates before opening promoted-parent
    # output artifacts or indexing any sealed known-shower truth.
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(eq_geo6)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    ordinary_labels = parent.eom_labels(tree, ordinary)
    req(parent.canonical_partition(model.labels_) == parent.canonical_partition(ordinary_labels), "equalized hierarchy custom ordinary EOM diverged from vanilla HDBSCAN")

    recurrent, annual_stability = parent.recurrent_stability(tree, years)
    successor_labels = parent.eom_labels(tree, recurrent)
    successor_nodes = parent.selected_eom_nodes(tree, recurrent)
    req(len(successor_nodes) == len(set(int(x) for x in successor_labels if int(x) >= 0)), "equalized selected-node/label count mismatch")
    successor_candidates = parent.candidates_from_labels(successor_labels, successor_nodes, eq_events, ordinary, recurrent, True)

    tree_path = a.output / "PHASE_EQUALIZED_CONDENSED_TREE.npy"
    np.save(tree_path, tree, allow_pickle=False)
    geo_path = a.output / "PHASE_EQUALIZED_GEO6.npy"
    np.save(geo_path, eq_geo6, allow_pickle=False)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_PHASE_EQUALIZED_RECURRENT_EOM_V1",
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "ordered_event_ids_sha256": ordered_ids_sha(ids),
        "raw_sol_raw_f64_sha256": raw_f64_sha(phase.raw_sol),
        "unwrapped_s_raw_f64_sha256": raw_f64_sha(phase.unwrapped_s),
        "equalized_sol_raw_f64_sha256": raw_f64_sha(phase.equalized_sol),
        "raw_geo6_nonphase_raw_f64_sha256": raw_f64_sha(raw_geo6[:, 2:]),
        "equalized_geo6_raw_f64_sha256": raw_f64_sha(eq_geo6),
        "equalized_geo6_npy_sha256": sha(geo_path),
        "condensed_tree_npy_sha256": sha(tree_path),
        "phase_transform_nonidentity": phase_nonidentity,
        "nonphase_geo6_exactly_preserved": True,
        "successor_selected_nodes": list(successor_nodes),
        "successor_candidates": successor_candidates,
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual_stability.items())},
        "transform": {
            "name": "pooled_empirical_phase_intensity_equalization",
            "blind_low": 20.0,
            "blind_high": 55.0,
            "arc_origin_deg": 55.0,
            "arc_length_deg": 325.0,
            "mid_distribution": "(count_below + count_at_or_below)/(2N)",
            "pooled_years": [2022, 2023],
            "uses_only_raw_accessible_solar_longitude": True,
            "year_specific_warp": False,
            "smoothing": False,
        },
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "asfn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "PHASE_EQUALIZED_RECURRENT_EOM_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after the complete successor prelabel freeze may promoted-parent output
    # and sealed shower truth enter evaluation.
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA, "promoted recurrent-EOM parent result changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA, "promoted recurrent-EOM parent prelabel changed")
    parent_result = json.loads(a.parent_result_json.read_text())
    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(parent_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "promoted recurrent-EOM parent no longer PASS")
    req(parent_result["events_by_year"] == {str(y): len(ids_by_year[y]) for y in YEARS}, "current GMN event counts differ from promoted parent")
    parent_candidates = list(parent_prelabel["successor_candidates"])

    hidden = hidden_sealed
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")
    reproduced_parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(reproduced_parent_metrics == parent_result["successor_metrics"], "promoted recurrent-EOM metrics failed exact reproduction")
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(reproduced_parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(reproduced_parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    parent_membership_order = [tuple(str(x) for x in c["event_ids"]) for c in parent_candidates]
    successor_membership_order = [tuple(str(x) for x in c["event_ids"]) for c in successor_candidates]
    mechanism_active = successor_membership_order != parent_membership_order
    passed = bool(
        strict_100
        and mechanism_active
        and phase_nonidentity
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT" if passed else "FAIL_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parent_result_sha256": PARENT_RESULT_SHA,
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA,
        "parent_metrics_exactly_reproduced": True,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "mechanism_active": mechanism_active,
        "phase_transform_nonidentity": phase_nonidentity,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": reproduced_parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "frozen_hdbscan": {
            "representation": "GEO6_PHASE_EQ",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "transform": prelabel["transform"],
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "asfn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "parent": {y: metric_core(reproduced_parent_metrics[y]) for y in reproduced_parent_metrics},
        "successor": {y: metric_core(successor_metrics[y]) for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
