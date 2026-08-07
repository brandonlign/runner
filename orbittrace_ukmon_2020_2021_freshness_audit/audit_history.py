#!/usr/bin/env python3
"""Full-repository zero-data freshness audit for UKMON 2020/2021."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT=Path('output'); OUT.mkdir(exist_ok=True)
TARGETS=(2020,2021)
SELF=(
    'orbittrace_ukmon_2020_2021_freshness_audit/',
    '.github/workflows/orbittrace-ukmon-2020-2021-freshness-audit',
)
UKMON_MARKER=re.compile(r'UKMON|UK Meteor (Observation|Network)|UK Meteor Network|ukmeteors\.co\.uk|api\.ukmeteors\.co\.uk|archive\.ukmeteors\.co\.uk|ukmda',re.I)
YEAR_LITERAL=re.compile(r'(?<!\d)(2020|2021)(?!\d)')
DATE_LITERAL=re.compile(r'(?<!\d)(2020|2021)\d{4}(?!\d)')
RANGE=re.compile(r'range\(\s*(\d{4})\s*,\s*(\d{4})\s*\)')


def run(*args:str)->str:
    return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL)


def refs()->list[str]:
    return [x for x in run('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines() if x and not x.endswith('/HEAD')]


def ukmon_paths(ref:str)->set[str]:
    p=subprocess.run(['git','grep','-l','-I','-E',UKMON_MARKER.pattern,ref,'--'],text=True,capture_output=True)
    if p.returncode not in (0,1): raise RuntimeError(p.stderr)
    prefix=ref+':'
    paths=set()
    for line in p.stdout.splitlines():
        if not line.startswith(prefix): continue
        path=line[len(prefix):]
        if path.startswith(SELF): continue
        paths.add(path)
    return paths


def file_text(ref:str,path:str)->str:
    p=subprocess.run(['git','show',f'{ref}:{path}'],text=True,capture_output=True,errors='replace')
    if p.returncode!=0: return ''
    return p.stdout


def evidence(ref:str,path:str,text:str)->list[dict]:
    rows=[]
    lines=text.splitlines()
    for i,line in enumerate(lines,1):
        if YEAR_LITERAL.search(line) or DATE_LITERAL.search(line):
            rows.append({'ref':ref,'path':path,'line':i,'text':line[:1200],'reason':'literal_target_year_in_ukmon_related_file'})
    for m in RANGE.finditer(text):
        start,end=map(int,m.groups())
        covered=list(range(start,end))
        hit=sorted(set(covered).intersection(TARGETS))
        if hit:
            line=text.count('\n',0,m.start())+1
            rows.append({'ref':ref,'path':path,'line':line,'text':m.group(0),'reason':'python_range_includes_target_year','dynamic_range_years':hit})
    # Path itself can encode a consumed year even if the payload line is generic.
    if re.search(r'2020|2021',path):
        rows.append({'ref':ref,'path':path,'line':0,'text':'','reason':'target_year_in_ukmon_related_path'})
    return rows


def dedup(rows:list[dict])->list[dict]:
    seen=set(); out=[]
    for row in rows:
        key=(row['path'],row['line'],row['reason'],row.get('text',''))
        if key not in seen:
            seen.add(key); out.append(row)
    return out


def main()->int:
    rs=refs(); hits=[]; ukmon_file_count=0
    positive={'ukmon_2022_interface_detected':False,'ukmon_2024_2025_external_detected':False}
    for ref in rs:
        for path in ukmon_paths(ref):
            ukmon_file_count += 1
            low=path.lower()
            if 'ukmon_2022_interface' in low or 'ukmon-2022-interface' in low:
                positive['ukmon_2022_interface_detected']=True
            if 'ukmon_2024_2025' in low or 'ukmon-2024-2025' in low:
                positive['ukmon_2024_2025_external_detected']=True
            text=file_text(ref,path)
            hits.extend(evidence(ref,path,text))
    suspicious=dedup(hits)
    verdict=(
        'PASS_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
        if not suspicious and all(positive.values())
        else 'FAIL_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    )
    result={
        'verdict':verdict,
        'refs_scanned':len(rs),
        'ukmon_related_file_occurrences_scanned':ukmon_file_count,
        'candidate_years':[2020,2021],
        'potential_exposure_hits':suspicious,
        'potential_exposure_hit_count':len(suspicious),
        'positive_controls':positive,
        'catalogue_access_this_audit':False,
        'meteor_api_contacted':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'claim_boundary':'Full remote-branch repository-history audit only. A pass reserves UKMON 2020/2021 against prior project use; it does not contact UKMON or authorize scientific access. A separate structure/interface protocol is required before any 2020/2021 meteor value is requested.',
    }
    (OUT/'ukmon_2020_2021_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
    return 0

if __name__=='__main__': raise SystemExit(main())
