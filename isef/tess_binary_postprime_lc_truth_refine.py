#!/usr/bin/env python3
"""Refine the post-prime known-satellite geometry inventory to strong LC truth.

Metadata-only. Joins the existing Sectors 14-96 geometry artifact to Johnston's
satellite summary and retains fresh asteroids with at least one companion whose
discovery method is LC (photometric light curve). No TESS pixels/light curves
are opened.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL='https://www.johnstonsarchive.net/astro/astmoontable.html'
OUT=Path('results/tess_binary_postprime_lc_truth_refine'); OUT.mkdir(parents=True,exist_ok=True)
NUM_RE=re.compile(r'\(([0-9]{1,7})\)')
METHODS={'AOT','HST','IMG','LC','OCC','RAD','SC'}


def parse_rows(html: bytes):
    """Parse Johnston rows by semantic method token, avoiding fragile pandas headers."""
    soup=BeautifulSoup(html,'html.parser')
    grouped={}
    current_num=None
    for tr in soup.find_all('tr'):
        cells=[' '.join(td.stripped_strings) for td in tr.find_all(['td','th'])]
        if not cells:
            continue
        # Rowspans can omit the minor-planet cell on later companion rows.
        for c in cells[:3]:
            m=NUM_RE.search(c)
            if m:
                current_num=int(m.group(1)); break
        if current_num is None:
            continue
        method=None; mi=None
        for i,c in enumerate(cells):
            token=c.strip().upper()
            if token in METHODS:
                method=token; mi=i; break
        if method is None:
            continue
        grouped.setdefault(current_num,[]).append({
            'minor_planet_text': next((c for c in cells[:3] if NUM_RE.search(c)), str(current_num)),
            'discovery_method': method,
            'row_cells': cells,
            'method_cell_index': mi,
        })
    return grouped


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('geometry_root'); a=ap.parse_args()
    matches=list(Path(a.geometry_root).rglob('report.json'))
    if len(matches)!=1: raise RuntimeError(f'expected one geometry report; found {matches}')
    geo=json.loads(matches[0].read_text()); fresh={int(z['number']):z for z in geo['fresh']}
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-postprime-LC-truth/1.1'}); r.raise_for_status()
    grouped=parse_rows(r.content)
    if len(grouped)<100:
        raise RuntimeError(f'Johnston parser found only {len(grouped)} numbered systems; refusing silent schema failure')
    strong=[]
    for n,z in fresh.items():
        entries=grouped.get(n,[]); lc=[e for e in entries if e['discovery_method']=='LC']
        if not lc: continue
        q=dict(z); q['johnston_lc_companions']=lc; q['johnston_all_companion_rows']=entries; strong.append(q)
    strong.sort(key=lambda z:(z['H'],-len(z['sectors']),z['number']))
    rep={'role':'metadata-only strong-positive refinement: fresh post-prime known binaries discovered by light curve',
         'tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,'johnston_url':URL,
         'johnston_sha256':hashlib.sha256(r.content).hexdigest(),'geometry_source_run':33457113454,'geometry_source_artifact_id':9781953108,
         'fresh_geometry_object_n':len(fresh),'johnston_numbered_system_n':len(grouped),
         'lc_discovered_fresh_object_n':len(strong),
         'lc_discovered_fresh_object_sector_n':sum(len(z['sectors']) for z in strong),'strong':strong}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    (OUT/'strong_numbers.txt').write_text(''.join(f"{z['number']}\n" for z in strong))
    print(json.dumps({'fresh_geometry_object_n':len(fresh),'johnston_numbered_system_n':len(grouped),
      'lc_discovered_fresh_object_n':len(strong),'lc_discovered_fresh_object_sector_n':rep['lc_discovered_fresh_object_sector_n'],
      'strong_numbers':[z['number'] for z in strong]},indent=2))

if __name__=='__main__': main()
