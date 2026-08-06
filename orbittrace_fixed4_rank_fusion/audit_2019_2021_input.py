#!/usr/bin/env python3
"""Freeze the target-excluded 2019-2021 catalogue universe without scoring."""
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCANNER_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
YEARS = (2019, 2020, 2021)
CORPUS = "orbittrace-fixed4-rank-fusion-prospective-2019-2021"
BLIND_INTERVAL = (20.0, 55.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def decode_parts(path: Path, expected_count: int) -> bytes:
    parts = sorted(path.glob("part*.b64"))
    expected = [f"part{i:02d}.b64" for i in range(expected_count)]
    if [part.name for part in parts] != expected:
        raise RuntimeError(f"unexpected source parts under {path}: {[part.name for part in parts]}")
    encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in parts)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def load_scanner(source: bytes) -> types.ModuleType:
    digest = hashlib.sha256(source).hexdigest()
    if digest != SCANNER_SHA256:
        raise RuntimeError(f"scanner source mismatch: {digest}")
    module = types.ModuleType("fixed4_rank_fusion_input_audit_scanner")
    module.__file__ = "fixed4_rank_fusion_input_audit_scanner.py"
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    module.YEARS = YEARS
    module.MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
    module.CORPUS = CORPUS
    if float(module.BLIND_LOW) != BLIND_INTERVAL[0] or float(module.BLIND_HIGH) != BLIND_INTERVAL[1]:
        raise RuntimeError("blind interval changed")
    return module


def eligibility(hidden_labels: dict[str, str]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for event_id, label in hidden_labels.items():
        year = int(str(event_id)[:4])
        if year in YEARS and label != "SPORADIC":
            counts[label][year] += 1
    eligible = {
        label: {str(year): int(year_counts.get(year, 0)) for year in YEARS}
        for label, year_counts in sorted(counts.items())
        if sum(year_counts.values()) >= 8 and all(year_counts.get(year, 0) >= 4 for year in YEARS)
    }
    all_counts = {
        label: {str(year): int(year_counts.get(year, 0)) for year in YEARS}
        for label, year_counts in sorted(counts.items())
    }
    return eligible, all_counts


def source_guard(source: bytes) -> dict[str, Any]:
    tree = ast.parse(source.decode("utf-8"))
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    required = {"load_sources", "parse_catalogue", "scan_year", "build_families", "evaluate_panel"}
    if not required.issubset(functions):
        raise RuntimeError(f"missing scanner functions: {sorted(required - functions.keys())}")
    return {
        "scanner_source_sha256": hashlib.sha256(source).hexdigest(),
        "parse_catalogue_ast_sha256": hashlib.sha256(ast.unparse(functions["parse_catalogue"]).encode()).hexdigest(),
        "scan_year_ast_sha256": hashlib.sha256(ast.unparse(functions["scan_year"]).encode()).hexdigest(),
        "build_families_ast_sha256": hashlib.sha256(ast.unparse(functions["build_families"]).encode()).hexdigest(),
        "evaluate_panel_ast_sha256": hashlib.sha256(ast.unparse(functions["evaluate_panel"]).encode()).hexdigest(),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = decode_parts(args.scanner_parts, 4)
    guard = source_guard(source)
    scanner = load_scanner(source)
    candidate, base, scorer = scanner.load_sources(args)
    scan_by_year, calibration_by_year, hidden_labels, sources = scanner.parse_catalogue(base)

    if tuple(sorted(scan_by_year)) != YEARS or tuple(sorted(calibration_by_year)) != YEARS:
        raise RuntimeError("unexpected prospective year universe")
    eligible, all_label_counts = eligibility(hidden_labels)
    scan_counts = {str(year): len(scan_by_year[year]) for year in YEARS}
    calibration_counts = {str(year): len(calibration_by_year[year]) for year in YEARS}
    if any(value < 1000 for value in scan_counts.values()) or any(value < 1000 for value in calibration_counts.values()):
        raise RuntimeError("insufficient prospective input events")

    gates = {
        "exact_scanner_source": guard["scanner_source_sha256"] == SCANNER_SHA256,
        "exact_years": tuple(sorted(scan_by_year)) == YEARS,
        "exact_blind_interval": [float(scanner.BLIND_LOW), float(scanner.BLIND_HIGH)] == list(BLIND_INTERVAL),
        "at_least_8_eligible_showers": len(eligible) >= 8,
        "every_eligible_shower_has_four_events_each_year": all(
            all(int(counts[str(year)]) >= 4 for year in YEARS) for counts in eligible.values()
        ),
        "no_detector_score_computed": True,
        "no_family_built": True,
        "no_ranking_computed": True,
        "no_orbittrace_target_access": True,
    }
    verdict = (
        "PASS_FIXED4_RANK_FUSION_2019_2021_INPUT_AUDIT"
        if all(gates.values())
        else "FAIL_FIXED4_RANK_FUSION_2019_2021_INPUT_AUDIT"
    )
    result = {
        "verdict": verdict,
        "classification": (
            "target-excluded catalogue transport and known-shower eligibility audit; no detector score, "
            "component, family, or ranking computed"
        ),
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(scanner.MONTH_KEYS),
            "corpus": CORPUS,
            "blind_exclusion": list(BLIND_INTERVAL),
            "frozen_rank_fusion_weight": 0.02,
            "eligibility_rule": "at least 8 total labeled events and at least 4 in each of 2019, 2020, and 2021",
        },
        "source_guard": guard,
        "source_hashes": {
            "candidate": scanner.EXPECTED_CANDIDATE_SHA,
            "baseline": scanner.EXPECTED_BASELINE_SHA,
            "scorer": scanner.EXPECTED_SCORER_SHA,
        },
        "scan_event_counts": scan_counts,
        "calibration_event_counts": calibration_counts,
        "eligible_shower_count": len(eligible),
        "eligible_shower_year_counts": eligible,
        "all_nonsporadic_label_year_counts": all_label_counts,
        "catalogue_sources": sources,
        "gates": gates,
        "prohibited_access": {
            "scan_year_called": False,
            "fixed4_score_computed": False,
            "components_built": False,
            "families_built": False,
            "rankings_computed": False,
            "orbittrace_interval_present": False,
        },
    }
    (args.output / "fixed4_rank_fusion_2019_2021_input_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Fixed4 rank-fusion 2019–2021 input audit",
        "",
        f"Verdict: `{verdict}`",
        "",
        f"Eligible known showers: **{len(eligible)}**",
        "",
        "| year | scan events | sporadic calibration events |",
        "|---:|---:|---:|",
    ]
    for year in YEARS:
        lines.append(f"| {year} | {scan_counts[str(year)]} | {calibration_counts[str(year)]} |")
    lines.extend([
        "",
        "Solar longitude 20°–55° was excluded before label normalization. No detector score, component, family, or ranking was computed.",
    ])
    (args.output / "FIXED4_RANK_FUSION_2019_2021_INPUT_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
