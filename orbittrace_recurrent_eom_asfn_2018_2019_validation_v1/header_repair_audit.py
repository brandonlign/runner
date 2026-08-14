#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

PASS = "PASS_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT"
FAIL = "FAIL_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def raises_runtime(fn, tokens: list[str]) -> bool:
    try:
        fn(tokens)
    except RuntimeError:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", type=Path, required=True)
    ap.add_argument("--wrapper", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    repo = a.runner.resolve().parents[1]
    recurrent_dir = repo / "orbittrace_recurrent_eom_hdbscan_v1"
    if str(recurrent_dir) not in sys.path:
        sys.path.insert(0, str(recurrent_dir))

    runner = load(a.runner, "asfn_frozen_validation_audit_target")
    wrapper = load(a.wrapper, "asfn_hash_header_wrapper_audit_target")

    fields = tuple(runner.FIELDS)
    ordinary = list(fields)
    hash_header = ["#"] + list(fields)
    changed = list(hash_header)
    changed[5] = changed[5] + "_CHANGED"
    short = ["#"] + list(fields[:-1])
    data_like = ["20180101-00:00:00"] + ["0"] * 43
    arbitrary = ["not", "a", "header"]

    original = runner.header_or_record
    original_results = {
        "ordinary": bool(original(ordinary)),
        "hash_header": bool(original(hash_header)),
        "data_like": bool(original(data_like)),
        "blank": bool(original([])),
        "arbitrary": bool(original(arbitrary)),
    }

    frozen_names = (
        "FIELDS", "IDX", "YEARS", "BLIND", "ARCHIVE_SHA", "README_SHA",
        "MIN_CLUSTER_SIZE", "MIN_SAMPLES",
    )
    frozen_values = {name: runner.__dict__[name] for name in frozen_names}
    module_identity_before = {
        name: id(value)
        for name, value in runner.__dict__.items()
        if name != "header_or_record"
    }

    wrapper.install_header_repair(runner)
    repaired = runner.header_or_record

    repaired_results = {
        "ordinary": bool(repaired(ordinary)),
        "hash_header": bool(repaired(hash_header)),
        "changed_hash_header_raises": raises_runtime(repaired, changed),
        "short_hash_header_raises": raises_runtime(repaired, short),
        "data_like": bool(repaired(data_like)),
        "blank": bool(repaired([])),
        "arbitrary": bool(repaired(arbitrary)),
    }

    constants_unchanged = all(runner.__dict__[name] == frozen_values[name] for name in frozen_names)
    module_identity_after = {
        name: id(value)
        for name, value in runner.__dict__.items()
        if name != "header_or_record"
    }
    non_header_module_identity_unchanged = module_identity_before == module_identity_after

    source = a.wrapper.read_text()
    forbidden_fragments = (
        "requests", "urllib", "urlopen", "curl", "zipfile", "hdbscan",
        "MIN_CLUSTER_SIZE =", "MIN_SAMPLES =", "BLIND =", "YEARS =",
        "ARCHIVE_SHA =", "README_SHA =", "eom_labels", "recurrent_stability",
    )
    wrapper_forbidden_fragments_absent = all(x not in source for x in forbidden_fragments)

    checks = {
        "ordinary_original_true": original_results["ordinary"] is True,
        "ordinary_repaired_true": repaired_results["ordinary"] is True,
        "hash_original_false": original_results["hash_header"] is False,
        "hash_repaired_true": repaired_results["hash_header"] is True,
        "changed_hash_header_raises": repaired_results["changed_hash_header_raises"] is True,
        "short_hash_header_raises": repaired_results["short_hash_header_raises"] is True,
        "data_like_original_false": original_results["data_like"] is False,
        "data_like_repaired_false": repaired_results["data_like"] is False,
        "blank_preserved_false": original_results["blank"] is False and repaired_results["blank"] is False,
        "arbitrary_preserved_false": original_results["arbitrary"] is False and repaired_results["arbitrary"] is False,
        "constants_unchanged": constants_unchanged,
        "non_header_module_identity_unchanged": non_header_module_identity_unchanged,
        "wrapper_forbidden_fragments_absent": wrapper_forbidden_fragments_absent,
    }
    passed = all(checks.values())

    out = {
        "verdict": PASS if passed else FAIL,
        "checks": checks,
        "original_results": original_results,
        "repaired_results": repaired_results,
        "network_access": False,
        "asfn_archive_access": False,
        "asfn_event_value_access": False,
        "asfn_shw_access": False,
        "scientific_endpoint": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = a.output / "ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
