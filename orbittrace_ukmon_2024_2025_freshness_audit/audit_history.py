#!/usr/bin/env python3
"""Zero-data full-history audit for reserved UKMON 2024/2025 external panel."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path

OUT=Path('output'); OUT.mkdir(exist_ok=True)
SELF=('orbittrace_ukmon_2024_2025_freshness_audit/','.github/workflows/orbittrace-ukmon-2024-2025-freshness-audit')

def run(*args): return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL)
def refs(): return [r for r in run('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines() if r and not r.endswith('/HEAD')]
def grep_ref(ref,pat):
    p=subprocess.run(['git','grep','-n','-I','-E',pat,ref,'--'],text=True,capture_output=True)
    if p.returncode not in (0,1): raise RuntimeError(p.stderr)
    out=[]; prefix=ref+':'
    for line in p.stdout.splitlines():
        if not line.startswith(prefix): continue
        parts=line[len(prefix):].split(':',2)
        if len(parts)!=3: continue
        path,ln,text=parts
        if path.startswith(SELF): continue
        out.append({'ref':ref,'path':path,'line':int(ln),'text':text[:1200]})
    return out

def collect(rs,pats):
    seen=set(); out=[]
    for ref in rs:
        for pat in pats:
            for row in grep_ref(ref,pat):
                key=(row['path'],row['line'],row['text'])
                if key not in seen: seen.add(key); out.append(row)
    return out

def main():
    rs=refs()
    candidate=collect(rs,[
        r'UKMON|UK Meteor (Observation|Network)|UK Meteor Network',
        r'ukmeteors\.co\.uk|api\.ukmeteors\.co\.uk|archive\.ukmeteors\.co\.uk',
        r'ukmda|ukmda-dataprocessing',
    ])
    # Any repository hit is conservative potential exposure except generic literature prose.
    suspicious=[]; citation_only=[]
    data=re.compile(r'ukmeteors\.co\.uk|api\.ukmeteors|archive\.ukmeteors|download|api|parser|trajectory|orbit|meteor|match|summary|UKMON',re.I)
    for hit in candidate:
        if data.search(hit['text']):
            hit['classification']='potential_ukmon_data_or_scientific_exposure'; suspicious.append(hit)
        else:
            hit['classification']='bibliographic_only'; citation_only.append(hit)
    # Positive controls must prove history search reaches spent survey work.
    saamer=collect(rs,[r'iaumdcSAAMER2020|SAAMER 2020-2021 external validation'])
    sonotaco=collect(rs,[r'SNMv3/023a|SonotaCo 2023'])
    pc_saamer=any('saamer' in x['path'].lower() for x in saamer)
    pc_sonotaco=any('sonotaco' in x['path'].lower() for x in sonotaco)
    verdict='PASS_UKMON_2024_2025_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if not suspicious and pc_saamer and pc_sonotaco else 'FAIL_UKMON_2024_2025_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    result={
        'verdict':verdict,'refs_scanned':len(rs),'reserved_years':[2024,2025],
        'candidate_hits':candidate,'candidate_hit_count':len(candidate),
        'potential_exposure_hits':suspicious,'potential_exposure_hit_count':len(suspicious),
        'bibliographic_only_hits':citation_only,
        'catalogue_access_this_audit':False,'scientific_value_access_this_audit':False,
        'target_information_access':False,
        'positive_controls':{'spent_saamer_detected':pc_saamer,'spent_sonotaco_detected':pc_sonotaco},
        'external_basis':{
            'network':'UK Meteor Network (UKMON)',
            'public_archive':'https://archive.ukmeteors.co.uk/',
            'public_api_documentation':'https://ukmeteornetwork.org/our-data-apis/',
            'reservation_reason':'2024 and 2025 are the two most recent complete calendar years before the current 2026 date; 2022 may be used later only for parser/interface development if this freshness audit passes.'
        },
        'claim_boundary':'Repository-history audit only. It does not contact UKMON, download API data, inspect a trajectory, or access OrbitTrace target information.'
    }
    (OUT/'ukmon_2024_2025_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
if __name__=='__main__': main()
