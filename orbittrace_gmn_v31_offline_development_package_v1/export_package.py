#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PARENT_SOURCE_BLOB = "b4e2d72e532e47aa95ed335f690748423d11ea59"
EXPECTED_N = 226
EXPECTED_D = 23
EXPECTED_CM_D = 8
PARENT_PRELABEL_SHA = "b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09"
PARENT_FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
BLIND = [20.0, 55.0]


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    spec = importlib.util.spec_from_file_location("frozen_gmn_v31_parent_offline_export", path)
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


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent_out = a.output / "exact_parent"
    package_out = a.output / "package"
    parent_out.mkdir(exist_ok=True)
    package_out.mkdir(exist_ok=True)

    mod = load_parent(a.parent_source)
    original_family_truth = mod.q.v1.family_truth
    original_eligible_labels = mod.q.v1.eligible_labels
    original_centroid_matrix = mod.q.centroid_matrix
    original_argv = sys.argv[:]

    captured_truths: dict[str, dict[str, Any]] = {}
    captured_eligible_labels: list[str] = []
    captured_cm: list[np.ndarray] = []

    def capture_family_truth(family, hidden_labels, eligible):
        truth = original_family_truth(family, hidden_labels, eligible)
        fid = str(family["family_id"])
        req(fid not in captured_truths, f"duplicate captured family truth {fid}")
        captured_truths[fid] = {
            "positive": bool(truth["positive"]),
            "best_label": None if truth["best_label"] is None else str(truth["best_label"]),
            "overlap": int(truth["overlap"]),
            "precision": float(truth["precision"]),
            "recall": float(truth["recall"]),
            "f1": float(truth["f1"]),
            "dominant_precision": float(truth["dominant_precision"]),
        }
        return truth

    def capture_eligible_labels(hidden_labels):
        eligible = original_eligible_labels(hidden_labels)
        captured_eligible_labels.clear()
        captured_eligible_labels.extend(sorted(map(str, eligible.keys())))
        return eligible

    def capture_centroid_matrix(hard):
        cm = np.asarray(original_centroid_matrix(hard), dtype=float)
        captured_cm.clear()
        captured_cm.append(cm.copy())
        return cm

    try:
        mod.q.v1.family_truth = capture_family_truth
        mod.q.v1.eligible_labels = capture_eligible_labels
        mod.q.centroid_matrix = capture_centroid_matrix
        sys.argv = parent_cli(a, parent_out)
        rc = int(mod.main())
        req(rc == 0, "exact parent exporter run returned nonzero")
    finally:
        mod.q.v1.family_truth = original_family_truth
        mod.q.v1.eligible_labels = original_eligible_labels
        mod.q.centroid_matrix = original_centroid_matrix
        sys.argv = original_argv

    result_path = parent_out / "GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF_RESULT.json"
    prelabel_path = parent_out / "GMN_V31_PRINCIPLE_PRELABEL.json"
    x_path = parent_out / "GMN_V31_PRINCIPLE_INTRINSIC_FEATURES.npy"
    req(result_path.exists() and prelabel_path.exists() and x_path.exists(), "parent output incomplete")
    parent = json.loads(result_path.read_text())
    prelabel = json.loads(prelabel_path.read_text())
    X = np.load(x_path, allow_pickle=False)

    req(parent["verdict"] == "PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF", "parent did not pass")
    req(parent["candidate_count"] == EXPECTED_N and parent["feature_dimension"] == EXPECTED_D, "parent shape changed")
    req(parent["prelabel_sha256"] == PARENT_PRELABEL_SHA and file_sha(prelabel_path) == PARENT_PRELABEL_SHA, "parent prelabel changed")
    req(parent["feature_matrix_sha256"] == PARENT_FEATURE_SHA and array_sha(X) == PARENT_FEATURE_SHA, "parent X changed")
    req(parent["margin_sha256"] == PARENT_MARGIN_SHA, "parent margin changed")
    pm = parent["equal_rank_fusion"]
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(pm[key]) == int(PARENT_CONTROL[key]), f"parent {key} changed")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(pm[key], PARENT_CONTROL[key]), f"parent {key} changed")
    req(parent["blind_exclusion"] == BLIND, "parent blind exclusion changed")
    for key in ("sonotaco_2013_2014_access", "target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access"):
        req(parent[key] is False, f"parent firewall violation: {key}")

    req(X.shape == (EXPECTED_N, EXPECTED_D) and np.isfinite(X).all(), "invalid parent X")
    req(len(captured_cm) == 1, "centroid matrix capture failed")
    cm = captured_cm[0]
    req(cm.shape == (EXPECTED_N, EXPECTED_CM_D) and np.isfinite(cm).all(), "invalid centroid matrix")
    req(len(captured_truths) == EXPECTED_N, "truth capture count changed")
    req(len(captured_eligible_labels) > 0, "eligible-label capture empty")

    p19 = json.loads(a.p19_prelabel_json.read_text())
    hard_families = p19["hard_families"]
    hard_order = [str(x) for x in p19["hard_order"]]
    ids = [str(f["family_id"]) for f in hard_families]
    req(len(ids) == EXPECTED_N and len(set(ids)) == EXPECTED_N, "P19 family IDs changed")
    req(len(hard_order) == EXPECTED_N and set(hard_order) == set(ids), "P19 hard order changed")
    req(set(captured_truths) == set(ids), "captured truth IDs mismatch")

    rows: list[dict[str, Any]] = []
    folds_seen: set[int] = set()
    for fid in ids:
        truth = captured_truths[fid]
        label = truth["best_label"]
        group = ("SHOWER/" + str(label)) if label is not None else ("NEG/" + fid)
        fold = int(mod.q.v1.deterministic_fold(group))
        folds_seen.add(fold)
        rows.append({
            "family_id": fid,
            "strict_group": group,
            "fold": fold,
            "truth": truth,
        })
    req(folds_seen == set(range(5)), "offline fold universe changed")

    x_out = package_out / "GMN_V31_OFFLINE_X.npy"
    cm_out = package_out / "GMN_V31_OFFLINE_CENTROIDS.npy"
    np.save(x_out, X, allow_pickle=False)
    np.save(cm_out, cm, allow_pickle=False)
    req(array_sha(np.load(x_out, allow_pickle=False)) == PARENT_FEATURE_SHA, "written offline X changed")

    manifest = {
        "verdict": "PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1",
        "scientific_role": "ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED",
        "parent_source_git_blob": PARENT_SOURCE_BLOB,
        "candidate_count": EXPECTED_N,
        "feature_dimension": EXPECTED_D,
        "centroid_dimension": EXPECTED_CM_D,
        "feature_matrix_sha256": array_sha(X),
        "centroid_matrix_sha256": array_sha(cm),
        "parent_prelabel_sha256": parent["prelabel_sha256"],
        "parent_margin_sha256": parent["margin_sha256"],
        "hard_order": hard_order,
        "family_input_order": ids,
        "eligible_labels": captured_eligible_labels,
        "rows": rows,
        "parent_baseline_metrics": {k: v for k, v in parent["baseline"].items() if k != "first_rank_by_label"},
        "parent_fused_metrics": {k: v for k, v in parent["equal_rank_fusion"].items() if k != "first_rank_by_label"},
        "development_role": "GMN_2022_2023_TARGET_EXCLUDED_ONLY",
        "raw_event_rows_exported": False,
        "raw_event_ids_exported": False,
        "raw_hidden_label_mapping_exported": False,
        "new_feature_or_score_created": False,
        "new_rank_evaluated": False,
        "successor_selected": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": BLIND,
    }
    manifest["canonical_sha256_without_self_field"] = canonical_sha(manifest)
    manifest_path = package_out / "GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")

    # Strong content guards: no raw event-level data is serialized by this exporter.
    serialized = manifest_path.read_text()
    req('"event_ids"' not in serialized and '"hidden_labels"' not in serialized and '"event_rows"' not in serialized, "forbidden raw event-level field serialized")
    req(len(rows) == EXPECTED_N and all(set(r) == {"family_id", "strict_group", "fold", "truth"} for r in rows), "row schema changed")

    print(json.dumps({
        "verdict": manifest["verdict"],
        "candidate_count": EXPECTED_N,
        "feature_matrix_sha256": manifest["feature_matrix_sha256"],
        "centroid_matrix_sha256": manifest["centroid_matrix_sha256"],
        "manifest_sha256": file_sha(manifest_path),
        "eligible_label_count": len(captured_eligible_labels),
        "positive_family_count": sum(bool(r["truth"]["positive"]) for r in rows),
        "fold_counts": {str(f): sum(r["fold"] == f for r in rows) for f in range(5)},
        "raw_event_rows_exported": False,
        "raw_event_ids_exported": False,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
