#!/usr/bin/env python3
"""Semantic-neutral loader wrapper for exact frozen Sugar/HDBSCAN source bytes.

The historical runner's import helper executes modules without first registering them in
sys.modules. Python 3.11 dataclasses require that registration, and the frozen HDBSCAN
source imports its sibling literature_comparators module by name. This wrapper changes
only module-loading mechanics; comparator source bytes and scientific calls are identical.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_comparators_v1 import pretruth_comparators as comp


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> str:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_module_compat(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    # Required by Python 3.11 dataclasses and standard module semantics.
    sys.modules[name] = module
    source_dir = str(path.resolve().parent)
    inserted = source_dir not in sys.path
    if inserted:
        sys.path.insert(0, source_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted and sys.path and sys.path[0] == source_dir:
            sys.path.pop(0)
    return module


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--comparator", choices=["sugar", "hdbscan"], required=True)
    p.add_argument("--year", type=int, choices=[2013, 2014], required=True)
    p.add_argument("--rows", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    rows = json.loads(a.rows.read_text())
    require(isinstance(rows, list) and rows, "empty comparator rows")

    if a.comparator == "sugar":
        require(sha256_path(a.source) == comp.SUGAR_CORE_SHA256, "Sugar source identity changed")
        module = load_module_compat(a.source, "final_sugar_core")
        module.__source_sha256__ = comp.SUGAR_CORE_SHA256
        result = comp.run_sugar(rows, year=a.year, sugar=module)
    else:
        require(sha256_path(a.source) == comp.HDBSCAN_SOURCE_SHA256, "HDBSCAN source identity changed")
        sibling = a.source.parent / "literature_comparators.py"
        require(sibling.is_file(), "frozen HDBSCAN sibling literature_comparators.py missing")
        module = load_module_compat(a.source, "final_hdbscan_runner")
        module.__source_sha256__ = comp.HDBSCAN_SOURCE_SHA256
        result = comp.run_hdbscan(rows, year=a.year, hdbscan_runner=module, core_dist_jobs=1)

    source_manifest = {
        "comparator": result["method"],
        "year": a.year,
        "scientific_source_sha256": sha256_path(a.source),
        "adapter_sha256": sha256_path(Path(comp.__file__)),
        "loader_compatibility_only": True,
        "truth_labels_accepted": False,
        "target_information_access": False,
    }
    source_sha = dump(a.output / "comparator_source_manifest.json", source_manifest)
    result["source_manifest_sha256"] = source_sha
    primary_sha = dump(a.output / "comparator_primary_output.json", result)
    summary = {
        "verdict": "PASS_FINAL_PRETRUTH_COMPARATOR_OUTPUT_FREEZE",
        "comparator": a.comparator,
        "year": a.year,
        "primary_output_sha256": primary_sha,
        "source_manifest_sha256": source_sha,
        "family_count": result["retained_family_count"],
        "truth_accessed": False,
        "loader_compatibility_only": True,
    }
    dump(a.output / "comparator_pretruth_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
