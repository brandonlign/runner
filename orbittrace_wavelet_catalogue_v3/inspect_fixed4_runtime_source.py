#!/usr/bin/env python3
"""Source-only inspection of frozen fixed4 geometry for runtime equivalence work."""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path("orbittrace_fixed4_support_wrapper_development/source_parts")
EXPECTED_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
TARGETS = {"exact_anchor_distances", "quartet_score"}


def main() -> None:
    parts = sorted(ROOT.glob("part*.b64"))
    expected = [f"part{i:02d}.b64" for i in range(4)]
    if [p.name for p in parts] != expected:
        raise RuntimeError([p.name for p in parts])
    encoded = "".join("".join(p.read_text(encoding="ascii").split()) for p in parts)
    payload = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"frozen support source changed: {digest}")
    text = payload.decode("utf-8")
    tree = ast.parse(text)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in TARGETS:
            found[node.name] = ast.get_source_segment(text, node)
    if set(found) != TARGETS:
        raise RuntimeError(f"missing targets: {sorted(TARGETS - set(found))}")
    print("PASS_FROZEN_FIXED4_SOURCE_GUARD", digest)
    for name in sorted(found):
        print(f"FIXED4_SOURCE_BEGIN {name}")
        print(found[name])
        print(f"FIXED4_SOURCE_END {name}")


if __name__ == "__main__":
    main()
