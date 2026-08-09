#!/usr/bin/env python3
"""Implementation-only correction for the frozen P3 patch generator.

The first generator accidentally declared the large inserted source block as a raw
triple-quoted string while encoding source line boundaries with ``\n`` escapes.
That would emit literal backslash-n tokens between Python statements.  This wrapper
changes only that Python-string delimiter from raw to ordinary before executing the
already-frozen transform.  Inside-source ``"\\n"`` string literals remain escaped
correctly because they are double-backslashed in the generator source.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

V1_NAME = "apply_crossfit_seed_floor_patch.py"
EXPECTED_V1_BLOB = ""  # verified by the GitHub source-audit workflow via git hash-object


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_crossfit_seed_floor_patch_v2.py CANONICAL_P2_V2.py OUTPUT.py")
    v1 = Path(__file__).with_name(V1_NAME)
    text = v1.read_text(encoding="utf-8")
    needle = "AFTER_FINAL_FIT = r'''"
    replacement = "AFTER_FINAL_FIT = '''"
    if text.count(needle) != 1:
        raise RuntimeError(f"unexpected raw crossfit block marker count: {text.count(needle)}")
    corrected = text.replace(needle, replacement, 1)
    # This is the sole correction.  The frozen transform anchors/scientific content
    # are otherwise byte-identical to v1.
    ns = {"__name__": "orbittrace_p3_corrected_generator", "__file__": str(v1)}
    exec(compile(corrected, str(v1), "exec"), ns)
    old_argv = sys.argv
    try:
        sys.argv = [str(v1), old_argv[1], old_argv[2]]
        result = int(ns["main"]())
    finally:
        sys.argv = old_argv
    out = Path(old_argv[2])
    if result == 0:
        compile(out.read_text(encoding="utf-8"), str(out), "exec")
        print(f"P3_CROSSFIT_V2_OUTPUT_SHA256={hashlib.sha256(out.read_bytes()).hexdigest()}")
        print("P3_CROSSFIT_V2_CORRECTION=raw-string delimiter only; scientific transform unchanged")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
