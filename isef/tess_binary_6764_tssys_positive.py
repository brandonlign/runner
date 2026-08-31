#!/usr/bin/env python3
"""Run the frozen Stage-0 detector on the published 6764 TSSYS-DR1 positive."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, requests
from tess_binary_stage0_detector import detect

OUT=Path('results/tess_binary_6764_tssys_positive');OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
ORBIT_H=30.41

def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-frozen-positive-control/1.0'});r.raise_for_status()
    raw=OUT/'6764.lc';raw.write_bytes(r.content)
    a=np.loadtxt(raw)
    if a.ndim!=2 or a.shape[1]<13:raise RuntimeError(f'unexpected TSSYS shape {a.shape}')
    # TSSYS README: JD col2, TESS magnitude col5, uncertainty col6, flags col10.
    d=detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    selected_h=d.get('bls',{}).get('period_d',np.nan)*24 if d.get('eligible') else np.nan
    harmonic_matches={str(f):bool(np.isfinite(selected_h) and abs(selected_h-f*ORBIT_H)/(f*ORBIT_H)<=0.05) for f in (0.5,1.0,2.0)}
    positive_pass=bool(d.get('hard_pass',False) and any(harmonic_matches.values()))
    rep={'role':'external known-binary positive control','target':'(6764) Kirillavrov','source_url':URL,
         'raw_sha256':__import__('hashlib').sha256(r.content).hexdigest(),'year8_values_opened':False,
         'published_orbital_period_h':ORBIT_H,'allowed_positive_harmonics':[0.5,1.0,2.0],
         'selected_event_period_h':float(selected_h) if np.isfinite(selected_h) else None,
         'harmonic_matches_within_5pct':harmonic_matches,'positive_gate_pass':positive_pass,'detector':d}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'positive_gate_pass':positive_pass,'selected_event_period_h':rep['selected_event_period_h'],'harmonic_matches':harmonic_matches,
                      'hard_pass':d.get('hard_pass'),'score':d.get('score'),'hard_conditions':d.get('hard_conditions'),
                      'rotation_period_h':d.get('rotation',{}).get('rotation_period_h'),'bls':d.get('bls'),'events':d.get('events'),'model_comparison':d.get('model_comparison')},indent=2,allow_nan=False))
    raise SystemExit(0 if positive_pass else 3)

if __name__=='__main__':main()
