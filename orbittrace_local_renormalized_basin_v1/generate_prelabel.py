#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
SUPPORT_PRUNED_PRETRUTH_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def event_hash_u64(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big", signed=False)


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("structural-runner", "parent-runner", "quality-source", "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "support-pruned-pretruth"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve().parent
    lrb = load(here / "local_renormalized_basin.py", "lrb_method")
    support_pruned = load(here.parent / "orbittrace_m2d_support_pruned_cut_v1" / "support_pruned_cut.py", "lrb_support_pruned")
    structural = load(a.structural_runner, "lrb_structural")
    parent_runner = load(a.parent_runner, "lrb_parent_geometry")

    req(sha(a.quality_source) == QUALITY_SHA, "quality source changed")
    req(sha(a.v8_result_json) == V8_SHA, "v8 result changed")
    req(sha(a.support_pruned_pretruth) == SUPPORT_PRUNED_PRETRUTH_SHA, "support-pruned pretruth changed")
    req(float(lrb.RADIUS) == float(support_pruned.RADIUS) == float(structural.RADIUS) == 1.0, "radius changed")
    req(int(lrb.MIN_SUPPORT) == int(support_pruned.MIN_SUPPORT) == int(structural.MIN_SUPPORT) == 4, "support changed")
    req(int(lrb.LOCAL_PASSES) == 1, "local pass count changed")
    req(tuple(structural.BLIND) == BLIND and tuple(parent_runner.BLIND) == BLIND, "blind interval changed")

    baseline = json.loads(a.support_pruned_pretruth.read_text())
    req(baseline.get("schema") == "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH", "wrong support-pruned baseline schema")
    req(baseline.get("scientific_role") == "TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_RANKING_FROZEN_BEFORE_TRUTH", "wrong support-pruned baseline role")
    req(baseline.get("shower_truth_used") is False and baseline.get("target_information_access") is False and baseline.get("target_region_events_accessed") is False and baseline.get("orbittrace_reveal_access") is False, "baseline firewall changed")
    base_subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in baseline["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(base_subsets) == keys, "baseline panel set changed")

    q = load(a.quality_source, "lrb_gmn_loader")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = q.v1.mult.MONTH_KEYS
    support.CORPUS = "orbittrace-local-renormalized-basin-v1-target-excluded"
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
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected target-region event survived")
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(x) for x in ids_full], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    mechanism_panels = 0
    replaced_total = 0
    local_noise_total = 0
    for d in DENOMS:
        for b in BUCKETS:
            bs = base_subsets[(d, b)]
            ix = selected_indices(hashes, d, b)
            sub = [events[int(i)] for i in ix]
            ids = [ids_full[int(i)] for i in ix]
            yrs = np.asarray([int(events[int(i)]["year"]) for i in ix], dtype=np.int64)
            frozen_annual = {str(y): [str(x) for x in bs["annual_event_ids"][str(y)]] for y in YEARS}
            frozen_ids = set(frozen_annual["2022"]).union(frozen_annual["2023"])
            req(set(ids) == frozen_ids and len(ids) == int(bs["event_count"]), f"sparse universe mismatch d={d} b={b}")
            req(universe_hash(ids) == str(bs.get("event_universe_sha256", universe_hash(ids))), f"sparse universe hash mismatch d={d} b={b}")

            print(f"[lrb-prelabel] d={d} b={b} n={len(ids)}", flush=True)
            rows, summary = lrb.local_renormalized_basin_cut(structural, support_pruned, sub)
            if bool(summary["mechanism_active"]):
                mechanism_panels += 1
            replaced_total += int(summary["replaced_parent_count"])
            local_noise_total += int(summary["local_discarded_event_count"])
            req(all(len(r["event_ids"]) == int(r["member_count"]) >= 4 for r in rows), "invalid LRB candidate")
            sets = [frozenset(str(x) for x in r["event_ids"]) for r in rows]
            req(all(not x.intersection(y) for i, x in enumerate(sets) for y in sets[i + 1 :]), "LRB overlap")
            req(all(m.issubset(frozen_ids) for m in sets), "LRB candidate outside frozen universe")

            subsets.append({
                "denominator": d,
                "bucket": b,
                "event_count": len(ids),
                "events_by_year": {str(y): int(np.sum(yrs == y)) for y in YEARS},
                "event_universe_sha256": universe_hash(ids),
                "annual_event_ids": frozen_annual,
                "equal_budget_k": int(bs["equal_budget_k"]),
                "lrb_candidates": rows,
                "support_pruned_baseline_candidates": list(bs["refined_candidates"]),
                "lrb_summary": summary,
            })

    payload = {
        "schema": "ORBITTRACE_LOCAL_RENORMALIZED_BASIN_V1_PRELABEL",
        "scientific_role": "TARGET_EXCLUDED_GMN_LOCAL_RENORMALIZED_BASIN_V1_FROZEN_BEFORE_M2D_AND_TRUTH",
        "configuration": {
            "parent": "promoted_support_pruned_m2d_v1",
            "radius": 1.0,
            "minimum_support": 4,
            "local_passes": 1,
            "local_density": "induced_radius_degree_over_parent_member_count",
            "replacement_rule": "replace_parent_iff_local_support_pruned_pass_has_at_least_two_reportable_candidates",
            "contrast_unit_conversion": "local_modal_contrast_times_parent_member_count_over_panel_event_count",
            "ranking_before_M2D": ["globalized_modal_contrast_desc", "family_hash_asc"],
            "new_tuned_parameters": [],
        },
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_PRETRUTH_SHA,
        "subsets": subsets,
        "mechanism_summary": {
            "active_panels": mechanism_panels,
            "total_panels": 8,
            "replaced_parent_count": replaced_total,
            "local_discarded_event_count": local_noise_total,
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "orbittrace_reveal_access": False,
        "sonotaco_2013_2014_access": False,
        "method_parameter_selection_from_result": False,
    }
    dst = a.output / "LOCAL_RENORMALIZED_BASIN_V1_PRELABEL.json"
    dst.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_LRB_V1_PRELABEL", "sha256": sha(dst), "mechanism_summary": payload["mechanism_summary"], "panels": [{"d":s["denominator"],"b":s["bucket"],"candidates":len(s["lrb_candidates"]),"K":s["equal_budget_k"],"replaced":s["lrb_summary"]["replaced_parent_count"]} for s in subsets]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
