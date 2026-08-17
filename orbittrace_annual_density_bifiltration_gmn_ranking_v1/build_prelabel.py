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
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BIF_PRETRUTH_SHA = "63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b"
BIF_STRUCTURAL_SHA = "d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7"
SPARSE_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"
PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_EVENTS = 738682


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


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()


def candidate_membership_hash(event_ids: list[str]) -> str:
    members = tuple(sorted(str(x) for x in event_ids))
    return hashlib.sha256(("\n".join(members) + "\n").encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bif-pretruth", type=Path, required=True)
    ap.add_argument("--bif-structural-result", type=Path, required=True)
    ap.add_argument("--sparse-source", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.bif_pretruth) == BIF_PRETRUTH_SHA, "bifiltration pretruth SHA mismatch")
    req(sha256(a.bif_structural_result) == BIF_STRUCTURAL_SHA, "bifiltration structural SHA mismatch")
    req(git_blob(a.sparse_source) == SPARSE_SOURCE_BLOB, "sparse evaluator source changed")
    req(git_blob(a.parent_runner) == PARENT_SOURCE_BLOB, "recurrent wrapper source changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == V8_SHA256, "GMN support artifact changed")

    bif = json.loads(a.bif_pretruth.read_text())
    structural = json.loads(a.bif_structural_result.read_text())
    req(bif.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_PRETRUTH_V1", "wrong bif pretruth schema")
    req(bif.get("scientific_role") == "ZERO_LABEL_BIFILTRATION_CANDIDATE_FREEZE", "wrong bif pretruth role")
    req(bif.get("shower_truth_used") is False, "bif pretruth truth flag")
    req(bif.get("target_information_access") is False and bif.get("target_region_events_accessed") is False, "bif pretruth firewall")
    req(structural.get("interpretation") == "SUPPORTS_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE", "structural prerequisite did not pass")
    req(structural.get("pretruth_sha256") == BIF_PRETRUTH_SHA, "structural result does not bind candidate freeze")

    frozen_subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in bif.get("subsets", [])}
    req(set(frozen_subsets) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "wrong bif subset set")

    sparse = load_module(a.sparse_source, "bifrank_sparse")
    parent = load_module(a.parent_runner, "bifrank_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")

    qmod = load_module(a.quality_source, "bifrank_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-annual-density-bifiltration-gmn-ranking-v1-target-excluded-prelabel"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    # Deliberately discard the sealed label mapping before any subset/candidate work.
    del hidden_sealed
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == EXPECTED_EVENTS, f"pooled event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([sparse.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    rows: list[dict[str, Any]] = []
    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            ix = sparse.selected_indices(hashes, denominator, bucket)
            ids = [ids_full[int(i)] for i in ix]
            years = np.asarray(years_full[ix], dtype=np.int64)
            x = np.asarray(xfull[ix], dtype=float)
            universe = set(ids)
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")

            recurrent, recurrent_summary = sparse.recurrent_ranked(parent, x, years, ids)
            k = len(recurrent)
            req(k > 0 and int(recurrent_summary["candidate_count"]) == k, "invalid recurrent budget")

            frozen = frozen_subsets[(denominator, bucket)]
            candidates = list(frozen.get("candidates", []))
            req(len(candidates) >= k, f"bif list shorter than K d={denominator} b={bucket}")
            req([int(r["rank"]) for r in candidates] == list(range(1, len(candidates) + 1)), "bif rank discontinuity")
            # Re-verify the total order that was frozen before the structural result.
            sorted_rows = sorted(candidates, key=lambda r: (-float(r["persistence_area"]), -int(r["member_count"]), str(r["family_hash"])))
            req([str(r["family_hash"]) for r in candidates] == [str(r["family_hash"]) for r in sorted_rows], "frozen bif order changed")
            seen: set[str] = set()
            for r in candidates:
                eids = [str(x) for x in r["event_ids"]]
                req(len(eids) == int(r["member_count"]), "bif member count mismatch")
                req(len(set(eids)) == len(eids), "duplicate event in bif candidate")
                req(set(eids).issubset(universe), "bif candidate contains out-of-universe event")
                req(candidate_membership_hash(eids) == str(r["family_hash"]), "bif membership hash mismatch")
                req(str(r["family_hash"]) not in seen, "duplicate bif membership hash")
                seen.add(str(r["family_hash"]))
                req(float(r["persistence_area"]) > 0.0, "nonpositive bif persistence area")

            annual_ids = {str(y): sorted(ids[int(i)] for i in np.flatnonzero(years == y)) for y in YEARS}
            rows.append({
                "denominator": denominator,
                "bucket": bucket,
                "event_count": len(ids),
                "event_universe_sha256": universe_hash(ids),
                "annual_event_ids": annual_ids,
                "equal_budget_k": k,
                "recurrent_candidates": recurrent,
                "bifiltration_candidates": candidates,
            })

    out = {
        "schema": "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL",
        "scientific_role": "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY",
        "frozen_bif_pretruth_sha256": BIF_PRETRUTH_SHA,
        "frozen_bif_structural_sha256": BIF_STRUCTURAL_SHA,
        "configuration": {
            "years": list(YEARS),
            "denominators": list(DENOMINATORS),
            "buckets": list(BUCKETS),
            "successor_order": ["persistence_area_desc", "member_count_desc", "membership_sha256_asc"],
            "equal_budget": "K_equals_complete_recurrent_candidate_count_per_pooled_subset",
        },
        "subsets": rows,
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
    result_sha = dump(a.output / "BIFILTRATION_GMN_RANKING_V1_PRELABEL.json", out)
    print(json.dumps({"prelabel_sha256": result_sha, "subset_count": len(rows), "budgets": [{"d":r["denominator"],"b":r["bucket"],"K":r["equal_budget_k"],"bif":len(r["bifiltration_candidates"])} for r in rows]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
