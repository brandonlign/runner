#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); BUCKETS=(0,1,2,3)
QUALITY_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"; V8_SHA="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"; SOURCE_PRELABEL_SHA="db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de"; MANIFEST_SHA="3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8"; INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"

def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def aggregate(ps:list[dict[str,Any]],which:str)->dict[str,Any]:
    v=[p[which] for p in ps]; return {'qualified_total':sum(int(x['qualified_matches']) for x in v),'mrr_mean':float(np.mean([float(x['mrr']) for x in v])),'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in v])),'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in v])),'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in v),'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in v),'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in v),'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in v)}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('intrinsic-runner','prelabel','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'frozen input changed'); pre_sha=sha(a.prelabel); pre=json.loads(a.prelabel.read_text())
    req(pre['schema']=='ORBITTRACE_TOPOMODAL_ANNUAL_CONFIRMATION_V1_PRELABEL' and pre['scientific_role']=='PRELABEL_TOPOMODAL_ANNUAL_CONFIRMATION_V1','prelabel schema'); req(pre['source_1284_prelabel_sha256']==SOURCE_PRELABEL_SHA and pre['universe_manifest_sha256']==MANIFEST_SHA and pre['intrinsic_source_blob']==INTRINSIC_BLOB,'pretruth source pin'); req(pre['blind_exclusion']==[20.0,55.0] and pre['shower_truth_used'] is False and pre['shower_truth_parsed'] is False and pre['target_information_access'] is False,'prelabel firewall')
    req(pre['configuration']=={'candidate_generator':'exact_1284_complete_topomodal_hierarchy_from_immutable_prelabel','annual_topology':'exact_1284_topomodal_separately_per_year','annual_support_floor':4,'annual_similarity':'best_jaccard_of_candidate_year_restriction_to_any_reportable_annual_family','confirmation':'min(best_jaccard_2022,best_jaccard_2023)','ranking':'annual_confirmation_desc_then_family_hash','root_priority':False,'equal_budget':'recurrent_candidate_count'},'configuration changed')
    frozen={(int(r['denominator']),int(r['bucket'])):r for r in pre['subsets']}; req(set(frozen)=={(d,b) for d in (128,1024) for b in BUCKETS},'panel set'); req(pre['candidate_budget_shortage_any_panel'] is False,'candidate budget shortage')
    for r in pre['subsets']:
        succ,par=r['successor_candidates'],r['recurrent_candidates']; req(len(succ)>=len(par)==int(r['equal_budget_k']) and len(par)>0,'budget'); req([int(x['rank']) for x in succ]==list(range(1,len(succ)+1)),'rank continuity'); req(all('annual_jaccard_2022' in x and 'annual_jaccard_2023' in x and 'annual_confirmation' in x for x in succ),'confirmation fields missing')
    intrinsic=load(a.intrinsic_runner,'annual_eval_intrinsic'); parent=load(a.parent_runner,'annual_eval_parent'); req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,'parent constants')
    q=load(a.quality_source,'annual_eval_gmn'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-topomodal-annual-confirmation-v1-evaluator'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(isinstance(hidden,dict) and sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'truth source')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'universe/firewall'); ids=[str(e['id']) for e in events]; yrs=np.asarray([int(e['year']) for e in events],dtype=np.int64); hashes=np.asarray([intrinsic.event_hash_u64(x) for x in ids],dtype=np.uint64)
    panels=[]
    for d in (128,1024):
        for b in BUCKETS:
            fr=frozen[(d,b)]; ii=intrinsic.selected_indices(hashes,d,b); sid=[ids[int(i)] for i in ii]; sy=np.asarray(yrs[ii]); req(len(sid)==int(fr['events_total']) and intrinsic.universe_hash(sid)==str(fr['event_universe_sha256']),'event universe'); K=int(fr['equal_budget_k']); succ=fr['successor_candidates'][:K]; par=fr['recurrent_candidates']; req(len(succ)==len(par)==K,'budget')
            for y in YEARS:
                annual={sid[int(i)] for i in np.flatnonzero(sy==y)}; pm=compact(parent.metrics(par,hidden,annual)); sm=compact(parent.metrics(succ,hidden,annual)); panels.append({'denominator':d,'bucket':b,'year':y,'equal_budget_k':K,'parent':pm,'successor':sm,'qualified_nonlower':int(sm['qualified_matches'])>=int(pm['qualified_matches']),'qualified_strict_win':int(sm['qualified_matches'])>int(pm['qualified_matches'])})
    scales={}
    for d in (128,1024):
        ps=[p for p in panels if p['denominator']==d]; pa,sa=aggregate(ps,'parent'),aggregate(ps,'successor'); non=sum(bool(p['qualified_nonlower']) for p in ps); win=sum(bool(p['qualified_strict_win']) for p in ps); scales[str(d)]={'parent':pa,'successor':sa,'qualified_nonlower_panels':non,'qualified_strict_win_panels':win,'qualified_loss_panels':8-non}
    fp,fs=scales['1024']['parent'],scales['1024']['successor']; cp,cs=scales['128']['parent'],scales['128']['successor']
    gates={'fine_qualified_total_strictly_greater':fs['qualified_total']>fp['qualified_total'],'fine_qualified_nonlower_at_least_6_of_8':scales['1024']['qualified_nonlower_panels']>=6,'fine_mrr_mean_not_lower':fs['mrr_mean']>=fp['mrr_mean'],'fine_precision_mean_not_lower':fs['precision_mean']>=fp['precision_mean'],'fine_fragmentation_mean_not_higher':fs['fragmentation_mean']<=fp['fragmentation_mean'],'coarse_qualified_total_not_lower':cs['qualified_total']>=cp['qualified_total'],'coarse_qualified_nonlower_at_least_6_of_8':scales['128']['qualified_nonlower_panels']>=6,'coarse_mrr_mean_not_lower':cs['mrr_mean']>=cp['mrr_mean'],'coarse_precision_mean_not_lower':cs['precision_mean']>=cp['precision_mean'],'coarse_fragmentation_mean_not_higher':cs['fragmentation_mean']<=cp['fragmentation_mean']}
    verdict='PASS_TOPOMODAL_ANNUAL_CONFIRMATION_V1' if all(gates.values()) else 'FAIL_TOPOMODAL_ANNUAL_CONFIRMATION_V1'
    out={'schema':'ORBITTRACE_TOPOMODAL_ANNUAL_CONFIRMATION_V1','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_AND_GENERALIZATION_DEVELOPMENT','verdict':verdict,'prelabel_sha256':pre_sha,'source_1284_prelabel_sha256':SOURCE_PRELABEL_SHA,'universe_manifest_sha256':MANIFEST_SHA,'panels':panels,'scale_aggregates':scales,'gates':gates,'blind_exclusion':[20.0,55.0],'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    p=a.output/'TOPOMODAL_ANNUAL_CONFIRMATION_V1.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'prelabel_sha256':pre_sha,'scales':scales,'gates':gates},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
