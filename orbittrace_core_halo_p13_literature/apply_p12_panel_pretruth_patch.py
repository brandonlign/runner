#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path

EXPECTED_P12_SHA256='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32'
EXPECTED_PANEL_SOURCE_SHA256='4c2ee663541fe00ec959b3e3d0ec7d9e5bf2fad062bf9f8b709a3d7bedbde6ae'
PATCH_PATH=Path(__file__).with_name('P12_PANEL_PATCH_B64.txt')


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: apply_p12_panel_pretruth_patch.py EXACT_P12 OUTPUT')
    source=Path(sys.argv[1]); output=Path(sys.argv[2])
    raw=source.read_bytes(); actual=sha(raw)
    if actual!=EXPECTED_P12_SHA256:
        raise RuntimeError(f'exact P12 source SHA changed: {actual}')
    patches=json.loads(zlib.decompress(base64.b64decode(PATCH_PATH.read_text().strip(),validate=True)).decode())
    lines=raw.decode().splitlines(keepends=True)
    for patch in sorted(patches,key=lambda item:int(item['s']),reverse=True):
        lines[int(patch['s']):int(patch['e'])]=str(patch['r']).splitlines(keepends=True)
    text=''.join(lines); result=sha(text.encode())
    if result!=EXPECTED_PANEL_SOURCE_SHA256:
        raise RuntimeError(f'P12 matched-panel transform SHA mismatch: {result}')
    for forbidden in ('OrbitTrace-April','target_coordinate'):
        if forbidden in text:
            raise RuntimeError(f'forbidden target token introduced: {forbidden}')
    output.write_text(text)
    print(f'P13_MATCHED_P12_INPUT_SHA256={EXPECTED_P12_SHA256}')
    print(f'P13_MATCHED_P12_OUTPUT_SHA256={result}')
    print('P13_MATCHED_P12_PATCH_SCOPE=exact P12 membership transported to strict SonotaCo 2023/2025 pairwise panel inputs; years/universe input only; stop after complete pretruth core/halo decision freeze before truth/comparator access')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
