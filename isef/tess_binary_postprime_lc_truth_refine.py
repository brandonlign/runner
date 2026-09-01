#!/usr/bin/env python3
"""Refine the post-prime known-satellite geometry inventory to strong LC truth.

This is metadata-only. It joins the already-produced Sectors 14-96 geometry
artifact to Johnston's summary table and retains fresh asteroids for which at
least one companion has discovery method `LC` (light-curve discovery). These
are much stronger positives for a mutual-event / eclipsing-binary detector than
mere satellite membership. No TESS pixels or light-curve values are opened.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import pandas as pd, requests

URL='https://www.johnstonsarchive.net/astro/astmoontable.html'
OUT=Path('results/tess_binary_postprime_lc_truth_refine'); OUT.mkdir(parents=True,exist_ok=True)
NUM_RE=re.compile(r'\(([0-9]{1,7})\)')


def flat(c):
    if isinstance(c,tuple): return ' | '.join(str(x).strip() for x in c if str(x).strip() and str(x)!='nan').lower()
    return str(c).strip().lower()


def choose_col(cols,needles):
    for c in cols:
        s=flat(c)
        if all(n in s for n in needles): return c
    return None


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('geometry_root'); a=ap.parse_args()
    matches=list(Path(a.geometry_root).rglob('report.json'))
    if len(matches)!=1: raise RuntimeError(f'expected one geometry report; found {matches}')
    geo=json.loads(matches[0].read_text()); fresh={int(z['number']):z for z in geo['fresh']}
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-postprime-LC-truth/1.0'}); r.raise_for_status()
    tables=pd.read_html(r.text)
    chosen=None; mapping=None
    for df in tables:
        cols=list(df.columns)
        minor=choose_col(cols,['minor planet']); method=choose_col(cols,['discovery','method'])
        if minor is None or method is None: continue
        primary_d=choose_col(cols,['diameter','primary']) or choose_col(cols,['primary','diameter'])
        sec_a=choose_col(cols,['semimajor axis','secondary']) or choose_col(cols,['secondary','semimajor axis'])
        sec_p=choose_col(cols,['orbital period','secondary']) or choose_col(cols,['secondary','orbital period'])
        sec_d=choose_col(cols,['diameter','secondary']) or choose_col(cols,['secondary','diameter'])
        chosen=df; mapping={'minor':minor,'method':method,'primary_d':primary_d,'sec_a':sec_a,'sec_p':sec_p,'sec_d':sec_d}; break
    if chosen is None: raise RuntimeError('could not identify Johnston summary table')
    grouped={}
    for _,row in chosen.iterrows():
        text=str(row[mapping['minor']]); m=NUM_RE.search(text)
        if not m: continue
        n=int(m.group(1)); method=str(row[mapping['method']]).strip().upper()
        z={'minor_planet_text':text,'discovery_method':method}
        for key in ('primary_d','sec_a','sec_p','sec_d'):
            c=mapping.get(key); z[key]=None if c is None else str(row[c]).strip()
        grouped.setdefault(n,[]).append(z)
    strong=[]
    for n,z in fresh.items():
        entries=grouped.get(n,[]); lc=[e for e in entries if e['discovery_method']=='LC']
        if not lc: continue
        q=dict(z); q['johnston_lc_companions']=lc; q['johnston_all_companion_rows']=entries; strong.append(q)
    strong.sort(key=lambda z:(z['H'],-len(z['sectors']),z['number']))
    rep={'role':'metadata-only strong-positive refinement: fresh post-prime known binaries discovered by light curve',
         'tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,'johnston_url':URL,
         'johnston_sha256':hashlib.sha256(r.content).hexdigest(),'geometry_source_run':33457113454,'geometry_source_artifact_id':9781953108,
         'fresh_geometry_object_n':len(fresh),'lc_discovered_fresh_object_n':len(strong),
         'lc_discovered_fresh_object_sector_n':sum(len(z['sectors']) for z in strong),'strong':strong,
         'table_columns':[flat(c) for c in chosen.columns],'column_mapping':{k:(None if v is None else flat(v)) for k,v in mapping.items()}}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    (OUT/'strong_numbers.txt').write_text(''.join(f"{z['number']}\n" for z in strong))
    print(json.dumps({'fresh_geometry_object_n':len(fresh),'lc_discovered_fresh_object_n':len(strong),
      'lc_discovered_fresh_object_sector_n':rep['lc_discovered_fresh_object_sector_n'],'strong':strong},indent=2))

if __name__=='__main__': main()
