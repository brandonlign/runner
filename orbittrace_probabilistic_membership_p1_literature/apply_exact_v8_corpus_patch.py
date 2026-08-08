#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

BEFORE = "    support.CORPUS = 'p1-sonotaco-exact-row-pretruth'\n"
AFTER = "    support.CORPUS = 'sonotaco-exact-row-literature-pairwise'\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit('usage: apply_exact_v8_corpus_patch.py INPUT OUTPUT')
    source=Path(sys.argv[1]); output=Path(sys.argv[2])
    text=source.read_text()
    if text.count(BEFORE) != 1:
        raise RuntimeError('P1 matched exact-v8 corpus patch anchor not unique')
    # Deterministic seed ordering correction must already be present before the
    # exact-v8 namespace is pinned.
    required = "ordered_family_ids = [str(eid) for eid in family['event_ids']]"
    if required not in text:
        raise RuntimeError('deterministic immutable seed ordering correction absent')
    patched=text.replace(BEFORE,AFTER,1)
    if patched.replace(AFTER,BEFORE,1) != text:
        raise RuntimeError('P1 matched exact-v8 corpus patch is not reversible')
    output.write_text(patched)
    print('P1_MATCHED_INPUT_SOURCE_SHA256='+digest(text.encode()))
    print('P1_MATCHED_EXACT_V8_RUNTIME_SHA256='+digest(patched.encode()))
    print('P1_MATCHED_CORPUS=sonotaco-exact-row-literature-pairwise')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
