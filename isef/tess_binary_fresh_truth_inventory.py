#!/usr/bin/env python3
"""Build external-truth inventory for fresh TSSYS binary benchmarks without .lc access.

The program reads TSSYS release.merge metadata, Johnston confirmed-binary object
pages, and the consumed Stage-3 manifest.  It never requests a TSSYS light-curve
file.  Its purpose is to identify *before raw-light-curve access* systems whose
published satellite period (or half/double recurrence) agrees with the published
TSSYS catalogue period while the primary spin period is distinct.
"""
from __future__ import annotations
import hashlib, json, math, re, urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT=Path('results/tess_binary_fresh_truth_inventory');OUT.mkdir(parents=True,exist_ok=True)
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'
JOHN='https://www.johnstonsarchive.net/astro/asteroidmoons.html'
CONTROL=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
CONSUMED_POS={1803,6764}
ANCHOR_RE=re.compile(r'^\s*\(([0-9]{1,7})\)\s+(.+?)\s*$')
NUM=r'([0-9]+(?:\.[0-9]+)?)'


def get(url):
    for u in (url,url.replace('https://www.johnstonsarchive.net/','https://johnstonsarchive.net/')):
        try:
            r=requests.get(u,timeout=120,headers={'User-Agent':'ISEF-TESS-binary-truth-inventory/1.0'})
            if r.status_code==200:return r.text,u
        except Exception:pass
    raise RuntimeError(f'could not fetch {url}')


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


def designation_links(html):
    soup=BeautifulSoup(html,'html.parser');out={}
    for a in soup.find_all('a'):
        text=' '.join(a.get_text(' ',strip=True).split());m=ANCHOR_RE.match(text)
        if not m:continue
        n=int(m.group(1));href=a.get('href') or ''
        if not href:continue
        url=urllib.parse.urljoin(JOHN,href)
        if '/astmoons/am-' not in url:continue
        out.setdefault(n,{'name':text,'url':url})
    return out


def vals(pattern,text):
    return [float(x) for x in re.findall(pattern,text,re.I)]


def page_truth(html):
    soup=BeautifulSoup(html,'html.parser');txt=' '.join(soup.stripped_strings)
    orbit_d=vals(r'orbital\s+period\s+P[_ ]?s\s*:\s*'+NUM+r'(?:\s*±\s*'+NUM+r')?\s*d',txt)
    # re.findall returns tuples when uncertainty subcapture exists; recover using a simpler scan too.
    orbit=[]
    for m in re.finditer(r'orbital\s+period\s+P[_ ]?s\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*(?:±\s*[0-9]+(?:\.[0-9]+)?\s*)?(d|h)',txt,re.I):
        v=float(m.group(1));orbit.append(v*24 if m.group(2).lower()=='d' else v)
    rotation=[]
    for m in re.finditer(r'rotation\s+period\s+RP[_ ]?p\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*(?:±\s*[0-9]+(?:\.[0-9]+)?\s*)?h',txt,re.I):rotation.append(float(m.group(1)))
    mutual=[]
    for m in re.finditer(r'amplitude\s+in\s+mag\.?,?\s+mutual\s+events\s+ΔM\s*:\s*([0-9]+(?:\.[0-9]+)?)',txt,re.I):mutual.append(float(m.group(1)))
    return {'satellite_orbit_periods_h':orbit,'primary_rotation_periods_h':rotation,'documented_mutual_event_amplitudes_mag':mutual}


def rel(a,b):return abs(a-b)/b if b else math.inf


def main():
    merge,merge_url=get(MERGE);john,john_url=get(JOHN)
    rows=parse_merge(merge);by={z['number']:z for z in rows};links=designation_links(john)
    consumed={int(x) for x in CONTROL.read_text().split()}|CONSUMED_POS
    candidates=[]
    for n in sorted(set(by)&set(links)-consumed):
        z=dict(by[n]);meta=links[n]
        try:
            page,actual=get(meta['url']);truth=page_truth(page);page_sha=hashlib.sha256(page.encode()).hexdigest();err=None
        except Exception as e:
            truth={'satellite_orbit_periods_h':[],'primary_rotation_periods_h':[],'documented_mutual_event_amplitudes_mag':[]};page_sha=None;actual=None;err=f'{type(e).__name__}: {e}'
        p=z['period_h'];matches=[]
        for op in truth['satellite_orbit_periods_h']:
            for factor in (0.5,1.0,2.0):
                target=factor*op;matches.append({'satellite_orbit_h':op,'factor_of_orbit':factor,'target_h':target,'relative_error':rel(p,target)})
        best=min(matches,key=lambda q:q['relative_error']) if matches else None
        rotmatches=[]
        for rp in truth['primary_rotation_periods_h']:
            for factor in (0.5,1.0,2.0):rotmatches.append(rel(p,factor*rp))
        best_rot=min(rotmatches) if rotmatches else None
        strong=bool(best and best['relative_error']<=0.03 and (best_rot is None or best_rot>0.05) and z['n_good']>=300)
        very_strong=bool(strong and truth['documented_mutual_event_amplitudes_mag'])
        z.update({'johnston_name':meta['name'],'johnston_url':meta['url'],'johnston_actual_url':actual,'johnston_page_sha256':page_sha,
                  'truth_parse_error':err,**truth,'best_orbit_or_half_double_match':best,'best_rotation_or_half_double_relative_error':best_rot,
                  'strong_orbital_timescale_benchmark':strong,'very_strong_mutual_event_benchmark':very_strong})
        candidates.append(z)
    ranked=sorted(candidates,key=lambda z:(not z['very_strong_mutual_event_benchmark'],not z['strong_orbital_timescale_benchmark'],
                                          z['best_orbit_or_half_double_match']['relative_error'] if z['best_orbit_or_half_double_match'] else 9,
                                          -z['n_good'],z['number']))
    strong=[z for z in ranked if z['strong_orbital_timescale_benchmark']];very=[z for z in ranked if z['very_strong_mutual_event_benchmark']]
    rep={'role':'external-truth metadata-only fresh benchmark inventory; no TSSYS .lc values opened','lightcurve_values_opened':False,
      'selection_rule':{'orbit_or_half_double_relative_error_max':0.03,'rotation_or_half_double_relative_error_must_exceed':0.05,'n_good_min':300,
                        'very_strong_additionally_requires':'documented Johnston mutual-event amplitude'},
      'sources':{'tssys_release_merge':merge_url,'johnston_confirmed_list':john_url},
      'source_hashes':{'release_merge_sha256':hashlib.sha256(merge.encode()).hexdigest(),'johnston_list_sha256':hashlib.sha256(john.encode()).hexdigest()},
      'fresh_confirmed_tssys_n':len(candidates),'strong_n':len(strong),'very_strong_n':len(very),
      'strong_numbers':[z['number'] for z in strong],'very_strong_numbers':[z['number'] for z in very],
      'ranked':ranked}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact=[]
    for z in ranked[:30]:compact.append({'number':z['number'],'name':z['johnston_name'],'tssys_period_h':z['period_h'],'n_good':z['n_good'],'mag':z['median_tess_mag'],
      'orbit_h':z['satellite_orbit_periods_h'],'rotation_h':z['primary_rotation_periods_h'],'mutual_amp':z['documented_mutual_event_amplitudes_mag'],
      'best':z['best_orbit_or_half_double_match'],'best_rot_rel':z['best_rotation_or_half_double_relative_error'],
      'strong':z['strong_orbital_timescale_benchmark'],'very_strong':z['very_strong_mutual_event_benchmark']})
    print(json.dumps({'fresh_confirmed_tssys_n':len(candidates),'strong_n':len(strong),'very_strong_n':len(very),'strong_numbers':rep['strong_numbers'],'very_strong_numbers':rep['very_strong_numbers'],'top30':compact},indent=2))

if __name__=='__main__':main()
