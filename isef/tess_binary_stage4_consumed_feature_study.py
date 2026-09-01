#!/usr/bin/env python3
"""Stage-4 morphology study on ONLY already-consumed historical light curves.

Development labels/data allowed here:
  positives: 6764, 1803
  negatives/diagnostics: exact 128 Stage-3 historical controls

No fresh benchmark light curve and no Year-8 light curve is requested.  This is
feature discovery, not a frozen detector.  It characterizes why Stage-3's box
model confuses rotational minima with mutual events.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np, requests
import tess_binary_stage0_detector as s0
import tess_binary_stage3_frozen as s3

ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
CONTROL=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
OUT=Path('results/tess_binary_stage4_consumed_features')
SHARDS=8
POSITIVES={6764:'development_positive',1803:'consumed_validation_positive'}


def robust_sigma(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if len(x)<2:return math.nan
    med=np.median(x);s=1.4826*np.median(np.abs(x-med))
    return float(s if s>0 else np.std(x))


def phase(t,t0,P):return ((t-t0+0.5*P)%P)-0.5*P


def fetch(number):
    u=f'{ROOT}/{number}.lc';r=requests.get(u,timeout=120,headers={'User-Agent':'ISEF-stage4-consumed-diagnostic/1.0'});r.raise_for_status()
    a=np.loadtxt(r.content.splitlines());return a


def fixed_box_bic(t,y,dy,b):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time'];ph=phase(t,t0,P);box=(np.abs(ph)<=dur/2).astype(float)
    X0=np.ones((len(t),1));Xb=np.column_stack([np.ones(len(t)),box])
    _,r0=s3.fit(X0,y,dy);bb,rb=s3.fit(Xb,y,dy);n=len(t)
    return {'n':int(n),'depth':float(bb[-1]),'dbic_noevent':float(s3.bic(r0,n,1)-s3.bic(rb,n,2))}


def local_morphology(t,y,b):
    P=float(b['period_d']);dur=float(b['duration_d']);t0=float(b['transit_time']);ph=phase(t,t0,P);q=np.abs(ph)/dur
    center=y[q<=0.5];inner=y[(q>=0.75)&(q<=1.5)];outer=y[(q>1.5)&(q<=3.0)]
    shoulder=np.concatenate([inner,outer]) if len(inner)+len(outer) else np.array([])
    sig=robust_sigma(outer if len(outer)>=20 else y)
    pooled=float(np.median(center)-np.median(shoulder)) if len(center) and len(shoulder) else math.nan
    inner_c=float(np.median(center)-np.median(inner)) if len(center) and len(inner) else math.nan
    outer_c=float(np.median(center)-np.median(outer)) if len(center) and len(outer) else math.nan
    # Per-cycle local contrasts; geometry fixed by full-data BLS candidate.
    k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1;events=[]
    for k in range(k0,k1+1):
        c=t0+k*P;d=np.abs(t-c)/dur
        cm=y[d<=0.5];sh=y[(d>=0.75)&(d<=2.0)]
        if len(cm)>=2 and len(sh)>=4:events.append(float(np.median(cm)-np.median(sh)))
    ev=np.asarray(events,float)
    return {'center_n':int(len(center)),'inner_shoulder_n':int(len(inner)),'outer_shoulder_n':int(len(outer)),
            'pooled_center_minus_shoulders':pooled,'center_minus_inner_shoulder':inner_c,'center_minus_outer_shoulder':outer_c,
            'pooled_sharpness_snr':float(pooled/sig) if np.isfinite(pooled) and np.isfinite(sig) and sig>0 else math.nan,
            'event_local_contrasts':events,'event_local_contrast_n':int(len(events)),
            'event_local_contrast_median':float(np.median(ev)) if len(ev) else math.nan,
            'event_positive_fraction':float(np.mean(ev>0)) if len(ev) else math.nan,
            'event_gt_1sigma_fraction':float(np.mean(ev>sig)) if len(ev) and np.isfinite(sig) and sig>0 else math.nan,
            'reference_sigma':sig}


def parity_morphology(t,y,b):
    P=float(b['period_d']);dur=float(b['duration_d']);t0=float(b['transit_time']);k=np.rint((t-t0)/P).astype(int)
    out={}
    for parity in (0,1):
        keep=(np.mod(k,2)==parity);ph=phase(t[keep],t0,P);q=np.abs(ph)/dur;yy=y[keep]
        c=yy[q<=0.5];sh=yy[(q>=0.75)&(q<=2.0)]
        out[str(parity)]={'center_n':int(len(c)),'shoulder_n':int(len(sh)),
          'contrast':float(np.median(c)-np.median(sh)) if len(c) and len(sh) else math.nan}
    vals=[out[str(p)]['contrast'] for p in (0,1)]
    finite=[v for v in vals if np.isfinite(v)]
    out['both_positive']=bool(len(finite)==2 and all(v>0 for v in finite))
    out['min_contrast']=float(min(finite)) if finite else math.nan
    out['max_contrast']=float(max(finite)) if finite else math.nan
    return out


def smooth_complexity(t,y,dy,d):
    c=d['chosen_hypothesis'];Porb=float(c['physical_period_d']);rot=float(d['rotation_period_h_alias'])/24;tref=float(np.median(t))
    Xr=s3.fourier_design(t,rot,tref,s3.ROT_HARMONICS,linear=True)
    # Rebuild exact chosen compact boxes.
    Pe=float(d['bls']['period_d']);t0=float(d['bls']['transit_time']);dur=float(d['bls']['duration_d']);mult=int(c['orbit_multiplier'])
    if mult==1:boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float)]
    else:boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float),(np.abs(phase(t,t0+Pe,Porb))<=dur/2).astype(float)]
    Xb=np.column_stack([Xr,*boxes]);_,rb=s3.fit(Xb,y,dy);n=len(t);bicb=s3.bic(rb,n,Xb.shape[1])
    out={}
    for h in (4,8,12,16):
        Xe=s3.fourier_design(t,Porb,tref,h,linear=False)[:,1:];Xs=np.column_stack([Xr,Xe]);_,rs=s3.fit(Xs,y,dy)
        out[str(h)]={'delta_bic_smooth_minus_binary':float(s3.bic(rs,n,Xs.shape[1])-bicb),'smooth_added_parameters':int(Xe.shape[1])}
    return out


def analyze(number,label):
    try:
        a=fetch(number);t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int));d=s3.detect(t,y,dy,None)
        if not d.get('eligible'):return {'number':number,'label':label,'ok':True,'eligible':False,'detector':d}
        b=d['bls'];mid=float(np.median(t));ea=t<=mid;la=t>mid
        rep={'number':number,'label':label,'ok':True,'eligible':True,'n_good':len(t),'baseline_d':float(t.max()-t.min()),
             'stage3_hard_pass':bool(d['hard_pass']),'stage3':d,
             'local':local_morphology(t,y,b),'parity':parity_morphology(t,y,b),
             'split_fixed_ephemeris':{'early':fixed_box_bic(t[ea],y[ea],dy[ea],b),'late':fixed_box_bic(t[la],y[la],dy[la],b)},
             'smooth_complexity':smooth_complexity(t,y,dy,d)}
        print(number,label,d['hard_pass'],rep['local']['pooled_sharpness_snr'],rep['local']['event_positive_fraction'],rep['smooth_complexity']['12']['delta_bic_smooth_minus_binary'],flush=True)
        return rep
    except Exception as e:return {'number':number,'label':label,'ok':False,'error':f'{type(e).__name__}: {e}'[:1000]}


def shard(i):
    OUT.mkdir(parents=True,exist_ok=True);controls=[int(x) for x in CONTROL.read_text().split()]
    nums=[n for j,n in enumerate(controls) if j%SHARDS==i]
    # Put consumed positives in shard 0 only.
    tasks=[(n,'control') for n in nums]+([(n,l) for n,l in POSITIVES.items()] if i==0 else [])
    results=[analyze(n,l) for n,l in tasks]
    p=OUT/f'shard-{i}';p.mkdir(parents=True,exist_ok=True);(p/'report.json').write_text(json.dumps({'shard':i,'results':results},indent=2,sort_keys=True,allow_nan=False)+'\n')


def aggregate():
    rows=[]
    for i in range(SHARDS):rows.extend(json.loads((OUT/f'shard-{i}'/'report.json').read_text())['results'])
    good=[z for z in rows if z.get('eligible')];pos=[z for z in good if z['label']!='control'];ctl=[z for z in good if z['label']=='control']
    def vals(group,path):
        out=[]
        for z in group:
            q=z
            for k in path:q=q[k]
            if isinstance(q,(int,float)) and np.isfinite(q):out.append(float(q))
        return out
    paths={
      'sharpness_snr':['local','pooled_sharpness_snr'],
      'event_positive_fraction':['local','event_positive_fraction'],
      'event_gt_1sigma_fraction':['local','event_gt_1sigma_fraction'],
      'parity_min_contrast':['parity','min_contrast'],
      'early_dbic':['split_fixed_ephemeris','early','dbic_noevent'],
      'late_dbic':['split_fixed_ephemeris','late','dbic_noevent'],
      'dbic_smooth4':['smooth_complexity','4','delta_bic_smooth_minus_binary'],
      'dbic_smooth8':['smooth_complexity','8','delta_bic_smooth_minus_binary'],
      'dbic_smooth12':['smooth_complexity','12','delta_bic_smooth_minus_binary'],
      'dbic_smooth16':['smooth_complexity','16','delta_bic_smooth_minus_binary']}
    summary={}
    for name,path in paths.items():
        pv=vals(pos,path);cv=vals(ctl,path)
        summary[name]={'positive_values':pv,'control_n':len(cv),'control_quantiles':{str(q):float(np.quantile(cv,q)) for q in (0,0.1,0.25,0.5,0.75,0.9,0.95,0.98,1)} if cv else {}}
    hard=[z for z in ctl if z.get('stage3_hard_pass')]
    rep={'role':'development-only morphology diagnostics on consumed Stage-3 data','fresh_lightcurves_opened':False,'year8_values_opened':False,
         'eligible_positive_n':len(pos),'eligible_control_n':len(ctl),'stage3_hard_control_n':len(hard),'summary':summary,
         'positive_details':pos,'stage3_hard_control_details':hard}
    (OUT/'aggregate.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'eligible_positive_n':len(pos),'eligible_control_n':len(ctl),'stage3_hard_control_n':len(hard),'summary':summary},indent=2,allow_nan=False))


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True);q=sp.add_parser('shard');q.add_argument('index',type=int);sp.add_parser('aggregate');a=ap.parse_args()
    if a.mode=='shard':shard(a.index)
    else:aggregate()

if __name__=='__main__':main()
