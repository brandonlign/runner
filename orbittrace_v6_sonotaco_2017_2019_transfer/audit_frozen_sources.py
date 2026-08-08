#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path

EXPECTED_PARSER_SHA = {
    2017: "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",
    2019: "301a711e4de43566ba434f2d4a94fc38a85714a33dcee45e26cb19340101ea43",
}
EXPECTED_REPAIRED_V6_SHA = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_assignments(tree: ast.Module) -> dict[str, object]:
    out: dict[str, object] = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try:
                out[n.targets[0].id] = ast.literal_eval(n.value)
            except Exception:
                pass
    return out


def function_sources(text: str) -> dict[str, str]:
    tree = ast.parse(text)
    return {
        n.name: ast.get_source_segment(text, n) or ""
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def audit_parser(path: Path, year: int) -> None:
    require(sha(path) == EXPECTED_PARSER_SHA[year], f"parser {year} source identity changed")
    text = path.read_text()
    blind = 'if BLIND_SOLAR_MIN <= sol <= BLIND_SOLAR_MAX:'
    label = 'token = row[index["shower"]]'
    require(blind in text and label in text and text.index(blind) < text.index(label), f"parser {year} blind ordering changed")
    require('"blind_interval_removed_before_label_access": True' in text, f"parser {year} blind audit marker missing")
    require('"at_least_30_distinct_labeled_showers": distinct_showers >= 30' in text, f"parser {year} mapped-shower identity gate changed")
    require('"at_least_30_supported_native_codes": len(supported_codes) >= 30' in text, f"parser {year} obsolete gate anchor changed")


def audit_repaired_v6(path: Path) -> None:
    require(sha(path) == EXPECTED_REPAIRED_V6_SHA, "repaired v6 source identity changed")
    text = path.read_text(); defs = function_sources(text)
    require("calibrate_year_v6" in defs and "scan_year_v6" in defs, "v6 calibration/scan functions missing")
    cal = defs["calibrate_year_v6"]; scan = defs["scan_year_v6"]
    for token in (
        "for bin_index in range(36)",
        "range(old.CALIBRATION_PER_BIN)",
        "if len(v3_calibration) < 30:",
        "insufficient supported calibration bins",
    ):
        require(token in cal, f"v6 calibration rule changed: {token}")
    require(scan.index("calibrate_year_v6(") < scan.index("event_lookup ="), "v6 calibration no longer precedes survey scan")


def audit_corrected_runner(path: Path) -> None:
    text = path.read_text(); tree = ast.parse(text); vals = literal_assignments(tree); defs = function_sources(text)
    expected = {
        "YEARS": (2017, 2019),
        "MIN_BACKGROUND_EVENTS": 10000,
        "MIN_DISTINCT_MAPPED_SHOWERS": 30,
        "MIN_SUPPORTED_V6_CALIBRATION_BINS": 30,
        "MIN_V3_PRIMARY_FAMILIES": 40,
        "RECOVERY100_RETENTION": 0.80,
        "QUALIFIED_RETENTION": 0.60,
        "TOP100_PRECISION_FLOOR": 0.50,
        "MRR_RETENTION": 0.80,
        "IMPROVEMENT_ENDPOINTS": ("recovered_at_25", "recovered_at_50", "recovered_at_100", "mrr", "macro_f1"),
    }
    for key, value in expected.items():
        require(vals.get(key) == value, f"transfer constant changed {key}={vals.get(key)!r}")
    pre = defs["preflight_before_survey_scoring"]
    require("v6.calibrate_year_v6(" in pre, "preflight no longer uses exact v6 calibration")
    require("current_v6_transfer(" not in pre and "exact_v8_transfer(" not in pre and "scan_year_v6(" not in pre, "survey scoring entered preflight")
    require('"survey_candidate_scores_computed": False' in pre and '"null_calibration_only": True' in pre, "preflight boundary markers changed")
    main = defs["main"]
    i_pre = main.index("preflight_before_survey_scoring(")
    i_v6 = main.index("legacy.current_v6_transfer(")
    i_v8 = main.index("run_true_v8_same_universe(")
    i_f1 = main.index('(args.output / "current_v6_pretruth.sha256").write_text')
    i_f2 = main.index('(args.output / "true_v8_pretruth.sha256").write_text')
    i_truth = main.index("current_full = v6.evaluate_families_v6(")
    require(i_pre < i_v6 < i_f1 < i_truth and i_pre < i_v8 < i_f2 < i_truth, "transfer chronology changed")
    require('math.floor(RECOVERY100_RETENTION * int(v8_metrics["recovered_at_100"]))' in main, "recovery retention gate changed")
    require('math.floor(QUALIFIED_RETENTION * int(v8_metrics["qualified_matches"]))' in main, "qualified retention gate changed")
    require('MRR_RETENTION * float(v8_metrics["mrr"])' in main, "MRR retention gate changed")
    require("any(strict_improvements.values())" in main, "strict-improvement gate changed")
    require("development_v6_mrr" not in main, "obsolete development-MRR transfer gate returned")
    for gate in (
        "at_least_40_recurrent_v3_primary_families",
        "recovery100_at_least_floor_080_v8",
        "qualified_at_least_floor_060_v8",
        "top100_dominant_precision_at_least_050",
        "mrr_at_least_080_v8",
        "at_least_one_frozen_endpoint_strictly_exceeds_v8",
    ):
        require(gate in main, f"missing scientific gate {gate}")


def audit_parallel(path: Path) -> None:
    text = path.read_text(); tree = ast.parse(text); defs = function_sources(text)
    imports: list[str] = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            imports.extend(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or "")
    require(not any(x in {"numpy", "math", "scipy", "sklearn"} or x.startswith(("numpy.", "scipy.", "sklearn.")) for x in imports), "accelerator reimplements scientific math")
    worker = ast.parse(defs["_run_chunk"])
    calls = []
    for n in ast.walk(worker):
        if isinstance(n, ast.Call):
            f = n.func
            calls.append(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "<dynamic>")
    require(calls.count("_ORIGINAL") == 1 and set(calls) <= {"_ORIGINAL", "RuntimeError"}, f"accelerator worker call surface changed: {calls}")
    install = defs["install"]
    require("worker_count = min(requested, cpu_count, 4)" in install, "accelerator worker ceiling changed")
    require("pool.map(_run_chunk, chunks, chunksize=1)" in install, "accelerator order-preserving map changed")
    require("output_ids != input_ids" in install, "accelerator output-order guard missing")


def audit_entry(path: Path) -> None:
    text = path.read_text(); defs = function_sources(text)
    pre = defs["exact_namespace_preflight"]
    require("old.YEARS = corrected.YEARS" in pre and "old.MONTH_KEYS = tuple()" in pre, "preflight transfer year namespace changed")
    require("old.CORPUS = corrected.legacy.CORPUS_V6" in pre, "preflight calibration corpus seed namespace changed")
    load = defs["accelerated_load_module"]
    require('name == "orbittrace_transfer_corrected_v6"' in load, "accelerator no longer restricted to current v6")
    require("install_parallel_exact(module, workers=4, min_parallel_records=256)" in load, "accelerator configuration changed")
    main = defs["main"]
    require("corrected.preflight_before_survey_scoring = exact_namespace_preflight" in main, "preflight wrapper not installed")
    require("corrected.legacy.load_module = accelerated_load_module" in main, "v6 accelerator loader not installed")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--parser-2019", required=True, type=Path)
    p.add_argument("--repaired-v6", required=True, type=Path)
    p.add_argument("--corrected-runner", required=True, type=Path)
    p.add_argument("--parallel-wrapper", required=True, type=Path)
    p.add_argument("--entry", required=True, type=Path)
    a = p.parse_args()
    audit_parser(a.parser_2017, 2017)
    audit_parser(a.parser_2019, 2019)
    audit_repaired_v6(a.repaired_v6)
    audit_corrected_runner(a.corrected_runner)
    audit_parallel(a.parallel_wrapper)
    audit_entry(a.entry)
    print("PASS_PROTOCOL_EXACT_V6_SONOTACO_2017_2019_TRANSFER_SOURCE_AUDIT")
    print("NO_CATALOGUE_ARCHIVE_NO_LABEL_VALUES_NO_TARGET_REGION_NO_ORBITTRACE_TARGET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
