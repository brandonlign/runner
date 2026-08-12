#!/usr/bin/env python3
"""Target-excluded GMN physical-block consensus successor to passed v31-principle geometry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent

q = parent.q
YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
EXPECTED_HARD = parent.EXPECTED_HARD
FEATURE_DIM = parent.FEATURE_DIM
DIVERSITY_LAMBDA = parent.DIVERSITY_LAMBDA
DIVERSITY_SCALE = parent.DIVERSITY_SCALE
PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
PARENT_METRICS = {
    "recovered_at_100": 66,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
BLOCKS = {
    "structural": (0, 10),
    "cohesion": (10, 17),
    "neighbor": (17, 23),
}
CORPUS = "orbittrace-gmn-v31-principle-block-consensus-oof-v1"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "quality_source",
        "support_source_parts",
        "candidate_payload",
        "baseline_payload",
        "scorer_parts",
        "v8_result_json",
        "p19_prelabel_json",
        "output",
    ):
        p.add_argument("--" + name.replace("_", "-"), dest=name, type=Path, required=True)
    return p.parse_args()


def nearest_margin(P: np.ndarray, N: np.ndarray, point: np.ndarray) -> float:
    dpos = float(np.min(np.linalg.norm(P - point[None, :], axis=1)))
    dneg = float(np.min(np.linalg.norm(N - point[None, :], axis=1)))
    return dneg - dpos


def oof_full_and_blocks(
    X: np.ndarray,
    y: np.ndarray,
    groups: list[str],
) -> tuple[np.ndarray, dict[str, np.ndarray], list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(group) for group in groups], dtype=int)
    parent.req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")
    full = np.zeros(len(X), dtype=float)
    block = {name: np.zeros(len(X), dtype=float) for name in BLOCKS}
    diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        parent.req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        parent.req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        parent.req(y[train].any() and (~y[train]).any(), f"fold {fold} lacks both reference classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        pos = y[train]
        neg = ~pos
        P = Ztr[pos]
        N = Ztr[neg]
        test_indices = np.where(test)[0]

        for j, global_i in enumerate(test_indices.tolist()):
            full[global_i] = nearest_margin(P, N, Zte[j])
            for name, (lo, hi) in BLOCKS.items():
                block[name][global_i] = nearest_margin(P[:, lo:hi], N[:, lo:hi], Zte[j, lo:hi])

        diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
        })

    parent.req(np.isfinite(full).all(), "nonfinite parent full-space OOF margin")
    for name in BLOCKS:
        parent.req(np.isfinite(block[name]).all(), f"nonfinite {name} block OOF margin")
    return full, block, diag


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent.req(parent.sha(a.quality_source) == parent.QUALITY_SHA, "active GMN ranker source changed")
    parent.req(parent.sha(a.v8_result_json) == parent.V8_RESULT_SHA, "v8 result changed")
    parent.req(parent.sha(a.p19_prelabel_json) == parent.P19_PRELABEL_SHA, "P19 hard-family prelabel changed")

    payload = json.loads(a.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    parent.req(len(hard) == EXPECTED_HARD and len(hard_order) == EXPECTED_HARD, "hard family count changed")
    ids = [str(f["family_id"]) for f in hard]
    parent.req(len(set(ids)) == EXPECTED_HARD and set(ids) == set(hard_order), "hard family identity changed")
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    parent.req(BLOCKS == {"structural": (0, 10), "cohesion": (10, 17), "neighbor": (17, 23)}, "block definition changed")

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    parent.req(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan_by_year, _calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    parent.req(sorted(scan_by_year) == list(YEARS), "GMN year universe changed")
    parent.req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month panel changed")

    # Fail closed on protected data before representation or truth interpretation.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = parent.event_sol(row)
    for family in hard:
        for year in YEARS:
            centroid = family.get("centroids", {}).get(str(year))
            parent.req(centroid is not None, f"missing centroid for {family['family_id']} {year}")
            csol = float(centroid["sol"]) % 360.0
            parent.req(not (BLIND[0] <= csol <= BLIND[1]), f"protected centroid reached diagnostic: {family['family_id']} {year}")

    lookup = q.v2.event_lookup(scan_by_year)
    cm = q.centroid_matrix(hard)
    parent.req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "centroid matrix changed")
    nf = q.neighbor_features(cm)
    parent.req(nf.shape == (EXPECTED_HARD, 6) and np.isfinite(nf).all(), "neighbor matrix changed")
    X = np.asarray([
        parent.intrinsic_features(family, hard_rank, lookup, support, base, nf[i])
        for i, family in enumerate(hard)
    ], dtype=float)
    parent.req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "intrinsic feature matrix invalid")

    np.save(a.output / "GMN_V31_BLOCK_CONSENSUS_INTRINSIC_FEATURES.npy", X, allow_pickle=False)
    prelabel = {
        "scope": "GMN 2022/2023 target-excluded physical-block consensus v31-principle successor",
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "feature_matrix_sha256": parent.array_sha(X),
        "hard_order_sha256": parent.order_sha(hard_order),
        "blocks": {name: [lo, hi] for name, (lo, hi) in BLOCKS.items()},
        "block_dimensions": {name: hi - lo for name, (lo, hi) in BLOCKS.items()},
        "block_definition_outcome_selected": False,
        "representation_changed_from_parent": False,
        "truth_interpreted_for_feature_construction": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GMN_V31_BLOCK_CONSENSUS_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = parent.sha(prelabel_path)

    # Development truth starts after representation and blocks are sealed.
    eligible = q.v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in ids}
    y = np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)
    parent.req(y.any() and (~y).any(), "recoverability reference target degenerate")
    groups: list[str] = []
    for fid in ids:
        label = truths[fid]["best_label"]
        groups.append(("SHOWER/" + str(label)) if label is not None else ("NEG/" + fid))

    full_margin, block_margin, fold_diag = oof_full_and_blocks(X, y, groups)
    parent.req(parent.array_sha(full_margin) == PARENT_MARGIN_SHA, "parent full-space OOF margin did not reproduce exactly")

    block_scales: dict[str, float] = {}
    standardized: list[np.ndarray] = []
    for name in ("structural", "cohesion", "neighbor"):
        scale = float(np.median(np.abs(block_margin[name])))
        parent.req(np.isfinite(scale) and scale > 0.0, f"invalid {name} median absolute margin")
        block_scales[name] = scale
        standardized.append(block_margin[name] / scale)
    stack = np.vstack(standardized)
    parent.req(stack.shape == (3, EXPECTED_HARD) and np.isfinite(stack).all(), "invalid standardized block stack")
    consensus = np.median(stack, axis=0)
    parent.req(np.isfinite(consensus).all(), "nonfinite block consensus")

    parent_scale = float(np.median(np.abs(full_margin)))
    consensus_scale = float(np.median(np.abs(consensus)))
    parent.req(np.isfinite(parent_scale) and parent_scale > 0.0, "invalid parent median absolute margin")
    parent.req(np.isfinite(consensus_scale) and consensus_scale > 0.0, "invalid consensus median absolute margin")
    unit_factor = float(parent_scale / consensus_scale)
    parent.req(np.isfinite(unit_factor) and unit_factor > 0.0, "invalid consensus unit factor")
    consensus_margin = consensus * unit_factor
    parent.req(np.isfinite(consensus_margin).all(), "nonfinite scaled block consensus margin")

    tie = [(hard_rank[fid], fid) for fid in ids]

    # Reproduce exact parent ranking and metrics before interpreting successor.
    parent_idx = q.diversity_order(full_margin, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    parent_local_order = [ids[i] for i in parent_idx]
    parent_fused_order = parent.equal_rank_fusion(hard_order, parent_local_order)
    parent_metrics = q.v1.monotone_metrics(hard, parent_fused_order, truths, eligible)
    for key, expected in PARENT_METRICS.items():
        got = parent_metrics[key]
        if isinstance(expected, float):
            parent.req(abs(float(got) - expected) < 1e-15, f"parent metric {key} changed: {got}")
        else:
            parent.req(int(got) == expected, f"parent metric {key} changed: {got}")

    idx = q.diversity_order(consensus_margin, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in idx]
    fused_order = parent.equal_rank_fusion(hard_order, local_order)
    candidate = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    parent.req(int(candidate["qualified_matches"]) == PARENT_METRICS["qualified_matches"], "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_above_parent": int(candidate["recovered_at_100"]) > PARENT_METRICS["recovered_at_100"],
        "recovered_at_50_not_below_parent": int(candidate["recovered_at_50"]) >= PARENT_METRICS["recovered_at_50"],
        "top100_precision_not_below_parent": float(candidate["top100_dominant_precision"]) >= PARENT_METRICS["top100_dominant_precision"],
        "mrr_not_below_parent": float(candidate["mrr"]) >= PARENT_METRICS["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == PARENT_METRICS["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_PRINCIPLE_BLOCK_CONSENSUS_OOF" if passed else "FAIL_GMN_V31_PRINCIPLE_BLOCK_CONSENSUS_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_PHYSICAL_BLOCK_CONSENSUS_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "prelabel_sha256": prelabel_sha,
        "feature_matrix_sha256": parent.array_sha(X),
        "parent_full_margin_sha256": parent.array_sha(full_margin),
        "block_margin_sha256": {name: parent.array_sha(block_margin[name]) for name in BLOCKS},
        "block_median_absolute_margin": block_scales,
        "consensus_raw_sha256": parent.array_sha(consensus),
        "consensus_scaled_margin_sha256": parent.array_sha(consensus_margin),
        "parent_median_absolute_margin": parent_scale,
        "consensus_median_absolute_margin": consensus_scale,
        "unit_factor": unit_factor,
        "blocks": {name: [lo, hi] for name, (lo, hi) in BLOCKS.items()},
        "consensus": "elementwise median of three block margins after division by each block median absolute OOF margin",
        "unit_preservation": "parent median absolute margin / consensus median absolute margin",
        "nearest_k": 1,
        "distance": "ordinary Euclidean after exact parent fold-training z-score, restricted to frozen blocks",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "parent": parent.metric_subset(parent_metrics),
        "candidate": parent.metric_subset(candidate),
        "pass_gates": gates,
        "fold_diagnostics": fold_diag,
        "block_search": False,
        "block_subset_search": False,
        "block_weight_search": False,
        "consensus_rule_search": False,
        "scale_statistic_search": False,
        "unit_transform_search": False,
        "k_search": False,
        "metric_search": False,
        "feature_search": False,
        "threshold_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "family_deletion": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    out = a.output / "GMN_V31_PRINCIPLE_BLOCK_CONSENSUS_OOF_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent100": parent_metrics["recovered_at_100"],
        "candidate100": candidate["recovered_at_100"],
        "parent50": parent_metrics["recovered_at_50"],
        "candidate50": candidate["recovered_at_50"],
        "parent_precision": parent_metrics["top100_dominant_precision"],
        "candidate_precision": candidate["top100_dominant_precision"],
        "parent_mrr": parent_metrics["mrr"],
        "candidate_mrr": candidate["mrr"],
        "qualified": candidate["qualified_matches"],
        "block_scales": block_scales,
        "parent_scale": parent_scale,
        "consensus_scale": consensus_scale,
        "unit_factor": unit_factor,
        "parent_full_margin_sha256": parent.array_sha(full_margin),
        "consensus_scaled_margin_sha256": parent.array_sha(consensus_margin),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
