#!/usr/bin/env python3
"""Equivalence preflight for the frozen Stage-4 detector.

This script opens only values already consumed during Stage-3/Stage-4
development: positives 6764/1803 and the 18 Stage-3 hard-pass controls. It must
return exactly 2/2 development positives passing and 0/18 consumed negatives
passing before any fresh Stage-4 validation light curve is opened.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np, requests
import tess_binary_stage4_frozen as s4

ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
OUT=Path('results/tess_binary_stage4_preflight'); OUT.mkdir(parents=True,exist_ok=True)
POSITIVES=[6764,1803]
NEGATIVES=[1262,29489,8909,21976,18804,8400,14873,16171,25888,5676,3439,6701,18284,37203,45156,18031,6886,72939]


def sanitize(x):
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if math.isfinite(v) else None
    return x


def run_one(n,role):
    url=f'{ROOT}/{n}.lc'; r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage4-frozen-preflight/1.0'}); r.raise_for_status()
    a=np.loadtxt(r.content.splitlines())
    d=s4.detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    return sanitize({'number':n,'role':role,'source_sha256':hashlib.sha256(r.content).hexdigest(),'detector':d})


def main():
    rows=[run_one(n,'development_positive') for n in POSITIVES]+[run_one(n,'consumed_stage3_hardpass_negative') for n in NEGATIVES]
    pp=[z for z in rows if z['role']=='development_positive' and z['detector'].get('hard_pass')]
    npass=[z for z in rows if z['role'].startswith('consumed') and z['detector'].get('hard_pass')]
    checks={'positive_pass_n_exact_2':len(pp)==2,'negative_pass_n_exact_0':len(npass)==0,
            'all_eligible':all(z['detector'].get('eligible') for z in rows)}
    rep={'role':'frozen Stage-4 equivalence preflight on consumed values only','fresh_validation_values_opened':False,
         'positive_n':2,'negative_n':18,'positive_pass_n':len(pp),'negative_pass_n':len(npass),'negative_pass_numbers':[z['number'] for z in npass],
         'checks':checks,'pass':bool(all(checks.values())),'rows':rows}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'positive_pass_n':len(pp),'negative_pass_n':len(npass),'negative_pass_numbers':rep['negative_pass_numbers'],'checks':checks,'pass':rep['pass'],
      'positive_metrics':[{ 'number':z['number'],'event_recurrence_period_h':z['detector'].get('event_recurrence_period_h'),
      'local_bridge':z['detector'].get('local_bridge',{}).get('aggregate'),'hard_conditions':z['detector'].get('hard_conditions')} for z in rows if z['role']=='development_positive']},indent=2))
    raise SystemExit(0 if rep['pass'] else 20)

if __name__=='__main__': main()
