#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
COUNTS = {2022: 315024, 2023: 423658}
DIRECT_PRETRUTH_SHA = "f52371ba1a302d57a4050b380c2a744a3be560fee0916b28ba10efbdf20e8351"
DIRECT_RESULT_SHA = "20dd97323813f168da57383fe27dbd9685e68ddacd9b2ca1b9b31040c1cf1c4c"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"


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


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in (
        "protocol",
        "local-prelabel",
        "local-result",
        "direct-pretruth",
        "direct-result",
        "parent-evaluator",
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
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.direct_pretruth) == DIRECT_PRETRUTH_SHA, "sealed direct literature pretruth changed")
    req(sha(a.direct_result) == DIRECT_RESULT_SHA, "sealed direct literature result changed")
    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility changed")
    req(sha(a.v8_result_json) == V8_SHA, "frozen GMN support artifact changed")

    local_pre = json.loads(a.local_prelabel.read_text())
    local_res = json.loads(a.local_result.read_text())
    req(local_pre["schema"] == "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_PRELABEL", "wrong local-trunk prelabel schema")
    req(local_pre["scientific_role"] == "PRELABEL_TARGET_EXCLUDED_FIXED_RANK_MEMBERSHIP_REPRESENTATION", "wrong local-trunk prelabel role")
    req(local_pre["shower_truth_used"] is False, "local-trunk prelabel used shower truth")
    req(local_pre["target_information_access"] is False and local_pre["target_region_events_accessed"] is False, "local-trunk prelabel target firewall failed")
    req(local_pre["parent_ordered_membership_sha256"] == EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA, "local-trunk parent identity changed")
    req(local_res["schema"] == "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_BINDING_RESULT", "wrong local-trunk result schema")
    req(local_res["verdict"] == "PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1", "local-trunk did not pass binding gate")
    req(int(local_res["passed_gate_count"]) == 16 and int(local_res["total_gate_count"]) == 16, "local-trunk binding gate count not exact PASS")
    req(local_res["prelabel_sha256"] == sha(a.local_prelabel), "local-trunk result does not bind supplied prelabel")

    candidates = list(local_pre["successor_candidates"])
    req(len(candidates) == 2094, "local-trunk slot count changed")
    req([int(row["rank"]) for row in candidates] == list(range(1, 2095)), "local-trunk fixed rank order changed")
    req(all("family_id" in row and "event_ids" in row for row in candidates), "local-trunk candidate schema changed")

    parent_eval = load(a.parent_evaluator, "local_trunk_literature_parent_eval")
    req(getattr(parent_eval, "BLIND", None) == BLIND, "literature evaluator blind interval changed")
    pre = json.loads(a.direct_pretruth.read_text())
    direct = json.loads(a.direct_result.read_text())
    req(pre["scientific_role"] == "TARGET_EXCLUDED_GMN_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "direct pretruth role changed")
    req(pre["shower_truth_used"] is False, "direct comparator pretruth used truth")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "direct comparator firewall failed")
    req(direct["verdict"] == "PASS_RECURRENT_EOM_GMN_LITERATURE_4_OF_4", "historical direct literature result identity changed")

    parent_runner = load(a.parent_runner, "local_trunk_literature_parent")
    qmod = load(a.quality_source, "local_trunk_literature_quality")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-local-trunk-gmn-literature-fairness-v1-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    args = SimpleNamespace(fixed4_baseline_json=a.v8_result_json, candidate_payload=a.candidate_payload, baseline_payload=a.baseline_payload, scorer_parts=a.scorer_parts)
    for key, value in vars(a).items():
        setattr(args, key, value)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), "GMN years changed")
    req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN source list changed")

    annual: dict[int, set[str]] = {}
    for year in YEARS:
        rows = [parent_runner.normalize_event(row, year) for row in list(scan[year])]
        annual[year] = {str(event["id"]) for event in rows}
        req(len(annual[year]) == COUNTS[year], f"event count changed {year}")

    panel_keys = {"sugar2017": "sugar", "hdbscan2025": "hdbscan2025"}
    metrics: dict[str, Any] = {}
    gates: dict[str, Any] = {}
    passed = 0
    for comparator, pre_key in panel_keys.items():
        metrics[comparator] = {}
        for year in YEARS:
            literature = list(pre["panels"][str(year)][pre_key]["clusters"])
            K = len(literature)
            req(0 < K <= len(candidates), f"invalid matched capacity {comparator} {year}")
            successor_metrics = parent_eval.evaluate(candidates[:K], hidden, annual[year])
            comparator_metrics = parent_eval.evaluate(literature, hidden, annual[year])

            old = direct["metrics"][comparator][str(year)]
            for key in ("candidate_count", "eligible_showers", "macro_f1", "recovered_f1_gt_05"):
                if isinstance(old[key], float):
                    req(abs(float(comparator_metrics[key]) - float(old[key])) <= 1e-15, f"comparator reproduction {comparator} {year} {key}")
                else:
                    req(comparator_metrics[key] == old[key], f"comparator reproduction {comparator} {year} {key}")
            req(successor_metrics["candidate_count"] == comparator_metrics["candidate_count"] == K, f"capacity mismatch {comparator} {year}")

            ok = bool(
                successor_metrics["macro_f1"] > comparator_metrics["macro_f1"]
                and successor_metrics["recovered_f1_gt_05"] >= comparator_metrics["recovered_f1_gt_05"]
            )
            passed += int(ok)
            metrics[comparator][str(year)] = {
                "K": K,
                "local_trunk_matched_capacity": successor_metrics,
                "literature_complete_catalogue": comparator_metrics,
            }
            gates[f"{comparator}_{year}"] = {
                "passed": ok,
                "K": K,
                "local_trunk_macro_f1": successor_metrics["macro_f1"],
                "comparator_macro_f1": comparator_metrics["macro_f1"],
                "local_trunk_recovered_gt05": successor_metrics["recovered_f1_gt_05"],
                "comparator_recovered_gt05": comparator_metrics["recovered_f1_gt_05"],
            }

    verdict = "PASS_LOCAL_TRUNK_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4" if passed == 4 else "NO_LOCAL_TRUNK_GMN_MATCHED_CAPACITY_4_OF_4_SUPERIORITY"
    output = {
        "schema": "ORBITTRACE_LOCAL_TRUNK_GMN_LITERATURE_FAIRNESS_V1_RESULT",
        "verdict": verdict,
        "passed_pair_gates": passed,
        "total_pair_gates": 4,
        "protocol_sha256": sha(a.protocol),
        "local_trunk_prelabel_sha256": sha(a.local_prelabel),
        "local_trunk_binding_result_sha256": sha(a.local_result),
        "sealed_direct_pretruth_sha256": sha(a.direct_pretruth),
        "sealed_direct_result_sha256": sha(a.direct_result),
        "metrics": metrics,
        "pair_gates": gates,
        "fairness_rule": "literature complete catalogue versus identical-size prefix of immutable local-trunk fixed-rank catalogue",
        "sugar_claim_boundary": "deterministic published DBSCAN core only; full uncertainty-resampling pipeline not represented on GMN",
        "mrr_head_to_head_defined": False,
        "asfn_negative_result_remains_binding": True,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "amos_scientific_access": False,
        "asfn_efn_event_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n")
    compact = {
        comparator: {
            str(year): {
                "K": metrics[comparator][str(year)]["K"],
                "local_trunk_f1": metrics[comparator][str(year)]["local_trunk_matched_capacity"]["macro_f1"],
                "literature_f1": metrics[comparator][str(year)]["literature_complete_catalogue"]["macro_f1"],
                "local_trunk_recovered": metrics[comparator][str(year)]["local_trunk_matched_capacity"]["recovered_f1_gt_05"],
                "literature_recovered": metrics[comparator][str(year)]["literature_complete_catalogue"]["recovered_f1_gt_05"],
            }
            for year in YEARS
        }
        for comparator in panel_keys
    }
    print(json.dumps({"verdict": verdict, "passed_pair_gates": passed, "metrics": compact, "pair_gates": gates, "result_sha256": sha(a.output)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
