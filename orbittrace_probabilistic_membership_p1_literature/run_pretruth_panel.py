#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import runpy
import sys
from pathlib import Path

INTERMEDIATE = Path(__file__).with_name("run_pretruth_panel_intermediate.py")
INTERMEDIATE_SHA256 = "af0c48e185793514ea98e90bdeb0fcf18be60751deeb7c818fac0c2d11b1cb1e"
RUNTIME_SHA256 = "127ff2af8cd2597736cedbb4eab19cecdf7985e89f65c5267eda46e97ed82dcb"
BEFORE = "    support.CORPUS = 'p1-sonotaco-exact-row-pretruth'\n"
AFTER = "    support.CORPUS = 'sonotaco-exact-row-literature-pairwise'\n"
RUNTIME = Path('/tmp/orbittrace_p1_matched_pretruth_protocol_exact.py')


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    raw = INTERMEDIATE.read_bytes()
    if sha256(raw) != INTERMEDIATE_SHA256:
        raise RuntimeError(f"P1 matched intermediate source identity changed: {sha256(raw)}")
    text = raw.decode('utf-8')
    required = "ordered_family_ids = [str(eid) for eid in family['event_ids']]"
    if required not in text:
        raise RuntimeError('deterministic immutable seed ordering correction absent')
    if text.count(BEFORE) != 1:
        raise RuntimeError('exact-v8 corpus patch anchor not unique')
    patched = text.replace(BEFORE, AFTER, 1)
    if patched.replace(AFTER, BEFORE, 1) != text:
        raise RuntimeError('exact-v8 corpus patch not exactly reversible')
    payload = patched.encode('utf-8')
    if sha256(payload) != RUNTIME_SHA256:
        raise RuntimeError(f"P1 matched runtime identity changed: {sha256(payload)}")
    RUNTIME.write_bytes(payload)
    print(f"P1_MATCHED_EXECUTION_RUNTIME_SHA256={RUNTIME_SHA256}", flush=True)
    print('P1_MATCHED_EXECUTION_CORPUS=sonotaco-exact-row-literature-pairwise', flush=True)
    old_argv0 = sys.argv[0]
    try:
        sys.argv[0] = str(RUNTIME)
        runpy.run_path(str(RUNTIME), run_name='__main__')
    finally:
        sys.argv[0] = old_argv0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
