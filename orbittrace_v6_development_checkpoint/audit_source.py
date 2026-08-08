#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import pickle
import py_compile
from pathlib import Path

FROZEN_SHA = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"

BEFORE = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    components = primary_components + rescue_components
'''
AFTER = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components
'''


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(frozen_root: Path) -> tuple[str, str]:
    parts = sorted((frozen_root / "orbittrace_v3_catalogue_v6/exact_parts").glob("part*.b64"))
    require(parts, "no frozen source parts")
    encoded = "".join(p.read_text() for p in parts).replace("\n", "").replace("\r", "")
    original = gzip.decompress(base64.b64decode(encoded)).decode()
    require(hashlib.sha256(original.encode()).hexdigest() == FROZEN_SHA, "frozen source SHA mismatch")
    require(original.count(BEFORE) == 1, "two-line repair anchor is not unique")
    repaired = original.replace(BEFORE, AFTER, 1)
    require(repaired.replace(AFTER, BEFORE, 1) == original, "repair is not exactly reversible")
    return original, repaired


def call_names(fn: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            out.append(f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "<dynamic>"))
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--recovery-root", type=Path, required=True)
    p.add_argument("--frozen-root", type=Path, required=True)
    args = p.parse_args()

    original, repaired = reconstruct(args.frozen_root)
    repaired_sha = hashlib.sha256(repaired.encode()).hexdigest()
    print("FROZEN_V6_SHA256=" + FROZEN_SHA)
    print("REPAIRED_V6_SHA256=" + repaired_sha)
    print("PASS_EXACT_TWO_LINE_REPAIR_RECONSTRUCTION")

    recovery_dir = args.recovery_root / "orbittrace_v6_development_checkpoint"
    run_path = recovery_dir / "run_year.py"
    replay_path = recovery_dir / "replay_main.py"
    protocol_path = recovery_dir / "PROTOCOL.md"
    require(run_path.exists() and replay_path.exists() and protocol_path.exists(), "missing recovery source")

    temp = Path("/tmp/orbittrace_v6_repaired_for_audit.py")
    temp.write_text(repaired)
    for path in (temp, run_path, replay_path):
        py_compile.compile(str(path), doraise=True)

    tree = ast.parse(repaired)
    defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    required = {"main", "evaluate_families_v6", "build_family_track_v6", "scan_year_v6"}
    require(required <= set(defs), f"missing frozen functions {sorted(required-set(defs))}")
    frozen_main = defs["main"]

    scan_calls: list[tuple[int, str | None]] = []
    for node in ast.walk(frozen_main):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "<dynamic>")
            if name == "scan_year_v6":
                scan_calls.append((node.lineno, ast.get_source_segment(repaired, node)))
    require(len(scan_calls) == 1, f"unexpected frozen scan calls {scan_calls}")
    require("scan_by_year[year]" in (scan_calls[0][1] or ""), "scan input binding changed")
    require("calibration_by_year[year]" in (scan_calls[0][1] or ""), "calibration input binding changed")

    year_loop = next(
        n for n in frozen_main.body
        if isinstance(n, ast.For) and ast.get_source_segment(repaired, n.iter) == "YEARS"
    )
    year_loop_src = ast.get_source_segment(repaired, year_loop) or ""
    require("scan_year_v6" in year_loop_src, "year loop no longer scans")
    require("build_family_track_v6" not in year_loop_src, "family construction entered year loop")
    require("evaluate_families_v6" not in year_loop_src, "evaluation entered year loop")
    family_line = next(
        n.lineno for n in ast.walk(frozen_main)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "build_family_track_v6"
    )
    evaluation_line = next(
        n.lineno for n in ast.walk(frozen_main)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "evaluate_families_v6"
    )
    require(year_loop.end_lineno is not None and year_loop.end_lineno < family_line < evaluation_line,
            "post-scan order changed")

    run_text = run_path.read_text()
    run_tree = ast.parse(run_text)
    run_calls = call_names(run_tree)
    require(run_calls.count("scan_year_v6") == 1, "year checkpoint must call scan_year_v6 exactly once")
    require("build_family_track_v6" not in run_calls and "evaluate_families_v6" not in run_calls,
            "year checkpoint performs downstream science")
    require("ordered_scan_ids_sha256" in run_text and "ordered_calibration_ids_sha256" in run_text,
            "year input identity hashes missing")
    require("truth_used_for_scan" in run_text and "target_access" in run_text, "checkpoint firewall flags missing")

    replay_text = replay_path.read_text()
    ast.parse(replay_text)
    require("v6.scan_year_v6 = replay_scan_year_v6" in replay_text, "replay does not replace only scan call")
    require("result = v6.main()" in replay_text, "replay bypasses frozen main")
    require("build_family_track_v6" not in replay_text and "evaluate_families_v6" not in replay_text,
            "replay reimplements downstream science")
    for token in ("ordered scan universe changed", "ordered calibration universe changed", "catalogue source identity changed"):
        require(token in replay_text, f"replay identity guard missing: {token}")
    forbidden = {
        "PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT",
        "FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT",
        "recovered_at_100",
        "top100_dominant_precision",
        "qualified_matches",
    }
    require(all(token not in replay_text for token in forbidden), "replay contains scientific verdict/gate logic")

    representative = {
        "audit": {"supported_bins": [1, 2], "x": 0.12345678901234568},
        "anchors": [{"id": "a"}],
        "components": [{"event_ids": ["a", "b"]}],
        "flag": False,
    }
    raw = pickle.dumps(representative, protocol=pickle.HIGHEST_PROTOCOL)
    require(pickle.loads(raw) == representative, "checkpoint roundtrip changed native objects")

    print("FROZEN_MAIN_SCAN_LOOP_END=" + str(year_loop.end_lineno))
    print("FROZEN_MAIN_FAMILY_LINE=" + str(family_line))
    print("FROZEN_MAIN_EVALUATION_LINE=" + str(evaluation_line))
    print("RUN_YEAR_SHA256=" + sha(run_path))
    print("REPLAY_MAIN_SHA256=" + sha(replay_path))
    print("RECOVERY_PROTOCOL_SHA256=" + sha(protocol_path))
    print("AUDIT_SOURCE_SHA256=" + sha(Path(__file__)))
    print("PASS_V6_DEVELOPMENT_CACHED_YEAR_REPLAY_SOURCE_AUDIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
