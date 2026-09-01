#!/usr/bin/env python3
"""Inventory fresh known-binary asteroids in TSSYS-DR1 without opening light curves.

Reads only TSSYS release.merge catalogue metadata and Johnston's public list of
confirmed asteroid satellites.  It explicitly excludes all consumed Stage-3
objects (6764, 1803, and the 128 historical controls).  No .lc URL is requested.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import requests

OUT=Path('results/tess_binary_fresh_positive_inventory');OUT.mkdir(parents=True,exist_ok=True)
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'
JOHN='https://www.johnstonsarchive.net/astro/asteroidmoons.html'
CONTROL=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
CONSUMED_POS={1803,6764}


def get(url):
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-TESS-binary-metadata-inventory/1.0'});r.raise_for_status();return r.text


def parse_merge(text):
    rows=[]
    for raw in text.splitlines():
        p=raw.split()
        if len(p)<12 or not p[0].isdigit():continue
        try:
            rows.append({'number':int(p[0]),'frequency_cpd':float(p[1]),'lc_type':p[2],'period_h':float(p[3]),
              'amplitude_mag':float(p[4]),'n_good':int(p[5]),'sector':int(p[6]),'camera':int(p[7]),'ccd':int(p[8]),
              'median_tess_mag':float(p[9]),'expected_tess_mag':float(p[10]),'H':float(p[11])})
        except Exception:continue
    return rows


def main():
    merge=get(MERGE);john=get(JOHN)
    rows=parse_merge(merge);by={z['number']:z for z in rows}
    # The main Johnston list renders numbered asteroid designations as parenthesized integers.
    # Over-inclusion from unrelated parenthesized integers is harmless because of TSSYS intersection.
    known={int(x) for x in re.findall(r'\(([0-9]{1,7})\)',john)}
    controls={int(x) for x in CONTROL.read_text().split()}
    consumed=controls|CONSUMED_POS
    inter=[]
    for n in sorted(known & set(by)):
        z=dict(by[n]);z['consumed_stage3']=n in consumed
        z['rank_key']=[z['median_tess_mag'],-z['n_good'],-z['amplitude_mag'],n]
        inter.append(z)
    fresh=[z for z in inter if not z['consumed_stage3']]
    fresh.sort(key=lambda z:tuple(z['rank_key']))
    high_quality=[z for z in fresh if z['n_good']>=600 and z['median_tess_mag']<=15.5]
    rep={'role':'metadata-only inventory of fresh confirmed-binary TSSYS objects; no light curves opened',
      'lightcurve_values_opened':False,'sources':{'tssys_release_merge':MERGE,'johnston_confirmed_binary_list':JOHN},
      'source_hashes':{'tssys_release_merge_sha256':hashlib.sha256(merge.encode()).hexdigest(),'johnston_page_sha256':hashlib.sha256(john.encode()).hexdigest()},
      'tssys_row_n':len(rows),'johnston_parenthesized_number_n':len(known),'intersection_n':len(inter),
      'consumed_exclusion_n':len([z for z in inter if z['consumed_stage3']]),'fresh_intersection_n':len(fresh),
      'high_quality_definition':{'n_good_min':600,'median_tess_mag_max':15.5},'high_quality_n':len(high_quality),
      'consumed_stage3_numbers':sorted(consumed),'fresh_ranked':fresh,'high_quality_ranked':high_quality}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'intersection_n':len(inter),'consumed_exclusion_n':rep['consumed_exclusion_n'],'fresh_intersection_n':len(fresh),
      'high_quality_n':len(high_quality),'top40':fresh[:40],'high_quality':high_quality[:40]},indent=2))

if __name__=='__main__':main()
