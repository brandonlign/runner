#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

YEARS=(2022,2023)
P2_SOURCE_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
DSH_COMPARATOR_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
V8_SOURCE_COMMIT='c9d6c44704013ba0c9430100e98a29a56b453304'
EXPECTED_P6_MEMBERSHIP_SHA='40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6'
EXPECTED_P6_DECISIONS_SHA='5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490'
EXPECTED_P7_MEMBERSHIP_SHA='c68dcf21761cdad3048508902a7382039ea543df5b58a6b95a094c7c17f2db7a'
EXPECTED_P7_DECISIONS_SHA='4ffb9a4a4735788322825aaa24a1adee50ac7f5d13d0aba61c579d4b7b206ba5'
EXPECTED_FAMILY_COUNT=226
EXPECTED_P7_ASSIGNMENTS=4463
EXPECTED_GAINING_FAMILIES=214
EXPECTED_BINDING_CELLS=283
EXPECTED_BINDING_FAMILIES=174
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
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def reconstruct_seed_families(expanded:list[dict[str,Any]])->list[dict[str,Any]]:
    seeds=[]
    for out in expanded:
        row=json.loads(json.dumps(out))
        additions=set(map(str,row.get('p2_added_event_ids',[])))
        members=set(map(str,row['event_ids']))
        require(additions<=members,f'P7 addition outside family {row["family_id"]}')
        original=sorted(members-additions); require(original,f'empty reconstructed v8 seed family {row["family_id"]}')
        row['event_ids']=original; row['event_count']=len(original)
        row.pop('p2_added_event_ids',None); row.pop('p2_added_event_count',None)
        seeds.append(row)
    return seeds

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--p2-source',required=True,type=Path)
    p.add_argument('--p7-expanded-families',required=True,type=Path)
    p.add_argument('--p7-membership-sha',required=True,type=Path)
    p.add_argument('--p7-decisions',required=True,type=Path)
    p.add_argument('--p7-decisions-sha',required=True,type=Path)
    p.add_argument('--p7-transform-json',required=True,type=Path)
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
    require(a.p7_membership_sha.read_text().strip()==EXPECTED_P7_MEMBERSHIP_SHA,'P7 stored membership SHA changed')
    require(a.p7_decisions_sha.read_text().strip()==EXPECTED_P7_DECISIONS_SHA,'P7 stored decisions SHA changed')

    raw=gzip.decompress(a.p7_expanded_families.read_bytes()); require(hashlib.sha256(raw).hexdigest()==EXPECTED_P7_MEMBERSHIP_SHA,'P7 membership payload changed')
    expanded=json.loads(raw); require(len(expanded)==EXPECTED_FAMILY_COUNT,'P7 family count changed')
    d_raw=gzip.decompress(a.p7_decisions.read_bytes()); require(hashlib.sha256(d_raw).hexdigest()==EXPECTED_P7_DECISIONS_SHA,'P7 decisions payload changed')
    decisions=json.loads(d_raw); assignments=decisions['assignments']; require(len(assignments)==EXPECTED_P7_ASSIGNMENTS,'P7 assignment count changed')
    transform=json.loads(a.p7_transform_json.read_text())
    require(transform['source_p6_membership_sha256']==EXPECTED_P6_MEMBERSHIP_SHA,'P6 membership source changed')
    require(transform['source_p6_decisions_sha256']==EXPECTED_P6_DECISIONS_SHA,'P6 decisions source changed')
    require(transform['retained_assignments']==EXPECTED_P7_ASSIGNMENTS and transform['families_gaining_members']==EXPECTED_GAINING_FAMILIES,'P7 frozen counts changed')
    require(transform['budget_binding_family_year_cells']==EXPECTED_BINDING_CELLS and transform['budget_binding_families']==EXPECTED_BINDING_FAMILIES,'P7 binding counts changed')
    require(transform['membership_pretruth_sha256']==EXPECTED_P7_MEMBERSHIP_SHA and transform['decisions_pretruth_sha256']==EXPECTED_P7_DECISIONS_SHA,'P7 transform identity changed')
    require(transform['known_shower_truth_accessed'] is False and transform['target_information_accessed'] is False,'P7 pretruth firewall changed')

    budgets=decisions['family_year_budgets']
    retained_counts=Counter((str(rec['family_id']),str(int(rec['target_year']))) for rec in assignments.values())
    for fid,rec in budgets.items():
        for year in map(str,YEARS):
            require(retained_counts.get((fid,year),0)<=int(rec['immutable_seed_count_by_year'][year]),f'P7 year seed budget exceeded: {fid} {year}')

    p2=load_module(a.p2_source,'orbittrace_p7_eval_p2')
    old=load_module(a.base_runner,'orbittrace_p7_eval_base')
    v8=load_module(a.v8_runner,'orbittrace_p7_eval_v8')
    support=old.load_support_module(a.support_source_parts)
    source_args=type('Args',(),{'candidate_payload':a.candidate_payload,'baseline_payload':a.baseline_payload,'scorer_parts':a.scorer_parts})()
    _,base,_=support.load_sources(source_args)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    scan_by_year,_,hidden_labels,_=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),'development year universe changed')
    require(all(not(20.0<=float(e['sol'])<=55.0) for y in YEARS for e in scan_by_year[y]),'target interval entered P7 evaluation')

    order=[str(f['family_id']) for f in expanded]; require(len(order)==len(set(order))==EXPECTED_FAMILY_COUNT,'P7 family IDs/order changed')
    seeds=reconstruct_seed_families(expanded); require([str(f['family_id']) for f in seeds]==order,'reconstructed v8 order changed')
    require(all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),'P7 seed preservation failed')
    require(sum(len(f.get('p2_added_event_ids',[])) for f in expanded)==EXPECTED_P7_ASSIGNMENTS,'P7 addition count changed')
    require(sum(bool(f.get('p2_added_event_ids')) for f in expanded)==EXPECTED_GAINING_FAMILIES,'P7 gaining-family count changed')

    v8.mult.YEARS=YEARS; v8.mult.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); v8.mult.TOP_K=100
    baseline_full=v8.mult.evaluate_order(hidden_labels,seeds,order); p7_full=v8.mult.evaluate_order(hidden_labels,expanded,order)
    v8_result=json.loads(a.v8_result_json.read_text()); require(v8_result['verdict']=='PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT' and int(v8_result['family_count'])==EXPECTED_FAMILY_COUNT,'promoted-v8 prerequisite changed')
    baseline=v8_result['metrics']['multiplicity']
    exact={'eligible_labels':baseline['eligible_labels'],'qualified_matches':baseline['qualified_matches'],'recovered_at_100':baseline['recovered_at_100'],'recovered_at_500':baseline['recovered_at_500'],'mrr':baseline['mrr'],'median_rank':baseline['median_rank'],'macro_f1':baseline['macro_f1'],'top100_dominant_precision':baseline['top100_dominant_precision']}
    baseline_reproduced=all((abs(float(baseline_full[k])-float(v))<=1e-12 if isinstance(v,(int,float)) and v is not None else baseline_full[k]==v) for k,v in exact.items())
    require(int(baseline_full['qualified_matches'])==EXPECTED_BASELINE_QUALIFIED and int(baseline_full['recovered_at_100'])==EXPECTED_BASELINE_RECOVERY100,'reconstructed v8 coverage changed')
    require(abs(float(baseline_full['mrr'])-EXPECTED_BASELINE_MRR)<=1e-15 and abs(float(baseline_full['top100_dominant_precision'])-EXPECTED_BASELINE_TOP100_PRECISION)<=1e-12 and abs(float(baseline_full['macro_f1'])-EXPECTED_BASELINE_MACRO_F1)<=1e-12,'reconstructed v8 metric identity changed')

    totals=p2.label_totals(hidden_labels,v8.mult)
    large_labels={str(row['label']) for row in baseline_full['per_label'] if bool(row.get('qualified',False)) and totals.get(str(row['label']),0)>=LARGE_TOTAL_MIN}
    require(bool(large_labels),'no exact-v8 large-shower subset')
    baseline_large=p2.large_summary(baseline_full,totals,large_labels); p7_large=p2.large_summary(p7_full,totals,large_labels)
    gates={
        'exact_v8_226_family_order':len(expanded)==EXPECTED_FAMILY_COUNT and [str(f['family_id']) for f in expanded]==order,
        'exact_v8_seed_members_preserved':all(set(map(str,s['event_ids'])).issubset(set(map(str,e['event_ids']))) for s,e in zip(seeds,expanded)),
        'v8_baseline_reproduced':bool(baseline_reproduced),
        'exact_dsh_source_identity':sha256_file(a.dsh_comparator)==DSH_COMPARATOR_SHA256,
        'p7_membership_frozen_before_truth':a.p7_membership_sha.read_text().strip()==EXPECTED_P7_MEMBERSHIP_SHA,
        'p7_decisions_frozen_before_truth':a.p7_decisions_sha.read_text().strip()==EXPECTED_P7_DECISIONS_SHA,
        'p7_exact_year_seed_budget_identity':transform['budget_binding_family_year_cells']==EXPECTED_BINDING_CELLS and transform['retained_assignments']==EXPECTED_P7_ASSIGNMENTS,
        'p7_every_family_year_addition_count_le_seed_count':all(retained_counts.get((fid,year),0)<=int(rec['immutable_seed_count_by_year'][year]) for fid,rec in budgets.items() for year in map(str,YEARS)),
        'p7_strict_subset_of_p6':transform['retained_assignments']==EXPECTED_P7_ASSIGNMENTS and transform['dropped_assignments']==17163,
        'expansion_nonvacuous':EXPECTED_P7_ASSIGNMENTS>0,
        'qualified_matches_no_regression':int(p7_full['qualified_matches'])>=EXPECTED_BASELINE_QUALIFIED,
        'recovery_at_100_no_regression':int(p7_full['recovered_at_100'])>=EXPECTED_BASELINE_RECOVERY100,
        'top100_dominant_precision_at_least_065':float(p7_full['top100_dominant_precision'])>=TOP100_PRECISION_FLOOR,
        'macro_f1_gain_at_least_008':float(p7_full['macro_f1'])>=EXPECTED_BASELINE_MACRO_F1+MACRO_F1_GAIN_GATE,
        'large_shower_mean_recall_at_least_15x_v8':float(p7_large['mean_recall'])>=LARGE_RECALL_MULTIPLIER*float(baseline_large['mean_recall']),
        'large_shower_mean_precision_at_least_085':float(p7_large['mean_precision'])>=LARGE_PRECISION_FLOOR,
    }
    verdict='PASS_YEAR_SEED_BUDGET_MEMBERSHIP_P7_DEVELOPMENT' if all(gates.values()) else 'FAIL_YEAR_SEED_BUDGET_MEMBERSHIP_P7_NO_GO'
    result={
        'verdict':verdict,
        'classification':'artifact-only P6 membership with per-target-year additions capped by exact immutable-v8 seed evidence; immutable promoted-v8 cores and rank',
        'configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'v8_source_commit':V8_SOURCE_COMMIT,'family_count':EXPECTED_FAMILY_COUNT,'source_p6_run':31294731265,'source_p6_artifact_id':9032590228,'year_seed_budget_rule':'within each family/target-year, retained additions <= immutable v8 seeds in that year; strongest frozen responsibility/probability retained','parameter_search':False,'new_members_can_seed_growth':False,'ranking_after_membership':'unchanged exact promoted-v8 multiplicity order'},
        'hashes':{'source_p6_membership_sha256':EXPECTED_P6_MEMBERSHIP_SHA,'source_p6_decisions_sha256':EXPECTED_P6_DECISIONS_SHA,'p7_membership_pretruth_sha256':EXPECTED_P7_MEMBERSHIP_SHA,'p7_decisions_pretruth_sha256':EXPECTED_P7_DECISIONS_SHA},
        'baseline_v8':{k:v for k,v in baseline_full.items() if k!='per_label'},
        'p7':{k:v for k,v in p7_full.items() if k!='per_label'},
        'baseline_large_shower':baseline_large,'p7_large_shower':p7_large,'gates':gates,
        'diagnostics':{'artifact_only_transform':True,'source_p6_assignments':21626,'dropped_p6_assignments':17163,'assigned_nonseed_events':EXPECTED_P7_ASSIGNMENTS,'families_gaining_members':EXPECTED_GAINING_FAMILIES,'budget_binding_family_year_cells':EXPECTED_BINDING_CELLS,'budget_binding_families':EXPECTED_BINDING_FAMILIES},
        'claim_boundary':'Target-excluded development only. P7 membership/decisions were deterministically frozen from immutable P6 pretruth artifacts before known-shower truth was reopened; no detector refit, rescore, rerank or target access occurred.',
    }
    (a.output/'year_seed_budget_membership_p7_development.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (a.output/'YEAR_SEED_BUDGET_MEMBERSHIP_P7_DEVELOPMENT.md').write_text(
        '# OrbitTrace P7 per-year immutable-seed evidence-budget membership development\n\n'
        f'Verdict: **`{verdict}`**\n\n'
        f"- v8 -> P7 macro F1: **{baseline_full['macro_f1']:.6f} -> {p7_full['macro_f1']:.6f}**\n"
        f"- v8 -> P7 qualified: **{baseline_full['qualified_matches']} -> {p7_full['qualified_matches']}**\n"
        f"- v8 -> P7 recovery@100: **{baseline_full['recovered_at_100']} -> {p7_full['recovered_at_100']}**\n"
        f"- v8 -> P7 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p7_full['top100_dominant_precision']:.6f}**\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p7_large['mean_recall']:.6f}**\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p7_large['mean_precision']:.6f}**\n"
        f'- retained P7 additions: **{EXPECTED_P7_ASSIGNMENTS:,}**; dropped P6 assignments: **17,163**\n'
        f'- P7 membership SHA-256: `{EXPECTED_P7_MEMBERSHIP_SHA}`\n'
        f'- P7 decisions SHA-256: `{EXPECTED_P7_DECISIONS_SHA}`\n\n'
        'No OrbitTrace target information or target-region event was used.\n'
    )
    print((a.output/'YEAR_SEED_BUDGET_MEMBERSHIP_P7_DEVELOPMENT.md').read_text(),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
