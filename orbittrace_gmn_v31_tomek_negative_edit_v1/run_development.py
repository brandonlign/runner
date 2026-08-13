#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

PARENT_SOURCE_BLOB = "b4e2d72e532e47aa95ed335f690748423d11ea59"
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}

OLD_BLOCK = '''        pos = y[train]\n        neg = ~pos\n        P = Ztr[pos]\n        N = Ztr[neg]\n        for j, global_i in enumerate(test_indices.tolist()):\n            dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))\n            dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))\n            margins[global_i] = dneg - dpos\n        fold_diag.append({\n            "fold": fold,\n            "train_examples": int(train.sum()),\n            "test_examples": int(test.sum()),\n            "positive_references": int(pos.sum()),\n            "nonpositive_references": int(neg.sum()),\n            "heldout_positive": int(y[test].sum()),\n            "zero_variance_features": int(np.sum(sd == 0.0)),\n            "train_group_count": len(train_groups),\n            "test_group_count": len(test_groups),\n        })\n'''

NEW_BLOCK = '''        pos = y[train]\n        neg = ~pos\n\n        # Sole successor change: single-pass Tomek editing of nonpositive references.\n        # Nearest-neighbor search is ordinary Euclidean in the exact parent fold-z-scored space.\n        train_fids = [ids[i] for i in train_indices.tolist()]\n        D = np.linalg.norm(Ztr[:, None, :] - Ztr[None, :, :], axis=2)\n        np.fill_diagonal(D, np.inf)\n        nearest = []\n        for ii in range(len(Ztr)):\n            jj = min(\n                (j for j in range(len(Ztr)) if j != ii),\n                key=lambda j: (float(D[ii, j]), hard_rank[train_fids[j]], train_fids[j]),\n            )\n            nearest.append(int(jj))\n        tomek_pairs = []\n        remove_negative_local = set()\n        for ii, jj in enumerate(nearest):\n            if ii < jj and nearest[jj] == ii and bool(pos[ii]) != bool(pos[jj]):\n                tomek_pairs.append((ii, jj))\n                remove_negative_local.add(ii if bool(neg[ii]) else jj)\n        keep_neg = neg.copy()\n        for ii in sorted(remove_negative_local):\n            keep_neg[ii] = False\n        req(pos.any(), f"fold {fold} lost all positive references")\n        req(keep_neg.any(), f"fold {fold} lost all nonpositive references after Tomek editing")\n\n        P = Ztr[pos]\n        N = Ztr[keep_neg]\n        for j, global_i in enumerate(test_indices.tolist()):\n            dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))\n            dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))\n            margins[global_i] = dneg - dpos\n        fold_diag.append({\n            "fold": fold,\n            "train_examples": int(train.sum()),\n            "test_examples": int(test.sum()),\n            "positive_references": int(pos.sum()),\n            "nonpositive_references": int(keep_neg.sum()),\n            "original_nonpositive_references": int(neg.sum()),\n            "tomek_pairs": int(len(tomek_pairs)),\n            "removed_nonpositive_references": int(len(remove_negative_local)),\n            "heldout_positive": int(y[test].sum()),\n            "zero_variance_features": int(np.sum(sd == 0.0)),\n            "train_group_count": len(train_groups),\n            "test_group_count": len(test_groups),\n        })\n'''


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


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


def load_module_from_source(source: str, name: str, filename: str):
    mod = types.ModuleType(name)
    mod.__file__ = filename
    sys.modules[name] = mod
    exec(compile(source, filename, "exec"), mod.__dict__)
    return mod


def read_result(out: Path) -> dict[str, Any]:
    p = out / "GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF_RESULT.json"
    req(p.exists(), f"missing result {p}")
    return json.loads(p.read_text())


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent_out = a.output / "parent_reproduction"
    candidate_out = a.output / "tomek_candidate"
    parent_out.mkdir(exist_ok=True)
    candidate_out.mkdir(exist_ok=True)

    req(git_blob_sha(a.parent_source) == PARENT_SOURCE_BLOB, "parent GMN v31 source changed")
    source = a.parent_source.read_text()
    req(source.count(OLD_BLOCK) == 1, "frozen parent Tomek patch site changed")
    edited_source = source.replace(OLD_BLOCK, NEW_BLOCK, 1)
    req(edited_source != source and OLD_BLOCK not in edited_source, "Tomek patch did not apply exactly once")

    original_argv = sys.argv[:]
    try:
        parent_mod = load_module_from_source(source, "frozen_gmn_v31_parent_tomek_control", str(a.parent_source))
        sys.argv = parent_cli(a, parent_out)
        req(int(parent_mod.main()) == 0, "exact parent reproduction failed")
        parent = read_result(parent_out)

        pm = parent["equal_rank_fusion"]
        req(parent["verdict"] == "PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF", "parent no longer passes")
        for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
            req(int(pm[k]) == int(PARENT_CONTROL[k]), f"parent {k} changed")
        for k in ("top100_dominant_precision", "mrr"):
            req(metric_close(pm[k], PARENT_CONTROL[k]), f"parent {k} changed")

        candidate_mod = load_module_from_source(edited_source, "frozen_gmn_v31_tomek_candidate", str(a.parent_source) + "#TOMEK_NEGATIVE_EDIT_V1")
        sys.argv = parent_cli(a, candidate_out)
        req(int(candidate_mod.main()) == 0, "Tomek candidate execution failed")
        cand_raw = read_result(candidate_out)
    finally:
        sys.argv = original_argv

    # Representation, truth universe, folds, and baseline must remain identical.
    for k in (
        "candidate_count", "feature_dimension", "prelabel_sha256", "feature_matrix_sha256",
        "hard_order_sha256", "reference_definition", "strict_whole_shower_oof", "fold_count",
        "nearest_k", "distance", "diversity", "baseline", "blind_exclusion",
    ):
        req(cand_raw[k] == parent[k], f"immutable parent state changed at {k}")
    req(cand_raw["margin_sha256"] != parent["margin_sha256"], "Tomek edit did not alter OOF margin")

    for fd in cand_raw["fold_diagnostics"]:
        req(fd["positive_references"] > 0 and fd["nonpositive_references"] > 0, "empty edited reference class")
        req(fd["original_nonpositive_references"] >= fd["nonpositive_references"], "invalid negative edit count")
        req(fd["removed_nonpositive_references"] == fd["original_nonpositive_references"] - fd["nonpositive_references"], "negative removal count mismatch")
        req(fd["tomek_pairs"] == fd["removed_nonpositive_references"], "each Tomek pair must remove exactly one negative")

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
    verdict = "PASS_GMN_V31_TOMEK_NEGATIVE_EDIT_V1" if passed else "FAIL_GMN_V31_TOMEK_NEGATIVE_EDIT_V1"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_REFERENCE_EDIT_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "parent_source_git_blob": PARENT_SOURCE_BLOB,
        "candidate_count": int(parent["candidate_count"]),
        "feature_dimension": int(parent["feature_dimension"]),
        "feature_matrix_sha256": parent["feature_matrix_sha256"],
        "parent_margin_sha256": parent["margin_sha256"],
        "tomek_margin_sha256": cand_raw["margin_sha256"],
        "hard_order_sha256": parent["hard_order_sha256"],
        "parent_local_order_sha256": parent["local_diversified_order_sha256"],
        "tomek_local_order_sha256": cand_raw["local_diversified_order_sha256"],
        "tomek_fused_order_sha256": cand_raw["fused_order_sha256"],
        "parent_control": PARENT_CONTROL,
        "parent_reproduced_metrics": pm,
        "tomek_candidate_metrics": candidate,
        "tomek_local_geometry_only_metrics": cand_raw["local_geometry_only"],
        "fold_diagnostics": cand_raw["fold_diagnostics"],
        "reference_edit": {
            "rule": "single-pass ordinary Tomek links in exact fold-z-scored 23D space; remove nonpositive endpoint only",
            "nearest_neighbor_k": 1,
            "tie_break": "immutable_hard_rank_then_family_id",
            "positive_endpoints_removed": False,
            "iterative": False,
        },
        "pass_gates": gates,
        "strict_whole_shower_oof": True,
        "distance": "ordinary Euclidean after fold-training z-score",
        "margin": "d_nonpositive-d_positive after fixed nonpositive Tomek endpoint removal",
        "diversity": {"lambda": 0.8, "scale": 1.0},
        "fusion": "exact parent equal rank-sum with immutable P19 hard order",
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "feature_search": False,
        "metric_search": False,
        "scaling_search": False,
        "tomek_variant_search": False,
        "threshold_search": False,
        "k_search": False,
        "reference_weight_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "post_result_second_search": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
        "sonotaco_benchmark_authorized_by_this_result": bool(passed),
    }
    (a.output / "GMN_V31_TOMEK_NEGATIVE_EDIT_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: candidate[k] for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500", "top100_dominant_precision", "mrr", "qualified_matches")},
        "fold_tomek": [{"fold":fd["fold"],"pairs":fd["tomek_pairs"],"neg_before":fd["original_nonpositive_references"],"neg_after":fd["nonpositive_references"]} for fd in cand_raw["fold_diagnostics"]],
        "gates": gates,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
