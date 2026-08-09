#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import types
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
EXPECTED_FAMILY_COUNT=226
EXPECTED_MEMBERSHIP_SHA256="b077bc16e0a4792e5ae75a2be48801cd0a1404ee282856d73e99e891dfb93a6e"
EXPECTED_MODEL_SHA256="0cc5e2472f65e586cb18febffdbe3109e9e4041a6e09da07aa0bd4903a78c85f"
EXPECTED_DSH_SHA256="85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a"
EXPECTED_BASELINE_QUALIFIED=95
EXPECTED_BASELINE_RECOVERY100=58
EXPECTED_BASELINE_MRR=0.045531138942766655
EXPECTED_BASELINE_TOP100_PRECISION=0.6884631112636006
EXPECTED_BASELINE_MACRO_F1=0.1736657194465356
MACRO_F1_GAIN_GATE=0.08
TOP100_PRECISION_FLOOR=0.65
LARGE_TOTAL_MIN=100
LARGE_RECALL_MULTIPLIER=1.5
LARGE_PRECISION_FLOOR=0.85
LOGISTIC_MAX_ITER=1000


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load_module(path:Path,name:str)->types.ModuleType:
    require(path.is_file(),f"missing source {path}")
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f"cannot import {path}")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def load_families(path:Path)->list[dict[str,Any]]:
    rows=json.loads(gzip.decompress(path.read_bytes()).decode())
    require(isinstance(rows,list) and len(rows)==EXPECTED_FAMILY_COUNT,"P2 family count changed")
    return rows


def reconstruct_v8_seeds(expanded:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    baseline=[]; seen_additions=set(); total_additions=0; gaining=0
    for family in expanded:
        fid=str(family['family_id'])
        all_ids=set(map(str,family['event_ids']))
        additions=set(map(str,family.get('p2_added_event_ids',[])))
        require(int(family.get('p2_added_event_count',len(additions)))==len(additions),f"P2 addition count mismatch {fid}")
        require(additions.issubset(all_ids),f"P2 additions not subset {fid}")
        require(not (seen_additions & additions),f"P2 nonseed assigned to multiple families {fid}")
        seen_additions |= additions
        seeds=all_ids-additions
        require(seeds,f"empty v8 seed set {fid}")
        out=copy.deepcopy(family)
        out.pop('p2_added_event_ids',None);out.pop('p2_added_event_count',None)
        out['event_ids']=sorted(seeds);out['event_count']=len(seeds)
        baseline.append(out)
        total_additions+=len(additions);gaining+=int(bool(additions))
    return baseline,{
        'assigned_nonseed_events':total_additions,
        'families_gaining_members':gaining,
        'assigned_nonseed_ids_unique':len(seen_additions)==total_additions,
    }


def label_totals(hidden_labels:dict[str,str],mult:types.ModuleType)->dict[str,int]:
    eligible=mult.eligible_labels(hidden_labels)
    return {label:int(sum(per_year.values())) for label,per_year in eligible.items()}


def large_summary(metrics:dict[str,Any],totals:dict[str,int],subset:set[str])->dict[str,Any]:
    rows={str(r['label']):r for r in metrics['per_label']}; vals=[]
    for label in sorted(subset):
        row=rows[label]
        vals.append({'label':label,'total':totals[label],'qualified':bool(row.get('qualified',False)),'precision':float(row.get('precision',0.0)),'recall':float(row.get('recall',0.0)),'f1':float(row.get('f1',0.0))})
    return {
        'labels':len(vals),
        'mean_precision':float(np.mean([x['precision'] for x in vals])) if vals else 0.0,
        'mean_recall':float(np.mean([x['recall'] for x in vals])) if vals else 0.0,
        'mean_f1':float(np.mean([x['f1'] for x in vals])) if vals else 0.0,
        'qualified':sum(x['qualified'] for x in vals),
    }


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--p2-families',required=True,type=Path)
    p.add_argument('--p2-membership-sha',required=True,type=Path)
    p.add_argument('--p2-model',required=True,type=Path)
    p.add_argument('--p2-model-sha',required=True,type=Path)
    p.add_argument('--base-runner',required=True,type=Path)
    p.add_argument('--v8-runner',required=True,type=Path)
    p.add_argument('--dsh-comparator',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def main()->int:
    args=parse_args();args.output.mkdir(parents=True,exist_ok=True)
    membership_expected=args.p2_membership_sha.read_text().strip()
    model_expected=args.p2_model_sha.read_text().strip()
    require(membership_expected==EXPECTED_MEMBERSHIP_SHA256,f"unexpected frozen P2 membership SHA {membership_expected}")
    require(model_expected==EXPECTED_MODEL_SHA256,f"unexpected frozen P2 model SHA {model_expected}")
    expanded=load_families(args.p2_families)
    require(canonical_sha(expanded)==membership_expected,"frozen P2 membership payload hash mismatch")
    model=json.loads(args.p2_model.read_text())
    require(canonical_sha(model)==model_expected,"frozen P2 model payload hash mismatch")
    require(model['feature_order']==['d_obs','d_orb'],"P2 feature order changed")
    require(model['settings']['C']==1.0 and model['settings']['solver']=='lbfgs',"P2 logistic settings changed")
    require(model['settings']['max_iter']==LOGISTIC_MAX_ITER and model['settings']['tol']==1e-10,"P2 solver stopping rule changed")
    require(int(max(model['logistic_n_iter']))<LOGISTIC_MAX_ITER,"P2 frozen classifier did not converge")
    require(sha256_file(args.dsh_comparator)==EXPECTED_DSH_SHA256,"exact D_SH source identity changed")

    baseline_families,pretruth_diag=reconstruct_v8_seeds(expanded)
    order=[str(f['family_id']) for f in baseline_families]
    require(len(order)==EXPECTED_FAMILY_COUNT and len(set(order))==EXPECTED_FAMILY_COUNT,"family order invalid")

    # FIRST truth-capable catalogue load in this recovery occurs only after immutable
    # model + membership hashes and reconstructed seed membership are verified.
    old=load_module(args.base_runner,'orbittrace_p2_recovery_base')
    v8=load_module(args.v8_runner,'orbittrace_p2_recovery_v8')
    support=old.load_support_module(args.support_source_parts)
    source_args=types.SimpleNamespace(candidate_payload=args.candidate_payload,baseline_payload=args.baseline_payload,scorer_parts=args.scorer_parts)
    _,base,_=support.load_sources(source_args)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,"blind interval changed")
    scan_by_year,_,hidden_labels,sources=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),"development years changed")

    v8.mult.YEARS=YEARS;v8.mult.TOP_K=100
    baseline=v8.mult.evaluate_order(hidden_labels,baseline_families,order)
    p2=v8.mult.evaluate_order(hidden_labels,expanded,order)
    require(int(baseline['qualified_matches'])==EXPECTED_BASELINE_QUALIFIED,"v8 qualified baseline mismatch")
    require(int(baseline['recovered_at_100'])==EXPECTED_BASELINE_RECOVERY100,"v8 recovery baseline mismatch")
    require(abs(float(baseline['mrr'])-EXPECTED_BASELINE_MRR)<=1e-15,"v8 MRR baseline mismatch")
    require(abs(float(baseline['top100_dominant_precision'])-EXPECTED_BASELINE_TOP100_PRECISION)<=1e-12,"v8 precision baseline mismatch")
    require(abs(float(baseline['macro_f1'])-EXPECTED_BASELINE_MACRO_F1)<=1e-12,"v8 macro-F1 baseline mismatch")

    totals=label_totals(hidden_labels,v8.mult)
    large_labels={str(row['label']) for row in baseline['per_label'] if bool(row.get('qualified',False)) and totals.get(str(row['label']),0)>=LARGE_TOTAL_MIN}
    require(bool(large_labels),"empty frozen large-shower subset")
    baseline_large=large_summary(baseline,totals,large_labels)
    p2_large=large_summary(p2,totals,large_labels)

    gates={
        'exact_v8_226_family_order':len(expanded)==EXPECTED_FAMILY_COUNT and [str(f['family_id']) for f in expanded]==order,
        'exact_v8_seed_members_preserved':all(set(map(str,b['event_ids'])).issubset(set(map(str,x['event_ids']))) for b,x in zip(baseline_families,expanded)),
        'v8_baseline_reproduced':True,
        'exact_dsh_source_identity':sha256_file(args.dsh_comparator)==EXPECTED_DSH_SHA256,
        'model_frozen_before_truth_evaluation':canonical_sha(model)==EXPECTED_MODEL_SHA256,
        'membership_frozen_before_truth_evaluation':canonical_sha(expanded)==EXPECTED_MEMBERSHIP_SHA256,
        'classifier_converged':int(max(model['logistic_n_iter']))<LOGISTIC_MAX_ITER,
        'expansion_nonvacuous':int(pretruth_diag['assigned_nonseed_events'])>0,
        'qualified_matches_no_regression':int(p2['qualified_matches'])>=EXPECTED_BASELINE_QUALIFIED,
        'recovery_at_100_no_regression':int(p2['recovered_at_100'])>=EXPECTED_BASELINE_RECOVERY100,
        'top100_dominant_precision_at_least_065':float(p2['top100_dominant_precision'])>=TOP100_PRECISION_FLOOR,
        'macro_f1_gain_at_least_008':float(p2['macro_f1'])>=EXPECTED_BASELINE_MACRO_F1+MACRO_F1_GAIN_GATE,
        'large_shower_mean_recall_at_least_15x_v8':float(p2_large['mean_recall'])>=LARGE_RECALL_MULTIPLIER*float(baseline_large['mean_recall']),
        'large_shower_mean_precision_at_least_085':float(p2_large['mean_precision'])>=LARGE_PRECISION_FLOOR,
    }
    verdict='PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT' if all(gates.values()) else 'FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO'
    result={
        'verdict':verdict,
        'classification':'post-pretruth evaluation-only recovery of exact frozen canonical P2 membership; no membership recomputation',
        'configuration':{
            'years':list(YEARS),'blind_exclusion':[20.0,55.0],'family_count':EXPECTED_FAMILY_COUNT,
            'features':['cross-year source-seed OAS Mahalanobis observation distance','minimum exact D_SH to source-year immutable seed'],
            'window_half_width_deg':5.0,'negative_minimum_per_direction':128,
            'family_direction_class_total_weights':{'positive':0.5,'negative':0.5},
            'classifier':'LogisticRegression L2 C=1.0 lbfgs max_iter=1000 tol=1e-10',
            'background_odds_weight':1.0,'responsibility_threshold':0.5,
            'new_members_can_seed_growth':False,'ranking_after_membership':'unchanged exact promoted-v8 multiplicity order','parameter_search':False,
        },
        'sources':sources,
        'model_pretruth_sha256':model_expected,
        'membership_pretruth_sha256':membership_expected,
        'baseline_v8':{k:v for k,v in baseline.items() if k!='per_label'},
        'p2':{k:v for k,v in p2.items() if k!='per_label'},
        'baseline_large_shower':baseline_large,'p2_large_shower':p2_large,'gates':gates,
        'diagnostics':pretruth_diag,
        'recovery_provenance':{
            'source_run':31289333209,
            'header_recovery_run':31289791712,
            'header_recovery_artifact_id':9031107930,
            'header_recovery_artifact_digest':'sha256:62f3d547c1abd2f329b1d4a59f6603640ef11dba0497c1d63e1c4656e28d0486',
            'canonical_p2_source_sha256':'f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb',
            'header_wrapper_git_blob':'6acf42979bbbf733b51e103b995f2b39220af50d',
            'failure_after_membership_freeze':'NameError in diagnostics-only valid_nonseed_by_year field',
            'membership_recomputed':False,
            'model_refit':False,
        },
        'claim_boundary':'Target-excluded development only. This recovery evaluates the already-frozen P2 model/membership from the technical no-result; it changes no scientific operation or threshold.',
    }
    (args.output/'crossyear_two_view_membership_p2_development.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    summary=(
        '# OrbitTrace P2 post-pretruth evaluation recovery\n\n'
        f'Verdict: **`{verdict}`**\n\n'
        f"- v8 -> P2 macro F1: **{baseline['macro_f1']:.6f} -> {p2['macro_f1']:.6f}**\n"
        f"- v8 -> P2 qualified: **{baseline['qualified_matches']} -> {p2['qualified_matches']}**\n"
        f"- v8 -> P2 recovery@100: **{baseline['recovered_at_100']} -> {p2['recovered_at_100']}**\n"
        f"- v8 -> P2 top100 precision: **{baseline['top100_dominant_precision']:.6f} -> {p2['top100_dominant_precision']:.6f}**\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p2_large['mean_recall']:.6f}**\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p2_large['mean_precision']:.6f}**\n"
        f"- frozen assigned nonseed events: **{pretruth_diag['assigned_nonseed_events']:,}** across **{pretruth_diag['families_gaining_members']}** families\n"
        f'- model SHA-256: `{model_expected}`\n- membership SHA-256: `{membership_expected}`\n'
    )
    (args.output/'CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md').write_text(summary)
    print(summary,flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
