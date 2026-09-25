#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import mean
from typing import Any

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BUCKETS = (0, 1, 2, 3)
PRELABEL_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
EXPECTED_K = {(128,0):29,(128,1):35,(128,2):38,(128,3):33,(1024,0):8,(1024,1):5,(1024,2):6,(1024,3):9}


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


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], field: str) -> dict[str, Any]:
    vals = [p[field] for p in panels]
    return {
        "qualified_total": sum(int(v["qualified_matches"]) for v in vals),
        "mrr_mean": mean(float(v["mrr"]) for v in vals),
        "precision_mean": mean(float(v["top100_dominant_precision"]) for v in vals),
        "fragmentation_mean": mean(float(v["fragmentation_median_top500"]) for v in vals),
        "recovered_at_25_total": sum(int(v["recovered_at_25"]) for v in vals),
        "recovered_at_50_total": sum(int(v["recovered_at_50"]) for v in vals),
        "recovered_at_100_total": sum(int(v["recovered_at_100"]) for v in vals),
        "recovered_at_500_total": sum(int(v["recovered_at_500"]) for v in vals),
    }


def pairwise_disjoint(rows: list[dict[str, Any]]) -> bool:
    sets = [set(str(x) for x in r["event_ids"]) for r in rows]
    return all(not a.intersection(b) for i, a in enumerate(sets) for b in sets[i + 1 :])


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
    req(pre.get("configuration", {}).get("formula") == "M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)", "score formula changed")
    req(pre.get("configuration", {}).get("ranking") == ["internal_2d_mass_desc", "modal_contrast_desc", "family_hash_asc"], "ranking changed")
    req(pre.get("shower_truth_used") is False, "truth entered prelabel")
    req(pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False, "prelabel target firewall")
    req(pre.get("sonotaco_2013_2014_access") is False, "SonotaCo entered prelabel")
    req(pre.get("amos_scientific_access") is False and pre.get("maarsy_scientific_access") is False and pre.get("dms_scientific_access") is False, "protected external access in prelabel")

    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subsets) == set(EXPECTED_K), "panel set changed")
    for key, s in subsets.items():
        k = int(s["equal_budget_k"])
        req(k == EXPECTED_K[key], f"K changed {key}")
        succ = list(s["successor_candidates"])
        par = list(s["recurrent_candidates"])
        req(len(succ) >= k and len(par) >= k, f"capacity changed {key}")
        req([int(r["internal_mass_rank"]) for r in succ] == list(range(1, len(succ) + 1)), f"rank discontinuity {key}")
        frozen_order = sorted(succ, key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
        req([str(r["family_id"]) for r in succ] == [str(r["family_id"]) for r in frozen_order], f"stored order changed {key}")
        req(pairwise_disjoint(succ), f"support-cut disjointness changed {key}")
        annual = s["annual_event_ids"]
        req(set(annual) == {"2022", "2023"}, f"annual universe keys changed {key}")
        req(len(set(map(str, annual["2022"])).intersection(map(str, annual["2023"]))) == 0, f"annual universes overlap {key}")
        req(len(set(map(str, annual["2022"])).union(map(str, annual["2023"]))) == int(s["event_count"]), f"event count mismatch {key}")

    parent = load_module(a.parent_runner, "internal_mass_gmn_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")

    qmod = load_module(a.quality_source, "internal_mass_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-support-cut-bifiltration-internal-mass-v1-gmn-evaluation"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "evaluation firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict), "sealed GMN truth mapping unavailable")
    req(sorted(scan) == list(YEARS), "GMN development years changed")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    # Candidate construction/ranking stays sealed. Only verify that each stored evaluation ID has truth.
    all_eval_ids: set[str] = set()
    for s in subsets.values():
        for year in YEARS:
            all_eval_ids.update(str(x) for x in s["annual_event_ids"][str(year)])
    req(all(eid in hidden for eid in all_eval_ids), "stored evaluation event missing truth mapping")

    panels: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            s = subsets[(denominator, bucket)]
            k = int(s["equal_budget_k"])
            succ = list(s["successor_candidates"][:k])
            par = list(s["recurrent_candidates"][:k])
            for year in YEARS:
                annual_ids = set(str(x) for x in s["annual_event_ids"][str(year)])
                pm = compact(parent.metrics(par, hidden, annual_ids))
                sm = compact(parent.metrics(succ, hidden, annual_ids))
                panels.append({
                    "denominator": denominator,
                    "bucket": bucket,
                    "year": year,
                    "equal_budget_k": k,
                    "parent_equal_budget": pm,
                    "successor_equal_budget": sm,
                    "qualified_nonlower": int(sm["qualified_matches"]) >= int(pm["qualified_matches"]),
                    "qualified_strict_win": int(sm["qualified_matches"]) > int(pm["qualified_matches"]),
                })

    req(len(panels) == 16, "wrong annual panel count")
    scales: dict[str, Any] = {}
    for denominator in (128, 1024):
        ps = [p for p in panels if int(p["denominator"]) == denominator]
        req(len(ps) == 8, f"wrong scale panel count d={denominator}")
        parent_agg = aggregate(ps, "parent_equal_budget")
        succ_agg = aggregate(ps, "successor_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in ps)
        strict = sum(bool(p["qualified_strict_win"]) for p in ps)
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
    verdict = "PASS_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN" if all(gates.values()) else "FAIL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN"
    result = {
        "schema": "ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "prelabel_sha256": PRELABEL_SHA,
        "panels": panels,
        "scale_aggregates": scales,
        "gates": gates,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": PRELABEL_SHA, "scale_aggregates": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
