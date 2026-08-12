#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
FEATURE_COLUMNS = tuple(range(1, 11)) + tuple(range(14, 21)) + tuple(range(28, 34))
FEATURE_DIM = 23
RECOVERY = 0.5
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
EXPECTED_COUNTS = {"sugar": 267, "hdbscan": 229}
EXPECTED_PARENT_ORDER_SHA = {
    "sugar": "5b3d27e11079f36148bbfb8bfdab60882fae380143fcfd84c6dc290c53295aae",
    "hdbscan": "85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d",
}
V31_PARENT_METRICS = {
    ("sugar", 2013): (0.2719801488280529, 16),
    ("sugar", 2014): (0.31529041952487225, 17),
    ("hdbscan", 2013): (0.14888037368183737, 9),
    ("hdbscan", 2014): (0.15198123772301594, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(",", ":")).encode())
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(map(str, order)).encode()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def roots_from_args(a: argparse.Namespace) -> dict[str, Path]:
    return {"sugar": a.sugar_root, "hdbscan": a.hdbscan_root}


def run_pretruth(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    roots = roots_from_args(a)
    routes: dict[str, Any] = {}
    for route in ROUTES:
        root = roots[route]
        meta = json.loads((root / "V22_PRETRUTH_FEATURE_MANIFEST.json").read_text())
        memberships = json.loads((root / "family_memberships.json").read_text())
        require(meta["truth_accessed"] is False and memberships["truth_accessed"] is False, f"{route} pretruth firewall failed")
        require(int(meta["feature_dimension"]) == 71, f"{route} source feature dimension changed")
        require(meta["feature_blocks"] == {"raw_839": 34, "relative_noncat_839": 30, "rank_percentiles": 3, "consensus_graph": 4}, f"{route} feature-block layout changed")
        ids = list(map(str, meta["family_ids"]))
        require(len(ids) == EXPECTED_COUNTS[route] and len(ids) == len(set(ids)), f"{route} family count changed")
        require([str(f["family_id"]) for f in memberships["families"]] == ids, f"{route} family order changed")

        x71 = np.load(root / "features.npy", allow_pickle=False)
        centroids = np.load(root / "centroids.npy", allow_pickle=False)
        require(x71.shape == (len(ids), 71) and centroids.shape == (len(ids), 8), f"{route} source array shape changed")
        require(v22.array_sha(x71) == meta["feature_sha256"], f"{route} source feature identity changed")
        require(v22.array_sha(centroids) == meta["centroid_sha256"], f"{route} centroid identity changed")
        require(np.isfinite(x71).all() and np.isfinite(centroids).all(), f"{route} nonfinite source array")

        x23 = np.asarray(x71[:, FEATURE_COLUMNS], dtype=np.float64)
        require(x23.shape == (len(ids), FEATURE_DIM) and np.isfinite(x23).all(), f"{route} intrinsic matrix invalid")
        out_dir = a.output / route
        out_dir.mkdir(parents=True, exist_ok=True)
        np.save(out_dir / "intrinsic_features.npy", x23, allow_pickle=False)
        route_manifest = {
            "comparator": route,
            "candidate_count": len(ids),
            "family_ids": ids,
            "feature_dimension": FEATURE_DIM,
            "selected_zero_based_columns": list(FEATURE_COLUMNS),
            "selected_blocks": {
                "intrinsic_structural_raw_839": list(range(1, 11)),
                "cohesion_raw_839": list(range(14, 21)),
                "centroid_neighbor_raw_839": list(range(28, 34)),
            },
            "source_feature_dimension": 71,
            "source_feature_blocks": meta["feature_blocks"],
            "source_feature_sha256": meta["feature_sha256"],
            "source_centroid_sha256": meta["centroid_sha256"],
            "intrinsic_feature_sha256": array_sha(x23),
            "v19_order_sha256": order_sha(list(map(str, meta["v19_order"]))),
            "truth_accessed": False,
            "feature_search": False,
            "column_search": False,
            "imputation": False,
            "representation_weighting": False,
            "candidate_membership_changed": False,
            "target_information_access": False,
            "target_region_events_accessed": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
            "blind_exclusion": [20.0, 55.0],
        }
        route_manifest_sha = dump(out_dir / "V62_INTRINSIC_PRETRUTH_MANIFEST.json", route_manifest)
        routes[route] = {
            "candidate_count": len(ids),
            "intrinsic_feature_sha256": route_manifest["intrinsic_feature_sha256"],
            "route_manifest_sha256": route_manifest_sha,
            "v19_order_sha256": route_manifest["v19_order_sha256"],
        }

    overall = {
        "scientific_stage": "V62_INTRINSIC_REPRESENTATION_PRETRUTH",
        "feature_dimension": FEATURE_DIM,
        "selected_zero_based_columns": list(FEATURE_COLUMNS),
        "routes": routes,
        "truth_accessed": False,
        "feature_search": False,
        "column_search": False,
        "imputation": False,
        "representation_weighting": False,
        "candidate_membership_changed": False,
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
    }
    overall_sha = dump(a.output / "V62_INTRINSIC_PRETRUTH.json", overall)
    print(json.dumps({"pretruth_sha256": overall_sha, "routes": routes}, indent=2, sort_keys=True))
    return 0


def load_intrinsic(pretruth_root: Path, route: str, source_root: Path) -> tuple[np.ndarray, dict[str, Any], dict[str, Any], np.ndarray]:
    pm = json.loads((pretruth_root / route / "V62_INTRINSIC_PRETRUTH_MANIFEST.json").read_text())
    meta = json.loads((source_root / "V22_PRETRUTH_FEATURE_MANIFEST.json").read_text())
    memberships = json.loads((source_root / "family_memberships.json").read_text())
    x = np.load(pretruth_root / route / "intrinsic_features.npy", allow_pickle=False)
    c = np.load(source_root / "centroids.npy", allow_pickle=False)
    require(pm["truth_accessed"] is False and meta["truth_accessed"] is False and memberships["truth_accessed"] is False, f"{route} pretruth truth flag changed")
    require(pm["selected_zero_based_columns"] == list(FEATURE_COLUMNS) and int(pm["feature_dimension"]) == FEATURE_DIM, f"{route} selected columns changed")
    require(array_sha(x) == pm["intrinsic_feature_sha256"], f"{route} intrinsic feature identity changed")
    require(v22.array_sha(c) == meta["centroid_sha256"], f"{route} centroid identity changed")
    ids = list(map(str, meta["family_ids"]))
    require(x.shape == (len(ids), FEATURE_DIM) and c.shape == (len(ids), 8), f"{route} sealed array shape changed")
    require(pm["family_ids"] == ids and [str(f["family_id"]) for f in memberships["families"]] == ids, f"{route} family order changed")
    return x, meta, memberships, c


def run_evaluate(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    overall = json.loads((a.pretruth_root / "V62_INTRINSIC_PRETRUTH.json").read_text())
    require(overall["truth_accessed"] is False and overall["selected_zero_based_columns"] == list(FEATURE_COLUMNS), "v62 pretruth seal invalid")
    require(overall["feature_search"] is False and overall["column_search"] is False, "v62 feature search flag invalid")

    parent = json.loads(a.parent_orders.read_text())
    require(parent["verdict"] == "PASS_EXACT_V31_PARENT_ORDER_RECONSTRUCTION" and parent["scientific_change"] is False, "v31 parent-order provenance invalid")
    for route in ROUTES:
        require(parent["routes"][route]["v31_fused_order_sha256"] == EXPECTED_PARENT_ORDER_SHA[route], f"{route} v31 parent order hash changed")

    roots = roots_from_args(a)
    truth: dict[tuple[str, int], Any] = {}
    frozen_eval: dict[tuple[str, int], Any] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((a.truth_root / f"truth_{route}_{year}.json").read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f"evaluation_{route}_{year}.json").read_text())

    ranker = v22.load_module(a.ranker_source, "frozen_839_v62_intrinsic_geometry")
    route_data: dict[str, Any] = {}
    xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0

    for route in ROUTES:
        root = roots[route]
        x, meta, fp, centroids = load_intrinsic(a.pretruth_root, route, root)
        ids = list(map(str, meta["family_ids"]))
        fams = fp["families"]
        by = {year: truth[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden: dict[str, Any] = {}
        hidden.update(by[2013])
        hidden.update(by[2014])
        base = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        route_groups: list[str] = []
        for family_id, f, t in zip(ids, fams, base):
            label = t["best_label"]
            route_groups.append(("SHOWER/" + str(label)) if label is not None else f"NEG/{route}/{family_id}")
            if not t["positive"] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13))
            y14.append(float(q14))

        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        xs.append(x)
        y13s.append(np.asarray(y13, dtype=float))
        y14s.append(np.asarray(y14, dtype=float))
        groups.extend(route_groups)
        route_data[route] = {"meta": meta, "fams": fams, "ids": ids, "centroids": centroids}

    xall = np.vstack(xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    require(xall.shape == (cursor, FEATURE_DIM) and len(groups) == cursor, "stacked intrinsic input mismatch")
    folds = np.asarray([v22.v1.deterministic_fold(str(g)) for g in groups], dtype=int)
    require(set(folds.tolist()) == set(range(5)), "strict five-fold assignment changed")

    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    fold_diag: list[dict[str, Any]] = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f"empty fold {fold}")
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f"group leakage fold {fold}")
        mu = np.mean(xall[tr], axis=0)
        sd = np.std(xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (xall[tr] - mu[None, :]) / scale[None, :]
        zte = (xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        annual_diag: dict[str, Any] = {}
        for year, yall, out in ((2013, y13all, margin13), (2014, y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f"{year} fold {fold} lacks positive/nonpositive references")
            p = ztr[pos]
            n = ztr[neg]
            for j, global_i in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(p - zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(n - zte[j][None, :], axis=1)))
                out[global_i] = dneg - dpos
            annual_diag[str(year)] = {"positive_references": int(pos.sum()), "nonpositive_references": int(neg.sum())}
        fold_diag.append({
            "fold": fold,
            "train_examples": int(tr.sum()),
            "test_examples": int(te.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "annual_references": annual_diag,
        })

    combined = np.minimum(margin13, margin14)
    require(np.isfinite(combined).all(), "nonfinite v62 combined margin")

    variants: dict[str, list[dict[str, Any]]] = {}
    order_diag: dict[str, Any] = {}
    parent_controls: list[dict[str, Any]] = []
    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd["ids"]
        scores = combined[lo:hi]
        tie = [(int(rd["meta"]["tie_rank"][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(scores, rd["centroids"], DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
        local_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd["meta"]["v19_order"]))
        fused = list(v19.fusion_orders(local_order, v19_order)["rank_sum"])
        variants[route] = v22.rerank(rd["fams"], fused)
        order_diag[route] = {
            "annual_margin_2013_sha256": v22.array_sha(margin13[lo:hi]),
            "annual_margin_2014_sha256": v22.array_sha(margin14[lo:hi]),
            "combined_margin_sha256": v22.array_sha(scores),
            "local_diversity_order_sha256": order_sha(local_order),
            "fused_order_sha256": order_sha(fused),
            "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
            "fusion": "equal rank-sum with exact v19",
        }

        parent_order = list(map(str, parent["routes"][route]["v31_fused_order"]))
        require(order_sha(parent_order) == EXPECTED_PARENT_ORDER_SHA[route], f"{route} parent order payload changed")
        parent_ranked = v22.rerank(rd["fams"], parent_order)
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
            cur = v22.evaluate(parent_ranked, truth[(route, year)], budget)
            exp = V31_PARENT_METRICS[(route, year)]
            require(abs(float(cur["macro_f1"]) - exp[0]) < 1e-12 and int(cur["recovered_f1_gt_0_5"]) == exp[1], f"{route} {year} v31 parent control changed")
            parent_controls.append({"comparator": route, "year": year, **cur})

    panels: list[dict[str, Any]] = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]["candidate_budget"]["comparator_budget"])
        cur = v22.evaluate(variants[route], truth[(route, year)], budget)
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
            "parent_v31_macro_f1": V31_PARENT_METRICS[(route, year)][0],
            "parent_v31_recovered_f1_gt_0_5": V31_PARENT_METRICS[(route, year)][1],
            "superiority_pair_pass": bool(cm > lm and cr >= lr),
        })

    wins = sum(int(p["superiority_pair_pass"]) for p in panels)
    passed = wins == 4
    result = {
        "scientific_stage": "EXPOSED_SONOTACO_V62_INTRINSIC_STRICT_OOF_LOCAL_GEOMETRY_V1",
        "verdict": "PASS_V62_INTRINSIC_LOCAL_GEOMETRY_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS" if passed else "FAIL_V62_INTRINSIC_LOCAL_GEOMETRY_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS",
        "first_valid_outcome_binding": True,
        "sole_scientific_change": "v31 71D representation replaced by exact pretruth 23D intrinsic raw-URC subset validated by target-excluded GMN",
        "parent_method": "v31 strict-OOF local-geometry margin",
        "feature_dimension": FEATURE_DIM,
        "selected_zero_based_columns": list(FEATURE_COLUMNS),
        "recovery_f1_threshold": RECOVERY,
        "nearest_k": 1,
        "distance": "ordinary Euclidean across all 23 fold-training standardized intrinsic dimensions",
        "scaling": "fold-training mean and population std; zero std -> 1.0",
        "annual_margin": "d_nonpositive-d_positive",
        "annual_combiner": "min(margin_2013,margin_2014)",
        "strict_whole_shower_oof": True,
        "candidate_membership_changed": False,
        "source_pretruth_payload_immutable": True,
        "representation_changed_from_parent": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "one equal rank-sum with exact v19",
        "panel_wins": wins,
        "panels": panels,
        "v31_parent_controls": parent_controls,
        "fold_diagnostics": fold_diag,
        "order_diagnostics": order_diag,
        "k_search": False,
        "metric_search": False,
        "scaling_search": False,
        "feature_search": False,
        "column_search": False,
        "representation_weight_search": False,
        "threshold_search": False,
        "annual_reference_search": False,
        "annual_combiner_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "source_quota_selected": False,
        "post_result_rescue": False,
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "blind_exclusion": [20.0, 55.0],
    }
    dump(a.output / "V62_INTRINSIC_LOCAL_GEOMETRY_OOF_RESULT.json", result)
    print(json.dumps({"verdict": result["verdict"], "panel_wins": wins, "panels": panels}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    pp = sub.add_parser("pretruth")
    pp.add_argument("--sugar-root", type=Path, required=True)
    pp.add_argument("--hdbscan-root", type=Path, required=True)
    pp.add_argument("--output", type=Path, required=True)
    pe = sub.add_parser("evaluate")
    pe.add_argument("--pretruth-root", type=Path, required=True)
    pe.add_argument("--sugar-root", type=Path, required=True)
    pe.add_argument("--hdbscan-root", type=Path, required=True)
    pe.add_argument("--truth-root", type=Path, required=True)
    pe.add_argument("--ranker-source", type=Path, required=True)
    pe.add_argument("--parent-orders", type=Path, required=True)
    pe.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    return run_pretruth(a) if a.mode == "pretruth" else run_evaluate(a)


if __name__ == "__main__":
    raise SystemExit(main())
