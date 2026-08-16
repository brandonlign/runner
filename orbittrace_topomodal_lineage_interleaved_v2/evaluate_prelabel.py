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


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], which: str) -> dict[str, Any]:
    vals = [p[which] for p in panels]
    return {
        "qualified_total": int(sum(int(v["qualified_matches"]) for v in vals)),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])) if vals else 0.0,
        "precision_mean": float(np.mean([float(v["top100_dominant_precision"]) for v in vals])) if vals else 0.0,
        "fragmentation_mean": float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])) if vals else 0.0,
        "recovered_at_25_total": int(sum(int(v["recovered_at_25"]) for v in vals)),
        "recovered_at_50_total": int(sum(int(v["recovered_at_50"]) for v in vals)),
        "recovered_at_100_total": int(sum(int(v["recovered_at_100"]) for v in vals)),
        "recovered_at_500_total": int(sum(int(v["recovered_at_500"]) for v in vals)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "intrinsic-runner",
        "prelabel",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    intrinsic = load_module(a.intrinsic_runner, "lineage_v2_eval_intrinsic")
    req(intrinsic.sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN utility changed")
    req(intrinsic.sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen v8 artifact changed")

    pre_sha = intrinsic.sha256(a.prelabel)
    pre = json.loads(a.prelabel.read_text())
    req(pre["schema"] == "ORBITTRACE_TOPOMODAL_LINEAGE_INTERLEAVED_V2_PRELABEL", "wrong prelabel schema")
    req(pre["scientific_role"] == "PRELABEL_TOPOMODAL_LINEAGE_INTERLEAVED_V2", "wrong prelabel role")
    req(pre["structural_result_sha256"] == STRUCTURAL_RESULT_SHA256, "structural source changed")
    req(pre["intrinsic_source_blob"] == INTRINSIC_SOURCE_BLOB, "intrinsic source changed")
    req(pre["configuration"]["candidate_universe"] == "complete_exact_1284_hierarchy", "candidate universe changed")
    req(pre["configuration"]["intrinsic_order"] == "exact_topomodal_sparse_recovery_v1_order", "intrinsic order changed")
    req(pre["configuration"]["lineage"] == "surviving_mode_peak_then_event_id_tie_break", "lineage changed")
    req(pre["configuration"]["ranking"] == "lineage_round_asc_then_intrinsic_rank_asc", "ranking changed")
    req(pre["blind_exclusion"] == list(BLIND) and pre["shower_truth_used"] is False, "prelabel firewall")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "target firewall")

    panels = {(int(r["denominator"]), int(r["bucket"])): r for r in pre["subsets"]}
    req(set(panels) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "prelabel panel set changed")
    for r in pre["subsets"]:
        succ = r["successor_candidates"]
        par = r["recurrent_candidates"]
        req(len(succ) >= len(par) and int(r["equal_budget_k"]) == len(par), "equal budget changed")
        req([int(x["rank"]) for x in succ] == list(range(1, len(succ) + 1)), "successor rank continuity")
        exp = sorted(succ, key=lambda x: (int(x["lineage_round"]), int(x["intrinsic_rank"])))
        req([str(x["family_id"]) for x in succ] == [str(x["family_id"]) for x in exp], "successor rank order changed")
        intrinsic_sorted = sorted(succ, key=lambda x: int(x["intrinsic_rank"]))
        req([int(x["intrinsic_rank"]) for x in intrinsic_sorted] == list(range(1, len(succ) + 1)), "intrinsic rank permutation changed")
        req(int(r["lineage_summary"]["first_round_count"]) == int(r["lineage_summary"]["lineage_count"]), "round-1 lineage coverage changed")
        req(len({str(x["lineage_key"]) for x in succ if int(x["lineage_round"]) == 1}) == int(r["lineage_summary"]["lineage_count"]), "round-1 lineage uniqueness changed")

    parent = load_module(a.parent_runner, "lineage_v2_eval_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support changed")

    q = load_module(a.quality_source, "lineage_v2_eval_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-lineage-interleaved-v2-evaluator"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base_source, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base_source)
    req(isinstance(hidden, dict), "truth payload not expected mapping")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == 738682, "pooled target-excluded event count changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row reached evaluator")

    ids = [str(e["id"]) for e in events]
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([intrinsic.event_hash_u64(eid) for eid in ids], dtype=np.uint64)

    truth_panels: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            fr = panels[(denominator, bucket)]
            ii = intrinsic.selected_indices(hashes, denominator, bucket)
            sid = [ids[int(i)] for i in ii]
            sy = np.asarray(years[ii], dtype=np.int64)
            req(len(sid) == int(fr["events_total"]), "event count changed at evaluation")
            req(intrinsic.universe_hash(sid) == str(fr["event_universe_sha256"]), "event universe changed at evaluation")

            K = int(fr["equal_budget_k"])
            succ = fr["successor_candidates"][:K]
            par = fr["recurrent_candidates"]
            req(len(succ) == len(par) == K and K > 0, "equal-budget list mismatch")

            for year in YEARS:
                annual = {sid[int(i)] for i in np.flatnonzero(sy == year)}
                pm = compact(parent.metrics(par, hidden, annual))
                sm = compact(parent.metrics(succ, hidden, annual))
                truth_panels.append(
                    {
                        "denominator": int(denominator),
                        "bucket": int(bucket),
                        "year": int(year),
                        "equal_budget_k": K,
                        "parent": pm,
                        "successor": sm,
                        "qualified_nonlower": int(sm["qualified_matches"]) >= int(pm["qualified_matches"]),
                        "qualified_strict_win": int(sm["qualified_matches"]) > int(pm["qualified_matches"]),
                    }
                )

    scales: dict[str, Any] = {}
    for denominator in (128, 1024):
        ps = [p for p in truth_panels if int(p["denominator"]) == denominator]
        req(len(ps) == 8, f"truth panel count changed d={denominator}")
        pa = aggregate(ps, "parent")
        sa = aggregate(ps, "successor")
        non = int(sum(bool(p["qualified_nonlower"]) for p in ps))
        win = int(sum(bool(p["qualified_strict_win"]) for p in ps))
        scales[str(denominator)] = {
            "parent": pa,
            "successor": sa,
            "qualified_nonlower_panels": non,
            "qualified_strict_win_panels": win,
            "qualified_loss_panels": 8 - non,
        }

    fp, fs = scales["1024"]["parent"], scales["1024"]["successor"]
    cp, cs = scales["128"]["parent"], scales["128"]["successor"]
    gates = {
        "fine_qualified_total_strictly_greater": fs["qualified_total"] > fp["qualified_total"],
        "fine_qualified_nonlower_at_least_6_of_8": scales["1024"]["qualified_nonlower_panels"] >= 6,
        "fine_mrr_mean_not_lower": fs["mrr_mean"] >= fp["mrr_mean"],
        "fine_precision_mean_not_lower": fs["precision_mean"] >= fp["precision_mean"],
        "fine_fragmentation_mean_not_higher": fs["fragmentation_mean"] <= fp["fragmentation_mean"],
        "coarse_qualified_total_not_lower": cs["qualified_total"] >= cp["qualified_total"],
        "coarse_qualified_nonlower_at_least_6_of_8": scales["128"]["qualified_nonlower_panels"] >= 6,
        "coarse_mrr_mean_not_lower": cs["mrr_mean"] >= cp["mrr_mean"],
        "coarse_precision_mean_not_lower": cs["precision_mean"] >= cp["precision_mean"],
        "coarse_fragmentation_mean_not_higher": cs["fragmentation_mean"] <= cp["fragmentation_mean"],
    }
    verdict = "PASS_TOPOMODAL_LINEAGE_INTERLEAVED_V2" if all(gates.values()) else "FAIL_TOPOMODAL_LINEAGE_INTERLEAVED_V2"

    result = {
        "schema": "ORBITTRACE_TOPOMODAL_LINEAGE_INTERLEAVED_V2",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "prelabel_sha256": pre_sha,
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "intrinsic_source_commit": "312b1b718ae105813de242355142a74e7d377d65",
        "intrinsic_source_blob": INTRINSIC_SOURCE_BLOB,
        "panels": truth_panels,
        "scale_aggregates": scales,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "TOPOMODAL_LINEAGE_INTERLEAVED_V2.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": pre_sha, "scales": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
