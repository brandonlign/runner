#!/usr/bin/env python3
"""Implementation-only transform-order correction for frozen P4 generator.

The P4 science block replacement removes the original P2 responsibility block.  The
first generator attempted to rename the inherited expanded-membership fields after
that large replacement.  This wrapper moves the same exact field rename before the
large block replacement; no scientific text, threshold, model, split or gate changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
V1=HERE/'apply_p4_patch.py'
OLD='''    text = replace_once(text, HELPER_ANCHOR, HELPER_REPL, "P4 helper insertion")
    start = text.index(SCIENCE_START)
    end = text.index(SCIENCE_END, start)
    text = text[:start] + SCIENCE_REPL + text[end:]
    text = replace_once(text, ADD_KEY_ANCHOR, ADD_KEY_REPL, "P4 addition keys")
'''
NEW='''    text = replace_once(text, HELPER_ANCHOR, HELPER_REPL, "P4 helper insertion")
    text = replace_once(text, ADD_KEY_ANCHOR, ADD_KEY_REPL, "P4 addition keys")
    start = text.index(SCIENCE_START)
    end = text.index(SCIENCE_END, start)
    text = text[:start] + SCIENCE_REPL + text[end:]
'''


def main()->int:
    source=V1.read_text(encoding='utf-8')
    if source.count(OLD)!=1:
        raise RuntimeError(f'unexpected P4 generator ordering anchor count={source.count(OLD)}')
    corrected=source.replace(OLD,NEW,1)
    ns={'__name__':'orbittrace_p4_generator_v2','__file__':str(V1)}
    exec(compile(corrected,str(V1),'exec'),ns)
    old_argv=sys.argv
    try:
        sys.argv=[str(V1),*old_argv[1:]]
        result=int(ns['main']())
    finally:
        sys.argv=old_argv
    print('P4_GENERATOR_V2_CORRECTION=membership field rename moved before responsibility-block replacement only')
    return result


if __name__=='__main__':
    raise SystemExit(main())
