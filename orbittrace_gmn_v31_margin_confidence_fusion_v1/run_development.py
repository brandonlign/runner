#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

PARENT_SOURCE_BLOB = "b4e2d72e532e47aa95ed335f690748423d11ea59"
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
EXPECTED_N = 226


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def array_sha(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode())
    h.update(str(tuple(arr.shape)).encode())
    h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "parent_source",
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


def load_parent(path: Path):
    req(git_blob_sha(path) == PARENT_SOURCE_BLOB, "parent GMN v31 source blob changed")
    spec = importlib.util.spec_from_file_location("frozen_gmn_v31_parent_confidence", path)
    req(spec is not None and spec.loader is not None, "cannot import frozen GMN v31 parent")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def parent_cli(a: argparse.Namespace, out: Path) -> list[str]:
    return [
        "run_development.py",
        "--quality-source", str(a.quality_source),
        "--support-source-parts", str(a.support_source_parts),
        "--candidate-payload", str(a.candidate_payload),
        "--baseline-payload", str(a.baseline_payload),
        "--scorer-parts", str(a.scorer_parts),
        "--v8-result-json", str(a.v8_result_json),
        "--p19-prelabel-json", str(a.p19_prelabel_json),
        "--output", str(out),
    ]


def read_parent_result(out: Path) -> dict[str, Any]:
    p = out / "GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF_RESULT.json"
    req(p.exists(), f"missing parent result {p}")
    return json.loads(p.read_text())


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def average_ranks_ascending(values: list[float]) -> list[float]:
    n = len(values)
    req(n > 1 and all(math.isfinite(v) for v in values), "invalid confidence values")
    idx = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    start = 0
    while start < n:
        end = start + 1
        v = values[idx[start]]
        while end < n and values[idx[end]] == v:
            end += 1
        # 1-based average rank for positions start..end-1.
        avg = ((start + 1) + end) / 2.0
        for k in range(start, end):
            ranks[idx[k]] = avg
        start = end
    return ranks


def confidence_from_margins(hard_order: list[str], margin_by_id: dict[str, float]) -> dict[str, float]:
    req(len(hard_order) == EXPECTED_N and len(set(hard_order)) == EXPECTED_N, "hard-order universe changed")
    req(set(hard_order) == set(margin_by_id), "margin confidence universe mismatch")
    mags = [abs(float(margin_by_id[fid])) for fid in hard_order]
    req(all(math.isfinite(v) for v in mags), "nonfinite margin magnitude")
    req(max(mags) > min(mags), "all margin magnitudes identical")
    ranks = average_ranks_ascending(mags)
    denom = float(EXPECTED_N - 1)
    conf = {fid: (ranks[i] - 1.0) / denom for i, fid in enumerate(hard_order)}
    req(all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in conf.values()), "invalid confidence vector")
    return conf


def confidence_fusion(
    hard_order: list[str],
    local_order: list[str],
    margin_by_id: dict[str, float],
) -> tuple[list[str], dict[str, float]]:
    req(len(hard_order) == EXPECTED_N and len(local_order) == EXPECTED_N, "rank-universe size changed")
    req(set(hard_order) == set(local_order), "rank universe mismatch")
    rh = {fid: i + 1 for i, fid in enumerate(hard_order)}
    rg = {fid: i + 1 for i, fid in enumerate(local_order)}
    conf = confidence_from_margins(hard_order, margin_by_id)
    denom = float(EXPECTED_N - 1)
    score: dict[str, float] = {}
    for fid in hard_order:
        uh = (EXPECTED_N - rh[fid]) / denom
        ug = (EXPECTED_N - rg[fid]) / denom
        parent_utility = 0.5 * (uh + ug)
        c = conf[fid]
        score[fid] = (1.0 - c) * uh + c * parent_utility
    order = sorted(hard_order, key=lambda fid: (-score[fid], rh[fid], fid))
    req(len(order) == EXPECTED_N and len(set(order)) == EXPECTED_N, "invalid confidence-fusion order")
    return order, conf


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent_out = a.output / "parent_reproduction"
    candidate_out = a.output / "confidence_candidate"
    parent_out.mkdir(exist_ok=True)
    candidate_out.mkdir(exist_ok=True)

    mod = load_parent(a.parent_source)
    original_fusion = mod.equal_rank_fusion
    original_diversity = mod.q.diversity_order
    original_argv = sys.argv[:]
    capture: dict[str, Any] = {}
    candidate_confidence: dict[str, float] = {}

    try:
        # Exact untouched parent reproduction first.
        sys.argv = parent_cli(a, parent_out)
        rc = int(mod.main())
        req(rc == 0, "parent reproduction returned nonzero")
        parent = read_parent_result(parent_out)
        req(parent["verdict"] == "PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF", "parent no longer passes")
        pm = parent["equal_rank_fusion"]
        for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
            req(int(pm[k]) == int(PARENT_CONTROL[k]), f"parent {k} changed: {pm[k]}")
        for k in ("top100_dominant_precision", "mrr"):
            req(metric_close(pm[k], PARENT_CONTROL[k]), f"parent {k} changed: {pm[k]}")
        req(parent["candidate_count"] == EXPECTED_N and parent["feature_dimension"] == 23, "parent universe/representation changed")
        req(parent["distance"] == "ordinary Euclidean after fold-training z-score", "parent distance changed")
        req(parent["nearest_k"] == 1 and parent["margin"] == "d_nonpositive-d_positive", "parent geometry changed")
        req(parent["diversity"] == {"lambda": 0.8, "scale": 1.0}, "parent diversity changed")
        req(parent["strict_whole_shower_oof"] is True and parent["blind_exclusion"] == [20.0, 55.0], "parent OOF/firewall changed")

        def capturing_diversity(scores, cm, lam, scale, tie):
            arr = np.asarray(scores, dtype=float)
            req(arr.shape == (EXPECTED_N,) and np.isfinite(arr).all(), "captured margin vector invalid")
            req(len(tie) == EXPECTED_N, "captured tie vector size changed")
            ids = [str(x[1]) for x in tie]
            req(len(set(ids)) == EXPECTED_N, "captured tie IDs not unique")
            capture["margin_array"] = arr.copy()
            capture["margin_ids"] = ids
            capture["margin_by_id"] = {fid: float(arr[i]) for i, fid in enumerate(ids)}
            return original_diversity(scores, cm, lam, scale, tie)

        def adaptive_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
            req("margin_by_id" in capture, "margin vector not captured before fusion")
            order, conf = confidence_fusion(hard_order, local_order, capture["margin_by_id"])
            candidate_confidence.clear()
            candidate_confidence.update(conf)
            return order

        # Sole successor change: candidate-specific confidence in the already-frozen local leg.
        mod.q.diversity_order = capturing_diversity
        mod.equal_rank_fusion = adaptive_fusion
        sys.argv = parent_cli(a, candidate_out)
        rc = int(mod.main())
        req(rc == 0, "margin-confidence candidate execution returned nonzero")
        cand_raw = read_parent_result(candidate_out)
    finally:
        mod.equal_rank_fusion = original_fusion
        mod.q.diversity_order = original_diversity
        sys.argv = original_argv

    req("margin_array" in capture and "margin_by_id" in capture, "candidate margin capture missing")
    req(array_sha(capture["margin_array"]) == parent["margin_sha256"], "captured raw margin hash differs from frozen parent")
    req(cand_raw["margin_sha256"] == parent["margin_sha256"], "candidate raw margin hash changed")

    # All pre-fusion scientific state must be identical between parent and candidate runs.
    for k in (
        "candidate_count", "feature_dimension", "prelabel_sha256", "feature_matrix_sha256",
        "margin_sha256", "hard_order_sha256", "local_diversified_order_sha256",
        "reference_definition", "strict_whole_shower_oof", "fold_count", "nearest_k",
        "distance", "margin", "diversity", "baseline", "local_geometry_only", "fold_diagnostics",
        "blind_exclusion",
    ):
        req(cand_raw[k] == parent[k], f"pre-fusion parent state changed at {k}")

    candidate = cand_raw["equal_rank_fusion"]
    req(len(candidate_confidence) == EXPECTED_N, "confidence vector not captured")
    hard_ids = sorted(candidate_confidence)
    confidence_rows = [
        {
            "family_id": fid,
            "oof_margin": float(capture["margin_by_id"][fid]),
            "absolute_margin": abs(float(capture["margin_by_id"][fid])),
            "confidence": float(candidate_confidence[fid]),
        }
        for fid in hard_ids
    ]
    confidence_sha = canonical_sha(confidence_rows)
    confidence_payload = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_MARGIN_CONFIDENCE_PROVENANCE",
        "candidate_count": EXPECTED_N,
        "definition": "average-rank percentile of absolute frozen OOF local margin",
        "confidence_sha256": confidence_sha,
        "rows": confidence_rows,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
    }
    (a.output / "GMN_V31_MARGIN_CONFIDENCE_VECTOR.json").write_text(
        json.dumps(confidence_payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    gates = {
        "recovered_at_100_strictly_better_than_parent": int(candidate["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(candidate["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(candidate["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(candidate["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(candidate["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_MARGIN_CONFIDENCE_FUSION_V1" if passed else "FAIL_GMN_V31_MARGIN_CONFIDENCE_FUSION_V1"

    conf_values = list(candidate_confidence.values())
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "parent_source_git_blob": PARENT_SOURCE_BLOB,
        "candidate_count": int(parent["candidate_count"]),
        "feature_dimension": int(parent["feature_dimension"]),
        "prelabel_sha256": parent["prelabel_sha256"],
        "feature_matrix_sha256": parent["feature_matrix_sha256"],
        "margin_sha256": parent["margin_sha256"],
        "captured_margin_sha256": array_sha(capture["margin_array"]),
        "hard_order_sha256": parent["hard_order_sha256"],
        "local_diversified_order_sha256": parent["local_diversified_order_sha256"],
        "confidence_fused_order_sha256": cand_raw["fused_order_sha256"],
        "confidence_vector_sha256": confidence_sha,
        "confidence_summary": {
            "min": float(min(conf_values)),
            "max": float(max(conf_values)),
            "mean": float(sum(conf_values) / len(conf_values)),
            "zero_count": int(sum(v == 0.0 for v in conf_values)),
            "one_count": int(sum(v == 1.0 for v in conf_values)),
        },
        "confidence_definition": "c=(average_rank_ascending(abs(oof_margin))-1)/(N-1)",
        "fusion_definition": "u=(1-c)*hard_rank_utility+c*((hard_rank_utility+local_rank_utility)/2)",
        "parent_control": PARENT_CONTROL,
        "parent_reproduced_metrics": pm,
        "confidence_candidate_metrics": candidate,
        "local_geometry_only": parent["local_geometry_only"],
        "pass_gates": gates,
        "strict_whole_shower_oof": True,
        "distance": parent["distance"],
        "nearest_k": 1,
        "margin": parent["margin"],
        "diversity": parent["diversity"],
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "feature_search": False,
        "metric_search": False,
        "scaling_search": False,
        "reference_definition_search": False,
        "diversity_search": False,
        "confidence_threshold_search": False,
        "confidence_transform_search": False,
        "fusion_weight_search": False,
        "alternate_fusion_search": False,
        "post_result_second_search": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
        "sonotaco_benchmark_authorized_by_this_result": bool(passed),
        "claim_boundary": "GMN development only; a PASS authorizes only a separately frozen one-shot exposed SonotaCo comparison.",
    }
    out = a.output / "GMN_V31_MARGIN_CONFIDENCE_FUSION_V1_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: candidate[k] for k in (
            "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500",
            "top100_dominant_precision", "mrr", "qualified_matches"
        )},
        "confidence_summary": result["confidence_summary"],
        "gates": gates,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
