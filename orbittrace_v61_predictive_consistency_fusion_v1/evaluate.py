#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

FEATURE_DIM = 71
RECOVERY = 0.5
EXPECTED_V31 = {
    ("sugar", 2013): (0.2719801488280529, 16),
    ("sugar", 2014): (0.31529041952487225, 17),
    ("hdbscan", 2013): (0.14888037368183737, 9),
    ("hdbscan", 2014): (0.15198123772301594, 9),
}
EXPECTED_COUNTS = {"sugar": 267, "hdbscan": 229}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(map(str, order)).encode()).hexdigest()


def rank_sum(v31_order: list[str], predictive_order: list[str]) -> list[str]:
    require(len(v31_order) == len(predictive_order) and set(v31_order) == set(predictive_order), "v61 fusion universe mismatch")
    a = {fid: i + 1 for i, fid in enumerate(v31_order)}
    b = {fid: i + 1 for i, fid in enumerate(predictive_order)}
    return sorted(v31_order, key=lambda fid: (a[fid] + b[fid], a[fid], fid))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sugar-root", type=Path, required=True)
    p.add_argument("--hdbscan-root", type=Path, required=True)
    p.add_argument("--predictive-sugar-json", type=Path, required=True)
    p.add_argument("--predictive-hdbscan-json", type=Path, required=True)
    p.add_argument("--truth-root", type=Path, required=True)
    p.add_argument("--ranker-source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(v31.v22.sha(a.ranker_source) == v31.v24.RANKER_SOURCE_SHA, "#839 ranker source changed")

    roots = {"sugar": a.sugar_root, "hdbscan": a.hdbscan_root}
    pred_paths = {"sugar": a.predictive_sugar_json, "hdbscan": a.predictive_hdbscan_json}
    predictive: dict[str, dict[str, Any]] = {}

    for route in v31.v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / "V22_PRETRUTH_FEATURE_MANIFEST.json").read_text())
        fp = json.loads((root / "family_memberships.json").read_text())
        require(meta["truth_accessed"] is False and meta["feature_dimension"] == FEATURE_DIM and fp["truth_accessed"] is False, f"{route} invalid pretruth payload")
        X = np.load(root / "features.npy", allow_pickle=False)
        C = np.load(root / "centroids.npy", allow_pickle=False)
        require(X.shape[1] == FEATURE_DIM and C.shape[1] == 8, f"{route} array shape changed")
        require(v31.v22.array_sha(X) == meta["feature_sha256"] and v31.v22.array_sha(C) == meta["centroid_sha256"], f"{route} array identity changed")

        pr = json.loads(pred_paths[route].read_text())
        require(pr["truth_accessed"] is False and pr["route"] == route and pr["candidate_count"] == EXPECTED_COUNTS[route], f"{route} invalid predictive pretruth")
        require(pr["parameter_search"] is False and pr["membership_changed"] is False, f"{route} predictive search/membership changed")
        require(pr["blind_exclusion"] == [20.0, 55.0] and pr["target_information_access"] is False and pr["target_region_events_accessed"] is False, f"{route} predictive firewall changed")
        po = list(map(str, pr["predictive_order"]))
        ids = list(map(str, meta["family_ids"]))
        require(len(po) == len(set(po)) == len(ids) and set(po) == set(ids), f"{route} predictive order universe mismatch")
        require(order_sha(po) == pr["predictive_order_sha256"], f"{route} predictive order hash mismatch")
        predictive[route] = pr

    truth: dict[tuple[str, int], dict[str, str]] = {}
    frozen_eval: dict[tuple[str, int], dict[str, Any]] = {}
    for route, year in v31.v24.PANELS:
        truth[(route, year)] = json.loads((a.truth_root / f"truth_{route}_{year}.json").read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f"evaluation_{route}_{year}.json").read_text())

    ranker = v31.v22.load_module(a.ranker_source, "frozen_839_v61")
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    route_offsets: dict[str, tuple[int, int]] = {}
    cursor = 0

    for route in v31.v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / "V22_PRETRUTH_FEATURE_MANIFEST.json").read_text())
        fp = json.loads((root / "family_memberships.json").read_text())
        ids = list(map(str, meta["family_ids"]))
        fams = fp["families"]
        require([str(f["family_id"]) for f in fams] == ids, f"{route} family order changed")
        X = np.load(root / "features.npy", allow_pickle=False)
        C = np.load(root / "centroids.npy", allow_pickle=False)
        by = {y: truth[(route, y)] for y in v31.v24.YEARS}
        eligible = v31.v22.eligible_from_year_truth(by)
        hidden: dict[str, str] = {}
        hidden.update(by[2013])
        hidden.update(by[2014])
        base = [v31.v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        rg: list[str] = []
        for i, (f, t) in enumerate(zip(fams, base)):
            label = t["best_label"]
            rg.append(("SHOWER/" + str(label)) if label is not None else f"NEG/{route}/{ids[i]}")
            if not t["positive"] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v31.v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13))
            y14.append(float(q14))
        route_offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        y13s.append(np.asarray(y13, float))
        y14s.append(np.asarray(y14, float))
        groups.extend(rg)
        route_data[route] = {"meta": meta, "fams": fams, "ids": ids, "centroids": C}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM) and len(y13all) == len(y14all) == len(groups) == cursor, "stacked v31 input mismatch")

    folds = np.asarray([v31.v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    fold_diag: list[dict[str, Any]] = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f"empty fold {fold}")
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f"group leakage fold {fold}")
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]
        Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        annual_diag: dict[str, Any] = {}
        for year, yall, out in ((2013, y13all, margin13), (2014, y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f"{year} fold {fold} lacks positive/nonpositive references")
            P = Ztr[pos]
            N = Ztr[neg]
            for j, global_i in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                out[global_i] = dneg - dpos
            annual_diag[str(year)] = {"positive_references": int(pos.sum()), "nonpositive_references": int(neg.sum())}
        fold_diag.append({"fold": fold, "train_examples": int(tr.sum()), "test_examples": int(te.sum()), "zero_variance_features": int(np.sum(sd == 0.0)), "annual_references": annual_diag})

    combined = np.minimum(margin13, margin14)
    require(np.all(np.isfinite(combined)), "nonfinite combined v31 local-geometry margin")

    v31_orders: dict[str, list[str]] = {}
    v61_orders: dict[str, list[str]] = {}
    order_diag: dict[str, Any] = {}
    v31_control: list[dict[str, Any]] = []

    for route in v31.v24.ROUTES:
        lo, hi = route_offsets[route]
        rd = route_data[route]
        ids = rd["ids"]
        scores = combined[lo:hi]
        tie = [(int(rd["meta"]["tie_rank"][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(scores, rd["centroids"], 0.8, 1.0, tie)
        local_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd["meta"]["v19_order"]))
        v31_order = list(v31.v19.fusion_orders(local_order, v19_order)["rank_sum"])
        pred_order = list(map(str, predictive[route]["predictive_order"]))
        v61_order = rank_sum(v31_order, pred_order)
        v31_orders[route] = v31_order
        v61_orders[route] = v61_order
        order_diag[route] = {
            "annual_margin_2013_sha256": v31.v22.array_sha(margin13[lo:hi]),
            "annual_margin_2014_sha256": v31.v22.array_sha(margin14[lo:hi]),
            "combined_margin_sha256": v31.v22.array_sha(scores),
            "v31_local_diversity_order_sha256": order_sha(local_order),
            "v31_fused_order_sha256": order_sha(v31_order),
            "predictive_order_sha256": order_sha(pred_order),
            "v61_equal_rank_sum_order_sha256": order_sha(v61_order),
            "v61_fusion": "equal 1-based rank-sum of exact v31 final order and exact pretruth predictive order; tie by v31 rank then family_id",
        }

        v31_ranked = v31.v22.rerank(rd["fams"], v31_order)
        for year in v31.v24.YEARS:
            budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
            cur = v31.v22.evaluate(v31_ranked, truth[(route, year)], budget)
            exp = EXPECTED_V31[(route, year)]
            require(abs(float(cur["macro_f1"]) - float(exp[0])) < 1e-12 and int(cur["recovered_f1_gt_0_5"]) == int(exp[1]), f"{route} {year} v31 historical control changed")
            v31_control.append({"comparator": route, "year": year, **cur})

    panels: list[dict[str, Any]] = []
    for route, year in v31.v24.PANELS:
        rd = route_data[route]
        ranked = v31.v22.rerank(rd["fams"], v61_orders[route])
        budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
        cur = v31.v22.evaluate(ranked, truth[(route, year)], budget)
        lit = frozen_eval[(route, year)]["comparator_summary"]
        cm = float(cur["macro_f1"])
        cr = int(cur["recovered_f1_gt_0_5"])
        lm = float(lit["macro_f1"])
        lr = int(lit["recovered_f1_gt_0_5"])
        panels.append({
            "comparator": route,
            "year": year,
            "budget": budget,
            "candidate_macro_f1": cm,
            "literature_macro_f1": lm,
            "candidate_recovered_f1_gt_0_5": cr,
            "literature_recovered_f1_gt_0_5": lr,
            "macro_f1_ratio": cm / lm if lm else float("inf"),
            "recovery_ratio": cr / lr if lr else float("inf"),
            "superiority_pair_pass": bool(cm > lm and cr >= lr),
        })

    wins = sum(int(r["superiority_pair_pass"]) for r in panels)
    passed = bool(wins == 4)
    result = {
        "scientific_stage": "EXPOSED_SONOTACO_V61_GMN_MOTIVATED_PREDICTIVE_CONSISTENCY_FUSION_V1",
        "verdict": "PASS_V61_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT" if passed else "FAIL_V61_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT",
        "motivation": "binding target-excluded GMN predictive-consistency diagnostic PASS",
        "sole_scientific_change": "equal rank-sum exact v31 final route order with exact label-free candidate-internal predictive-consistency order frozen pretruth",
        "panel_wins": wins,
        "panels": panels,
        "v31_historical_control": v31_control,
        "fold_diagnostics": fold_diag,
        "order_diagnostics": order_diag,
        "candidate_membership_changed": False,
        "pretruth_71d_features_changed": False,
        "predictive_order_truth_accessed": False,
        "predictive_parameter_search": False,
        "fusion_weight_search": False,
        "rank_product_search": False,
        "post_fusion_diversity": False,
        "budget_specific_rule": False,
        "source_quota_selected": False,
        "post_result_rescue_authorized": False,
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "blind_exclusion": [20.0, 55.0],
    }
    path = a.output / "V61_PREDICTIVE_CONSISTENCY_FUSION_RESULT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "V61_PREDICTIVE_CONSISTENCY_FUSION_RESULT.md").write_text(
        "# OrbitTrace v61 predictive-consistency fusion\n\n"
        f"- verdict: `{result['verdict']}`\n"
        f"- literature panel wins: `{wins}/4`\n"
        + "\n".join(
            f"- {r['comparator']} {r['year']}: F1 `{r['candidate_macro_f1']:.12f}` vs `{r['literature_macro_f1']:.12f}`; recovered `{r['candidate_recovered_f1_gt_0_5']}` vs `{r['literature_recovered_f1_gt_0_5']}`; pass `{r['superiority_pair_pass']}`"
            for r in panels
        )
        + "\n"
    )
    print(json.dumps({"verdict": result["verdict"], "panel_wins": wins, "panels": panels}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
