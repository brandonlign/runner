#!/usr/bin/env python3
"""Frozen Stage-4 harmonic-agnostic mutual-event detector.

Scientific target: recurrent, localized dimmings that are significantly sharper
than a smooth bridge across the same phase window. The returned recurrence
period is an event-spacing period; P versus 2P physical-orbit ambiguity is not
resolved unless independent information exists.

Do not change this file after opening the Stage-4 fresh validation light curves.
"""
from __future__ import annotations
import math
import numpy as np
import tess_binary_stage0_detector as s0

SHOULDER_INNER=0.75
SHOULDER_OUTER=2.50
MIN_SHOULDER_N=4
MIN_IN_N=1
SMOOTH_BRIDGE_DEGREE=4
MIN_BLS_SNR=6.0
MIN_USABLE_EVENTS=3
MIN_POSITIVE_EVENT_FRACTION=0.90
MIN_MEDIAN_LOCAL_SIGMA=1.50
MIN_BRIDGE_DBIC=40.0


def phase(t,t0,P): return ((t-t0+0.5*P)%P)-0.5*P

def bic(rss,n,k): return float(n*np.log(max(rss/n,1e-300))+k*np.log(max(n,2)))

def wfit(X,y,dy):
    if dy is None:
        sig=max(float(s0.robust_sigma(y)),1e-12); w=np.full(len(y),1/sig)
    else: w=1/np.asarray(dy,float)
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]; m=X@b
    return b,float(np.sum(((y-m)*w)**2)),m


def local_bridge(t,y,dy,b):
    P=float(b['period_d']); dur=float(b['duration_d']); t0=float(b['transit_time'])
    k0=math.floor((t.min()-t0)/P)-1; k1=math.ceil((t.max()-t0)/P)+1
    ev=[]; all_x=[]; all_y=[]; all_dy=[]; all_box=[]
    for k in range(k0,k1+1):
        c=t0+k*P; dt=t-c; ad=np.abs(dt)
        inside=ad<=dur/2
        shoulder=(ad>=SHOULDER_INNER*dur)&(ad<=SHOULDER_OUTER*dur)
        local=ad<=SHOULDER_OUTER*dur
        if int(inside.sum())<MIN_IN_N or int(shoulder.sum())<MIN_SHOULDER_N: continue
        xs=dt[shoulder]/dur; ys=y[shoulder]; es=dy[shoulder] if dy is not None else None
        Xs=np.column_stack([np.ones(len(xs)),xs,xs*xs]); coef,_,_=wfit(Xs,ys,es)
        xi=dt[inside]/dur; pred=np.column_stack([np.ones(len(xi)),xi,xi*xi])@coef
        depth=float(np.median(np.asarray(y[inside]-pred,float)))
        shoulder_res=ys-Xs@coef; sig=float(s0.robust_sigma(shoulder_res))
        if not np.isfinite(sig) or sig<=0: sig=float(s0.robust_sigma(ys))
        ev.append({'center':float(c),'n_in':int(inside.sum()),'n_shoulder':int(shoulder.sum()),
                   'depth':depth,'depth_over_local_sigma':float(depth/max(sig,1e-12))})
        xl=dt[local]/dur; yl=y[local]
        if dy is None:
            el=np.full(int(local.sum()),max(float(s0.robust_sigma(yl)),1e-12))
        else: el=dy[local]
        all_x.extend(xl.tolist()); all_y.extend(np.asarray(yl,float).tolist()); all_dy.extend(np.asarray(el,float).tolist())
        all_box.extend((np.abs(xl)<=0.5).astype(float).tolist())
    depths=np.array([z['depth'] for z in ev],float); ds=np.array([z['depth_over_local_sigma'] for z in ev],float)
    agg={'usable_event_n':int(len(ev)),'positive_event_fraction':float(np.mean(depths>0)) if len(depths) else 0.0,
         'median_event_depth':float(np.median(depths)) if len(depths) else None,
         'median_depth_over_local_sigma':float(np.median(ds)) if len(ds) else None,
         'event_depth_mad':float(1.4826*np.median(np.abs(depths-np.median(depths)))) if len(depths) else None}
    if len(all_y)>=20:
        x=np.asarray(all_x); yy=np.asarray(all_y); ee=np.asarray(all_dy); box=np.asarray(all_box)
        Xs=np.column_stack([x**k for k in range(SMOOTH_BRIDGE_DEGREE+1)])
        _,rs,_=wfit(Xs,yy,ee); Xb=np.column_stack([Xs,box]); bb,rb,_=wfit(Xb,yy,ee)
        agg.update({'fold_local_n':int(len(x)),'bridge_box_depth':float(bb[-1]),
                    'delta_bic_smooth_bridge_minus_box':float(bic(rs,len(x),Xs.shape[1])-bic(rb,len(x),Xb.shape[1]))})
    else:
        agg.update({'fold_local_n':int(len(all_y)),'bridge_box_depth':None,'delta_bic_smooth_bridge_minus_box':None})
    return {'events':ev,'aggregate':agg}


def detect(time,faintness,error=None,quality=None):
    t,y,dy=s0.clean_input(time,faintness,error,quality)
    out={'eligible':False,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0}
    if len(t)<s0.MIN_N or out['baseline_d']<s0.MIN_BASELINE_D: return out
    sig=float(s0.robust_sigma(y))
    if not np.isfinite(sig) or sig<=0: return out
    b,_=s0.scan_bls(t,y-np.median(y),dy)
    bridge=local_bridge(t,y,dy,b); a=bridge['aggregate']
    hard={'bls_snr':bool(b['depth_snr']>=MIN_BLS_SNR),
          'usable_event_n':bool(a['usable_event_n']>=MIN_USABLE_EVENTS),
          'positive_event_fraction':bool(a['positive_event_fraction']>=MIN_POSITIVE_EVENT_FRACTION),
          'median_local_sigma':bool(a['median_depth_over_local_sigma'] is not None and a['median_depth_over_local_sigma']>=MIN_MEDIAN_LOCAL_SIGMA),
          'positive_bridge_depth':bool(a['bridge_box_depth'] is not None and a['bridge_box_depth']>0),
          'bridge_dbic':bool(a['delta_bic_smooth_bridge_minus_box'] is not None and a['delta_bic_smooth_bridge_minus_box']>=MIN_BRIDGE_DBIC)}
    out.update({'eligible':True,'input_robust_sigma':sig,'bls':b,'event_recurrence_period_h':float(b['period_d']*24),
                'physical_orbit_alias_class_h':[float(b['period_d']*24),float(2*b['period_d']*24)],
                'local_bridge':bridge,'hard_conditions':hard,'hard_pass':bool(all(hard.values()))})
    return out
