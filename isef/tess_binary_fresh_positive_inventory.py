#!/usr/bin/env python3
"""Inventory fresh confirmed-binary asteroids in TSSYS-DR1 without opening light curves.

Reads only TSSYS release.merge catalogue metadata and Johnston's public list of
confirmed asteroid satellites. It explicitly excludes all consumed Stage-3
objects (6764, 1803, and the 128 historical controls). No .lc URL is requested.

Important parser rule: a Johnston asteroid number counts only when it appears at
the START of an anchor's visible text as a parenthesized numbered designation,
e.g. ``(22) Kalliope``. Generic parenthesized integers elsewhere on the page are
not accepted.
"""
from __future__ import annotations
import hashlib, json, re, urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT=Path('results/tess_binary_fresh_positive_inventory');OUT.mkdir(parents=True,exist_ok=True)
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'
JOHN='https://www.johnstonsarchive.net/astro/asteroidmoons.html'
CONTROL=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
CONSUMED_POS={1803,6764}
ANCHOR_RE=re.compile(r'^\s*\(([0-9]{1,7})\)\s+(.+?)\s*$')


def get(url):
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-TESS-binary-metadata-inventory/1.1'});r.raise_for_status();return r.text


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


def johnston_designations(html):
    soup=BeautifulSoup(html,'html.parser'); found={}
    for a in soup.find_all('a'):
        text=' '.join(a.get_text(' ',strip=True).split())
        m=ANCHOR_RE.match(text)
        if not m:continue
        n=int(m.group(1)); href=a.get('href') or ''
        found.setdefault(n,[]).append({'anchor_text':text,'href':urllib.parse.urljoin(JOHN,href) if href else None})
    return found


def main():
    merge=get(MERGE);john=get(JOHN)
    rows=parse_merge(merge);by={z['number']:z for z in rows}
    designation_links=johnston_designations(john);known=set(designation_links)
    controls={int(x) for x in CONTROL.read_text().split()}
    consumed=controls|CONSUMED_POS
    inter=[]
    for n in sorted(known & set(by)):
        z=dict(by[n]);z['johnston_links']=designation_links[n];z['consumed_stage3']=n in consumed
        z['rank_key']=[z['median_tess_mag'],-z['n_good'],-z['amplitude_mag'],n]
        inter.append(z)
    fresh=[z for z in inter if not z['consumed_stage3']]
    fresh.sort(key=lambda z:tuple(z['rank_key']))
    high_quality=[z for z in fresh if z['n_good']>=600 and z['median_tess_mag']<=15.5]
    rep={'role':'metadata-only inventory of fresh confirmed-binary TSSYS objects; no light curves opened',
      'lightcurve_values_opened':False,'parser_version':'Johnston anchor text must begin with parenthesized numbered designation',
      'sources':{'tssys_release_merge':MERGE,'johnston_confirmed_binary_list':JOHN},
      'source_hashes':{'tssys_release_merge_sha256':hashlib.sha256(merge.encode()).hexdigest(),'johnston_page_sha256':hashlib.sha256(john.encode()).hexdigest()},
      'tssys_row_n':len(rows),'johnston_designation_anchor_number_n':len(known),'intersection_n':len(inter),
      'consumed_exclusion_n':len([z for z in inter if z['consumed_stage3']]),'fresh_intersection_n':len(fresh),
      'high_quality_definition':{'n_good_min':600,'median_tess_mag_max':15.5},'high_quality_n':len(high_quality),
      'consumed_stage3_numbers':sorted(consumed),'fresh_ranked':fresh,'high_quality_ranked':high_quality}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'johnston_designation_anchor_number_n':len(known),'intersection_n':len(inter),'consumed_exclusion_n':rep['consumed_exclusion_n'],
      'fresh_intersection_n':len(fresh),'high_quality_n':len(high_quality),'top40':fresh[:40],'high_quality':high_quality[:40]},indent=2))

if __name__=='__main__':main()
