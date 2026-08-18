#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

YEARS=(2022,2023)
MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
COUNTS={2022:315024,2023:423658}
PRETRUTH_SHA='f52371ba1a302d57a4050b380c2a744a3be560fee0916b28ba10efbdf20e8351'
DIRECT_RESULT_SHA='20dd97323813f168da57383fe27dbd9685e68ddacd9b2ca1b9b31040c1cf1c4c'
REC_PRE_SHA='e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1'
REC_RES_SHA='433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
PARENT_EVALUATOR_BLOB='bb4dec3a40429db7d017bafcb442c536c4c7e6d6'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('protocol','pretruth','direct-result','recurrent-prelabel','recurrent-result','parent-evaluator','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):
        ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.pretruth)==PRETRUTH_SHA,'sealed direct pretruth changed')
    req(sha(a.direct_result)==DIRECT_RESULT_SHA,'sealed direct result changed')
    req(sha(a.recurrent_prelabel)==REC_PRE_SHA and sha(a.recurrent_result)==REC_RES_SHA,'recurrent artifacts changed')
    req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime inputs changed')
    parent_eval=load(a.parent_evaluator,'gmn_lit_parent_eval')
    req(getattr(parent_eval,'BLIND',None)==BLIND,'parent evaluator blind interval changed')
    pre=json.loads(a.pretruth.read_text()); direct=json.loads(a.direct_result.read_text())
    req(pre['scientific_role']=='TARGET_EXCLUDED_GMN_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH' and pre['shower_truth_used'] is False,'pretruth role/firewall')
    req(pre['target_information_access'] is False and pre['target_region_events_accessed'] is False,'target firewall')
    req(direct['verdict']=='PASS_RECURRENT_EOM_GMN_LITERATURE_4_OF_4','historical direct result identity')
    rec=list(pre['recurrent_candidates']); req(len(rec)==2097,'recurrent candidate count changed')
    sealed=json.loads(a.recurrent_result.read_text()); req(sealed['verdict']=='PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT','recurrent parent not frozen PASS')

    pr=load(a.parent_runner,'gmn_lit_fair_parent'); q=load(a.quality_source,'gmn_lit_fair_q')
    q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-recurrent-eom-gmn-literature-fairness-v1-truth'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed')
    args=SimpleNamespace(fixed4_baseline_json=a.v8_result_json,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    # load_sources expects the full argparse namespace used by the parent support runtime.
    for k,v in vars(a).items(): setattr(args,k,v)
    _c,base,_s=support.load_sources(args); scan,_cal,hidden,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
    annual={}
    for y in YEARS:
        rows=[pr.normalize_event(r,y) for r in list(scan[y])]; annual[y]={str(e['id']) for e in rows}; req(len(annual[y])==COUNTS[y],f'count {y}')

    panel_keys={'sugar2017':'sugar','hdbscan2025':'hdbscan2025'}
    metrics={}; gates={}; passed=0
    for comp,pkey in panel_keys.items():
        metrics[comp]={}
        for y in YEARS:
            lit=list(pre['panels'][str(y)][pkey]['clusters']); K=len(lit); req(0<K<=len(rec),f'invalid K {comp} {y}')
            rmet=parent_eval.evaluate(rec[:K],hidden,annual[y]); cmet=parent_eval.evaluate(lit,hidden,annual[y])
            # Verify comparator metric exactly reproduces the historical direct result.
            old=direct['metrics'][comp][str(y)]
            for key in ('candidate_count','eligible_showers','macro_f1','recovered_f1_gt_05'):
                if isinstance(old[key],float): req(abs(float(cmet[key])-float(old[key]))<=1e-15,f'comparator reproduction {comp} {y} {key}')
                else: req(cmet[key]==old[key],f'comparator reproduction {comp} {y} {key}')
            req(rmet['candidate_count']==cmet['candidate_count']==K,f'capacity mismatch {comp} {y}')
            ok=bool(rmet['macro_f1']>cmet['macro_f1'] and rmet['recovered_f1_gt_05']>=cmet['recovered_f1_gt_05'])
            passed+=int(ok)
            metrics[comp][str(y)]={'K':K,'recurrent_matched_capacity':rmet,'literature_complete_catalogue':cmet,'historical_recurrent_full_catalogue':direct['metrics']['recurrent_eom'][str(y)]}
            gates[f'{comp}_{y}']={'passed':ok,'K':K,'recurrent_macro_f1':rmet['macro_f1'],'comparator_macro_f1':cmet['macro_f1'],'recurrent_recovered_gt05':rmet['recovered_f1_gt_05'],'comparator_recovered_gt05':cmet['recovered_f1_gt_05']}
    verdict='PASS_RECURRENT_EOM_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4' if passed==4 else 'NO_RECURRENT_EOM_GMN_MATCHED_CAPACITY_4_OF_4_SUPERIORITY'
    out={'schema':'ORBITTRACE_RECURRENT_EOM_GMN_LITERATURE_FAIRNESS_V1_RESULT','verdict':verdict,'passed_pair_gates':passed,'total_pair_gates':4,'protocol_sha256':sha(a.protocol),'sealed_direct_pretruth_sha256':sha(a.pretruth),'sealed_direct_result_sha256':sha(a.direct_result),'metrics':metrics,'pair_gates':gates,'fairness_rule':'literature complete catalogue versus identical-size prefix of immutable recurrent-EOM order','sugar_claim_boundary':'deterministic published DBSCAN core only; full uncertainty-resampling pipeline not represented on GMN','mrr_head_to_head_defined':False,'mrr_reason':'literature comparator outputs are unordered catalogues','asfn_negative_result_remains_binding':True,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'amos_scientific_access':False,'asfn_efn_event_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={c:{str(y):{'K':metrics[c][str(y)]['K'],'recurrent_f1':metrics[c][str(y)]['recurrent_matched_capacity']['macro_f1'],'literature_f1':metrics[c][str(y)]['literature_complete_catalogue']['macro_f1'],'recurrent_recovered':metrics[c][str(y)]['recurrent_matched_capacity']['recovered_f1_gt_05'],'literature_recovered':metrics[c][str(y)]['literature_complete_catalogue']['recovered_f1_gt_05']} for y in YEARS} for c in panel_keys}
    print(json.dumps({'verdict':verdict,'passed_pair_gates':passed,'metrics':compact,'pair_gates':gates,'result_sha256':sha(a.output)},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
