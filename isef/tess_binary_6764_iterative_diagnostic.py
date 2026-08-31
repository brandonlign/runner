#!/usr/bin/env python3
"""External-positive-only diagnostic after frozen Stage-0 failure.

Purpose: test whether Stage-0's rotation model was contaminated by the mutual-
event train. The preliminary event mask is generated ONLY from Stage-0's own
BLS output, before published 6764 orbital truth is consulted. Event/BIC hard
thresholds are unchanged. This is diagnostic development, not a target-stage
analyzer; Year-8 values are forbidden.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np, requests
from astropy.timeseries import LombScargle
from scipy.optimize import least_squares
import tess_binary_stage0_detector as d

OUT=Path('results/tess_binary_6764_iterative_diagnostic');OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
TRUTH_ORBIT_H=30.41


def fit_rotation_excluding(t,y,dy,exclude):
    use=~exclude
    base=float(t[use].max()-t[use].min())
    fmin=24.0/d.ROT_P_MAX_H;fmax=24.0/d.ROT_P_MIN_H;df=1.0/(d.ROT_OVERSAMPLE*base)
    freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t[use],y[use]-np.median(y[use]),dy[use] if dy is not None else None,fit_mean=True,center_data=True)
    power=ls.power(freq);j=int(np.nanargmax(power));p=1.0/freq[j]
    # Freeze time origin from full good light curve so the fitted coefficients
    # apply identically to masked and unmasked cadences.
    x=t-np.median(t);cols=[np.ones(len(t)),x];w=2*np.pi/p
    for h in range(1,d.ROT_HARMONICS+1):cols += [np.sin(h*w*x),np.cos(h*w*x)]
    X=np.column_stack(cols);Xu=X[use];yu=y[use]
    if dy is None:
        s=d.robust_sigma(yu-np.median(yu));ww=np.full(len(yu),1.0/max(s,1e-12))
    else:ww=1.0/dy[use]
    beta0=np.linalg.lstsq(Xu*ww[:,None],yu*ww,rcond=None)[0]
    fs=max(float(d.robust_sigma(yu-Xu@beta0)),1e-12)
    res=least_squares(lambda b:(yu-Xu@b)*ww,beta0,loss='soft_l1',f_scale=fs*np.median(ww),max_nfev=3000)
    return X@res.x,{'rotation_period_h':float(p*24),'ls_peak_power':float(power[j]),'rotation_parameters':res.x.tolist(),'fit_n':int(use.sum()),'excluded_n':int(exclude.sum())}


def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-positive-diagnostic/1.0'});r.raise_for_status();raw=OUT/'6764.lc';raw.write_bytes(r.content)
    a=np.loadtxt(raw);t,y,dy=d.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    # Reproduce Stage-0 preliminary result without consulting orbital truth.
    rot0,rm0=d.fit_rotation(t,y,dy);res0=y-rot0;b0,s0=d.scan_bls(t,res0,dy)
    phase0=((t-b0['transit_time']+0.5*b0['period_d'])%b0['period_d'])-0.5*b0['period_d']
    exclude=np.abs(phase0)<=b0['duration_d']/2
    rot1,rm1=fit_rotation_excluding(t,y,dy,exclude);res1=y-rot1
    b1,s1=d.scan_bls(t,res1,dy);ev1=d.event_diagnostics(t,res1,b1);mc1=d.model_comparison(t,res1,dy,b1,s1)
    hard={
      'depth_snr':b1['depth_snr']>=d.MIN_DEPTH_SNR,
      'event_n':ev1['predicted_observed_event_n']>=d.MIN_EVENTS,
      'coherent_fraction':ev1['coherent_event_fraction']>=d.MIN_COH_FRAC,
      'positive_median_event_depth':ev1['event_depth_median'] is not None and ev1['event_depth_median']>0,
      'dbic_noevent':mc1['delta_bic_noevent_minus_box']>=d.MIN_DBIC_NOEVENT,
      'dbic_smooth':mc1['delta_bic_smooth_minus_box']>=d.MIN_DBIC_SMOOTH,
    }
    hard_pass=bool(all(hard.values()));sel_h=b1['period_d']*24
    truth_match={str(f):bool(abs(sel_h-f*TRUTH_ORBIT_H)/(f*TRUTH_ORBIT_H)<=0.05) for f in (0.5,1.0,2.0)}
    score=float(b1['depth_snr']*math.sqrt(ev1['coherent_event_fraction'])*math.log1p(ev1['predicted_observed_event_n'])) if hard_pass else None
    rep={'role':'known-positive method diagnostic only; not frozen target analyzer','year8_values_opened':False,'raw_sha256':hashlib.sha256(r.content).hexdigest(),
         'preliminary_stage0':{'rotation':rm0,'bls':b0},'data_selected_event_mask':{'excluded_n':int(exclude.sum()),'excluded_fraction':float(exclude.mean())},
         'masked_rotation':rm1,'final_bls':b1,'events':ev1,'model_comparison':mc1,'hard_conditions_unchanged':hard,'hard_pass_unchanged':hard_pass,'score_under_stage0_formula':score,
         'truth_evaluation_after_final_selection':{'published_orbit_h':TRUTH_ORBIT_H,'selected_event_period_h':sel_h,'harmonic_matches_within_5pct':truth_match,'positive_gate_if_iterative':bool(hard_pass and any(truth_match.values()))}}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'prelim_rotation_h':rm0['rotation_period_h'],'prelim_bls_h':b0['period_d']*24,'excluded_n':int(exclude.sum()),'masked_rotation_h':rm1['rotation_period_h'],
      'final_bls_h':sel_h,'depth_snr':b1['depth_snr'],'events':ev1,'model_comparison':mc1,'hard':hard,'truth':rep['truth_evaluation_after_final_selection']},indent=2))

if __name__=='__main__':main()
