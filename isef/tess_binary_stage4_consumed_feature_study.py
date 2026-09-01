#!/usr/bin/env python3
"""Stage-4 morphology study on ONLY already-consumed historical light curves.

Development labels/data allowed here: positives 6764 and 1803; diagnostics are
the exact 128 Stage-3 historical controls. No fresh benchmark or Year-8 light
curve is requested. This is feature discovery, not a frozen detector.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np,requests
import tess_binary_stage0_detector as s0
import tess_binary_stage3_frozen as s3
ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
CONTROL=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
OUT=Path('results/tess_binary_stage4_consumed_features');SHARDS=8
POSITIVES={6764:'development_positive',1803:'consumed_validation_positive'}

def sanitize(x):
    if isinstance(x,dict):return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)):return bool(x)
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x);return v if math.isfinite(v) else None
    return x

def rsig(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if len(x)<2:return math.nan
    m=np.median(x);s=1.4826*np.median(np.abs(x-m));return float(s if s>0 else np.std(x))
def phase(t,t0,P):return ((t-t0+0.5*P)%P)-0.5*P
def fetch(n):
    r=requests.get(f'{ROOT}/{n}.lc',timeout=120,headers={'User-Agent':'ISEF-stage4-consumed-diagnostic/1.1'});r.raise_for_status();return np.loadtxt(r.content.splitlines())
def fixed_box(t,y,dy,b):
    ph=phase(t,b['transit_time'],b['period_d']);box=(np.abs(ph)<=b['duration_d']/2).astype(float);X0=np.ones((len(t),1));Xb=np.column_stack([np.ones(len(t)),box]);_,r0=s3.fit(X0,y,dy);bb,rb=s3.fit(Xb,y,dy);n=len(t)
    return {'n':int(n),'depth':float(bb[-1]),'dbic_noevent':float(s3.bic(r0,n,1)-s3.bic(rb,n,2))}
def local(t,y,b):
    P=float(b['period_d']);dur=float(b['duration_d']);t0=float(b['transit_time']);q=np.abs(phase(t,t0,P))/dur
    c=y[q<=.5];inn=y[(q>=.75)&(q<=1.5)];out=y[(q>1.5)&(q<=3)];sh=np.concatenate([inn,out]) if len(inn)+len(out) else np.array([]);sig=rsig(out if len(out)>=20 else y)
    pooled=float(np.median(c)-np.median(sh)) if len(c) and len(sh) else math.nan
    events=[];k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1
    for k in range(k0,k1+1):
        d=np.abs(t-(t0+k*P))/dur;cm=y[d<=.5];ss=y[(d>=.75)&(d<=2)]
        if len(cm)>=2 and len(ss)>=4:events.append(float(np.median(cm)-np.median(ss)))
    ev=np.asarray(events,float)
    return {'center_n':len(c),'inner_shoulder_n':len(inn),'outer_shoulder_n':len(out),'pooled_center_minus_shoulders':pooled,
      'center_minus_inner_shoulder':float(np.median(c)-np.median(inn)) if len(c) and len(inn) else math.nan,
      'center_minus_outer_shoulder':float(np.median(c)-np.median(out)) if len(c) and len(out) else math.nan,
      'pooled_sharpness_snr':float(pooled/sig) if np.isfinite(pooled) and np.isfinite(sig) and sig>0 else math.nan,
      'event_local_contrasts':events,'event_local_contrast_n':len(events),'event_local_contrast_median':float(np.median(ev)) if len(ev) else math.nan,
      'event_positive_fraction':float(np.mean(ev>0)) if len(ev) else math.nan,'event_gt_1sigma_fraction':float(np.mean(ev>sig)) if len(ev) and np.isfinite(sig) and sig>0 else math.nan,'reference_sigma':sig}
def parity(t,y,b):
    P=float(b['period_d']);dur=float(b['duration_d']);t0=float(b['transit_time']);k=np.rint((t-t0)/P).astype(int);o={}
    for p in (0,1):
        keep=np.mod(k,2)==p;q=np.abs(phase(t[keep],t0,P))/dur;yy=y[keep];c=yy[q<=.5];sh=yy[(q>=.75)&(q<=2)];o[str(p)]={'center_n':len(c),'shoulder_n':len(sh),'contrast':float(np.median(c)-np.median(sh)) if len(c) and len(sh) else math.nan}
    v=[o[str(p)]['contrast'] for p in (0,1)];f=[x for x in v if np.isfinite(x)];o['both_positive']=bool(len(f)==2 and all(x>0 for x in f));o['min_contrast']=min(f) if f else math.nan;o['max_contrast']=max(f) if f else math.nan;return o
def smooth_complexity(t,y,dy,d):
    c=d['chosen_hypothesis'];Porb=float(c['physical_period_d']);rot=float(d['rotation_period_h_alias'])/24;tref=float(np.median(t));Xr=s3.fourier_design(t,rot,tref,s3.ROT_HARMONICS,linear=True);Pe=float(d['bls']['period_d']);t0=float(d['bls']['transit_time']);dur=float(d['bls']['duration_d']);mult=int(c['orbit_multiplier'])
    boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float)] if mult==1 else [(np.abs(phase(t,t0,Porb))<=dur/2).astype(float),(np.abs(phase(t,t0+Pe,Porb))<=dur/2).astype(float)]
    Xb=np.column_stack([Xr,*boxes]);_,rb=s3.fit(Xb,y,dy);n=len(t);bb=s3.bic(rb,n,Xb.shape[1]);o={}
    for h in (4,8,12,16):
        Xe=s3.fourier_design(t,Porb,tref,h,linear=False)[:,1:];Xs=np.column_stack([Xr,Xe]);_,rr=s3.fit(Xs,y,dy);o[str(h)]={'delta_bic_smooth_minus_binary':float(s3.bic(rr,n,Xs.shape[1])-bb),'smooth_added_parameters':Xe.shape[1]}
    return o
def analyze(n,label):
    try:
        a=fetch(n);t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int));d=s3.detect(t,y,dy,None)
        if not d.get('eligible'):return {'number':n,'label':label,'ok':True,'eligible':False,'stage3':d}
        b=d['bls'];mid=float(np.median(t));e=t<=mid;l=t>mid
        z={'number':n,'label':label,'ok':True,'eligible':True,'n_good':len(t),'baseline_d':float(t.max()-t.min()),'stage3_hard_pass':bool(d['hard_pass']),'stage3':d,'local':local(t,y,b),'parity':parity(t,y,b),'split_fixed_ephemeris':{'early':fixed_box(t[e],y[e],dy[e],b),'late':fixed_box(t[l],y[l],dy[l],b)},'smooth_complexity':smooth_complexity(t,y,dy,d)}
        print(n,label,d['hard_pass'],z['local']['pooled_sharpness_snr'],z['local']['event_positive_fraction'],z['smooth_complexity']['12']['delta_bic_smooth_minus_binary'],flush=True);return z
    except Exception as e:return {'number':n,'label':label,'ok':False,'error':f'{type(e).__name__}: {e}'[:1000]}
def shard(i):
    OUT.mkdir(parents=True,exist_ok=True);ctl=[int(x) for x in CONTROL.read_text().split()];tasks=[(n,'control') for j,n in enumerate(ctl) if j%SHARDS==i]+([(n,l) for n,l in POSITIVES.items()] if i==0 else []);r=[analyze(n,l) for n,l in tasks];p=OUT/f'shard-{i}';p.mkdir(parents=True,exist_ok=True);(p/'report.json').write_text(json.dumps(sanitize({'shard':i,'results':r}),indent=2,sort_keys=True,allow_nan=False)+'\n')
def aggregate():
    rows=[]
    for i in range(SHARDS):rows+=json.loads((OUT/f'shard-{i}'/'report.json').read_text())['results']
    good=[z for z in rows if z.get('eligible')];pos=[z for z in good if z['label']!='control'];ctl=[z for z in good if z['label']=='control']
    paths={'sharpness_snr':['local','pooled_sharpness_snr'],'event_positive_fraction':['local','event_positive_fraction'],'event_gt_1sigma_fraction':['local','event_gt_1sigma_fraction'],'parity_min_contrast':['parity','min_contrast'],'early_dbic':['split_fixed_ephemeris','early','dbic_noevent'],'late_dbic':['split_fixed_ephemeris','late','dbic_noevent'],'dbic_smooth4':['smooth_complexity','4','delta_bic_smooth_minus_binary'],'dbic_smooth8':['smooth_complexity','8','delta_bic_smooth_minus_binary'],'dbic_smooth12':['smooth_complexity','12','delta_bic_smooth_minus_binary'],'dbic_smooth16':['smooth_complexity','16','delta_bic_smooth_minus_binary']}
    def values(g,path):
        o=[]
        for z in g:
            q=z
            for k in path:q=q.get(k) if isinstance(q,dict) else None
            if isinstance(q,(int,float)) and q is not None and np.isfinite(q):o.append(float(q))
        return o
    sm={}
    for name,path in paths.items():
        pv=values(pos,path);cv=values(ctl,path);sm[name]={'positive_values':pv,'control_n':len(cv),'control_quantiles':{str(q):float(np.quantile(cv,q)) for q in (0,.1,.25,.5,.75,.9,.95,.98,1)} if cv else {}}
    hard=[z for z in ctl if z.get('stage3_hard_pass')];rep={'role':'development-only morphology diagnostics on consumed Stage-3 data','fresh_lightcurves_opened':False,'year8_values_opened':False,'eligible_positive_n':len(pos),'eligible_control_n':len(ctl),'stage3_hard_control_n':len(hard),'summary':sm,'positive_details':pos,'stage3_hard_control_details':hard};(OUT/'aggregate.json').write_text(json.dumps(sanitize(rep),indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(sanitize({'eligible_positive_n':len(pos),'eligible_control_n':len(ctl),'stage3_hard_control_n':len(hard),'summary':sm}),indent=2,allow_nan=False))
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True);q=sp.add_parser('shard');q.add_argument('index',type=int);sp.add_parser('aggregate');a=ap.parse_args();shard(a.index) if a.mode=='shard' else aggregate()
if __name__=='__main__':main()
