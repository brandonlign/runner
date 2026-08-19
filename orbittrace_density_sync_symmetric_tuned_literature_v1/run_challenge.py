#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import get_clusters

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "orbittrace_symmetric_tuned_literature_v2"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
import run_benchmark as bench  # noqa: E402

SUPPORT_GRID = (
    (5, 5),
    (10, 5), (10, 10),
    (20, 10), (20, 20),
    (40, 20), (40, 40),
    (50, 25), (50, 50),
    (80, 40), (80, 80),
    (100, 50), (100, 100),
)
EXPECTED_PARENT_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
EXPECTED_SYNC_BLOB = "587a304f451e41b9503272f1783a6c6ebb295000"
HDB_PRIMARY = 0.345475559012312
HDB_RECOVERED40 = 52


def req(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def load_kernels(parent_path: Path, sync_path: Path) -> tuple[Any, Any]:
    parent = load_module(parent_path, "recurrent_eom")
    sync = load_module(sync_path, "density_synchronous_eom_frozen")
    return parent, sync


def install_runtime_compat() -> None:
    bench.install_hdb_compat()


def density_sync_outputs(
    rows: list[dict[str, Any]],
    x_geo: np.ndarray,
    parent: Any,
    sync_kernel: Any,
) -> dict[str, list[dict[str, Any]]]:
    years = np.asarray([int(r["year"]) for r in rows], dtype=np.int64)
    outputs: dict[str, list[dict[str, Any]]] = {}
    for mcs, ms in SUPPORT_GRID:
        model = hdbscan.HDBSCAN(
            min_cluster_size=mcs,
            min_samples=ms,
            metric="euclidean",
            cluster_selection_method="eom",
            cluster_selection_epsilon=0.0,
            allow_single_cluster=False,
            prediction_data=False,
        ).fit(x_geo)
        tree = model.condensed_tree_._raw_tree
        synchronous, _parent_annual, _reconstructed = sync_kernel.density_synchronous_stability(
            tree, years
        )
        labels, probabilities, _stabilities = get_clusters(
            tree,
            dict(synchronous),
            cluster_selection_method="eom",
            allow_single_cluster=False,
            match_reference_implementation=False,
            cluster_selection_epsilon=0.0,
            max_cluster_size=0,
        )
        labels = np.asarray(labels, dtype=int)
        probabilities = np.asarray(probabilities, dtype=float)
        nodes = parent.selected_eom_nodes(tree, synchronous)
        positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
        req(
            positive == list(range(len(nodes))),
            f"density-sync compact-label mapping changed for {mcs}/{ms}",
        )
        node_score = np.zeros(len(labels), dtype=float)
        for lab, node in enumerate(nodes):
            node_score[labels == lab] = float(synchronous[float(node)])
        cfg = f"mcs={mcs},ms={ms}"
        outputs[cfg] = bench.families_from_labels(
            labels,
            rows,
            "DSEOM2",
            node_score,
            probabilities,
        )
    return outputs


def command_pretruth(args: argparse.Namespace) -> int:
    install_runtime_compat()
    parent, sync_kernel = load_kernels(args.parent_kernel, args.sync_kernel)

    rows, ids_by_year, universe = bench.merge_common_rows(args.rows_root)
    req(len(rows) == 29246, f"common-universe count changed: {len(rows)}")
    req(len(ids_by_year[2013]) == 15988, "2013 common count changed")
    req(len(ids_by_year[2014]) == 13258, "2014 common count changed")

    sugar_source = args.sources / "sugar_uncertainty_core.py"
    req(sugar_source.exists(), "frozen Sugar geometry source missing")
    sugar = load_module(sugar_source, "density_sync_fair_sugar_geometry")
    sol, ra, dec, vg, *_ = bench.sugar_arrays(rows)
    x_geo = np.asarray(sugar.feature_matrix_from_equatorial(sol, ra, dec, vg), dtype=float)
    req(x_geo.shape == (len(rows), 6), f"unexpected GEO6 shape: {x_geo.shape}")
    req(np.all(np.isfinite(x_geo)), "non-finite GEO6 input")

    outputs = density_sync_outputs(rows, x_geo, parent, sync_kernel)
    pretruth = {
        "schema": "ORBITTRACE_DENSITY_SYNC_SYMMETRIC_TUNED_PRETRUTH_V1",
        "truth_accessed": False,
        "method_definition_selected_before_symmetric_benchmark": True,
        "support_grid": [list(x) for x in SUPPORT_GRID],
        "pooled_common_event_count": len(rows),
        "universe": universe,
        "event_ids_by_year": {
            str(year): sorted(ids) for year, ids in ids_by_year.items()
        },
        "source_sha256": {
            "parent_recurrent_eom": sha256(args.parent_kernel),
            "density_synchronous_eom": sha256(args.sync_kernel),
            "sugar_geometry_source": sha256(sugar_source),
        },
        "expected_git_blobs": {
            "parent_recurrent_eom": EXPECTED_PARENT_BLOB,
            "density_synchronous_eom": EXPECTED_SYNC_BLOB,
        },
        "candidate_counts": {cfg: len(families) for cfg, families in outputs.items()},
        "outputs": outputs,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output / "DENSITY_SYNC_PRETRUTH.json"
    out.write_text(json.dumps(pretruth, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({
        "truth_accessed": False,
        "pooled_common_event_count": len(rows),
        "candidate_counts": pretruth["candidate_counts"],
        "pretruth_sha256": sha256(out),
    }, indent=2, sort_keys=True))
    return 0


def aggregate_folds(folds: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mean_test_auc_macro_f1": float(np.mean([
            fold["test"]["auc_macro_f1"] for fold in folds
        ])),
        "mean_test_macro_f1_at_40": float(np.mean([
            fold["test"]["budgets"]["40"]["macro_f1"] for fold in folds
        ])),
        "total_test_recovered_at_40": int(sum(
            fold["test"]["budgets"]["40"]["recovered_f1_gt_0_5"] for fold in folds
        )),
        "mean_native_macro_f1": float(np.mean([
            fold["test"]["native"]["macro_f1"] for fold in folds
        ])),
    }


def command_score(args: argparse.Namespace) -> int:
    pretruth = json.loads(args.pretruth.read_text())
    req(pretruth["schema"] == "ORBITTRACE_DENSITY_SYNC_SYMMETRIC_TUNED_PRETRUTH_V1", "wrong pretruth schema")
    req(pretruth["truth_accessed"] is False, "pretruth truth-access flag changed")
    req(pretruth["pooled_common_event_count"] == 29246, "pretruth common universe changed")
    req(tuple(tuple(x) for x in pretruth["support_grid"]) == SUPPORT_GRID, "support grid changed")

    ids_by_year = {
        int(year): set(map(str, ids))
        for year, ids in pretruth["event_ids_by_year"].items()
    }
    truth = bench.common_truth(args.truth_root, ids_by_year)
    outputs = pretruth["outputs"]

    folds: list[dict[str, Any]] = []
    for dev_year, test_year in ((2013, 2014), (2014, 2013)):
        selection = bench.select(outputs, truth[dev_year])
        selected = selection["selected"]
        chosen = outputs[selected["config"]]
        folds.append({
            "dev_year": dev_year,
            "test_year": test_year,
            "selected_config": selected,
            "test": bench.curve(chosen, truth[test_year]),
        })

    aggregate = aggregate_folds(folds)
    frozen = json.loads(args.frozen_v2_result.read_text())
    req(
        frozen.get("schema") == "ORBITTRACE_SYMMETRIC_TUNED_LITERATURE_BENCHMARK_V2",
        "wrong frozen symmetric-v2 result schema",
    )
    frozen_aggregate = frozen["aggregate"]
    hdb = frozen_aggregate["hdbscan"]
    req(abs(float(hdb["mean_test_auc_macro_f1"]) - HDB_PRIMARY) < 1e-15, "frozen HDB primary changed")
    req(int(hdb["total_test_recovered_at_40"]) == HDB_RECOVERED40, "frozen HDB recovery changed")

    primary_delta = float(aggregate["mean_test_auc_macro_f1"] - hdb["mean_test_auc_macro_f1"])
    recovery_delta = int(aggregate["total_test_recovered_at_40"] - hdb["total_test_recovered_at_40"])
    passed = primary_delta > 0.0 and recovery_delta >= 0
    verdict = (
        "PASS_DENSITY_SYNC_BEATS_TUNED_HDBSCAN_SYMMETRIC_V1"
        if passed
        else "FAIL_DENSITY_SYNC_BEATS_TUNED_HDBSCAN_SYMMETRIC_V1"
    )

    comparison = {
        "density_sync_recurrent_eom": aggregate,
        "frozen_symmetric_v2": frozen_aggregate,
        "delta_vs_tuned_hdbscan": {
            "mean_test_auc_macro_f1": primary_delta,
            "mean_test_macro_f1_at_40": float(
                aggregate["mean_test_macro_f1_at_40"] - hdb["mean_test_macro_f1_at_40"]
            ),
            "total_test_recovered_at_40": recovery_delta,
            "mean_native_macro_f1": float(
                aggregate["mean_native_macro_f1"] - hdb["mean_native_macro_f1"]
            ),
        },
    }

    result = {
        "schema": "ORBITTRACE_DENSITY_SYNC_SYMMETRIC_TUNED_CHALLENGE_V1",
        "verdict": verdict,
        "pass_gate": {
            "strict_primary_superiority": primary_delta > 0.0,
            "no_recovery_loss_at_k40": recovery_delta >= 0,
            "all_required": passed,
        },
        "scientific_role": "ONE_SHOT_TRANSFER_OF_PREEXISTING_FROZEN_DENSITY_SYNC_METHOD",
        "pretruth_sha256": sha256(args.pretruth),
        "frozen_v2_result_sha256": sha256(args.frozen_v2_result),
        "folds": folds,
        "comparison": comparison,
        "method_changes_after_result_authorized": False,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output / "RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "density_sync": aggregate,
        "tuned_hdbscan": hdb,
        "delta_vs_hdbscan": comparison["delta_vs_tuned_hdbscan"],
        "selected_configs": [fold["selected_config"]["config"] for fold in folds],
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pretruth")
    p.add_argument("--rows-root", type=Path, required=True)
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--parent-kernel", type=Path, required=True)
    p.add_argument("--sync-kernel", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(func=command_pretruth)

    s = sub.add_parser("score")
    s.add_argument("--pretruth", type=Path, required=True)
    s.add_argument("--truth-root", type=Path, required=True)
    s.add_argument("--frozen-v2-result", type=Path, required=True)
    s.add_argument("--output", type=Path, required=True)
    s.set_defaults(func=command_score)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
