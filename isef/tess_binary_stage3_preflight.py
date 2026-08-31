#!/usr/bin/env python3
"""Preflight frozen Stage-3 on the already-open 6764 development positive only."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np, requests
from tess_binary_stage3_frozen import detect

OUT=Path('results/tess_binary_stage3_preflight');OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
EXPECTED_PERIOD_H=30.400419855420907
EXPECTED_MULT=2
EXPECTED_DBIC_SMOOTH=103.00419171309795


def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-stage3-frozen-preflight/1.0'});r.raise_for_status()
    a=np.loadtxt(r.content.splitlines())
    d=detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    c=d.get('chosen_hypothesis',{})
    checks={
      'eligible':bool(d.get('eligible')),
      'hard_pass':bool(d.get('hard_pass')),
      'orbit_multiplier_exact':c.get('orbit_multiplier')==EXPECTED_MULT,
      'period_reproduces_development':abs(float(c.get('physical_period_h',-1))-EXPECTED_PERIOD_H)<1e-9,
      'dbic_smooth_reproduces_development':abs(float(c.get('delta_bic_smooth_minus_binary',-1))-EXPECTED_DBIC_SMOOTH)<1e-8,
      'two_positive_depths':len(c.get('box_depths_faintness',[]))==2 and all(x>0 for x in c.get('box_depths_faintness',[])),
    }
    rep={'role':'preflight only on already-open 6764 development positive','source_sha256':hashlib.sha256(r.content).hexdigest(),
         'checks':checks,'pass':bool(all(checks.values())),'detector':d,'null_control_values_opened':False,'validation_positive_1803_opened':False,'year8_values_opened':False}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'chosen_hypothesis':c,'pass':rep['pass']},indent=2,allow_nan=False))
    raise SystemExit(0 if rep['pass'] else 7)

if __name__=='__main__':main()
