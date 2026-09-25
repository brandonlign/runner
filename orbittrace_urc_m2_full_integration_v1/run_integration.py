#!/usr/bin/env python3
"""One-shot full-URC integration evaluator for the #846 M2 membership challenger.

This source is frozen before #846's scientific result is known. It is dormant unless:
1) #846 passes its preregistered feasibility test, and
2) the already-frozen #850 five-salt fixed-policy stress also passes.

No model, threshold, cap, candidate, rank, radius, generator, or gate is selected here.
The exact #846 OOF-selected hard-family membership is reconstructed and inserted into the
immutable #839 hard+P19+P20 candidate order exactly once, then judged by #848.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import types
from pathlib import Path
from typing import Any, Callable

import numpy as np

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
EXPECTED_ORDER_SHA = "ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449"
EXPECTED_UNION_RESULT_SHA = "e932ad2507f6305a96c9d442a556593e470c966f1adfc2f4f2098adbc8f9dbcd"
EXPECTED_P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
EXPECTED_P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED_COUNTS = (226, 1075, 3203, 4504)

M0 = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "qualified_matches": 256,
    "mrr": 0.019037817654898162,
    "top100_dominant_precision": 0.7645689180574315,
    "best_membership_macro_f1_all_eligible": 0.17953659309876194,
}
M2_MIN_MACRO = M0["best_membership_macro_f1_all_eligible"] + 0.02
MODERATE_LARGE = ("25-49", "50-99", "100+")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--event-lab-source", required=True, type=Path)
    p.add_argument("--event-result", required=True, type=Path)
    p.add_argument("--event-stress-result", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p12-dir", required=True, type=Path)
    p.add_argument("--p19-result-json", required=True, type=Path)
    p.add_argument("--p19-prelabel-json", required=True, type=Path)
    p.add_argument("--p20-result-json", required=True, type=Path)
    p.add_argument("--p20-prelabel-json", required=True, type=Path)
    p.add_argument("--union-ranker", required=True, type=Path)
    p.add_argument("--union-reference-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_fixed_union_order(union: types.ModuleType, args: argparse.Namespace) -> list[str]:
    """Rerun exact #839 and capture only the already-frozen selected order."""
    captured: dict[str, list[str]] = {}
    patched: list[tuple[Any, str, Callable[..., Any]]] = []
    seen: set[int] = set()

    def patch(obj: Any) -> None:
        if id(obj) in seen:
            return
        seen.add(id(obj))
        original = getattr(obj, "monotone_metrics", None)
        if not callable(original):
            return

        def wrapped(*a: Any, __orig: Callable[..., Any] = original, **kw: Any) -> Any:
            order = kw.get("order")
            if order is None and len(a) >= 2:
                order = a[1]
            if isinstance(order, (list, tuple)) and order and all(isinstance(x, str) for x in order):
                candidate = list(order)
                if order_sha(candidate) == EXPECTED_ORDER_SHA:
                    captured["order"] = candidate
            return __orig(*a, **kw)

        setattr(obj, "monotone_metrics", wrapped)
        patched.append((obj, "monotone_metrics", original))

    patch(union)
    patch(v1)
    for value in union.__dict__.values():
        if isinstance(value, types.ModuleType):
            patch(value)

    old_argv = sys.argv[:]
    rerun_output = args.output / "exact_union_rerun"
    rerun_output.mkdir(parents=True, exist_ok=True)
    sys.argv = [
        str(args.union_ranker),
        "--support-source-parts", str(args.support_source_parts),
        "--candidate-payload", str(args.candidate_payload),
        "--baseline-payload", str(args.baseline_payload),
        "--scorer-parts", str(args.scorer_parts),
        "--v8-result-json", str(args.v8_result_json),
        "--p19-result-json", str(args.p19_result_json),
        "--p19-prelabel-json", str(args.p19_prelabel_json),
        "--p20-result-json", str(args.p20_result_json),
        "--p20-prelabel-json", str(args.p20_prelabel_json),
        "--output", str(rerun_output),
    ]
    try:
        rc = union.main()
        require(rc in (None, 0), f"exact #839 rerun returned {rc}")
    finally:
        sys.argv = old_argv
        for obj, name, original in reversed(patched):
            setattr(obj, name, original)

    require("order" in captured, "failed to capture exact #839 selected order")
    require(order_sha(captured["order"]) == EXPECTED_ORDER_SHA, "#839 order hash changed")
    return captured["order"]


def exact_union_metrics(hidden: dict[str, str], families: list[dict[str, Any]], order: list[str]) -> dict[str, Any]:
    eligible = v1.eligible_labels(hidden)
    truths = {
        str(f["family_id"]): v1.family_truth(f, hidden, eligible)
        for f in families
    }
    return v1.monotone_metrics(families, order, truths, eligible)


def annual_deltas(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, dict[str, float]]:
    names = ("4-9", "10-24", "25-49", "50-99", "100+", "all")
    return {
        str(year): {
            name: float(current[str(year)][name]["mean_f1"] - baseline[str(year)][name]["mean_f1"])
            for name in names
        }
        for year in YEARS
    }


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Downstream authorization: both preregistered M2 stages must pass before integration.
    event_result = json.loads(args.event_result.read_text())
    stress_result = json.loads(args.event_stress_result.read_text())
    require(event_result["verdict"] == "PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY", "#846 did not pass; M2 integration unauthorized")
    require(int(event_result["robustness"]["passing_grid_variants"]) >= 3, "#846 multi-variant gate changed")
    require(stress_result["verdict"] == "PASS_EVENT_LEVEL_P12_FIXED_GROUP_STRESS", "#850 fixed-policy stress did not pass")
    require(bool(stress_result["aggregate_gates"]["all_five_fixed_policy_panels_pass"]), "#850 did not pass all five panels")

    selected = event_result["selected"]["policy"]
    stress_policy = stress_result["selected_policy"]
    require(str(selected["model"]) == str(stress_policy["model"]), "stress model differs from #846")
    require(close(float(selected["threshold"]), float(stress_policy["threshold"])), "stress threshold differs from #846")
    require(str(selected["cap_ratio"]) == str(stress_policy["cap_ratio"]), "stress cap differs from #846")

    # Immutable candidate/ranking provenance.
    for path, expected, name in (
        (args.union_reference_json, EXPECTED_UNION_RESULT_SHA, "#839 reference"),
        (args.p19_result_json, EXPECTED_P19_RESULT_SHA, "P19 result"),
        (args.p19_prelabel_json, EXPECTED_P19_PRELABEL_SHA, "P19 prelabel"),
        (args.p20_result_json, EXPECTED_P20_RESULT_SHA, "P20 result"),
        (args.p20_prelabel_json, EXPECTED_P20_PRELABEL_SHA, "P20 prelabel"),
    ):
        require(sha256_file(path) == expected, f"{name} hash changed")
    union_reference = json.loads(args.union_reference_json.read_text())
    require(union_reference["verdict"] == "PASS_URC_UNION_RANKING_FEASIBILITY", "#839 verdict changed")
    require(union_reference["best_cross_validated"]["order_sha256"] == EXPECTED_ORDER_SHA, "#839 order reference changed")

    event = load_module(args.event_lab_source, "frozen_event_membership_lab")
    union = load_module(args.union_ranker, "frozen_urc_union_ranker")
    fixed_order = capture_fixed_union_order(union, args)

    # Reconstruct exact M0 union candidates from the already-frozen prelabel payloads.
    p19 = json.loads(args.p19_prelabel_json.read_text())
    p20 = json.loads(args.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    p19_soft = p19["soft_families"]
    p20_soft = p20["soft_families"]
    require(hard == p20["hard_families"], "P19/P20 hard-family payloads differ")
    m0_families = hard + p19_soft + p20_soft
    require((len(hard), len(p19_soft), len(p20_soft), len(m0_families)) == EXPECTED_COUNTS, "union candidate counts changed")
    require(set(fixed_order) == {str(f["family_id"]) for f in m0_families}, "#839 order/candidate universe mismatch")

    # Reconstruct the exact #846 OOF-selected hard-family membership. No fitting/search beyond
    # the single selected policy is permitted here.
    expanded = event.load_gz(args.p12_dir / "p12_expanded_families.json.gz")
    decisions = event.load_gz(args.p12_dir / "p12_decisions_pretruth.json.gz")
    assignments = decisions["assignments"]
    cores = [event.core_from_expanded(f) for f in expanded]
    require(len(cores) == 226 and len(assignments) == 17238, "P12 hard/assignment universe changed")
    core_by_id = {str(f["family_id"]): f for f in cores}
    require(set(core_by_id) == {str(f["family_id"]) for f in hard}, "P12/v8 hard-family IDs differ")
    for f in hard:
        fid = str(f["family_id"])
        require(set(map(str, f["event_ids"])) == set(map(str, core_by_id[fid]["event_ids"])), f"hard core event set changed for {fid}")

    runtime = event.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = event.YEARS
    support.MONTH_KEYS = event.MONTH_KEYS
    support.CORPUS = "orbittrace-urc-m2-full-integration-v1"
    support.RANKING_VARIANTS = ("persistence",)
    event.mult.YEARS = event.YEARS
    event.mult.MONTH_KEYS = event.MONTH_KEYS
    event.mult.TOP_K = 100
    require((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _calibration, hidden, sources = support.parse_catalogue(base)
    require([r["key"] for r in sources] == list(event.MONTH_KEYS), "GMN month universe changed")

    X, y, groups, eids, _meta = event.make_rows(hidden, cores, expanded, assignments)
    factories = dict(event.model_factories())
    model_name = str(selected["model"])
    require(model_name in factories, f"selected #846 model unavailable: {model_name}")
    pred, _fold_diag = event.oof_predictions(X, y, groups, factories[model_name])
    threshold = float(selected["threshold"])
    cap_raw = selected["cap_ratio"]
    cap = float("inf") if str(cap_raw) == "Infinity" else float(cap_raw)
    selected_hard, kept_additions = event.filter_membership(cores, expanded, eids, pred, threshold, cap)

    # Reproduce #846's selected hard-family endpoint before integrating it.
    hard_scored, _summary = event.mult.score_families(cores, scan_by_year, runtime, base)
    hard_order = [str(x) for x in event.mult.rank_scored(hard_scored, "multiplicity")]
    selected_historical = event.mult.evaluate_order(hidden, selected_hard, hard_order)
    selected_corrected = event.catalogue_metrics(hidden, selected_hard, hard_order)
    require(close(selected_historical["macro_f1"], event_result["selected"]["historical"]["macro_f1"]), "#846 selected macro F1 did not reproduce")
    require(int(selected_corrected["qualified_matches"]) == int(event_result["selected"]["corrected"]["qualified_matches"]), "#846 selected qualified count did not reproduce")
    require(int(selected_corrected["recovered_at_100"]) == int(event_result["selected"]["corrected"]["recovered_at_100"]), "#846 selected r100 did not reproduce")
    require(close(selected_corrected["top100_dominant_precision"], event_result["selected"]["corrected"]["top100_dominant_precision"]), "#846 selected precision did not reproduce")

    selected_hard_by_id = {str(f["family_id"]): f for f in selected_hard}
    require(set(selected_hard_by_id) == set(core_by_id), "selected hard-family IDs changed")
    m2_families = [selected_hard_by_id[str(f["family_id"])] for f in hard] + p19_soft + p20_soft
    require(len(m2_families) == 4504, "M2 integration changed candidate count")
    require({str(f["family_id"]) for f in m2_families} == set(fixed_order), "M2 integration changed candidate identities")

    m0_metrics = exact_union_metrics(hidden, m0_families, fixed_order)
    m2_metrics = exact_union_metrics(hidden, m2_families, fixed_order)
    m0_annual = event.annual_metrics(hidden, m0_families)
    m2_annual = event.annual_metrics(hidden, m2_families)
    deltas = annual_deltas(m2_annual, m0_annual)

    # Exact M0 reproduction is mandatory before M2 is judged.
    for key, expected in M0.items():
        require(close(m0_metrics[key], expected), f"M0 reference mismatch for {key}: {m0_metrics[key]} != {expected}")

    moderate_large_pass = {
        name: bool(
            deltas["2022"][name] > 0.0
            and deltas["2023"][name] > 0.0
            and (deltas["2022"][name] + deltas["2023"][name]) / 2.0 >= 0.015
        )
        for name in MODERATE_LARGE
    }
    sparse_mean = (deltas["2022"]["4-9"] + deltas["2023"]["4-9"]) / 2.0
    gates = {
        "recovery25_preserved": int(m2_metrics["recovered_at_25"]) >= 22,
        "recovery50_preserved": int(m2_metrics["recovered_at_50"]) >= 40,
        "recovery100_preserved": int(m2_metrics["recovered_at_100"]) >= 75,
        "recovery500_preserved": int(m2_metrics["recovered_at_500"]) >= 159,
        "qualified_256_preserved": int(m2_metrics["qualified_matches"]) >= 256,
        "mrr_preserved": float(m2_metrics["mrr"]) >= M0["mrr"],
        "top100_precision_at_least_074": float(m2_metrics["top100_dominant_precision"]) >= 0.74,
        "macro_f1_gain_at_least_002": float(m2_metrics["best_membership_macro_f1_all_eligible"]) >= M2_MIN_MACRO,
        "annual_all_nonregression_both_years": deltas["2022"]["all"] >= 0.0 and deltas["2023"]["all"] >= 0.0,
        "annual_sparse_floor_both_years": deltas["2022"]["4-9"] >= -0.002 and deltas["2023"]["4-9"] >= -0.002,
        "annual_sparse_mean_nonnegative": sparse_mean >= 0.0,
        "moderate_or_large_material_gain": any(moderate_large_pass.values()),
        "candidate_count_unchanged": len(m2_families) == len(m0_families) == 4504,
        "candidate_ids_unchanged": {str(f["family_id"]) for f in m2_families} == {str(f["family_id"]) for f in m0_families},
        "rank_order_unchanged": order_sha(fixed_order) == EXPECTED_ORDER_SHA,
        "event_policy_unchanged": True,
        "target_firewall_unchanged": True,
    }
    verdict = "PASS_M2_FULL_URC_PROMOTION_GATE" if all(gates.values()) else "FAIL_M2_FULL_URC_PROMOTION_GATE"

    out = {
        "verdict": verdict,
        "scope": "one-shot #848 full-URC integration of the single #846/#850 M2 policy",
        "selected_policy": {
            "model": model_name,
            "threshold": threshold,
            "cap_ratio": "Infinity" if not math.isfinite(cap) else cap,
            "kept_additions": int(kept_additions),
        },
        "m0": m0_metrics,
        "m2": m2_metrics,
        "annual_m0": m0_annual,
        "annual_m2": m2_annual,
        "annual_deltas": deltas,
        "moderate_large_pass": moderate_large_pass,
        "gates": gates,
        "integrity": {
            "candidate_universe": "exact #839 hard+P19+P20 4504-family union",
            "order_sha256": order_sha(fixed_order),
            "model_search": False,
            "threshold_search": False,
            "cap_search": False,
            "candidate_search": False,
            "ranking_search": False,
            "membership_source": "exact #846 selected OOF policy",
            "years": [2022, 2023],
            "blind_exclusion": [20.0, 55.0],
            "sonotaco_2013_2014_access": False,
            "maarsy_access": False,
            "target_information_access": False,
        },
        "claim_boundary": "This run can only decide whether M2 replaces M0 under the already-frozen #848 GMN promotion rule. It cannot alter the method after seeing the result.",
    }
    (args.output / "urc_m2_full_integration_v1.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    summary = [
        "# URC M2 full integration v1",
        "",
        f"- verdict: `{verdict}`",
        f"- policy: `{model_name}` / `{threshold}` / `{'Infinity' if not math.isfinite(cap) else cap}`",
        f"- kept P12 additions: `{kept_additions}`",
        f"- M0 r25/r50/r100/r500: `{m0_metrics['recovered_at_25']}/{m0_metrics['recovered_at_50']}/{m0_metrics['recovered_at_100']}/{m0_metrics['recovered_at_500']}`",
        f"- M2 r25/r50/r100/r500: `{m2_metrics['recovered_at_25']}/{m2_metrics['recovered_at_50']}/{m2_metrics['recovered_at_100']}/{m2_metrics['recovered_at_500']}`",
        f"- M0/M2 qualified: `{m0_metrics['qualified_matches']}` / `{m2_metrics['qualified_matches']}`",
        f"- M0/M2 macro F1: `{m0_metrics['best_membership_macro_f1_all_eligible']:.6f}` / `{m2_metrics['best_membership_macro_f1_all_eligible']:.6f}`",
        f"- M0/M2 top100 precision: `{m0_metrics['top100_dominant_precision']:.6f}` / `{m2_metrics['top100_dominant_precision']:.6f}`",
        f"- M0/M2 MRR: `{m0_metrics['mrr']:.9f}` / `{m2_metrics['mrr']:.9f}`",
        f"- annual deltas: `{deltas}`",
        f"- moderate/large material-gain flags: `{moderate_large_pass}`",
    ]
    (args.output / "URC_M2_FULL_INTEGRATION_V1.md").write_text("\n".join(summary) + "\n")
    print(verdict)
    print(json.dumps({"m0": m0_metrics, "m2": m2_metrics, "annual_deltas": deltas, "gates": gates}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
