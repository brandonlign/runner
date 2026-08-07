#!/usr/bin/env python3
"""Repository-history audit for SAAMER 2020/2021 before any SAAMER archive access."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path('output')
OUT.mkdir(exist_ok=True)
SELF_PREFIXES = (
    'orbittrace_multiplicity_saamer_2020_2021_freshness_audit/',
    '.github/workflows/orbittrace-multiplicity-saamer-2020-2021-freshness-audit',
)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refs() -> list[str]:
    return [
        x for x in run('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines()
        if x and not x.endswith('/HEAD')
    ]


def grep_ref(ref: str, pattern: str) -> list[dict]:
    proc = subprocess.run(['git','grep','-n','-I','-E',pattern,ref,'--'], text=True, capture_output=True)
    if proc.returncode not in (0,1):
        raise RuntimeError(proc.stderr)
    prefix = ref + ':'
    hits=[]
    for line in proc.stdout.splitlines():
        if not line.startswith(prefix):
            continue
        rest=line[len(prefix):]
        parts=rest.split(':',2)
        if len(parts)!=3:
            continue
        path,lineno,text=parts
        if path.startswith(SELF_PREFIXES):
            continue
        hits.append({'ref':ref,'path':path,'line':int(lineno),'text':text[:1000]})
    return hits


def dedup(hits: list[dict]) -> list[dict]:
    seen=set(); out=[]
    for h in hits:
        key=(h['path'],h['line'],h['text'])
        if key not in seen:
            seen.add(key); out.append(h)
    return out


def collect(refs_: list[str], patterns: list[str]) -> list[dict]:
    hits=[]
    for ref in refs_:
        for pattern in patterns:
            hits.extend(grep_ref(ref,pattern))
    return dedup(hits)


def main() -> int:
    all_refs=refs()
    # Broad SAAMER scan plus exact annual archive names. Any pre-existing hit is treated
    # conservatively as exposure until manually adjudicated; audit code itself is excluded.
    saamer=collect(all_refs,[
        r'SAAMER|Saamer|saamer',
        r'iaumdcSAAMER2020|iaumdcSAAMER2021',
        r'radio_offline/iaumdcSAAMER',
    ])

    # Cross-survey positive controls prove the full-ref grep can see known-spent external data.
    edmond_pc=collect(all_refs,[r'iaumdcedmond2017',r'EDMOND[^\n]{0,100}2017|2017[^\n]{0,100}EDMOND'])
    sonotaco_pc=collect(all_refs,[r'SNMv3/023a|sonotaco[^\n]{0,100}2023|2023[^\n]{0,100}sonotaco'])
    edmond_actual=any('edmond2017_external/' in h['path'] or 'ghoststream_external/' in h['path'] for h in edmond_pc)
    sonotaco_actual=any('sonotaco-2023' in h['path'].lower() or 'sonotaco_2023' in h['path'].lower() for h in sonotaco_pc)

    verdict = (
        'PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
        if not saamer and edmond_actual and sonotaco_actual
        else 'FAIL_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    )
    result={
        'verdict':verdict,
        'refs_scanned':len(all_refs),
        'saamer_hits':saamer,
        'saamer_hit_count':len(saamer),
        'candidate_years':[2020,2021],
        'catalogue_access_this_audit':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'positive_controls':{
            'edmond_2017_spent_detected':edmond_actual,
            'edmond_2017_hit_count':len(edmond_pc),
            'sonotaco_2023_spent_detected':sonotaco_actual,
            'sonotaco_2023_hit_count':len(sonotaco_pc),
        },
        'official_archive_names_not_accessed':[
            'iaumdcSAAMER2020.zip',
            'iaumdcSAAMER2021.zip',
        ],
        'claim_boundary':'A pass establishes only repository-history scientific freshness. No SAAMER archive is requested or inspected by this audit. Structural compatibility and scientific evaluation require separately frozen later stages.',
    }
    (OUT/'saamer_2020_2021_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'):
        raise SystemExit(1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
