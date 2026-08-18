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

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
PRETRUTH_SHA256 = "22ee242d16e73c553d0e2041e55a8d938963c504a824797e92119d15b4bab7ba"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
FEATURE_DIM = 16
BUCKETS = (0, 1, 2, 3)
DENOMINATORS = (128, 1024)


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


def metric_record(raw: dict[str, Any], eligible_count: int) -> dict[str, Any]:
    req(eligible_count > 0, "zero eligible-label denominator")
    first = raw.get("first_rank_by_label")
    req(isinstance(first, dict), "missing first_rank_by_label")
    reciprocal = 0.0
    for rank in first.values():
        r = int(rank)
        req(r >= 1, "invalid first rank")
        reciprocal += 1.0 / r
    out = {k: v for k, v in raw.items() if k != "first_rank_by_label"}
    out["mrr_zero_filled"] = float(reciprocal / eligible_count)
    out["eligible_label_count"] = int(eligible_count)
    out["recovered_label_count"] = int(len(first))
    return out


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    return {
        "qualified_total": sum(int(v["qualified_matches"]) for v in vals),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])),
        "mrr_zero_filled_mean": float(np.mean([float(v["mrr_zero_filled"]) for v in vals])),
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
    ap.add_argument("--predecessor-trainer", type=Path, required=True)
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

    req(sha256(a.pretruth) == PRETRUTH_SHA256, "sealed predecessor pretruth changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(a.ranker_source) == QUALITY_SHA256, "#839 ranker source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 support artifact changed")

    old = load_module(a.predecessor_trainer, "topomodal_raw_f1_predecessor")
    req(old.GROUP_SALT == "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1|", "predecessor fold salt changed")
    req(old.FEATURE_DIM == FEATURE_DIM and tuple(old.DENOMINATORS) == DENOMINATORS and tuple(old.BUCKETS) == BUCKETS, "predecessor experiment geometry changed")

    pre = json.loads(a.pretruth.read_text())
    req(pre["schema"] == "ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["scientific_role"] == "PRETRUTH_FEATURE_AND_MEMBERSHIP_FREEZE", "wrong pretruth role")
    req(pre["structural_result_sha256"] == STRUCTURAL_RESULT_SHA256, "structural source changed")
    req(int(pre["feature_dimension"]) == FEATURE_DIM and len(pre["feature_names"]) == FEATURE_DIM, "feature map changed")
    req(pre["blind_exclusion"] == list(BLIND) and pre["shower_truth_used"] is False, "pretruth firewall changed")
    subset_map = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subset_map) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "pretruth panel set changed")

    parent = load_module(a.parent_runner, "representative_share_eval_parent")
    ranker = load_module(a.ranker_source, "representative_share_frozen_839")
    base_params = ranker.model().get_params()
    req(base_params.get("max_depth") == 4 and base_params.get("min_samples_leaf") == 5, "#839 baseline capacity changed")
    req(base_params.get("n_estimators") == 600, "#839 tree count changed")

    q = load_module(a.quality_source, "representative_share_eval_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-representative-share-oof-v1-supervised-stage"
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
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event survived parser")
    ids_full = [str(e["id"]) for e in events]
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([old.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    panel_context: dict[tuple[int, int], dict[str, Any]] = {}
    X_rows: list[list[float]] = []
    y22_rows: list[float] = []
    y23_rows: list[float] = []
    groups: list[str] = []
    offsets: dict[tuple[int, int], tuple[int, int]] = {}
    target_diagnostics: list[dict[str, Any]] = []
    cursor = 0

    for d in DENOMINATORS:
        for b in BUCKETS:
            fr = subset_map[(d, b)]
            ix = old.selected_indices(hashes, d, b)
            ids = [ids_full[int(i)] for i in ix]
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            req(len(ids) == int(fr["events_total"]), f"panel event count changed d={d} b={b}")
            annual_ids = {y: {ids[int(i)] for i in np.flatnonzero(yrs == y)} for y in YEARS}
            eligible = {y: parent.eligible_labels(hidden, annual_ids[y]) for y in YEARS}
            candidates = fr["candidates"]

            raw_rows: list[dict[str, Any]] = []
            sums22: dict[str, float] = defaultdict(float)
            sums23: dict[str, float] = defaultdict(float)
            for c in candidates:
                feature = [float(x) for x in c["features"]]
                req(len(feature) == FEATURE_DIM and all(math.isfinite(x) for x in feature), "invalid sealed feature row")
                group, f22, f23, diag = old.choose_group_and_targets(c, annual_ids, eligible, hidden, d, b)
                raw_rows.append({"candidate": c, "feature": feature, "group": str(group), "f22": float(f22), "f23": float(f23), "diag": diag})
                if str(group).startswith("SHOWER/"):
                    sums22[str(group)] += float(f22)
                    sums23[str(group)] += float(f23)

            lo = cursor
            panel_share_sums22: dict[str, float] = defaultdict(float)
            panel_share_sums23: dict[str, float] = defaultdict(float)
            nonzero = 0
            balanced_nonzero = 0
            positive_groups: set[str] = set()
            for row in raw_rows:
                group = row["group"]
                if group.startswith("SHOWER/"):
                    t22 = row["f22"] / sums22[group] if sums22[group] > 0.0 else 0.0
                    t23 = row["f23"] / sums23[group] if sums23[group] > 0.0 else 0.0
                    positive_groups.add(group)
                    panel_share_sums22[group] += t22
                    panel_share_sums23[group] += t23
                else:
                    t22 = t23 = 0.0
                req(0.0 <= t22 <= 1.0 + 1e-12 and 0.0 <= t23 <= 1.0 + 1e-12, "invalid representative-share target")
                X_rows.append(row["feature"])
                y22_rows.append(float(t22))
                y23_rows.append(float(t23))
                groups.append(group)
                nonzero += int(max(t22, t23) > 0.0)
                balanced_nonzero += int(min(t22, t23) > 0.0)
                cursor += 1

            for group in sorted(positive_groups):
                if sums22[group] > 0.0:
                    req(abs(panel_share_sums22[group] - 1.0) < 1e-10, f"2022 share mass changed d={d} b={b} group={group}")
                else:
                    req(panel_share_sums22[group] == 0.0, "zero-denominator 2022 share nonzero")
                if sums23[group] > 0.0:
                    req(abs(panel_share_sums23[group] - 1.0) < 1e-10, f"2023 share mass changed d={d} b={b} group={group}")
                else:
                    req(panel_share_sums23[group] == 0.0, "zero-denominator 2023 share nonzero")

            offsets[(d, b)] = (lo, cursor)
            panel_context[(d, b)] = {
                "annual_ids": annual_ids,
                "eligible": eligible,
                "candidates": candidates,
                "recurrent_candidates": fr["recurrent_candidates"],
            }
            target_diagnostics.append({
                "denominator": d,
                "bucket": b,
                "candidate_count": len(candidates),
                "truth_tied_candidate_count": nonzero,
                "balanced_nonzero_target_count": balanced_nonzero,
                "positive_shower_group_count": len(positive_groups),
                "eligible_showers": {str(y): len(eligible[y]) for y in YEARS},
                "share_mass_2022_groups_at_one": sum(abs(v - 1.0) < 1e-10 for g, v in panel_share_sums22.items() if sums22[g] > 0.0),
                "share_mass_2023_groups_at_one": sum(abs(v - 1.0) < 1e-10 for g, v in panel_share_sums23.items() if sums23[g] > 0.0),
            })

    X = np.asarray(X_rows, dtype=np.float64)
    y22 = np.asarray(y22_rows, dtype=np.float64)
    y23 = np.asarray(y23_rows, dtype=np.float64)
    groups = list(map(str, groups))
    req(X.shape == (cursor, FEATURE_DIM), "stacked feature shape changed")
    req(len(y22) == len(y23) == len(groups) == cursor, "stacked target/group shape changed")
    req(np.all(np.isfinite(X)) and np.all(np.isfinite(y22)) and np.all(np.isfinite(y23)), "nonfinite stacked data")
    req(np.all((y22 >= 0.0) & (y22 <= 1.0 + 1e-12)) and np.all((y23 >= 0.0) & (y23 <= 1.0 + 1e-12)), "invalid share targets")

    folds = np.asarray([old.group_fold(g) for g in groups], dtype=np.int64)
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
        chosen, inner_diag = old.inner_select_capacity(ranker, X, y22, y23, groups, folds, weights, fold)
        m22 = old.capacity_model(ranker, chosen)
        m23 = old.capacity_model(ranker, chosen)
        m22.fit(X[train], y22[train], sample_weight=weights[train])
        m23.fit(X[train], y23[train], sample_weight=weights[train])
        oof22[test] = np.asarray(m22.predict(X[test]), dtype=np.float64)
        oof23[test] = np.asarray(m23.predict(X[test]), dtype=np.float64)
        fold_diagnostics.append({
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
        })

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
            selected = old.learned_antichain(ctx["candidates"], utility[lo:hi])
            recurrent = ctx["recurrent_candidates"]
            budget = len(recurrent)
            capacity_ok = len(selected) >= budget
            all_capacity = all_capacity and capacity_ok
            selector_summaries.append({
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
            })
            if not capacity_ok:
                continue
            successor_budget = selected[:budget]
            for y in YEARS:
                annual_ids = ctx["annual_ids"][y]
                eligible_count = len(ctx["eligible"][y])
                parent_raw = parent.metrics(recurrent, hidden, annual_ids)
                successor_raw = parent.metrics(successor_budget, hidden, annual_ids)
                parent_metrics = metric_record(parent_raw, eligible_count)
                successor_metrics = metric_record(successor_raw, eligible_count)
                panels.append({
                    "denominator": d,
                    "bucket": b,
                    "year": y,
                    "equal_budget_k": budget,
                    "parent_equal_budget": parent_metrics,
                    "successor_equal_budget": successor_metrics,
                    "qualified_nonlower": int(successor_metrics["qualified_matches"]) >= int(parent_metrics["qualified_matches"]),
                    "qualified_strict_win": int(successor_metrics["qualified_matches"]) > int(parent_metrics["qualified_matches"]),
                })

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
        "fine_conditional_mrr_mean_not_lower",
        "fine_zero_filled_mrr_mean_not_lower",
        "fine_precision_mean_not_lower",
        "fine_fragmentation_mean_not_higher",
        "coarse_qualified_total_not_lower",
        "coarse_qualified_nonlower_at_least_6_of_8",
        "coarse_conditional_mrr_mean_not_lower",
        "coarse_zero_filled_mrr_mean_not_lower",
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
            "fine_conditional_mrr_mean_not_lower": fs["mrr_mean"] >= fp["mrr_mean"],
            "fine_zero_filled_mrr_mean_not_lower": fs["mrr_zero_filled_mean"] >= fp["mrr_zero_filled_mean"],
            "fine_precision_mean_not_lower": fs["precision_mean"] >= fp["precision_mean"],
            "fine_fragmentation_mean_not_higher": fs["fragmentation_mean"] <= fp["fragmentation_mean"],
            "coarse_qualified_total_not_lower": cs["qualified_total"] >= cp["qualified_total"],
            "coarse_qualified_nonlower_at_least_6_of_8": scales["128"]["qualified_nonlower_panels"] >= 6,
            "coarse_conditional_mrr_mean_not_lower": cs["mrr_mean"] >= cp["mrr_mean"],
            "coarse_zero_filled_mrr_mean_not_lower": cs["mrr_zero_filled_mean"] >= cp["mrr_zero_filled_mean"],
            "coarse_precision_mean_not_lower": cs["precision_mean"] >= cp["precision_mean"],
            "coarse_fragmentation_mean_not_higher": cs["fragmentation_mean"] <= cp["fragmentation_mean"],
        }
    else:
        gates = {name: False for name in gate_names}

    verdict = "PASS_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1" if complete and all(bool(v) for v in gates.values()) else "FAIL_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1"
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_SUPERVISED_DEVELOPMENT_CONTINUATION",
        "verdict": verdict,
        "pretruth_sha256": PRETRUTH_SHA256,
        "protocol_sha256": sha256(a.protocol),
        "feature_dimension": FEATURE_DIM,
        "target_definition": "PANELWISE_YEARWISE_F1_SHARE_WITHIN_ASSIGNED_SHOWER_GROUP",
        "fold_definition": "EXACT_PREDECESSOR_WHOLE_SHOWER_FOLDS",
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
        "shower_truth_used_after_exact_pretruth_hash_gate": True,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
        "supersedes_frozen_amos_endpoint": False,
    }
    out = a.output / "TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1.json"
    result_sha = dump(out, result)
    print(json.dumps({
        "verdict": verdict,
        "result_sha256": result_sha,
        "pretruth_sha256": PRETRUTH_SHA256,
        "candidate_capacity_all_panels": bool(all_capacity),
        "selector_summaries": selector_summaries,
        "scales": scales,
        "gates": gates,
        "selected_capacities": [d["selected_capacity"] for d in fold_diagnostics],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
