#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def evaluate(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth); active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    mat=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_r,_fid,pred) in enumerate(active):
            ov=len(actual&pred)
            if ov:
                precision=ov/len(pred); recall=ov/len(actual); mat[i,j]=2*precision*recall/(precision+recall)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(cost); vals=[]; matches=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i>=len(labels): continue
        val=float(mat[i,j]) if j<len(active) else 0.0; vals.append(val)
        if j<len(active) and val>0:
            rank,fid,pred=active[j]; actual=truth_sets[labels[i]]; ov=len(actual&pred); precision=ov/len(pred); recall=ov/len(actual)
            matches.append({'label':labels[i],'family_id':fid,'rank':rank,'f1':val,'overlap':ov,'precision':precision,'recall':recall})
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(x>0.5 for x in vals)),'candidate_used':len(active),'matched_positive_pairs':matches}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--catalogue',type=Path,required=True); p.add_argument('--summary',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    summary=json.loads(a.summary.read_text()); require(summary['verdict']=='PASS_TARGET_OVERLAP_CANONICAL_SONOTACO_PRETRUTH_CATALOGUE_FREEZE','pretruth catalogue not frozen')
    require(summary['truth_accessed'] is False and summary['matched_comparator_rows_accessed'] is False and summary['model_retrained_on_sonotaco'] is False,'pretruth boundary changed')
    require(summary['feature_dimension']==21 and summary['source_specific_features_used'] is False,'source-blind feature boundary changed')
    require(summary['model_trained_with_sonotaco_label_free_covariates'] is True and summary['model_trained_with_sonotaco_shower_truth'] is False,'adaptation training boundary changed')
    catalogue=json.loads(a.catalogue.read_text()); require(sha(a.catalogue)==summary['primary_output_sha256'],'pretruth catalogue hash changed')
    require(catalogue['input_role'].startswith('single canonical SonotaCo base pair'),'detector input role changed')
    require(catalogue['truth_accessed'] is False and catalogue['matched_comparator_rows_accessed'] is False and catalogue['model_retrained_on_sonotaco'] is False,'pretruth catalogue became truth-bearing')
    require(catalogue['feature_dimension']==21 and catalogue['source_specific_features_used'] is False,'source-specific ranking information entered target-overlap application')
    require(catalogue['model_trained_with_sonotaco_label_free_covariates'] is True and catalogue['model_trained_with_sonotaco_shower_truth'] is False,'model adaptation provenance changed')
    families=catalogue['families']; require(len(families)==catalogue['family_count'] and [int(f['rank']) for f in families]==list(range(1,len(families)+1)),'ranked family catalogue invalid')
    final=json.loads((a.truth_root/'V15_FINAL_LITERATURE_RESULT.json').read_text()); require(final['verdict']=='FAIL_FINAL_LITERATURE_SUPERIORITY','immutable truth/comparator package changed')
    panels=[]
    for route,year in PANELS:
        truth=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text()); budget=int(frozen['candidate_budget']['comparator_budget'])
        cur=evaluate(families,truth,budget); lit=frozen['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); win=bool(cm>lm and cr>=lr)
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf'),'superiority_pair_pass':win,'candidate_used':cur['candidate_used'],'eligible_showers':cur['eligible_showers'],'matched_positive_pairs':cur['matched_positive_pairs']})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4
    result={'scientific_stage':'TARGET_OVERLAP_CANONICAL_SONOTACO_EXPOSED_LITERATURE_DEVELOPMENT','single_canonical_detector_catalogue':True,'panel_specific_candidate_generation':False,'panel_specific_ranking':False,'candidate_catalogue_sha256':sha(a.catalogue),'candidate_order_sha256':catalogue['target_overlap_order_sha256'],'candidate_counts':catalogue['candidate_counts'],'membership_diagnostics':catalogue['membership_diagnostics'],'feature_dimension':21,'source_specific_features_used':False,'model_trained_with_sonotaco_label_free_covariates':True,'model_trained_with_sonotaco_shower_truth':False,'panels':panels,'panel_wins':wins,'verdict':'PASS_TARGET_OVERLAP_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_TARGET_OVERLAP_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','model_retrained_on_sonotaco':False,'matched_comparator_rows_used_as_detector_input':False,'parameter_search':False,'post_result_second_search':False,'source_quota_selected':False,'alternate_overlap_rule_selected':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'TARGET_OVERLAP_CANONICAL_SONOTACO_EXPOSED_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':[{k:v for k,v in x.items() if k!='matched_positive_pairs'} for x in panels]},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
