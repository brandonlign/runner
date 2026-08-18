#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
YEARS=(2022,2023);MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13));BLIND=(20.0,55.0)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990';V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b';PP_SHA='efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993';PR_SHA='ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711';ORDER_SHA='e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2';COUNTS={2022:315024,2023:423658}
def req(x:bool,m:str)->None:
 if not x:raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
 s=importlib.util.spec_from_file_location(n,p);req(s is not None and s.loader is not None,f'cannot import {p}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def eligible(hidden:dict[str,str],annual:set[str])->dict[str,int]:
 c=Counter(v for k,v in hidden.items() if k in annual and v!='SPORADIC');return {k:n for k,n in c.items() if n>=4}
def one_truth(ids:list[str],hidden:dict[str,str],el:dict[str,int])->dict[str,Any]:
 c=Counter(hidden.get(x,'SPORADIC') for x in ids);rows=[]
 for lab,total in el.items():
  ov=int(c.get(lab,0))
  if ov<=0:continue
  p=ov/max(len(ids),1);r=ov/total;f=2*p*r/(p+r) if p+r else 0;rows.append((f,p,ov,lab,r))
 non=c.copy();non.pop('SPORADIC',None);dom=max(non.values(),default=0)/max(len(ids),1)
 if not rows:return {'positive':False,'best_label':None,'dominant_precision':float(dom)}
 f,p,ov,lab,r=max(rows,key=lambda x:(x[0],x[1],x[2],x[3]));return {'positive':bool(p>=.5 and ov>=4),'best_label':lab,'dominant_precision':float(dom),'f1':float(f),'precision':float(p),'recall':float(r),'overlap':ov}
def metrics(rows:list[dict[str,Any]],hidden:dict[str,str],annual:set[str])->dict[str,Any]:
 el=eligible(hidden,annual);first={x:None for x in el};frag=Counter();tp=[]
 for rank,row in enumerate(rows,1):
  ids=[str(x) for x in row['event_ids'] if str(x) in annual];t=one_truth(ids,hidden,el)
  if rank<=100:tp.append(float(t['dominant_precision']))
  if t['positive'] and t['best_label'] in el:
   lab=str(t['best_label']);
   if rank<=500:frag[lab]+=1
   if first[lab] is None:first[lab]=rank
 rep=[x for x,r in first.items() if r is not None];rr=sum(1.0/r for r in first.values() if r is not None);q=len(rep);e=len(el);fv=[frag[x] for x in rep if first[x] is not None and first[x]<=500]
 return {'eligible_labels':e,'qualified_matches':q,'recovered_at_25':sum(r is not None and r<=25 for r in first.values()),'recovered_at_50':sum(r is not None and r<=50 for r in first.values()),'recovered_at_100':sum(r is not None and r<=100 for r in first.values()),'recovered_at_500':sum(r is not None and r<=500 for r in first.values()),'top100_dominant_precision':float(np.mean(tp)) if tp else 0.0,'conditional_mrr':float(rr/q) if q else 0.0,'zero_filled_mrr':float(rr/e) if e else 0.0,'reciprocal_rank_mass':float(rr),'fragmentation_median_top500':float(np.median(fv)) if fv else 0.0,'first_rank_by_label':first}
def close(a,b):return bool(np.isclose(float(a),float(b),rtol=0,atol=1e-15))
def main()->int:
 ap=argparse.ArgumentParser()
 for n in ('prelabel','parent-prelabel','parent-result','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);req(sha(a.parent_prelabel)==PP_SHA and sha(a.parent_result)==PR_SHA,'parent artifacts changed');req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime source changed')
 f=json.loads(a.prelabel.read_text());req(f['schema']=='ORBITTRACE_RECURRENT_CROSSYEAR_TUKEY_CORE_V1_PRELABEL' and f['scientific_role']=='PRELABEL_TARGET_EXCLUDED_FIXED_RANK_CROSSYEAR_TUKEY_CORE','wrong prelabel');req(f['shower_truth_used'] is False and f['target_information_access'] is False and f['target_region_events_accessed'] is False,'prelabel firewall');req(f['parent_ordered_membership_sha256']==ORDER_SHA and f['parent_candidate_count']==f['successor_candidate_count']==2094,'parent contract');parents=list(f['parent_candidates']);succ=list(f['successor_candidates']);req([r['rank'] for r in succ]==list(range(1,2095)),'rank changed')
 for p,s in zip(parents,succ):req(str(p['family_id'])==str(s['family_id'])==str(s['parent_family_id']),'identity changed');req(set(s['event_ids']).issubset(set(p['event_ids'])),'escaped parent')
 sealed=json.loads(a.parent_result.read_text());req(sealed['verdict']=='PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT','parent not pass')
 pr=load(a.parent_runner,'tukey_truth_parent');q=load(a.quality_source,'tukey_truth_q');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100;rt=q.v1.mult.load_frozen_runtime();support=rt.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-recurrent-crossyear-tukey-core-v1-binding';support.RANKING_VARIANTS=('persistence',);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed');setattr(a,'fixed4_baseline_json',a.v8_result_json);_c,base,_s=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(base);req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
 annual={}
 for y in YEARS:
  rows=[pr.normalize_event(r,y) for r in list(scan[y])];annual[y]={str(e['id']) for e in rows};req(len(annual[y])==COUNTS[y],f'count {y}')
 pm={str(y):metrics(parents,hidden,annual[y]) for y in YEARS};sm={str(y):metrics(succ,hidden,annual[y]) for y in YEARS}
 for y in YEARS:
  x=pm[str(y)];z=sealed['successor_metrics'][str(y)]
  for k in ('eligible_labels','qualified_matches','recovered_at_25','recovered_at_50','recovered_at_100','recovered_at_500'):req(int(x[k])==int(z[k]),f'parent reproduction {y} {k}')
  req(close(x['top100_dominant_precision'],z['top100_dominant_precision']) and close(x['conditional_mrr'],z['mrr']) and close(x['fragmentation_median_top500'],z['fragmentation_median_top500']),'parent float reproduction');req(x['first_rank_by_label']==z['first_rank_by_label'],'first rank reproduction')
 gates=[];annual_gates={}
 for y in YEARS:
  p=pm[str(y)];s=sm[str(y)];g={'qualified_recovery_not_lower':s['qualified_matches']>=p['qualified_matches'],'recovered_at_25_not_lower':s['recovered_at_25']>=p['recovered_at_25'],'recovered_at_50_not_lower':s['recovered_at_50']>=p['recovered_at_50'],'recovered_at_100_not_lower':s['recovered_at_100']>=p['recovered_at_100'],'recovered_at_500_not_lower':s['recovered_at_500']>=p['recovered_at_500'],'zero_filled_mrr_not_lower':s['zero_filled_mrr']>=p['zero_filled_mrr'],'top100_precision_not_lower':s['top100_dominant_precision']>=p['top100_dominant_precision'],'fragmentation_not_higher':s['fragmentation_median_top500']<=p['fragmentation_median_top500']};annual_gates[str(y)]=g;gates.extend({'gate':f'{y}:{k}','passed':bool(v)} for k,v in g.items())
 passed=sum(int(x['passed']) for x in gates);verdict='PASS_RECURRENT_CROSSYEAR_TUKEY_CORE_V1' if passed==16 else 'FAIL_RECURRENT_CROSSYEAR_TUKEY_CORE_V1'
 out={'schema':'ORBITTRACE_RECURRENT_CROSSYEAR_TUKEY_CORE_V1_BINDING_RESULT','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_FIXED_RANK_CROSSYEAR_CORE_BINDING','verdict':verdict,'prelabel_sha256':sha(a.prelabel),'parent_binding_run_id':31852836840,'parent_binding_artifact_id':9238142199,'parent_metrics':pm,'successor_metrics':sm,'annual_gates':annual_gates,'gates':gates,'passed_gate_count':passed,'total_gate_count':16,'changed_slot_count':f['changed_slot_count'],'fallback_slot_count':f['fallback_slot_count'],'total_removed_events':f['total_removed_events'],'binding_retrieval_metric':'zero_filled_eligible_query_mrr','historical_conditional_mrr_is_diagnostic_only':True,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'passed_gate_count':passed,'parent_metrics':{y:{k:v for k,v in m.items() if k!='first_rank_by_label'} for y,m in pm.items()},'successor_metrics':{y:{k:v for k,v in m.items() if k!='first_rank_by_label'} for y,m in sm.items()},'annual_gates':annual_gates,'result_sha256':sha(a.output)},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
