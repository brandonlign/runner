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
EXPECTED_PRETRUTH_SCHEMA = "ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_PRETRUTH"
EXPECTED_SPARSE_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"
EXPECTED_PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
EXPECTED_QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
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


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    return {
        "qualified_total": int(sum(int(v["qualified_matches"]) for v in vals)),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])),
        "precision_mean": float(np.mean([float(v["top100_dominant_precision"]) for v in vals])),
        "fragmentation_mean": float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])),
        "recovered_at_25_total": int(sum(int(v["recovered_at_25"]) for v in vals)),
        "recovered_at_50_total": int(sum(int(v["recovered_at_50"]) for v in vals)),
        "recovered_at_100_total": int(sum(int(v["recovered_at_100"]) for v in vals)),
        "recovered_at_500_total": int(sum(int(v["recovered_at_500"]) for v in vals)),
    }


def compact(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
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

    req(git_blob(a.sparse_source) == EXPECTED_SPARSE_SOURCE_BLOB, "sparse source changed")
    req(git_blob(a.parent_runner) == EXPECTED_PARENT_SOURCE_BLOB, "parent source changed")
    req(sha256(a.quality_source) == EXPECTED_QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == EXPECTED_V8_SHA256, "GMN support artifact changed")

    pre = json.loads(a.pretruth.read_text())
    pre_sha = sha256(a.pretruth)
    req(pre.get("schema") == EXPECTED_PRETRUTH_SCHEMA, "wrong pretruth schema")
    req(pre.get("scientific_role") == "PRETRUTH_TARGET_EXCLUDED_GMN_SCALE_GENERALIZATION", "wrong pretruth role")
    req(pre.get("shower_truth_used") is False, "pretruth truth flag")
    req(pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False, "pretruth firewall")
    req(pre.get("sonotaco_2013_2014_access") is False, "SonotaCo entered pretruth")
    req(len(pre.get("subsets", [])) == 8, "wrong subset count")

    sparse = load_module(a.sparse_source, "ptc_gmn_eval_sparse")
    parent = load_module(a.parent_runner, "ptc_gmn_eval_parent")
    qmod = load_module(a.quality_source, "ptc_gmn_eval_utility")
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
    _scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")
    req(isinstance(hidden_sealed, dict), "hidden truth payload unavailable")

    panels: list[dict[str, Any]] = []
    for subset in pre["subsets"]:
        d = int(subset["denominator"])
        b = int(subset["bucket"])
        req(d in DENOMINATORS and b in BUCKETS, "unexpected subset")
        k = int(subset["equal_budget_k"])
        recurrent = list(subset["recurrent_candidates"])
        req(len(recurrent) == k, "recurrent budget changed")
        for year in YEARS:
            annual = subset["annual_predictive_tree_cut"][str(year)]
            annual_ids = set(str(x) for x in annual["event_ids"])
            successor_all = list(annual["candidates"])
            req(len(successor_all) >= k, "pretruth capacity no longer holds")
            successor = successor_all[:k]
            parent_m = compact(parent.metrics(recurrent, hidden_sealed, annual_ids))
            succ_m = compact(parent.metrics(successor, hidden_sealed, annual_ids))
            panels.append({
                "denominator": d,
                "bucket": b,
                "year": year,
                "equal_budget_k": k,
                "recurrent_eom": parent_m,
                "predictive_tree_cut": succ_m,
                "qualified_nonlower": int(succ_m["qualified_matches"]) >= int(parent_m["qualified_matches"]),
                "qualified_strict_win": int(succ_m["qualified_matches"]) > int(parent_m["qualified_matches"]),
            })

    req(len(panels) == 16, "wrong truth panel count")
    scale: dict[str, Any] = {}
    gates: dict[str, bool] = {}
    for d in DENOMINATORS:
        ps = [p for p in panels if int(p["denominator"]) == d]
        req(len(ps) == 8, f"wrong panel count d={d}")
        parent_agg = aggregate(ps, "recurrent_eom")
        succ_agg = aggregate(ps, "predictive_tree_cut")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in ps)
        strict = sum(bool(p["qualified_strict_win"]) for p in ps)
        scale[str(d)] = {
            "recurrent_eom": parent_agg,
            "predictive_tree_cut": succ_agg,
            "qualified_nonlower_panels": nonlower,
            "qualified_strict_win_panels": strict,
            "qualified_loss_panels": 8 - nonlower,
        }
        prefix = "fine" if d == 1024 else "coarse"
        gates[f"{prefix}_qualified_total_strictly_greater"] = int(succ_agg["qualified_total"]) > int(parent_agg["qualified_total"])
        gates[f"{prefix}_qualified_nonlower_at_least_6_of_8"] = nonlower >= 6
        gates[f"{prefix}_mrr_mean_not_lower"] = float(succ_agg["mrr_mean"]) >= float(parent_agg["mrr_mean"])
        gates[f"{prefix}_precision_mean_not_lower"] = float(succ_agg["precision_mean"]) >= float(parent_agg["precision_mean"])
        gates[f"{prefix}_fragmentation_mean_not_higher"] = float(succ_agg["fragmentation_mean"]) <= float(parent_agg["fragmentation_mean"])

    req(len(gates) == 10, "wrong gate count")
    verdict = "PASS_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_GENERALIZATION" if all(gates.values()) else "FAIL_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_GENERALIZATION"
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_GENERALIZATION",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SCALE_GENERALIZATION_DEVELOPMENT",
        "verdict": verdict,
        "pretruth_sha256": pre_sha,
        "panels": panels,
        "scale_aggregates": scale,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "PREDICTIVE_TREE_CUT_V1_GMN_SCALE_RESULT.json", result)
    print(json.dumps({"verdict": verdict, "result_sha256": result_sha, "pretruth_sha256": pre_sha, "scale_aggregates": scale, "gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
