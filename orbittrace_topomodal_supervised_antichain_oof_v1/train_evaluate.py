#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.base import clone

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
RANKER_SOURCE_SHA256 = QUALITY_SHA256
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
SCALE_SALT = "ORBITTRACE_SCALE_STRESS_V1|"
GROUP_SALT = "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1|"
FEATURE_DIM = 16
BUCKETS = (0, 1, 2, 3)
DENOMINATORS = (128, 1024)

CAPACITIES = (
    ("baseline_d4_l5", {"max_depth": 4, "min_samples_leaf": 5}),
    ("medium_d8_l3", {"max_depth": 8, "min_samples_leaf": 3}),
    ("high_unbounded_l2", {"max_depth": None, "min_samples_leaf": 2}),
)
CAPACITY_TIE_PREFERENCE = {
    "baseline_d4_l5": 3,
    "medium_d8_l3": 2,
    "high_unbounded_l2": 1,
}


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


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SCALE_SALT + eid).encode()).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def group_fold(group: str) -> int:
    return int.from_bytes(hashlib.sha256((GROUP_SALT + group).encode()).digest()[:8], "big") % 5


def label_f1(
    candidate_event_ids: list[str],
    annual_ids: set[str],
    hidden: dict[str, str],
    annual_total: int,
    label: str,
) -> float:
    ids = [eid for eid in candidate_event_ids if eid in annual_ids]
    if not ids or annual_total <= 0:
        return 0.0
    overlap = sum(hidden.get(eid, "SPORADIC") == label for eid in ids)
    if overlap <= 0:
        return 0.0
    precision = overlap / len(ids)
    recall = overlap / annual_total
    return float(2.0 * precision * recall / (precision + recall)) if precision + recall else 0.0


def choose_group_and_targets(
    candidate: dict[str, Any],
    annual_ids: dict[int, set[str]],
    eligible: dict[int, dict[str, int]],
    hidden: dict[str, str],
    denominator: int,
    bucket: int,
) -> tuple[str, float, float, dict[str, Any]]:
    labels = sorted(set(eligible[2022]) | set(eligible[2023]))
    rows: list[tuple[float, float, float, str, float, float]] = []
    ids = list(map(str, candidate["event_ids"]))
    for label in labels:
        f22 = label_f1(ids, annual_ids[2022], hidden, int(eligible[2022].get(label, 0)), label)
        f23 = label_f1(ids, annual_ids[2023], hidden, int(eligible[2023].get(label, 0)), label)
        lo = min(f22, f23)
        mean = 0.5 * (f22 + f23)
        hi = max(f22, f23)
        rows.append((lo, mean, hi, label, f22, f23))
    if not rows:
        return (
            f"NEG/{denominator}/{bucket}/{candidate['family_hash']}",
            0.0,
            0.0,
            {"best_label": None, "best_min_f1": 0.0, "best_mean_f1": 0.0, "best_max_f1": 0.0},
        )
    best = min(rows, key=lambda r: (-r[0], -r[1], -r[2], r[3]))
    lo, mean, hi, label, f22, f23 = best
    if hi <= 0.0:
        group = f"NEG/{denominator}/{bucket}/{candidate['family_hash']}"
        label_out: str | None = None
        f22 = f23 = 0.0
    else:
        group = "SHOWER/" + label
        label_out = label
    return (
        group,
        float(f22),
        float(f23),
        {
            "best_label": label_out,
            "best_min_f1": float(lo if hi > 0.0 else 0.0),
            "best_mean_f1": float(mean if hi > 0.0 else 0.0),
            "best_max_f1": float(hi if hi > 0.0 else 0.0),
        },
    )


def capacity_model(ranker: Any, name: str):
    params = dict(CAPACITIES)[name]
    model = clone(ranker.model())
    model.set_params(**params)
    return model


def stable_group_ndcg(
    pred: np.ndarray,
    y22: np.ndarray,
    y23: np.ndarray,
    groups: list[str],
    mask: np.ndarray,
) -> float:
    idx = np.where(mask)[0]
    req(len(idx) > 0, "empty NDCG mask")
    per: dict[str, list[int]] = defaultdict(list)
    for i in idx.tolist():
        per[str(groups[i])].append(int(i))
    group_ids = sorted(per)
    relevance: list[float] = []
    scores: list[float] = []
    for group in group_ids:
        ii = np.asarray(per[group], dtype=int)
        relevance.append(float(np.max(np.minimum(y22[ii], y23[ii]))))
        scores.append(float(np.max(pred[ii])))
    rel = np.asarray(relevance, dtype=np.float64)
    score = np.asarray(scores, dtype=np.float64)
    req(np.all(np.isfinite(rel)) and np.all(np.isfinite(score)), "nonfinite NDCG input")
    req(np.all((rel >= 0.0) & (rel <= 1.0)), "invalid NDCG relevance")
    gain = np.exp2(rel) - 1.0

    def dcg(order: list[int]) -> float:
        return float(sum(gain[i] / np.log2(rank + 2.0) for rank, i in enumerate(order)))

    pred_order = sorted(range(len(group_ids)), key=lambda i: (-score[i], group_ids[i]))
    ideal_order = sorted(range(len(group_ids)), key=lambda i: (-rel[i], group_ids[i]))
    ideal = dcg(ideal_order)
    req(ideal > 0.0, "zero ideal NDCG in nested capacity selection")
    return dcg(pred_order) / ideal


def fit_predict_capacity(
    ranker: Any,
    name: str,
    X: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
) -> np.ndarray:
    model = capacity_model(ranker, name)
    model.fit(X[train], y[train], sample_weight=weights[train])
    return np.asarray(model.predict(X[test]), dtype=np.float64)


def inner_select_capacity(
    ranker: Any,
    X: np.ndarray,
    y22: np.ndarray,
    y23: np.ndarray,
    groups: list[str],
    folds: np.ndarray,
    weights: np.ndarray,
    outer_fold: int,
) -> tuple[str, list[dict[str, Any]]]:
    outer_train = folds != outer_fold
    diagnostics: list[dict[str, Any]] = []
    for name, params in CAPACITIES:
        p22 = np.full(len(groups), np.nan, dtype=np.float64)
        p23 = np.full(len(groups), np.nan, dtype=np.float64)
        inner_rows: list[dict[str, Any]] = []
        for inner_fold in range(5):
            if inner_fold == outer_fold:
                continue
            train = outer_train & (folds != inner_fold)
            test = outer_train & (folds == inner_fold)
            req(train.any() and test.any(), f"empty inner fold outer={outer_fold} inner={inner_fold}")
            train_groups = {groups[i] for i in np.where(train)[0]}
            test_groups = {groups[i] for i in np.where(test)[0]}
            req(train_groups.isdisjoint(test_groups), f"inner group leakage outer={outer_fold} inner={inner_fold}")
            p22[test] = fit_predict_capacity(ranker, name, X, y22, weights, train, test)
            p23[test] = fit_predict_capacity(ranker, name, X, y23, weights, train, test)
            inner_rows.append(
                {
                    "inner_fold": inner_fold,
                    "train_examples": int(train.sum()),
                    "test_examples": int(test.sum()),
                    "train_groups": len(train_groups),
                    "test_groups": len(test_groups),
                }
            )
        req(np.all(np.isfinite(p22[outer_train])) and np.all(np.isfinite(p23[outer_train])), f"incomplete inner OOF {name} outer={outer_fold}")
        req(np.all(np.isnan(p22[~outer_train])) and np.all(np.isnan(p23[~outer_train])), f"outer test populated during inner selection {name} outer={outer_fold}")
        combined = np.minimum(p22, p23)
        score = stable_group_ndcg(combined, y22, y23, groups, outer_train)
        diagnostics.append(
            {
                "capacity": name,
                "params": dict(params),
                "inner_group_ndcg": float(score),
                "inner_folds": inner_rows,
                "tie_preference": CAPACITY_TIE_PREFERENCE[name],
            }
        )
    winner = max(diagnostics, key=lambda d: (d["inner_group_ndcg"], d["tie_preference"]))
    return str(winner["capacity"]), diagnostics


def learned_antichain(candidates: list[dict[str, Any]], utility: np.ndarray) -> list[dict[str, Any]]:
    req(len(candidates) == len(utility), "panel utility alignment changed")
    by_node = {int(c["node"]): i for i, c in enumerate(candidates)}
    req(len(by_node) == len(candidates), "duplicate eligible hierarchy node")
    roots = [int(c["node"]) for c in candidates if bool(c["is_root"])]
    req(bool(roots), "no eligible TopoModal roots")
    memo: dict[int, tuple[float, list[int]]] = {}

    def rec(node: int) -> tuple[float, list[int]]:
        if node in memo:
            return memo[node]
        i = by_node[node]
        child_total = 0.0
        child_selected: list[int] = []
        for child in candidates[i]["eligible_child_nodes"]:
            cnode = int(child)
            req(cnode in by_node, "eligible child missing from candidate universe")
            value, chosen = rec(cnode)
            child_total += value
            child_selected.extend(chosen)
        node_value = max(0.0, float(utility[i]))
        if node_value > 0.0 and node_value >= child_total:
            ans = (node_value, [i])
        else:
            ans = (child_total, child_selected)
        memo[node] = ans
        return ans

    selected: list[int] = []
    for root in roots:
        selected.extend(rec(root)[1])
    req(len(selected) == len(set(selected)), "duplicate antichain selection")

    owner: dict[str, int] = {}
    out: list[dict[str, Any]] = []
    for i in selected:
        c = candidates[i]
        score = float(utility[i])
        req(score > 0.0 and math.isfinite(score), "selected candidate has nonpositive/nonfinite utility")
        for eid in c["event_ids"]:
            req(eid not in owner, "learned antichain overlaps")
            owner[eid] = i
        out.append(
            {
                "family_id": str(c["family_id"]),
                "family_hash": str(c["family_hash"]),
                "node": int(c["node"]),
                "event_ids": list(map(str, c["event_ids"])),
                "member_count": int(c["member_count"]),
                "oof_utility": score,
            }
        )
    out.sort(key=lambda r: (-float(r["oof_utility"]), str(r["family_hash"])))
    for rank, row in enumerate(out, 1):
        row["rank"] = rank
    return out


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    return {
        "qualified_total": sum(int(v["qualified_matches"]) for v in vals),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])),
        "precision_mean": float(np.mean([float(v["top100_dominant_precision"]) for v in vals])),
        "fragmentation_mean": float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])),
        "recovered_at_25_total": sum(int(v["recovered_at_25"]) for v in vals),
        "recovered_at_50_total": sum(int(v["recovered_at_50"]) for v in vals),
        "recovered_at_100_total": sum(int(v["recovered_at_100"]) for v in vals),
        "recovered_at_500_total": sum(int(v["recovered_at_500"]) for v in vals),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--ranker-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(a.ranker_source) == RANKER_SOURCE_SHA256, "#839 ranker source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 support artifact changed")

    pretruth_sha = sha256(a.pretruth)
    pre = json.loads(a.pretruth.read_text())
    req(pre["schema"] == "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["scientific_role"] == "PRETRUTH_FEATURE_AND_MEMBERSHIP_FREEZE", "wrong pretruth role")
    req(pre["structural_result_sha256"] == STRUCTURAL_RESULT_SHA256, "structural source changed")
    req(int(pre["feature_dimension"]) == FEATURE_DIM and len(pre["feature_names"]) == FEATURE_DIM, "feature map changed")
    req(pre["protocol_sha256"] == sha256(a.protocol), "protocol changed after pretruth freeze")
    req(pre["blind_exclusion"] == list(BLIND) and pre["shower_truth_used"] is False, "pretruth firewall changed")
    subset_map = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subset_map) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "pretruth panel set changed")

    parent = load_module(a.parent_runner, "tsa_eval_parent")
    ranker = load_module(a.ranker_source, "tsa_frozen_839")
    base_params = ranker.model().get_params()
    req(base_params.get("max_depth") == 4 and base_params.get("min_samples_leaf") == 5, "#839 baseline capacity changed")
    req(base_params.get("n_estimators") == 600, "#839 tree count changed")

    q = load_module(a.quality_source, "tsa_eval_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-supervised-antichain-oof-v1-supervised-stage"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict), "GMN hidden truth unavailable")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source set changed")

    events: list[dict[str, Any]] = []
    for y in YEARS:
        events.extend(parent.normalize_event(row, y) for row in list(scan[y]))
    req(len(events) == 738682 and len({str(e["id"]) for e in events}) == 738682, "pooled target-excluded event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived supervised-stage parser")
    ids_full = [str(e["id"]) for e in events]
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    panel_context: dict[tuple[int, int], dict[str, Any]] = {}
    X_rows: list[list[float]] = []
    y22_rows: list[float] = []
    y23_rows: list[float] = []
    groups: list[str] = []
    target_diagnostics: list[dict[str, Any]] = []
    offsets: dict[tuple[int, int], tuple[int, int]] = {}
    cursor = 0

    for d in DENOMINATORS:
        for b in BUCKETS:
            fr = subset_map[(d, b)]
            ix = selected_indices(hashes, d, b)
            ids = [ids_full[int(i)] for i in ix]
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            req(len(ids) == int(fr["events_total"]), f"panel event count changed d={d} b={b}")
            annual_ids = {y: {ids[int(i)] for i in np.flatnonzero(yrs == y)} for y in YEARS}
            eligible = {y: parent.eligible_labels(hidden, annual_ids[y]) for y in YEARS}
            candidates = fr["candidates"]
            lo = cursor
            nonzero = 0
            balanced_nonzero = 0
            positive_groups: set[str] = set()
            for c in candidates:
                feature = [float(x) for x in c["features"]]
                req(len(feature) == FEATURE_DIM and all(math.isfinite(x) for x in feature), "invalid sealed feature row")
                group, t22, t23, _diag = choose_group_and_targets(c, annual_ids, eligible, hidden, d, b)
                X_rows.append(feature)
                y22_rows.append(t22)
                y23_rows.append(t23)
                groups.append(group)
                nonzero += int(max(t22, t23) > 0.0)
                balanced_nonzero += int(min(t22, t23) > 0.0)
                if group.startswith("SHOWER/"):
                    positive_groups.add(group)
            cursor += len(candidates)
            offsets[(d, b)] = (lo, cursor)
            panel_context[(d, b)] = {
                "annual_ids": annual_ids,
                "eligible_counts": {str(y): len(eligible[y]) for y in YEARS},
                "candidates": candidates,
                "recurrent_candidates": fr["recurrent_candidates"],
            }
            target_diagnostics.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "candidate_count": len(candidates),
                    "truth_tied_candidate_count": nonzero,
                    "balanced_nonzero_target_count": balanced_nonzero,
                    "positive_shower_group_count": len(positive_groups),
                    "eligible_showers": {str(y): len(eligible[y]) for y in YEARS},
                }
            )

    X = np.asarray(X_rows, dtype=np.float64)
    y22 = np.asarray(y22_rows, dtype=np.float64)
    y23 = np.asarray(y23_rows, dtype=np.float64)
    groups = list(map(str, groups))
    req(X.shape == (cursor, FEATURE_DIM), "stacked feature shape changed")
    req(len(y22) == len(y23) == len(groups) == cursor, "stacked target/group shape changed")
    req(np.all(np.isfinite(X)) and np.all(np.isfinite(y22)) and np.all(np.isfinite(y23)), "nonfinite stacked data")
    req(np.all((y22 >= 0.0) & (y22 <= 1.0)) and np.all((y23 >= 0.0) & (y23 <= 1.0)), "invalid supervised targets")

    folds = np.asarray([group_fold(g) for g in groups], dtype=np.int64)
    req(set(map(int, np.unique(folds))) == set(range(5)), "outer fold coverage collapsed")
    weights = np.asarray(ranker.grouped_weights(groups), dtype=np.float64)
    req(weights.shape == (cursor,) and np.all(np.isfinite(weights)) and np.all(weights > 0.0), "invalid grouped weights")

    oof22 = np.full(cursor, np.nan, dtype=np.float64)
    oof23 = np.full(cursor, np.nan, dtype=np.float64)
    fold_diagnostics: list[dict[str, Any]] = []
    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty outer fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        req(train_groups.isdisjoint(test_groups), f"outer group leakage {fold}")
        chosen, inner_diag = inner_select_capacity(ranker, X, y22, y23, groups, folds, weights, fold)
        m22 = capacity_model(ranker, chosen)
        m23 = capacity_model(ranker, chosen)
        m22.fit(X[train], y22[train], sample_weight=weights[train])
        m23.fit(X[train], y23[train], sample_weight=weights[train])
        oof22[test] = np.asarray(m22.predict(X[test]), dtype=np.float64)
        oof23[test] = np.asarray(m23.predict(X[test]), dtype=np.float64)
        fold_diagnostics.append(
            {
                "outer_fold": fold,
                "train_examples": int(train.sum()),
                "test_examples": int(test.sum()),
                "train_groups": len(train_groups),
                "test_groups": len(test_groups),
                "selected_capacity": chosen,
                "inner_capacity_diagnostics": inner_diag,
                "outer_test_nonzero_2022": int(np.sum(y22[test] > 0.0)),
                "outer_test_nonzero_2023": int(np.sum(y23[test] > 0.0)),
                "outer_test_balanced_nonzero": int(np.sum(np.minimum(y22[test], y23[test]) > 0.0)),
            }
        )

    req(np.all(np.isfinite(oof22)) and np.all(np.isfinite(oof23)), "incomplete/nonfinite outer OOF predictions")
    utility = np.minimum(oof22, oof23)
    req(np.all(np.isfinite(utility)), "nonfinite combined OOF utility")

    panels: list[dict[str, Any]] = []
    all_capacity = True
    selector_summaries: list[dict[str, Any]] = []
    for d in DENOMINATORS:
        for b in BUCKETS:
            lo, hi = offsets[(d, b)]
            ctx = panel_context[(d, b)]
            selected = learned_antichain(ctx["candidates"], utility[lo:hi])
            recurrent = ctx["recurrent_candidates"]
            budget = len(recurrent)
            capacity_ok = len(selected) >= budget
            all_capacity = all_capacity and capacity_ok
            selector_summaries.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "hierarchy_candidate_count": len(ctx["candidates"]),
                    "selected_candidate_count": len(selected),
                    "recurrent_budget": budget,
                    "capacity_ok": bool(capacity_ok),
                    "positive_oof_utility_count": int(np.sum(utility[lo:hi] > 0.0)),
                    "oof_utility_min": float(np.min(utility[lo:hi])),
                    "oof_utility_max": float(np.max(utility[lo:hi])),
                    "oof_utility_mean": float(np.mean(utility[lo:hi])),
                }
            )
            if not capacity_ok:
                continue
            successor_budget = selected[:budget]
            for y in YEARS:
                annual_ids = ctx["annual_ids"][y]
                parent_metrics = compact(parent.metrics(recurrent, hidden, annual_ids))
                successor_metrics = compact(parent.metrics(successor_budget, hidden, annual_ids))
                panels.append(
                    {
                        "denominator": d,
                        "bucket": b,
                        "year": y,
                        "equal_budget_k": budget,
                        "parent_equal_budget": parent_metrics,
                        "successor_equal_budget": successor_metrics,
                        "qualified_nonlower": int(successor_metrics["qualified_matches"]) >= int(parent_metrics["qualified_matches"]),
                        "qualified_strict_win": int(successor_metrics["qualified_matches"]) > int(parent_metrics["qualified_matches"]),
                    }
                )

    scales: dict[str, Any] = {}
    for d in DENOMINATORS:
        ps = [p for p in panels if int(p["denominator"]) == d]
        if len(ps) != 8:
            scales[str(d)] = {"panel_count": len(ps), "all_candidate_capacity_ok": False}
            continue
        parent_agg = aggregate(ps, "parent_equal_budget")
        successor_agg = aggregate(ps, "successor_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in ps)
        strict = sum(bool(p["qualified_strict_win"]) for p in ps)
        scales[str(d)] = {
            "panel_count": 8,
            "all_candidate_capacity_ok": True,
            "parent_equal_budget": parent_agg,
            "successor_equal_budget": successor_agg,
            "qualified_nonlower_panels": nonlower,
            "qualified_strict_win_panels": strict,
            "qualified_loss_panels": 8 - nonlower,
        }

    gate_names = (
        "fine_qualified_total_strictly_greater",
        "fine_qualified_nonlower_at_least_6_of_8",
        "fine_mrr_mean_not_lower",
        "fine_precision_mean_not_lower",
        "fine_fragmentation_mean_not_higher",
        "coarse_qualified_total_not_lower",
        "coarse_qualified_nonlower_at_least_6_of_8",
        "coarse_mrr_mean_not_lower",
        "coarse_precision_mean_not_lower",
        "coarse_fragmentation_mean_not_higher",
    )
    complete = all_capacity and all(scales[str(d)].get("panel_count") == 8 for d in DENOMINATORS)
    if complete:
        fp = scales["1024"]["parent_equal_budget"]
        fs = scales["1024"]["successor_equal_budget"]
        cp = scales["128"]["parent_equal_budget"]
        cs = scales["128"]["successor_equal_budget"]
        gates = {
            "fine_qualified_total_strictly_greater": fs["qualified_total"] > fp["qualified_total"],
            "fine_qualified_nonlower_at_least_6_of_8": scales["1024"]["qualified_nonlower_panels"] >= 6,
            "fine_mrr_mean_not_lower": fs["mrr_mean"] >= fp["mrr_mean"],
            "fine_precision_mean_not_lower": fs["precision_mean"] >= fp["precision_mean"],
            "fine_fragmentation_mean_not_higher": fs["fragmentation_mean"] <= fp["fragmentation_mean"],
            "coarse_qualified_total_not_lower": cs["qualified_total"] >= cp["qualified_total"],
            "coarse_qualified_nonlower_at_least_6_of_8": scales["128"]["qualified_nonlower_panels"] >= 6,
            "coarse_mrr_mean_not_lower": cs["mrr_mean"] >= cp["mrr_mean"],
            "coarse_precision_mean_not_lower": cs["precision_mean"] >= cp["precision_mean"],
            "coarse_fragmentation_mean_not_higher": cs["fragmentation_mean"] <= cp["fragmentation_mean"],
        }
    else:
        gates = {name: False for name in gate_names}

    verdict = (
        "PASS_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1"
        if complete and all(bool(v) for v in gates.values())
        else "FAIL_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1"
    )
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_SUPERVISED_DEVELOPMENT",
        "verdict": verdict,
        "pretruth_sha256": pretruth_sha,
        "protocol_sha256": sha256(a.protocol),
        "feature_dimension": FEATURE_DIM,
        "candidate_capacity_all_panels": bool(all_capacity),
        "selector_summaries": selector_summaries,
        "target_diagnostics": target_diagnostics,
        "fold_diagnostics": fold_diagnostics,
        "panels": panels,
        "scale_aggregates": scales,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used_after_pretruth_freeze": True,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1.json"
    result_sha = dump(out, result)
    print(
        json.dumps(
            {
                "verdict": verdict,
                "result_sha256": result_sha,
                "pretruth_sha256": pretruth_sha,
                "candidate_capacity_all_panels": bool(all_capacity),
                "selector_summaries": selector_summaries,
                "scales": scales,
                "gates": gates,
                "selected_capacities": [d["selected_capacity"] for d in fold_diagnostics],
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
