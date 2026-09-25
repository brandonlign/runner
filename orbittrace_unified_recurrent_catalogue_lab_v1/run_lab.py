#!/usr/bin/env python3
"""Development-only lab for a unified recurrent meteor-family catalogue.

This does not modify or rescue frozen P19. It uses P19's already-generated target-excluded
hard+soft candidate universe as a development diagnostic to ask whether unified ranking and
candidate suppression can convert the demonstrated sparse-family signal into a useful catalogue.
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
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-unified-recurrent-catalogue-lab-v1"
BLIND = (20.0, 55.0)
TOPS = (25, 50, 100, 500)
EXPECTED_P19_RESULT_SHA256 = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA256 = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_HARD = 226
EXPECTED_SOFT = 1075
EXPECTED_COMBINED = 1301
C_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
JACCARD_GRID = (None, 0.75, 0.50, 0.25, 0.10)
SIZE_BINS = (
    ("4-9", 4, 9),
    ("10-24", 10, 24),
    ("25-49", 25, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)
FEATURE_NAMES = (
    "is_soft",
    "log_event_count",
    "log_anchor_count",
    "log_quartet_count",
    "log_component_count",
    "best_score",
    "year_strength_min",
    "year_strength_max",
    "year_strength_balance",
    "member_year_balance",
    "centroid_crossyear_distance",
    "hard_rank_percentile",
    "soft_support_fraction",
    "soft_trigger_distance",
)


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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def circular_diff_deg(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def family_centroid_distance(family: dict[str, Any]) -> float:
    c = family.get("centroids", {})
    a = c.get("2022")
    b = c.get("2023")
    if not a or not b:
        return 10.0
    # Fixed physical scales inherited from the detector's local-window/probe geometry.
    d_sol = circular_diff_deg(a["sol"], b["sol"]) / 10.0
    d_sun = circular_diff_deg(a["sun_lon"], b["sun_lon"]) / 4.0
    d_lat = abs(float(a["ecl_lat"]) - float(b["ecl_lat"])) / 4.0
    va = max(abs(float(a["vg"])), 1e-6)
    vb = max(abs(float(b["vg"])), 1e-6)
    d_v = abs(math.log(va / vb)) / math.log(1.10)
    return float(math.sqrt(d_sol * d_sol + d_sun * d_sun + d_lat * d_lat + d_v * d_v))


def member_year_balance(family: dict[str, Any]) -> float:
    counts = Counter(int(str(eid)[:4]) for eid in family["event_ids"])
    a = int(counts.get(2022, 0))
    b = int(counts.get(2023, 0))
    return float(min(a, b) / max(a, b, 1))


def structural_features(family: dict[str, Any], hard_rank: dict[str, int]) -> list[float]:
    fid = str(family["family_id"])
    is_soft = 1.0 if family.get("family_type") else 0.0
    strengths = [float(family.get("year_strengths", {}).get(str(y), 0.0)) for y in YEARS]
    smin, smax = min(strengths), max(strengths)
    sbalance = float((smin + 1e-6) / (smax + 1e-6)) if smax >= 0.0 else 0.0
    event_count = max(int(family.get("event_count", len(family.get("event_ids", [])))), 1)
    support_count = int(family.get("soft_support_count", 0))
    trigger = float(family.get("soft_trigger_max_seed_distance", 1.5))
    h_rank = int(hard_rank.get(fid, EXPECTED_HARD + 1))
    h_pct = float((h_rank - 1) / max(EXPECTED_HARD - 1, 1)) if not is_soft else 1.0
    return [
        is_soft,
        math.log1p(event_count),
        math.log1p(max(int(family.get("anchor_count", 0)), 0)),
        math.log1p(max(int(family.get("quartet_count", 0)), 0)),
        math.log1p(max(int(family.get("component_count", 0)), 0)),
        float(family.get("best_score", 0.0)),
        smin,
        smax,
        sbalance,
        member_year_balance(family),
        family_centroid_distance(family),
        h_pct,
        float(support_count / event_count),
        trigger,
    ]


def eligible_labels(hidden_labels: dict[str, str]) -> dict[str, Counter[int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for eid, label in hidden_labels.items():
        year = int(str(eid)[:4])
        if year in YEARS and label != "SPORADIC":
            counts[label][year] += 1
    return {
        label: per_year
        for label, per_year in counts.items()
        if sum(per_year.values()) >= 8 and all(per_year.get(year, 0) >= 4 for year in YEARS)
    }


def family_truth(
    family: dict[str, Any],
    hidden_labels: dict[str, str],
    eligible: dict[str, Counter[int]],
) -> dict[str, Any]:
    ids = [str(x) for x in family["event_ids"]]
    counts = Counter(hidden_labels.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, per_year in eligible.items():
        overlap = int(counts.get(label, 0))
        if overlap <= 0:
            continue
        total = int(sum(per_year.values()))
        precision = overlap / max(len(ids), 1)
        recall = overlap / total
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append((f1, precision, overlap, label, recall))
    if not rows:
        return {
            "positive": False,
            "best_label": None,
            "overlap": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "dominant_precision": 0.0,
        }
    f1, precision, overlap, label, recall = max(rows, key=lambda r: (r[0], r[1], r[2], r[3]))
    nonsporadic = counts.copy()
    nonsporadic.pop("SPORADIC", None)
    dominant = max(nonsporadic.values(), default=0) / max(len(ids), 1)
    return {
        "positive": bool(precision >= 0.5 and overlap >= 4),
        "best_label": str(label),
        "overlap": int(overlap),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "dominant_precision": float(dominant),
    }


def monotone_metrics(
    families: list[dict[str, Any]],
    order: list[str],
    truths: dict[str, dict[str, Any]],
    eligible: dict[str, Counter[int]],
) -> dict[str, Any]:
    by_id = {str(f["family_id"]): f for f in families}
    require(len(order) == len(set(order)), "rank order contains duplicates")
    require(set(order).issubset(by_id), "rank order contains unknown family")
    rank = {fid: i + 1 for i, fid in enumerate(order)}

    qualified_by_label: dict[str, list[tuple[int, str, float]]] = defaultdict(list)
    best_f1: dict[str, float] = {label: 0.0 for label in eligible}
    candidate_counts: dict[str, int] = defaultdict(int)
    for fid in order:
        t = truths[fid]
        label = t["best_label"]
        if label is None or label not in eligible:
            continue
        best_f1[label] = max(best_f1[label], float(t["f1"]))
        if t["positive"]:
            qualified_by_label[label].append((rank[fid], fid, float(t["f1"])))
            candidate_counts[label] += 1

    first_ranks = {
        label: min((r for r, _fid, _f1 in qualified_by_label.get(label, [])), default=None)
        for label in eligible
    }
    qualified_labels = [label for label, r in first_ranks.items() if r is not None]
    top_prec = [truths[fid]["dominant_precision"] for fid in order[:100]]
    duplicate_counts = [candidate_counts[label] for label in qualified_labels]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(qualified_labels),
        "recovered_at_25": sum(first_ranks[label] is not None and first_ranks[label] <= 25 for label in eligible),
        "recovered_at_50": sum(first_ranks[label] is not None and first_ranks[label] <= 50 for label in eligible),
        "recovered_at_100": sum(first_ranks[label] is not None and first_ranks[label] <= 100 for label in eligible),
        "recovered_at_500": sum(first_ranks[label] is not None and first_ranks[label] <= 500 for label in eligible),
        "mrr": float(np.mean([1.0 / first_ranks[label] for label in qualified_labels])) if qualified_labels else 0.0,
        "median_first_rank": float(np.median([first_ranks[label] for label in qualified_labels])) if qualified_labels else None,
        "best_membership_macro_f1_all_eligible": float(np.mean(list(best_f1.values()))) if best_f1 else 0.0,
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "labels_with_duplicate_qualified_candidates": sum(x > 1 for x in duplicate_counts),
        "mean_qualified_candidates_per_recovered_label": float(np.mean(duplicate_counts)) if duplicate_counts else 0.0,
        "max_qualified_candidates_for_one_label": max(duplicate_counts, default=0),
        "first_rank_by_label": first_ranks,
    }


def annual_bins(
    families: list[dict[str, Any]],
    hidden_labels: dict[str, str],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        totals = Counter(
            label for eid, label in hidden_labels.items()
            if int(str(eid)[:4]) == year and label != "SPORADIC"
        )
        rows = {}
        for label, total in totals.items():
            if total < 4:
                continue
            best = 0.0
            for family in families:
                ids = [eid for eid in family["event_ids"] if int(str(eid)[:4]) == year]
                if not ids:
                    continue
                overlap = sum(hidden_labels.get(eid) == label for eid in ids)
                if not overlap:
                    continue
                precision = overlap / len(ids)
                recall = overlap / total
                f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
                best = max(best, float(f1))
            rows[label] = {"total": int(total), "f1": best}
        bins = {}
        for name, lo, hi in SIZE_BINS:
            vals = [r["f1"] for r in rows.values() if r["total"] >= lo and (hi is None or r["total"] <= hi)]
            bins[name] = {"showers": len(vals), "mean_f1": float(np.mean(vals)) if vals else 0.0}
        vals = [r["f1"] for r in rows.values()]
        bins["all"] = {"showers": len(vals), "mean_f1": float(np.mean(vals)) if vals else 0.0}
        out[str(year)] = bins
    return out


def deterministic_fold(group: str, folds: int = 5) -> int:
    return int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % folds


def jaccard(a: set[str], b: set[str]) -> float:
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def suppress(order: list[str], sets: dict[str, set[str]], threshold: float | None) -> list[str]:
    if threshold is None:
        return list(order)
    kept: list[str] = []
    for fid in order:
        current = sets[fid]
        if any(jaccard(current, sets[old]) >= threshold for old in kept):
            continue
        kept.append(fid)
    return kept


def score_key(metrics: dict[str, Any]) -> tuple[float, ...]:
    return (
        float(metrics["recovered_at_100"]),
        float(metrics["recovered_at_50"]),
        float(metrics["recovered_at_25"]),
        float(metrics["top100_dominant_precision"]),
        float(metrics["mrr"]),
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.p19_result_json) == EXPECTED_P19_RESULT_SHA256, "P19 result hash changed")
    require(sha256_file(args.p19_prelabel_json) == EXPECTED_P19_PRELABEL_SHA256, "P19 prelabel hash changed")
    p19_result = json.loads(args.p19_result_json.read_text())
    require(p19_result["verdict"] == "FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT", "P19 no-go identity changed")
    payload = json.loads(args.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    soft = payload["soft_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    families = hard + soft
    require(len(hard) == EXPECTED_HARD and len(soft) == EXPECTED_SOFT and len(families) == EXPECTED_COMBINED, "P19 family universe changed")
    require(len(hard_order) == EXPECTED_HARD and set(hard_order) == {str(f["family_id"]) for f in hard}, "P19 hard order changed")

    # Exact temporal substitution used by the promoted v8 development runtime.
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target exclusion changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)

    # Only development labels are opened here, after the 20-55 interval is excluded by the frozen parser.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "development month universe changed")

    eligible = eligible_labels(hidden_labels)
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    family_by_id = {str(f["family_id"]): f for f in families}
    truths = {fid: family_truth(f, hidden_labels, eligible) for fid, f in family_by_id.items()}
    feature_matrix = np.asarray([structural_features(f, hard_rank) for f in families], dtype=float)
    family_ids = [str(f["family_id"]) for f in families]
    y = np.asarray([int(truths[fid]["positive"]) for fid in family_ids], dtype=int)
    require(int(y.sum()) > 0 and int((1-y).sum()) > 0, "candidate-quality target is degenerate")

    groups = []
    for fid in family_ids:
        t = truths[fid]
        if t["positive"] and t["best_label"]:
            groups.append("POS/" + str(t["best_label"]))
        else:
            groups.append("NEG/" + fid)
    folds = np.asarray([deterministic_fold(g) for g in groups], dtype=int)

    hard_only_metrics = monotone_metrics(hard, hard_order, truths, eligible)
    append_order = hard_order + [str(f["family_id"]) for f in soft]
    append_metrics = monotone_metrics(families, append_order, truths, eligible)

    # Truth-aware unique-label ceiling: diagnostic only, never a deployable ranking.
    positive_by_label: dict[str, list[str]] = defaultdict(list)
    for fid in family_ids:
        t = truths[fid]
        if t["positive"] and t["best_label"]:
            positive_by_label[str(t["best_label"])].append(fid)
    oracle_front = []
    for label in sorted(positive_by_label):
        candidates = positive_by_label[label]
        best = max(candidates, key=lambda fid: (truths[fid]["f1"], truths[fid]["precision"], truths[fid]["overlap"], fid))
        oracle_front.append(best)
    oracle_front.sort(key=lambda fid: (-truths[fid]["f1"], -truths[fid]["precision"], fid))
    oracle_order = oracle_front + [fid for fid in family_ids if fid not in set(oracle_front)]
    oracle_metrics = monotone_metrics(families, oracle_order, truths, eligible)

    cv_rows = []
    best_cv = None
    for c in C_GRID:
        oof = np.zeros(len(family_ids), dtype=float)
        fold_diagnostics = []
        for fold in range(5):
            train = folds != fold
            test = folds == fold
            require(train.any() and test.any(), f"empty CV fold {fold}")
            require(np.unique(y[train]).size == 2, f"training fold {fold} lacks both classes")
            model = Pipeline([
                ("scale", StandardScaler()),
                ("logit", LogisticRegression(C=float(c), class_weight="balanced", max_iter=2000, solver="lbfgs")),
            ])
            model.fit(feature_matrix[train], y[train])
            oof[test] = model.predict_proba(feature_matrix[test])[:, 1]
            fold_diagnostics.append({
                "fold": fold,
                "train_n": int(train.sum()),
                "test_n": int(test.sum()),
                "train_positive": int(y[train].sum()),
                "test_positive": int(y[test].sum()),
            })
        raw_order = [fid for _score, _hr, fid in sorted(
            zip(oof, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
            key=lambda row: (-float(row[0]), int(row[1]), str(row[2])),
        )]
        sets = {fid: set(map(str, family_by_id[fid]["event_ids"])) for fid in family_ids}
        for threshold in JACCARD_GRID:
            order = suppress(raw_order, sets, threshold)
            metrics = monotone_metrics(families, order, truths, eligible)
            row = {
                "C": float(c),
                "jaccard_suppression": threshold,
                "output_family_count": len(order),
                "metrics": {k: v for k, v in metrics.items() if k != "first_rank_by_label"},
                "folds": fold_diagnostics,
            }
            cv_rows.append(row)
            key = score_key(metrics) + (-float(len(order)),)
            if best_cv is None or key > best_cv["key"]:
                best_cv = {"key": key, "C": float(c), "threshold": threshold, "order": order, "metrics": metrics, "oof": oof.copy()}

    require(best_cv is not None, "no CV candidate")

    final_model = Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(C=best_cv["C"], class_weight="balanced", max_iter=2000, solver="lbfgs")),
    ])
    final_model.fit(feature_matrix, y)
    final_scores = final_model.predict_proba(feature_matrix)[:, 1]
    final_raw_order = [fid for _score, _hr, fid in sorted(
        zip(final_scores, [hard_rank.get(fid, EXPECTED_HARD + 1) for fid in family_ids], family_ids),
        key=lambda row: (-float(row[0]), int(row[1]), str(row[2])),
    )]
    sets = {fid: set(map(str, family_by_id[fid]["event_ids"])) for fid in family_ids}
    final_order = suppress(final_raw_order, sets, best_cv["threshold"])
    final_metrics = monotone_metrics(families, final_order, truths, eligible)

    scale = final_model.named_steps["scale"]
    logit = final_model.named_steps["logit"]
    coefficients = {
        name: float(value)
        for name, value in zip(FEATURE_NAMES, logit.coef_[0])
    }
    model_export = {
        "C": best_cv["C"],
        "jaccard_suppression": best_cv["threshold"],
        "feature_names": list(FEATURE_NAMES),
        "scaler_mean": [float(x) for x in scale.mean_],
        "scaler_scale": [float(x) for x in scale.scale_],
        "logistic_intercept": float(logit.intercept_[0]),
        "logistic_coefficients": coefficients,
    }

    annual = {
        "hard_only": annual_bins(hard, hidden_labels),
        "all_p19_candidates": annual_bins(families, hidden_labels),
        "cv_selected_suppressed": annual_bins([family_by_id[fid] for fid in best_cv["order"]], hidden_labels),
    }

    # Development viability is intentionally demanding but this is a lab, not a frozen final candidate.
    cvm = best_cv["metrics"]
    viable = (
        int(cvm["recovered_at_100"]) >= int(hard_only_metrics["recovered_at_100"]) + 5
        and int(cvm["recovered_at_50"]) >= int(hard_only_metrics["recovered_at_50"])
        and float(cvm["top100_dominant_precision"]) >= float(hard_only_metrics["top100_dominant_precision"]) - 0.05
        and int(cvm["qualified_matches"]) >= int(hard_only_metrics["qualified_matches"]) + 20
    )
    verdict = "PASS_URC_UNIFIED_RANKING_FEASIBILITY" if viable else "FAIL_URC_UNIFIED_RANKING_FEASIBILITY"

    result = {
        "verdict": verdict,
        "scope": "target-excluded GMN 2022/2023 development-only ranking/deduplication laboratory",
        "candidate_universe": {
            "hard": len(hard),
            "soft": len(soft),
            "combined": len(families),
            "family_level_positive_candidates": int(y.sum()),
            "eligible_known_showers": len(eligible),
            "distinct_positive_labels": len(positive_by_label),
        },
        "baseline_hard_only": {k: v for k, v in hard_only_metrics.items() if k != "first_rank_by_label"},
        "historical_p19_append_order_under_monotone_metric": {k: v for k, v in append_metrics.items() if k != "first_rank_by_label"},
        "truth_aware_unique_label_ceiling": {k: v for k, v in oracle_metrics.items() if k != "first_rank_by_label"},
        "best_cross_validated_structural_ranker": {
            "C": best_cv["C"],
            "jaccard_suppression": best_cv["threshold"],
            "output_family_count": len(best_cv["order"]),
            "metrics": {k: v for k, v in best_cv["metrics"].items() if k != "first_rank_by_label"},
            "order_sha256": hashlib.sha256("\n".join(best_cv["order"]).encode()).hexdigest(),
        },
        "all_cv_candidates": cv_rows,
        "full_development_fit_diagnostic": {
            "metrics": {k: v for k, v in final_metrics.items() if k != "first_rank_by_label"},
            "model": model_export,
            "order_sha256": hashlib.sha256("\n".join(final_order).encode()).hexdigest(),
        },
        "annual_membership_bins": annual,
        "integrity": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "p19_result_sha256": EXPECTED_P19_RESULT_SHA256,
            "p19_prelabel_sha256": EXPECTED_P19_PRELABEL_SHA256,
            "candidate_generation_recomputed": False,
            "candidate_membership_changed": False,
            "labels_used_only_for_GMN_development_model_selection_and_evaluation": True,
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": (
            "Development feasibility only. Exact P19 remains a permanent no-go. A PASS means the broad "
            "hard+subcomponent candidate mechanism contains enough generic structural signal to justify a "
            "new unified recurrent-catalogue architecture; it does not promote P19 or authorize final-test access."
        ),
    }
    (args.output / "unified_recurrent_catalogue_lab_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "UNIFIED_RECURRENT_CATALOGUE_LAB_V1.md").write_text(
        "# Unified recurrent catalogue lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- hard-only monotone recovery@100: `{hard_only_metrics['recovered_at_100']}`\n"
        f"- P19 candidate-universe qualified labels: `{append_metrics['qualified_matches']}`\n"
        f"- truth-aware unique-label recovery@100 ceiling: `{oracle_metrics['recovered_at_100']}`\n"
        f"- cross-validated unified recovery@100: `{best_cv['metrics']['recovered_at_100']}`\n"
        f"- cross-validated unified recovery@50: `{best_cv['metrics']['recovered_at_50']}`\n"
        f"- cross-validated top100 dominant precision: `{best_cv['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- selected suppression threshold: `{best_cv['threshold']}`\n"
        f"- selected C: `{best_cv['C']}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "hard_recovery100": hard_only_metrics["recovered_at_100"],
        "append_monotone_recovery100": append_metrics["recovered_at_100"],
        "oracle_recovery100": oracle_metrics["recovered_at_100"],
        "cv_recovery100": best_cv["metrics"]["recovered_at_100"],
        "cv_recovery50": best_cv["metrics"]["recovered_at_50"],
        "cv_top100_precision": best_cv["metrics"]["top100_dominant_precision"],
        "cv_qualified": best_cv["metrics"]["qualified_matches"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
