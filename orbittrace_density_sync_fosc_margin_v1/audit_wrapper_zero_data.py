#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import run_gmn

EXPECTED = {
    "orbittrace_density_sync_fosc_margin_v1/THEORY_REPAIR_FREEZE.md": "41bb237fdbb195cdb7dc159f91b348bb91d41457",
    "orbittrace_density_sync_fosc_margin_v1/PROTOCOL.md": "88409670230013c58b293b8e0fcf12feca66abbe",
    "orbittrace_density_sync_fosc_margin_v1/fosc_margin.py": "d4639b70124eecae33b61bee7c05f9ae54cbab48",
    "orbittrace_density_sync_fosc_margin_v1/run_gmn.py": "b123ce8082428ea1565e564c01bb5a9246eb3f93",
    "orbittrace_recurrent_eom_hdbscan_v1/recurrent_eom.py": "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
    "orbittrace_recurrent_eom_hdbscan_v1/run_development.py": "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c",
    "orbittrace_density_synchronous_recurrent_eom_v1/density_synchronous_eom.py": "587a304f451e41b9503272f1783a6c6ebb295000",
    "orbittrace_density_synchronous_recurrent_eom_v1/run_development.py": "157813ca331165180a6d20aa71bfc78d5984396f",
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # Byte-pin all repaired successor and exact-parent sources without invoking
    # any scientific runner main() or data parser.
    blobs = {path: run_gmn.git_blob(Path(path)) for path in EXPECTED}
    for path, expected in EXPECTED.items():
        req(blobs[path] == expected, f"frozen source blob changed: {path}: {blobs[path]} != {expected}")

    run_gmn.verify_parent_sources()
    recurrent = run_gmn.preload_recurrent_runner()
    sync = run_gmn.load_sync_runner()

    req(tuple(recurrent.YEARS) == (2022, 2023), "recurrent parent years changed")
    req(tuple(float(x) for x in recurrent.BLIND) == (20.0, 55.0), "recurrent target firewall changed")
    req(int(recurrent.MIN_CLUSTER_SIZE) == 10, "recurrent min_cluster_size changed")
    req(int(recurrent.MIN_SAMPLES) == 10, "recurrent min_samples changed")
    req(sync.parent_runner is recurrent, "#1263 runner did not bind to explicitly preloaded recurrent parent")
    req(sync.density_synchronous_stability.__module__ == "density_synchronous_eom", "#1263 density-sync kernel resolved incorrectly")
    req(sync.sync_candidates_from_labels.__module__ == "density_sync_exact_parent_runner", "#1263 candidate builder resolved incorrectly")
    req(sync.parent_runner.metrics is recurrent.metrics, "#1263 evaluator is not exact recurrent parent evaluator")

    req(run_gmn.EXPECTED_SYNC_TREE_SHA == "f708b61d925f7b14f999a88b3ce2ff106a6417624a9d02b48174a8d64ad0ec25", "binding #1263 tree pin changed")
    req(run_gmn.EXPECTED_SYNC_ORDER_SHA == "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2", "binding #1263 order pin changed")
    req(run_gmn.EXPECTED_SYNC_COUNT == 2094, "binding #1263 candidate count pin changed")
    req(run_gmn.EXPECTED_SYNC_METRICS["2022"]["recovered_at_100"] == 89, "binding #1263 2022 @100 pin changed")
    req(run_gmn.EXPECTED_SYNC_METRICS["2023"]["recovered_at_100"] == 90, "binding #1263 2023 @100 pin changed")

    # Static source audit: the wrapper may use exact local filesystem/git/import
    # machinery, but it must not contain network clients or hidden alternate
    # scientific scorers. Dataset names may appear only in explicit false-access
    # provenance fields / firewall text, so we audit imports and scientific-call
    # surfaces rather than naive word bans.
    source_path = Path("orbittrace_density_sync_fosc_margin_v1/run_gmn.py")
    source = source_path.read_text()
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    req(not ({"requests", "urllib", "httpx", "aiohttp", "socket"} & imports), f"network import found: {sorted(imports)}")
    req("global_fosc_exclusion_margins" in source, "repaired global exclusion kernel not used")
    req("fosc_optimal_values_and_selected_margins" not in source, "failed local-margin kernel still referenced")
    req("rank_exact_pr1263_selected_candidates_by_global_forced_exclusion_fosc_objective_loss" in source, "sole-change declaration missing")
    req("EXPECTED_SYNC_ORDER_SHA" in source and "EXPECTED_SYNC_TREE_SHA" in source, "exact #1263 pretruth reproduction pins missing")
    req("parent_ordered_membership_sha256" in source and "successor_ordered_membership_sha256" in source, "pretruth order persistence missing")
    req("candidate_membership_multiset_sha256" in source, "candidate membership identity audit missing")
    req("sonotaco_validation_eligible\": False" in source, "SonotaCo must remain disabled at Gate A")
    req("amos_access\": False" in source, "AMOS firewall field missing")

    # This audit intentionally does not call run_gmn.main(), sync.main(), parser,
    # HDBSCAN.fit, metrics, or any catalogue loader.
    result = {
        "schema": "DENSITY_SYNC_GLOBAL_FOSC_EXCLUSION_MARGIN_V1_ZERO_DATA_WRAPPER_AUDIT",
        "verdict": "PASS_DENSITY_SYNC_FOSC_MARGIN_V1_ZERO_DATA_WRAPPER_AUDIT",
        "source_blobs": blobs,
        "run_gmn_sha256": file_sha256(source_path),
        "exact_parent_module_bound": True,
        "exact_density_sync_kernel_bound": True,
        "exact_candidate_builder_bound": True,
        "exact_evaluator_bound": True,
        "binding_tree_pin_present": True,
        "binding_order_pin_present": True,
        "candidate_universe_pin_present": True,
        "global_exclusion_kernel_only": True,
        "network_imports_absent": True,
        "scientific_runner_main_called": False,
        "catalogue_parser_called": False,
        "hdbscan_fit_called": False,
        "scientific_metrics_called": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "gmn_catalogue_accessed": False,
        "scientific_labels_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DENSITY_SYNC_FOSC_MARGIN_V1_ZERO_DATA_WRAPPER_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
