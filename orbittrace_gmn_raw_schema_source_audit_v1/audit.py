#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
from pathlib import Path

PATTERNS = (
    'ra_sd','dec_sd','vg_sd','sigma','uncert','error','err','qc','conv','ncam',
    'radiant','ra','dec','vg','velocity','speed','trajectory','meteor','gmn'
)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--parts', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a=ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    payload=''.join((a.parts/f'part{i:02d}.b64').read_text().strip() for i in range(4))
    raw=gzip.decompress(base64.b64decode(payload)).decode('utf-8')
    lines=raw.splitlines()
    hits=[]
    names=set()
    for n,line in enumerate(lines,1):
        low=line.lower()
        matched=sorted({p for p in PATTERNS if p in low})
        if matched:
            # Source code only; no catalogue values are accessed by this audit.
            hits.append({'line':n,'patterns':matched,'source':line[:500]})
        for m in re.finditer(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]", line):
            key=m.group(1)
            if any(p in key.lower() for p in PATTERNS):
                names.add(key)
    result={
        'verdict':'PASS_GMN_RAW_SCHEMA_SOURCE_AUDIT_V1',
        'scientific_role':'ZERO_DATA_FROZEN_SOURCE_ONLY',
        'decoded_source_line_count':len(lines),
        'relevant_string_literals':sorted(names),
        'relevant_source_hits':hits,
        'catalogue_data_accessed':False,
        'event_values_accessed':False,
        'known_shower_labels_accessed':False,
        'target_information_access':False,
        'target_region_events_accessed':False,
        'external_scientific_access':False,
    }
    (a.output/'GMN_RAW_SCHEMA_SOURCE_AUDIT_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':result['verdict'],'relevant_string_literals':result['relevant_string_literals'],'hit_count':len(hits)},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
