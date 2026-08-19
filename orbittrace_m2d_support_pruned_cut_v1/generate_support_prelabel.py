#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

BASELINE_M2D_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("structural-runner", "structural-result-json", "parent-runner", "quality-source", "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "baseline-m2d-prelabel"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve().parent
    original = load(here.parent / "orbittrace_topomodal_support_resolved_cut_v1" / "generate_prelabel.py", "support_cut_parent_exact")
    refined = load(here / "support_pruned_cut.py", "support_pruned_cut_exact")
    structural = original.load_module(a.structural_runner, "support_pruned_structural")
    parent_runner = original.load_module(a.parent_runner, "support_pruned_parent_geometry")

    req(float(original.RADIUS) == 1.0 and int(original.MIN_SUPPORT) == 4, "parent cut constants changed")
    req(float(refined.RADIUS) == 1.0 and int(refined.MIN_SUPPORT) == 4, "refined cut constants changed")
    req(tuple(structural.BLIND) == BLIND and float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent geometry blind interval changed")
    req(original.sha256(a.quality_source) == original.QUALITY_SHA256, "quality source changed")
    req(original.sha256(a.v8_result_json) == original.V8_RESULT_SHA256, "v8 artifact changed")
    req(original.sha256(a.structural_result_json) == original.STRUCTURAL_RESULT_SHA256, "structural artifact changed")
    req(sha256(a.baseline_m2d_prelabel) == BASELINE_M2D_SHA, "baseline M2D prelabel changed")

    sr = json.loads(a.structural_result_json.read_text())
    req(sr["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "structural prerequisite")
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in sr["fits"]}
    baseline = json.loads(a.baseline_m2d_prelabel.read_text())
    req(baseline.get("schema") == "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL", "wrong baseline M2D schema")
    base_subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in baseline["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(expected) == set(base_subsets) == keys, "panel set changed")

    q = original.load_module(a.quality_source, "support_pruned_gmn_loader")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = q.v1.mult.MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-support-pruned-cut-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "loader blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _c, base, _s = support.load_sources(a)
    scan, _cal, hidden_unused, sources = support.parse_catalogue(base)
    del hidden_unused
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(q.v1.mult.MONTH_KEYS), "GMN source set changed")

    events: list[dict[str, Any]] = []
    for y in YEARS:
        events.extend(parent_runner.normalize_event(r, y) for r in list(scan[y]))
    req(len(events) == 738682 and len({str(e["id"]) for e in events}) == 738682, "event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived")
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([original.event_hash_u64(x) for x in ids_full], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    for d in DENOMS:
        for b in BUCKETS:
            key = (d, b)
            ix = original.selected_indices(hashes, d, b)
            sub = [events[int(i)] for i in ix]
            ids = [ids_full[int(i)] for i in ix]
            yrs = np.asarray([int(events[int(i)]["year"]) for i in ix], dtype=np.int64)
            bs = base_subsets[key]
            frozen_annual = {str(y): [str(x) for x in bs["annual_event_ids"][str(y)]] for y in YEARS}
            frozen_ids = set(frozen_annual["2022"]).union(frozen_annual["2023"])
            req(set(ids) == frozen_ids and len(ids) == int(bs["event_count"]), f"baseline sparse universe mismatch d={d} b={b}")
            req({str(y): int(np.sum(yrs == y)) for y in YEARS} == {str(y): len(frozen_annual[str(y)]) for y in YEARS}, f"annual counts changed d={d} b={b}")

            print(f"[support-pruned-prelabel] d={d} b={b} n={len(ids)}", flush=True)
            succ, summary = refined.support_pruned_cut(structural, sub)
            ex = expected[key]
            req(ex["topomodal"]["candidate_rows"] == summary["full_candidate_rows"] and int(ex["topomodal"]["candidate_count"]) == int(summary["full_candidate_count"]), f"frozen hierarchy mismatch d={d} b={b}")
            k = int(bs["equal_budget_k"])
            req(k > 0 and len(succ) >= k, f"refined candidate capacity below frozen budget d={d} b={b}")
            subsets.append({
                "denominator": d,
                "bucket": b,
                "events_total": len(ids),
                "events_by_year": {str(y): int(np.sum(yrs == y)) for y in YEARS},
                "event_universe_sha256": original.universe_hash(ids),
                "annual_event_ids": frozen_annual,
                "equal_budget_k": k,
                "cut_summary": summary,
                "successor_candidates": succ,
            })

    payload = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SUPPORT_PRELABEL",
        "scientific_role": "PRELABEL_TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_CUT_V1",
        "configuration": {
            "cut_rule": "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport",
            "minimum_support": 4,
            "radius": 1.0,
            "ranking": "modal_contrast_desc_then_family_hash_asc",
            "candidate_budget": "exact_frozen_baseline_M2D_equal_budget_k_per_panel",
            "new_tuned_parameters": [],
        },
        "parent_cut_source_blob": "4988997c023d9df2b504372b4290dcab379a6dcc",
        "baseline_m2d_prelabel_sha256": BASELINE_M2D_SHA,
        "structural_result_sha256": original.STRUCTURAL_RESULT_SHA256,
        "subsets": subsets,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "orbittrace_reveal_access": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    dst = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SUPPORT_PRELABEL.json"
    dst.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": "PASS_SUPPORT_PRUNED_CUT_V1_PRELABEL",
        "sha256": sha256(dst),
        "subsets": [{"d": s["denominator"], "b": s["bucket"], "candidates": len(s["successor_candidates"]), "K": s["equal_budget_k"], "discarded_events": s["cut_summary"]["discarded_subsupport_event_count"]} for s in subsets],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
