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
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
BUCKETS = (0, 1, 2, 3)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SOURCE_DAG_PRELABEL_SHA256 = "65ead5f26026dbed74a098cc1df17d000c28705cd8fcd3af5134fd98151a0573"
SOURCE_DAG_RESULT_SHA256 = "b7b4a4355a488108f4107e86e98bfc872f67c176d63eac1e56772a78f0708721"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def zero_filled_mrr(metrics: dict[str, Any]) -> float:
    eligible = int(metrics["eligible_labels"])
    qualified = int(metrics["qualified_matches"])
    conditional = float(metrics["mrr"])
    req(eligible >= qualified >= 0, "invalid eligible/qualified counts")
    if eligible == 0:
        return 0.0
    if qualified == 0:
        req(conditional == 0.0, "nonzero conditional MRR with zero qualified")
        return 0.0
    return conditional * qualified / eligible


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    eligible = sum(int(x["eligible_labels"]) for x in vals)
    mass = sum(float(x["mrr"]) * int(x["qualified_matches"]) for x in vals)
    return {
        "qualified_total": sum(int(x["qualified_matches"]) for x in vals),
        "eligible_total": eligible,
        "conditional_mrr_mean": float(np.mean([float(x["mrr"]) for x in vals])),
        "zero_filled_mrr_mean": float(np.mean([zero_filled_mrr(x) for x in vals])),
        "zero_filled_mrr_pooled": mass / eligible if eligible else 0.0,
        "reciprocal_mass": mass,
        "precision_mean": float(np.mean([float(x["top100_dominant_precision"]) for x in vals])),
        "fragmentation_mean": float(np.mean([float(x["fragmentation_median_top500"]) for x in vals])),
        "recovered_at_25_total": sum(int(x["recovered_at_25"]) for x in vals),
        "recovered_at_50_total": sum(int(x["recovered_at_50"]) for x in vals),
        "recovered_at_100_total": sum(int(x["recovered_at_100"]) for x in vals),
        "recovered_at_500_total": sum(int(x["recovered_at_500"]) for x in vals),
    }


def event_hash_u64(event_id: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + event_id).encode()).digest()[:8], "big")


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "prelabel",
        "pretruth",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
        "output",
    ):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 result changed")
    pre_sha = sha256(a.prelabel)
    audit_sha = sha256(a.pretruth)
    pre = json.loads(a.prelabel.read_text())
    audit = json.loads(a.pretruth.read_text())

    req(pre["schema"] == "ORBITTRACE_DAG_CORROBORATION_MASS_RANK_V1_PRELABEL", "wrong prelabel schema")
    req(pre["scientific_role"] == "PRELABEL_DAG_CORROBORATION_MASS_RANK_V1", "wrong prelabel role")
    req(pre["source_dag_prelabel_sha256"] == SOURCE_DAG_PRELABEL_SHA256, "wrong DAG prelabel source")
    req(pre["source_dag_result_sha256"] == SOURCE_DAG_RESULT_SHA256, "wrong DAG result source")
    req(pre["source_dag_verdict"] == "SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1", "DAG source not supported")
    req(
        pre["configuration"]
        == {
            "candidate_membership": "exact_raw_support_resolved_topomodal",
            "recurrent_priority": "q=(N_R-rank+1)/N_R",
            "score": "sum_atoms((atom_size/topomodal_size)*recurrent_priority)",
            "final_order": "score_desc_native_topomodal_rank_asc_family_hash_asc",
            "equal_budget": "min(raw_topomodal_count,recurrent_count)",
        },
        "configuration changed",
    )
    for flag in (
        "shower_truth_used",
        "target_information_access",
        "target_region_events_accessed",
        "sonotaco_scientific_access",
        "asfn_efn_event_level_access",
        "amos_scientific_access",
        "maarsy_scientific_access",
        "dms_scientific_access",
        "post_result_parameter_search",
    ):
        req(pre.get(flag) is False, f"prelabel firewall {flag}")

    req(audit["schema"] == "ORBITTRACE_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH", "wrong pretruth schema")
    req(audit["scientific_role"] == "ZERO_LABEL_PRETRUTH_AUTHORIZATION", "wrong pretruth role")
    req(audit["verdict"] == "PASS_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH", "pretruth did not pass")
    req(audit["prelabel_sha256"] == pre_sha, "pretruth/prelabel mismatch")
    req(len(audit["gates"]) == 13 and all(bool(x) for x in audit["gates"].values()), "pretruth gates did not all pass")
    req(audit["shower_truth_used"] is False and audit["target_information_access"] is False and audit["target_region_events_accessed"] is False, "pretruth firewall")

    subset = {(int(x["denominator"]), int(x["bucket"])): x for x in pre["subsets"]}
    req(set(subset) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "prelabel panel set changed")
    for row in pre["subsets"]:
        succ = list(row["successor_candidates"])
        native = list(row["native_topomodal_candidates"])
        recurrent = list(row["recurrent_candidates"])
        nt, nr = len(native), len(recurrent)
        K = int(row["equal_budget_k"])
        req(K == min(nt, nr) and len(succ) == nt and K > 0, "equal budget/count changed")
        req([int(x["dag_corroboration_mass_rank"]) for x in succ] == list(range(1, nt + 1)), "successor rank continuity")
        req([int(x["rank"]) for x in native] == list(range(1, nt + 1)), "native rank continuity")
        req([int(x["rank"]) for x in recurrent] == list(range(1, nr + 1)), "recurrent rank continuity")
        req({str(x["family_hash"]) for x in succ} == {str(x["family_hash"]) for x in native}, "successor identity changed")
        native_members = {str(x["family_hash"]): tuple(sorted(str(z) for z in x["event_ids"])) for x in native}
        req(all(tuple(sorted(str(z) for z in x["event_ids"])) == native_members[str(x["family_hash"])] for x in succ), "successor membership changed")

    parent = load_module(a.parent_runner, "dag_corroboration_truth_parent")
    q = load_module(a.quality_source, "dag_corroboration_truth_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-dag-corroboration-mass-rank-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "truth firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(a)
    scan, _calibration, hidden, sources = support.parse_catalogue(baseline)
    req(isinstance(hidden, dict), "hidden truth unavailable")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "truth/source set changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(r, year) for r in list(scan[year]))
    req(len(events) == 738682, "target-excluded event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region entered truth runtime")
    ids = [str(e["id"]) for e in events]
    req(len(set(ids)) == len(ids), "event IDs nonunique")
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([event_hash_u64(eid) for eid in ids], dtype=np.uint64)

    panels: list[dict[str, Any]] = []
    for d in (128, 1024):
        for b in BUCKETS:
            frozen = subset[(d, b)]
            ix = np.flatnonzero((hashes % np.uint64(d)) == np.uint64(b))
            panel_ids = [ids[int(i)] for i in ix]
            panel_years = np.asarray(years[ix], dtype=np.int64)
            req(len(panel_ids) == int(frozen["events_total"]), f"panel count changed d={d} b={b}")
            req(universe_hash(panel_ids) == str(frozen["event_universe_sha256"]), f"panel universe changed d={d} b={b}")
            K = int(frozen["equal_budget_k"])
            succ = list(frozen["successor_candidates"])[:K]
            native = list(frozen["native_topomodal_candidates"])[:K]
            recurrent = list(frozen["recurrent_candidates"])[:K]
            req(len(succ) == len(native) == len(recurrent) == K, "equal budget drift")

            for year in YEARS:
                annual = {panel_ids[int(i)] for i in np.flatnonzero(panel_years == year)}
                sm = compact(parent.metrics(succ, hidden, annual))
                nm = compact(parent.metrics(native, hidden, annual))
                rm = compact(parent.metrics(recurrent, hidden, annual))
                req(int(sm["eligible_labels"]) == int(nm["eligible_labels"]) == int(rm["eligible_labels"]), "eligibility changed across controls")
                panels.append(
                    {
                        "denominator": d,
                        "bucket": b,
                        "year": year,
                        "equal_budget_k": K,
                        "successor_equal_budget": sm,
                        "native_topomodal_equal_budget": nm,
                        "recurrent_equal_budget": rm,
                        "successor_zero_filled_mrr": zero_filled_mrr(sm),
                        "native_topomodal_zero_filled_mrr": zero_filled_mrr(nm),
                        "recurrent_zero_filled_mrr": zero_filled_mrr(rm),
                        "qualified_nonlower_than_native": int(sm["qualified_matches"]) >= int(nm["qualified_matches"]),
                        "qualified_strict_win_over_native": int(sm["qualified_matches"]) > int(nm["qualified_matches"]),
                    }
                )

    scales: dict[str, Any] = {}
    for d in (128, 1024):
        ps = [p for p in panels if int(p["denominator"]) == d]
        req(len(ps) == 8, f"missing annual panels d={d}")
        sa = aggregate(ps, "successor_equal_budget")
        na = aggregate(ps, "native_topomodal_equal_budget")
        ra = aggregate(ps, "recurrent_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower_than_native"]) for p in ps)
        strict = sum(bool(p["qualified_strict_win_over_native"]) for p in ps)
        scales[str(d)] = {
            "panel_count": 8,
            "successor_equal_budget": sa,
            "native_topomodal_equal_budget": na,
            "recurrent_equal_budget": ra,
            "qualified_nonlower_than_native_panels": nonlower,
            "qualified_strict_win_over_native_panels": strict,
            "qualified_loss_vs_native_panels": 8 - nonlower,
        }

    fine = scales["1024"]
    coarse = scales["128"]
    fs, fn, fr = fine["successor_equal_budget"], fine["native_topomodal_equal_budget"], fine["recurrent_equal_budget"]
    cs, cn, cr = coarse["successor_equal_budget"], coarse["native_topomodal_equal_budget"], coarse["recurrent_equal_budget"]

    gates = {
        "fine_qualified_total_not_lower_than_native": fs["qualified_total"] >= fn["qualified_total"],
        "fine_qualified_nonlower_than_native_at_least_6_of_8": fine["qualified_nonlower_than_native_panels"] >= 6,
        "fine_zero_filled_mrr_strictly_greater_than_native": fs["zero_filled_mrr_mean"] > fn["zero_filled_mrr_mean"],
        "fine_zero_filled_mrr_not_lower_than_recurrent": fs["zero_filled_mrr_mean"] >= fr["zero_filled_mrr_mean"],
        "fine_precision_not_lower_than_native": fs["precision_mean"] >= fn["precision_mean"],
        "fine_fragmentation_not_higher_than_native": fs["fragmentation_mean"] <= fn["fragmentation_mean"],
        "coarse_qualified_total_not_lower_than_native": cs["qualified_total"] >= cn["qualified_total"],
        "coarse_qualified_nonlower_than_native_at_least_6_of_8": coarse["qualified_nonlower_than_native_panels"] >= 6,
        "coarse_zero_filled_mrr_strictly_greater_than_native": cs["zero_filled_mrr_mean"] > cn["zero_filled_mrr_mean"],
        "coarse_zero_filled_mrr_not_lower_than_recurrent": cs["zero_filled_mrr_mean"] >= cr["zero_filled_mrr_mean"],
        "coarse_recovered_at_25_not_lower_than_native": cs["recovered_at_25_total"] >= cn["recovered_at_25_total"],
        "coarse_precision_and_fragmentation_not_worse_than_native": cs["precision_mean"] >= cn["precision_mean"] and cs["fragmentation_mean"] <= cn["fragmentation_mean"],
    }
    verdict = "PASS_DAG_CORROBORATION_MASS_RANK_V1" if all(gates.values()) else "FAIL_DAG_CORROBORATION_MASS_RANK_V1"

    out = {
        "schema": "ORBITTRACE_DAG_CORROBORATION_MASS_RANK_V1_TRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RANKING_DEVELOPMENT",
        "verdict": verdict,
        "source_dag_run_id": 32185851992,
        "source_dag_artifact_id": 9342489614,
        "source_dag_prelabel_sha256": SOURCE_DAG_PRELABEL_SHA256,
        "source_dag_result_sha256": SOURCE_DAG_RESULT_SHA256,
        "prelabel_sha256": pre_sha,
        "pretruth_sha256": audit_sha,
        "ranking_metric_gate": "zero_filled_eligible_query_mrr_panel_mean",
        "historical_conditional_mrr_role": "diagnostic_only",
        "panels": panels,
        "scale_aggregates": scales,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
        "post_result_rescue": False,
    }
    out_path = a.output / "DAG_CORROBORATION_MASS_RANK_V1_TRUTH.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "TRUTH_SHA256.txt").write_text(sha256(out_path) + "\n")
    print(json.dumps({"verdict": verdict, "scales": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
