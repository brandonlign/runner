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
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
BLIND = (20.0, 55.0)
EXPECTED_SPARSE_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"
EXPECTED_SELECTOR_SOURCE_BLOB = "9bc98c6430bc9ed897b8ae81d7d9814e70050a61"
EXPECTED_PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
EXPECTED_QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_STRUCTURAL_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
EXPECTED_EVENT_TOTAL = 738682
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sparse-source", type=Path, required=True)
    ap.add_argument("--selector-source", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--structural-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob(a.sparse_source) == EXPECTED_SPARSE_SOURCE_BLOB, "sparse source blob changed")
    req(git_blob(a.selector_source) == EXPECTED_SELECTOR_SOURCE_BLOB, "selector source blob changed")
    req(git_blob(a.parent_runner) == EXPECTED_PARENT_SOURCE_BLOB, "parent source blob changed")
    req(sha256(a.quality_source) == EXPECTED_QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == EXPECTED_V8_SHA256, "GMN support artifact changed")
    req(sha256(a.structural_result_json) == EXPECTED_STRUCTURAL_SHA256, "structural result changed")

    sparse = load_module(a.sparse_source, "ptc_gmn_sparse")
    selector = load_module(a.selector_source, "ptc_gmn_selector")
    parent = load_module(a.parent_runner, "ptc_gmn_parent")
    structural = json.loads(a.structural_result_json.read_text())
    req(structural["scientific_role"] == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "structural role changed")
    req(structural["interpretation"] == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "structural prerequisite not positive")
    expected_fits = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected_fits) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "structural panel set changed")

    qmod = load_module(a.quality_source, "ptc_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-predictive-tree-cut-gmn-scale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == EXPECTED_EVENT_TOTAL, f"pooled event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([sparse.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    subsets: list[dict[str, Any]] = []
    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            ix = sparse.selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            x = np.asarray(xfull[ix], dtype=float)
            sub_years = np.asarray(years_full[ix], dtype=np.int64)
            sub_ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(sub_years == y) for y in YEARS), "subset lost a year")

            topo, topo_summary = sparse.topomodal_ranked(sub_events)
            recurrent, recurrent_summary = sparse.recurrent_ranked(parent, x, sub_years, sub_ids)
            expected = expected_fits[(denominator, bucket)]
            req(int(expected["events_total"]) == len(sub_ids), f"structural event count mismatch d={denominator} b={bucket}")
            req(expected["topomodal"]["candidate_rows"] == topo_summary["candidate_rows"], f"TopoModal membership mismatch d={denominator} b={bucket}")
            req(expected["recurrent_eom"]["candidate_rows"] == recurrent_summary["candidate_rows"], f"recurrent membership mismatch d={denominator} b={bucket}")
            k = len(recurrent)
            req(k > 0, "zero recurrent budget")

            annual: dict[str, Any] = {}
            for year in YEARS:
                annual_events = sorted((e for e in sub_events if int(e["year"]) == year), key=lambda e: str(e["id"]))
                annual_ids = [str(e["id"]) for e in annual_events]
                req(annual_ids, f"empty annual subset {year}")
                payload = {"families": topo}
                candidates = selector.projected_candidates(payload, annual_ids)
                _par, children, roots, sets = selector.build_laminar_forest(candidates, len(annual_ids))
                selector_rows = [
                    {
                        "id": str(e["id"]),
                        "sol": float(e["sol"]),
                        "sun_lon": float(e["lon"]),
                        "ecl_lat": float(e["lat"]),
                        "vg": float(e["vg"]),
                    }
                    for e in annual_events
                ]
                z = selector.embedding(selector_rows)
                atr, ate, dtr, dte, graph_summary = selector.split_graph(annual_ids, z)
                selector.score_candidates(candidates, atr, ate, dtr, dte)
                selected_ix = selector.predictive_cut(candidates, children, roots, sets)

                selected: list[dict[str, Any]] = []
                for rank, ci in enumerate(selected_ix, 1):
                    c = candidates[ci]
                    req(float(c["heldout_predictive_gain"]) > 0.0, "nonpositive selected gain")
                    selected.append({
                        "family_id": "ptc-gmn-" + str(c["annual_membership_sha256"])[:20],
                        "rank": rank,
                        "event_ids": list(c["event_ids"]),
                        "member_count": int(c["member_count"]),
                        "annual_membership_sha256": str(c["annual_membership_sha256"]),
                        "heldout_predictive_gain": float(c["heldout_predictive_gain"]),
                    })
                req(len(selected) >= k, f"predictive cut capacity below recurrent budget d={denominator} b={bucket} y={year}: {len(selected)}<{k}")
                req([r["rank"] for r in selected] == list(range(1, len(selected) + 1)), "rank discontinuity")
                annual[str(year)] = {
                    "event_ids": annual_ids,
                    "event_count": len(annual_ids),
                    "projected_candidate_count": len(candidates),
                    "selected_candidate_count": len(selected),
                    "graph_summary": graph_summary,
                    "candidates": selected,
                }

            subsets.append({
                "denominator": denominator,
                "bucket": bucket,
                "events_total": len(sub_ids),
                "events_by_year": {str(y): int(np.sum(sub_years == y)) for y in YEARS},
                "equal_budget_k": k,
                "recurrent_candidates": recurrent,
                "annual_predictive_tree_cut": annual,
            })

    result = {
        "schema": "ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_PRETRUTH",
        "scientific_role": "PRETRUTH_TARGET_EXCLUDED_GMN_SCALE_GENERALIZATION",
        "configuration": {
            "years": list(YEARS),
            "denominators": list(DENOMINATORS),
            "buckets": list(BUCKETS),
            "selector_source_blob": EXPECTED_SELECTOR_SOURCE_BLOB,
            "topomodal_sparse_source_blob": EXPECTED_SPARSE_SOURCE_BLOB,
            "equal_budget": "K_equals_complete_recurrent_candidate_count_per_pooled_subset",
        },
        "subsets": subsets,
        "blind_exclusion": list(BLIND),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "PREDICTIVE_TREE_CUT_V1_GMN_SCALE_PRETRUTH.json"
    result_sha = dump(out, result)
    print(json.dumps({"pretruth_sha256": result_sha, "subset_count": len(subsets), "capacities": [
        {"d": s["denominator"], "b": s["bucket"], "K": s["equal_budget_k"], "selected": {y: s["annual_predictive_tree_cut"][y]["selected_candidate_count"] for y in ("2022", "2023")}}
        for s in subsets
    ]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
