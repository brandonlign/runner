#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED = (226, 1075, 3203, 4504)
FEATURE_DIM = 34
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
DIVERSITY = {"lambda": 0.8, "scale": 1.0}
OPTIMIZER = {"method": "L-BFGS-B", "maxiter": 10000, "ftol": 1e-12, "gtol": 1e-8}
QUALITY_CONTROL = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "qualified_matches": 256,
    "top100_dominant_precision": 0.7645689180574315,
    "mrr": 0.019037817654898162,
}
SHARE_CONTROL = {
    "recovered_at_25": 22,
    "recovered_at_50": 43,
    "recovered_at_100": 80,
    "recovered_at_500": 171,
    "qualified_matches": 256,
    "top100_dominant_precision": 0.8075287489258385,
    "mrr": 0.02016666446026534,
}


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(",", ":")).encode())
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def canonical_sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def trimmed(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def assert_metrics(m: dict[str, Any], expected: dict[str, Any], name: str) -> None:
    for k, v in expected.items():
        if isinstance(v, float):
            req(abs(float(m[k]) - v) < 1e-12, f"{name} mismatch {k}: {m[k]} != {v}")
        else:
            req(int(m[k]) == int(v), f"{name} mismatch {k}: {m[k]} != {v}")


def fit_listwise(x_train: np.ndarray, r_train: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, dict[str, Any]]:
    req(x_train.ndim == 2 and x_train.shape[1] == FEATURE_DIM, "listwise train feature shape changed")
    req(r_train.ndim == 1 and r_train.shape[0] == x_train.shape[0], "listwise train target shape changed")
    req(np.isfinite(x_train).all() and np.isfinite(r_train).all(), "nonfinite listwise training input")
    req(np.all(r_train >= 0.0), "negative representative-share target")
    mass = float(np.sum(r_train))
    req(mass > 0.0, "empty listwise target mass")

    mean = np.mean(x_train, axis=0)
    scale = np.std(x_train, axis=0, ddof=0)
    scale = np.where(scale == 0.0, 1.0, scale)
    z = (x_train - mean) / scale
    p = r_train / mass
    req(abs(float(np.sum(p)) - 1.0) < 1e-12, "listwise target distribution does not sum to one")

    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        scores = z @ beta
        lse = float(logsumexp(scores))
        probs = np.exp(scores - lse)
        loss = float(-np.dot(p, scores) + lse)
        grad = z.T @ (probs - p)
        return loss, np.asarray(grad, dtype=float)

    beta0 = np.zeros(FEATURE_DIM, dtype=float)
    result = minimize(
        objective,
        beta0,
        method=OPTIMIZER["method"],
        jac=True,
        options={
            "maxiter": OPTIMIZER["maxiter"],
            "ftol": OPTIMIZER["ftol"],
            "gtol": OPTIMIZER["gtol"],
        },
    )
    req(bool(result.success), f"listwise optimizer failed before scientific result: status={result.status} message={result.message}")
    beta = np.asarray(result.x, dtype=float)
    loss, grad = objective(beta)
    train_scores = z @ beta
    logz = float(logsumexp(train_scores))
    req(np.isfinite(beta).all() and np.isfinite(mean).all() and np.isfinite(scale).all(), "nonfinite fitted listwise parameters")
    req(math.isfinite(loss) and np.isfinite(grad).all() and math.isfinite(logz), "nonfinite fitted listwise objective")
    diagnostic = {
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "iterations": int(result.nit),
        "function_evaluations": int(result.nfev),
        "final_loss": loss,
        "gradient_l2": float(np.linalg.norm(grad)),
        "beta_l2": float(np.linalg.norm(beta)),
        "training_target_mass": mass,
        "training_log_partition": logz,
    }
    return beta, mean, scale, logz, diagnostic


def score_listwise(x_test: np.ndarray, beta: np.ndarray, mean: np.ndarray, scale: np.ndarray, train_logz: float) -> np.ndarray:
    z = (x_test - mean) / scale
    out = z @ beta - float(train_logz)
    req(np.isfinite(out).all(), "nonfinite held-out listwise scores")
    return np.asarray(out, dtype=float)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-result-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "#839 quality source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "v8 development result changed")
    req(sha(a.p19_result_json) == P19_RESULT_SHA and sha(a.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 inputs changed")
    req(sha(a.p20_result_json) == P20_RESULT_SHA and sha(a.p20_prelabel_json) == P20_PRELABEL_SHA, "P20 inputs changed")
    qmod = load_module(a.quality_source, "frozen_839_listwise_share")

    p19 = json.loads(a.p19_prelabel_json.read_text())
    p20 = json.loads(a.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    s19 = p19["soft_families"]
    s20 = p20["soft_families"]
    hard_order = list(map(str, p19["hard_order"]))
    fams = hard + s19 + s20
    req((len(hard), len(s19), len(s20), len(fams)) == EXPECTED, "candidate universe changed")
    ids = [str(f["family_id"]) for f in fams]
    req(len(set(ids)) == len(ids), "family IDs collide")
    source = {str(f["family_id"]): "hard" for f in hard}
    source.update({str(f["family_id"]): "p19" for f in s19})
    source.update({str(f["family_id"]): "p20" for f in s20})
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-gmn-listwise-representative-share-oof-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, labels, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), "GMN years changed")
    req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month sources changed")

    eligible = qmod.v1.eligible_labels(labels)
    by = {str(f["family_id"]): f for f in fams}
    truths = {fid: qmod.v1.family_truth(by[fid], labels, eligible) for fid in ids}
    cm = qmod.centroid_matrix(fams)
    lookup = qmod.v2.event_lookup(scan)
    nf = qmod.neighbor_features(cm)

    x_rows: list[list[float]] = []
    for i, f in enumerate(fams):
        fid = str(f["family_id"])
        src = source[fid]
        source_feats = [float(src == "hard"), float(src == "p19"), float(src == "p20")]
        p20_feats = [
            float(f.get("p20_cross_year_distance", 0.0)),
            math.log1p(max(int(f.get("p20_min_anchor_count", 0)), 0)),
            float(f.get("p20_min_bin_strength", 0.0)),
            float(f.get("p20_min_quartet_score", 0.0)),
        ]
        x_rows.append(
            qmod.v1.structural_features(f, hard_rank)
            + qmod.v2.cohesion_features(f, lookup, support, base)
            + source_feats
            + p20_feats
            + nf[i].tolist()
        )
    x = np.asarray(x_rows, dtype=float)
    req(x.shape == (len(fams), FEATURE_DIM) and np.isfinite(x).all(), "exact #839 feature matrix invalid")

    feature_names = (
        list(qmod.v1.FEATURE_NAMES)
        + list(qmod.v2.COHESION_FEATURE_NAMES)
        + ["source_hard", "source_p19", "source_p20"]
        + ["p20_cross_year_distance", "log1p_p20_min_anchor_count", "p20_min_bin_strength", "p20_min_quartet_score"]
        + ["neighbor_log_count_0p25", "neighbor_log_count_0p5", "neighbor_log_count_1p0", "neighbor_log_count_1p5", "neighbor_nearest_distance", "neighbor_median_first5_distance"]
    )
    req(len(feature_names) == FEATURE_DIM, "feature-name schema changed")

    q_abs = np.asarray([
        float(truths[fid]["f1"]) if truths[fid]["positive"] else 0.0
        for fid in ids
    ], dtype=float)
    req(np.isfinite(q_abs).all() and np.all(q_abs >= 0.0), "absolute #839 target invalid")
    groups = [
        ("SHOWER/" + str(truths[fid]["best_label"]))
        if truths[fid]["best_label"] is not None
        else ("NEG/" + fid)
        for fid in ids
    ]
    folds = np.asarray([qmod.v1.deterministic_fold(g) for g in groups], dtype=int)
    weights = qmod.grouped_weights(groups)
    tie = [(hard_rank.get(fid, 999999), fid) for fid in ids]

    # Exact #839 quality/diversity OOF control.
    oof_abs = np.zeros(len(ids), dtype=float)
    fold_membership: list[dict[str, Any]] = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        req(tr.any() and te.any(), f"empty #839 control fold {fold}")
        train_groups = {groups[i] for i in np.where(tr)[0]}
        test_groups = {groups[i] for i in np.where(te)[0]}
        req(train_groups.isdisjoint(test_groups), f"#839 group leakage fold {fold}")
        m = qmod.model()
        m.fit(x[tr], q_abs[tr], sample_weight=weights[tr])
        oof_abs[te] = m.predict(x[te])
        fold_membership.append({
            "fold": fold,
            "train": int(tr.sum()),
            "test": int(te.sum()),
            "train_groups": len(train_groups),
            "test_groups": len(test_groups),
        })
    req(np.isfinite(oof_abs).all(), "#839 control OOF prediction invalid")
    q_idx = qmod.diversity_order(oof_abs, cm, DIVERSITY["lambda"], DIVERSITY["scale"], tie)
    q_order = [ids[i] for i in q_idx]
    q_metrics = qmod.v1.monotone_metrics(fams, q_order, truths, eligible)
    assert_metrics(q_metrics, QUALITY_CONTROL, "#839 quality/diversity control")

    # Exact frozen #1194 representative-share target.
    group_total: dict[str, float] = {}
    for g, q in zip(groups, q_abs):
        group_total[g] = group_total.get(g, 0.0) + float(q)
    y_share = np.zeros(len(ids), dtype=float)
    for i, (g, q) in enumerate(zip(groups, q_abs)):
        total = group_total[g]
        if g.startswith("SHOWER/") and total > 0.0:
            y_share[i] = float(q) / total
    req(np.isfinite(y_share).all() and np.all(y_share >= 0.0), "representative-share target invalid")
    positive_shower_groups = sorted(g for g, total in group_total.items() if g.startswith("SHOWER/") and total > 0.0)
    for g in positive_shower_groups:
        idx = [i for i, gg in enumerate(groups) if gg == g]
        req(abs(float(np.sum(y_share[idx])) - 1.0) < 1e-12, f"representative-share group mass changed for {g}")

    # Exact #1194 pointwise ExtraTrees OOF control.
    oof_share = np.zeros(len(ids), dtype=float)
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f"#1194 group leakage fold {fold}")
        m = qmod.model()
        m.fit(x[tr], y_share[tr], sample_weight=weights[tr])
        oof_share[te] = m.predict(x[te])
    req(np.isfinite(oof_share).all(), "#1194 control OOF prediction invalid")
    share_idx = qmod.diversity_order(oof_share, cm, DIVERSITY["lambda"], DIVERSITY["scale"], tie)
    share_order = [ids[i] for i in share_idx]
    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)
    assert_metrics(share_metrics, SHARE_CONTROL, "#1194 representative-share control")

    # Sole frozen successor: one whole-list softmax objective per strict OOF fold.
    oof_listwise = np.zeros(len(ids), dtype=float)
    optimizer_folds: list[dict[str, Any]] = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        train_groups = {groups[i] for i in np.where(tr)[0]}
        test_groups = {groups[i] for i in np.where(te)[0]}
        req(train_groups.isdisjoint(test_groups), f"listwise group leakage fold {fold}")
        beta, mean, scale, train_logz, diag = fit_listwise(x[tr], y_share[tr])
        oof_listwise[te] = score_listwise(x[te], beta, mean, scale, train_logz)
        diag.update({
            "fold": fold,
            "train": int(tr.sum()),
            "test": int(te.sum()),
            "train_groups": len(train_groups),
            "test_groups": len(test_groups),
            "coefficient_sha256": array_sha(beta),
            "scaler_mean_sha256": array_sha(mean),
            "scaler_scale_sha256": array_sha(scale),
        })
        optimizer_folds.append(diag)
    req(np.isfinite(oof_listwise).all(), "listwise OOF scores invalid")

    list_idx = qmod.diversity_order(oof_listwise, cm, DIVERSITY["lambda"], DIVERSITY["scale"], tie)
    list_order = [ids[i] for i in list_idx]
    list_metrics = qmod.v1.monotone_metrics(fams, list_order, truths, eligible)

    passed = bool(
        int(list_metrics["recovered_at_100"]) > 80
        and int(list_metrics["recovered_at_50"]) >= 43
        and int(list_metrics["recovered_at_25"]) >= 22
        and int(list_metrics["recovered_at_500"]) >= 171
        and float(list_metrics["top100_dominant_precision"]) >= SHARE_CONTROL["top100_dominant_precision"]
        and float(list_metrics["mrr"]) >= SHARE_CONTROL["mrr"]
        and int(list_metrics["qualified_matches"]) == 256
    )

    full = {
        "verdict": "NOT_FROZEN_GMN_LISTWISE_REPRESENTATIVE_SHARE_FAIL",
        "model_payload_sha256": None,
    }
    if passed:
        beta, mean, scale, full_logz, diag = fit_listwise(x, y_share)
        payload = {
            "model": "linear_full_list_softmax_cross_entropy",
            "feature_dimension": FEATURE_DIM,
            "feature_names": feature_names,
            "scaler_mean": [float(v) for v in mean],
            "scaler_scale": [float(v) for v in scale],
            "coefficients": [float(v) for v in beta],
            "training_log_partition": float(full_logz),
            "optimizer": OPTIMIZER,
            "optimizer_diagnostic": diag,
            "deployment_diversity": DIVERSITY,
        }
        payload_sha = canonical_sha(payload)
        (a.output / "FULL_MODEL_PAYLOAD.json").write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
        full = {
            "verdict": "PASS_GMN_LISTWISE_REPRESENTATIVE_SHARE_FULL_MODEL_FREEZE",
            "model_payload_sha256": payload_sha,
            "feature_matrix_sha256": array_sha(x),
            "feature_name_sha256": hashlib.sha256("\n".join(feature_names).encode()).hexdigest(),
            "representative_share_target_sha256": array_sha(y_share),
            "training_examples": len(ids),
            "positive_shower_groups": len(positive_shower_groups),
            "deployment_diversity": DIVERSITY,
            "sonotaco_2013_2014_access": False,
            "target_information_access": False,
            "target_region_events_accessed": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
            "blind_exclusion": list(BLIND),
        }

    result = {
        "stage": "GMN_LISTWISE_REPRESENTATIVE_SHARE_OOF_V1",
        "verdict": "PASS_GMN_LISTWISE_REPRESENTATIVE_SHARE_OOF_V1" if passed else "FAIL_GMN_LISTWISE_REPRESENTATIVE_SHARE_OOF_V1",
        "scientific_role": "GMN_2022_2023_TARGET_EXCLUDED_METHOD_DEVELOPMENT_ONLY",
        "sole_scientific_change": "replace #1194 pointwise ExtraTrees squared-error fit with one parameter-free linear full-list softmax cross-entropy objective; representative-share target/features/folds/diversity/evaluator remain frozen",
        "candidate_counts": {"hard": len(hard), "p19": len(s19), "p20": len(s20), "union": len(fams)},
        "eligible_labels": len(eligible),
        "positive_shower_groups": len(positive_shower_groups),
        "feature_dimension": FEATURE_DIM,
        "feature_names": feature_names,
        "feature_matrix_sha256": array_sha(x),
        "absolute_target_sha256": array_sha(q_abs),
        "representative_share_target_sha256": array_sha(y_share),
        "grouped_weights_sha256": array_sha(weights),
        "quality_839_control": trimmed(q_metrics),
        "representative_share_1194_control": trimmed(share_metrics),
        "listwise_candidate": trimmed(list_metrics),
        "quality_839_order_sha256": order_sha(q_order),
        "representative_share_1194_order_sha256": order_sha(share_order),
        "listwise_order_sha256": order_sha(list_order),
        "listwise_oof_score_sha256": array_sha(oof_listwise),
        "optimizer": OPTIMIZER,
        "optimizer_folds": optimizer_folds,
        "fold_membership": fold_membership,
        "diversity": DIVERSITY,
        "promotion_gate": {
            "recovered_at_100_gt_80": int(list_metrics["recovered_at_100"]) > 80,
            "recovered_at_50_ge_43": int(list_metrics["recovered_at_50"]) >= 43,
            "recovered_at_25_ge_22": int(list_metrics["recovered_at_25"]) >= 22,
            "recovered_at_500_ge_171": int(list_metrics["recovered_at_500"]) >= 171,
            "precision_ge_parent": float(list_metrics["top100_dominant_precision"]) >= SHARE_CONTROL["top100_dominant_precision"],
            "mrr_ge_parent": float(list_metrics["mrr"]) >= SHARE_CONTROL["mrr"],
            "qualified_eq_256": int(list_metrics["qualified_matches"]) == 256,
        },
        "full_model_freeze": full,
        "same_shower_all_fragments_same_fold": True,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "representative_share_target_changed": False,
        "pairwise_objective_used": False,
        "pointwise_candidate_model_used": False,
        "regularization_used": False,
        "temperature_used": False,
        "intercept_used": False,
        "target_search": False,
        "feature_search": False,
        "model_search": False,
        "hyperparameter_search": False,
        "diversity_search": False,
        "source_quota_selected": False,
        "family_deletion": False,
        "post_result_second_search": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
        "later_external_benchmark_requires_separate_freeze": True,
    }

    (a.output / "GMN_LISTWISE_REPRESENTATIVE_SHARE_OOF_V1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    (a.output / "FULL_MODEL_FREEZE.json").write_text(
        json.dumps(full, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": result["verdict"],
        "quality_839_control": result["quality_839_control"],
        "representative_share_1194_control": result["representative_share_1194_control"],
        "listwise_candidate": result["listwise_candidate"],
        "promotion_gate": result["promotion_gate"],
        "optimizer_folds": optimizer_folds,
        "full_model_freeze": full,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
