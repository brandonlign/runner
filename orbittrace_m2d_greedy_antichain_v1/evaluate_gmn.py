#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    raw_args = list(sys.argv[1:])
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--recursive-evaluator", type=Path, required=True)
    ap.add_argument("--refined-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    known, _ = ap.parse_known_args(raw_args)
    req(sha(known.refined_pretruth) == known.expected_pretruth_sha, "sealed antichain pretruth changed")
    original = json.loads(known.refined_pretruth.read_text())
    req(original.get("schema") == "ORBITTRACE_M2D_GREEDY_ANTICHAIN_V1_PRETRUTH", "wrong antichain schema")
    req(original.get("scientific_role") == "TARGET_EXCLUDED_GMN_GREEDY_M2D_ANTICHAIN_FROZEN_BEFORE_TRUTH", "wrong antichain role")
    req(original.get("shower_truth_used") is False and original.get("target_information_access") is False and original.get("target_region_events_accessed") is False, "pretruth firewall")
    req(original.get("orbittrace_reveal_access") is False and original.get("sonotaco_scientific_access") is False, "reveal/external firewall")
    req(original.get("configuration", {}).get("new_tuned_parameters") == [] and original.get("post_result_parameter_search") is False, "post-result tuning")

    compat = json.loads(json.dumps(original))
    compat["schema"] = "ORBITTRACE_M2D_RECURSIVE_EVIDENCE_CUT_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_RECURSIVE_M2D_EVIDENCE_CUT_FROZEN_BEFORE_TRUTH"
    compat["total_evidence_split_count"] = int(original["total_overlap_rejection_count"])

    recursive = load(known.recursive_evaluator, "greedy_antichain_frozen_truth_evaluator")
    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        compat_path = td / "compat_pretruth.json"
        compat_path.write_text(json.dumps(compat, separators=(",", ":"), sort_keys=True) + "\n")
        compat_sha = sha(compat_path)
        translated = []
        skip_next = False
        for i, token in enumerate(raw_args):
            if skip_next:
                skip_next = False
                continue
            if token == "--recursive-evaluator":
                skip_next = True
                continue
            if token == "--refined-pretruth":
                translated.extend([token, str(compat_path)])
                skip_next = True
                continue
            if token == "--expected-pretruth-sha":
                translated.extend([token, compat_sha])
                skip_next = True
                continue
            translated.append(token)
        old = sys.argv
        try:
            sys.argv = [old[0], *translated]
            rc = int(recursive.main() or 0)
        finally:
            sys.argv = old
        req(rc == 0, "frozen evaluator failed")

    # Rewrite only provenance/schema names after scoring; metrics and gates are untouched.
    req("--output" in raw_args, "missing --output")
    out_path = Path(raw_args[raw_args.index("--output") + 1])
    result = json.loads(out_path.read_text())
    result["schema"] = "ORBITTRACE_M2D_GREEDY_ANTICHAIN_V1_GMN_RESULT"
    result["pretruth_sha256"] = known.expected_pretruth_sha
    result["compatibility_pretruth_sha256"] = compat_sha
    result["evaluation_compatibility_translation"] = "schema/role/mechanism-counter only; candidate memberships, ordering, budgets, truth, Hungarian evaluator, metrics, and frozen gates unchanged"
    result["verdict"] = result["verdict"].replace("M2D_RECURSIVE_EVIDENCE_CUT_V1", "M2D_GREEDY_ANTICHAIN_V1")
    result["total_overlap_rejection_count"] = int(original["total_overlap_rejection_count"])
    result.pop("total_evidence_split_count", None)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "routes": result["routes"], "scales": result["scales"], "size_summary": result["size_summary"], "gates": result["gates"], "result_sha256": sha(out_path)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
