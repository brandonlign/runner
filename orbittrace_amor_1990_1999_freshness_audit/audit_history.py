#!/usr/bin/env python3
"""Full-repository scientific-freshness audit for IAU MDC AMOR 1990-1999; no catalogue access."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT=Path('output'); OUT.mkdir(exist_ok=True)
SELF_PREFIXES=(
    'orbittrace_amor_1990_1999_freshness_audit/',
    '.github/workflows/orbittrace-amor-1990-1999-freshness-audit',
)


def run(*args:str)->str:
    return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL)


def refs()->list[str]:
    return [x for x in run('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines() if x and not x.endswith('/HEAD')]


def grep_ref(ref:str,pattern:str)->list[dict]:
    p=subprocess.run(['git','grep','-n','-I','-E',pattern,ref,'--'],text=True,capture_output=True)
    if p.returncode not in (0,1):
        raise RuntimeError(p.stderr)
    prefix=ref+':'
    rows=[]
    for line in p.stdout.splitlines():
        if not line.startswith(prefix):
            continue
        parts=line[len(prefix):].split(':',2)
        if len(parts)!=3:
            continue
        path,line_number,text=parts
        if path.startswith(SELF_PREFIXES):
            continue
        rows.append({'ref':ref,'path':path,'line':int(line_number),'text':text[:1200]})
    return rows


def dedup(rows:list[dict])->list[dict]:
    out=[]; seen=set()
    for row in rows:
        key=(row['path'],row['line'],row['text'])
        if key not in seen:
            seen.add(key); out.append(row)
    return out


def collect(rs:list[str],patterns:list[str])->list[dict]:
    rows=[]
    for ref in rs:
        for pattern in patterns:
            rows.extend(grep_ref(ref,pattern))
    return dedup(rows)


def main()->int:
    rs=refs()
    hits=collect(rs,[
        r'\bAMOR\b|\bAmor\b|\bamor\b',
        r'AMOR[^\n]{0,100}199[0-9]|199[0-9][^\n]{0,100}AMOR',
        r'radio_offline[^\n]{0,100}AMOR|AMOR[^\n]{0,100}radio_offline',
    ])
    archive_token=re.compile(r'AMOR[_-]?199[0-9]|iaumdc[^\s"\']*AMOR|AMOR[^\s"\']*\.zip|radio_offline[^\n]{0,100}AMOR',re.I)
    scientific_token=re.compile(r'archive|download|parser|parse|row|meteor|catalog|data|result|score|cluster|family|component|radiant|\bLS\b|\bRA\b|\bDEC\b|\bVg\b|\bq\b|\be\b|\bi\b|\barg\b|\bnod\b|orbit',re.I)
    bibliographic_token=re.compile(r'citation|reference|paper|Baggaley|radar facility|Meteoroids|published',re.I)
    suspicious=[]; provenance=[]
    for hit in hits:
        text=hit['text']
        path=hit['path'].lower()
        looks_like_science_path=any(x in path for x in ('amor','external','validation','result','parser','catalog','data'))
        if archive_token.search(text) or (scientific_token.search(text) and not bibliographic_token.search(text)) or looks_like_science_path:
            hit['classification']='potential_data_or_scientific_exposure'; suspicious.append(hit)
        else:
            hit['classification']='bibliographic_or_general_reference_only'; provenance.append(hit)

    # Positive controls prove the history scan sees actually consumed survey work.
    spent_saamer=collect(rs,[r'orbittrace_label_free_v6_saamer_external',r'iaumdcSAAMER2020|iaumdcSAAMER2021'])
    spent_saamer_actual=any('orbittrace_label_free_v6_saamer_external/' in h['path'] for h in spent_saamer)
    spent_sonotaco=collect(rs,[r'SNMv3/023a',r'sonotaco[^\n]{0,80}2023|2023[^\n]{0,80}sonotaco'])
    spent_sonotaco_actual=any('sonotaco-2023' in h['path'].lower() or 'sonotaco_2023' in h['path'].lower() for h in spent_sonotaco)

    verdict='PASS_AMOR_1990_1999_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if not suspicious and spent_saamer_actual and spent_sonotaco_actual else 'FAIL_AMOR_1990_1999_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    result={
        'verdict':verdict,
        'refs_scanned':len(rs),
        'candidate_catalogue':'IAU MDC AMOR',
        'candidate_years':list(range(1990,2000)),
        'candidate_hits':hits,
        'candidate_hit_count':len(hits),
        'potential_exposure_hits':suspicious,
        'potential_exposure_hit_count':len(suspicious),
        'bibliographic_or_general_reference_hits':provenance,
        'catalogue_access_this_audit':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'positive_controls':{
            'saamer_2020_2021_spent_detected':spent_saamer_actual,
            'sonotaco_2023_spent_detected':spent_sonotaco_actual,
        },
        'claim_boundary':'A pass establishes repository-history scientific freshness for the IAU MDC AMOR 1990-1999 radio catalogue pool only. This audit downloads no AMOR archive and reads no AMOR meteor value.',
    }
    (OUT/'amor_1990_1999_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'):
        raise SystemExit(1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
