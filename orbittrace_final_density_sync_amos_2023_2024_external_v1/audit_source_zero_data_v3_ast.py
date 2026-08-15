#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ALLOWED_EVALUATOR_REPO_MODULE = "orbittrace_recurrent_eom_hdbscan_v1.run_development"
FORBIDDEN_DIRECT_MODULES = {
    "hdbscan",
    "hdbscan._hdbscan_tree",
    "orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom",
    "orbittrace_density_synchronous_recurrent_eom_v1.density_synchronous_eom",
}
FORBIDDEN_CALLS = {
    "HDBSCAN",
    "fit",
    "geo_matrix",
    "compute_stability",
    "recurrent_stability",
    "density_synchronous_stability",
    "eom_labels",
    "selected_eom_nodes",
    "candidates_from_labels",
    "sync_candidates_from_labels",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parser_options(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("--"):
                    out.add(arg.value)
    return out


def imports(tree: ast.AST) -> tuple[set[str], dict[str, set[str]]]:
    modules: set[str] = set()
    symbols: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return modules, symbols


def called_names(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            out.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            out.add(node.func.attr)
    return out


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"missing function {name}")


def direct_call_lines(fn: ast.FunctionDef, name: str) -> list[int]:
    out: list[int] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == name:
            out.append(int(node.lineno))
        elif isinstance(node.func, ast.Attribute) and node.func.attr == name:
            out.append(int(node.lineno))
    return sorted(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--hardening-v1-freeze", type=Path, required=True)
    p.add_argument("--hardening-v3-freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    gsrc = a.generator.read_text(encoding="utf-8")
    esrc = a.evaluator.read_text(encoding="utf-8")
    gtree = ast.parse(gsrc)
    etree = ast.parse(esrc)

    require(parser_options(gtree) == {"--canonical-2023", "--canonical-2024", "--output"}, "generator CLI surface changed")
    require(parser_options(etree) == {"--pretruth", "--pretruth-sha256", "--labels-2023", "--labels-2024", "--output"}, "evaluator CLI surface changed")
    require(sum(1 for n in ast.walk(gtree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fit") == 1, "generator must fit exactly one pooled hierarchy")

    modules, symbols = imports(etree)
    require(not (modules & FORBIDDEN_DIRECT_MODULES), f"evaluator imports forbidden scientific module(s): {sorted(modules & FORBIDDEN_DIRECT_MODULES)}")
    repo_modules = {m for m in modules if m.startswith("orbittrace_")}
    require(repo_modules == {ALLOWED_EVALUATOR_REPO_MODULE}, f"unexpected evaluator repository import(s): {sorted(repo_modules)}")
    require(symbols.get(ALLOWED_EVALUATOR_REPO_MODULE, set()) == {"annual_gate", "metrics"}, "evaluator inherited scientific import surface changed")

    calls = called_names(etree)
    require(not (calls & FORBIDDEN_CALLS), f"evaluator calls forbidden scientific recomputation target(s): {sorted(calls & FORBIDDEN_CALLS)}")
    require({"metrics", "annual_gate"} <= calls, "evaluator lost inherited metric/gate calls")

    main_fn = function_node(etree, "main")
    validate_lines = direct_call_lines(main_fn, "validate_pretruth")
    label_lines = direct_call_lines(main_fn, "load_labels")
    metric_lines = direct_call_lines(main_fn, "metrics")
    require(len(validate_lines) == 1 and len(label_lines) == 2 and metric_lines, "evaluator control-flow audit surface changed")
    require(validate_lines[0] < min(label_lines) < min(metric_lines), "pretruth validation not structurally before labels/metrics")

    for literal in (
        "EXPECTED_PRETRUTH_KEYS",
        "CANDIDATE_SCHEMAS",
        "FAMILY_PREFIX",
        "NO_ASSOCIATION_ALIASES",
        "unexpected top-level pretruth schema",
        "candidate deterministic family ID mismatch",
        "candidate order inconsistent with frozen score/tie sort",
        "pretruth scientific/transport source pins changed",
        "annual EOM reconstruction mismatch",
        "noncanonical SPORADIC sentinel",
        "ambiguous no-association sentinel",
        "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
    ):
        require(literal in esrc, f"hardened evaluator missing invariant/literal: {literal}")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3",
        "generator_sha256": sha(a.generator),
        "evaluator_sha256": sha(a.evaluator),
        "protocol_sha256": sha(a.protocol),
        "hardening_v1_freeze_sha256": sha(a.hardening_v1_freeze),
        "hardening_v3_freeze_sha256": sha(a.hardening_v3_freeze),
        "forbidden_detection": "AST_EXACT_IMPORTS_AND_CALL_TARGETS",
        "allowed_evaluator_repo_module": ALLOWED_EVALUATOR_REPO_MODULE,
        "allowed_inherited_symbols": ["annual_gate", "metrics"],
        "pretruth_validation_before_label_open": True,
        "exact_pretruth_schema_enforced": True,
        "exact_candidate_schemas_enforced": True,
        "family_ids_recomputed": True,
        "score_sort_order_recomputed": True,
        "empty_candidate_lists_structurally_allowed": True,
        "exact_sporadic_sentinel_enforced": True,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
