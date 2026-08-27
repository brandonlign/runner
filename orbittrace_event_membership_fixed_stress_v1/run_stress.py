#!/usr/bin/env python3
"""Fixed-setting repeat-fold stress for a passing #846 event-level P12 selector.

This source is frozen before the #846 scientific result is known. It never searches a model,
threshold, or cap. It reads the single policy selected by #846's already-frozen selector and
reruns only that policy under five new whole-shower fold assignments.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

SALTS = (
    "URC-EVENT-STRESS-A",
    "URC-EVENT-STRESS-B",
    "URC-EVENT-STRESS-C",
    "URC-EVENT-STRESS-D",
    "URC-EVENT-STRESS-E",
)
EXPECTED_SOURCE_COMMIT = "99fdc0d21e91b68496adeddc21b2837093473ed9"
EXPECTED_V8_MACRO = 0.1736657194465356


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--lab-source", required=True, type=Path)
    p.add_argument("--lab-result", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p12-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("frozen_event_membership_lab", path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def salted_group_folds(groups: list[str], salt: str, nfold: int = 5) -> np.ndarray:
    counts = Counter(groups)
    fold_load = [0] * nfold
    assignment: dict[str, int] = {}
    ordered = sorted(
        counts,
        key=lambda g: (
            -counts[g],
            hashlib.sha256(f"{salt}|{g}".encode()).hexdigest(),
        ),
    )
    for group in ordered:
        fold = min(range(nfold), key=lambda i: (fold_load[i], i))
        assignment[group] = fold
        fold_load[fold] += counts[group]
    return np.asarray([assignment[g] for g in groups], dtype=int)


def fixed_oof(module: Any, X: np.ndarray, y: np.ndarray, groups: list[str], factory: Any, salt: str) -> tuple[np.ndarray, list[dict[str, Any]]]:
    folds = salted_group_folds(groups, salt)
    weights = module.sample_weights(y, groups)
    pred = np.zeros(len(y), dtype=float)
    diag: list[dict[str, Any]] = []
    group_array = np.asarray(groups, dtype=object)
    for fold in range(5):
        train = np.where(folds != fold)[0]
        test = np.where(folds == fold)[0]
        train_groups = set(group_array[train].tolist())
        test_groups = set(group_array[test].tolist())
        require(train_groups.isdisjoint(test_groups), f"same-shower leakage in {salt} fold {fold}")
        model = factory()
        model.fit(X[train], y[train], sample_weight=weights[train])
        pred[test] = model.predict_proba(X[test])[:, 1]
        diag.append({
            "fold": fold,
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "train_groups": int(len(train_groups)),
            "test_groups": int(len(test_groups)),
            "test_positive": int(y[test].sum()),
        })
    require(np.all(np.isfinite(pred)), f"nonfinite predictions for {salt}")
    return pred, diag


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = json.loads(args.lab_result.read_text())
    require(result["verdict"] == "PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY", "#846 did not scientifically pass; stress is unauthorized")
    require(int(result["robustness"]["passing_grid_variants"]) >= 3, "#846 passing-grid requirement changed")
    policy = result["selected"]["policy"]
    selected_model = str(policy["model"])
    threshold = float(policy["threshold"])
    cap_raw = policy["cap_ratio"]
    cap = float("inf") if str(cap_raw) == "Infinity" else float(cap_raw)

    module = load_module(args.lab_source)
    factories = dict(module.model_factories())
    require(selected_model in factories, f"unknown selected #846 model {selected_model}")
    factory = factories[selected_model]

    expanded = module.load_gz(args.p12_dir / "p12_expanded_families.json.gz")
    decisions = module.load_gz(args.p12_dir / "p12_decisions_pretruth.json.gz")
    require(len(expanded) == module.EXPECTED_FAMILIES, "P12 family count changed")
    assignments = decisions["assignments"]
    require(len(assignments) == 17238, "P12 assignment count changed")
    cores = [module.core_from_expanded(f) for f in expanded]

    runtime = module.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = module.YEARS
    support.MONTH_KEYS = module.MONTH_KEYS
    support.CORPUS = "orbittrace-event-membership-fixed-stress-v1"
    support.RANKING_VARIANTS = ("persistence",)
    module.mult.YEARS = module.YEARS
    module.mult.MONTH_KEYS = module.MONTH_KEYS
    module.mult.TOP_K = 100
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _calibration, hidden, sources = support.parse_catalogue(base)
    require([r["key"] for r in sources] == list(module.MONTH_KEYS), "development month universe changed")

    hard_scored, _summary = module.mult.score_families(cores, scan_by_year, runtime, base)
    order = [str(x) for x in module.mult.rank_scored(hard_scored, "multiplicity")]
    hist_core = module.mult.evaluate_order(hidden, cores, order)
    require(abs(float(hist_core["macro_f1"]) - EXPECTED_V8_MACRO) < 1e-12, "v8 reproduction failed")
    corrected_core = module.catalogue_metrics(hidden, cores, order)
    annual_core = module.annual_metrics(hidden, cores)

    X, y, groups, eids, _meta = module.make_rows(hidden, cores, expanded, assignments)
    require(len(X) == 17238 and len(y) == 17238 and len(groups) == 17238 and len(eids) == 17238, "event training universe changed")
    require(len(set(groups)) >= 50, "strict-group universe unexpectedly small")

    panels: list[dict[str, Any]] = []
    for salt in SALTS:
        pred, fold_diag = fixed_oof(module, X, y, groups, factory, salt)
        families, kept = module.filter_membership(cores, expanded, eids, pred, threshold, cap)
        historical = module.mult.evaluate_order(hidden, families, order)
        corrected = module.catalogue_metrics(hidden, families, order)
        annual = module.annual_metrics(hidden, families)
        gains = {
            str(year): float(annual[str(year)]["all"]["mean_f1"] - annual_core[str(year)]["all"]["mean_f1"])
            for year in module.YEARS
        }
        gates = {
            "qualified_at_least_95": int(corrected["qualified_matches"]) >= 95,
            "recovery100_at_least_59": int(corrected["recovered_at_100"]) >= 59,
            "top100_precision_at_least_0668": float(corrected["top100_dominant_precision"]) >= 0.668,
            "historical_macro_at_least_030": float(historical["macro_f1"]) >= 0.30,
            "annual_all_gain_2022_at_least_0015": gains["2022"] >= 0.015,
            "annual_all_gain_2023_at_least_0015": gains["2023"] >= 0.015,
        }
        panels.append({
            "salt": salt,
            "pass": bool(all(gates.values())),
            "gates": gates,
            "kept_additions": int(kept),
            "historical_macro_f1": float(historical["macro_f1"]),
            "historical_qualified": int(historical["qualified_matches"]),
            "corrected": {k: v for k, v in corrected.items() if k != "per_label"},
            "annual_all_f1_gain": gains,
            "folds": fold_diag,
        })

    aggregate_gates = {
        "all_five_fixed_policy_panels_pass": all(row["pass"] for row in panels),
        "selected_model_unchanged": True,
        "selected_threshold_unchanged": True,
        "selected_cap_unchanged": True,
        "no_policy_reselection": True,
    }
    verdict = "PASS_EVENT_LEVEL_P12_FIXED_GROUP_STRESS" if all(aggregate_gates.values()) else "FAIL_EVENT_LEVEL_P12_FIXED_GROUP_STRESS"
    output = {
        "verdict": verdict,
        "scope": "five-salt whole-shower repeat-fold stress of the single policy selected by #846",
        "selected_policy": {
            "model": selected_model,
            "threshold": threshold,
            "cap_ratio": "Infinity" if not math.isfinite(cap) else cap,
        },
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "panels": panels,
        "aggregate_gates": aggregate_gates,
        "integrity": {
            "model_search": False,
            "threshold_search": False,
            "cap_search": False,
            "same_shower_grouped": True,
            "years": [2022, 2023],
            "blind_exclusion": [20.0, 55.0],
            "sonotaco_2013_2014_access": False,
            "maarsy_access": False,
            "target_information_access": False,
        },
    }
    (args.output / "event_membership_fixed_stress_v1.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Event-level P12 fixed-policy repeat-fold stress\n",
        f"- verdict: `{verdict}`",
        f"- fixed policy: `{selected_model}` / `{threshold}` / `{'Infinity' if not math.isfinite(cap) else cap}`",
    ]
    for row in panels:
        c = row["corrected"]
        lines.append(
            f"- {row['salt']}: pass `{row['pass']}`, macro `{row['historical_macro_f1']:.6f}`, "
            f"qualified `{c['qualified_matches']}`, r100 `{c['recovered_at_100']}`, "
            f"precision `{c['top100_dominant_precision']:.6f}`, annual gains `{row['annual_all_f1_gain']}`"
        )
    (args.output / "EVENT_MEMBERSHIP_FIXED_STRESS_V1.md").write_text("\n".join(lines) + "\n")
    print(verdict)
    for row in panels:
        print(row["salt"], row["pass"], row["historical_macro_f1"], row["corrected"]["qualified_matches"], row["corrected"]["recovered_at_100"], row["annual_all_f1_gain"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
