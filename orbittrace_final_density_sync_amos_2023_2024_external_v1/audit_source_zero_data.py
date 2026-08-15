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


def call_count(tree: ast.AST, attr: str) -> int:
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == attr)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
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
    require(all("label" not in x and "truth" not in x and "shower" not in x for x in gopts), "generator accepts a truth-bearing argument")
    require("csv" not in gimports, "generator unexpectedly imports CSV/truth transport")
    require("density_synchronous_stability" in gimports and "recurrent_stability" in gimports, "generator does not bind both frozen recurrent kernels")
    require(call_count(gtree, "fit") == 1, "generator must fit exactly one pooled HDBSCAN hierarchy")

    require(eopts == {"--pretruth", "--pretruth-sha256", "--labels-2023", "--labels-2024", "--output"}, f"evaluator CLI surface changed: {sorted(eopts)}")
    require("hdbscan" not in eimports, "evaluator must not import HDBSCAN")
    for forbidden in ("density_synchronous_stability", "recurrent_stability", "geo_matrix", "compute_stability", "HDBSCAN"):
        require(forbidden not in esrc, f"evaluator contains forbidden recomputation surface: {forbidden}")
    require("metrics" in eimports and "annual_gate" in eimports, "evaluator does not use frozen inherited metric/gate implementation")

    required_generator_tokens = (
        "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
        "587a304f451e41b9503272f1783a6c6ebb295000",
        "157813ca331165180a6d20aa71bfc78d5984396f",
        "9a0fb05f94d6a28cd95f97d864e76400056273b0",
        "9fed803aa09f03f779610eaff5304251bbf21020",
        "1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993",
        "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY",
        "density_synchronous_recurrent_eom_hdbscan_v1_pr1263",
    )
    for token in required_generator_tokens:
        require(token in gsrc, f"generator missing frozen identity/token: {token}")
    for token in (
        "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
        "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
        "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
        "NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
    ):
        require(token in esrc, f"evaluator missing frozen verdict token: {token}")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V1",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V1",
        "generator_sha256": sha(a.generator),
        "evaluator_sha256": sha(a.evaluator),
        "protocol_sha256": sha(a.protocol),
        "generator_options": sorted(gopts),
        "evaluator_options": sorted(eopts),
        "generator_single_fit": True,
        "generator_truth_input_surface": False,
        "evaluator_hierarchy_recomputation_surface": False,
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
    path = a.output / "FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
