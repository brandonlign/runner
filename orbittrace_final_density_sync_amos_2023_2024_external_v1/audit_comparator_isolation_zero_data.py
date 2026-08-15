#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

FORBIDDEN_PRIMARY_FIELDS = {
    "ra_sd_deg",
    "dec_sd_deg",
    "vg_sd_km_s",
    "convergence_angle_deg",
    "q_au",
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--old-contract", type=Path, required=True)
    p.add_argument("--old-selftest", type=Path, required=True)
    p.add_argument("--old-selftest-result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    gsrc = a.generator.read_text(encoding="utf-8")
    gtree = ast.parse(gsrc)
    opts = parser_options(gtree)
    require(opts == {"--canonical-2023", "--canonical-2024", "--output"}, "primary generator CLI surface changed")
    require("predata_contract" not in gsrc, "primary generator imports comparator supplement contract")
    for name in FORBIDDEN_PRIMARY_FIELDS:
        require(name not in gsrc, f"comparator-only field leaked into primary generator source: {name}")

    old = json.loads(a.old_selftest_result.read_text(encoding="utf-8"))
    require(old["verdict"] == "PASS_AMOS_MULTIMETHOD_PREDATA_CONTRACT_SELFTEST_V1", "old frozen comparator selftest did not pass")
    require(old["synthetic_only"] is True, "old comparator selftest was not synthetic-only")
    require(old["amos_data_accessed"] is False and old["amos_truth_accessed"] is False, "old comparator selftest accessed AMOS data/truth")
    require(old["comparator_only_fields_entered_recurrent_eom"] is False, "old comparator contract leaked optional fields")
    require(old["recurrent_projection_keys"] == ["id", "year", "sol", "sun_lon", "ecl_lat", "vg"], "old recurrent projection changed")

    result = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT_V1",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT_V1",
        "generator_sha256": sha(a.generator),
        "old_contract_sha256": sha(a.old_contract),
        "old_selftest_sha256": sha(a.old_selftest),
        "old_selftest_result_sha256": sha(a.old_selftest_result),
        "primary_generator_accepts_comparator_supplement": False,
        "comparator_only_fields_enter_primary_generator": False,
        "old_pairwise_projection_is_six_field_geometry_only": True,
        "synthetic_only": True,
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
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
