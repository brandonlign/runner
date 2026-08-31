#!/usr/bin/env python3
"""Stage-2 detector development using ONLY the already-open 6764 positive.

Motivation: Stage-0 first fit the strongest smooth periodicity and called it
rotation.  On 6764 that period is ~15.26 h, while the published physical
rotation is 4.739 h and the mutual-event orbit is 30.41 h.  Stage-2 therefore
finds an event ephemeris first, masks those event windows, estimates the smooth
rotation on out-of-event data, and then compares joint models on all cadences.
No frozen null-control or Year-8 discovery light curve may be opened here.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np, requests
from astropy.timeseries import LombScargle
import tess_binary_stage0_detector as s0

OUT=Path('results/tess_binary_stage2_development'); OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
PUBLISHED_ROT_H=4.739
PUBLISHED_ORBIT_H=30.41
EVENT_MASK_PAD=1.5
ROT_HARMONICS=4
EVENT_SMOOTH_HARMONICS=4
MIN_DEPTH_SNR=6.0
MIN_EVENTS=3
MIN_DBIC_ROT_ONLY=20.0
MIN_DBIC_SMOOTH_EVENT=10.0


def fourier_design(t,period_d,tref,harmonics,linear=False):
    x=np.asarray(t,float)-float(tref); cols=[np.ones(len(x))]
    if linear: cols.append(x)
    w=2*np.pi/period_d
    for h in range(1,harmonics+1): cols += [np.sin(h*w*x),np.cos(h*w*x)]
    return np.column_stack(cols)


def weighted_fit(X,y,dy):
    w=1.0/np.asarray(dy,float)
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    m=X@b
    rss=float(np.sum(((y-m)/dy)**2))
    return m,b,rss


def bic(rss,n,k): return float(n*np.log(max(rss/n,1e-300))+k*np.log(n))


def event_mask(t,b,pad=EVENT_MASK_PAD):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time']
    phase=((t-t0+0.5*P)%P)-0.5*P
    return np.abs(phase)<=pad*dur/2


def estimate_rotation_period(t,y,dy):
    base=float(t.max()-t.min());fmin=24.0/s0.ROT_P_MAX_H;fmax=24.0/s0.ROT_P_MIN_H
    df=1.0/(s0.ROT_OVERSAMPLE*base);freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t,y-np.median(y),dy,fit_mean=True,center_data=True)
    power=np.asarray(ls.power(freq),float);j=int(np.nanargmax(power))
    return float(1.0/freq[j]),float(power[j])


def joint_compare(t,y,dy,b,rot_p):
    tref=float(np.median(t)); em=event_mask(t,b,pad=1.0).astype(float)
    Xr=fourier_design(t,rot_p,tref,ROT_HARMONICS,linear=True)
    Xb=np.column_stack([Xr,em])
    Xe=fourier_design(t,b['period_d'],tref,EVENT_SMOOTH_HARMONICS,linear=False)[:,1:]
    Xs=np.column_stack([Xr,Xe])
    _,br,rr=weighted_fit(Xr,y,dy);_,bb,rb=weighted_fit(Xb,y,dy);_,bs,rs=weighted_fit(Xs,y,dy)
    n=len(t);bic_r=bic(rr,n,Xr.shape[1]);bic_b=bic(rb,n,Xb.shape[1]);bic_s=bic(rs,n,Xs.shape[1])
    return {'bic_rotation_only':bic_r,'bic_rotation_plus_box':bic_b,'bic_rotation_plus_event_smooth':bic_s,
            'delta_bic_rotation_only_minus_box':bic_r-bic_b,'delta_bic_smooth_event_minus_box':bic_s-bic_b,
            'fitted_box_faintness_depth':float(bb[-1]),'rotation_model_parameter_n':int(Xr.shape[1]),
            'smooth_event_added_parameter_n':int(Xe.shape[1])}


def sanitize(x):
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if math.isfinite(v) else None
    return x


def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-stage2-dev-positive-only/1.0'});r.raise_for_status()
    raw=OUT/'6764.lc';raw.write_bytes(r.content)
    a=np.loadtxt(raw);t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    if len(t)<s0.MIN_N or t.max()-t.min()<s0.MIN_BASELINE_D: raise RuntimeError('6764 unexpectedly ineligible')
    # Event search precedes any rotation prewhitening; BLS sees only median-centered raw faintness.
    b,raw_sig=s0.scan_bls(t,y-np.median(y),dy)
    masked=event_mask(t,b)
    tout,yout,dyout=t[~masked],y[~masked],dy[~masked]
    rot_p,rot_power=estimate_rotation_period(tout,yout,dyout)
    cmp=joint_compare(t,y,dy,b,rot_p)
    # Count event windows that actually contain >=2 good cadences; this is geometry only, not depth thresholding.
    P=b['period_d'];t0=b['transit_time'];dur=b['duration_d'];k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1
    event_n=0
    for k in range(k0,k1+1):
        if int((np.abs(t-(t0+k*P))<=dur/2).sum())>=2:event_n+=1
    hard={'depth_snr':b['depth_snr']>=MIN_DEPTH_SNR,'event_n':event_n>=MIN_EVENTS,
          'positive_box_depth':cmp['fitted_box_faintness_depth']>0,
          'dbic_rotation_only':cmp['delta_bic_rotation_only_minus_box']>=MIN_DBIC_ROT_ONLY,
          'dbic_smooth_event':cmp['delta_bic_smooth_event_minus_box']>=MIN_DBIC_SMOOTH_EVENT}
    stage2_pass=bool(all(hard.values()))
    event_h=float(P*24);rot_h=float(rot_p*24)
    event_harm={str(f):bool(abs(event_h-f*PUBLISHED_ORBIT_H)/(f*PUBLISHED_ORBIT_H)<=0.05) for f in (0.5,1.0,2.0)}
    rot_match=bool(abs(rot_h-PUBLISHED_ROT_H)/PUBLISHED_ROT_H<=0.05 or abs(2*rot_h-PUBLISHED_ROT_H)/PUBLISHED_ROT_H<=0.05 or abs(rot_h/2-PUBLISHED_ROT_H)/PUBLISHED_ROT_H<=0.05)
    dev_positive_pass=bool(stage2_pass and any(event_harm.values()) and rot_match)
    rep=sanitize({'role':'Stage-2 development on already-open 6764 positive only; no null/discovery values opened',
      'target':'(6764) Kirillavrov','source_url':URL,'raw_sha256':hashlib.sha256(r.content).hexdigest(),
      'architecture':'raw BLS event search -> padded event mask -> out-of-event rotation search -> full-data joint BIC',
      'thresholds':{'event_mask_pad':EVENT_MASK_PAD,'min_depth_snr':MIN_DEPTH_SNR,'min_events':MIN_EVENTS,
                    'min_dbic_rotation_only':MIN_DBIC_ROT_ONLY,'min_dbic_smooth_event':MIN_DBIC_SMOOTH_EVENT,
                    'rotation_harmonics':ROT_HARMONICS,'event_smooth_harmonics':EVENT_SMOOTH_HARMONICS},
      'n_good':len(t),'baseline_d':float(t.max()-t.min()),'masked_event_fraction':float(masked.mean()),'out_of_event_n':len(tout),
      'bls':b,'event_n':event_n,'selected_event_period_h':event_h,'published_orbital_period_h':PUBLISHED_ORBIT_H,
      'event_harmonic_matches_within_5pct':event_harm,
      'selected_rotation_period_h':rot_h,'rotation_ls_power':rot_power,'published_rotation_period_h':PUBLISHED_ROT_H,
      'rotation_matches_published_or_half_double_within_5pct':rot_match,
      'joint_model_comparison':cmp,'hard_conditions':hard,'stage2_detector_pass':stage2_pass,'development_positive_pass':dev_positive_pass,
      'null_control_values_opened':False,'year8_values_opened':False})
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:rep[k] for k in ('selected_event_period_h','event_harmonic_matches_within_5pct','selected_rotation_period_h','rotation_matches_published_or_half_double_within_5pct','masked_event_fraction','joint_model_comparison','hard_conditions','stage2_detector_pass','development_positive_pass')},indent=2,allow_nan=False))
    raise SystemExit(0 if dev_positive_pass else 5)

if __name__=='__main__':main()
