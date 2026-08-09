#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_TRANSPORT_SHA256 = "f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae"
SEED_YEAR_NEEDLE = "seed_years = sorted(set(int(seed_id[:4]) for seed_id in seed_ids))"
KEY_YEAR_NEEDLE = "year = int(key[:4])"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enclosing_function(tree: ast.AST, line: int) -> str:
    candidates: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = int(node.lineno)
            end = int(getattr(node, "end_lineno", start))
            if start <= line <= end:
                candidates.append((end - start, node.name))
    return min(candidates)[1] if candidates else "<module>"


def print_context(lines: list[str], line: int, radius: int = 10) -> None:
    lo = max(1, line - radius)
    hi = min(len(lines), line + radius)
    for n in range(lo, hi + 1):
        marker = ">>>" if n == line else "   "
        print(f"{marker} {n:04d}: {lines[n-1]}")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_p12_snm_id_transport.py EXACT_P12_PANEL")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    actual = sha256(path)
    if actual != EXPECTED_TRANSPORT_SHA256:
        raise RuntimeError(f"existing exact P12 matched transport SHA changed: {actual}")
    if text.count(SEED_YEAR_NEEDLE) != 1:
        raise RuntimeError(f"remaining seed-year prefix anchor count={text.count(SEED_YEAR_NEEDLE)}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token present")

    tree = ast.parse(text)
    lines = text.splitlines()
    print(f"P12_MATCHED_TRANSPORT_SHA256={actual}")

    prefix_hits: list[tuple[int, str, str]] = []
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        if "[:4]" in line:
            prefix_hits.append((n, stripped, enclosing_function(tree, n)))
    print("P12_PREFIX_YEAR_PARSE_HITS", prefix_hits)
    expected_texts = [SEED_YEAR_NEEDLE, KEY_YEAR_NEEDLE, KEY_YEAR_NEEDLE]
    if [x[1] for x in prefix_hits] != expected_texts:
        raise RuntimeError(f"unexpected remaining year-prefix parse surface: {prefix_hits}")

    for line, statement, function in prefix_hits:
        print(f"\nPREFIX_PARSE_CONTEXT line={line} function={function} statement={statement!r}")
        print_context(lines, line, radius=12)

    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "source_observation_model":
            calls.append((node.lineno, enclosing_function(tree, int(node.lineno)), ast.unparse(node)))
    print("\nSOURCE_OBSERVATION_MODEL_CALLS", calls)
    if len(calls) != 1:
        raise RuntimeError(f"source_observation_model call count={len(calls)}")
    for line, function, call in calls:
        print(f"\nSOURCE_OBSERVATION_MODEL_CALL_CONTEXT line={line} function={function} call={call!r}")
        print_context(lines, line, radius=12)

    print("PASS_P14_P12_SNM_ID_TRANSPORT_SOURCE_DIAGNOSTIC_NO_DATA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
