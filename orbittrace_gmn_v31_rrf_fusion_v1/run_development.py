#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

RRF_K = 60
PARENT_SOURCE_BLOB = "b4e2d72e532e47aa95ed335f690748423d11ea59"
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


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
    spec = importlib.util.spec_from_file_location("frozen_gmn_v31_parent", path)
    req(spec is not None and spec.loader is not None, "cannot import frozen GMN v31 parent")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def rrf_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
    req(len(hard_order) == len(local_order) and set(hard_order) == set(local_order), "RRF rank universe mismatch")
    rh = {fid: i + 1 for i, fid in enumerate(hard_order)}
    rg = {fid: i + 1 for i, fid in enumerate(local_order)}
    score = {fid: 1.0 / (RRF_K + rh[fid]) + 1.0 / (RRF_K + rg[fid]) for fid in hard_order}
    return sorted(hard_order, key=lambda fid: (-score[fid], rh[fid], fid))


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


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent_out = a.output / "parent_reproduction"
    candidate_out = a.output / "rrf_candidate"
    parent_out.mkdir(exist_ok=True)
    candidate_out.mkdir(exist_ok=True)

    mod = load_parent(a.parent_source)
    original_fusion = mod.equal_rank_fusion
    original_argv = sys.argv[:]
    try:
        # Exact parent reproduction first.
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
        req(parent["distance"] == "ordinary Euclidean after fold-training z-score", "parent distance changed")
        req(parent["nearest_k"] == 1 and parent["margin"] == "d_nonpositive-d_positive", "parent geometry changed")
        req(parent["diversity"] == {"lambda": 0.8, "scale": 1.0}, "parent diversity changed")
        req(parent["strict_whole_shower_oof"] is True and parent["blind_exclusion"] == [20.0, 55.0], "parent OOF/firewall changed")

        # Sole successor change: replace final equal-rank fusion with fixed RRF(k=60).
        mod.equal_rank_fusion = rrf_fusion
        sys.argv = parent_cli(a, candidate_out)
        rc = int(mod.main())
        req(rc == 0, "RRF candidate execution returned nonzero")
        cand_raw = read_parent_result(candidate_out)
    finally:
        mod.equal_rank_fusion = original_fusion
        sys.argv = original_argv

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
    gates = {
        "recovered_at_100_strictly_better_than_parent": int(candidate["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(candidate["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(candidate["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(candidate["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(candidate["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_RRF_FUSION_V1" if passed else "FAIL_GMN_V31_RRF_FUSION_V1"

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
        "hard_order_sha256": parent["hard_order_sha256"],
        "local_diversified_order_sha256": parent["local_diversified_order_sha256"],
        "rrf_order_sha256": cand_raw["fused_order_sha256"],
        "parent_control": PARENT_CONTROL,
        "parent_reproduced_metrics": pm,
        "rrf_candidate_metrics": candidate,
        "local_geometry_only": parent["local_geometry_only"],
        "rrf": {"k": RRF_K, "formula": "1/(60+hard_rank)+1/(60+local_geometry_rank)", "tie_break": "hard_rank_then_family_id"},
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
        "fusion_k_search": False,
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
    out = a.output / "GMN_V31_RRF_FUSION_V1_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: candidate[k] for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500", "top100_dominant_precision", "mrr", "qualified_matches")},
        "gates": gates,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
