#!/usr/bin/env python3
"""Repository-history audit for CAMSv3 2017/2018 scientific freshness."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path('output')
OUT.mkdir(exist_ok=True)
SELF_PREFIXES = (
    'orbittrace_multiplicity_camsv3_2017_2018_freshness_audit/',
    '.github/workflows/orbittrace-multiplicity-camsv3-2017-2018-freshness',
)
TARGETS = (2017, 2018)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refs() -> list[str]:
    raw = run('git','for-each-ref','--format=%(refname)','refs/remotes/origin')
    return [x.strip() for x in raw.splitlines() if x.strip() and not x.endswith('/HEAD')]


def grep(ref: str, pattern: str) -> list[dict]:
    proc = subprocess.run(['git','grep','-n','-I','-E',pattern,ref,'--'], text=True, capture_output=True)
    if proc.returncode not in (0,1):
        raise RuntimeError(proc.stderr)
    out=[]
    prefix=ref+':'
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
        out.append({'ref':ref,'path':path,'line':int(lineno),'text':text[:1000]})
    return out


def dedup(hits: list[dict]) -> list[dict]:
    seen=set(); out=[]
    for h in hits:
        key=(h['path'],h['line'],h['text'])
        if key in seen:
            continue
        seen.add(key); out.append(h)
    return out


def years_from_python_range(text: str) -> set[int]:
    years=set()
    for m in re.finditer(r'range\(\s*(\d{4})\s*,\s*(\d{4})\s*\)', text):
        a,b=map(int,m.groups())
        years.update(range(a,b))
    return years


def classify_target_hit(hit: dict, year: int) -> str:
    p=hit['path'].lower(); t=hit['text'].lower()
    # Explicit statements that the target remains unread/untouched are provenance, not exposure.
    if any(x in t for x in (
        'untouched','remain unread','remains unread','not downloaded','not download','must not download',
        'must not request','do not request','do not access','no scientific','no label','no meteor-record',
        'neither requested nor opened','reserved',
    )):
        return 'reservation_or_no_access_statement'
    # Structural/schema-only references are not scientific-value exposure if the text is clearly structural.
    if any(x in p for x in ('feasibility','schema_audit','reader_spec_audit','structural')) and any(
        x in t for x in ('header','row count','row_count','basename','sha256','archive','schema','member')
    ):
        return 'structural_only_reference'
    # A Python half-open range ending at the target year does not include it.
    yrs=years_from_python_range(hit['text'])
    if 'range(' in hit['text'] and year not in yrs:
        return 'range_excludes_target'
    # SonotaCo/GMN/etc year references are unrelated unless CAMSv3/CAMS is on the same hit.
    if 'cams' not in t and 'cams' not in p:
        return 'unrelated_non_cams_year'
    return 'potential_exposure'


def target_hits(all_refs: list[str], year: int) -> list[dict]:
    # Exact annual archive/name forms plus CAMS/year co-occurrence and dynamic range declarations.
    patterns = [
        rf'iaumdcCAMSv3_{year}',
        rf'CAMSv3[^\n]{{0,120}}{year}|{year}[^\n]{{0,120}}CAMSv3',
        rf'CAMS[^\n]{{0,120}}{year}|{year}[^\n]{{0,120}}CAMS',
        r'CAMS[^\n]{0,160}range\([^\n]{0,80}\)|range\([^\n]{0,80}\)[^\n]{0,160}CAMS',
    ]
    hits=[]
    for ref in all_refs:
        for pat in patterns:
            hits.extend(grep(ref,pat))
    hits=dedup(hits)
    for h in hits:
        h['classification']=classify_target_hit(h,year)
        h['dynamic_range_years']=sorted(years_from_python_range(h['text'])) if 'range(' in h['text'] else []
    return hits


def positive_control_hits(all_refs: list[str], year: int) -> list[dict]:
    pats=[rf'iaumdcCAMSv3_{year}',rf'CAMSv3[^\n]{{0,120}}{year}|{year}[^\n]{{0,120}}CAMSv3']
    hits=[]
    for ref in all_refs:
        for pat in pats:
            hits.extend(grep(ref,pat))
    return dedup(hits)


def main() -> int:
    all_refs=refs()
    targets={}
    for year in TARGETS:
        hits=target_hits(all_refs,year)
        suspicious=[h for h in hits if h['classification']=='potential_exposure']
        targets[str(year)]={'hits':hits,'potential_exposure_hits':suspicious}

    pc2015=positive_control_hits(all_refs,2015)
    pc2016=positive_control_hits(all_refs,2016)
    # Positive controls must detect actual downstream use, not merely structural references.
    pc2015_actual=any(any(k in h['path'].lower() for k in ('aggregate_audit','shower_label_audit','common_origin','ghoststream_external')) for h in pc2015)
    pc2016_actual=any(any(k in h['path'].lower() for k in ('common_origin','ghoststream_external','nop_solution004_cams_recovery')) for h in pc2016)

    clean=all(not targets[str(y)]['potential_exposure_hits'] for y in TARGETS)
    verdict='PASS_CAMSV3_2017_2018_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if clean and pc2015_actual and pc2016_actual else 'FAIL_CAMSV3_2017_2018_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    result={
        'verdict':verdict,
        'refs_scanned':len(all_refs),
        'catalogue_access_this_audit':False,
        'scientific_value_access_this_audit':False,
        'label_access_this_audit':False,
        'target_information_access':False,
        'targets':targets,
        'positive_controls':{
            '2015_spent_detected':pc2015_actual,
            '2015_hit_count':len(pc2015),
            '2016_spent_detected':pc2016_actual,
            '2016_hit_count':len(pc2016),
        },
        'python_range_semantics':'range(a,b) is treated as half-open [a,b); e.g. range(2010,2017) does not expose 2017.',
        'claim_boundary':'A pass establishes repository-history scientific freshness only. It does not download or inspect CAMSv3 2017/2018 and authorizes only a separately frozen structural transport audit before any scientific-value or label access.',
    }
    (OUT/'camsv3_2017_2018_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'):
        raise SystemExit(1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
