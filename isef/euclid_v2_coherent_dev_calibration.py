#!/usr/bin/env python3
"""Euclid Q2 v2 coherent-event development calibration on frozen Field 1 only.

Applies the unchanged Stage-0B morphology+FLAG+common-mode measurement layer to
the same five development patches. Defines an interpretable coherent-event score:
for adjacent chronological accepted epochs with the same sign, score the smaller
absolute corrected excursion; the source statistic is the maximum such pair.

For a scalable survey-level null, create deterministic *decoy* light curves by
permuting complete (fraction, accepted) measurements only within each of the four
same-dither groups (epoch mod 4). This preserves source-specific amplitudes,
quality losses and dither distributions while breaking chronological coherence.
No Field 2-9 science pixels are touched.
"""
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_v2_coherent_dev_calibration.json');OUT.parent.mkdir(parents=True,exist_ok=True)
RNG=np.random.default_rng(20260829);NDECOY=500
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
GRID=np.round(np.arange(.05,.501,.01),2)

def pair_stat(vals,ok):
 best=0.0;where=None
 for e in range(15):
  if ok[e] and ok[e+1] and vals[e]*vals[e+1]>0:
   s=min(abs(vals[e]),abs(vals[e+1]))
   if s>best:best=float(s);where=(e,e+1)
 return best,where
def triplet_stat(vals,ok):
 best=0.0;where=None
 for e in range(14):
  if ok[e] and ok[e+1] and ok[e+2] and ((vals[e]>0 and vals[e+1]>0 and vals[e+2]>0) or (vals[e]<0 and vals[e+1]<0 and vals[e+2]<0)):
   s=min(abs(vals[e]),abs(vals[e+1]),abs(vals[e+2]))
   if s>best:best=float(s);where=(e,e+1,e+2)
 return best,where
def permute_within_dither(vals,ok,rng):
 v=np.array(vals,float).copy();q=np.array(ok,bool).copy()
 for g in range(4):
  ix=np.arange(g,16,4);p=rng.permutation(ix);v[ix]=v[p];q[ix]=q[p]
 return v,q

def patch_sequences(idx,spec):
 cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta];ra,de,peak=pd.sources(cube,hs,orig);src=[];checks=[]
 for j,(r,d) in enumerate(zip(ra,de)):
  cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
  if any(x is None for x in cuts.values()):continue
  mm=[]
  for e in range(16):
   peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);m=pd.morph_ok(s,c,MORPH);row={'epoch':e,'fraction':float(f),'morph':bool(m),'artifact':False};mm.append(row)
   if m and abs(f)>fg.CHECK_FLOOR:checks.append((row,hs[e],e,float(r),float(d)))
  src.append({'patch':idx,'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'mm':mm})
 with ThreadPoolExecutor(max_workers=32) as ex:
  fs={ex.submit(fg.flag_artifact,h,e,r,d):row for row,h,e,r,d in checks}
  for fut in as_completed(fs):
   row=fs[fut]
   try:row['artifact']=bool(fut.result()[0])
   except Exception:row['artifact']=True
 common=[]
 for e in range(16):
  z=[s['mm'][e]['fraction'] for s in src if s['mm'][e]['morph'] and not s['mm'][e]['artifact']];common.append(float(np.median(z)) if z else 0.)
 out=[]
 for s in src:
  vals=[];ok=[]
  for e,row in enumerate(s['mm']):
   vals.append(float(fg.common_correct(row['fraction'],common[e])));ok.append(bool(row['morph'] and not row['artifact']))
  if sum(ok)<pd.MIN_ACCEPTED:continue
  ps,pw=pair_stat(vals,ok);ts,tw=triplet_stat(vals,ok)
  out.append({'patch':idx,'star':s['star'],'ra':s['ra'],'dec':s['dec'],'peak':s['peak'],'accepted_epochs':int(sum(ok)),'corrected_fraction':vals,'accepted':ok,'pair_stat':ps,'pair_epochs':pw,'triplet_stat':ts,'triplet_epochs':tw})
 return out

def main():
 gm=er.map_groups();selected,rejected=mp.select_safe(gm);stars=[];fail=[]
 for i,spec in enumerate(selected):
  try:stars.extend(patch_sequences(i,spec))
  except Exception as e:fail.append({'patch':i,'error':f'{type(e).__name__}: {e}'})
 real_pair=np.array([s['pair_stat'] for s in stars]);real_tri=np.array([s['triplet_stat'] for s in stars]);dec_pair=[];dec_tri=[]
 for s in stars:
  for _ in range(NDECOY):
   v,q=permute_within_dither(s['corrected_fraction'],s['accepted'],RNG);dec_pair.append(pair_stat(v,q)[0]);dec_tri.append(triplet_stat(v,q)[0])
 dec_pair=np.asarray(dec_pair);dec_tri=np.asarray(dec_tri);rows=[]
 for t in GRID:
  rp=int(np.sum(real_pair>=t));dp=int(np.sum(dec_pair>=t));rt=int(np.sum(real_tri>=t));dt=int(np.sum(dec_tri>=t));
  rows.append({'threshold':float(t),'real_pair_sources':rp,'decoy_pair_exceedances':dp,'expected_false_pair':float(dp/NDECOY),'estimated_pair_fdr':float(min(1,(dp/NDECOY)/rp)) if rp else None,'real_triplet_sources':rt,'decoy_triplet_exceedances':dt,'expected_false_triplet':float(dt/NDECOY),'estimated_triplet_fdr':float(min(1,(dt/NDECOY)/rt)) if rt else None})
 # Development recommendation is diagnostic only: smallest grid threshold with >=1 real and target-decoy FDR<=1%.
 elig=[r for r in rows if r['real_pair_sources']>0 and r['estimated_pair_fdr'] is not None and r['estimated_pair_fdr']<=.01]
 rec=min(elig,key=lambda r:r['threshold']) if elig else None
 out={'success':len(stars)>=100 and not fail,'note':'Field-1-only development calibration; target-decoy within-dither permutations preserve source/dither distributions and break chronological coherence','five_patch_selected':len(selected),'analysis_failures':fail,'valid_sources':len(stars),'decoys_per_source':NDECOY,'real_pair_summary':pd.summary(real_pair),'real_triplet_summary':pd.summary(real_tri),'decoy_pair_summary':pd.summary(dec_pair),'decoy_triplet_summary':pd.summary(dec_tri),'threshold_grid':rows,'development_pair_recommendation':rec,'top_pair_sources':sorted(stars,key=lambda x:x['pair_stat'],reverse=True)[:20]};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
