#!/usr/bin/env python3
"""Freeze a metadata-only pseudo-period null panel for the Stage-5 TESS pilot.

Controls come only from the already-consumed Stage-4 control identities. Selection
uses post-prime ephemeris/footprint metadata, never TESS flux/BLS/dip values.
Each pilot binary contributes four unique controls; each control inherits that
binary's already-frozen orbital period as a pseudo-truth period. Recovery of that
pseudo-period under the unchanged Stage-5 pipeline estimates accidental recovery.
"""
from __future__ import annotations
import json, math, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from tess_asteroids import MovingTPF

HERE=Path(__file__).resolve().parent
OUT=HERE/'results'/'tess_binary_stage5_null_manifest'
OUT.mkdir(parents=True,exist_ok=True)
POOL_FILE=HERE/'tess_binary_stage4_validation_controls.txt'
CONFIRMED='https://www.johnstonsarchive.net/astro/asteroidmoons.html'
POSSIBLE='https://www.johnstonsarchive.net/astro/asteroidmoonsq.html'
CONTACT='https://www.johnstonsarchive.net/astro/contactbinast.html'
ANY_NUM_RE=re.compile(r'\(([0-9]{1,7})\)')

# Frozen Stage-5 recoverability pilot definitions. These values were fixed before
# their post-prime science extraction and are now consumed development data.
PILOT=[
 {'number':20325,'period':0.9808,'sectors':[42,43]},
 {'number':2171,'period':0.9567,'sectors':[43,44]},
 {'number':761,'period':2.3783,'sectors':[44,45,46]},
 {'number':2680,'period':2.2170,'sectors':[44,45,46]},
 {'number':2486,'period':7.1920,'sectors':[71,73,91]},
 {'number':2280,'period':0.89496,'sectors':[71,72,91]},
 {'number':854,'period':1.5720,'sectors':[34,70,71]},
 {'number':2080,'period':1.0762,'sectors':[71,72,92]},
 {'number':7393,'period':1.6426,'sectors':[42,43,44]},
 {'number':2019,'period':0.74925,'sectors':[55,71,72,91]},
 {'number':809,'period':0.6424,'sectors':[72,91]},
 {'number':4528,'period':1.4592,'sectors':[30,45,46]},
]
N_PER=4


def mentions(url):
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage5-null-manifest/1.0'})
    r.raise_for_status()
    return {int(x) for x in ANY_NUM_RE.findall(BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True))}


def visibility(number,sectors):
    hits=[]
    for s in sectors:
        try:
            mt=MovingTPF.from_name(str(number),sector=int(s))
            n=int(len(mt.ephem))
            if n:
                hits.append({'sector':int(s),'ephemeris_rows':n,'camera':int(mt.camera),'ccd':int(mt.ccd)})
        except Exception:
            pass
    return hits


def sig(hits):
    return (len(hits),sum(h['ephemeris_rows'] for h in hits))


def cost(ph,ch):
    pn,pr=sig(ph); cn,cr=sig(ch)
    # Strongly prefer the same number of visible sectors, then comparable
    # on-detector ephemeris duration. No flux/light-curve value enters.
    return (abs(cn-pn),abs(math.log((cr+1)/(pr+1))))


def main():
    pool=[int(x) for x in POOL_FILE.read_text().split()]
    binaryish=mentions(CONFIRMED)|mentions(POSSIBLE)|mentions(CONTACT)|{p['number'] for p in PILOT}
    pool=[n for n in pool if n not in binaryish]
    used=set(); rows=[]
    for p in PILOT:
        ph=visibility(p['number'],p['sectors'])
        if not ph:
            raise RuntimeError(f"pilot positive {p['number']} unexpectedly has no metadata visibility")
        candidates=[]
        for n in pool:
            if n in used: continue
            ch=visibility(n,p['sectors'])
            if not ch: continue
            candidates.append((cost(ph,ch),n,ch))
        candidates.sort(key=lambda x:(x[0][0],x[0][1],x[1]))
        chosen=candidates[:N_PER]
        if len(chosen)!=N_PER:
            raise RuntimeError(f"only {len(chosen)} controls for {p['number']}")
        for c,n,ch in chosen:
            used.add(n)
            rows.append({'source_positive':p['number'],'control':n,'pseudo_period_days':p['period'],
                         'tested_sectors':[h['sector'] for h in ch],
                         'positive_visibility':ph,'control_visibility':ch,
                         'metadata_cost':[float(c[0]),float(c[1])]})
        print(p['number'],[(n,[h['sector'] for h in ch]) for _,n,ch in chosen],flush=True)
    if len(rows)!=len(PILOT)*N_PER or len({r['control'] for r in rows})!=len(rows):
        raise RuntimeError('null panel cardinality/uniqueness failure')
    report={'role':'Stage-5 development pseudo-period null panel; metadata-only selection',
            'science_pixels_opened_during_selection':False,
            'control_source':'already-consumed Stage-4 control identities',
            'binaryish_exclusions':[CONFIRMED,POSSIBLE,CONTACT],
            'matching':'same pilot sector opportunities; minimize visible-sector-count difference then log ephemeris-row difference; deterministic number tie-break',
            'controls_per_positive':N_PER,'n_controls':len(rows),'rows':rows}
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'matrix.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'n_controls':len(rows),'controls':[r['control'] for r in rows]},indent=2))

if __name__=='__main__': main()
