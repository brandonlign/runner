#!/usr/bin/env python3
"""Frozen Stage-0 mutual-event detector for asteroid light curves.

Scientific contract: brandonlign/isef research/TESS_BINARY_STAGE0_FREEZE_2026-08-31.md
Do not change thresholds after reading the 6764 positive or Year-8 targets.
"""
from __future__ import annotations
import math
import numpy as np
from astropy.timeseries import LombScargle, BoxLeastSquares
from scipy.optimize import least_squares

ROT_P_MIN_H=2.0
ROT_P_MAX_H=50.0
ROT_OVERSAMPLE=5.0
ROT_HARMONICS=4
ORB_P_MIN_D=0.25
ORB_P_MAX_D=8.0
BLS_N_PERIOD=6000
DURATIONS_H=np.array([0.5,1.0,1.5,2.0,3.0,4.0,6.0,8.0],float)
MIN_N=200
MIN_BASELINE_D=5.0
MIN_DEPTH_SNR=6.0
MIN_EVENTS=3
MIN_COH_FRAC=0.60
MIN_EVENT_SIGMA=1.5
MIN_DBIC_NOEVENT=20.0
MIN_DBIC_SMOOTH=10.0


def robust_sigma(x):
    a=np.asarray(x,float);a=a[np.isfinite(a)]
    if not len(a): return np.nan
    m=float(np.median(a));s=1.4826*float(np.median(np.abs(a-m)))
    if not np.isfinite(s) or s<=0: s=float(np.std(a))
    return s


def clean_input(time,faintness,error=None,quality=None):
    t=np.asarray(time,float);y=np.asarray(faintness,float)
    good=np.isfinite(t)&np.isfinite(y)
    if error is not None:
        e=np.asarray(error,float);good &= np.isfinite(e)&(e>0)
    else:e=None
    if quality is not None:good &= np.asarray(quality)==0
    t=t[good];y=y[good];e=e[good] if e is not None else None
    o=np.argsort(t);t=t[o];y=y[o];e=e[o] if e is not None else None
    return t,y,e


def design_fourier(t,period_d,harmonics=4,linear=False):
    x=t-np.median(t);cols=[np.ones(len(t))]
    if linear: cols.append(x)
    w=2*np.pi/period_d
    for h in range(1,harmonics+1):
        cols += [np.sin(h*w*x),np.cos(h*w*x)]
    return np.column_stack(cols)


def fit_rotation(t,y,dy):
    y0=y-np.median(y);base=float(t.max()-t.min())
    fmin=24.0/ROT_P_MAX_H;fmax=24.0/ROT_P_MIN_H
    df=1.0/(ROT_OVERSAMPLE*base)
    freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t,y0,dy if dy is not None else None,fit_mean=True,center_data=True)
    power=ls.power(freq);j=int(np.nanargmax(power));p=1.0/freq[j]
    X=design_fourier(t,p,ROT_HARMONICS,linear=True)
    if dy is None:
        s=robust_sigma(y0);w=np.full(len(t),1.0/max(s,1e-12))
    else:w=1.0/dy
    beta0=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    fs=robust_sigma(y-X@beta0);fs=max(float(fs),1e-12)
    def fun(b):return (y-X@b)*w
    res=least_squares(fun,beta0,loss='soft_l1',f_scale=fs*np.median(w),max_nfev=3000)
    model=X@res.x
    return model,{'rotation_period_h':float(p*24),'ls_peak_power':float(power[j]),'rotation_parameters':res.x.tolist()}


def weighted_rss(y,model,dy,sigma):
    scale=dy if dy is not None else np.full(len(y),sigma)
    r=(y-model)/scale
    return float(np.sum(r*r))


def linear_weighted_fit(X,y,dy,sigma):
    w=1.0/(dy if dy is not None else np.full(len(y),sigma))
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    return X@b,b


def bic(rss,n,k):
    return float(n*np.log(max(rss/n,1e-300))+k*np.log(n))


def scan_bls(t,resid,dy):
    baseline=float(t.max()-t.min());pmax=min(ORB_P_MAX_D,baseline/3.0)
    if pmax<=ORB_P_MIN_D: raise ValueError('baseline too short for frozen orbital search')
    periods=np.geomspace(ORB_P_MIN_D,pmax,BLS_N_PERIOD)
    sig=robust_sigma(resid);err=dy if dy is not None else np.full(len(t),sig)
    bls=BoxLeastSquares(t,-resid,dy=err)
    best=None
    for dh in DURATIONS_H:
        d=dh/24.0;pp=periods[periods>4.0*d]
        if not len(pp):continue
        q=bls.power(pp,d,objective='snr')
        sn=np.asarray(q.depth_snr,float);j=int(np.nanargmax(sn))
        z={'period_d':float(q.period[j]),'duration_d':float(q.duration[j]),'transit_time':float(q.transit_time[j]),
           'depth_snr':float(sn[j]),'bls_power':float(np.asarray(q.power)[j]),'bls_depth_flux_units':float(np.asarray(q.depth)[j])}
        if best is None or z['depth_snr']>best['depth_snr']:best=z
    if best is None:raise RuntimeError('no valid BLS duration/period combination')
    return best,sig


def event_diagnostics(t,resid,b):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time'];sig=robust_sigma(resid)
    k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1
    depths=[];centers=[]
    for k in range(k0,k1+1):
        c=t0+k*P;m=np.abs(t-c)<=dur/2
        if int(m.sum())>=2:
            depths.append(float(np.median(resid[m])));centers.append(float(c))
    coh=[d>=MIN_EVENT_SIGMA*sig for d in depths]
    frac=float(np.mean(coh)) if coh else 0.0
    return {'predicted_observed_event_n':len(depths),'coherent_event_n':int(sum(coh)),'coherent_event_fraction':frac,
            'event_depths_faintness':depths,'event_centers':centers,'event_depth_median':float(np.median(depths)) if depths else None,'residual_robust_sigma':float(sig)}


def model_comparison(t,resid,dy,b,sigma):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time'];phase=((t-t0+0.5*P)%P)-0.5*P
    box=(np.abs(phase)<=dur/2).astype(float)
    X0=np.ones((len(t),1));Xb=np.column_stack([np.ones(len(t)),box]);Xs=design_fourier(t,P,4,linear=False)
    m0,_=linear_weighted_fit(X0,resid,dy,sigma);mb,bb=linear_weighted_fit(Xb,resid,dy,sigma);ms,_=linear_weighted_fit(Xs,resid,dy,sigma)
    r0=weighted_rss(resid,m0,dy,sigma);rb=weighted_rss(resid,mb,dy,sigma);rs=weighted_rss(resid,ms,dy,sigma);n=len(t)
    b0=bic(r0,n,1);bbox=bic(rb,n,2);bs=bic(rs,n,9)
    return {'bic_no_event':b0,'bic_box':bbox,'bic_smooth4':bs,'delta_bic_noevent_minus_box':b0-bbox,'delta_bic_smooth_minus_box':bs-bbox,
            'fitted_box_faintness_depth':float(bb[1])}


def detect(time,faintness,error=None,quality=None):
    t,y,dy=clean_input(time,faintness,error,quality)
    out={'eligible':False,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0}
    if len(t)<MIN_N or out['baseline_d']<MIN_BASELINE_D:return out
    s0=robust_sigma(y)
    if not np.isfinite(s0) or s0<=0:return out
    rot,rm=fit_rotation(t,y,dy);resid=y-rot
    b,sig=scan_bls(t,resid,dy);ev=event_diagnostics(t,resid,b);mc=model_comparison(t,resid,dy,b,sig)
    hard={
      'depth_snr':b['depth_snr']>=MIN_DEPTH_SNR,
      'event_n':ev['predicted_observed_event_n']>=MIN_EVENTS,
      'coherent_fraction':ev['coherent_event_fraction']>=MIN_COH_FRAC,
      'positive_median_event_depth':ev['event_depth_median'] is not None and ev['event_depth_median']>0,
      'dbic_noevent':mc['delta_bic_noevent_minus_box']>=MIN_DBIC_NOEVENT,
      'dbic_smooth':mc['delta_bic_smooth_minus_box']>=MIN_DBIC_SMOOTH,
    }
    passed=bool(all(hard.values()))
    score=float(b['depth_snr']*math.sqrt(ev['coherent_event_fraction'])*math.log1p(ev['predicted_observed_event_n'])) if passed else float('-inf')
    out.update({'eligible':True,'input_robust_sigma':float(s0),'rotation':rm,'bls':b,'events':ev,'model_comparison':mc,'hard_conditions':hard,'hard_pass':passed,'score':score})
    return out
