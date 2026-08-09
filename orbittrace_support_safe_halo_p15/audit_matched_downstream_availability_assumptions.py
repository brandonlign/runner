#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
TOKENS=(
    'direction_audits','feature_records','crossfit','model','proposal','membership',
    'source_year','target_year','negative_events','MIN_DIRECTION_NEGATIVES',
    '2 * len(families)','len(families) * 2','2*len(families)','len(families)*2',
    'len(direction_audits)','len(feature_records)','direction_key','direction_models',
    'features_by','model_by','records_by','p12_drift','p12_crossfit','p12_model',
)


def main()->int:
    if len(sys.argv)!=2: raise SystemExit('usage: audit_matched_downstream_availability_assumptions.py MATCHED_P15_SOURCE')
    p=Path(sys.argv[1]); raw=p.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED_SHA: raise RuntimeError(f'P15 matched source changed: {sha}')
    text=raw.decode(); lines=text.splitlines()
    tree=ast.parse(text)

    print('P15_MATCHED_SOURCE_SHA256',sha)
    print('P15_SOURCE_LINES',len(lines))
    print('=== TOKEN OCCURRENCES ===')
    hits=set()
    for i,line in enumerate(lines,1):
        if any(tok in line for tok in TOKENS):
            hits.add(i)
            print(f'{i:04d}: {line}')

    print('=== HIGH-RISK CONTEXT BLOCKS ===')
    anchors=[]
    needles=(
        'if len(negative_events) < MIN_DIRECTION_NEGATIVES:',
        'direction_audits.append(',
        'p15_unavailable_directions.append(',
        'p12_drift_pretruth.json',
        'p12_crossfit_pretruth.json',
        'p12_model_pretruth.json',
        'p12_density_pretruth.json',
        'for family in families:',
        'for source_year, target_year in',
        'for source_year in',
        'for target_year in',
    )
    for i,line in enumerate(lines,1):
        if any(n in line for n in needles): anchors.append(i)
    for i in sorted(set(anchors)):
        print(f'--- context around line {i} ---')
        for j in range(max(1,i-12),min(len(lines),i+26)+1):
            print(f'{j:04d}: {lines[j-1]}')

    print('=== AST LOOPS WITH DIRECTION NAMES ===')
    for node in ast.walk(tree):
        if isinstance(node,(ast.For,ast.comprehension)):
            src=ast.get_source_segment(text,node) or ''
            head=src.splitlines()[0] if src else ''
            if 'source_year' in head or 'target_year' in head or 'direction' in head or 'famil' in head:
                lineno=getattr(node,'lineno',-1)
                print(f'LOOP {lineno}: {head[:300]}')
        if isinstance(node,ast.Subscript):
            src=ast.get_source_segment(text,node) or ''
            if ('source_year' in src and 'target_year' in src) or 'direction' in src:
                print(f'SUBSCRIPT {getattr(node,"lineno",-1)}: {src[:300]}')

    print('=== REQUIRE ASSERTIONS WITH COUNTS/DIRECTIONS ===')
    for i,line in enumerate(lines,1):
        stripped=line.strip()
        if ('require(' in stripped or stripped.startswith('assert ')) and any(x in stripped for x in ('direction','len(','model','feature','proposal','family')):
            print(f'{i:04d}: {line}')

    # This diagnostic is intentionally non-adjudicative. It proves only that the
    # exact frozen source was inspected without data/truth and enumerates the
    # downstream control-flow surfaces that a preregistered availability repair
    # may need to address.
    for forbidden in ('OrbitTrace-April','target_coordinate'):
        if forbidden in text: raise RuntimeError(f'forbidden target token in source: {forbidden}')
    print('PASS_P15_DOWNSTREAM_AVAILABILITY_SOURCE_CONTEXT_ENUMERATED')
    print('NO_COMPARATOR_ARTIFACT_NO_ARCHIVE_NO_TRUTH_NO_EXTERNAL_NO_TARGET_ACCESS')
    return 0


if __name__=='__main__': raise SystemExit(main())
