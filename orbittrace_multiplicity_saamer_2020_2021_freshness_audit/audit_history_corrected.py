#!/usr/bin/env python3
"""Corrected SAAMER freshness audit: citation-only title metadata is not data exposure."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT=Path('output'); OUT.mkdir(exist_ok=True)
SELF_PREFIXES=(
    'orbittrace_multiplicity_saamer_2020_2021_freshness_audit/',
    '.github/workflows/orbittrace-multiplicity-saamer-2020-2021-freshness-audit',
)
CITATION_PATH='orbittrace_literature_comparison/WAVELET_EPISODE_PROTOCOL.json'
CITATION_TITLE='A comparative study of radar and optical observations of meteor showers using SAAMER-OS and CAMS'


def run(*args:str)->str:
    return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL)


def refs()->list[str]:
    return [x for x in run('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines() if x and not x.endswith('/HEAD')]


def grep_ref(ref:str,pattern:str)->list[dict]:
    p=subprocess.run(['git','grep','-n','-I','-E',pattern,ref,'--'],text=True,capture_output=True)
    if p.returncode not in (0,1): raise RuntimeError(p.stderr)
    pref=ref+':'; out=[]
    for line in p.stdout.splitlines():
        if not line.startswith(pref): continue
        parts=line[len(pref):].split(':',2)
        if len(parts)!=3: continue
        path,ln,text=parts
        if path.startswith(SELF_PREFIXES): continue
        out.append({'ref':ref,'path':path,'line':int(ln),'text':text[:1000]})
    return out


def dedup(xs:list[dict])->list[dict]:
    seen=set(); out=[]
    for x in xs:
        k=(x['path'],x['line'],x['text'])
        if k not in seen: seen.add(k); out.append(x)
    return out


def collect(rs:list[str],patterns:list[str])->list[dict]:
    xs=[]
    for r in rs:
        for p in patterns: xs.extend(grep_ref(r,p))
    return dedup(xs)


def classify(h:dict)->str:
    if h['path']==CITATION_PATH and CITATION_TITLE in h['text']:
        return 'literature_citation_only'
    return 'potential_data_or_scientific_exposure'


def main()->int:
    rs=refs()
    hits=collect(rs,[r'SAAMER|Saamer|saamer',r'iaumdcSAAMER2020|iaumdcSAAMER2021',r'radio_offline/iaumdcSAAMER'])
    for h in hits: h['classification']=classify(h)
    suspicious=[h for h in hits if h['classification']=='potential_data_or_scientific_exposure']

    edmond=collect(rs,[r'iaumdcedmond2017',r'EDMOND[^\n]{0,100}2017|2017[^\n]{0,100}EDMOND'])
    sonotaco=collect(rs,[r'SNMv3/023a',r'sonotaco[^\n]{0,100}2023|2023[^\n]{0,100}sonotaco'])
    edmond_actual=any('edmond2017_external/' in h['path'] or 'ghoststream_external/' in h['path'] for h in edmond)
    sonotaco_actual=any('sonotaco-2023' in h['path'].lower() or 'sonotaco_2023' in h['path'].lower() for h in sonotaco)

    verdict='PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if not suspicious and edmond_actual and sonotaco_actual else 'FAIL_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    result={
        'verdict':verdict,
        'refs_scanned':len(rs),
        'candidate_years':[2020,2021],
        'all_saamer_hits':hits,
        'all_saamer_hit_count':len(hits),
        'potential_exposure_hits':suspicious,
        'potential_exposure_hit_count':len(suspicious),
        'literature_citation_only_count':sum(h['classification']=='literature_citation_only' for h in hits),
        'catalogue_access_this_audit':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'positive_controls':{
            'edmond_2017_spent_detected':edmond_actual,
            'sonotaco_2023_spent_detected':sonotaco_actual,
        },
        'claim_boundary':'A pass establishes repository-history scientific freshness only. The sole permitted SAAMER occurrence is a bibliographic paper-title citation; no SAAMER archive/data/result may have a hit. No SAAMER archive is accessed by this audit.',
    }
    (OUT/'saamer_2020_2021_repo_freshness_audit_corrected.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
    return 0


if __name__=='__main__': raise SystemExit(main())
