#!/usr/bin/env python3
"""Repository-history audit for CAMSv3 2016/2017 scientific-value freshness."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path('output')
OUT.mkdir(exist_ok=True)
SELF = 'orbittrace_multiplicity_camsv3_2016_2017_freshness_audit/'


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refs() -> list[str]:
    raw = run('git','for-each-ref','--format=%(refname)','refs/remotes/origin')
    return [x.strip() for x in raw.splitlines() if x.strip() and not x.endswith('/HEAD')]


def grep_ref(ref: str, pattern: str) -> list[dict]:
    proc = subprocess.run(['git','grep','-n','-I','-E',pattern,ref,'--'], text=True, capture_output=True)
    if proc.returncode not in (0,1):
        raise RuntimeError(proc.stderr)
    hits=[]
    for line in proc.stdout.splitlines():
        # ref:path:line:text; split only first 3 ':' after ref is embedded by git grep.
        prefix = ref + ':'
        if not line.startswith(prefix):
            continue
        rest=line[len(prefix):]
        parts=rest.split(':',2)
        if len(parts)!=3:
            continue
        path,lineno,text=parts
        if path.startswith(SELF) or path.startswith('.github/workflows/orbittrace-multiplicity-camsv3-2016-2017-freshness'):
            continue
        hits.append({'ref':ref,'path':path,'line':int(lineno),'text':text[:500]})
    return hits


def classify_2016(hit: dict) -> str:
    p=hit['path'].lower(); t=hit['text'].lower()
    # The only permitted 2016 archive access before this audit is structural parser feasibility:
    # archive hash/member/header/row-width only, with explicit scientific_values_read/label_values_read false.
    if 'camsv3' in p and 'feasibility' in p:
        return 'allowed_structural_only'
    # Later development protocols/scripts are allowed to mention 2016 only as a reserved/absent panel.
    if ('camsv3_shower_label_audit' in p or 'camsv3_aggregate_audit' in p):
        if any(x in t for x in ('untouched','reserved','must not','absent','neither requested nor opened','not download')):
            return 'allowed_reservation_only'
        # Workflows may assert 2016 absence without data access.
        if '2016' in t and any(x in t for x in ('grep','assert','not in','absent')):
            return 'allowed_absence_guard'
    return 'suspicious'


def classify_2017(hit: dict) -> str:
    p=hit['path'].lower(); t=hit['text'].lower()
    # No pre-existing CAMSv3 2017 scientific or structural work is expected.
    if 'sonotaco' in p:
        return 'unrelated_sonotaco_year'
    return 'suspicious'


def main() -> int:
    all_refs=refs()
    # Broad enough to catch exact archive names and nearby CAMSv3 year declarations.
    pat2016=r'(iaumdcCAMSv3_2016|CAMSv3[^\n]{0,80}2016|2016[^\n]{0,80}CAMSv3)'
    pat2017=r'(iaumdcCAMSv3_2017|CAMSv3[^\n]{0,80}2017|2017[^\n]{0,80}CAMSv3)'
    h16=[]; h17=[]
    for ref in all_refs:
        h16.extend(grep_ref(ref,pat2016))
        h17.extend(grep_ref(ref,pat2017))
    # Deduplicate identical path/text appearances across inherited branches for compact provenance.
    def dedup(hits):
        seen=set(); out=[]
        for h in hits:
            key=(h['path'],h['line'],h['text'])
            if key in seen: continue
            seen.add(key); out.append(h)
        return out
    h16=dedup(h16); h17=dedup(h17)
    for h in h16: h['classification']=classify_2016(h)
    for h in h17: h['classification']=classify_2017(h)

    suspicious16=[h for h in h16 if h['classification']=='suspicious']
    suspicious17=[h for h in h17 if h['classification']=='suspicious']

    # Positive-control evidence: 2015 was deliberately consumed by aggregate label/value audits.
    positive=[]
    for ref in all_refs:
        positive.extend(grep_ref(ref,r'(iaumdcCAMSv3_2015|2015[^\n]{0,80}CAMSv3|CAMSv3[^\n]{0,80}2015)'))
    positive=dedup(positive)
    positive_actual=any('aggregate_audit' in h['path'].lower() or 'shower_label_audit' in h['path'].lower() for h in positive)

    verdict = 'PASS_CAMSV3_2016_2017_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if not suspicious16 and not suspicious17 and positive_actual else 'FAIL_CAMSV3_2016_2017_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    result={
        'verdict':verdict,
        'catalogue_access_this_audit':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'refs_scanned':len(all_refs),
        'years':{
            '2016':{
                'classification':'structural-only previously; scientific values/labels expected untouched',
                'hits':h16,
                'suspicious_hits':suspicious16,
            },
            '2017':{
                'classification':'no prior CAMSv3 access expected',
                'hits':h17,
                'suspicious_hits':suspicious17,
            },
        },
        'positive_control_2015_actual_development_hit':positive_actual,
        'positive_control_2015_hit_count':len(positive),
        'claim_boundary':'A pass establishes repository-history freshness only. It does not inspect CAMSv3 2016/2017 archive values and does not authorize scientific evaluation until separate structural/parser/protocol gates are frozen.',
    }
    (OUT/'camsv3_2016_2017_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'):
        raise SystemExit(1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
