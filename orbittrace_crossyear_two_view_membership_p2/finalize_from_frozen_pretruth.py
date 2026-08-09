#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
P2_SOURCE_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
EXPECTED_MODEL_SHA256='0cc5e2472f65e586cb18febffdbe3109e9e4041a6e09da07aa0bd4903a78c85f'
EXPECTED_MEMBERSHIP_SHA256='b077bc16e0a4792e5ae75a2be48801cd0a1404ee282856d73e99e891dfb93a6e'
EXPECTED_FAMILY_COUNT=226
EXPECTED_BASELINE_QUALIFIED=95
EXPECTED_BASELINE_RECOVERY100=58
EXPECTED_BASELINE_MRR=0.045531138942766655
EXPECTED_BASELINE_TOP100_PRECISION=0.6884631112636006
EXPECTED_BASELINE_MACRO_F1=0.1736657194465356
TOP100_PRECISION_FLOOR=0.65
MACRO_F1_GAIN_GATE=0.08
LARGE_TOTAL_MIN=100
LARGE_RECALL_MULTIPLIER=1.5
LARGE_PRECISION_FLOOR=0.85
DSH_COMPARATOR_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
V8_SOURCE_COMMIT='c9d6c44704013ba0c9430100e98a29a56b453304'

def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)
def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def reconstruct_seed_families(expanded:list[dict[str,Any]])->list[dict[str,Any]]:
    seeds=[]
    for out in expanded:
        row=json.loads(json.dumps(out)); additions=set(map(str,row.get('p2_added_event_ids',[]))); members=set(map(str,row['event_ids'])); require(additions<=members,f'P2 addition outside expanded family {row["family_id"]}'); original=sorted(members-additions); require(original,f'empty reconstructed seed family {row["family_id"]}'); row['event_ids']=original; row['event_count']=len(original); row.pop('p2_added_event_ids',None); row.pop('p2_added_event_count',None); seeds.append(row)
    return seeds

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--p2-source',required=True,type=Path); p.add_argument('--expanded-families',required=True,type=Path); p.add_argument('--membership-sha',required=True,type=Path); p.add_argument('--model-json',required=True,type=Path); p.add_argument('--model-sha',required=True,type=Path); p.add_argument('--base-runner',required=True,type=Path); p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path); p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path); p.add_argument('--v8-result-json',required=True,type=Path); p.add_argument('--v8-runner',required=True,type=Path); p.add_argument('--dsh-comparator',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha256_file(a.p2_source)==P2_SOURCE_SHA256,'canonical P2 source changed'); require(sha256_file(a.v8_result_json)==V8_RESULT_SHA256,'promoted-v8 result artifact changed'); require(sha256_file(a.dsh_comparator)==DSH_COMPARATOR_SHA256,'D_SH source changed'); require(a.membership_sha.read_text().strip()==EXPECTED_MEMBERSHIP_SHA256,'stored P2 membership hash changed'); require(a.model_sha.read_text().strip()==EXPECTED_MODEL_SHA256,'stored P2 model hash changed')
    raw=gzip.decompress(a.expanded_families.read_bytes()); require(hashlib.sha256(raw).hexdigest()==EXPECTED_MEMBERSHIP_SHA256,'expanded P2 membership payload changed'); expanded=json.loads(raw); require(len(expanded)==EXPECTED_FAMILY_COUNT,'P2 family count changed'); require(canonical_sha(json.loads(a.model_json.read_text()))==EXPECTED_MODEL_SHA256,'P2 model canonical hash changed')
    p2=load_module(a.p2_source,'orbittrace_p2_direct_finalize_science'); old=load_module(a.base_runner,'orbittrace_p2_direct_finalize_base'); v8=load_module(a.v8_runner,'orbittrace_p2_direct_finalize_v8'); support=old.load_support_module(a.support_source_parts); source_args=type('Args',(),{'candidate_payload':a.candidate_payload,'baseline_payload':a.baseline_payload,'scorer_parts':a.scorer_parts})(); _,base,_=support.load_sources(source_args); require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    scan_by_year,_,hidden_labels,_sources=support.parse_catalogue(base); require(sorted(scan_by_year)==list(YEARS),'development year universe changed'); require(all(not(20.0<=float(e['sol'])<=55.0) for y in YEARS for e in scan_by_year[y]),'target interval entered direct finalization')
    order=[str(f['family_id']) for f in expanded]; require(len(order)==len(set(order))==EXPECTED_FAMILY_COUNT,'P2 family IDs/order changed'); seeds=reconstruct_seed_families(expanded); require([str(f['family_id']) for f in seeds]==order,'reconstructed v8 order changed'); require(all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),'P2 seed preservation failed')
    v8.mult.YEARS=YEARS; v8.mult.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); v8.mult.TOP_K=100
    baseline_full=v8.mult.evaluate_order(hidden_labels,seeds,order); p2_full=v8.mult.evaluate_order(hidden_labels,expanded,order)
    v8_result=json.loads(a.v8_result_json.read_text()); require(v8_result['verdict']=='PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT' and int(v8_result['family_count'])==EXPECTED_FAMILY_COUNT,'promoted-v8 prerequisite changed'); baseline=v8_result['metrics']['multiplicity']; exact={'eligible_labels':baseline['eligible_labels'],'qualified_matches':baseline['qualified_matches'],'recovered_at_100':baseline['recovered_at_100'],'recovered_at_500':baseline['recovered_at_500'],'mrr':baseline['mrr'],'median_rank':baseline['median_rank'],'macro_f1':baseline['macro_f1'],'top100_dominant_precision':baseline['top100_dominant_precision']}; baseline_reproduced=all((abs(float(baseline_full[k])-float(v))<=1e-12 if isinstance(v,(int,float)) and v is not None else baseline_full[k]==v) for k,v in exact.items()); require(int(baseline_full['qualified_matches'])==EXPECTED_BASELINE_QUALIFIED and int(baseline_full['recovered_at_100'])==EXPECTED_BASELINE_RECOVERY100,'reconstructed v8 coverage changed'); require(abs(float(baseline_full['mrr'])-EXPECTED_BASELINE_MRR)<=1e-15 and abs(float(baseline_full['top100_dominant_precision'])-EXPECTED_BASELINE_TOP100_PRECISION)<=1e-12 and abs(float(baseline_full['macro_f1'])-EXPECTED_BASELINE_MACRO_F1)<=1e-12,'reconstructed v8 metric identity changed')
    totals=p2.label_totals(hidden_labels,v8.mult); large_labels={str(row['label']) for row in baseline_full['per_label'] if bool(row.get('qualified',False)) and totals.get(str(row['label']),0)>=LARGE_TOTAL_MIN}; require(bool(large_labels),'no exact-v8 large-shower subset'); baseline_large=p2.large_summary(baseline_full,totals,large_labels); p2_large=p2.large_summary(p2_full,totals,large_labels)
    gates={'exact_v8_226_family_order':len(expanded)==EXPECTED_FAMILY_COUNT and [str(f['family_id']) for f in expanded]==order,'exact_v8_seed_members_preserved':all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),'v8_baseline_reproduced':bool(baseline_reproduced),'exact_dsh_source_identity':sha256_file(a.dsh_comparator)==DSH_COMPARATOR_SHA256,'model_frozen_before_truth_evaluation':a.model_sha.read_text().strip()==EXPECTED_MODEL_SHA256,'membership_frozen_before_truth_evaluation':a.membership_sha.read_text().strip()==EXPECTED_MEMBERSHIP_SHA256,'classifier_converged':int(json.loads(a.model_json.read_text())['logistic_n_iter'][0])<1000,'expansion_nonvacuous':sum(len(f.get('p2_added_event_ids',[])) for f in expanded)>0,'qualified_matches_no_regression':int(p2_full['qualified_matches'])>=EXPECTED_BASELINE_QUALIFIED,'recovery_at_100_no_regression':int(p2_full['recovered_at_100'])>=EXPECTED_BASELINE_RECOVERY100,'top100_dominant_precision_at_least_065':float(p2_full['top100_dominant_precision'])>=TOP100_PRECISION_FLOOR,'macro_f1_gain_at_least_008':float(p2_full['macro_f1'])>=EXPECTED_BASELINE_MACRO_F1+MACRO_F1_GAIN_GATE,'large_shower_mean_recall_at_least_15x_v8':float(p2_large['mean_recall'])>=LARGE_RECALL_MULTIPLIER*float(baseline_large['mean_recall']),'large_shower_mean_precision_at_least_085':float(p2_large['mean_precision'])>=LARGE_PRECISION_FLOOR}; verdict='PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT' if all(gates.values()) else 'FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO'
    result={'verdict':verdict,'classification':'cross-year self-supervised two-view membership discriminator; direct finalization from immutable pretruth after post-verdict diagnostic crash','configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'v8_source_commit':V8_SOURCE_COMMIT,'family_count':EXPECTED_FAMILY_COUNT,'features':['cross-year source-seed OAS Mahalanobis observation distance','minimum exact D_SH to source-year immutable seed'],'window_half_width_deg':5.0,'negative_minimum_per_direction':128,'family_direction_class_total_weights':{'positive':0.5,'negative':0.5},'scaler':'StandardScaler fit with frozen sample weights','classifier':'LogisticRegression L2 C=1.0 lbfgs max_iter=1000 tol=1e-10','background_odds_weight':1.0,'responsibility_threshold':0.5,'new_members_can_seed_growth':False,'ranking_after_membership':'unchanged exact promoted-v8 multiplicity order','parameter_search':False},'sources':{'canonical_p2_sha256':P2_SOURCE_SHA256,'dsh_sha256':DSH_COMPARATOR_SHA256,'pretruth_source_run':31289791712,'pretruth_artifact_id':9031107930},'model_pretruth_sha256':EXPECTED_MODEL_SHA256,'membership_pretruth_sha256':EXPECTED_MEMBERSHIP_SHA256,'baseline_v8':{k:v for k,v in baseline_full.items() if k!='per_label'},'p2':{k:v for k,v in p2_full.items() if k!='per_label'},'baseline_large_shower':baseline_large,'p2_large_shower':p2_large,'gates':gates,'diagnostics':{'direct_finalization_from_frozen_pretruth':True,'assigned_nonseed_events':sum(len(f.get('p2_added_event_ids',[])) for f in expanded),'families_gaining_members':sum(bool(f.get('p2_added_event_ids')) for f in expanded),'omitted_stale_non_scientific_diagnostic':'valid_nonseed_events_by_year'},'claim_boundary':'Target-excluded development only. Scientific method/model/memberships were frozen before truth in source run 31289791712; this finalizer evaluates those exact immutable memberships under unchanged canonical P2 gates.'}; out=a.output/'crossyear_two_view_membership_p2_development.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); (a.output/'CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md').write_text('# OrbitTrace cross-year two-view membership P2 development\n\n'+f'Verdict: **`{verdict}`**\n\n'+f"- v8 -> P2 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\n"+f"- v8 -> P2 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\n"+f"- v8 -> P2 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\n"+f"- v8 -> P2 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\n"+f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p2_large['mean_recall']:.6f}**\n"+f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p2_large['mean_precision']:.6f}**\n"+f"- assigned nonseed events (frozen pretruth): **{sum(len(f.get('p2_added_event_ids',[])) for f in expanded):,}**\n"+f'- model SHA-256: `{EXPECTED_MODEL_SHA256}`\n'+f'- membership SHA-256: `{EXPECTED_MEMBERSHIP_SHA256}`\n\nNo target information or target-region event was used.\n'); print((a.output/'CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md').read_text(),flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
