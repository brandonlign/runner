#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_TRANSPORT_SHA256 = "f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae"
NEEDLE = "seed_years = sorted(set(int(seed_id[:4]) for seed_id in seed_ids))"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_p12_snm_id_transport.py EXACT_P12_PANEL")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    actual = sha256(path)
    if actual != EXPECTED_TRANSPORT_SHA256:
        raise RuntimeError(f"existing exact P12 matched transport SHA changed: {actual}")
    if text.count(NEEDLE) != 1:
        raise RuntimeError(f"remaining seed-year prefix anchor count={text.count(NEEDLE)}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token present")

    tree = ast.parse(text)
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    fn = functions.get("source_observation_model")
    if fn is None:
        raise RuntimeError("source_observation_model missing")
    start = int(fn.lineno)
    end = int(getattr(fn, "end_lineno", start))
    lines = text.splitlines()
    print(f"P12_MATCHED_TRANSPORT_SHA256={actual}")
    print(f"SOURCE_OBSERVATION_MODEL_LINES={start}:{end}")
    for n in range(start, end + 1):
        print(f"{n:04d}: {lines[n-1]}")

    prefix_hits = []
    for n, line in enumerate(lines, 1):
        if "[:4]" in line or "int(str(eid)[:4])" in line or "int(seed_id[:4])" in line:
            prefix_hits.append((n, line.strip()))
    print("P12_PREFIX_YEAR_PARSE_HITS", prefix_hits)
    if prefix_hits != [(start + 10, NEEDLE)]:
        # Keep this fail-closed: the exact source context must be inspected before any repair.
        raise RuntimeError(f"unexpected remaining year-prefix parse surface: {prefix_hits}")

    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "source_observation_model":
            calls.append((node.lineno, ast.unparse(node)))
    print("SOURCE_OBSERVATION_MODEL_CALLS", calls)
    if len(calls) != 1:
        raise RuntimeError(f"source_observation_model call count={len(calls)}")

    print("PASS_P14_P12_SNM_ID_TRANSPORT_SOURCE_DIAGNOSTIC_NO_DATA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
