#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import density_synchronous_eom as kernel


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment_line(tree: ast.AST, target_name: str) -> int:
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    lines.append(int(node.lineno))
    if len(lines) != 1:
        raise RuntimeError(f"expected exactly one assignment to {target_name}, got {lines}")
    return lines[0]


def call_lines(tree: ast.AST, attr: str) -> list[int]:
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr == attr:
            out.append(int(node.lineno))
    return sorted(out)


def main() -> int:
    root = Path(__file__).resolve().parent
    protocol = root / "PROTOCOL.md"
    kernel_path = root / "density_synchronous_eom.py"
    runner = root / "run_development.py"

    # The scientific kernel accepts only the condensed tree and annual identity vector.
    sig = inspect.signature(kernel.density_synchronous_stability)
    req(list(sig.parameters) == ["tree", "years"], f"kernel interface widened: {sig}")
    req(all(p.default is inspect._empty for p in sig.parameters.values()), "kernel acquired configurable defaults")

    kernel_text = kernel_path.read_text()
    runner_text = runner.read_text()
    protocol_text = protocol.read_text()
    ktree = ast.parse(kernel_text)
    rtree = ast.parse(runner_text)

    # No network/data connector/client surface inside the scientific kernel.
    banned_kernel_import_roots = {
        "requests", "urllib", "httpx", "aiohttp", "pandas", "sklearn", "gmn_python_api",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(ktree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    req(not (imported_roots & banned_kernel_import_roots), f"kernel gained forbidden imports: {sorted(imported_roots & banned_kernel_import_roots)}")

    # The exact promoted-parent annual accounting must be the reference implementation.
    req("parent._birth_lambdas(tree)" in kernel_text, "kernel no longer uses exact parent birth lambdas")
    req("parent._descendant_year_counts(tree, years_arr)" in kernel_text, "kernel no longer uses exact parent descendant-year accounting")
    req("parent.recurrent_stability(tree, years_arr)" in kernel_text, "kernel no longer verifies against exact parent annual EOM")
    req("min(alive_norm[0], alive_norm[1])" in kernel_text, "sole pointwise minimum objective changed")
    req("TOL = 1e-12" in kernel_text, "frozen engineering identity tolerance changed")

    # No scientific tuning/search constructs in the kernel.
    banned_tokens = [
        "GridSearch", "RandomizedSearch", "optuna", "bayes", "bandwidth", "threshold=", "weight=",
        "sonotaco", "asfn", "efn", "amos", "maarsy", "dms",
    ]
    lower_kernel = kernel_text.lower()
    for token in banned_tokens:
        req(token.lower() not in lower_kernel, f"kernel contains forbidden tuning/external token {token}")

    # Runner must use exactly one pooled HDBSCAN fit and the exact kernel once.
    req(runner_text.count("hdbscan.HDBSCAN(") == 1, "development runner no longer has exactly one pooled HDBSCAN construction")
    req(runner_text.count("density_synchronous_stability(tree, years)") == 1, "development runner changed synchronous-kernel invocation count")
    req("parent_reom.recurrent_stability(tree, years)" in runner_text, "runner no longer reconstructs champion recurrent-EOM directly")
    req("parent_runner.annual_gate" in runner_text, "runner no longer inherits exact no-regression annual gate")
    req("strict_100" in runner_text, "strict recovered@100 improvement gate missing")

    # Prelabel persistence must occur before truth mapping is promoted from sealed variable.
    hidden_line = assignment_line(rtree, "hidden")
    write_lines = call_lines(rtree, "write_text")
    req(write_lines, "runner has no prelabel/result persistence calls")
    prelabel_write_candidates = [line for line in write_lines if line < hidden_line]
    req(prelabel_write_candidates, f"no persisted prelabel before hidden truth use at line {hidden_line}")
    req("prelabel_path.write_text" in runner_text, "named prelabel persistence changed")
    req(runner_text.index("prelabel_path.write_text") < runner_text.index("hidden = hidden_sealed"), "truth use precedes prelabel freeze")

    # Frozen firewall declarations must be explicit in both persisted prelabel and final result.
    for key in [
        "target_information_access", "target_region_events_accessed", "sonotaco_2013_2014_access",
        "efn_access", "asfn_access", "amos_access", "maarsy_scientific_access", "dms_scientific_access",
    ]:
        req(runner_text.count(f'"{key}": False') >= 2, f"firewall flag {key} not explicit in both outputs")
    req("BLIND = parent_runner.BLIND" in runner_text, "runner no longer inherits exact parent blind interval")
    req("315024" in runner_text and "423658" in runner_text, "exact accessible annual event-count guards missing")

    # No external-survey source is imported or opened by the runner. Names appear only as false firewall flags.
    runner_imports: set[str] = set()
    for node in ast.walk(rtree):
        if isinstance(node, ast.Import):
            runner_imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            runner_imports.add(node.module.split(".")[0])
    req(not (runner_imports & {"requests", "urllib", "httpx", "aiohttp"}), "runner gained network client import")

    # Protocol must remain explicitly pre-outcome and prohibit rescue/search.
    req("PRE-IMPLEMENTATION / PRE-OUTCOME SCIENTIFIC FREEZE" in protocol_text, "protocol pre-outcome status missing")
    req("Permanent no-rescue rule" in protocol_text, "protocol no-rescue section missing")
    req("does not authorize SonotaCo" in protocol_text, "protocol external-data prohibition missing")

    result = {
        "verdict": "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_SOURCE_FIREWALL_AUDIT",
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "efn_access": False,
        "asfn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "kernel_signature": str(sig),
        "hidden_truth_assignment_line": hidden_line,
        "last_pretruth_write_line": max(prelabel_write_candidates),
        "sha256": {
            "protocol": sha256(protocol),
            "kernel": sha256(kernel_path),
            "runner": sha256(runner),
        },
        "checks": {
            "kernel_tree_years_only": True,
            "parent_annual_accounting_inherited": True,
            "pointwise_min_objective_exact": True,
            "no_kernel_tuning_or_external_surface": True,
            "one_pooled_hdbscan_fit": True,
            "champion_reconstructed_directly": True,
            "prelabel_before_truth_use": True,
            "exact_parent_gate_inherited": True,
            "external_firewall_explicit": True,
            "no_network_client": True,
            "no_rescue_protocol": True,
        },
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_SOURCE_FIREWALL_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
