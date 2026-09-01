#!/usr/bin/env python3
"""Stage-4 development diagnostics using only already-consumed Stage-3 light curves.

No fresh known-binary inventory object and no future validation control is opened.
The development positives are 6764 and 1803. The development negatives are the
18 Stage-3 hard-pass historical controls, which are now explicitly diagnostic
rather than confirmatory data.

Goal: test whether BLS-selected recurrent dimmings are abrupt/localized relative
to a smooth bridge across the event window, rather than merely minima of an
ordinary smooth asteroid rotational waveform.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np, requests
import tess_binary_stage0_detector as s0

ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
OUT=Path('results/tess_binary_stage4_dev_diagnostics'); OUT.mkdir(parents=True,exist_ok=True)
POSITIVES=[6764,1803]
NEGATIVES=[1262,29489,8909,21976,18804,8400,14873,16171,25888,5676,3439,6701,18284,37203,45156,18031,6886,72939]
SHOULDER_INNER=0.75
SHOULDER_OUTER=2.50
MIN_SHOULDER_N=4
MIN_IN_N=1


def phase(t,t0,P): return ((t-t0+0.5*P)%P)-0.5*P

def bic(rss,n,k): return float(n*np.log(max(rss/n,1e-300))+k*np.log(max(n,2)))

def wfit(X,y,dy):
    if dy is None:
        sig=max(float(s0.robust_sigma(y)),1e-12); w=np.full(len(y),1/sig)
    else: w=1/np.asarray(dy,float)
    b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0]
    m=X@b
    return b,float(np.sum(((y-m)*(w))**2)),m


def local_bridge(t,y,dy,b):
    P=float(b['period_d']); dur=float(b['duration_d']); t0=float(b['transit_time'])
    k0=math.floor((t.min()-t0)/P)-1; k1=math.ceil((t.max()-t0)/P)+1
    ev=[]
    all_x=[]; all_y=[]; all_dy=[]; all_box=[]
    for k in range(k0,k1+1):
        c=t0+k*P; dt=t-c; ad=np.abs(dt)
        inside=ad<=dur/2
        shoulder=(ad>=SHOULDER_INNER*dur)&(ad<=SHOULDER_OUTER*dur)
        local=ad<=SHOULDER_OUTER*dur
        if int(inside.sum())<MIN_IN_N or int(shoulder.sum())<MIN_SHOULDER_N: continue
        xs=dt[shoulder]/dur; ys=y[shoulder]; es=dy[shoulder] if dy is not None else None
        Xs=np.column_stack([np.ones(len(xs)),xs,xs*xs])
        coef,_,_=wfit(Xs,ys,es)
        xi=dt[inside]/dur; pred=np.column_stack([np.ones(len(xi)),xi,xi*xi])@coef
        depths=np.asarray(y[inside]-pred,float)
        depth=float(np.median(depths)); shoulder_res=ys-Xs@coef
        sig=float(s0.robust_sigma(shoulder_res));
        if not np.isfinite(sig) or sig<=0: sig=float(s0.robust_sigma(ys))
        ev.append({'center':float(c),'n_in':int(inside.sum()),'n_shoulder':int(shoulder.sum()),
                   'depth':depth,'depth_over_local_sigma':float(depth/max(sig,1e-12))})
        xl=dt[local]/dur; yl=y[local]; el=dy[local] if dy is not None else np.full(int(local.sum()),max(float(s0.robust_sigma(y[local])),1e-12))
        all_x.extend(xl.tolist()); all_y.extend(yl.tolist()); all_dy.extend(np.asarray(el,float).tolist()); all_box.extend((np.abs(xl)<=0.5).astype(float).tolist())
    depths=np.array([z['depth'] for z in ev],float)
    ds=np.array([z['depth_over_local_sigma'] for z in ev],float)
    agg={'usable_event_n':int(len(ev)),'positive_event_fraction':float(np.mean(depths>0)) if len(depths) else 0.0,
         'median_event_depth':float(np.median(depths)) if len(depths) else None,
         'median_depth_over_local_sigma':float(np.median(ds)) if len(ds) else None,
         'event_depth_mad':float(1.4826*np.median(np.abs(depths-np.median(depths)))) if len(depths) else None}
    if len(all_y)>=20:
        x=np.asarray(all_x); yy=np.asarray(all_y); ee=np.asarray(all_dy); box=np.asarray(all_box)
        Xs=np.column_stack([np.ones(len(x)),x,x*x,x**3,x**4])
        _,rs,_=wfit(Xs,yy,ee)
        Xb=np.column_stack([Xs,box]); bb,rb,_=wfit(Xb,yy,ee)
        agg.update({'fold_local_n':int(len(x)),'bridge_box_depth':float(bb[-1]),
                    'delta_bic_smooth_bridge_minus_box':float(bic(rs,len(x),Xs.shape[1])-bic(rb,len(x),Xb.shape[1]))})
    else:
        agg.update({'fold_local_n':int(len(all_y)),'bridge_box_depth':None,'delta_bic_smooth_bridge_minus_box':None})
    return {'events':ev,'aggregate':agg}


def run_one(n,role):
    url=f'{ROOT}/{n}.lc'; r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage4-consumed-dev/1.0'}); r.raise_for_status()
    a=np.loadtxt(r.content.splitlines()); t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    b,_=s0.scan_bls(t,y-np.median(y),dy)
    bridge=local_bridge(t,y,dy,b)
    return {'number':n,'role':role,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()),'bls':b,'local_bridge':bridge}


def main():
    rows=[]
    for n in POSITIVES: rows.append(run_one(n,'development_positive'))
    for n in NEGATIVES: rows.append(run_one(n,'development_negative_stage3_hardpass'))
    rep={'role':'Stage-4 consumed-data-only diagnostic; fresh validation binaries remain sealed',
         'fresh_validation_values_opened':False,'parameters':{'shoulder_inner_duration':SHOULDER_INNER,'shoulder_outer_duration':SHOULDER_OUTER,
         'smooth_bridge_polynomial_degree':4},'rows':rows}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact=[]
    for z in rows:
        a=z['local_bridge']['aggregate']; compact.append({'number':z['number'],'role':z['role'],'bls_period_h':z['bls']['period_d']*24,
          'bls_duration_h':z['bls']['duration_d']*24,'bls_snr':z['bls']['depth_snr'],**a})
    print(json.dumps(compact,indent=2,allow_nan=False))

if __name__=='__main__': main()
