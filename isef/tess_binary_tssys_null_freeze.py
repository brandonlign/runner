#!/usr/bin/env python3
"""Freeze historical TSSYS-DR1 null controls without opening light curves.

Only catalogue/list metadata are read. The selected `.lc` files are NOT
requested by this program. Binary/companion/contact-binary exclusions are
constructed from Johnston's Archive before SHA-256 selection.

Revision provenance: the first metadata-only attempt used mag<=13.5, n>=600,
period 3--30 h, amplitude 0.03--0.40 and produced only 56 eligible objects,
short of the preregistered >=128 controls. No light-curve value was opened.
This revision broadens only null-pool eligibility, before outcome data, while
leaving the frozen scientific detector untouched.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT=Path('results/tess_binary_tssys_null_freeze');OUT.mkdir(parents=True,exist_ok=True)
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'
JOHN_CONF='https://johnstonsarchive.net/astro/asteroidmoons.html'
JOHN_POSS='https://johnstonsarchive.net/astro/asteroidmoonsq.html'
JOHN_CONTACT='https://johnstonsarchive.net/astro/contactbinast.html'
N_CONTROL=128
MAG_MAX=16.0
N_GOOD_MIN=400
PERIOD_MIN_H=2.0
PERIOD_MAX_H=80.0
AMP_MIN=0.02
AMP_MAX=0.60
LC_TYPES={'P1','P2','P1P2'}
FAILED_FIRST_ELIGIBILITY={'median_tess_mag_max':13.5,'n_good_min':600,'period_h':[3.0,30.0],'amplitude_mag':[0.03,0.40],'lc_types':['P1','P2'],'eligible_n':56}


def get(url):
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-prospective-metadata-freeze/1.0'});r.raise_for_status();return r.text


def table_first_column_numbers(html):
    """Conservatively collect every integer that begins the first cell of a table row."""
    soup=BeautifulSoup(html,'html.parser');out=set()
    for tr in soup.find_all('tr'):
        cells=tr.find_all(['td','th'])
        if not cells: continue
        m=re.match(r'^\s*\(?([0-9]{1,7})\)?\b',cells[0].get_text(' ',strip=True))
        if m: out.add(int(m.group(1)))
    return out


def exclusion_sets():
    hconf=get(JOHN_CONF);hposs=get(JOHN_POSS);hcontact=get(JOHN_CONTACT)
    confirmed={int(x) for x in re.findall(r'\(([0-9]{1,7})\)',hconf)}
    possible=table_first_column_numbers(hposs)
    contact=table_first_column_numbers(hcontact)
    return confirmed,possible,contact,{
        'confirmed_page_sha256':hashlib.sha256(hconf.encode()).hexdigest(),
        'possible_page_sha256':hashlib.sha256(hposs.encode()).hexdigest(),
        'contact_page_sha256':hashlib.sha256(hcontact.encode()).hexdigest(),
    }


def parse_merge(text):
    rows=[]
    for raw in text.splitlines():
        p=raw.split()
        if len(p)<12 or not p[0].isdigit(): continue
        try:
            z={'number':int(p[0]),'frequency_cpd':float(p[1]),'lc_type':p[2],
               'period_h':float(p[3]),'amplitude_mag':float(p[4]),'n_good':int(p[5]),
               'sector':int(p[6]),'camera':int(p[7]),'ccd':int(p[8]),
               'median_tess_mag':float(p[9]),'expected_tess_mag':float(p[10]),'H':float(p[11])}
        except Exception:
            continue
        rows.append(z)
    return rows


def main():
    merge_text=get(MERGE);rows=parse_merge(merge_text)
    confirmed,possible,contact,hashes=exclusion_sets();excluded=confirmed|possible|contact
    eligible=[]
    for z in rows:
        if z['number'] in excluded: continue
        if z['lc_type'] not in LC_TYPES: continue
        if z['median_tess_mag']>MAG_MAX or z['n_good']<N_GOOD_MIN: continue
        if not (PERIOD_MIN_H<=z['period_h']<=PERIOD_MAX_H): continue
        if not (AMP_MIN<=z['amplitude_mag']<=AMP_MAX): continue
        q=dict(z);q['sha256_number']=hashlib.sha256(str(z['number']).encode()).hexdigest();eligible.append(q)
    eligible.sort(key=lambda z:(z['sha256_number'],z['number']))
    if len(eligible)<N_CONTROL: raise RuntimeError(f'only {len(eligible)} eligible controls')
    controls=eligible[:N_CONTROL]
    rep={
      'role':'metadata-only historical-null freeze; no TSSYS light-curve values opened',
      'lightcurve_values_opened':False,
      'selection_revision_reason':'first metadata-only box produced 56 < preregistered 128; broadened before any selected LC was opened',
      'failed_first_eligibility':FAILED_FIRST_ELIGIBILITY,
      'sources':{'tssys_release_merge':MERGE,'johnston_confirmed_probable':JOHN_CONF,'johnston_possible_reports':JOHN_POSS,'johnston_contact_binary':JOHN_CONTACT},
      'source_hashes':{'tssys_release_merge_sha256':hashlib.sha256(merge_text.encode()).hexdigest(),**hashes},
      'catalogue_row_n':len(rows),'exclusion_counts':{'confirmed_regex_n':len(confirmed),'possible_table_n':len(possible),'contact_table_n':len(contact),'union_n':len(excluded)},
      'eligibility':{'lc_types':sorted(LC_TYPES),'median_tess_mag_max':MAG_MAX,'n_good_min':N_GOOD_MIN,'period_h':[PERIOD_MIN_H,PERIOD_MAX_H],'amplitude_mag':[AMP_MIN,AMP_MAX]},
      'eligible_n':len(eligible),'selection':'ascending SHA256(decimal minor-planet number), then number','control_n':N_CONTROL,'controls':controls}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    with (OUT/'controls.txt').open('w') as f:
        for z in controls:f.write(f"{z['number']}\n")
    print(json.dumps({'catalogue_row_n':len(rows),'eligible_n':len(eligible),'control_n':len(controls),'first20':[z['number'] for z in controls[:20]],'exclusion_counts':rep['exclusion_counts'],'source_hashes':rep['source_hashes']},indent=2))

if __name__=='__main__':main()
