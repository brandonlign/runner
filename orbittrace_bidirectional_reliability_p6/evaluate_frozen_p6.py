#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS=(2022,2023)
P2_SOURCE_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
DSH_COMPARATOR_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
V8_SOURCE_COMMIT='c9d6c44704013ba0c9430100e98a29a56b453304'
EXPECTED_P5_MEMBERSHIP_SHA='933be44170bc91cf8e92a38b84689d590610ecdf809e911ac40022b5d4e806c9'
EXPECTED_P5_DECISIONS_SHA='b9b87427e8d5521e92bca3d27ef9528da7509f2c9d5a647764789abc65323711'
EXPECTED_CROSSFIT_SHA='55defa606101cfc0e0f9038d326fd19cfd99d0c423b68602ecd5581e00ff8ac1'
EXPECTED_MODEL_SHA='8ac8b13ab025a636884d44a2b19d478c9de5c138c3da190f3dfe3d73490257eb'
EXPECTED_P6_MEMBERSHIP_SHA='40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6'
EXPECTED_P6_DECISIONS_SHA='5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490'
EXPECTED_FAMILY_COUNT=226
EXPECTED_ELIGIBLE_FAMILIES=218
EXPECTED_INELIGIBLE_FAMILIES=8
EXPECTED_P6_ASSIGNMENTS=21626
EXPECTED_P6_GAINING_FAMILIES=214
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
        row=json.loads(json.dumps(out))
        additions=set(map(str,row.get('p2_added_event_ids',[])))
        members=set(map(str,row['event_ids']))
        require(additions<=members,f'P6 addition outside expanded family {row["family_id"]}')
        original=sorted(members-additions)
        require(original,f'empty reconstructed v8 seed family {row["family_id"]}')
        row['event_ids']=original; row['event_count']=len(original)
        row.pop('p2_added_event_ids',None); row.pop('p2_added_event_count',None)
        seeds.append(row)
    return seeds

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--p2-source',required=True,type=Path)
    p.add_argument('--p6-expanded-families',required=True,type=Path)
    p.add_argument('--p6-membership-sha',required=True,type=Path)
    p.add_argument('--p6-decisions',required=True,type=Path)
    p.add_argument('--p6-decisions-sha',required=True,type=Path)
    p.add_argument('--p6-transform-json',required=True,type=Path)
    p.add_argument('--base-runner',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--v8-result-json',required=True,type=Path)
    p.add_argument('--v8-runner',required=True,type=Path)
    p.add_argument('--dsh-comparator',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    require(sha256_file(a.p2_source)==P2_SOURCE_SHA256,'canonical P2 source changed')
    require(sha256_file(a.v8_result_json)==V8_RESULT_SHA256,'promoted-v8 result changed')
    require(sha256_file(a.dsh_comparator)==DSH_COMPARATOR_SHA256,'D_SH source changed')
    require(a.p6_membership_sha.read_text().strip()==EXPECTED_P6_MEMBERSHIP_SHA,'P6 stored membership SHA changed')
    require(a.p6_decisions_sha.read_text().strip()==EXPECTED_P6_DECISIONS_SHA,'P6 stored decisions SHA changed')

    raw=gzip.decompress(a.p6_expanded_families.read_bytes())
    require(hashlib.sha256(raw).hexdigest()==EXPECTED_P6_MEMBERSHIP_SHA,'P6 expanded membership payload changed')
    expanded=json.loads(raw); require(len(expanded)==EXPECTED_FAMILY_COUNT,'P6 family count changed')
    d_raw=gzip.decompress(a.p6_decisions.read_bytes()); require(hashlib.sha256(d_raw).hexdigest()==EXPECTED_P6_DECISIONS_SHA,'P6 decisions payload changed')
    decisions=json.loads(d_raw); require(len(decisions['assignments'])==EXPECTED_P6_ASSIGNMENTS,'P6 retained assignment count changed')
    transform=json.loads(a.p6_transform_json.read_text())
    require(transform['membership_pretruth_sha256']==EXPECTED_P6_MEMBERSHIP_SHA and transform['decisions_pretruth_sha256']==EXPECTED_P6_DECISIONS_SHA,'P6 transform identity changed')
    require(transform['source_p5_membership_sha256']==EXPECTED_P5_MEMBERSHIP_SHA and transform['source_p5_decisions_sha256']==EXPECTED_P5_DECISIONS_SHA,'P5 source identity changed')
    require(transform['source_crossfit_sha256']==EXPECTED_CROSSFIT_SHA and transform['source_model_sha256']==EXPECTED_MODEL_SHA,'P5 model/crossfit identity changed')
    require(transform['bidirectionally_reliable_families']==EXPECTED_ELIGIBLE_FAMILIES and transform['ineligible_families']==EXPECTED_INELIGIBLE_FAMILIES,'P6 family eligibility changed')
    require(transform['retained_assignments']==EXPECTED_P6_ASSIGNMENTS and transform['families_gaining_members']==EXPECTED_P6_GAINING_FAMILIES,'P6 frozen counts changed')
    require(transform['known_shower_truth_accessed'] is False and transform['target_information_accessed'] is False,'P6 pretruth firewall record changed')

    p2=load_module(a.p2_source,'orbittrace_p6_eval_p2')
    old=load_module(a.base_runner,'orbittrace_p6_eval_base')
    v8=load_module(a.v8_runner,'orbittrace_p6_eval_v8')
    support=old.load_support_module(a.support_source_parts)
    source_args=type('Args',(),{'candidate_payload':a.candidate_payload,'baseline_payload':a.baseline_payload,'scorer_parts':a.scorer_parts})()
    _,base,_=support.load_sources(source_args)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    scan_by_year,_,hidden_labels,_sources=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),'development year universe changed')
    require(all(not(20.0<=float(e['sol'])<=55.0) for y in YEARS for e in scan_by_year[y]),'target interval entered P6 evaluation')

    order=[str(f['family_id']) for f in expanded]
    require(len(order)==len(set(order))==EXPECTED_FAMILY_COUNT,'P6 family IDs/order changed')
    seeds=reconstruct_seed_families(expanded)
    require([str(f['family_id']) for f in seeds]==order,'reconstructed v8 order changed')
    require(all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),'P6 seed preservation failed')
    require(sum(len(f.get('p2_added_event_ids',[])) for f in expanded)==EXPECTED_P6_ASSIGNMENTS,'P6 addition count changed')
    require(sum(bool(f.get('p2_added_event_ids')) for f in expanded)==EXPECTED_P6_GAINING_FAMILIES,'P6 gaining-family count changed')
    ineligible=set(transform['ineligible_family_ids'])
    require(all(not f.get('p2_added_event_ids') for f in expanded if str(f['family_id']) in ineligible),'ineligible family retained additions')

    v8.mult.YEARS=YEARS; v8.mult.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); v8.mult.TOP_K=100
    baseline_full=v8.mult.evaluate_order(hidden_labels,seeds,order)
    p6_full=v8.mult.evaluate_order(hidden_labels,expanded,order)
    v8_result=json.loads(a.v8_result_json.read_text())
    require(v8_result['verdict']=='PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT' and int(v8_result['family_count'])==EXPECTED_FAMILY_COUNT,'promoted-v8 prerequisite changed')
    baseline=v8_result['metrics']['multiplicity']
    exact={'eligible_labels':baseline['eligible_labels'],'qualified_matches':baseline['qualified_matches'],'recovered_at_100':baseline['recovered_at_100'],'recovered_at_500':baseline['recovered_at_500'],'mrr':baseline['mrr'],'median_rank':baseline['median_rank'],'macro_f1':baseline['macro_f1'],'top100_dominant_precision':baseline['top100_dominant_precision']}
    baseline_reproduced=all((abs(float(baseline_full[k])-float(v))<=1e-12 if isinstance(v,(int,float)) and v is not None else baseline_full[k]==v) for k,v in exact.items())
    require(int(baseline_full['qualified_matches'])==EXPECTED_BASELINE_QUALIFIED and int(baseline_full['recovered_at_100'])==EXPECTED_BASELINE_RECOVERY100,'reconstructed v8 coverage changed')
    require(abs(float(baseline_full['mrr'])-EXPECTED_BASELINE_MRR)<=1e-15 and abs(float(baseline_full['top100_dominant_precision'])-EXPECTED_BASELINE_TOP100_PRECISION)<=1e-12 and abs(float(baseline_full['macro_f1'])-EXPECTED_BASELINE_MACRO_F1)<=1e-12,'reconstructed v8 metric identity changed')

    totals=p2.label_totals(hidden_labels,v8.mult)
    large_labels={str(row['label']) for row in baseline_full['per_label'] if bool(row.get('qualified',False)) and totals.get(str(row['label']),0)>=LARGE_TOTAL_MIN}
    require(bool(large_labels),'no exact-v8 large-shower subset')
    baseline_large=p2.large_summary(baseline_full,totals,large_labels)
    p6_large=p2.large_summary(p6_full,totals,large_labels)
    gates={
        'exact_v8_226_family_order':len(expanded)==EXPECTED_FAMILY_COUNT and [str(f['family_id']) for f in expanded]==order,
        'exact_v8_seed_members_preserved':all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),
        'v8_baseline_reproduced':bool(baseline_reproduced),
        'exact_dsh_source_identity':sha256_file(a.dsh_comparator)==DSH_COMPARATOR_SHA256,
        'p6_membership_frozen_before_truth':a.p6_membership_sha.read_text().strip()==EXPECTED_P6_MEMBERSHIP_SHA,
        'p6_decisions_frozen_before_truth':a.p6_decisions_sha.read_text().strip()==EXPECTED_P6_DECISIONS_SHA,
        'p6_exact_bidirectionally_reliable_family_count':transform['bidirectionally_reliable_families']==EXPECTED_ELIGIBLE_FAMILIES,
        'p6_no_expansion_if_either_direction_unreliable':all(not f.get('p2_added_event_ids') for f in expanded if str(f['family_id']) in ineligible),
        'p6_strict_subset_of_p5':transform['retained_assignments']==EXPECTED_P6_ASSIGNMENTS and transform['dropped_assignments']==3320,
        'expansion_nonvacuous':EXPECTED_P6_ASSIGNMENTS>0,
        'qualified_matches_no_regression':int(p6_full['qualified_matches'])>=EXPECTED_BASELINE_QUALIFIED,
        'recovery_at_100_no_regression':int(p6_full['recovered_at_100'])>=EXPECTED_BASELINE_RECOVERY100,
        'top100_dominant_precision_at_least_065':float(p6_full['top100_dominant_precision'])>=TOP100_PRECISION_FLOOR,
        'macro_f1_gain_at_least_008':float(p6_full['macro_f1'])>=EXPECTED_BASELINE_MACRO_F1+MACRO_F1_GAIN_GATE,
        'large_shower_mean_recall_at_least_15x_v8':float(p6_large['mean_recall'])>=LARGE_RECALL_MULTIPLIER*float(baseline_large['mean_recall']),
        'large_shower_mean_precision_at_least_085':float(p6_large['mean_precision'])>=LARGE_PRECISION_FLOOR,
    }
    verdict='PASS_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_DEVELOPMENT' if all(gates.values()) else 'FAIL_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_NO_GO'
    result={
        'verdict':verdict,
        'classification':'artifact-only P5 membership with family expansion permitted only under reciprocal P3 reliability; immutable promoted-v8 cores and rank',
        'configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'v8_source_commit':V8_SOURCE_COMMIT,'family_count':EXPECTED_FAMILY_COUNT,'source_p5_run':31293431873,'source_p5_artifact_id':9032407268,'bidirectional_rule':'both opposite-year P3 reliability flags must be true or family reverts to exact v8 seeds','parameter_search':False,'new_members_can_seed_growth':False,'ranking_after_membership':'unchanged exact promoted-v8 multiplicity order'},
        'hashes':{'source_p5_membership_sha256':EXPECTED_P5_MEMBERSHIP_SHA,'source_p5_decisions_sha256':EXPECTED_P5_DECISIONS_SHA,'source_crossfit_sha256':EXPECTED_CROSSFIT_SHA,'source_model_sha256':EXPECTED_MODEL_SHA,'p6_membership_pretruth_sha256':EXPECTED_P6_MEMBERSHIP_SHA,'p6_decisions_pretruth_sha256':EXPECTED_P6_DECISIONS_SHA},
        'baseline_v8':{k:v for k,v in baseline_full.items() if k!='per_label'},
        'p6':{k:v for k,v in p6_full.items() if k!='per_label'},
        'baseline_large_shower':baseline_large,
        'p6_large_shower':p6_large,
        'gates':gates,
        'diagnostics':{'artifact_only_transform':True,'bidirectionally_reliable_families':EXPECTED_ELIGIBLE_FAMILIES,'ineligible_families':EXPECTED_INELIGIBLE_FAMILIES,'dropped_p5_assignments':3320,'assigned_nonseed_events':EXPECTED_P6_ASSIGNMENTS,'families_gaining_members':EXPECTED_P6_GAINING_FAMILIES},
        'claim_boundary':'Target-excluded development only. P6 membership/decisions were deterministically frozen from the immutable P5 pretruth artifact before known-shower truth was reopened; no detector refit, rescore or target access occurred.',
    }
    (a.output/'bidirectional_reliability_membership_p6_development.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (a.output/'BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_DEVELOPMENT.md').write_text(
        '# OrbitTrace P6 bidirectional-reliability membership development\n\n'
        f'Verdict: **`{verdict}`**\n\n'
        f"- v8 -> P6 macro F1: **{baseline_full['macro_f1']:.6f} -> {p6_full['macro_f1']:.6f}**\n"
        f"- v8 -> P6 qualified: **{baseline_full['qualified_matches']} -> {p6_full['qualified_matches']}**\n"
        f"- v8 -> P6 recovery@100: **{baseline_full['recovered_at_100']} -> {p6_full['recovered_at_100']}**\n"
        f"- v8 -> P6 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p6_full['top100_dominant_precision']:.6f}**\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p6_large['mean_recall']:.6f}**\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p6_large['mean_precision']:.6f}**\n"
        f'- retained P6 additions: **{EXPECTED_P6_ASSIGNMENTS:,}**; dropped one-way P5 assignments: **3,320**\n'
        f'- P6 membership SHA-256: `{EXPECTED_P6_MEMBERSHIP_SHA}`\n'
        f'- P6 decisions SHA-256: `{EXPECTED_P6_DECISIONS_SHA}`\n\n'
        'No OrbitTrace target information or target-region event was used.\n'
    )
    print((a.output/'BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_DEVELOPMENT.md').read_text(),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
