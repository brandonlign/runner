#!/usr/bin/env python3
"""One-shot Euclid Q2 v2 Field-2 validation under preregistration b8ae629c.

This is the first v2 analysis that reads Field-2 science pixels. Field 2 is
validation-only and cannot yield a discovery. The five centers, detector, 0.24
coherent-pair floor, 200-decoy rule, and 30% injection pass criteria were frozen
in brandonlign/isef commit b8ae629c34d13ac50f4a7f320f881699260b4959.
"""
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import euclid_field_runtime as fr
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_v2_field2_validation.json');OUT.parent.mkdir(parents=True,exist_ok=True)
FIELD=2;FLOOR=.24;NDECOY=200;SEED=20260829+FIELD;AMP=.30
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
CENTERS=[
 (267.498311894885,-29.259),(267.38368810511497,-29.259),(267.441,-29.159),
 (267.441,-29.359),(267.61293568465504,-29.309),
]
INJ_PAIRS=((2,3),(6,7),(10,11));SIGNS=(1,-1)

def pair_stat(vals,ok):
 best=0.
 for e in range(15):
  if ok[e] and ok[e+1] and vals[e]*vals[e+1]>0:best=max(best,min(abs(vals[e]),abs(vals[e+1])))
 return float(best)
def permute(vals,ok,rng):
 v=np.asarray(vals,float).copy();q=np.asarray(ok,bool).copy()
 for g in range(4):
  ix=np.arange(g,16,4);p=rng.permutation(ix);v[ix]=v[p];q[ix]=q[p]
 return v,q

def patch(idx,target,gm):
 routes,diag=er.route_target(gm,target);spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
 cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta];ra,de,peak=pd.sources(cube,hs,orig);src=[];flag_requests={}
 for j,(r,d) in enumerate(zip(ra,de)):
  cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
  if any(x is None for x in cuts.values()):continue
  refs={};mm=[]
  for e in range(16):
   peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);refs[e]=ref;f,s,c=pd.scale_metric(cuts[e],ref);m=bool(pd.morph_ok(s,c,MORPH));mm.append({'f':float(f),'morph':m,'artifact':False})
   if m and (abs(f)>fg.CHECK_FLOOR or e in {2,3,6,7,10,11}):flag_requests[(j,e)]=(hs[e],e,float(r),float(d))
  src.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'cuts':cuts,'refs':refs,'mm':mm})
 flag={}
 with ThreadPoolExecutor(max_workers=32) as ex:
  fs={ex.submit(fg.flag_artifact,*args):key for key,args in flag_requests.items()}
  for fut in as_completed(fs):
   key=fs[fut]
   try:flag[key]=bool(fut.result()[0])
   except Exception:flag[key]=True
 for z in src:
  for e,row in enumerate(z['mm']):row['artifact']=bool(flag.get((z['star'],e),False)) if (abs(row['f'])>fg.CHECK_FLOOR or e in {2,3,6,7,10,11}) else False
 common=[]
 for e in range(16):
  vals=[z['mm'][e]['f'] for z in src if z['mm'][e]['morph'] and not z['mm'][e]['artifact']];common.append(float(np.median(vals)) if vals else 0.)
 valid=[];trials=[]
 for z in src:
  vals=np.array([fg.common_correct(row['f'],common[e]) for e,row in enumerate(z['mm'])],float);ok=np.array([row['morph'] and not row['artifact'] for row in z['mm']],bool)
  if int(ok.sum())<pd.MIN_ACCEPTED:continue
  valid.append({'ra':z['ra'],'dec':z['dec'],'peak':z['peak'],'vals':vals.tolist(),'ok':ok.tolist(),'pair_stat':pair_stat(vals,ok)})
  for sign in SIGNS:
   for e0,e1 in INJ_PAIRS:
    iv=vals.copy();iq=ok.copy()
    for e in (e0,e1):
     ref=z['refs'][e];yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor;event=z['cuts'][e]+sign*AMP*tmpl;f,s,c=pd.scale_metric(event,ref);iv[e]=fg.common_correct(f,common[e]);iq[e]=bool(pd.morph_ok(s,c,MORPH) and not flag.get((z['star'],e),True))
    trials.append({'eligible':bool(iq[e0] and iq[e1]),'recovered':bool(pair_stat(iv,iq)>=FLOOR)})
 return {'patch':idx,'target':list(target),'routes':{str(k):int(v) for k,v in routes.items()},'detected_sources':len(ra),'valid_sources':len(valid),'common_mode':common},valid,trials

def main():
 fr.activate_field(FIELD);gm=er.map_groups();patches=[];stars=[];trials=[];fail=[]
 for i,t in enumerate(CENTERS):
  try:p,s,x=patch(i,t,gm);patches.append(p);stars.extend(s);trials.extend(x)
  except Exception as e:fail.append({'patch':i,'target':list(t),'error':f'{type(e).__name__}: {e}'})
 stars=sorted(stars,key=lambda x:(x['ra'],x['dec']));rng=np.random.default_rng(SEED);dec=[]
 for s in stars:
  for _ in range(NDECOY):v,q=permute(s['vals'],s['ok'],rng);dec.append(pair_stat(v,q))
 real=np.asarray([s['pair_stat'] for s in stars],float);dec=np.asarray(dec,float);D=int(np.sum(dec>=FLOOR));R=int(np.sum(real>=FLOOR));expfalse=float((D+1)/(NDECOY+1));fdr=float(expfalse/max(R,1));elig=float(np.mean([x['eligible'] for x in trials])) if trials else 0.;rec=float(np.mean([x['recovered'] for x in trials])) if trials else 0.
 criteria={'five_patches_complete':len(patches)==5 and not fail,'valid_sources_at_least_100':len(stars)>=100,'decoy_exceedances_at_0p24_le_9':D<=9,'injection_pair_eligibility_ge_0p50':elig>=.50,'injection_recovery_ge_0p45':rec>=.45}
 out={'success':True,'field':FIELD,'preregistration_commit':'b8ae629c34d13ac50f4a7f320f881699260b4959','validation_passed':all(criteria.values()),'criteria':criteria,'patches':patches,'analysis_failures':fail,'valid_sources':len(stars),'real_pair_summary':pd.summary(real),'real_sources_ge_0p24':R,'decoys_per_source':NDECOY,'decoy_pair_summary':pd.summary(dec),'decoy_exceedances_ge_0p24':D,'expected_false_sources_at_0p24_plus1':expfalse,'target_decoy_fdr_at_0p24':fdr,'injection_amplitude':AMP,'injection_trials':len(trials),'injection_pair_eligibility':elig,'injection_recovery_pair_stat_ge_0p24':rec,'note':'Field 2 is validation-only; source identities above threshold are intentionally not emitted.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
