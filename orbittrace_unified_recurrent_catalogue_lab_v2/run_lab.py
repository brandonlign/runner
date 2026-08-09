#!/usr/bin/env python3
"""URC-v2 development lab: nonlinear diversity-aware ranking + geometric suppression.

Development-only on target-excluded GMN 2022/2023. Exact P19 remains a no-go.
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

YEARS = v1.YEARS
MONTH_KEYS = v1.MONTH_KEYS
CORPUS = "orbittrace-unified-recurrent-catalogue-lab-v2"
BLIND = v1.BLIND
EXPECTED_HARD = v1.EXPECTED_HARD
EXPECTED_SOFT = v1.EXPECTED_SOFT
EXPECTED_COMBINED = v1.EXPECTED_COMBINED
EXPECTED_P19_RESULT_SHA256 = v1.EXPECTED_P19_RESULT_SHA256
EXPECTED_P19_PRELABEL_SHA256 = v1.EXPECTED_P19_PRELABEL_SHA256
EXTRA_DEPTHS = (4, 8, 16, None)
EXTRA_LEAVES = (2, 5, 10)
HGB_LEAVES = (7, 15, 31)
GEO_SUPPRESSION = (None, 0.25, 0.50, 0.75, 1.00, 1.50)
EVENT_JACCARD = (None, 0.10)
BASE_FEATURE_NAMES = tuple(v1.FEATURE_NAMES)
COHESION_FEATURE_NAMES = (
    "member_count_min_year",
    "member_count_max_year",
    "member_count_year_balance",
    "member_distance_median",
    "member_distance_q90",
    "member_distance_max",
    "year_q90_distance_max",
)
FEATURE_NAMES = BASE_FEATURE_NAMES + COHESION_FEATURE_NAMES


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p19-result-json", required=True, type=Path)
    p.add_argument("--p19-prelabel-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def event_lookup(scan_by_year: dict[int, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        str(row["id"]): row
        for year in YEARS
        for row in scan_by_year[year]
    }


def cohesion_features(
    family: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
) -> list[float]:
    all_distances: list[float] = []
    per_year_q90: list[float] = []
    counts: list[int] = []
    centroids = family.get("centroids", {})
    for year in YEARS:
        ids = [str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year]
        counts.append(len(ids))
        c = centroids.get(str(year))
        distances: list[float] = []
        if c is not None:
            for eid in ids:
                row = lookup.get(eid)
                require(row is not None, f"member event absent from development scan: {eid}")
                d = float(support.centroid_distance(row, c, base))
                require(math.isfinite(d), f"nonfinite member distance for {eid}")
                distances.append(d)
                all_distances.append(d)
        per_year_q90.append(float(np.quantile(distances, 0.90)) if distances else 10.0)
    cmin, cmax = min(counts), max(counts)
    balance = float(cmin / max(cmax, 1))
    return [
        float(cmin),
        float(cmax),
        balance,
        float(np.median(all_distances)) if all_distances else 10.0,
        float(np.quantile(all_distances, 0.90)) if all_distances else 10.0,
        float(max(all_distances)) if all_distances else 10.0,
        float(max(per_year_q90)),
    ]


def family_pair_distance(a: dict[str, Any], b: dict[str, Any], support: Any, base: Any) -> float:
    ds = []
    for year in YEARS:
        ca = a.get("centroids", {}).get(str(year))
        cb = b.get("centroids", {}).get(str(year))
        if ca is None or cb is None:
            return math.inf
        ds.append(float(support.centroid_distance(ca, cb, base)))
    return float(max(ds))


def jaccard(a: set[str], b: set[str]) -> float:
    inter = len(a & b)
    return float(inter / len(a | b)) if inter else 0.0


def suppress(
    order: list[str],
    by_id: dict[str, dict[str, Any]],
    sets: dict[str, set[str]],
    support: Any,
    base: Any,
    geo_threshold: float | None,
    jac_threshold: float | None,
) -> tuple[list[str], dict[str, int]]:
    kept: list[str] = []
    event_suppressed = 0
    geo_suppressed = 0
    pair_cache: dict[tuple[str, str], float] = {}
    for fid in order:
        drop = False
        for old in kept:
            if jac_threshold is not None and jaccard(sets[fid], sets[old]) >= jac_threshold:
                event_suppressed += 1
                drop = True
                break
            if geo_threshold is not None:
                key = (fid, old) if fid < old else (old, fid)
                if key not in pair_cache:
                    pair_cache[key] = family_pair_distance(by_id[fid], by_id[old], support, base)
                if pair_cache[key] <= geo_threshold:
                    geo_suppressed += 1
                    drop = True
                    break
        if not drop:
            kept.append(fid)
    return kept, {
        "event_suppressed": event_suppressed,
        "geometric_suppressed": geo_suppressed,
        "kept": len(kept),
    }


def deterministic_fold(group: str, folds: int = 5) -> int:
    return int(hashlib.sha256(group.encode()).hexdigest()[:8], 16) % folds


def diversity_weights(family_ids: list[str], truths: dict[str, dict[str, Any]], y: np.ndarray) -> np.ndarray:
    per_label = Counter(
        str(truths[fid]["best_label"])
        for fid, yi in zip(family_ids, y)
        if yi == 1 and truths[fid]["best_label"] is not None
    )
    pos_n = max(int(y.sum()), 1)
    neg_n = max(int((1 - y).sum()), 1)
    weights = np.ones(len(family_ids), dtype=float)
    for i, (fid, yi) in enumerate(zip(family_ids, y)):
        if yi == 1:
            label = str(truths[fid]["best_label"])
            weights[i] = (len(family_ids) / (2.0 * pos_n)) / max(per_label[label], 1)
        else:
            weights[i] = len(family_ids) / (2.0 * neg_n)
    weights *= len(weights) / weights.sum()
    return weights


def model_specs() -> list[dict[str, Any]]:
    specs = []
    for depth in EXTRA_DEPTHS:
        for leaf in EXTRA_LEAVES:
            specs.append({"kind": "extra", "depth": depth, "leaf": leaf})
    for leaves in HGB_LEAVES:
        specs.append({"kind": "hgb", "leaves": leaves})
    return specs


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


def fit_model(model, x: np.ndarray, y: np.ndarray, weights: np.ndarray):
    model.fit(x, y, sample_weight=weights)
    return model


def probability(model, x: np.ndarray) -> np.ndarray:
    return np.asarray(model.predict_proba(x)[:, 1], dtype=float)


def score_key(metrics: dict[str, Any], suppression: dict[str, int]) -> tuple[float, ...]:
    return (
        float(metrics["recovered_at_100"]),
        float(metrics["recovered_at_50"]),
        float(metrics["recovered_at_25"]),
        float(metrics["top100_dominant_precision"]),
        float(metrics["mrr"]),
        -float(metrics["mean_qualified_candidates_per_recovered_label"]),
        -float(suppression["kept"]),
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(v1.sha256_file(args.p19_result_json) == EXPECTED_P19_RESULT_SHA256, "P19 result hash changed")
    require(v1.sha256_file(args.p19_prelabel_json) == EXPECTED_P19_PRELABEL_SHA256, "P19 prelabel hash changed")
    p19 = json.loads(args.p19_result_json.read_text())
    require(p19["verdict"] == "FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT", "P19 identity changed")
    payload = json.loads(args.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    soft = payload["soft_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    families = hard + soft
    require((len(hard), len(soft), len(families)) == (EXPECTED_HARD, EXPECTED_SOFT, EXPECTED_COMBINED), "family universe changed")

    v1.mult.YEARS = YEARS
    v1.mult.MONTH_KEYS = MONTH_KEYS
    v1.mult.TOP_K = 100
    runtime = v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _cal, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "months changed")

    eligible = v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in families}
    family_ids = [str(f["family_id"]) for f in families]
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    truths = {fid: v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in family_ids}
    y = np.asarray([int(truths[fid]["positive"]) for fid in family_ids], dtype=int)
    require(np.unique(y).size == 2, "quality target degenerate")

    lookup = event_lookup(scan_by_year)
    rows = []
    for f in families:
        rows.append(v1.structural_features(f, hard_rank) + cohesion_features(f, lookup, support, base))
    x = np.asarray(rows, dtype=float)
    require(x.shape == (EXPECTED_COMBINED, len(FEATURE_NAMES)), "feature matrix shape changed")
    require(np.isfinite(x).all(), "nonfinite feature matrix")

    groups = []
    for fid in family_ids:
        t = truths[fid]
        groups.append("POS/" + str(t["best_label"]) if t["positive"] else "NEG/" + fid)
    folds = np.asarray([deterministic_fold(g) for g in groups], dtype=int)
    weights = diversity_weights(family_ids, truths, y)
    sets = {fid: set(map(str, by_id[fid]["event_ids"])) for fid in family_ids}

    hard_metrics = v1.monotone_metrics(hard, hard_order, truths, eligible)

    candidates = []
    best = None
    for spec in model_specs():
        oof = np.zeros(len(family_ids), dtype=float)
        fold_diag = []
        for fold in range(5):
            train = folds != fold
            test = folds == fold
            require(train.any() and test.any(), f"empty fold {fold}")
            require(np.unique(y[train]).size == 2, f"training fold {fold} one-class")
            model = make_model(spec)
            fit_model(model, x[train], y[train], weights[train])
            oof[test] = probability(model, x[test])
            fold_diag.append({"fold": fold, "train": int(train.sum()), "test": int(test.sum()), "positive_test": int(y[test].sum())})
        raw_order = [fid for _s, _hr, fid in sorted(
            zip(oof, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
            key=lambda r: (-float(r[0]), int(r[1]), str(r[2])),
        )]
        for geo in GEO_SUPPRESSION:
            for jac in EVENT_JACCARD:
                order, supdiag = suppress(raw_order, by_id, sets, support, base, geo, jac)
                metrics = v1.monotone_metrics(families, order, truths, eligible)
                row = {
                    "model": spec,
                    "geo_suppression": geo,
                    "event_jaccard": jac,
                    "suppression": supdiag,
                    "metrics": {k: v for k, v in metrics.items() if k != "first_rank_by_label"},
                    "folds": fold_diag,
                }
                candidates.append(row)
                key = score_key(metrics, supdiag)
                if best is None or key > best["key"]:
                    best = {"key": key, "spec": spec, "geo": geo, "jac": jac, "order": order, "metrics": metrics, "suppression": supdiag, "oof": oof.copy()}
    require(best is not None, "no ranking candidate")

    final_model = make_model(best["spec"])
    fit_model(final_model, x, y, weights)
    scores = probability(final_model, x)
    raw_final = [fid for _s, _hr, fid in sorted(
        zip(scores, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
        key=lambda r: (-float(r[0]), int(r[1]), str(r[2])),
    )]
    final_order, final_sup = suppress(raw_final, by_id, sets, support, base, best["geo"], best["jac"])
    final_metrics = v1.monotone_metrics(families, final_order, truths, eligible)

    viable = (
        int(best["metrics"]["recovered_at_100"]) >= int(hard_metrics["recovered_at_100"]) + 5
        and int(best["metrics"]["recovered_at_50"]) >= int(hard_metrics["recovered_at_50"])
        and float(best["metrics"]["top100_dominant_precision"]) >= float(hard_metrics["top100_dominant_precision"]) - 0.05
        and int(best["metrics"]["qualified_matches"]) >= int(hard_metrics["qualified_matches"]) + 20
    )
    verdict = "PASS_URC_V2_NONLINEAR_GEOMETRIC_RANKING_FEASIBILITY" if viable else "FAIL_URC_V2_NONLINEAR_GEOMETRIC_RANKING_FEASIBILITY"

    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 target-excluded development-only ranking laboratory",
        "candidate_universe": {
            "hard": len(hard), "soft": len(soft), "combined": len(families),
            "positive_candidates": int(y.sum()), "eligible_labels": len(eligible),
        },
        "hard_baseline": {k: v for k, v in hard_metrics.items() if k != "first_rank_by_label"},
        "best_cross_validated": {
            "model": best["spec"],
            "geo_suppression": best["geo"],
            "event_jaccard": best["jac"],
            "suppression": best["suppression"],
            "metrics": {k: v for k, v in best["metrics"].items() if k != "first_rank_by_label"},
            "order_sha256": hashlib.sha256("\n".join(best["order"]).encode()).hexdigest(),
        },
        "full_development_fit_diagnostic": {
            "metrics": {k: v for k, v in final_metrics.items() if k != "first_rank_by_label"},
            "suppression": final_sup,
            "order_sha256": hashlib.sha256("\n".join(final_order).encode()).hexdigest(),
        },
        "candidate_grid": candidates,
        "feature_names": list(FEATURE_NAMES),
        "integrity": {
            "p19_result_sha256": EXPECTED_P19_RESULT_SHA256,
            "p19_prelabel_sha256": EXPECTED_P19_PRELABEL_SHA256,
            "candidate_generation_changed": False,
            "membership_changed": False,
            "development_truth_used_for_training": True,
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": "Development feasibility only; exact P19 remains no-go. PASS would justify a separately frozen URC architecture.",
    }
    (args.output / "unified_recurrent_catalogue_lab_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "UNIFIED_RECURRENT_CATALOGUE_LAB_V2.md").write_text(
        "# URC-v2 nonlinear/geometric ranking lab\n\n"
        f"- verdict: `{verdict}`\n"
        f"- hard recovery@100: `{hard_metrics['recovered_at_100']}`\n"
        f"- CV recovery@100: `{best['metrics']['recovered_at_100']}`\n"
        f"- CV recovery@50: `{best['metrics']['recovered_at_50']}`\n"
        f"- CV recovery@25: `{best['metrics']['recovered_at_25']}`\n"
        f"- CV qualified: `{best['metrics']['qualified_matches']}`\n"
        f"- CV top100 precision: `{best['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- model: `{best['spec']}`\n"
        f"- geometric suppression: `{best['geo']}`\n"
        f"- event Jaccard suppression: `{best['jac']}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "hard_recovery100": hard_metrics["recovered_at_100"],
        "cv_recovery100": best["metrics"]["recovered_at_100"],
        "cv_recovery50": best["metrics"]["recovered_at_50"],
        "cv_recovery25": best["metrics"]["recovered_at_25"],
        "cv_qualified": best["metrics"]["qualified_matches"],
        "cv_top100_precision": best["metrics"]["top100_dominant_precision"],
        "model": best["spec"],
        "geo": best["geo"],
        "jac": best["jac"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
