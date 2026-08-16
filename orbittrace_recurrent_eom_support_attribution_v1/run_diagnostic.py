#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SCALE_RESULT_SHA256 = "0c6926aa84d9b88f19f5bb2817b2846b53d09579dbef6b5c4d9c9bb9fd252288"
PARENT_HEAD = "0248177a2b4dc1f7a0969931d835097d3e86c06f"
PARENT_KERNEL_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
PARENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
SUBSETS = tuple((d, b) for d in (128, 1024) for b in range(4))
CONFIGS = (
    ("PARENT_10_10", 10, 10),
    ("CONDENSATION_MIN_2_10", 2, 10),
    ("CORE_MIN_10_2", 10, 2),
    ("BOTH_MIN_2_2", 2, 2),
)


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash_u64(eid: str) -> int:
    digest = hashlib.sha256((SALT + str(eid)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def membership_hashes(labels: np.ndarray, event_ids: list[str], min_size: int) -> list[str]:
    out: list[str] = []
    for label in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        members = sorted(event_ids[int(i)] for i in np.flatnonzero(labels == label))
        req(len(members) >= min_size, f"selected membership below min_cluster_size={min_size}: label={label}")
        out.append(hashlib.sha256(("|".join(members)).encode("utf-8")).hexdigest())
    return sorted(out)


def fit_config(
    X: np.ndarray,
    years: np.ndarray,
    event_ids: list[str],
    config_name: str,
    min_cluster_size: int,
    min_samples: int,
    parent_runner: Any,
) -> dict[str, Any]:
    n = int(len(X))
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    req(len(tree) > 0, f"empty condensed tree for {config_name}")
    req(int(tree["parent"].min()) == n, f"root mismatch for {config_name}")

    ordinary = compute_stability(tree)
    ordinary_labels = eom_labels(tree, ordinary)
    req(
        parent_runner.canonical_partition(model.labels_) == parent_runner.canonical_partition(ordinary_labels),
        f"custom EOM diverged from HDBSCAN for {config_name}",
    )
    ordinary_nodes = selected_eom_nodes(tree, ordinary)

    recurrent, annual = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)

    ordinary_set = set(int(x) for x in ordinary_nodes)
    recurrent_set = set(int(x) for x in recurrent_nodes)
    union = ordinary_set | recurrent_set
    inter = ordinary_set & recurrent_set
    symdiff = ordinary_set ^ recurrent_set

    ordinary_memberships = membership_hashes(ordinary_labels, event_ids, min_cluster_size)
    recurrent_memberships = membership_hashes(recurrent_labels, event_ids, min_cluster_size)
    om = set(ordinary_memberships)
    rm = set(recurrent_memberships)

    root = n
    cluster_nodes = set(int(x) for x in tree["parent"] if int(x) >= root)
    cluster_nodes.update(int(x) for x in tree["child"] if int(x) >= root)

    return {
        "config": config_name,
        "min_cluster_size": int(min_cluster_size),
        "min_samples": int(min_samples),
        "condensed_tree_rows": int(len(tree)),
        "cluster_node_count": int(len(cluster_nodes)),
        "ordinary_selected_node_count": int(len(ordinary_nodes)),
        "recurrent_selected_node_count": int(len(recurrent_nodes)),
        "selected_node_intersection_count": int(len(inter)),
        "selected_node_symmetric_difference_count": int(len(symdiff)),
        "selected_node_jaccard": float(len(inter) / len(union)) if union else 1.0,
        "mechanism_active": bool(ordinary_set != recurrent_set),
        "ordinary_membership_hashes": ordinary_memberships,
        "recurrent_membership_hashes": recurrent_memberships,
        "exact_membership_intersection_count": int(len(om & rm)),
        "positive_recurrent_quality_node_count": int(sum(float(v) > 0.0 for v in recurrent.values())),
        "positive_both_year_annual_contribution_node_count": int(
            sum(float(v[0]) > 0.0 and float(v[1]) > 0.0 for v in annual.values())
        ),
    }


def reproduce_parent(row: dict[str, Any], frozen: dict[str, Any]) -> None:
    keys = (
        "condensed_tree_rows",
        "cluster_node_count",
        "ordinary_selected_node_count",
        "recurrent_selected_node_count",
        "selected_node_intersection_count",
        "selected_node_symmetric_difference_count",
        "mechanism_active",
        "ordinary_membership_hashes",
        "recurrent_membership_hashes",
        "exact_membership_intersection_count",
        "positive_recurrent_quality_node_count",
        "positive_both_year_annual_contribution_node_count",
    )
    for key in keys:
        req(row[key] == frozen[key], f"#1272 parent reproduction failed for {key}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--scale-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    req(sha256(a.scale_result_json) == SCALE_RESULT_SHA256, "binding #1272 result changed")

    scale = json.loads(a.scale_result_json.read_text())
    req(scale["schema"] == "ORBITTRACE_RECURRENT_EOM_SCALE_STRESS_V1", "wrong scale-stress schema")
    req(scale["interpretation"] == "SUPPORTS_FIXED_SCALE_INERTIA_HYPOTHESIS", "#1272 interpretation changed")
    frozen_rows = {(int(r["denominator"]), int(r["bucket"])): r for r in scale["all_fits"]}
    req(all(key in frozen_rows for key in SUBSETS), "#1272 result missing frozen attribution subset")
    req(all(frozen_rows[key]["mechanism_active"] is False for key in SUBSETS), "attribution subset not parent-inactive")

    parent_runner = load_module(a.parent_runner, "support_attribution_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10, "parent min_cluster_size changed")
    req(int(parent_runner.MIN_SAMPLES) == 10, "parent min_samples changed")

    qmod = load_module(a.quality_source, "support_attribution_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-support-attribution-v1-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        normalized = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(normalized) == len(raw), f"normalization count changed for {year}")
        events.extend(normalized)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    X_full = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    all_rows: list[dict[str, Any]] = []
    for denominator, bucket in SUBSETS:
        idx = selected_indices(hashes, denominator, bucket)
        X = np.asarray(X_full[idx], dtype=float)
        years = np.asarray(years_full[idx], dtype=np.int64)
        event_ids = [ids_full[int(i)] for i in idx]
        counts = {str(y): int(np.sum(years == y)) for y in YEARS}
        frozen = frozen_rows[(denominator, bucket)]
        req(int(frozen["events_total"]) == len(idx), "#1272 event count reproduction failed")
        req(frozen["events_by_year"] == counts, "#1272 annual count reproduction failed")
        req(all(counts[str(y)] > 0 for y in YEARS), "subset lost one year")

        for config_name, min_cluster_size, min_samples in CONFIGS:
            print(
                f"[support-attribution] d={denominator} b={bucket} config={config_name} "
                f"n={len(idx)} mcs={min_cluster_size} ms={min_samples}",
                flush=True,
            )
            fit = fit_config(
                X,
                years,
                event_ids,
                config_name,
                min_cluster_size,
                min_samples,
                parent_runner,
            )
            row = {
                "denominator": int(denominator),
                "bucket": int(bucket),
                "events_total": int(len(idx)),
                "events_by_year": counts,
                **fit,
            }
            if config_name == "PARENT_10_10":
                reproduce_parent(row, frozen)
            all_rows.append(row)
            print(
                json.dumps(
                    {
                        "d": denominator,
                        "b": bucket,
                        "config": config_name,
                        "tree_nodes": row["cluster_node_count"],
                        "ordinary": row["ordinary_selected_node_count"],
                        "recurrent": row["recurrent_selected_node_count"],
                        "symdiff": row["selected_node_symmetric_difference_count"],
                        "active": row["mechanism_active"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    req(len(all_rows) == 32, f"expected 32 factorial fits, got {len(all_rows)}")
    parent_rows = [r for r in all_rows if r["config"] == "PARENT_10_10"]
    req(len(parent_rows) == 8 and all(not r["mechanism_active"] for r in parent_rows), "parent did not reproduce inactivity")

    def activation(config: str) -> tuple[int, float]:
        rows = [r for r in all_rows if r["config"] == config]
        req(len(rows) == 8, f"wrong row count for {config}")
        count = sum(bool(r["mechanism_active"]) for r in rows)
        return int(count), float(count / len(rows))

    c_count, C = activation("CONDENSATION_MIN_2_10")
    k_count, K = activation("CORE_MIN_10_2")
    b_count, B = activation("BOTH_MIN_2_2")

    if C >= 0.75 and K <= 0.25:
        attribution = "CONDENSATION_DOMINANT_INERTIA"
    elif K >= 0.75 and C <= 0.25:
        attribution = "CORE_SMOOTHING_DOMINANT_INERTIA"
    elif C >= 0.75 and K >= 0.75:
        attribution = "EITHER_SINGLE_ABLATION_SUFFICIENT"
    elif C < 0.75 and K < 0.75 and B >= 0.75:
        attribution = "JOINT_SUPPORT_BOTTLENECK"
    else:
        attribution = "MIXED_SUPPORT_ATTRIBUTION"

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_SUPPORT_ATTRIBUTION_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "attribution": attribution,
        "question": "Which fixed HDBSCAN support operation is sufficient to cause recurrent-EOM inactivity at small sample sizes?",
        "parent": {
            "method": "recurrent-EOM HDBSCAN v1",
            "selected_branch_head": PARENT_HEAD,
            "kernel_git_blob": PARENT_KERNEL_BLOB,
            "runner_git_blob": PARENT_RUNNER_BLOB,
        },
        "source_scale_stress": {
            "pr": 1272,
            "run": 31929171717,
            "result_sha256": SCALE_RESULT_SHA256,
            "sampling_salt": SALT,
        },
        "subsets": [{"denominator": d, "bucket": b} for d, b in SUBSETS],
        "configurations": [
            {"code": code, "min_cluster_size": mcs, "min_samples": ms}
            for code, mcs, ms in CONFIGS
        ],
        "activation_summary": {
            "CONDENSATION_MIN_2_10": {"active_count": c_count, "fit_count": 8, "activation_rate": C},
            "CORE_MIN_10_2": {"active_count": k_count, "fit_count": 8, "activation_rate": K},
            "BOTH_MIN_2_2": {"active_count": b_count, "fit_count": 8, "activation_rate": B},
        },
        "all_fits": sorted(all_rows, key=lambda r: (int(r["denominator"]), int(r["bucket"]), str(r["config"]))),
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
        "intermediate_support_values_tested": False,
    }
    out = a.output / "RECURRENT_EOM_SUPPORT_ATTRIBUTION_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"attribution": attribution, "activation_summary": result["activation_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
