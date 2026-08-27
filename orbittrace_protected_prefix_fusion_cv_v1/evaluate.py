#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BUCKETS = (0, 1, 2, 3)
PREFIX_QUARTERS = (0, 1, 2, 3, 4)
PRELABEL_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
EXPECTED_K = {(128, 0): 29, (128, 1): 35, (128, 2): 38, (128, 3): 33,
              (1024, 0): 8, (1024, 1): 5, (1024, 2): 6, (1024, 3): 9}


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


def event_set(row: dict[str, Any]) -> set[str]:
    return set(map(str, row["event_ids"]))


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    seen: set[str] = set()
    for row in rows:
        ids = event_set(row)
        if seen.intersection(ids):
            return False
        seen.update(ids)
    return True


def prefix_count(k: int, quarter: int) -> int:
    req(quarter in PREFIX_QUARTERS, f"invalid prefix quarter {quarter}")
    if quarter == 0:
        return 0
    return int(math.ceil((quarter * k) / 4.0))


def tagged(row: dict[str, Any], source: str) -> dict[str, Any]:
    out = dict(row)
    out["fusion_source"] = source
    return out


def protected_prefix_fusion(
    recurrent: list[dict[str, Any]],
    support_cut: list[dict[str, Any]],
    k: int,
    quarter: int,
) -> list[dict[str, Any]]:
    req(len(recurrent) >= k, "recurrent candidate capacity below K")
    p = prefix_count(k, quarter)
    out = [tagged(row, "recurrent") for row in recurrent[:p]]
    used: set[str] = set()
    for row in out:
        ids = event_set(row)
        req(ids and used.isdisjoint(ids), "protected recurrent prefix overlaps")
        used.update(ids)
    for row in support_cut:
        if len(out) >= k:
            break
        ids = event_set(row)
        if ids and used.isdisjoint(ids):
            out.append(tagged(row, "support_cut"))
            used.update(ids)
    if len(out) < k:
        for row in recurrent[p:k]:
            if len(out) >= k:
                break
            ids = event_set(row)
            if ids and used.isdisjoint(ids):
                out.append(tagged(row, "recurrent_backfill"))
                used.update(ids)
    req(len(out) == k, f"fusion capacity below K for quarter={quarter}: {len(out)} < {k}")
    req(pairwise_disjoint(out), "fused catalogue overlaps")
    return out


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def aggregate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    req(bool(rows), "cannot aggregate empty metric list")
    return {
        "qualified_total": sum(int(r["qualified_matches"]) for r in rows),
        "mrr_mean": mean(float(r["mrr"]) for r in rows),
        "precision_mean": mean(float(r["top100_dominant_precision"]) for r in rows),
        "fragmentation_mean": mean(float(r["fragmentation_median_top500"]) for r in rows),
        "recovered_at_25_total": sum(int(r["recovered_at_25"]) for r in rows),
        "recovered_at_50_total": sum(int(r["recovered_at_50"]) for r in rows),
        "recovered_at_100_total": sum(int(r["recovered_at_100"]) for r in rows),
        "recovered_at_500_total": sum(int(r["recovered_at_500"]) for r in rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelabel", type=Path, required=True)
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

    req(sha256(a.prelabel) == PRELABEL_SHA, "sealed internal-mass prelabel changed")
    req(git_blob(a.parent_runner) == PARENT_BLOB, "parent metric source changed")
    req(sha256(a.quality_source) == QUALITY_SHA, "GMN utility source changed")
    req(sha256(a.v8_result_json) == V8_SHA, "frozen v8 support artifact changed")

    pre = json.loads(a.prelabel.read_text())
    req(pre.get("schema") == "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL", "wrong prelabel schema")
    req(pre.get("scientific_role") == "PRELABEL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1", "wrong prelabel role")
    req(pre.get("configuration", {}).get("ranking") == ["internal_2d_mass_desc", "modal_contrast_desc", "family_hash_asc"], "support-cut order changed")
    req(pre.get("shower_truth_used") is False, "truth entered prelabel")
    req(pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False, "prelabel target firewall")
    req(pre.get("sonotaco_2013_2014_access") is False, "SonotaCo entered prelabel")

    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subsets) == set(EXPECTED_K), "panel set changed")
    structural: dict[str, Any] = {"subsets": {}}
    for key, s in subsets.items():
        k = int(s["equal_budget_k"])
        req(k == EXPECTED_K[key], f"K changed {key}")
        rec = list(s["recurrent_candidates"])
        sup = list(s["successor_candidates"])
        req(len(rec) >= k and len(sup) >= k, f"source capacity changed {key}")
        req(pairwise_disjoint(rec), f"recurrent list no longer disjoint {key}")
        req(pairwise_disjoint(sup), f"support-cut list no longer disjoint {key}")
        qrows: dict[str, Any] = {}
        for q in PREFIX_QUARTERS:
            fused = protected_prefix_fusion(rec, sup, k, q)
            p = prefix_count(k, q)
            req([event_set(r) for r in fused[:p]] == [event_set(r) for r in rec[:p]], f"protected prefix changed {key} q={q}")
            if q == 4:
                req([event_set(r) for r in fused] == [event_set(r) for r in rec[:k]], f"q=4 is not exact recurrent baseline {key}")
            qrows[str(q)] = {
                "prefix_count": p,
                "candidate_count": len(fused),
                "support_cut_slots": sum(r.get("fusion_source") == "support_cut" for r in fused),
                "recurrent_slots": sum(str(r.get("fusion_source", "")).startswith("recurrent") for r in fused),
                "unique_event_coverage": len(set().union(*(event_set(r) for r in fused))),
            }
        structural["subsets"][f"{key[0]}:{key[1]}"] = qrows

    parent = load_module(a.parent_runner, "protected_prefix_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    qmod = load_module(a.quality_source, "protected_prefix_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-protected-prefix-fusion-cv-v1-gmn-evaluation"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "evaluation firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict), "sealed GMN truth mapping unavailable")
    req(sorted(scan) == list(YEARS), "GMN development years changed")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    all_eval_ids: set[str] = set()
    for s in subsets.values():
        for year in YEARS:
            all_eval_ids.update(str(x) for x in s["annual_event_ids"][str(year)])
    req(all(eid in hidden for eid in all_eval_ids), "stored evaluation event missing truth mapping")

    panel_cache: dict[tuple[int, int, int, int], dict[str, Any]] = {}
    parent_cache: dict[tuple[int, int, int], dict[str, Any]] = {}
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            s = subsets[(denominator, bucket)]
            k = int(s["equal_budget_k"])
            rec = list(s["recurrent_candidates"][:k])
            sup = list(s["successor_candidates"])
            for year in YEARS:
                annual_ids = set(str(x) for x in s["annual_event_ids"][str(year)])
                parent_cache[(denominator, bucket, year)] = compact(parent.metrics(rec, hidden, annual_ids))
                for q in PREFIX_QUARTERS:
                    fused = protected_prefix_fusion(rec, sup, k, q)
                    panel_cache[(denominator, bucket, year, q)] = compact(parent.metrics(fused, hidden, annual_ids))
                req(panel_cache[(denominator, bucket, year, 4)] == parent_cache[(denominator, bucket, year)],
                    f"q=4 metric baseline mismatch d={denominator} b={bucket} y={year}")

    selections: list[dict[str, Any]] = []
    heldout_panels: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for test_year in YEARS:
            dev_year = YEARS[1] if test_year == YEARS[0] else YEARS[0]
            parent_dev_rows = [parent_cache[(denominator, b, dev_year)] for b in BUCKETS]
            parent_dev = aggregate_metrics(parent_dev_rows)
            configs: list[dict[str, Any]] = []
            for q in PREFIX_QUARTERS:
                dev_rows = [panel_cache[(denominator, b, dev_year, q)] for b in BUCKETS]
                agg = aggregate_metrics(dev_rows)
                nonlower = sum(int(row["qualified_matches"]) >= int(par["qualified_matches"])
                               for row, par in zip(dev_rows, parent_dev_rows))
                admissible = (
                    int(agg["qualified_total"]) >= int(parent_dev["qualified_total"]) and
                    nonlower >= 3 and
                    float(agg["mrr_mean"]) >= float(parent_dev["mrr_mean"]) and
                    float(agg["precision_mean"]) >= float(parent_dev["precision_mean"]) and
                    float(agg["fragmentation_mean"]) <= float(parent_dev["fragmentation_mean"])
                )
                configs.append({
                    "prefix_quarter": q,
                    "prefix_fraction": q / 4.0,
                    "dev_aggregate": agg,
                    "dev_qualified_nonlower_buckets": nonlower,
                    "admissible": bool(admissible),
                })
            eligible = [c for c in configs if c["admissible"]]
            req(bool(eligible), f"no admissible config d={denominator} test={test_year}; recurrent baseline must remain admissible")
            chosen = max(
                eligible,
                key=lambda c: (
                    int(c["dev_aggregate"]["qualified_total"]),
                    int(c["dev_qualified_nonlower_buckets"]),
                    float(c["dev_aggregate"]["mrr_mean"]),
                    float(c["dev_aggregate"]["precision_mean"]),
                    int(c["prefix_quarter"]),
                ),
            )
            q = int(chosen["prefix_quarter"])
            selections.append({
                "denominator": denominator,
                "development_year": dev_year,
                "test_year": test_year,
                "selected_prefix_quarter": q,
                "selected_prefix_fraction": q / 4.0,
                "parent_development_aggregate": parent_dev,
                "configurations": configs,
            })
            for bucket in BUCKETS:
                pm = parent_cache[(denominator, bucket, test_year)]
                sm = panel_cache[(denominator, bucket, test_year, q)]
                heldout_panels.append({
                    "denominator": denominator,
                    "bucket": bucket,
                    "development_year": dev_year,
                    "test_year": test_year,
                    "selected_prefix_quarter": q,
                    "equal_budget_k": EXPECTED_K[(denominator, bucket)],
                    "parent_equal_budget": pm,
                    "successor_equal_budget": sm,
                    "qualified_nonlower": int(sm["qualified_matches"]) >= int(pm["qualified_matches"]),
                    "qualified_strict_win": int(sm["qualified_matches"]) > int(pm["qualified_matches"]),
                })

    req(len(heldout_panels) == 16, "wrong held-out panel count")
    scales: dict[str, Any] = {}
    for denominator in (128, 1024):
        rows = [p for p in heldout_panels if int(p["denominator"]) == denominator]
        req(len(rows) == 8, f"wrong held-out scale panel count d={denominator}")
        parent_agg = aggregate_metrics([p["parent_equal_budget"] for p in rows])
        succ_agg = aggregate_metrics([p["successor_equal_budget"] for p in rows])
        nonlower = sum(bool(p["qualified_nonlower"]) for p in rows)
        strict = sum(bool(p["qualified_strict_win"]) for p in rows)
        scales[str(denominator)] = {
            "parent_equal_budget": parent_agg,
            "successor_equal_budget": succ_agg,
            "qualified_nonlower_panels": nonlower,
            "qualified_strict_win_panels": strict,
            "qualified_loss_panels": 8 - nonlower,
        }

    fp, fs = scales["1024"]["parent_equal_budget"], scales["1024"]["successor_equal_budget"]
    cp, cs = scales["128"]["parent_equal_budget"], scales["128"]["successor_equal_budget"]
    gates = {
        "fine_qualified_total_strictly_greater": int(fs["qualified_total"]) > int(fp["qualified_total"]),
        "fine_qualified_nonlower_at_least_6_of_8": int(scales["1024"]["qualified_nonlower_panels"]) >= 6,
        "fine_mrr_mean_not_lower": float(fs["mrr_mean"]) >= float(fp["mrr_mean"]),
        "fine_precision_mean_not_lower": float(fs["precision_mean"]) >= float(fp["precision_mean"]),
        "fine_fragmentation_mean_not_higher": float(fs["fragmentation_mean"]) <= float(fp["fragmentation_mean"]),
        "coarse_qualified_total_not_lower": int(cs["qualified_total"]) >= int(cp["qualified_total"]),
        "coarse_qualified_nonlower_at_least_6_of_8": int(scales["128"]["qualified_nonlower_panels"]) >= 6,
        "coarse_mrr_mean_not_lower": float(cs["mrr_mean"]) >= float(cp["mrr_mean"]),
        "coarse_precision_mean_not_lower": float(cs["precision_mean"]) >= float(cp["precision_mean"]),
        "coarse_fragmentation_mean_not_higher": float(cs["fragmentation_mean"]) <= float(cp["fragmentation_mean"]),
    }
    verdict = "PASS_PROTECTED_PREFIX_FUSION_CV_V1_GMN" if all(gates.values()) else "FAIL_PROTECTED_PREFIX_FUSION_CV_V1_GMN"
    result = {
        "schema": "ORBITTRACE_PROTECTED_PREFIX_FUSION_CV_V1_GMN",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_CROSS_YEAR_HELDOUT_FUSION_DEVELOPMENT",
        "verdict": verdict,
        "source_prelabel_sha256": PRELABEL_SHA,
        "configuration": {
            "prefix_quarters": list(PREFIX_QUARTERS),
            "selection_scope": "one shared quarter per scale per fold, selected on opposite year across four buckets",
            "admissibility": "dev qualified_total >= parent; >=3/4 bucketwise qualified nonlower; dev MRR and precision nonlower; fragmentation nonhigher",
            "objective": "lexicographic qualified_total, nonlower_bucket_count, MRR, precision, larger protected prefix",
        },
        "structural_audit": structural,
        "selections": selections,
        "heldout_panels": heldout_panels,
        "scale_aggregates": scales,
        "gates": gates,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "test_year_used_for_configuration_selection": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "PROTECTED_PREFIX_FUSION_CV_V1_GMN.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "selections": selections, "scale_aggregates": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
