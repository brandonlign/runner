#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BUCKETS = (0, 1, 2, 3)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "base-generator", "intrinsic-runner", "structural-runner", "parent-runner", "quality-source",
        "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts",
        "v8-result-json", "structural-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    base = load_module(a.base_generator, "bdcp_base_generator")
    req = base.req
    intrinsic = load_module(a.intrinsic_runner, "bdcp_intrinsic_repair1")
    structural_runner = load_module(a.structural_runner, "bdcp_structural_repair1")
    parent = load_module(a.parent_runner, "bdcp_parent_repair1")

    req(intrinsic.sha256(a.quality_source) == QUALITY_SHA256, "GMN utility hash")
    req(intrinsic.sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 result hash")
    req(intrinsic.sha256(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "#1284 structural result hash")
    req(tuple(intrinsic.YEARS) == YEARS and tuple(intrinsic.BLIND) == BLIND, "intrinsic constants")
    req(float(intrinsic.RADIUS) == float(base.RADIUS) and int(intrinsic.MIN_SUPPORT) == int(base.MIN_SUPPORT), "#1284 radius/support changed")
    req(tuple(structural_runner.YEARS) == YEARS and tuple(structural_runner.BLIND) == BLIND, "structural comparator constants")
    req(int(structural_runner.COARSE_D) == 128 and int(structural_runner.FINE_D) == 1024 and tuple(structural_runner.BUCKETS) == BUCKETS, "structural sparse panels changed")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support")

    structural = json.loads(a.structural_result_json.read_text())
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "#1284 panel set")

    q = load_module(a.quality_source, "bdcp_gmn_repair1")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support_module = runtime.load_support_module(a.support_source_parts)
    support_module.YEARS = YEARS
    support_module.MONTH_KEYS = MONTH_KEYS
    support_module.CORPUS = "orbittrace-bivariate-density-component-persistence-v1-target-excluded-repair1"
    support_module.RANKING_VARIANTS = ("persistence",)
    req((float(support_module.BLIND_LOW), float(support_module.BLIND_HIGH)) == BLIND, "firewall")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base_source, _scorer = support_module.load_sources(a)
    scan, _cal, hidden_unused, sources = support_module.parse_catalogue(base_source)
    del hidden_unused
    req(sorted(scan) == list(YEARS), "wrong years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == 738682, f"pooled count changed {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived")

    Xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([intrinsic.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)
    subset_specs = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            ii = intrinsic.selected_indices(hashes, denominator, bucket)
            subset_specs.append((denominator, bucket, ii, [events[int(i)] for i in ii], np.asarray(Xfull[ii], dtype=float), np.asarray(years_full[ii], dtype=np.int64), [ids_full[int(i)] for i in ii]))
    smallest_key = min((len(s[-1]), s[0], s[1]) for s in subset_specs)[1:]

    subsets = []
    shortage = False
    for denominator, bucket, ii, sub_events, X, years, ids in subset_specs:
        print(f"[bdcp-prelabel-repair1] d={denominator} b={bucket} n={len(ids)}", flush=True)
        successor, successor_summary = base.build_candidates(intrinsic, sub_events, (denominator, bucket) == smallest_key)

        ranked_parent, ranked_summary = intrinsic.recurrent_ranked(parent, X, years, ids)
        structural_parent, structural_summary = structural_runner.recurrent_candidates(parent, X, years, ids)
        ex = expected[(denominator, bucket)]

        req(int(ex["events_total"]) == len(ids), "#1284 event count mismatch")
        req({str(k): int(v) for k, v in ex["events_by_year"].items()} == {str(y): int(np.sum(years == y)) for y in YEARS}, "annual count mismatch")

        # Immutable #1284 parent control is checked using the exact implementation that created it.
        req(structural_summary["candidate_rows"] == ex["recurrent_eom"]["candidate_rows"], f"#1284 structural parent membership mismatch d={denominator} b={bucket}")
        req(int(structural_summary["candidate_count"]) == int(ex["recurrent_eom"]["candidate_count"]), "#1284 structural parent count mismatch")

        # The ranked helper used by prior sparse truth experiments must be exactly the same membership set.
        structural_keys = {tuple(sorted(map(str, members))) for members in structural_parent}
        ranked_keys = {tuple(map(str, row["event_ids"])) for row in ranked_parent}
        req(len(structural_keys) == len(structural_parent), "duplicate structural parent memberships")
        req(len(ranked_keys) == len(ranked_parent), "duplicate ranked parent memberships")
        req(structural_keys == ranked_keys, f"ranked/structural recurrent parent membership disagreement d={denominator} b={bucket}")
        req(len(ranked_parent) == len(structural_parent), "ranked/structural parent count disagreement")

        sufficient = len(successor) >= len(ranked_parent)
        shortage = shortage or not sufficient
        subsets.append({
            "denominator": denominator,
            "bucket": bucket,
            "events_total": len(ids),
            "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
            "event_universe_sha256": intrinsic.universe_hash(ids),
            "equal_budget_k": len(ranked_parent),
            "candidate_budget_sufficient": sufficient,
            "successor_summary": successor_summary,
            "recurrent_summary": ranked_summary,
            "recurrent_structural_summary": structural_summary,
            "recurrent_dual_implementation_membership_exact": True,
            "successor_candidates": successor,
            "recurrent_candidates": ranked_parent,
        })

    pre = {
        "schema": "ORBITTRACE_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL",
        "scientific_role": "PRELABEL_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1",
        "engineering_repair": "repair1_dual_historical_recurrent_membership_audit",
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "intrinsic_source_commit": "312b1b718ae105813de242355142a74e7d377d65",
        "intrinsic_source_blob": INTRINSIC_SOURCE_BLOB,
        "configuration": {
            "graph": "exact_radius_1_physical_embedding_1284",
            "annual_coordinates": "radius_year_counts_over_annual_totals_no_scalarization",
            "filtration": "all_integer_count_threshold_pairs",
            "candidate": "every_exact_connected_component_membership_support_ge_4",
            "score": "support_cells_over_N22_times_N23",
            "ranking": "support_area_desc_then_family_hash_asc",
        },
        "candidate_budget_shortage_any_panel": shortage,
        "subsets": subsets,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL.json"
    out.write_text(json.dumps(pre, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "prelabel_sha256": intrinsic.sha256(out),
        "candidate_budget_shortage_any_panel": shortage,
        "smallest_panel_bruteforce_key": list(smallest_key),
        "subsets": [{"d":s["denominator"],"b":s["bucket"],"successor":len(s["successor_candidates"]),"recurrent":len(s["recurrent_candidates"]),"cells":s["successor_summary"]["exact_threshold_cell_count"],"states":s["successor_summary"]["raw_state_pair_count"]} for s in subsets],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
