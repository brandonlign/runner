#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

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
FORBIDDEN_IMPORT_MODULE_TOKENS = {
    "hdbscan",
    "density_synchronous_eom",
    "recurrent_eom",
}
ALLOWED_EVALUATOR_SCIENCE_CALLS = {"metrics", "annual_gate"}


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


def imported_modules(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def imported_symbols(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update((alias.asname or alias.name.split(".")[-1]) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.update((alias.asname or alias.name) for alias in node.names)
    return out


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

    gopts = parser_options(gtree)
    eopts = parser_options(etree)
    require(gopts == {"--canonical-2023", "--canonical-2024", "--output"}, f"generator CLI surface changed: {sorted(gopts)}")
    require(eopts == {"--pretruth", "--pretruth-sha256", "--labels-2023", "--labels-2024", "--output"}, f"evaluator CLI surface changed: {sorted(eopts)}")
    require(all("label" not in x and "truth" not in x and "shower" not in x for x in gopts), "generator accepts truth-bearing argument")

    g_calls = called_names(gtree)
    require("fit" in g_calls, "generator no longer fits pooled HDBSCAN")
    require(sum(1 for n in ast.walk(gtree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fit") == 1, "generator must fit exactly one pooled HDBSCAN hierarchy")

    e_modules = imported_modules(etree)
    e_symbols = imported_symbols(etree)
    e_calls = called_names(etree)
    for token in FORBIDDEN_IMPORT_MODULE_TOKENS:
        require(not any(token in mod for mod in e_modules), f"evaluator imports forbidden scientific module token: {token}")
    require(not (FORBIDDEN_CALLS & e_calls), f"evaluator calls forbidden scientific recomputation target(s): {sorted(FORBIDDEN_CALLS & e_calls)}")
    require(ALLOWED_EVALUATOR_SCIENCE_CALLS <= e_symbols, "evaluator lost inherited metrics/annual_gate imports")
    require(ALLOWED_EVALUATOR_SCIENCE_CALLS <= e_calls, "evaluator lost inherited metrics/annual_gate calls")

    main_fn = function_node(etree, "main")
    validate_lines = direct_call_lines(main_fn, "validate_pretruth")
    label_lines = direct_call_lines(main_fn, "load_labels")
    metric_lines = direct_call_lines(main_fn, "metrics")
    require(len(validate_lines) == 1, f"expected one validate_pretruth call: {validate_lines}")
    require(len(label_lines) == 2, f"expected two label-open calls: {label_lines}")
    require(metric_lines, "metrics calls missing")
    require(validate_lines[0] < min(label_lines) < min(metric_lines), "pretruth validation is not structurally before label opening and metrics")

    required_evaluator_identifiers = {
        "EXPECTED_PRETRUTH_KEYS",
        "CANDIDATE_SCHEMAS",
        "FAMILY_PREFIX",
        "NO_ASSOCIATION_ALIASES",
        "validate_pretruth",
        "validate_candidate_order",
        "validate_association_label",
        "member_hash",
        "expected_sort_key",
    }
    defined = {n.name for n in etree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assigned: set[str] = set()
    for node in etree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    require(required_evaluator_identifiers <= (defined | assigned), f"hardened evaluator missing identifiers: {sorted(required_evaluator_identifiers - (defined | assigned))}")

    for required_literal in (
        "unexpected top-level pretruth schema",
        "candidate deterministic family ID mismatch",
        "candidate order inconsistent with frozen score/tie sort",
        "candidate order hash mismatch",
        "candidate membership hash mismatch",
        "pretruth scientific/transport source pins changed",
        "frozen HDBSCAN declaration changed",
        "annual EOM reconstruction mismatch",
        "stored mechanism-active flags do not match selected nodes/orders",
        "noncanonical SPORADIC sentinel",
        "ambiguous no-association sentinel",
        "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
        "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
    ):
        require(required_literal in esrc, f"hardened evaluator missing literal/invariant: {required_literal}")

    for token in (
        "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
        "587a304f451e41b9503272f1783a6c6ebb295000",
        "157813ca331165180a6d20aa71bfc78d5984396f",
        "9a0fb05f94d6a28cd95f97d864e76400056273b0",
        "9fed803aa09f03f779610eaff5304251bbf21020",
        "1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993",
    ):
        require(token in esrc or token in gsrc, f"frozen identity missing from source pair: {token}")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3",
        "generator_sha256": sha(a.generator),
        "evaluator_sha256": sha(a.evaluator),
        "protocol_sha256": sha(a.protocol),
        "hardening_v1_freeze_sha256": sha(a.hardening_v1_freeze),
        "hardening_v3_freeze_sha256": sha(a.hardening_v3_freeze),
        "generator_options": sorted(gopts),
        "evaluator_options": sorted(eopts),
        "generator_single_fit": True,
        "generator_truth_input_surface": False,
        "evaluator_forbidden_scientific_imports": False,
        "evaluator_forbidden_scientific_calls": False,
        "source_audit_forbidden_detection": "AST_IMPORT_AND_CALL_TARGETS_NOT_RAW_SUBSTRINGS",
        "pretruth_internal_integrity_validation_before_label_open": True,
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
        "dms_scientific_access": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
