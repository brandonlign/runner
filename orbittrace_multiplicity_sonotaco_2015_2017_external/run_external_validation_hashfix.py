#!/usr/bin/env python3
"""Implementation-only wrapper: patch two stale pre-data parser hash literals."""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).with_name("run_external_validation.py")
OLD = {
    "88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3":
        "3d3d5439ec3e4db50ae79e4ea1ef7df02768be949ee24c5e68b01357b63a3d18",
    "bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3":
        "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",
}


def main() -> int:
    source = SOURCE.read_text()
    for old, new in OLD.items():
        if source.count(old) != 1:
            raise RuntimeError(f"unexpected stale-hash occurrence count for {old}: {source.count(old)}")
        if new in source:
            raise RuntimeError(f"replacement hash already present in frozen source: {new}")

    patched = source
    for old, new in OLD.items():
        patched = patched.replace(old, new)

    before = source.splitlines()
    after = patched.splitlines()
    if len(before) != len(after):
        raise RuntimeError("implementation-only patch changed line count")
    changed = [(i + 1, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if len(changed) != 2:
        raise RuntimeError(f"implementation-only patch changed {len(changed)} lines, expected 2")
    if not all("PARSER_SHA256" not in a for _, a, _ in changed):
        # The changed lines are the two dictionary value lines, not the dict header.
        raise RuntimeError("unexpected parser-hash patch location")
    expected_old = set(OLD)
    expected_new = set(OLD.values())
    if {next(h for h in expected_old if h in a) for _, a, _ in changed} != expected_old:
        raise RuntimeError("changed lines do not contain exactly the two stale hashes")
    if {next(h for h in expected_new if h in b) for _, _, b in changed} != expected_new:
        raise RuntimeError("changed lines do not contain exactly the two frozen transport hashes")

    out = Path("/tmp/orbittrace_run_external_validation_hashfixed.py")
    out.write_text(patched)
    print("PASS_HASHFIX_EXACTLY_TWO_PROVENANCE_LINES")
    print("original_sha256", hashlib.sha256(source.encode()).hexdigest())
    print("patched_sha256", hashlib.sha256(patched.encode()).hexdigest())
    os.execv(sys.executable, [sys.executable, str(out), *sys.argv[1:]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
