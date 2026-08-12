#!/usr/bin/env python3
"""Export an exact reusable target-excluded GMN development fixture after full provenance reproduction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent
from orbittrace_gmn_balanced_shrinkage_fisher_oof_v1 import run_development as fisher

q = parent.q
YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
EXPECTED_HARD = parent.EXPECTED_HARD
FEATURE_DIM = parent.FEATURE_DIM
EXPECTED_FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
EXPECTED_HARD_ORDER_SHA = "2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e"
EXPECTED_PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
EXPECTED_FISHER_SCALED_SHA = "9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e"
EXPECTED_PARENT_METRICS = {
    "recovered_at_100": 66,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
EXPECTED_FISHER_METRICS = {
    "recovered_at_100": 69,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7677499561973543,
    "mrr": 0.05055989766869564,
    "qualified_matches": 95,
}
CORPUS = "orbittrace-gmn-development-fixture-v1"


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


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dump_json(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    return parent.metric_subset(metrics)


def verify_metrics(name: str, metrics: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        got = metrics[key]
        if isinstance(value, float):
            parent.req(abs(float(got) - value) < 1e-15, f"{name} metric {key} changed: {got}")
        else:
            parent.req(int(got) == value, f"{name} metric {key} changed: {got}")


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
    parent.req(parent.order_sha(hard_order) == EXPECTED_HARD_ORDER_SHA, "hard order hash changed")
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}

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

    # Absolute firewall is checked before representation and development truth export.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = parent.event_sol(row)
    for family in hard:
        for year in YEARS:
            centroid = family.get("centroids", {}).get(str(year))
            parent.req(centroid is not None, f"missing centroid for {family['family_id']} {year}")
            csol = float(centroid["sol"]) % 360.0
            parent.req(not (BLIND[0] <= csol <= BLIND[1]), f"protected centroid reached fixture: {family['family_id']} {year}")

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
    parent.req(parent.array_sha(X) == EXPECTED_FEATURE_SHA, "exact parent 23D feature matrix did not reproduce")

    eligible = q.v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in ids}
    positive = np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)
    parent.req(positive.any() and (~positive).any(), "recoverability target degenerate")
    groups: list[str] = []
    for fid in ids:
        label = truths[fid]["best_label"]
        groups.append(("SHOWER/" + str(label)) if label is not None else ("NEG/" + fid))
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=np.int64)
    parent.req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")

    # Reproduce both authoritative development controls before exporting the cache.
    parent_margin, fisher_raw, fisher_fold_diag = fisher.oof_parent_and_fisher(X, positive, groups)
    parent.req(parent.array_sha(parent_margin) == EXPECTED_PARENT_MARGIN_SHA, "parent margin did not reproduce")
    parent_scale = float(np.median(np.abs(parent_margin)))
    fisher_scale = float(np.median(np.abs(fisher_raw)))
    parent.req(np.isfinite(parent_scale) and parent_scale > 0.0, "invalid parent margin scale")
    parent.req(np.isfinite(fisher_scale) and fisher_scale > 0.0, "invalid Fisher score scale")
    fisher_unit_factor = float(parent_scale / fisher_scale)
    fisher_scaled = fisher_raw * fisher_unit_factor
    parent.req(parent.array_sha(fisher_scaled) == EXPECTED_FISHER_SCALED_SHA, "binding Fisher scaled score did not reproduce")

    tie = [(hard_rank[fid], fid) for fid in ids]
    parent_idx = q.diversity_order(parent_margin, cm, parent.DIVERSITY_LAMBDA, parent.DIVERSITY_SCALE, tie)
    parent_local_order = [ids[i] for i in parent_idx]
    parent_fused_order = parent.equal_rank_fusion(hard_order, parent_local_order)
    parent_metrics = q.v1.monotone_metrics(hard, parent_fused_order, truths, eligible)
    verify_metrics("parent", parent_metrics, EXPECTED_PARENT_METRICS)

    fisher_idx = q.diversity_order(fisher_scaled, cm, parent.DIVERSITY_LAMBDA, parent.DIVERSITY_SCALE, tie)
    fisher_local_order = [ids[i] for i in fisher_idx]
    fisher_fused_order = parent.equal_rank_fusion(hard_order, fisher_local_order)
    fisher_metrics = q.v1.monotone_metrics(hard, fisher_fused_order, truths, eligible)
    verify_metrics("Fisher", fisher_metrics, EXPECTED_FISHER_METRICS)

    # Export only already-authorized target-excluded development information.
    np.save(a.output / "features.npy", X, allow_pickle=False)
    np.save(a.output / "centroids.npy", cm, allow_pickle=False)
    np.save(a.output / "positive.npy", positive, allow_pickle=False)
    np.save(a.output / "folds.npy", folds, allow_pickle=False)
    np.save(a.output / "parent_margin.npy", parent_margin, allow_pickle=False)
    np.save(a.output / "fisher_raw.npy", fisher_raw, allow_pickle=False)
    np.save(a.output / "fisher_scaled.npy", fisher_scaled, allow_pickle=False)

    hard_payload = {
        "hard_families": hard,
        "hard_order": hard_order,
        "ids": ids,
        "groups": groups,
        "truths": truths,
        "eligible": {str(label): dict(counts) for label, counts in eligible.items()},
    }
    hard_payload_sha = dump_json(a.output / "development_labels_and_memberships.json", hard_payload)

    manifest = {
        "verdict": "PASS_GMN_DEVELOPMENT_FIXTURE_V1",
        "scientific_change": False,
        "fixture_role": "AUTHORIZED_TARGET_EXCLUDED_GMN_DEVELOPMENT_CACHE_ONLY",
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "feature_matrix_sha256": parent.array_sha(X),
        "centroid_matrix_sha256": parent.array_sha(cm),
        "positive_vector_sha256": parent.array_sha(positive),
        "fold_vector_sha256": parent.array_sha(folds),
        "hard_order_sha256": parent.order_sha(hard_order),
        "groups_sha256": canonical_sha(groups),
        "truths_sha256": canonical_sha(truths),
        "eligible_sha256": canonical_sha(hard_payload["eligible"]),
        "labels_memberships_file_sha256": hard_payload_sha,
        "parent_margin_sha256": parent.array_sha(parent_margin),
        "parent_local_order_sha256": parent.order_sha(parent_local_order),
        "parent_fused_order_sha256": parent.order_sha(parent_fused_order),
        "parent_metrics": metric_subset(parent_metrics),
        "fisher_raw_sha256": parent.array_sha(fisher_raw),
        "fisher_scaled_sha256": parent.array_sha(fisher_scaled),
        "fisher_unit_factor": fisher_unit_factor,
        "fisher_local_order_sha256": parent.order_sha(fisher_local_order),
        "fisher_fused_order_sha256": parent.order_sha(fisher_fused_order),
        "fisher_metrics": metric_subset(fisher_metrics),
        "fisher_fold_diagnostics": fisher_fold_diag,
        "source_p19_prelabel_sha256": parent.sha(a.p19_prelabel_json),
        "source_v8_result_sha256": parent.sha(a.v8_result_json),
        "source_ranker_sha256": parent.sha(a.quality_source),
        "development_truth_cached": True,
        "candidate_generation_recomputed_for_future_tests": False,
        "future_fixture_use_requires_exact_hash_match": True,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    manifest_sha = dump_json(a.output / "GMN_DEVELOPMENT_FIXTURE_V1.json", manifest)
    print(json.dumps({
        "verdict": manifest["verdict"],
        "manifest_sha256": manifest_sha,
        "feature_matrix_sha256": manifest["feature_matrix_sha256"],
        "positive_families": int(positive.sum()),
        "nonpositive_families": int((~positive).sum()),
        "parent100": parent_metrics["recovered_at_100"],
        "fisher100": fisher_metrics["recovered_at_100"],
        "fisher_scaled_sha256": manifest["fisher_scaled_sha256"],
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
