#!/usr/bin/env python3
"""Stage-1 detector development using ONLY the already-open 6764 positive.

This file is development-only until frozen in the science repository.  It must
not be run on any frozen null-control or Year-8 discovery light curve before
that freeze.  The Stage-0 individual-event coherence rule is replaced by a
replication test: a full-data candidate ephemeris must retain positive box
support in independently rotation-fitted early and late time halves.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np, requests
import tess_binary_stage0_detector as s0

OUT=Path('results/tess_binary_stage1_development'); OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
ORBIT_H=30.41
MIN_SPLIT_N=100
MIN_SPLIT_DBIC_NOEVENT=6.0
MIN_SPLIT_DBIC_SMOOTH=0.0


def fixed_ephemeris_comparison(t,y,dy,b):
    rot,rm=s0.fit_rotation(t,y,dy)
    resid=y-rot
    sig=s0.robust_sigma(resid)
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time']
    phase=((t-t0+0.5*P)%P)-0.5*P
    box=(np.abs(phase)<=dur/2).astype(float)
    X0=np.ones((len(t),1)); Xb=np.column_stack([np.ones(len(t)),box]); Xs=s0.design_fourier(t,P,4,linear=False)
    m0,_=s0.linear_weighted_fit(X0,resid,dy,sig)
    mb,bb=s0.linear_weighted_fit(Xb,resid,dy,sig)
    ms,_=s0.linear_weighted_fit(Xs,resid,dy,sig)
    r0=s0.weighted_rss(resid,m0,dy,sig); rb=s0.weighted_rss(resid,mb,dy,sig); rs=s0.weighted_rss(resid,ms,dy,sig)
    n=len(t); b0=s0.bic(r0,n,1); bbox=s0.bic(rb,n,2); bs=s0.bic(rs,n,9)
    return {
      'n':int(n),'baseline_d':float(t.max()-t.min()),'rotation_period_h':float(rm['rotation_period_h']),
      'fitted_box_faintness_depth':float(bb[1]),
      'delta_bic_noevent_minus_box':float(b0-bbox),
      'delta_bic_smooth_minus_box':float(bs-bbox),
      'residual_robust_sigma':float(sig),
    }


def sanitize(x):
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if math.isfinite(v) else None
    return x


def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-stage1-dev-positive-only/1.0'}); r.raise_for_status()
    raw=OUT/'6764.lc'; raw.write_bytes(r.content)
    a=np.loadtxt(raw)
    t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    full=s0.detect(t,y,dy,None)
    if not full.get('eligible'): raise RuntimeError('6764 unexpectedly ineligible')
    b=full['bls']; tm=float(np.median(t))
    early=t<=tm; late=t>tm
    halves={'early':fixed_ephemeris_comparison(t[early],y[early],dy[early],b),
            'late':fixed_ephemeris_comparison(t[late],y[late],dy[late],b)}
    full_core={k:bool(full['hard_conditions'][k]) for k in ('depth_snr','event_n','positive_median_event_depth','dbic_noevent','dbic_smooth')}
    split_conditions={}
    for name,z in halves.items():
        split_conditions[name]={
          'n':z['n']>=MIN_SPLIT_N,
          'positive_depth':z['fitted_box_faintness_depth']>0,
          'dbic_noevent':z['delta_bic_noevent_minus_box']>=MIN_SPLIT_DBIC_NOEVENT,
          'dbic_smooth':z['delta_bic_smooth_minus_box']>=MIN_SPLIT_DBIC_SMOOTH,
        }
    stage1_pass=bool(all(full_core.values()) and all(all(v.values()) for v in split_conditions.values()))
    selected_h=float(b['period_d']*24)
    harmonic_matches={str(f):bool(abs(selected_h-f*ORBIT_H)/(f*ORBIT_H)<=0.05) for f in (0.5,1.0,2.0)}
    dev_positive_pass=bool(stage1_pass and any(harmonic_matches.values()))
    rep=sanitize({
      'role':'Stage-1 development on the already-open 6764 positive only; no null/discovery values opened',
      'target':'(6764) Kirillavrov','source_url':URL,'raw_sha256':hashlib.sha256(r.content).hexdigest(),
      'stage0_hard_pass':full['hard_pass'],'stage0_failed_conditions':[k for k,v in full['hard_conditions'].items() if not v],
      'stage1_change':'replace individual-event coherent_fraction gate with exact-ephemeris independent early/late replication',
      'thresholds':{'min_split_n':MIN_SPLIT_N,'min_split_dbic_noevent':MIN_SPLIT_DBIC_NOEVENT,'min_split_dbic_smooth':MIN_SPLIT_DBIC_SMOOTH,'split_positive_box_depth_required':True},
      'full_core_conditions':full_core,'split_conditions':split_conditions,'halves':halves,
      'selected_event_period_h':selected_h,'published_orbital_period_h':ORBIT_H,'harmonic_matches_within_5pct':harmonic_matches,
      'stage1_detector_pass':stage1_pass,'development_positive_pass':dev_positive_pass,
      'full_detector':full,
      'null_control_values_opened':False,'year8_values_opened':False,
    })
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:rep[k] for k in ('stage0_hard_pass','stage0_failed_conditions','selected_event_period_h','harmonic_matches_within_5pct','full_core_conditions','split_conditions','halves','stage1_detector_pass','development_positive_pass')},indent=2,allow_nan=False))
    raise SystemExit(0 if dev_positive_pass else 4)

if __name__=='__main__': main()
