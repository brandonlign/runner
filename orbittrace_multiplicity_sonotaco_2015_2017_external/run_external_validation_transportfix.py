#!/usr/bin/env python3
"""Implementation-only wrapper: patch four pre-data transport/provenance literals."""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).with_name("run_external_validation.py")
REPLACEMENTS = {
    "88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3":
        "3d3d5439ec3e4db50ae79e4ea1ef7df02768be949ee24c5e68b01357b63a3d18",
    "bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3":
        "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",
    "https://sonotaco.jp/doc/SNMv3/015a.zip":
        "https://www.astro.sk/iaumdcDB/PDA/SNMv3/015a.zip",
    "https://sonotaco.jp/doc/SNMv3/017a.zip":
        "https://www.astro.sk/iaumdcDB/PDA/SNMv3/017a.zip",
}


def main() -> int:
    source = SOURCE.read_text()
    for old, new in REPLACEMENTS.items():
        if source.count(old) != 1:
            raise RuntimeError(f"unexpected replacement occurrence count for {old}: {source.count(old)}")
        if new in source:
            raise RuntimeError(f"replacement already present in frozen source: {new}")

    patched = source
    for old, new in REPLACEMENTS.items():
        patched = patched.replace(old, new)

    before = source.splitlines()
    after = patched.splitlines()
    if len(before) != len(after):
        raise RuntimeError("transport patch changed line count")
    changed = [(i + 1, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if len(changed) != 4:
        raise RuntimeError(f"transport patch changed {len(changed)} lines, expected 4")
    olds = set(REPLACEMENTS)
    news = set(REPLACEMENTS.values())
    found_old = {old for _, a, _ in changed for old in olds if old in a}
    found_new = {new for _, _, b in changed for new in news if new in b}
    if found_old != olds or found_new != news:
        raise RuntimeError("transport patch did not change exactly the four frozen literals")

    out = Path("/tmp/orbittrace_run_external_validation_transportfixed.py")
    out.write_text(patched)
    print("PASS_TRANSPORTFIX_EXACTLY_FOUR_LINES")
    print("original_sha256", hashlib.sha256(source.encode()).hexdigest())
    print("patched_sha256", hashlib.sha256(patched.encode()).hexdigest())
    os.execv(sys.executable, [sys.executable, str(out), *sys.argv[1:]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
