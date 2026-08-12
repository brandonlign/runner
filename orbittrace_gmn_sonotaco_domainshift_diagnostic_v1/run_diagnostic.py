#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import ks_2samp
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

from orbittrace_v29_purity_diversity_sonotaco_canonical_v1 import run_candidate_pretruth as v29

GMN_YEARS=(2022,2023)
GMN_MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in GMN_YEARS for m in range(1,13))
SONO_YEARS=(2013,2014)
SONO_BASE_SHA={2013:'f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce',2014:'1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00'}
SONO_BASE_COUNTS={2013:24899,2014:20575}
EXPECTED_GMN={'hard':226,'p19':1075,'p20':3203,'union':4504}
EXPECTED_SONO={'hard':25,'p19':84,'p20':225,'union':334}
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
PURITY_SHA='7bbaa13b90ba10eb41f708b5aec6ebebd83e9c7c34018aa3f973b4aec086b96a'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
SOURCES=('hard','p19','p20')
FEATURE_DIM=21


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()
def digest_key(s:str)->tuple[str,str]: return (hashlib.sha256(s.encode()).hexdigest(),s)
def quantiles(x:np.ndarray)->dict[str,float]:
    return {'q25':float(np.quantile(x,0.25)),'median':float(np.median(x)),'q75':float(np.quantile(x,0.75)),'iqr':float(np.quantile(x,0.75)-np.quantile(x,0.25))}
def domain_model()->HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(learning_rate=0.05,max_iter=250,max_leaf_nodes=31,l2_regularization=1.0,random_state=20260809)
def assign_folds(domains:np.ndarray,sources:np.ndarray,ids:list[str])->np.ndarray:
    folds=np.full(len(ids),-1,dtype=int)
    for d in (0,1):
        for source in SOURCES:
            idx=[i for i in range(len(ids)) if int(domains[i])==d and str(sources[i])==source]
            idx=sorted(idx,key=lambda i:digest_key(ids[i]))
            req(len(idx)>=5,f'domain/source stratum too small: {d}/{source}={len(idx)}')
            for k,i in enumerate(idx): folds[i]=k%5
    req(bool(np.all(folds>=0)),'fold assignment incomplete')
    return folds


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
    qmod=load_module(a.quality_source,'frozen_839_domainshift'); pmod=load_module(a.purity_source,'frozen_840_domainshift')

    # Exact target-excluded GMN 21D generic family representation; no shower truth is read.
    p19_payload=json.loads(a.p19_prelabel_json.read_text()); p20_payload=json.loads(a.p20_prelabel_json.read_text())
    ghard=p19_payload['hard_families']; gp19=p19_payload['soft_families']; gp20=p20_payload['soft_families']; ghard_order=list(map(str,p19_payload['hard_order']))
    gfams=ghard+gp19+gp20; req({'hard':len(ghard),'p19':len(gp19),'p20':len(gp20),'union':len(gfams)}==EXPECTED_GMN,'GMN family universe changed')
    gids=[str(f['family_id']) for f in gfams]; req(len(set(gids))==len(gids),'GMN family IDs collide')
    gsource={str(f['family_id']):'hard' for f in ghard}; gsource.update({str(f['family_id']):'p19' for f in gp19}); gsource.update({str(f['family_id']):'p20' for f in gp20})
    ghard_rank={fid:i+1 for i,fid in enumerate(ghard_order)}
    qmod.v1.mult.YEARS=GMN_YEARS; qmod.v1.mult.MONTH_KEYS=GMN_MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); gsupport=runtime.load_support_module(a.support_source_parts)
    gsupport.YEARS=GMN_YEARS; gsupport.MONTH_KEYS=GMN_MONTH_KEYS; gsupport.CORPUS='orbittrace-gmn-sonotaco-domainshift-diagnostic-v1'; gsupport.RANKING_VARIANTS=('persistence',)
    req((float(gsupport.BLIND_LOW),float(gsupport.BLIND_HIGH))==(20.0,55.0),'GMN target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,gbase,_scorer=gsupport.load_sources(a)
    gscan,_cal,_labels,gsources=gsupport.parse_catalogue(gbase); req(sorted(gscan)==list(GMN_YEARS) and [x['key'] for x in gsources]==list(GMN_MONTH_KEYS),'GMN panel changed')
    pmod.v1.mult.YEARS=GMN_YEARS; pmod.v1.mult.MONTH_KEYS=GMN_MONTH_KEYS; pmod.v1.mult.TOP_K=100; pmod.v1.YEARS=GMN_YEARS; pmod.v1.MONTH_KEYS=GMN_MONTH_KEYS; pmod.v2.YEARS=GMN_YEARS
    feature_names=list(map(str,pmod.v2.FEATURE_NAMES)); req(len(feature_names)==FEATURE_DIM,'generic feature interface changed')
    glookup=pmod.v2.event_lookup(gscan)
    gx=np.asarray([pmod.v1.structural_features(f,ghard_rank)+pmod.v2.cohesion_features(f,glookup,gsupport,gbase) for f in gfams],dtype=float)
    req(gx.shape==(EXPECTED_GMN['union'],FEATURE_DIM) and np.isfinite(gx).all(),'GMN generic feature matrix invalid')
    gsrc=np.asarray([gsource[fid] for fid in gids],dtype=object)

    # Canonical label-free SonotaCo seed-family representation. No ranking, membership expansion, truth, or comparator rows.
    raw={}
    for year in SONO_YEARS:
        path=a.prepared/f'base_{year}.json'; req(path.is_file(),f'missing canonical SonotaCo base {year}'); req(sha(path)==SONO_BASE_SHA[year],f'SonotaCo base hash changed {year}')
        rows=json.loads(path.read_text()); req(len(rows)==SONO_BASE_COUNTS[year] and all(int(r['year'])==year for r in rows),f'SonotaCo base rows changed {year}')
        forbidden={'label','shower','truth','known_shower','native_background','sporadic'}; req(all(not (forbidden & {str(k).lower() for k in row}) for row in rows),'truth-bearing field in canonical SonotaCo detector input')
        raw[year]=rows
    canonical=v29.v15_application.validate_pair(SONO_YEARS,raw)
    sruntime,ssupport,sbase,_=v29.load_support_base(p19_module=type('Shim',(),{'mult':v29.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    v29.generators.configure_pair(SONO_YEARS,support=ssupport,mult=v29.MULT,v6=v29.v6,v8=v29.v8,p19=v29.p19,p20=v29.p20); req((float(ssupport.BLIND_LOW),float(ssupport.BLIND_HIGH))==(20.0,55.0),'SonotaCo runtime firewall changed')
    ssupport.CORPUS=v29.p19.CORPUS
    shard=v29.build_hard_with_v15_order(scan_by_year=canonical,support=ssupport,base=sbase,runtime=sruntime)
    sp19,_p19diag=v29.generators.build_p19_pair(years=SONO_YEARS,hard=shard,scan_by_year=canonical,support=ssupport,base=sbase,p19=v29.p19)
    sp20_result=v29.generators.build_p20_pair(years=SONO_YEARS,hard=shard,scan_by_year=canonical,support=ssupport,base=sbase,p20=v29.p20); sp20=sp20_result['soft_families']
    sfams=shard['hard_families']+sp19+sp20; req({'hard':len(shard['hard_families']),'p19':len(sp19),'p20':len(sp20),'union':len(sfams)}==EXPECTED_SONO,'SonotaCo seed-family universe changed')
    sids=[str(f['family_id']) for f in sfams]; req(len(set(sids))==len(sids),'SonotaCo family IDs collide')
    ssource={str(f['family_id']):'hard' for f in shard['hard_families']}; ssource.update({str(f['family_id']):'p19' for f in sp19}); ssource.update({str(f['family_id']):'p20' for f in sp20})
    shard_rank={fid:i+1 for i,fid in enumerate(shard['hard_order'])}
    slookup={str(row['id']):row for year in SONO_YEARS for row in canonical[year]}; req(len(slookup)==sum(len(canonical[y]) for y in SONO_YEARS),'SonotaCo event IDs collide')
    expected_hard=int(pmod.v1.EXPECTED_HARD); req(expected_hard==226,'historical hard-rank scale changed')
    sx=np.asarray([v29.portable_structural_features(f,shard_rank,slookup,expected_hard)+v29.portable_cohesion_features(f,slookup,ssupport,sbase) for f in sfams],dtype=float)
    req(sx.shape==(EXPECTED_SONO['union'],FEATURE_DIM) and np.isfinite(sx).all(),'SonotaCo generic feature matrix invalid')
    ssrc=np.asarray([ssource[fid] for fid in sids],dtype=object)

    # Descriptive per-feature distribution shift only.
    feature_stats=[]
    for j,name in enumerate(feature_names):
        row={'feature':name,'gmn':quantiles(gx[:,j]),'sonotaco':quantiles(sx[:,j]),'ks_overall':float(ks_2samp(gx[:,j],sx[:,j],method='auto').statistic),'ks_by_source':{}}
        for source in SOURCES:
            ga=gx[gsrc==source,j]; sa=sx[ssrc==source,j]
            row['ks_by_source'][source]=float(ks_2samp(ga,sa,method='auto').statistic) if len(ga)>=5 and len(sa)>=5 else None
        feature_stats.append(row)

    # Five-fold cross-validated survey classifier. Folds are balanced within domain/source strata.
    x=np.vstack([gx,sx]); domain=np.r_[np.zeros(len(gx),dtype=int),np.ones(len(sx),dtype=int)]; source=np.r_[gsrc,ssrc]
    ids=[f'GMN/{x}' for x in gids]+[f'SONOTACO/{x}' for x in sids]
    folds=assign_folds(domain,source,ids); pred=np.zeros(len(ids),dtype=float)
    fold_meta={}
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any(),'domain CV fold empty')
        n0=int(np.sum(tr&(domain==0))); n1=int(np.sum(tr&(domain==1))); req(n0>0 and n1>0,'domain CV training domain empty')
        weights=np.zeros(len(ids),dtype=float); weights[tr&(domain==0)]=float(np.sum(tr))/(2.0*n0); weights[tr&(domain==1)]=float(np.sum(tr))/(2.0*n1)
        model=domain_model(); model.fit(x[tr],domain[tr],sample_weight=weights[tr]); pred[te]=model.predict_proba(x[te])[:,1]
        fold_meta[str(fold)]={'train_gmn':n0,'train_sonotaco':n1,'test_gmn':int(np.sum(te&(domain==0))),'test_sonotaco':int(np.sum(te&(domain==1)))}
    req(np.isfinite(pred).all() and np.all((pred>=0.0)&(pred<=1.0)),'domain probabilities invalid')
    overall_auc=float(roc_auc_score(domain,pred)); overall_bacc=float(balanced_accuracy_score(domain,pred>=0.5))
    by_source={}
    for s in SOURCES:
        mask=source==s; req(np.unique(domain[mask]).size==2,f'missing domain within source {s}')
        by_source[s]={'roc_auc':float(roc_auc_score(domain[mask],pred[mask])),'balanced_accuracy_at_0_5':float(balanced_accuracy_score(domain[mask],pred[mask]>=0.5)),'gmn_count':int(np.sum(mask&(domain==0))),'sonotaco_count':int(np.sum(mask&(domain==1)))}
    probability_strata={}
    for d,label in ((0,'gmn'),(1,'sonotaco')):
        probability_strata[label]={}
        for s in SOURCES:
            vals=pred[(domain==d)&(source==s)]; probability_strata[label][s]={'count':len(vals),'mean':float(np.mean(vals)),**quantiles(vals)}

    result={
        'stage':'GMN_SONOTACO_GENERIC_FEATURE_DOMAIN_SHIFT_DIAGNOSTIC_V1',
        'verdict':'PASS_TRUTH_FREE_DOMAIN_SHIFT_DIAGNOSTIC_COMPLETE',
        'gmn_counts':EXPECTED_GMN,'sonotaco_counts':EXPECTED_SONO,
        'feature_dimension':FEATURE_DIM,'feature_names':feature_names,
        'gmn_feature_sha256':array_sha(gx),'sonotaco_feature_sha256':array_sha(sx),
        'feature_stats':feature_stats,
        'domain_classifier':{'model':'HistGradientBoostingClassifier','learning_rate':0.05,'max_iter':250,'max_leaf_nodes':31,'l2_regularization':1.0,'random_state':20260809,'overall_roc_auc':overall_auc,'overall_balanced_accuracy_at_0_5':overall_bacc,'by_source':by_source,'folds':fold_meta,'probability_strata':probability_strata},
        'successor_defined':False,'scientific_ranker_trained':False,'weighting_rule_selected':False,'feature_subset_selected':False,'probability_cutoff_selected':False,'source_quota_selected':False,
        'sonotaco_shower_truth_accessed':False,'literature_evaluation_performed':False,'matched_comparator_rows_used':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,
    }
    (a.output/'GMN_SONOTACO_GENERIC_FEATURE_DOMAIN_SHIFT_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'gmn_counts':result['gmn_counts'],'sonotaco_counts':result['sonotaco_counts'],'overall_roc_auc':overall_auc,'overall_balanced_accuracy_at_0_5':overall_bacc,'by_source':by_source,'top_ks_features':sorted([{'feature':r['feature'],'ks':r['ks_overall']} for r in feature_stats],key=lambda z:(-z['ks'],z['feature']))[:8]},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
