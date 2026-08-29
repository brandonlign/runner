#!/usr/bin/env python3
"""Field-1-only v2 coherent two-epoch image-level injection calibration.

Measures completeness/eligibility versus brightness and local crowding for the
coherent pair statistic. Uses the frozen five development patches and the
unchanged morphology+FLAG+common-mode measurement layer. Two adjacent epochs
receive the same-sign PSF-shaped signal. No Field 2-9 science pixels are read.
"""
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_v2_stratified_pair_injection.json');OUT.parent.mkdir(parents=True,exist_ok=True)
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
AMPS=(.15,.20,.30,.50);PAIRS=((2,3),(6,7),(10,11));SIGNS=(1,-1)

def pair_stat(vals,ok):
 best=0.
 for e in range(15):
  if ok[e] and ok[e+1] and vals[e]*vals[e+1]>0:best=max(best,min(abs(vals[e]),abs(vals[e+1])))
 return float(best)
def raw_neighbors(cube,hs,orig,ra,de):
 _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
 if tab is None:return np.full(len(ra),np.nan)
 x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);px,py=hs[0].w.world_to_pixel_values(ra,de);px=np.asarray(px)-orig[0][0];py=np.asarray(py)-orig[0][1];out=[]
 for a,b in zip(px,py):
  d=np.hypot(x-a,y-b);j=int(np.argmin(d));d[j]=np.inf;out.append(float(np.min(d)) if len(d)>1 else np.nan)
 return np.asarray(out)
def analyze_patch(idx,spec):
 cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta];ra,de,peak=pd.sources(cube,hs,orig);crowd=raw_neighbors(cube,hs,orig,ra,de);rows=[];need_flags={}
 for j,(r,d) in enumerate(zip(ra,de)):
  cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
  if any(x is None for x in cuts.values()):continue
  refs={};basef=[];basem=[]
  for e in range(16):
   peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);refs[e]=ref;f,s,c=pd.scale_metric(cuts[e],ref);basef.append(float(f));basem.append(bool(pd.morph_ok(s,c,MORPH)))
  rows.append({'patch':idx,'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'neighbor_px':float(crowd[j]),'cuts':cuts,'refs':refs,'basef':basef,'basem':basem,'hs':hs})
  for e in set(x for p in PAIRS for x in p):need_flags[(j,e)]=(hs[e],e,float(r),float(d))
 flag={}
 with ThreadPoolExecutor(max_workers=32) as ex:
  fs={ex.submit(fg.flag_artifact,*v):k for k,v in need_flags.items()}
  for fut in as_completed(fs):
   try:flag[fs[fut]]=bool(fut.result()[0])
   except Exception:flag[fs[fut]]=True
 # Baseline common mode uses unchanged full rule; only >5% morphology-clean baseline positions require FLG reads.
 checks=[]
 for z in rows:
  for e,(f,m) in enumerate(zip(z['basef'],z['basem'])):
   if m and abs(f)>fg.CHECK_FLOOR and (z['star'],e) not in flag:checks.append((z,e))
 with ThreadPoolExecutor(max_workers=32) as ex:
  fs={ex.submit(fg.flag_artifact,z['hs'][e],e,z['ra'],z['dec']):(z['star'],e) for z,e in checks}
  for fut in as_completed(fs):
   try:flag[fs[fut]]=bool(fut.result()[0])
   except Exception:flag[fs[fut]]=True
 common=[]
 for e in range(16):
  vals=[]
  for z in rows:
   f=z['basef'][e];m=z['basem'][e];art=flag.get((z['star'],e),False) if abs(f)>fg.CHECK_FLOOR else False
   if m and not art:vals.append(f)
  common.append(float(np.median(vals)) if vals else 0.)
 trials=[]
 for z in rows:
  bvals=np.array([fg.common_correct(f,common[e]) for e,f in enumerate(z['basef'])],float);bok=np.array([m and not (flag.get((z['star'],e),False) if abs(z['basef'][e])>fg.CHECK_FLOOR else False) for e,m in enumerate(z['basem'])],bool)
  if int(bok.sum())<pd.MIN_ACCEPTED:continue
  for amp in AMPS:
   for sign in SIGNS:
    for e0,e1 in PAIRS:
     vals=bvals.copy();ok=bok.copy()
     for e in (e0,e1):
      ref=z['refs'][e];yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor;event=z['cuts'][e]+sign*amp*tmpl;f,s,c=pd.scale_metric(event,ref);vals[e]=fg.common_correct(f,common[e]);ok[e]=bool(pd.morph_ok(s,c,MORPH) and not flag.get((z['star'],e),True))
     trials.append({'patch':idx,'star':z['star'],'peak':z['peak'],'neighbor_px':z['neighbor_px'],'amplitude':amp,'sign':'bright' if sign>0 else 'dim','pair':[e0,e1],'accepted_epochs':int(ok.sum()),'injected_pair_accepted':bool(ok[e0] and ok[e1]),'pair_stat':pair_stat(vals,ok)})
 return trials

def bin_summary(trials,key,edges,label):
 out=[]
 for lo,hi in zip(edges[:-1],edges[1:]):
  z=[x for x in trials if lo<=x[key]<=hi] if hi==edges[-1] else [x for x in trials if lo<=x[key]<hi]
  out.append({'bin':label(lo,hi),'n':len(z),'pair_eligibility':float(np.mean([x['injected_pair_accepted'] for x in z])) if z else None,'median_pair_stat':float(np.median([x['pair_stat'] for x in z])) if z else None})
 return out
def main():
 gm=er.map_groups();sel,_=mp.select_safe(gm);trials=[];fail=[]
 for i,s in enumerate(sel):
  try:trials.extend(analyze_patch(i,s))
  except Exception as e:fail.append({'patch':i,'error':f'{type(e).__name__}: {e}'})
 peaks=np.array([x['peak'] for x in trials]);nei=np.array([x['neighbor_px'] for x in trials]);pq=np.unique(np.quantile(peaks,[0,.33,.67,1]));nq=np.unique(np.quantile(nei[np.isfinite(nei)],[0,.33,.67,1]));byamp={}
 for a in AMPS:
  z=[x for x in trials if x['amplitude']==a];byamp[str(a)]={'trials':len(z),'pair_eligibility':float(np.mean([x['injected_pair_accepted'] for x in z])) if z else None,'pair_stat_summary':pd.summary([x['pair_stat'] for x in z]),'brightness_terciles':bin_summary(z,'peak',pq,lambda l,h:f'{l:.6g}..{h:.6g}') if len(pq)>1 else [],'crowding_terciles_neighbor_px':bin_summary(z,'neighbor_px',nq,lambda l,h:f'{l:.2f}..{h:.2f}') if len(nq)>1 else []}
 out={'success':len(trials)>0 and not fail,'note':'Field-1 five-patch image-level coherent two-epoch injections; brightness proxy is epoch-0 DAO peak; crowding proxy is nearest detected neighbor in pixels','analysis_failures':fail,'amplitudes':byamp,'total_trials':len(trials),'trial_rows':trials};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='trial_rows'},indent=2,sort_keys=True))
if __name__=='__main__':main()
