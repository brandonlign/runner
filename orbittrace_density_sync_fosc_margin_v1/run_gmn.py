#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

from fosc_margin import global_fosc_exclusion_margins, rank_candidates_by_margin

RECURRENT_RUNNER_PATH = Path("orbittrace_recurrent_eom_hdbscan_v1/run_development.py")
RECURRENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
RECURRENT_KERNEL_PATH = Path("orbittrace_recurrent_eom_hdbscan_v1/recurrent_eom.py")
RECURRENT_KERNEL_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
SYNC_RUNNER_PATH = Path("orbittrace_density_synchronous_recurrent_eom_v1/run_development.py")
SYNC_RUNNER_BLOB = "157813ca331165180a6d20aa71bfc78d5984396f"
SYNC_KERNEL_PATH = Path("orbittrace_density_synchronous_recurrent_eom_v1/density_synchronous_eom.py")
SYNC_KERNEL_BLOB = "587a304f451e41b9503272f1783a6c6ebb295000"

EXPECTED_SYNC_TREE_SHA = "f708b61d925f7b14f999a88b3ce2ff106a6417624a9d02b48174a8d64ad0ec25"
EXPECTED_SYNC_ORDER_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_SYNC_COUNT = 2094
EXPECTED_SYNC_METRICS = {
    "2022": {
        "recovered_at_50": 45,
        "recovered_at_100": 89,
        "top100_dominant_precision": 0.7873334042799703,
        "mrr": 0.022505373166085363,
        "fragmentation_median_top500": 1.0,
    },
    "2023": {
        "recovered_at_50": 46,
        "recovered_at_100": 90,
        "top100_dominant_precision": 0.7898245986099988,
        "mrr": 0.02203028490649908,
        "fragmentation_median_top500": 1.0,
    },
}
YEAR_COUNTS = {315024: "2022", 423658: "2023"}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def membership_multiset_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join(sorted("|".join(str(x) for x in row["event_ids"]) for row in candidates))
    return hashlib.sha256(payload.encode()).hexdigest()


def output_dir_from_argv() -> Path:
    req("--output" in sys.argv, "missing --output argument")
    i = sys.argv.index("--output")
    req(i + 1 < len(sys.argv), "missing --output value")
    return Path(sys.argv[i + 1])


def verify_parent_sources() -> None:
    checks = {
        RECURRENT_RUNNER_PATH: RECURRENT_RUNNER_BLOB,
        RECURRENT_KERNEL_PATH: RECURRENT_KERNEL_BLOB,
        SYNC_RUNNER_PATH: SYNC_RUNNER_BLOB,
        SYNC_KERNEL_PATH: SYNC_KERNEL_BLOB,
    }
    for path, expected in checks.items():
        got = git_blob(path)
        req(got == expected, f"frozen parent source changed: {path}: {got} != {expected}")


def preload_recurrent_runner() -> ModuleType:
    verify_parent_sources()
    spec = importlib.util.spec_from_file_location("run_development", RECURRENT_RUNNER_PATH)
    req(spec is not None and spec.loader is not None, "cannot construct recurrent parent module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_development"] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get("run_development") is module:
            del sys.modules["run_development"]
        raise
    req(Path(module.__file__).resolve() == RECURRENT_RUNNER_PATH.resolve(), "recurrent runner resolved to wrong path")
    req(sys.modules.get("run_development") is module, "recurrent runner preload was replaced")
    return module


def load_sync_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("density_sync_exact_parent_runner", SYNC_RUNNER_PATH)
    req(spec is not None and spec.loader is not None, "cannot construct exact #1263 runner module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    req(Path(module.__file__).resolve() == SYNC_RUNNER_PATH.resolve(), "#1263 runner resolved to wrong path")
    return module


def verify_exact_sync_metrics(metrics: dict[str, dict[str, Any]]) -> None:
    for year, expected in EXPECTED_SYNC_METRICS.items():
        got = metrics[year]
        for key in ("recovered_at_50", "recovered_at_100"):
            req(int(got[key]) == int(expected[key]), f"#1263 baseline {year} {key} changed: {got[key]} != {expected[key]}")
        for key in ("top100_dominant_precision", "mrr", "fragmentation_median_top500"):
            req(
                bool(np.isclose(float(got[key]), float(expected[key]), rtol=0.0, atol=1e-15)),
                f"#1263 baseline {year} {key} changed: {got[key]} != {expected[key]}",
            )


def main() -> int:
    output = output_dir_from_argv()
    output.mkdir(parents=True, exist_ok=True)
    recurrent_runner = preload_recurrent_runner()
    req(tuple(recurrent_runner.YEARS) == (2022, 2023), "parent years changed")
    req(tuple(float(x) for x in recurrent_runner.BLIND) == (20.0, 55.0), "target firewall changed")
    req(int(recurrent_runner.MIN_CLUSTER_SIZE) == 10 and int(recurrent_runner.MIN_SAMPLES) == 10, "parent HDBSCAN constants changed")

    sync_runner = load_sync_runner()
    original_density = sync_runner.density_synchronous_stability
    original_candidate_builder = sync_runner.sync_candidates_from_labels
    original_metrics = recurrent_runner.metrics

    state: dict[str, Any] = {
        "tree_sha": None,
        "selected_nodes": None,
        "optimal": None,
        "global_optimum": None,
        "forced_global": None,
        "margins": None,
        "baseline_candidates": None,
        "margin_candidates": None,
        "baseline_metrics": {},
    }

    def density_wrapper(tree, years):
        synchronous, annual_parent, reconstructed = original_density(tree, years)
        tree_digest = sync_runner.tree_sha(tree)
        req(tree_digest == EXPECTED_SYNC_TREE_SHA, f"exact #1263 condensed-tree hash changed: {tree_digest}")
        selected = sync_runner.parent_reom.selected_eom_nodes(tree, synchronous)
        optimal, global_optimum, forced_global, margins = global_fosc_exclusion_margins(
            tree, synchronous, selected
        )
        state["tree_sha"] = tree_digest
        state["selected_nodes"] = tuple(int(x) for x in selected)
        state["optimal"] = optimal
        state["global_optimum"] = float(global_optimum)
        state["forced_global"] = forced_global
        state["margins"] = margins
        return synchronous, annual_parent, reconstructed

    def candidate_wrapper(labels, selected_nodes, events, ordinary, synchronous):
        req(state["margins"] is not None, "global exclusion-margin state missing before candidate construction")
        req(
            tuple(int(x) for x in selected_nodes) == state["selected_nodes"],
            "selected node tuple changed between extraction and global-margin calculation",
        )
        baseline = original_candidate_builder(labels, selected_nodes, events, ordinary, synchronous)
        req(len(baseline) == EXPECTED_SYNC_COUNT, f"#1263 candidate count changed: {len(baseline)}")
        baseline_order = ordered_membership_sha(baseline)
        req(baseline_order == EXPECTED_SYNC_ORDER_SHA, f"exact #1263 ordered membership hash changed: {baseline_order}")

        successor = rank_candidates_by_margin(baseline, state["margins"])
        req(len(successor) == len(baseline), "global exclusion-margin ranking changed candidate count")
        base_multi = membership_multiset_sha(baseline)
        succ_multi = membership_multiset_sha(successor)
        req(base_multi == succ_multi, "global exclusion-margin ranking changed candidate membership universe")
        req(
            {r["family_id"] for r in baseline} == {r["family_id"] for r in successor},
            "global exclusion-margin ranking changed candidate identities",
        )

        successor_order = ordered_membership_sha(successor)
        mechanism_active = successor_order != baseline_order
        state["baseline_candidates"] = baseline
        state["margin_candidates"] = successor
        state["baseline_order_sha"] = baseline_order
        state["successor_order_sha"] = successor_order
        state["membership_multiset_sha"] = base_multi
        state["mechanism_active"] = mechanism_active

        margin_values = np.asarray(
            [float(state["margins"][int(r["node_id"])]) for r in baseline], dtype=float
        )
        forced_values = np.asarray(
            [float(state["forced_global"][int(r["node_id"])]) for r in baseline], dtype=float
        )
        req(np.all(margin_values >= 0.0), "negative global FOSC exclusion margin survived theorem kernel")
        req(np.all(forced_values <= float(state["global_optimum"]) + 1e-12), "forced optimum exceeds unrestricted optimum")

        prelabel = {
            "schema": "DENSITY_SYNC_GLOBAL_FOSC_EXCLUSION_MARGIN_V1_PRELABEL",
            "scientific_role": "PRELABEL_FROZEN_DENSITY_SYNC_GLOBAL_FOSC_EXCLUSION_MARGIN_V1",
            "direct_parent": "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PR1263",
            "condensed_tree_sha256": state["tree_sha"],
            "selected_nodes": list(state["selected_nodes"]),
            "parent_candidate_count": len(baseline),
            "successor_candidate_count": len(successor),
            "parent_ordered_membership_sha256": baseline_order,
            "successor_ordered_membership_sha256": successor_order,
            "candidate_membership_multiset_sha256": base_multi,
            "mechanism_active": mechanism_active,
            "global_fosc_optimum": float(state["global_optimum"]),
            "global_fosc_forced_optimum": {
                str(k): float(v) for k, v in sorted(state["forced_global"].items())
            },
            "global_fosc_exclusion_margin": {
                str(k): float(v) for k, v in sorted(state["margins"].items())
            },
            "margin_summary": {
                "minimum": float(np.min(margin_values)),
                "median": float(np.median(margin_values)),
                "maximum": float(np.max(margin_values)),
                "zero_count": int(np.sum(margin_values == 0.0)),
                "positive_count": int(np.sum(margin_values > 0.0)),
                "unique_value_count": int(np.unique(margin_values).size),
            },
            "parent_candidates": baseline,
            "successor_candidates": successor,
            "blind_exclusion": [20.0, 55.0],
            "target_information_access": False,
            "target_region_events_accessed": False,
            "sonotaco_2013_2014_access": False,
            "amos_access": False,
            "asfn_access": False,
            "efn_access": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
        }
        path = output / "DENSITY_SYNC_FOSC_MARGIN_V1_PRELABEL.json"
        path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
        state["official_prelabel_sha"] = sha(path)
        return successor

    def metrics_wrapper(candidates, hidden, annual_ids):
        result = original_metrics(candidates, hidden, annual_ids)
        req(
            state["baseline_candidates"] is not None,
            "#1263 baseline candidate order missing at truth evaluation",
        )
        year = YEAR_COUNTS.get(len(annual_ids))
        req(year is not None, f"unexpected annual accessible-ID count during metric evaluation: {len(annual_ids)}")
        baseline = original_metrics(state["baseline_candidates"], hidden, annual_ids)
        old = state["baseline_metrics"].get(year)
        if old is not None:
            req(old == baseline, f"#1263 baseline metric recomputation changed within run for {year}")
        state["baseline_metrics"][year] = baseline
        return result

    # Monkeypatch only the narrow interfaces needed to observe the already-
    # computed exact #1263 tree/objective, reorder its exact candidate list before
    # truth, and evaluate the untouched #1263 order under the same labels. Parsing,
    # HDBSCAN fitting, target exclusion, truth timing and metric implementation stay
    # inside the byte-pinned #1263/recurrent parent runners.
    sync_runner.density_synchronous_stability = density_wrapper
    sync_runner.sync_candidates_from_labels = candidate_wrapper
    sync_runner.parent_runner.metrics = metrics_wrapper

    rc = sync_runner.main()
    req(int(rc) == 0, f"exact #1263 parent runner returned nonzero status {rc}")
    req(set(state["baseline_metrics"]) == {"2022", "2023"}, "same-run #1263 baseline metrics incomplete")
    verify_exact_sync_metrics(state["baseline_metrics"])
    req(state["baseline_order_sha"] == EXPECTED_SYNC_ORDER_SHA, "#1263 order changed after truth evaluation")
    req(state["tree_sha"] == EXPECTED_SYNC_TREE_SHA, "#1263 tree changed after truth evaluation")

    internal_result_path = output / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT.json"
    internal_prelabel_path = output / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PRELABEL.json"
    req(internal_result_path.exists() and internal_prelabel_path.exists(), "exact parent runner outputs missing")
    internal_result = json.loads(internal_result_path.read_text())
    successor_metrics = internal_result["successor_metrics"]

    annual_gates = {
        year: recurrent_runner.annual_gate(state["baseline_metrics"][year], successor_metrics[year])
        for year in ("2022", "2023")
    }
    strict_100 = any(
        int(successor_metrics[year]["recovered_at_100"])
        > int(state["baseline_metrics"][year]["recovered_at_100"])
        for year in ("2022", "2023")
    )
    passed = bool(
        state["mechanism_active"]
        and strict_100
        and all(all(g.values()) for g in annual_gates.values())
        and len(state["margin_candidates"]) == EXPECTED_SYNC_COUNT
        and state["membership_multiset_sha"]
        == membership_multiset_sha(state["baseline_candidates"])
    )
    verdict = (
        "PASS_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT"
    )

    result = {
        "schema": "DENSITY_SYNC_GLOBAL_FOSC_EXCLUSION_MARGIN_V1_GMN_DEVELOPMENT",
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_TRAIN_DEVELOPMENT_ONLY",
        "prelabel_sha256": state["official_prelabel_sha"],
        "direct_parent": "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PR1263",
        "condensed_tree_sha256": state["tree_sha"],
        "global_fosc_optimum": float(state["global_optimum"]),
        "parent_candidate_count": len(state["baseline_candidates"]),
        "successor_candidate_count": len(state["margin_candidates"]),
        "parent_ordered_membership_sha256": state["baseline_order_sha"],
        "successor_ordered_membership_sha256": state["successor_order_sha"],
        "candidate_membership_multiset_sha256": state["membership_multiset_sha"],
        "mechanism_active": bool(state["mechanism_active"]),
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": state["baseline_metrics"],
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "sole_successor_change": "rank_exact_pr1263_selected_candidates_by_global_forced_exclusion_fosc_objective_loss",
        "gate_b_robustness_eligible": bool(passed),
        "sonotaco_validation_eligible": False,
        "blind_exclusion": [20.0, 55.0],
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    official = output / "DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT.json"
    official.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    # Preserve exact-parent wrapper products under nonbinding names. Their
    # internal recurrent-vs-reranked verdict is not this successor's binding
    # #1263-vs-global-margin gate.
    internal_result_path.rename(output / "INTERNAL_EXACT_PARENT_RUNNER_RESULT.json")
    internal_prelabel_path.rename(output / "INTERNAL_EXACT_PARENT_RUNNER_PRELABEL.json")

    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": state["mechanism_active"],
        "strict_100": strict_100,
        "global_fosc_optimum": state["global_optimum"],
        "parent_order_sha": state["baseline_order_sha"],
        "successor_order_sha": state["successor_order_sha"],
        "parent": {
            y: {k: v for k, v in state["baseline_metrics"][y].items() if k != "first_rank_by_label"}
            for y in ("2022", "2023")
        },
        "successor": {
            y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"}
            for y in ("2022", "2023")
        },
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
