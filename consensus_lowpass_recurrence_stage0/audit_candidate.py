#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

CANDIDATE_SHA256 = "9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa"
MAJORITY_SHA256 = "3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts", required=True, type=Path)
    parser.add_argument("--majority-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    majority_hash = hashlib.sha256(args.majority_source.read_bytes()).hexdigest()
    if majority_hash != MAJORITY_SHA256:
        raise RuntimeError(f"majority source mismatch: {majority_hash}")

    parts = sorted(args.parts.glob("part*.b64"))
    if [part.name for part in parts] != ["part00.b64", "part01.b64"]:
        raise RuntimeError(f"unexpected candidate parts: {[part.name for part in parts]}")
    encoded = "".join("".join(part.read_text().split()) for part in parts)
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if digest != CANDIDATE_SHA256:
        raise RuntimeError(f"candidate source mismatch: {digest}")

    text = source.decode("utf-8")
    tree = ast.parse(text)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"PERSISTENT_ACTIVE_YEARS", "CONSENSUS_SMOOTH_SIGMA"}
    }

    checks = {
        "persistent_active_years_exactly_12": assignments.get("PERSISTENT_ACTIVE_YEARS") == 12,
        "smooth_sigma_is_exact_inherited_scale": assignments.get("CONSENSUS_SMOOTH_SIGMA") == (1.6, 1.6, 1.0, 0.9),
        "ideal_null_sampler_definition_retained": "sample_year_histograms" in functions,
        "ideal_null_sampler_is_called": "sample_year_histograms" in calls,
        "shared_structure_sampler_definition_retained": "sample_shared_structure_histograms" in functions,
        "shared_structure_sampler_is_called": "sample_shared_structure_histograms" in calls,
        "recurrent_injector_retained": "inject_recurrent" in functions,
        "transient_injector_retained": "inject_transient" in functions,
        "annual_median_present": "consensus_evidence = np.median(per_year_evidence, axis=0)" in text,
        "smooth_consensus_present": "sigma=CONSENSUS_SMOOTH_SIGMA" in text,
        "smooth_only_subtraction_present": "per_year_evidence - smooth_consensus[None, ...]" in text,
        "third_year_recurrence_retained": "consensus_lowpass_score = ordered_consensus[-self.r_required]" in text,
        "persistent_shared_condition_present": "persistent_shared_records" in text,
        "persistent_shared_uses_shared_null": "persistent_base = sample_shared_structure_histograms" in text,
        "majority_comparator_retained": '"majority_conditioned"' in text,
        "candidate_method_key_present": '"consensus_lowpass"' in text,
        "candidate_verdict_present": "CONTINUE_CONSENSUS_LOWPASS_FULL_STAGE0" in text,
        "original_minority_condition_retained": "recurrent_records" in text,
        "one_year_artifact_condition_retained": "transient_records" in text,
    }
    if not all(checks.values()):
        raise RuntimeError(f"static candidate check failed: {checks}")

    candidate = args.output / "run_consensus_lowpass.py"
    candidate.write_bytes(source)
    audit = {
        "parent_majority_sha256": majority_hash,
        "candidate_sha256": digest,
        "candidate_bytes": len(source),
        "candidate_lines": len(text.splitlines()),
        "functions": sorted(functions),
        "called_module_functions": sorted(calls),
        "checks": checks,
    }
    (args.output / "source_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output / "RESULT.md").write_text(
        "# Consensus-lowpass candidate source audit\n\n"
        f"- parent majority source SHA-256: `{majority_hash}`\n"
        f"- candidate source SHA-256: `{digest}`\n"
        f"- candidate bytes: **{len(source):,}**\n"
        f"- candidate lines: **{len(text.splitlines()):,}**\n"
        "- all AST and frozen semantic checks: **PASS**\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
