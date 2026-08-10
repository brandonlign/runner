#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from orbittrace_v29_purity_diversity_sonotaco_canonical_v1 import run_candidate_pretruth as v29

GMN_YEARS=(2022,2023)
GMN_MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in GMN_YEARS for m in range(1,13))
SONO_YEARS=(2013,2014)
BLIND=(20.0,55.0)
EXPECTED_GMN={'hard':226,'p19':1075,'p20':3203,'union':4504}
EXPECTED_SONO={'hard':25,'p19':84,'p20':225,'union':334}
SONO_BASE_SHA={2013:'f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce',2014:'1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00'}
SONO_BASE_COUNTS={2013:24899,2014:20575}
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
PURITY_SHA='7bbaa13b90ba10eb41f708b5aec6ebebd83e9c7c34018aa3f973b4aec086b96a'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
RAW_977={'recovered_at_25':24,'recovered_at_50':47,'recovered_at_100':82,'recovered_at_500':165,'qualified_matches':256,'top100_dominant_precision':0.8558407874228419,'mrr':0.021025165849542556}
DOMAIN_AUC_990=0.88356922921475
PURITY_SPEC={'kind':'hgb','leaves':31}
SOURCES=('hard','p19','p20')
FEATURE_DIM=21


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def trimmed(m:dict[str,Any])->dict[str,Any]: return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def assert_metrics(m:dict[str,Any],expected:dict[str,Any],name:str)->None:
    for k,v in expected.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-12,f'{name} mismatch {k}: {m[k]} != {v}')
        else: req(int(m[k])==int(v),f'{name} mismatch {k}: {m[k]} != {v}')
def digest_key(s:str)->tuple[str,str]: return (hashlib.sha256(s.encode()).hexdigest(),s)
def domain_model()->HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(learning_rate=0.05,max_iter=250,max_leaf_nodes=31,l2_regularization=1.0,random_state=20260809)
def assign_domain_folds(domains:np.ndarray,sources:np.ndarray,ids:list[str])->np.ndarray:
    folds=np.full(len(ids),-1,dtype=int)
    for d in (0,1):
        for source in SOURCES:
            idx=[i for i in range(len(ids)) if int(domains[i])==d and str(sources[i])==source]
            idx=sorted(idx,key=lambda i:digest_key(ids[i]))
            req(len(idx)>=5,f'domain/source stratum too small: {d}/{source}={len(idx)}')
            for k,i in enumerate(idx): folds[i]=k%5
    req(bool(np.all(folds>=0)),'domain fold assignment incomplete')
    return folds
def balanced_domain_weights(domain:np.ndarray,mask:np.ndarray)->np.ndarray:
    out=np.zeros(len(domain),dtype=float); n=int(np.sum(mask)); n0=int(np.sum(mask&(domain==0))); n1=int(np.sum(mask&(domain==1)))
    req(n0>0 and n1>0,'domain balance empty')
    out[mask&(domain==0)]=n/(2.0*n0); out[mask&(domain==1)]=n/(2.0*n1); return out
def normalize_overlap(base_weights:np.ndarray,p_target:np.ndarray)->tuple[np.ndarray,float]:
    req(base_weights.shape==p_target.shape and np.isfinite(p_target).all(),'overlap inputs invalid')
    req(bool(np.all((p_target>=0.0)&(p_target<=1.0))),'target probabilities outside [0,1]')
    denom=float(np.sum(base_weights*p_target)); total=float(np.sum(base_weights)); req(denom>0.0 and total>0.0,'overlap normalization degenerate')
    c=total/denom; out=base_weights*p_target*c; req(np.isfinite(out).all() and float(np.sum(out))>0.0,'adapted weights invalid')
    req(abs(float(np.sum(out))-total)<=1e-9*max(1.0,total),'adapted total weight changed')
    return out,c


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--purity-source',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed'); req(sha(a.purity_source)==PURITY_SHA,'#840 purity source changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 inputs changed')
    req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 inputs changed')
    qmod=load_module(a.quality_source,'frozen_839_overlap'); pmod=load_module(a.purity_source,'frozen_840_overlap')

    # Exact target-excluded GMN 21D source-blind representation and GMN truth.
    p19_payload=json.loads(a.p19_prelabel_json.read_text()); p20_payload=json.loads(a.p20_prelabel_json.read_text())
    hard=p19_payload['hard_families']; s19=p19_payload['soft_families']; s20=p20_payload['soft_families']; hard_order=list(map(str,p19_payload['hard_order']))
    fams=hard+s19+s20; req({'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)}==EXPECTED_GMN,'GMN family universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'GMN family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})
    hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}
    qmod.v1.mult.YEARS=GMN_YEARS; qmod.v1.mult.MONTH_KEYS=GMN_MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); gsupport=runtime.load_support_module(a.support_source_parts)
    gsupport.YEARS=GMN_YEARS; gsupport.MONTH_KEYS=GMN_MONTH_KEYS; gsupport.CORPUS='orbittrace-target-overlap-sourceblind-adaptation-v1'; gsupport.RANKING_VARIANTS=('persistence',)
    req((float(gsupport.BLIND_LOW),float(gsupport.BLIND_HIGH))==BLIND,'GMN target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,gbase,_scorer=gsupport.load_sources(a)
    gscan,_cal,glabels,gsources=gsupport.parse_catalogue(gbase); req(sorted(gscan)==list(GMN_YEARS) and [x['key'] for x in gsources]==list(GMN_MONTH_KEYS),'GMN panel changed')
    pmod.v1.mult.YEARS=GMN_YEARS; pmod.v1.mult.MONTH_KEYS=GMN_MONTH_KEYS; pmod.v1.mult.TOP_K=100; pmod.v1.YEARS=GMN_YEARS; pmod.v1.MONTH_KEYS=GMN_MONTH_KEYS; pmod.v2.YEARS=GMN_YEARS
    feature_names=list(map(str,pmod.v2.FEATURE_NAMES)); req(len(feature_names)==FEATURE_DIM,'generic feature interface changed')
    glookup=pmod.v2.event_lookup(gscan)
    gx=np.asarray([pmod.v1.structural_features(f,hard_rank)+pmod.v2.cohesion_features(f,glookup,gsupport,gbase) for f in fams],dtype=float)
    req(gx.shape==(EXPECTED_GMN['union'],FEATURE_DIM) and np.isfinite(gx).all(),'GMN generic features invalid')
    gsrc=np.asarray([source[fid] for fid in ids],dtype=object)
    eligible=qmod.v1.eligible_labels(glabels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],glabels,eligible) for fid in ids}
    yp=np.asarray([int(truths[fid]['positive']) for fid in ids],dtype=int); req(np.unique(yp).size==2,'GMN purity target degenerate')
    groups=[pmod.strict_group(fid,truths[fid]) for fid in ids]; purity_folds=np.asarray([pmod.v2.deterministic_fold(g) for g in groups],dtype=int); base_weights=pmod.v2.diversity_weights(ids,truths,yp)
    cm=qmod.centroid_matrix(fams); tie=[(hard_rank.get(fid,999999),fid) for fid in ids]

    # Exact canonical label-free SonotaCo 21D seed-family representation; no shower truth exists here.
    raw={}
    for year in SONO_YEARS:
        path=a.prepared/f'base_{year}.json'; req(path.is_file(),f'missing canonical SonotaCo base {year}'); req(sha(path)==SONO_BASE_SHA[year],f'SonotaCo base hash changed {year}')
        rows=json.loads(path.read_text()); req(len(rows)==SONO_BASE_COUNTS[year] and all(int(r['year'])==year for r in rows),f'SonotaCo rows changed {year}')
        forbidden={'label','shower','truth','known_shower','native_background','sporadic'}; req(all(not (forbidden & {str(k).lower() for k in row}) for row in rows),'truth-bearing SonotaCo detector input')
        raw[year]=rows
    canonical=v29.v15_application.validate_pair(SONO_YEARS,raw)
    sruntime,ssupport,sbase,_=v29.load_support_base(p19_module=type('Shim',(),{'mult':v29.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    v29.generators.configure_pair(SONO_YEARS,support=ssupport,mult=v29.MULT,v6=v29.v6,v8=v29.v8,p19=v29.p19,p20=v29.p20); req((float(ssupport.BLIND_LOW),float(ssupport.BLIND_HIGH))==BLIND,'SonotaCo runtime firewall changed')
    ssupport.CORPUS=v29.p19.CORPUS
    shard=v29.build_hard_with_v15_order(scan_by_year=canonical,support=ssupport,base=sbase,runtime=sruntime)
    sp19,_p19diag=v29.generators.build_p19_pair(years=SONO_YEARS,hard=shard,scan_by_year=canonical,support=ssupport,base=sbase,p19=v29.p19)
    sp20_result=v29.generators.build_p20_pair(years=SONO_YEARS,hard=shard,scan_by_year=canonical,support=ssupport,base=sbase,p20=v29.p20); sp20=sp20_result['soft_families']
    sfams=shard['hard_families']+sp19+sp20; req({'hard':len(shard['hard_families']),'p19':len(sp19),'p20':len(sp20),'union':len(sfams)}==EXPECTED_SONO,'SonotaCo family universe changed')
    sids=[str(f['family_id']) for f in sfams]; req(len(set(sids))==len(sids),'SonotaCo family IDs collide')
    ssource={str(f['family_id']):'hard' for f in shard['hard_families']}; ssource.update({str(f['family_id']):'p19' for f in sp19}); ssource.update({str(f['family_id']):'p20' for f in sp20})
    shard_rank={fid:i+1 for i,fid in enumerate(shard['hard_order'])}
    slookup={str(row['id']):row for year in SONO_YEARS for row in canonical[year]}; req(len(slookup)==sum(len(canonical[y]) for y in SONO_YEARS),'SonotaCo event IDs collide')
    expected_hard=int(pmod.v1.EXPECTED_HARD); req(expected_hard==226,'historical hard-rank scale changed')
    sx=np.asarray([v29.portable_structural_features(f,shard_rank,slookup,expected_hard)+v29.portable_cohesion_features(f,slookup,ssupport,sbase) for f in sfams],dtype=float)
    req(sx.shape==(EXPECTED_SONO['union'],FEATURE_DIM) and np.isfinite(sx).all(),'SonotaCo generic features invalid')
    ssrc=np.asarray([ssource[fid] for fid in sids],dtype=object)

    # Reproduce #990 domain OOF and obtain bounded target-overlap multipliers for GMN.
    dx=np.vstack([gx,sx]); domain=np.r_[np.zeros(len(gx),dtype=int),np.ones(len(sx),dtype=int)]; dsource=np.r_[gsrc,ssrc]
    dids=[f'GMN/{fid}' for fid in ids]+[f'SONOTACO/{fid}' for fid in sids]; dfolds=assign_domain_folds(domain,dsource,dids); dpred=np.zeros(len(dids),dtype=float)
    for fold in range(5):
        tr=dfolds!=fold; te=dfolds==fold; req(tr.any() and te.any(),'domain CV fold empty')
        dw=balanced_domain_weights(domain,tr); model=domain_model(); model.fit(dx[tr],domain[tr],sample_weight=dw[tr]); dpred[te]=model.predict_proba(dx[te])[:,1]
    req(np.isfinite(dpred).all() and np.all((dpred>=0.0)&(dpred<=1.0)),'domain probabilities invalid')
    domain_auc=float(roc_auc_score(domain,dpred)); req(abs(domain_auc-DOMAIN_AUC_990)<1e-12,f'#990 domain AUC mismatch: {domain_auc}')
    p_target_oof=np.ascontiguousarray(dpred[:len(gx)]); adapted_weights,overlap_norm=normalize_overlap(base_weights,p_target_oof)

    # Exact raw #977 control and sole target-overlap-weighted candidate.
    def purity_oof(weights:np.ndarray)->np.ndarray:
        out=np.zeros(len(ids),dtype=float)
        for fold in range(5):
            tr=purity_folds!=fold; te=purity_folds==fold; req(tr.any() and te.any() and np.unique(yp[tr]).size==2,f'invalid purity fold {fold}')
            model=pmod.fit(pmod.make_model(PURITY_SPEC),gx[tr],yp[tr],weights[tr]); out[te]=pmod.probability(model,gx[te])
            req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'purity group leakage {fold}')
        return out
    raw_oof=purity_oof(base_weights); adapted_oof=purity_oof(adapted_weights)
    raw_order=[ids[i] for i in qmod.diversity_order(raw_oof,cm,0.8,1.0,tie)]; adapted_order=[ids[i] for i in qmod.diversity_order(adapted_oof,cm,0.8,1.0,tie)]
    raw_metrics=qmod.v1.monotone_metrics(fams,raw_order,truths,eligible); assert_metrics(raw_metrics,RAW_977,'#977 raw source-blind control')
    adapted_metrics=qmod.v1.monotone_metrics(fams,adapted_order,truths,eligible)
    hard_metrics=qmod.v1.monotone_metrics(hard,hard_order,{fid:truths[fid] for fid in hard_order},eligible)
    viable=bool(int(adapted_metrics['recovered_at_100'])>=75 and int(adapted_metrics['recovered_at_50'])>=int(hard_metrics['recovered_at_50']) and float(adapted_metrics['top100_dominant_precision'])>=float(hard_metrics['top100_dominant_precision'])-0.05 and int(adapted_metrics['qualified_matches'])>=230)

    full={'verdict':'NOT_FROZEN_TARGET_OVERLAP_GUARD_FAIL','purity_model_sha256':None,'domain_model_sha256':None}
    if viable:
        allmask=np.ones(len(domain),dtype=bool); dw=balanced_domain_weights(domain,allmask); dmodel=domain_model(); dmodel.fit(dx,domain,sample_weight=dw)
        pfull=np.asarray(dmodel.predict_proba(gx)[:,1],dtype=float); full_weights,full_norm=normalize_overlap(base_weights,pfull)
        pmodel=pmod.fit(pmod.make_model(PURITY_SPEC),gx,yp,full_weights)
        dpath=a.output/'target_domain_hgb31.joblib'; ppath=a.output/'target_overlap_sourceblind_purity_hgb31.joblib'; joblib.dump(dmodel,dpath); joblib.dump(pmodel,ppath)
        full={'verdict':'PASS_TARGET_OVERLAP_PRETRUTH_MODEL_FREEZE','purity_model_sha256':sha(ppath),'domain_model_sha256':sha(dpath),'feature_dimension':FEATURE_DIM,'feature_names':feature_names,'feature_name_sha256':hashlib.sha256('\n'.join(feature_names).encode()).hexdigest(),'gmn_training_examples':len(gx),'sonotaco_unlabeled_examples':len(sx),'positive_examples':int(yp.sum()),'gmn_feature_sha256':array_sha(gx),'sonotaco_feature_sha256':array_sha(sx),'target_sha256':array_sha(yp),'base_weight_sha256':array_sha(base_weights),'full_target_probability_sha256':array_sha(pfull),'adapted_weight_sha256':array_sha(full_weights),'full_overlap_normalization':full_norm,'deployment_diversity':{'lambda':0.8,'scale':1.0,'family_deletion':False,'complete_backfill':True}}

    result={
      'stage':'PRETRUTH_TARGET_OVERLAP_SOURCEBLIND_ADAPTATION_V1','verdict':'PASS_PRETRUTH_TARGET_OVERLAP_ADAPTATION_GUARD' if viable else 'FAIL_PRETRUTH_TARGET_OVERLAP_ADAPTATION_GUARD',
      'gmn_counts':EXPECTED_GMN,'sonotaco_counts':EXPECTED_SONO,'feature_dimension':FEATURE_DIM,'feature_names':feature_names,
      'domain_oof_roc_auc':domain_auc,'domain_oof_probability_sha256':array_sha(dpred),'gmn_target_overlap_probability_sha256':array_sha(p_target_oof),'overlap_rule':'bounded P(SonotaCo|x), no odds/clipping/exponent/calibration','overlap_normalization':overlap_norm,
      'raw_977_control':trimmed(raw_metrics),'hard_baseline':trimmed(hard_metrics),'adapted_candidate':trimmed(adapted_metrics),'adapted_order_sha256':order_sha(adapted_order),'viability_gate_pass':viable,
      'full_model_freeze':full,
      'sonotaco_label_free_covariates_used':True,'sonotaco_shower_truth_accessed':False,'literature_evaluation_performed':False,'matched_comparator_rows_used':False,
      'feature_subset_selected':False,'probability_cutoff_selected':False,'odds_transform_used':False,'weight_clipping_used':False,'weight_exponent_selected':False,'source_quota_selected':False,'source_routing_used_for_purity':False,'parameter_search':False,'post_result_second_search':False,
      'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND),
    }
    (a.output/'TARGET_OVERLAP_SOURCEBLIND_ADAPTATION_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (a.output/'FULL_MODEL_FREEZE.json').write_text(json.dumps(full,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'domain_oof_roc_auc':domain_auc,'raw_977_control':result['raw_977_control'],'hard_baseline':result['hard_baseline'],'adapted_candidate':result['adapted_candidate'],'viability_gate_pass':viable,'overlap_probability_summary':{'min':float(np.min(p_target_oof)),'q25':float(np.quantile(p_target_oof,0.25)),'median':float(np.median(p_target_oof)),'q75':float(np.quantile(p_target_oof,0.75)),'max':float(np.max(p_target_oof))},'full_model_freeze':full},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
