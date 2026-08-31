#!/usr/bin/env python3
"""Frozen Stage-1 mutual-event detector.

Scientific contract:
  brandonlign/isef/research/TESS_BINARY_STAGE1_FREEZE_2026-08-31.md

Stage-1 was designed using the external 6764 development positive. It must not
be altered after independent null/injection outcomes are inspected.
"""
from __future__ import annotations
import math
import numpy as np
from astropy.timeseries import LombScargle
from scipy.optimize import least_squares
import tess_binary_stage0_detector as s0


def _rotation_refit_excluding(t,y,dy,exclude):
    use=~np.asarray(exclude,bool)
    if int(use.sum())<s0.MIN_N: raise ValueError('too few cadences after preliminary event mask')
    base=float(t[use].max()-t[use].min())
    fmin=24.0/s0.ROT_P_MAX_H;fmax=24.0/s0.ROT_P_MIN_H
    df=1.0/(s0.ROT_OVERSAMPLE*base);freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t[use],y[use]-np.median(y[use]),dy[use] if dy is not None else None,fit_mean=True,center_data=True)
    power=ls.power(freq);j=int(np.nanargmax(power));p=1.0/freq[j]
    x=t-np.median(t);cols=[np.ones(len(t)),x];w=2*np.pi/p
    for h in range(1,s0.ROT_HARMONICS+1):cols += [np.sin(h*w*x),np.cos(h*w*x)]
    X=np.column_stack(cols);Xu=X[use];yu=y[use]
    if dy is None:
        sc=s0.robust_sigma(yu-np.median(yu));ww=np.full(len(yu),1.0/max(sc,1e-12))
    else:ww=1.0/dy[use]
    beta0=np.linalg.lstsq(Xu*ww[:,None],yu*ww,rcond=None)[0]
    fs=max(float(s0.robust_sigma(yu-Xu@beta0)),1e-12)
    rr=least_squares(lambda b:(yu-Xu@b)*ww,beta0,loss='soft_l1',f_scale=fs*np.median(ww),max_nfev=3000)
    return X@rr.x,{'rotation_period_h':float(p*24),'ls_peak_power':float(power[j]),'fit_n':int(use.sum()),'excluded_n':int((~use).sum()),'rotation_parameters':rr.x.tolist()}


def _fit_linear(X,y,dy,sigma):
    w=1.0/(dy if dy is not None else np.full(len(y),sigma))
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    m=X@b
    rss=s0.weighted_rss(y,m,dy,sigma)
    return b,m,rss,s0.bic(rss,len(y),X.shape[1])


def _smooth_design(t,P):
    x=t-np.median(t);cols=[np.ones(len(t))];w=2*np.pi/P
    for h in range(1,5):cols += [np.sin(h*w*x),np.cos(h*w*x)]
    return np.column_stack(cols)


def _interpretations(t,resid,dy,b,sigma):
    P0=float(b['period_d']);D=float(b['duration_d']);T0=float(b['transit_time']);n=len(t)
    X0=np.ones((n,1));_,_,r0,bic0=_fit_linear(X0,resid,dy,sigma)
    out=[]
    # H1: one event per P0
    ph=((t-T0+0.5*P0)%P0)-0.5*P0;bx=(np.abs(ph)<=D/2).astype(float)
    bb,_,rb,bice=_fit_linear(np.column_stack([np.ones(n),bx]),resid,dy,sigma)
    _,_,rs,bics=_fit_linear(_smooth_design(t,P0),resid,dy,sigma)
    out.append({'name':'H1_ONE_EVENT','orbital_period_d':P0,'event_bic':bice,'noevent_bic':bic0,'smooth_bic':bics,
                'delta_bic_noevent_minus_event':bic0-bice,'delta_bic_smooth_minus_event':bics-bice,
                'depths_faintness':[float(bb[1])],'positive_depths':bool(bb[1]>0)})
    # H2: two alternating events in 2P0, identical duration, independent depths.
    P2=2*P0;ph=((t-T0+0.5*P2)%P2)-0.5*P2
    b1=(np.abs(ph)<=D/2).astype(float);b2=(np.abs(np.abs(ph)-P0)<=D/2).astype(float)
    bb2,_,rb2,bice2=_fit_linear(np.column_stack([np.ones(n),b1,b2]),resid,dy,sigma)
    _,_,rs2,bics2=_fit_linear(_smooth_design(t,P2),resid,dy,sigma)
    out.append({'name':'H2_ALTERNATING_TWO_EVENT','orbital_period_d':P2,'event_bic':bice2,'noevent_bic':bic0,'smooth_bic':bics2,
                'delta_bic_noevent_minus_event':bic0-bice2,'delta_bic_smooth_minus_event':bics2-bice2,
                'depths_faintness':[float(bb2[1]),float(bb2[2])],'positive_depths':bool(bb2[1]>0 and bb2[2]>0)})
    for z in out:
        z['model_pass']=bool(z['positive_depths'] and z['delta_bic_noevent_minus_event']>=s0.MIN_DBIC_NOEVENT and z['delta_bic_smooth_minus_event']>=s0.MIN_DBIC_SMOOTH)
    passing=[z for z in out if z['model_pass']]
    selected=None
    if passing:
        passing=sorted(passing,key=lambda z:(-z['delta_bic_smooth_minus_event'],z['event_bic'],z['name']))
        selected=passing[0]
    return out,selected


def detect(time,faintness,error=None,quality=None):
    t,y,dy=s0.clean_input(time,faintness,error,quality)
    out={'eligible':False,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0}
    if len(t)<s0.MIN_N or out['baseline_d']<s0.MIN_BASELINE_D:return out
    sig0=s0.robust_sigma(y)
    if not np.isfinite(sig0) or sig0<=0:return out
    # Preliminary pass.
    rot0,rm0=s0.fit_rotation(t,y,dy);r0=y-rot0;b0,_=s0.scan_bls(t,r0,dy)
    ph0=((t-b0['transit_time']+0.5*b0['period_d'])%b0['period_d'])-0.5*b0['period_d']
    exclude=np.abs(ph0)<=b0['duration_d']/2
    # Event-masked nuisance refit; final event search sees all good cadences.
    rot1,rm1=_rotation_refit_excluding(t,y,dy,exclude);resid=y-rot1
    b1,sig=s0.scan_bls(t,resid,dy);ev=s0.event_diagnostics(t,resid,b1)
    interps,selected=_interpretations(t,resid,dy,b1,sig)
    hard_event={
      'depth_snr':b1['depth_snr']>=s0.MIN_DEPTH_SNR,
      'event_n':ev['predicted_observed_event_n']>=s0.MIN_EVENTS,
      'coherent_fraction':ev['coherent_event_fraction']>=s0.MIN_COH_FRAC,
      'positive_median_event_depth':ev['event_depth_median'] is not None and ev['event_depth_median']>0,
    }
    hard_pass=bool(all(hard_event.values()) and selected is not None)
    score=float(b1['depth_snr']*math.sqrt(ev['coherent_event_fraction'])*math.log1p(ev['predicted_observed_event_n'])) if hard_pass else float('-inf')
    out.update({'eligible':True,'input_robust_sigma':float(sig0),'preliminary_rotation':rm0,'preliminary_bls':b0,'preliminary_event_mask_n':int(exclude.sum()),
                'masked_rotation':rm1,'final_bls':b1,'events':ev,'interpretations':interps,'selected_interpretation':selected,
                'hard_event_conditions':hard_event,'hard_pass':hard_pass,'score':score})
    return out
