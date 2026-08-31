#!/usr/bin/env python3
"""Implementation sanity check for frozen Stage-1 using development object 6764.

6764 is development evidence only. This script must not be cited as independent
validation and opens no Year-8 data.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np, requests
from tess_binary_stage1_detector import detect

OUT=Path('results/tess_binary_6764_stage1_development');OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
TRUTH_H=30.41

def clean(x):
    if isinstance(x,(float,np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x,(int,np.integer)): return int(x)
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    return x

def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-stage1-development/1.0'});r.raise_for_status()
    a=np.loadtxt(__import__('io').BytesIO(r.content))
    z=detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    sel=z.get('selected_interpretation')
    Porb_h=float(sel['orbital_period_d']*24) if sel else None
    truth_match=bool(Porb_h is not None and abs(Porb_h-TRUTH_H)/TRUTH_H<=0.05)
    sanity=bool(z.get('hard_pass',False) and sel is not None and sel['name']=='H2_ALTERNATING_TWO_EVENT' and truth_match)
    rep={'role':'Stage-1 implementation sanity on development positive only','year8_values_opened':False,'target':'6764 Kirillavrov',
         'source_sha256':hashlib.sha256(r.content).hexdigest(),'published_orbit_h':TRUTH_H,
         'selected_orbit_h':Porb_h,'truth_match_within_5pct':truth_match,'sanity_pass':sanity,'detector':z}
    (OUT/'report.json').write_text(json.dumps(clean(rep),indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(clean({'sanity_pass':sanity,'hard_pass':z.get('hard_pass'),'selected':sel,'score':z.get('score'),
        'masked_rotation':z.get('masked_rotation'),'final_bls':z.get('final_bls'),'events':z.get('events')}),indent=2,allow_nan=False))
    raise SystemExit(0 if sanity else 3)

if __name__=='__main__':main()
