#!/usr/bin/env python3
"""Development-only event-level selector for P12 additions inside the fixed URC rank.

The 4,504-family hard+P19+P20 candidate universe and exact #839 rank never change.
Only already-frozen P12 additions to the 226 hard families are selectively admitted.
The selector is supervised on known GMN development showers, but application features contain
no shower identity and every shower used for evaluation receives strictly out-of-group scores.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
CORPUS = "orbittrace-urc-eventwise-p12-calibration-lab-v1"

EXPECTED_UNION_RESULT_SHA = "e932ad2507f6305a96c9d442a556593e470c966f1adfc2f4f2098adbc8f9dbcd"
EXPECTED_ORDER_SHA = "ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449"
EXPECTED_P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
EXPECTED_P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED_P12_RESULT_SHA = ""  # supplied by workflow through exact artifact file guard
EXPECTED_P12_DECISIONS_SHA = "6e11671cfb176302a58dd329d9fb09fc380a19e4ff9669bc444d5ce9624f00f5"
EXPECTED_COUNTS = (226, 1075, 3203, 4504)
EXPECTED_BASELINE = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "qualified_matches": 256,
    "top100_dominant_precision": 0.7645689180574315,
    "best_membership_macro_f1_all_eligible": 0.17953659309876194,
}
FEATURE_NAMES = (
    "responsibility",
    "responsibility_minus_membership_floor",
    "responsibility_minus_seed_floor",
    "log1p_odds",
    "drift_fraction_of_ceiling",
    "orbit_fraction_of_ceiling",
    "density_fraction_of_threshold",
    "membership_floor",
    "seed_floor",
    "log1p_core_event_count",
    "core_year_balance",
)
THRESHOLDS = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
MODEL_PARAMS = {
    "n_estimators": 512,
    "max_depth": 4,
    "min_samples_leaf": 20,
    "max_features": None,
    "random_state": 84601,
    "n_jobs": 1,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-result-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--p12-result-json", type=Path, required=True)
    p.add_argument("--p12-decisions-json-gz", type=Path, required=True)
    p.add_argument("--p12-expanded-json-gz", type=Path, required=True)
    p.add_argument("--union-ranker", type=Path, required=True)
    p.add_argument("--union-reference-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_fixed_union_order(union: types.ModuleType, args: argparse.Namespace) -> list[str]:
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
    rank_output = args.output / "exact_union_rerun"
    rank_output.mkdir(parents=True, exist_ok=True)
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
        "--output", str(rank_output),
    ]
    try:
        rc = union.main()
        require(rc in (None, 0), f"exact union ranker returned {rc}")
    finally:
        sys.argv = old_argv
        for obj, name, original in reversed(patched):
            setattr(obj, name, original)
    require("order" in captured, "failed to capture exact #839 selected order")
    require(order_sha(captured["order"]) == EXPECTED_ORDER_SHA, "captured #839 order changed")
    return captured["order"]


def year_balance(family: dict[str, Any]) -> float:
    counts = Counter(int(str(eid)[:4]) for eid in family["event_ids"])
    a, b = counts.get(2022, 0), counts.get(2023, 0)
    return float(min(a, b) / max(a, b, 1))


def decision_features(decision: dict[str, Any], family: dict[str, Any]) -> list[float]:
    responsibility = float(decision["responsibility"])
    membership_floor = float(decision["membership_floor"])
    seed_floor = float(decision["seed_floor"])
    obs_ceiling = max(float(decision["obs_ceiling"]), 1e-12)
    orb_ceiling = max(float(decision["orb_ceiling"]), 1e-12)
    density_score = max(float(decision["p11_density_score"]), 0.0)
    density_threshold = float(decision["p11_density_threshold"])
    if not math.isfinite(density_threshold) or density_threshold <= 0.0:
        density_fraction = 0.0
    else:
        density_fraction = min(density_score / density_threshold, 4.0)
    return [
        responsibility,
        responsibility - membership_floor,
        responsibility - seed_floor,
        math.log1p(max(float(decision["odds"]), 0.0)),
        min(float(decision["d_drift"]) / obs_ceiling, 4.0),
        min(float(decision["d_orb"]) / orb_ceiling, 4.0),
        density_fraction,
        membership_floor,
        seed_floor,
        math.log1p(max(len(family["event_ids"]), 1)),
        year_balance(family),
    ]


def annual_deltas(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        str(year): {
            name: float(current[str(year)][name]["mean_f1"] - baseline[str(year)][name]["mean_f1"])
            for name in ("4-9", "10-24", "25-49", "50-99", "100+", "all")
        }
        for year in YEARS
    }


def variant_pass(metrics: dict[str, Any], deltas: dict[str, Any], baseline_macro: float) -> bool:
    overall = [deltas[str(y)]["all"] for y in YEARS]
    sparse = [deltas[str(y)]["4-9"] for y in YEARS]
    moderate_large_material = any(
        min(deltas[str(y)][name] for y in YEARS) >= 0.02
        for name in ("25-49", "50-99", "100+")
    )
    return bool(
        metrics["recovered_at_100"] >= 75
        and metrics["recovered_at_50"] >= 40
        and metrics["qualified_matches"] >= 256
        and metrics["top100_dominant_precision"] >= 0.74
        and metrics["best_membership_macro_f1_all_eligible"] >= baseline_macro + 0.025
        and min(overall) >= 0.0
        and float(np.mean(overall)) >= 0.005
        and min(sparse) >= -0.002
        and float(np.mean(sparse)) >= 0.0
        and moderate_large_material
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for path, expected, name in (
        (args.union_reference_json, EXPECTED_UNION_RESULT_SHA, "#839 result"),
        (args.p19_result_json, EXPECTED_P19_RESULT_SHA, "P19 result"),
        (args.p19_prelabel_json, EXPECTED_P19_PRELABEL_SHA, "P19 prelabel"),
        (args.p20_result_json, EXPECTED_P20_RESULT_SHA, "P20 result"),
        (args.p20_prelabel_json, EXPECTED_P20_PRELABEL_SHA, "P20 prelabel"),
        (args.p12_decisions_json_gz, EXPECTED_P12_DECISIONS_SHA, "P12 decisions pretruth"),
    ):
        require(sha(path) == expected, f"{name} hash changed")

    p12_result = json.loads(args.p12_result_json.read_text())
    require(p12_result["verdict"] == "FAIL_DRIFT_CONDITIONED_TWO_VIEW_MEMBERSHIP_P12_NO_GO", "P12 verdict changed")
    require(p12_result["decisions_pretruth_sha256"] == EXPECTED_P12_DECISIONS_SHA, "P12 decision provenance changed")
    require(p12_result["baseline_v8"]["qualified_matches"] == 95, "P12 baseline qualification changed")
    require(p12_result["p12"]["qualified_matches"] == 91, "P12 no-go endpoint changed")

    reference = json.loads(args.union_reference_json.read_text())
    require(reference["verdict"] == "PASS_URC_UNION_RANKING_FEASIBILITY", "#839 verdict changed")
    require(reference["best_cross_validated"]["order_sha256"] == EXPECTED_ORDER_SHA, "#839 order changed")
    require(reference["best_cross_validated"]["lambda"] == 0.8, "#839 lambda changed")
    require(reference["best_cross_validated"]["scale"] == 1.0, "#839 scale changed")

    union = load_module(args.union_ranker, "exact_urc_union_ranker")
    fixed_order = capture_fixed_union_order(union, args)

    p19 = json.loads(args.p19_prelabel_json.read_text())
    p20 = json.loads(args.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    p19_soft = p19["soft_families"]
    p20_soft = p20["soft_families"]
    require(hard == p20["hard_families"], "hard families differ between P19/P20")
    families = hard + p19_soft + p20_soft
    require((len(hard), len(p19_soft), len(p20_soft), len(families)) == EXPECTED_COUNTS, "candidate counts changed")
    family_by_id = {str(f["family_id"]): f for f in families}
    hard_by_id = {str(f["family_id"]): f for f in hard}
    require(set(fixed_order) == set(family_by_id), "fixed order does not cover exact union")

    with gzip.open(args.p12_decisions_json_gz, "rt", encoding="utf-8") as fh:
        p12_decisions = json.load(fh)
    with gzip.open(args.p12_expanded_json_gz, "rt", encoding="utf-8") as fh:
        p12_expanded = json.load(fh)
    require(len(p12_expanded) == 226, "P12 expanded family count changed")
    require(set(str(f["family_id"]) for f in p12_expanded) == set(hard_by_id), "P12/hard IDs differ")
    assignments: dict[str, dict[str, Any]] = p12_decisions["assignments"]
    require(len(assignments) == 17238, "P12 assignment count changed")

    v1.mult.YEARS = YEARS
    v1.mult.MONTH_KEYS = MONTH_KEYS
    v1.mult.TOP_K = 100
    runtime = v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target exclusion changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _calibration, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "development months changed")

    eligible = v1.eligible_labels(hidden_labels)
    baseline_truth = {
        str(f["family_id"]): v1.family_truth(f, hidden_labels, eligible)
        for f in families
    }
    baseline_metrics = v1.monotone_metrics(families, fixed_order, baseline_truth, eligible)
    for key, expected in EXPECTED_BASELINE.items():
        value = baseline_metrics[key]
        if isinstance(expected, float):
            require(abs(float(value) - expected) < 1e-12, f"#839 baseline mismatch {key}: {value}")
        else:
            require(value == expected, f"#839 baseline mismatch {key}: {value}")
    baseline_annual = v1.annual_bins(families, hidden_labels)

    # Build supervised event examples only from already-qualified hard cores. The family/shower
    # label is used solely to define development correctness and CV groups; it is never a feature.
    X: list[list[float]] = []
    y: list[float] = []
    groups: list[str] = []
    keys: list[str] = []
    supervised_families: set[str] = set()
    for fid, family in hard_by_id.items():
        truth = baseline_truth[fid]
        if not truth["positive"] or truth["best_label"] is None:
            continue
        label = str(truth["best_label"])
        supervised_families.add(fid)
        core_ids = set(map(str, family["event_ids"]))
        for eid, decision in assignments.items():
            if str(decision["family_id"]) != fid or eid in core_ids:
                continue
            X.append(decision_features(decision, family))
            y.append(float(hidden_labels.get(eid, "SPORADIC") == label))
            groups.append(label)
            keys.append(eid)
    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    groups_arr = np.asarray(groups, dtype=object)
    require(X_arr.ndim == 2 and X_arr.shape[1] == len(FEATURE_NAMES), "event feature matrix invalid")
    require(np.all(np.isfinite(X_arr)), "non-finite event feature")
    unique_groups = sorted(set(groups))
    require(len(unique_groups) >= 50, f"insufficient supervised shower groups: {len(unique_groups)}")
    require(len(np.unique(y_arr)) == 2, "event correctness target is degenerate")

    oof: dict[str, float] = {}
    folds = GroupKFold(n_splits=5)
    fold_rows: list[dict[str, Any]] = []
    for fold, (train_idx, test_idx) in enumerate(folds.split(X_arr, y_arr, groups_arr)):
        model = ExtraTreesRegressor(**MODEL_PARAMS)
        model.fit(X_arr[train_idx], y_arr[train_idx])
        pred = np.clip(model.predict(X_arr[test_idx]), 0.0, 1.0)
        train_groups = set(groups_arr[train_idx].tolist())
        test_groups = set(groups_arr[test_idx].tolist())
        require(train_groups.isdisjoint(test_groups), "same-shower event leakage across CV fold")
        for idx, score in zip(test_idx.tolist(), pred.tolist()):
            require(keys[idx] not in oof, f"duplicate OOF event: {keys[idx]}")
            oof[keys[idx]] = float(score)
        fold_rows.append({
            "fold": fold,
            "train_examples": int(len(train_idx)),
            "test_examples": int(len(test_idx)),
            "train_groups": int(len(train_groups)),
            "test_groups": int(len(test_groups)),
            "test_positive_rate": float(np.mean(y_arr[test_idx])),
            "prediction_mean": float(np.mean(pred)),
        })
    require(len(oof) == len(keys), "OOF event predictions incomplete")

    all_model = ExtraTreesRegressor(**MODEL_PARAMS)
    all_model.fit(X_arr, y_arr)

    # Every accepted P12 assignment gets either an OOF score (if its family supplied supervised
    # examples) or an all-development score from a model that never trained on that family's labels.
    score_by_event: dict[str, float] = {}
    score_source: Counter[str] = Counter()
    for eid, decision in assignments.items():
        fid = str(decision["family_id"])
        family = hard_by_id[fid]
        if eid in set(map(str, family["event_ids"])):
            continue
        if eid in oof:
            score_by_event[eid] = float(oof[eid])
            score_source["strict_group_oof"] += 1
        else:
            score_by_event[eid] = float(np.clip(all_model.predict(np.asarray([decision_features(decision, family)]))[0], 0.0, 1.0))
            score_source["all_dev_model_nontraining_family"] += 1

    rows: list[dict[str, Any]] = []
    for threshold in THRESHOLDS:
        changed = copy.deepcopy(families)
        changed_by_id = {str(f["family_id"]): f for f in changed}
        additions = 0
        for eid, decision in assignments.items():
            if score_by_event.get(eid, -1.0) < threshold:
                continue
            fid = str(decision["family_id"])
            family = changed_by_id[fid]
            if eid not in family["event_ids"]:
                family["event_ids"].append(eid)
                additions += 1
        for family in changed[:len(hard)]:
            family["event_ids"] = sorted(set(map(str, family["event_ids"])))
            family["event_count"] = len(family["event_ids"])
        truths = {str(f["family_id"]): v1.family_truth(f, hidden_labels, eligible) for f in changed}
        metrics = v1.monotone_metrics(changed, fixed_order, truths, eligible)
        annual = v1.annual_bins(changed, hidden_labels)
        deltas = annual_deltas(annual, baseline_annual)
        passed = variant_pass(metrics, deltas, float(baseline_metrics["best_membership_macro_f1_all_eligible"]))
        rows.append({
            "threshold": threshold,
            "pass": bool(passed),
            "added_memberships": additions,
            "metrics": {k: v for k, v in metrics.items() if k != "first_rank_by_label"},
            "annual_mean_f1_delta": deltas,
        })

    passing = [row for row in rows if row["pass"]]
    adjacent: list[list[float]] = []
    pass_set = {float(row["threshold"]) for row in passing}
    for a, b in zip(THRESHOLDS, THRESHOLDS[1:]):
        if a in pass_set and b in pass_set:
            adjacent.append([a, b])
    robust = bool(adjacent)
    best = max(
        rows,
        key=lambda row: (
            float(row["metrics"]["best_membership_macro_f1_all_eligible"]),
            int(row["metrics"]["recovered_at_100"]),
            int(row["metrics"]["qualified_matches"]),
            float(row["metrics"]["top100_dominant_precision"]),
            -int(row["added_memberships"]),
            float(row["threshold"]),
        ),
    )
    if robust:
        robust_rows = [row for row in passing if any(float(row["threshold"]) in pair for pair in adjacent)]
        selected = max(
            robust_rows,
            key=lambda row: (
                float(row["metrics"]["best_membership_macro_f1_all_eligible"]),
                int(row["metrics"]["recovered_at_100"]),
                int(row["metrics"]["qualified_matches"]),
                float(row["metrics"]["top100_dominant_precision"]),
                -int(row["added_memberships"]),
                float(row["threshold"]),
            ),
        )
    else:
        selected = None

    verdict = (
        "PASS_URC_EVENTWISE_P12_CALIBRATION_FEASIBILITY"
        if robust
        else "FAIL_URC_EVENTWISE_P12_CALIBRATION_FEASIBILITY"
    )
    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 strict-shower-grouped eventwise filtering of exact P12 additions under fixed #839 URC rank",
        "fixed_ranking": {
            "source": "PR #839 strict-group ExtraTrees quality regression + diversity",
            "lambda": 0.8,
            "scale": 1.0,
            "order_sha256": EXPECTED_ORDER_SHA,
            "changed": False,
        },
        "event_model": {
            "type": "ExtraTreesRegressor on binary addition correctness",
            "params": MODEL_PARAMS,
            "features": list(FEATURE_NAMES),
            "training_family_rule": "only hard cores qualified on GMN; no shower identity enters features",
            "cv": "5-fold GroupKFold by best known shower; all additions of one shower held out together",
            "thresholds": list(THRESHOLDS),
            "supervised_examples": int(len(y_arr)),
            "supervised_positive_rate": float(np.mean(y_arr)),
            "supervised_shower_groups": len(unique_groups),
            "score_sources": dict(score_source),
            "folds": fold_rows,
        },
        "candidate_universe": {
            "hard": len(hard),
            "p19_soft": len(p19_soft),
            "p20_soft": len(p20_soft),
            "union": len(families),
        },
        "baseline": {
            "metrics": {k: v for k, v in baseline_metrics.items() if k != "first_rank_by_label"},
            "annual": baseline_annual,
        },
        "grid": rows,
        "adjacent_passing_threshold_pairs": adjacent,
        "best_diagnostic": best,
        "selected_if_pass": selected,
        "integrity": {
            "candidate_existence_changed": False,
            "candidate_rank_changed": False,
            "ranking_reselected": False,
            "p12_proposal_or_assignment_recomputed": False,
            "event_features_label_free_at_application": True,
            "development_training_uses_known_shower_correctness": True,
            "same_shower_grouped_oof_for_training_families": True,
            "original_members_never_removed": True,
            "new_members_recursive": False,
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": (
            "Development feasibility only. A PASS can promote only the frozen event selector around "
            "the exact #839 ranking after the independent URC generator stress is resolved; it cannot "
            "authorize SonotaCo, MAARSY, or target access by itself."
        ),
    }
    out_json = args.output / "urc_eventwise_p12_calibration_lab_v1.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    chosen = selected if selected is not None else best
    (args.output / "URC_EVENTWISE_P12_CALIBRATION_LAB_V1.md").write_text(
        "# URC eventwise P12 calibration lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- fixed #839 r100/r50/qualified: `{baseline_metrics['recovered_at_100']}/{baseline_metrics['recovered_at_50']}/{baseline_metrics['qualified_matches']}`\n"
        f"- supervised shower groups/examples: `{len(unique_groups)}/{len(y_arr)}`\n"
        f"- best diagnostic threshold: `{best['threshold']}`\n"
        f"- best diagnostic r100/r50/qualified: `{best['metrics']['recovered_at_100']}/{best['metrics']['recovered_at_50']}/{best['metrics']['qualified_matches']}`\n"
        f"- baseline/best macro F1: `{baseline_metrics['best_membership_macro_f1_all_eligible']:.6f}` / `{best['metrics']['best_membership_macro_f1_all_eligible']:.6f}`\n"
        f"- adjacent passing threshold pairs: `{adjacent}`\n"
        + (f"- selected threshold if PASS: `{chosen['threshold']}`\n" if selected is not None else "")
    )
    print(json.dumps({
        "verdict": verdict,
        "supervised_groups": len(unique_groups),
        "supervised_examples": len(y_arr),
        "positive_rate": float(np.mean(y_arr)),
        "baseline_r100": baseline_metrics["recovered_at_100"],
        "baseline_qualified": baseline_metrics["qualified_matches"],
        "baseline_macro_f1": baseline_metrics["best_membership_macro_f1_all_eligible"],
        "best_threshold": best["threshold"],
        "best_r100": best["metrics"]["recovered_at_100"],
        "best_qualified": best["metrics"]["qualified_matches"],
        "best_macro_f1": best["metrics"]["best_membership_macro_f1_all_eligible"],
        "adjacent_passing": adjacent,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
