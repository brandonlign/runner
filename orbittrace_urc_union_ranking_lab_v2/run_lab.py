#!/usr/bin/env python3
"""URC union-v2 development lab: robust nonlinear ranking on P19+P20 candidates.

Target-excluded GMN 2022/2023 development only. Exact P19 and P20 remain scientific no-gos;
this lab uses only their already-frozen pre-label candidate universes as development proposals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_unified_recurrent_catalogue_lab_v2 import run_lab as v2

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
CORPUS = "orbittrace-urc-union-ranking-lab-v2"
BLIND = (20.0, 55.0)

P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED_HARD = 226
EXPECTED_P19_SOFT = 1075
EXPECTED_P20_SOFT = 3203
EXPECTED_UNION = 4504

MODEL_SPECS = (
    *({"kind": "extra", "depth": depth, "leaf": leaf}
      for depth in (4, 8, 16, None) for leaf in (2, 5, 10)),
    *({"kind": "hgb", "leaves": leaves} for leaves in (7, 15, 31)),
)
JACCARD = (None, 0.10)

SOURCE_FEATURES = (
    "is_hard", "is_p19_soft", "is_p20_soft",
    "p20_cross_year_distance", "log_p20_min_anchor", "p20_min_bin_strength", "p20_min_quartet_score",
)
FEATURE_NAMES = tuple(v2.FEATURE_NAMES) + SOURCE_FEATURES


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p19-result-json", required=True, type=Path)
    p.add_argument("--p19-prelabel-json", required=True, type=Path)
    p.add_argument("--p20-result-json", required=True, type=Path)
    p.add_argument("--p20-prelabel-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_features(f: dict[str, Any], source: str) -> list[float]:
    return [
        1.0 if source == "hard" else 0.0,
        1.0 if source == "p19" else 0.0,
        1.0 if source == "p20" else 0.0,
        float(f.get("p20_cross_year_distance", 1.5)),
        math.log1p(max(int(f.get("p20_min_anchor_count", 0)), 0)),
        float(f.get("p20_min_bin_strength", 0.0)),
        float(f.get("p20_min_quartet_score", -2.0)),
    ]


def make_model(spec: dict[str, Any]):
    if spec["kind"] == "extra":
        return ExtraTreesClassifier(
            n_estimators=500,
            max_depth=spec["depth"],
            min_samples_leaf=int(spec["leaf"]),
            max_features=None,
            class_weight="balanced",
            random_state=20260809,
            n_jobs=-1,
        )
    return HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=250,
        max_leaf_nodes=int(spec["leaves"]),
        l2_regularization=1.0,
        random_state=20260809,
    )


def fit(model, x: np.ndarray, y: np.ndarray, weights: np.ndarray):
    model.fit(x, y, sample_weight=weights)
    return model


def probability(model, x: np.ndarray) -> np.ndarray:
    return np.asarray(model.predict_proba(x)[:, 1], dtype=float)


def strict_group(fid: str, truth: dict[str, Any]) -> str:
    label = truth.get("best_label")
    return "LBL/" + str(label) if label is not None else "NONE/" + fid


def fast_jaccard_suppress(
    order: list[str], sets: dict[str, set[str]], threshold: float | None
) -> tuple[list[str], int]:
    if threshold is None:
        return list(order), 0
    kept: list[str] = []
    event_to_kept: dict[str, set[str]] = defaultdict(set)
    suppressed = 0
    for fid in order:
        current = sets[fid]
        possible: set[str] = set()
        for eid in current:
            possible.update(event_to_kept.get(eid, ()))
        drop = False
        for old in possible:
            inter = len(current & sets[old])
            if inter and inter / len(current | sets[old]) >= threshold:
                drop = True
                break
        if drop:
            suppressed += 1
            continue
        kept.append(fid)
        for eid in current:
            event_to_kept[eid].add(fid)
    return kept, suppressed


def score_key(metrics: dict[str, Any]) -> tuple[float, ...]:
    return (
        float(metrics["recovered_at_100"]),
        float(metrics["recovered_at_50"]),
        float(metrics["recovered_at_25"]),
        float(metrics["top100_dominant_precision"]),
        float(metrics["mrr"]),
        -float(metrics["mean_qualified_candidates_per_recovered_label"]),
    )


def strict_pass(m: dict[str, Any], hard: dict[str, Any]) -> bool:
    return (
        int(m["recovered_at_100"]) >= 75
        and int(m["recovered_at_50"]) >= int(hard["recovered_at_50"])
        and float(m["top100_dominant_precision"]) >= float(hard["top100_dominant_precision"]) - 0.05
        and int(m["qualified_matches"]) >= 230
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha(args.p19_result_json) == P19_RESULT_SHA, "P19 result hash changed")
    require(sha(args.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 prelabel hash changed")
    require(sha(args.p20_result_json) == P20_RESULT_SHA, "P20 result hash changed")
    require(sha(args.p20_prelabel_json) == P20_PRELABEL_SHA, "P20 prelabel hash changed")
    r19 = json.loads(args.p19_result_json.read_text())
    r20 = json.loads(args.p20_result_json.read_text())
    require(r19["verdict"] == "FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT", "P19 identity changed")
    require(r20["verdict"] == "FAIL_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT", "P20 identity changed")

    a = json.loads(args.p19_prelabel_json.read_text())
    b = json.loads(args.p20_prelabel_json.read_text())
    hard = a["hard_families"]
    hard_order = [str(x) for x in a["hard_order"]]
    p19_soft = a["soft_families"]
    p20_soft = b["soft_families"]
    require(a["hard_families"] == b["hard_families"], "P19/P20 hard families differ")
    require(a["hard_order"] == b["hard_order"], "P19/P20 hard order differs")
    require((len(hard), len(p19_soft), len(p20_soft)) == (EXPECTED_HARD, EXPECTED_P19_SOFT, EXPECTED_P20_SOFT), "union counts changed")

    families = hard + p19_soft + p20_soft
    sources = ["hard"] * len(hard) + ["p19"] * len(p19_soft) + ["p20"] * len(p20_soft)
    family_ids = [str(f["family_id"]) for f in families]
    require(len(families) == EXPECTED_UNION and len(set(family_ids)) == EXPECTED_UNION, "union IDs not unique")
    eventsets = [tuple(sorted(map(str, f["event_ids"]))) for f in families]
    require(len(set(eventsets)) == EXPECTED_UNION, "exact event-set duplicates in union")

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
    scan_by_year, _cal, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "month universe changed")

    eligible = v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in families}
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    truths = {fid: v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in family_ids}
    y = np.asarray([int(truths[fid]["positive"]) for fid in family_ids], dtype=int)
    require(np.unique(y).size == 2, "quality target degenerate")

    lookup = v2.event_lookup(scan_by_year)
    x = np.asarray([
        v1.structural_features(f, hard_rank)
        + v2.cohesion_features(f, lookup, support, base)
        + source_features(f, source)
        for f, source in zip(families, sources)
    ], dtype=float)
    require(x.shape == (EXPECTED_UNION, len(FEATURE_NAMES)), "feature matrix shape changed")
    require(np.isfinite(x).all(), "nonfinite feature matrix")

    groups = [strict_group(fid, truths[fid]) for fid in family_ids]
    folds = np.asarray([v2.deterministic_fold(g) for g in groups], dtype=int)
    weights = v2.diversity_weights(family_ids, truths, y)
    sets = {fid: set(map(str, by_id[fid]["event_ids"])) for fid in family_ids}
    hard_metrics = v1.monotone_metrics(hard, hard_order, truths, eligible)
    union_order = hard_order + [str(f["family_id"]) for f in p19_soft] + [str(f["family_id"]) for f in p20_soft]
    union_metrics = v1.monotone_metrics(families, union_order, truths, eligible)

    rows = []
    best = None
    pass_count = 0
    model_pass = Counter()
    group_array = np.asarray(groups, dtype=object)
    for spec in MODEL_SPECS:
        oof = np.zeros(len(family_ids), dtype=float)
        fold_diag = []
        for fold_id in range(5):
            train = folds != fold_id
            test = folds == fold_id
            require(train.any() and test.any(), f"empty fold {fold_id}")
            require(np.unique(y[train]).size == 2, f"one-class train fold {fold_id}")
            model = fit(make_model(spec), x[train], y[train], weights[train])
            oof[test] = probability(model, x[test])
            train_groups = set(group_array[train])
            test_groups = set(group_array[test])
            require(not (train_groups & test_groups), f"group leakage fold {fold_id}")
            fold_diag.append({
                "fold": fold_id,
                "train": int(train.sum()),
                "test": int(test.sum()),
                "positive_test": int(y[test].sum()),
                "distinct_groups_test": len(test_groups),
            })
        raw = [fid for _s, _hr, fid in sorted(
            zip(oof, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
            key=lambda r: (-float(r[0]), int(r[1]), str(r[2])),
        )]
        for jac in JACCARD:
            order, suppressed = fast_jaccard_suppress(raw, sets, jac)
            m = v1.monotone_metrics(families, order, truths, eligible)
            passed = strict_pass(m, hard_metrics)
            pass_count += int(passed)
            if passed:
                model_pass[str(spec)] += 1
            row = {
                "model": spec,
                "event_jaccard": jac,
                "suppressed": suppressed,
                "output_family_count": len(order),
                "strict_pass": passed,
                "metrics": {k: v for k, v in m.items() if k != "first_rank_by_label"},
                "folds": fold_diag,
            }
            rows.append(row)
            key = score_key(m)
            if best is None or key > best["key"]:
                best = {"key": key, "spec": spec, "jac": jac, "order": order, "metrics": m, "suppressed": suppressed}

    require(best is not None, "no ranking result")
    final = fit(make_model(best["spec"]), x, y, weights)
    scores = probability(final, x)
    raw_final = [fid for _s, _hr, fid in sorted(
        zip(scores, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
        key=lambda r: (-float(r[0]), int(r[1]), str(r[2])),
    )]
    final_order, final_suppressed = fast_jaccard_suppress(raw_final, sets, best["jac"])
    final_metrics = v1.monotone_metrics(families, final_order, truths, eligible)

    importances = None
    if hasattr(final, "feature_importances_"):
        importances = sorted(
            ({"feature": name, "importance": float(value)} for name, value in zip(FEATURE_NAMES, final.feature_importances_)),
            key=lambda r: (-r["importance"], r["feature"]),
        )

    strict_fraction = pass_count / len(rows)
    robust = pass_count >= 6
    passed = strict_pass(best["metrics"], hard_metrics) and robust
    verdict = "PASS_URC_UNION_V2_ROBUST_RANKING_FEASIBILITY" if passed else "FAIL_URC_UNION_V2_ROBUST_RANKING_FEASIBILITY"

    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 target-excluded development-only P19+P20 union ranking lab",
        "candidate_universe": {
            "hard": len(hard), "p19_soft": len(p19_soft), "p20_soft": len(p20_soft), "union": len(families),
            "positive_candidates": int(y.sum()), "eligible_labels": len(eligible),
            "qualified_labels_anywhere": int(union_metrics["qualified_matches"]),
        },
        "hard_baseline": {k: v for k, v in hard_metrics.items() if k != "first_rank_by_label"},
        "append_union_diagnostic": {k: v for k, v in union_metrics.items() if k != "first_rank_by_label"},
        "best_cross_validated": {
            "model": best["spec"], "event_jaccard": best["jac"], "suppressed": best["suppressed"],
            "metrics": {k: v for k, v in best["metrics"].items() if k != "first_rank_by_label"},
            "order_sha256": hashlib.sha256("\n".join(best["order"]).encode()).hexdigest(),
        },
        "robustness": {
            "tested_variants": len(rows), "strict_pass_count": pass_count, "strict_pass_fraction": strict_fraction,
            "minimum_required_pass_count": 6,
            "model_pass_counts": dict(model_pass),
            "r100_range": [min(r["metrics"]["recovered_at_100"] for r in rows), max(r["metrics"]["recovered_at_100"] for r in rows)],
            "r50_range": [min(r["metrics"]["recovered_at_50"] for r in rows), max(r["metrics"]["recovered_at_50"] for r in rows)],
            "top100_precision_range": [min(r["metrics"]["top100_dominant_precision"] for r in rows), max(r["metrics"]["top100_dominant_precision"] for r in rows)],
        },
        "candidate_grid": rows,
        "full_development_fit_diagnostic": {
            "metrics": {k: v for k, v in final_metrics.items() if k != "first_rank_by_label"},
            "suppressed": final_suppressed,
            "feature_importances": importances,
        },
        "feature_names": list(FEATURE_NAMES),
        "integrity": {
            "p19_result_sha256": P19_RESULT_SHA, "p19_prelabel_sha256": P19_PRELABEL_SHA,
            "p20_result_sha256": P20_RESULT_SHA, "p20_prelabel_sha256": P20_PRELABEL_SHA,
            "candidate_generation_recomputed": False, "candidate_membership_changed": False,
            "same_label_fragments_grouped_across_cv": True,
            "sonotaco_2013_2014_access": False, "maarsy_scientific_access": False, "target_information_access": False,
        },
        "claim_boundary": "Development feasibility only. P19 and P20 remain no-gos; PASS supports a new integrated URC architecture only.",
    }
    (args.output / "urc_union_ranking_lab_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "URC_UNION_RANKING_LAB_V2.md").write_text(
        "# URC union ranking lab v2\n\n"
        f"- verdict: `{verdict}`\n"
        f"- hard recovery@100: `{hard_metrics['recovered_at_100']}`\n"
        f"- union qualified labels: `{union_metrics['qualified_matches']}`\n"
        f"- best OOF recovery@25/50/100/500: `{best['metrics']['recovered_at_25']}/{best['metrics']['recovered_at_50']}/{best['metrics']['recovered_at_100']}/{best['metrics']['recovered_at_500']}`\n"
        f"- best OOF top100 precision: `{best['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- strict variants passing: `{pass_count}/{len(rows)}`\n"
        f"- selected model: `{best['spec']}`; event Jaccard `{best['jac']}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "union_qualified": union_metrics["qualified_matches"],
        "best_r100": best["metrics"]["recovered_at_100"],
        "best_r50": best["metrics"]["recovered_at_50"],
        "best_r25": best["metrics"]["recovered_at_25"],
        "best_precision": best["metrics"]["top100_dominant_precision"],
        "strict_passes": pass_count,
        "variants": len(rows),
        "model": best["spec"],
        "jaccard": best["jac"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
