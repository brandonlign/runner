#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PARENT_TRANSPORT_SHA256='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
TECHNICAL_TRANSPORT_SHA256='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
OLD=f"P13_TRANSPORT_SOURCE_SHA256='{PARENT_TRANSPORT_SHA256}'\n"
NEW=f"P13_TRANSPORT_SOURCE_SHA256='{TECHNICAL_TRANSPORT_SHA256}'\n"


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: prepare_transport_compatible_p13_finalizer.py BASE OUTPUT')
    src,out=map(Path,sys.argv[1:])
    text=src.read_text(encoding='utf-8')
    if text.count(OLD)!=1:
        raise RuntimeError(f'P13 transport provenance constant count={text.count(OLD)}')
    if TECHNICAL_TRANSPORT_SHA256 in text:
        raise RuntimeError('technical transport SHA already present in immutable base')
    patched=text.replace(OLD,NEW,1)
    if patched.replace(NEW,OLD,1)!=text:
        raise RuntimeError('transport-compatible finalizer differs outside one provenance constant')
    for token in ('four_to_nine_gain_ge_0_10','four_to_twentyfour_gain_ge_0_10','macro_f1_not_more_than_0_10_lower','retain_at_least_80pct_f1_gt_0_5_count'):
        if patched.count(token)!=text.count(token) or token not in patched:
            raise RuntimeError(f'benchmark gate changed: {token}')
    for token in ('OrbitTrace-April','target_coordinate'):
        if token in patched:
            raise RuntimeError(f'forbidden target token present: {token}')
    out.write_text(patched,encoding='utf-8')
    print('PASS_P14_P13_FINALIZER_TRANSPORT_PROVENANCE_ONLY_PATCH')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
