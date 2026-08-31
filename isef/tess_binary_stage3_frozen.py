#!/usr/bin/env python3
"""Frozen Stage-3 mutual-event detector.

Scientific contract is recorded in brandonlign/isef.  This module is target
agnostic and contains no published target periods.  Do not change detector
architecture or thresholds after opening the untouched validation positive or
frozen null-control light curves.
"""
from __future__ import annotations
import math
import numpy as np
from astropy.timeseries import LombScargle
import tess_binary_stage0_detector as s0

EVENT_MASK_PAD=1.5
ROT_HARMONICS=4
EVENT_SMOOTH_HARMONICS=4
MIN_DEPTH_SNR=6.0
MIN_EVENTS=3
MIN_DBIC_ROT_ONLY=20.0
MIN_DBIC_SMOOTH=10.0


def fourier_design(t,period_d,tref,harmonics,linear=False):
    x=np.asarray(t,float)-float(tref);cols=[np.ones(len(x))]
    if linear:cols.append(x)
    w=2*np.pi/period_d
    for h in range(1,harmonics+1):cols += [np.sin(h*w*x),np.cos(h*w*x)]
    return np.column_stack(cols)


def fit(X,y,dy):
    if dy is None:
        sig=s0.robust_sigma(y)
        if not np.isfinite(sig) or sig<=0: sig=float(np.std(y))
        dy=np.full(len(y),max(float(sig),1e-12))
    w=1/np.asarray(dy,float)
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    m=X@b
    return b,float(np.sum(((y-m)/dy)**2))


def bic(rss,n,k):return float(n*np.log(max(rss/n,1e-300))+k*np.log(n))


def phase(t,t0,P):return ((t-t0+0.5*P)%P)-0.5*P


def base_event_mask(t,b,pad=EVENT_MASK_PAD):
    return np.abs(phase(t,b['transit_time'],b['period_d']))<=pad*b['duration_d']/2


def estimate_rotation(t,y,dy):
    base=float(t.max()-t.min());fmin=24/s0.ROT_P_MAX_H;fmax=24/s0.ROT_P_MIN_H
    df=1/(s0.ROT_OVERSAMPLE*base);freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t,y-np.median(y),dy if dy is not None else None,fit_mean=True,center_data=True)
    power=np.asarray(ls.power(freq),float);j=int(np.nanargmax(power))
    return float(1/freq[j]),float(power[j])


def compare_hypothesis(t,y,dy,b,rot_p,mult):
    Pe=b['period_d'];Porb=mult*Pe;t0=b['transit_time'];dur=b['duration_d'];tref=float(np.median(t))
    Xr=fourier_design(t,rot_p,tref,ROT_HARMONICS,linear=True)
    if mult==1:
        boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float)]
    elif mult==2:
        boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float),
               (np.abs(phase(t,t0+Pe,Porb))<=dur/2).astype(float)]
    else:raise ValueError(mult)
    Xb=np.column_stack([Xr,*boxes])
    Xe=fourier_design(t,Porb,tref,EVENT_SMOOTH_HARMONICS,linear=False)[:,1:]
    Xs=np.column_stack([Xr,Xe])
    _,rr=fit(Xr,y,dy);bb,rb=fit(Xb,y,dy);_,rs=fit(Xs,y,dy);n=len(t)
    BicR=bic(rr,n,Xr.shape[1]);BicB=bic(rb,n,Xb.shape[1]);BicS=bic(rs,n,Xs.shape[1])
    return {'orbit_multiplier':int(mult),'physical_period_d':float(Porb),'physical_period_h':float(Porb*24),
            'box_depths_faintness':[float(x) for x in bb[-len(boxes):]],
            'bic_rotation_only':BicR,'bic_binary_boxes':BicB,'bic_rotation_plus_smooth':BicS,
            'delta_bic_rotation_only_minus_binary':float(BicR-BicB),
            'delta_bic_smooth_minus_binary':float(BicS-BicB),
            'binary_added_parameter_n':int(len(boxes)),'smooth_added_parameter_n':int(Xe.shape[1])}


def observed_event_count(t,b):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time']
    k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1
    return int(sum(int((np.abs(t-(t0+k*P))<=dur/2).sum())>=2 for k in range(k0,k1+1)))


def detect(time,faintness,error=None,quality=None):
    t,y,dy=s0.clean_input(time,faintness,error,quality)
    out={'eligible':False,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0}
    if len(t)<s0.MIN_N or out['baseline_d']<s0.MIN_BASELINE_D:return out
    sig=s0.robust_sigma(y)
    if not np.isfinite(sig) or sig<=0:return out
    b,_=s0.scan_bls(t,y-np.median(y),dy)
    masked=base_event_mask(t,b)
    if int((~masked).sum())<s0.MIN_N:return out
    rot_p,rot_power=estimate_rotation(t[~masked],y[~masked],dy[~masked] if dy is not None else None)
    hyps=[compare_hypothesis(t,y,dy,b,rot_p,m) for m in (1,2)]
    chosen=min(hyps,key=lambda z:z['bic_binary_boxes'])
    event_n=observed_event_count(t,b)
    hard={'depth_snr':bool(b['depth_snr']>=MIN_DEPTH_SNR),'event_n':bool(event_n>=MIN_EVENTS),
          'all_box_depths_positive':bool(all(x>0 for x in chosen['box_depths_faintness'])),
          'dbic_rotation_only':bool(chosen['delta_bic_rotation_only_minus_binary']>=MIN_DBIC_ROT_ONLY),
          'dbic_smooth':bool(chosen['delta_bic_smooth_minus_binary']>=MIN_DBIC_SMOOTH)}
    passed=bool(all(hard.values()))
    out.update({'eligible':True,'input_robust_sigma':float(sig),'bls':b,'event_n':event_n,
                'event_mask_fraction':float(masked.mean()),'rotation_period_h_alias':float(rot_p*24),
                'rotation_ls_power':float(rot_power),'hypotheses':hyps,'chosen_hypothesis':chosen,
                'hard_conditions':hard,'hard_pass':passed})
    return out
