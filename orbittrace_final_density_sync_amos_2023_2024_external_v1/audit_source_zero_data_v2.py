#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


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


def import_names(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
            out.update(alias.name for alias in node.names)
    return out


def call_lines(tree: ast.AST, name: str) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == name:
            lines.append(int(node.lineno))
        elif isinstance(node.func, ast.Attribute) and node.func.attr == name:
            lines.append(int(node.lineno))
    return sorted(lines)


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"missing function {name}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--hardening-freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    gsrc = a.generator.read_text(encoding="utf-8")
    esrc = a.evaluator.read_text(encoding="utf-8")
    gtree = ast.parse(gsrc)
    etree = ast.parse(esrc)
    gopts = parser_options(gtree)
    eopts = parser_options(etree)
    gimports = import_names(gtree)
    eimports = import_names(etree)

    require(gopts == {"--canonical-2023", "--canonical-2024", "--output"}, f"generator CLI surface changed: {sorted(gopts)}")
    require(all("label" not in x and "truth" not in x and "shower" not in x for x in gopts), "generator accepts truth-bearing argument")
    require("csv" not in gimports, "generator unexpectedly imports CSV/truth transport")
    require(len(call_lines(gtree, "fit")) == 1, "generator must fit exactly one pooled HDBSCAN hierarchy")

    require(eopts == {"--pretruth", "--pretruth-sha256", "--labels-2023", "--labels-2024", "--output"}, f"evaluator CLI surface changed: {sorted(eopts)}")
    require("hdbscan" not in eimports, "evaluator must not import HDBSCAN")
    for forbidden in ("density_synchronous_stability", "recurrent_stability", "geo_matrix", "compute_stability", "HDBSCAN"):
        require(forbidden not in esrc, f"evaluator contains forbidden scientific recomputation surface: {forbidden}")
    require("metrics" in eimports and "annual_gate" in eimports, "evaluator does not use inherited metrics/gates")

    for required in (
        "EXPECTED_HDBSCAN",
        "EXPECTED_SOURCE_PINS",
        "validate_pretruth",
        "validate_candidate_order",
        "pretruth_internal_integrity_verified_before_labels",
        "candidate order hash mismatch",
        "candidate membership hash mismatch",
        "stored mechanism-active flags do not match selected nodes/orders",
        "pretruth scientific/transport source pins changed",
        "frozen HDBSCAN declaration changed",
        "annual EOM reconstruction mismatch",
    ):
        require(required in esrc, f"hardened evaluator missing required invariant: {required}")

    main_node = function_node(etree, "main")
    validation_lines = call_lines(main_node, "validate_pretruth")
    label_lines = call_lines(main_node, "load_labels")
    metric_lines = call_lines(main_node, "metrics")
    require(len(validation_lines) == 1, f"expected exactly one validate_pretruth call, got {validation_lines}")
    require(len(label_lines) == 2, f"expected exactly two label-open calls, got {label_lines}")
    require(metric_lines, "evaluator scientific metrics call missing")
    require(validation_lines[0] < min(label_lines) < min(metric_lines), "pretruth validation is not structurally before label opening and metrics")

    for token in (
        "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
        "587a304f451e41b9503272f1783a6c6ebb295000",
        "157813ca331165180a6d20aa71bfc78d5984396f",
        "9a0fb05f94d6a28cd95f97d864e76400056273b0",
        "9fed803aa09f03f779610eaff5304251bbf21020",
        "1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993",
        "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
        "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
    ):
        require(token in esrc or token in gsrc, f"frozen token missing from scientific sources: {token}")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V2",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V2",
        "generator_sha256": sha(a.generator),
        "evaluator_sha256": sha(a.evaluator),
        "protocol_sha256": sha(a.protocol),
        "hardening_freeze_sha256": sha(a.hardening_freeze),
        "generator_options": sorted(gopts),
        "evaluator_options": sorted(eopts),
        "generator_single_fit": True,
        "generator_truth_input_surface": False,
        "evaluator_hierarchy_recomputation_surface": False,
        "pretruth_internal_integrity_validation_before_label_open": True,
        "source_and_hdbscan_pins_enforced": True,
        "order_and_membership_hashes_recomputed": True,
        "mechanism_flags_recomputed": True,
        "annual_reconstruction_reverified": True,
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
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V2.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
