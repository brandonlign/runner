#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from orbittrace_v29_purity_diversity_sonotaco_canonical_v1 import run_candidate_pretruth as v29

YEARS=v29.YEARS
MONTH_KEYS=v29.MONTH_KEYS
MODEL_SHA='c886e6c9466130910fa918c168ea5a8b8ac05a4bf01cb9a5b570fef3cbe292cb'
FEATURE_NAME_SHA='e8507fbb8a2160485e7496bce9ec8d825cfeb248eac4533f5ce526e81e3cd861'
PURITY_SOURCE_SHA=v29.PURITY_SOURCE_SHA
QUALITY_SOURCE_SHA=v29.QUALITY_SOURCE_SHA
BASE_SHA=v29.BASE_SHA
BASE_COUNTS=v29.BASE_COUNTS
GENERIC_DIM=21


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--purity-source',type=Path,required=True)
    p.add_argument('--quality-source',type=Path,required=True)
    p.add_argument('--model-joblib',type=Path,required=True)
    p.add_argument('--model-manifest',type=Path,required=True)
    p.add_argument('--adaptation-result',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    v29.require(sha(a.purity_source)==PURITY_SOURCE_SHA,'#840 purity source changed')
    v29.require(sha(a.quality_source)==QUALITY_SOURCE_SHA,'#839 diversity source changed')
    v29.require(sha(a.model_joblib)==MODEL_SHA,'target-overlap purity model changed')
    mm=json.loads(a.model_manifest.read_text()); ar=json.loads(a.adaptation_result.read_text())
    v29.require(mm['verdict']=='PASS_TARGET_OVERLAP_PRETRUTH_MODEL_FREEZE','target-overlap full model was not frozen')
    v29.require(ar['verdict']=='PASS_PRETRUTH_TARGET_OVERLAP_ADAPTATION_GUARD','target-overlap pretruth gate did not pass')
    v29.require(mm['purity_model_sha256']==MODEL_SHA and mm['feature_dimension']==GENERIC_DIM,'target-overlap model identity changed')
    v29.require(mm['feature_name_sha256']==FEATURE_NAME_SHA,'target-overlap feature-name identity changed')
    v29.require(mm['deployment_diversity']=={'lambda':0.8,'scale':1.0,'family_deletion':False,'complete_backfill':True},'target-overlap diversity changed')
    v29.require(ar['feature_dimension']==GENERIC_DIM and ar['feature_subset_selected'] is False,'target-overlap feature boundary changed')
    v29.require(ar['probability_cutoff_selected'] is False and ar['odds_transform_used'] is False and ar['weight_clipping_used'] is False and ar['weight_exponent_selected'] is False,'target-overlap weighting rule changed')
    v29.require(ar['source_quota_selected'] is False and ar['source_routing_used_for_purity'] is False and ar['parameter_search'] is False and ar['post_result_second_search'] is False,'target-overlap no-search boundary changed')
    v29.require(ar['sonotaco_label_free_covariates_used'] is True and ar['sonotaco_shower_truth_accessed'] is False and ar['literature_evaluation_performed'] is False,'adaptation stage was not pretruth clean')
    v29.require(ar['target_information_access'] is False and ar['maarsy_scientific_access'] is False and ar['dms_scientific_access'] is False,'protected-data firewall changed')

    raw={}
    for year in YEARS:
        path=a.prepared/f'base_{year}.json'; v29.require(path.is_file(),f'missing canonical base {year}'); v29.require(sha(path)==BASE_SHA[year],f'canonical base hash changed {year}')
        rows=json.loads(path.read_text()); v29.require(len(rows)==BASE_COUNTS[year] and all(int(x['year'])==year for x in rows),f'canonical base rows changed {year}')
        forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
        v29.require(all(not (forbidden & {str(k).lower() for k in row}) for row in rows),'truth-bearing field in canonical detector input'); raw[year]=rows

    canonical=v29.v15_application.validate_pair(YEARS,raw)
    runtime,support,base,_=v29.load_support_base(p19_module=type('Shim',(),{'mult':v29.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    v29.generators.configure_pair(YEARS,support=support,mult=v29.MULT,v6=v29.v6,v8=v29.v8,p19=v29.p19,p20=v29.p20)
    v29.require((float(support.BLIND_LOW),float(support.BLIND_HIGH))==(20.0,55.0),'target firewall changed'); support.CORPUS=v29.p19.CORPUS

    hard=v29.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    p19_soft,p19_diag=v29.generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=v29.p19)
    p20_result=v29.generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=v29.p20); p20_soft=p20_result['soft_families']
    union=hard['hard_families']+p19_soft+p20_soft; ids=[str(f['family_id']) for f in union]; v29.require(len(set(ids))==len(ids),'union family IDs collide')
    source={str(f['family_id']):'hard' for f in hard['hard_families']}; source.update({str(f['family_id']):'p19' for f in p19_soft}); source.update({str(f['family_id']):'p20' for f in p20_soft}); v29.require(len(source)==len(union),'source map incomplete')
    hard_rank={fid:i+1 for i,fid in enumerate(hard['hard_order'])}

    pmod=v29.load_module(a.purity_source,'frozen_840_target_overlap_sonotaco'); qmod=v29.load_module(a.quality_source,'frozen_839_target_overlap_diversity')
    pmod.v1.mult.YEARS=YEARS; pmod.v1.mult.MONTH_KEYS=MONTH_KEYS; pmod.v1.mult.TOP_K=100; pmod.v1.YEARS=YEARS; pmod.v1.MONTH_KEYS=MONTH_KEYS; pmod.v2.YEARS=YEARS; qmod.YEARS=YEARS; qmod.MONTH_KEYS=MONTH_KEYS
    v29.require(tuple(mm['feature_names'])==tuple(pmod.v2.FEATURE_NAMES),'frozen target-overlap 21D feature names differ from exact generic #840 prefix')
    v29.require(tuple(ar['feature_names'])==tuple(pmod.v2.FEATURE_NAMES),'adaptation result generic feature names changed')

    lookup={str(row['id']):row for year in YEARS for row in canonical[year]}; v29.require(len(lookup)==sum(len(canonical[y]) for y in YEARS),'canonical event IDs are not unique')
    expected_hard=int(pmod.v1.EXPECTED_HARD); v29.require(expected_hard==226,'#840 hard-rank feature scale changed')
    x=np.asarray([v29.portable_structural_features(f,hard_rank,lookup,expected_hard)+v29.portable_cohesion_features(f,lookup,support,base) for f in union],dtype=float)
    v29.require(x.shape==(len(union),GENERIC_DIM) and np.isfinite(x).all(),'target-overlap application features invalid')

    model=joblib.load(a.model_joblib); scores=np.asarray(pmod.probability(model,x),dtype=float); v29.require(scores.shape==(len(union),) and np.isfinite(scores).all(),'target-overlap purity probabilities invalid')
    cm=qmod.centroid_matrix(union); tie=[(hard_rank.get(fid,999999),fid) for fid in ids]; idx=qmod.diversity_order(scores,cm,0.8,1.0,tie); order=[ids[i] for i in idx]; v29.require(set(order)==set(ids) and len(order)==len(ids),'target-overlap diversity order incomplete')

    by={str(f['family_id']):f for f in union}; ordered=[]
    for rank,fid in enumerate(order,start=1): ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,by[fid]['event_ids']))),'source':source[fid]})
    expanded,membership_diag=v29.expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)

    primary={
      'method':'OrbitTrace target-overlap adapted source-blind purity HGB31 + exact #839 diversity + exact #461 top100 membership expansion',
      'input_role':'single canonical SonotaCo base pair; no comparator-specific detector input','years':list(YEARS),'canonical_base_counts':BASE_COUNTS,'family_count':len(expanded),'families':expanded,
      'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
      'hard_order_sha256':v29.canonical_sha(hard['hard_order']),'seed_family_order_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
      'sourceblind_feature_sha256':v29.array_sha(x),'target_overlap_probability_sha256':v29.array_sha(scores),'target_overlap_order_sha256':order_sha(order),
      'target_overlap_model_sha256':MODEL_SHA,'feature_dimension':GENERIC_DIM,'feature_name_sha256':FEATURE_NAME_SHA,'source_specific_features_used':False,
      'adaptation_rule':'bounded P(SonotaCo|x) training overlap weight frozen pretruth in PR #993; no application-time adaptation',
      'model_trained_with_sonotaco_label_free_covariates':True,'model_trained_with_sonotaco_shower_truth':False,
      'purity_source_sha256':PURITY_SOURCE_SHA,'diversity_source_sha256':QUALITY_SOURCE_SHA,'membership_diagnostics':membership_diag,'p19_diagnostics':p19_diag,'p20_diagnostics':p20_result['soft_diagnostics'],
      'feature_schema_adapter':'exact #839/#840 generic formulas with canonical row year and application-pair centroid keys; no feature/order/scale change',
      'matched_comparator_rows_accessed':False,'truth_accessed':False,'model_retrained_on_sonotaco':False,'panel_specific_ranking':False,
      'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    primary_sha=v29.dump(a.output/'TARGET_OVERLAP_CANONICAL_PRETRUTH_CATALOGUE.json',primary)
    summary={'verdict':'PASS_TARGET_OVERLAP_CANONICAL_SONOTACO_PRETRUTH_CATALOGUE_FREEZE','primary_output_sha256':primary_sha,'family_count':len(expanded),'candidate_counts':primary['candidate_counts'],'membership_total_new':membership_diag['total_new_members'],'target_overlap_order_sha256':primary['target_overlap_order_sha256'],'feature_dimension':GENERIC_DIM,'source_specific_features_used':False,'feature_schema_adapter':primary['feature_schema_adapter'],'model_trained_with_sonotaco_label_free_covariates':True,'model_trained_with_sonotaco_shower_truth':False,'matched_comparator_rows_accessed':False,'truth_accessed':False,'model_retrained_on_sonotaco':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    v29.dump(a.output/'TARGET_OVERLAP_CANONICAL_PRETRUTH_SUMMARY.json',summary); print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
