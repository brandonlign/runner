#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

ROUTES = ("sugar", "hdbscan")
PANELS = (("sugar", 2013, 34), ("sugar", 2014, 46), ("hdbscan", 2013, 11), ("hdbscan", 2014, 9))
EXPECTED_PARENT_PRETRUTH_SHA = "c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef"
EXPECTED_PARENT_RESULT_SHA = "c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12"
EXPECTED_PARENT = {
    ("sugar", 2013): (0.3752906816276458, 23),
    ("sugar", 2014): (0.43773122295664196, 24),
    ("hdbscan", 2013): (0.1914598192215768, 11),
    ("hdbscan", 2014): (0.1685878550176112, 9),
}
EXPECTED_TRUTH_SHA = {
    ("sugar", 2013): "e3c075e8c4b5d4020007ba31cc4c49f1161593f21b83d63b521fc668a0f26cb3",
    ("sugar", 2014): "6497a7c61d257b46a0f4f082eb05cdd2e590a6a5559cb00cb8e216a1c659c273",
    ("hdbscan", 2013): "b77cdf076ff51d81b45a38e8d6aa573f0beb43124753da7ae97e5143eb3c8f56",
    ("hdbscan", 2014): "eeeb98e249ef6be9cd9a1979316ac72da81578d9bb911752cc94b3793182c6e8",
}
EXPECTED_ROUTE_COUNTS = {"sugar": 144, "hdbscan": 123}
BLIND = [20.0, 55.0]


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def dump(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def membership_signature(candidates: list[dict[str, Any]]) -> str:
    rows = []
    for c in candidates:
        rows.append({
            "family_id": str(c["family_id"]),
            "event_ids": list(map(str, c["event_ids"])),
            "member_count": int(c["member_count"]),
            "node_id": int(c["node_id"]),
        })
    rows.sort(key=lambda x: x["family_id"])
    return canonical_sha(rows)


def validate_parent(parent: dict[str, Any]) -> None:
    req(parent.get("scientific_role") == "PRETRUTH_FROZEN_RECURRENT_EOM_SONOTACO_V31_BENCHMARK_V1", "wrong parent role")
    req(parent.get("sonotaco_role") == "EXPOSED_DEVELOPMENT_ONLY", "wrong SonotaCo role")
    req(parent.get("truth_accessed") is False, "parent pretruth accessed truth")
    req(parent.get("target_information_access") is False, "parent accessed target information")
    req(parent.get("target_region_events_accessed") is False, "parent accessed protected events")
    req(parent.get("maarsy_scientific_access") is False, "parent accessed MAARSY")
    req(parent.get("dms_scientific_access") is False, "parent accessed DMS")
    req(parent.get("blind_exclusion") == BLIND, "parent blind exclusion changed")
    req(set(parent.get("routes", {})) == set(ROUTES), "parent route set changed")


def efficiency_score(candidate: dict[str, Any]) -> float:
    rec = float(candidate["recurrent_stability"])
    ordinary = float(candidate["ordinary_stability"])
    req(math.isfinite(rec) and math.isfinite(ordinary), "nonfinite parent stability")
    req(rec >= 0.0, "negative recurrent stability")
    req(ordinary >= 0.0, "negative ordinary stability")
    if ordinary == 0.0:
        req(rec == 0.0, "positive recurrence with zero ordinary stability")
        return 0.0
    if rec == 0.0:
        return 0.0
    out = (rec * rec) / ordinary
    req(math.isfinite(out) and out >= 0.0, "invalid recurrence-efficiency score")
    return out


def rerank_route(route: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    req(len(candidates) == EXPECTED_ROUTE_COUNTS[route], f"parent candidate count changed for {route}")
    req([int(c["rank"]) for c in candidates] == list(range(1, len(candidates) + 1)), f"parent ranks changed for {route}")
    req(len({str(c["family_id"]) for c in candidates}) == len(candidates), f"duplicate family IDs for {route}")

    parent_order = [str(c["family_id"]) for c in candidates]
    parent_membership_sha = membership_signature(candidates)
    successor = []
    for c in candidates:
        x = copy.deepcopy(c)
        x["parent_rank"] = int(c["rank"])
        x["recurrence_efficiency"] = efficiency_score(c)
        successor.append(x)

    successor.sort(key=lambda c: (
        -float(c["recurrence_efficiency"]),
        -float(c["recurrent_stability"]),
        -float(c["ordinary_stability"]),
        -int(c["member_count"]),
        str(c["family_id"]),
    ))
    for rank, c in enumerate(successor, 1):
        c["rank"] = rank

    successor_order = [str(c["family_id"]) for c in successor]
    req(set(successor_order) == set(parent_order), f"family universe changed for {route}")
    req(membership_signature(successor) == parent_membership_sha, f"membership changed for {route}")

    return {
        "candidate_count": len(successor),
        "parent_order_sha256": hashlib.sha256("\n".join(parent_order).encode()).hexdigest(),
        "successor_order_sha256": hashlib.sha256("\n".join(successor_order).encode()).hexdigest(),
        "membership_signature_sha256": parent_membership_sha,
        "order_changed": successor_order != parent_order,
        "candidates": successor,
    }


def run_pretruth(parent_path: Path, output: Path) -> int:
    req(sha(parent_path) == EXPECTED_PARENT_PRETRUTH_SHA, "parent pretruth SHA changed")
    parent = json.loads(parent_path.read_text())
    validate_parent(parent)

    routes = {route: rerank_route(route, parent["routes"][route]["candidates"]) for route in ROUTES}
    req(any(routes[r]["order_changed"] for r in ROUTES), "recurrence-efficiency order is identical to parent")

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1_PRETRUTH",
        "scientific_role": "PRETRUTH_EXPOSED_SONOTACO_DEVELOPMENT_RANK_ONLY",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "parent_method": "recurrent-EOM HDBSCAN v1",
        "parent_pretruth_sha256": EXPECTED_PARENT_PRETRUTH_SHA,
        "score": "recurrent_stability^2 / ordinary_stability; zero when recurrent_stability=0; zero ordinary allowed only with zero recurrent",
        "ranking": "recurrence_efficiency desc, recurrent_stability desc, ordinary_stability desc, member_count desc, family_id asc",
        "routes": routes,
        "blind_exclusion": BLIND,
        "truth_accessed": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "pristine_external_access": False,
    }
    out = output / "RECURRENCE_EFFICIENCY_RANK_V1_PRETRUTH.json"
    out_sha = dump(out, result)
    print(json.dumps({
        "pretruth_sha256": out_sha,
        "routes": {r: {k: v for k, v in routes[r].items() if k != "candidates"} for r in ROUTES},
    }, indent=2, sort_keys=True))
    return 0


def evaluate(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    truth_ids = set(truth)

    active = []
    for family in families:
        members = set(map(str, family["event_ids"])) & truth_ids
        if members:
            active.append((int(family["rank"]), str(family["family_id"]), members))
    active = sorted(active, key=lambda x: (x[0], x[1]))[:int(budget)]

    mat = np.zeros((len(labels), len(active)), dtype=np.float64)
    for i, label in enumerate(labels):
        actual = truth_sets[label]
        for j, (_rank, _fid, pred) in enumerate(active):
            overlap = len(actual & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(actual)
                mat[i, j] = 2.0 * precision * recall / (precision + recall)

    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=np.float64)
    cost[:len(labels), :len(active)] = -mat
    ri, cj = linear_sum_assignment(cost)
    vals = [float(mat[i, j]) if j < len(active) else 0.0 for i, j in zip(ri.tolist(), cj.tolist()) if i < len(labels)]
    return {
        "eligible_showers": len(labels),
        "macro_f1": float(np.mean(vals)) if vals else 0.0,
        "recovered_f1_gt_0_5": int(sum(x > 0.5 for x in vals)),
        "candidate_used": len(active),
    }


def run_evaluate(successor_path: Path, expected_successor_sha: str, parent_path: Path, parent_result_path: Path, truth_root: Path, output: Path) -> int:
    req(sha(successor_path) == expected_successor_sha, "successor pretruth changed after freeze")
    req(sha(parent_path) == EXPECTED_PARENT_PRETRUTH_SHA, "parent pretruth changed")
    req(sha(parent_result_path) == EXPECTED_PARENT_RESULT_SHA, "parent result changed")

    successor = json.loads(successor_path.read_text())
    parent = json.loads(parent_path.read_text())
    parent_result = json.loads(parent_result_path.read_text())
    validate_parent(parent)
    req(successor.get("schema") == "ORBITTRACE_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1_PRETRUTH", "wrong successor schema")
    req(successor.get("truth_accessed") is False, "successor pretruth accessed truth")
    req(successor.get("blind_exclusion") == BLIND, "successor blind changed")
    req(successor.get("target_information_access") is False and successor.get("target_region_events_accessed") is False, "successor target firewall failed")
    req(successor.get("pristine_external_access") is False, "successor accessed pristine external data")
    req(parent_result.get("verdict") == "PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1", "unexpected parent result verdict")

    panel_rows = []
    all_nonregress = True
    any_strict = False
    for route, year, budget in PANELS:
        truth_path = truth_root / f"truth_{route}_{year}.json"
        req(sha(truth_path) == EXPECTED_TRUTH_SHA[(route, year)], f"truth SHA changed for {route} {year}")
        truth = json.loads(truth_path.read_text())
        req(isinstance(truth, dict), f"truth payload malformed for {route} {year}")

        parent_eval = evaluate(parent["routes"][route]["candidates"], truth, budget)
        successor_eval = evaluate(successor["routes"][route]["candidates"], truth, budget)
        exp_f1, exp_rec = EXPECTED_PARENT[(route, year)]
        req(abs(parent_eval["macro_f1"] - exp_f1) <= 1e-15, f"parent macro-F1 mismatch for {route} {year}")
        req(parent_eval["recovered_f1_gt_0_5"] == exp_rec, f"parent recovery mismatch for {route} {year}")

        f1_nonregress = successor_eval["macro_f1"] >= parent_eval["macro_f1"]
        recovery_nonregress = successor_eval["recovered_f1_gt_0_5"] >= parent_eval["recovered_f1_gt_0_5"]
        strict = (successor_eval["macro_f1"] > parent_eval["macro_f1"]) or (successor_eval["recovered_f1_gt_0_5"] > parent_eval["recovered_f1_gt_0_5"])
        all_nonregress = all_nonregress and f1_nonregress and recovery_nonregress
        any_strict = any_strict or strict

        panel_rows.append({
            "route": route,
            "year": year,
            "budget": budget,
            "parent_macro_f1": parent_eval["macro_f1"],
            "successor_macro_f1": successor_eval["macro_f1"],
            "macro_f1_delta": successor_eval["macro_f1"] - parent_eval["macro_f1"],
            "parent_recovered": parent_eval["recovered_f1_gt_0_5"],
            "successor_recovered": successor_eval["recovered_f1_gt_0_5"],
            "recovered_delta": successor_eval["recovered_f1_gt_0_5"] - parent_eval["recovered_f1_gt_0_5"],
            "macro_f1_nonregression": f1_nonregress,
            "recovery_nonregression": recovery_nonregress,
            "strict_improvement": strict,
        })

    mechanism_active = any(bool(successor["routes"][r]["order_changed"]) for r in ROUTES)
    passed = mechanism_active and all_nonregress and any_strict
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1_RESULT",
        "scientific_role": "EXPOSED_SONOTACO_DEVELOPMENT_RANK_ONLY",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "parent_method": "recurrent-EOM HDBSCAN v1",
        "successor_method": "recurrent-EOM recurrence-efficiency rank v1",
        "successor_pretruth_sha256": expected_successor_sha,
        "parent_pretruth_sha256": EXPECTED_PARENT_PRETRUTH_SHA,
        "parent_result_sha256": EXPECTED_PARENT_RESULT_SHA,
        "mechanism_active": mechanism_active,
        "all_panel_macro_f1_and_recovery_nonregression": all_nonregress,
        "any_panel_strict_improvement": any_strict,
        "panels": panel_rows,
        "verdict": "PASS_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1" if passed else "FAIL_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1",
        "post_result_parameter_search": False,
        "blind_exclusion": BLIND,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "pristine_external_access": False,
    }
    out = output / "RECURRENCE_EFFICIENCY_RANK_V1_RESULT.json"
    out_sha = dump(out, result)
    print(json.dumps({"verdict": result["verdict"], "panels": panel_rows, "result_sha256": out_sha}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("pretruth")
    p.add_argument("--parent-pretruth", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)

    e = sub.add_parser("evaluate")
    e.add_argument("--successor-pretruth", type=Path, required=True)
    e.add_argument("--expected-successor-sha", required=True)
    e.add_argument("--parent-pretruth", type=Path, required=True)
    e.add_argument("--parent-result", type=Path, required=True)
    e.add_argument("--truth-root", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)

    a = ap.parse_args()
    if a.mode == "pretruth":
        return run_pretruth(a.parent_pretruth, a.output)
    return run_evaluate(a.successor_pretruth, a.expected_successor_sha, a.parent_pretruth, a.parent_result, a.truth_root, a.output)


if __name__ == "__main__":
    raise SystemExit(main())
