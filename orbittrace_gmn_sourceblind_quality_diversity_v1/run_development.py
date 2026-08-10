#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED=(226,1075,3203,4504)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
QUALITY_CONTROL={'recovered_at_25':22,'recovered_at_50':40,'recovered_at_100':75,'recovered_at_500':159,'qualified_matches':256,'top100_dominant_precision':0.7645689180574315,'mrr':0.019037817654898162}
SOURCE_SUFFIX=('is_hard','is_p19_soft','is_p20_soft','p20_cross_year_distance','log_p20_min_anchor','p20_min_bin_strength','p20_min_quartet_score')
NEIGHBOR_NAMES=('neighbor_log_count_025','neighbor_log_count_050','neighbor_log_count_100','neighbor_log_count_150','neighbor_nearest_distance','neighbor_median5_distance')
GENERIC_DIM=21
SOURCEBLIND_DIM=27


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def metric_key(m:dict[str,Any])->tuple[float,...]: return (float(m['recovered_at_100']),float(m['recovered_at_50']),float(m['recovered_at_25']),float(m['top100_dominant_precision']),float(m['mrr']))
def trimmed(m:dict[str,Any])->dict[str,Any]: return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def assert_metrics(m:dict[str,Any],expected:dict[str,Any],name:str)->None:
    for k,v in expected.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-12,f'{name} mismatch {k}: {m[k]} != {v}')
        else: req(int(m[k])==int(v),f'{name} mismatch {k}: {m[k]} != {v}')


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 inputs changed')
    req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 inputs changed')
    qmod=load_module(a.quality_source,'frozen_839_sourceblind_quality')

    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; hard_order=list(map(str,p19['hard_order'])); fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})
    hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-sourceblind-quality-diversity-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN panel changed')

    eligible=qmod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    lookup=qmod.v2.event_lookup(scan); cm=qmod.centroid_matrix(fams); nf=qmod.neighbor_features(cm)
    req(nf.shape==(len(fams),6) and np.isfinite(nf).all(),'neighbor feature matrix changed')
    req(len(tuple(qmod.v2.FEATURE_NAMES))==GENERIC_DIM,'generic #839 feature prefix changed')
    generic=[]; full=[]
    for i,f in enumerate(fams):
        fid=str(f['family_id']); src=source[fid]
        g=qmod.v1.structural_features(f,hard_rank)+qmod.v2.cohesion_features(f,lookup,support,base)
        req(len(g)==GENERIC_DIM,'generic feature dimension changed')
        srcf=[float(src=='hard'),float(src=='p19'),float(src=='p20')]
        p20f=[float(f.get('p20_cross_year_distance',0.0)),math.log1p(max(int(f.get('p20_min_anchor_count',0)),0)),float(f.get('p20_min_bin_strength',0.0)),float(f.get('p20_min_quartet_score',0.0))]
        generic.append(g+nf[i].tolist()); full.append(g+srcf+p20f+nf[i].tolist())
    x27=np.asarray(generic,float); x34=np.asarray(full,float)
    req(x27.shape==(len(fams),SOURCEBLIND_DIM) and x34.shape==(len(fams),34),'quality feature dimensions changed')
    req(np.isfinite(x27).all() and np.isfinite(x34).all(),'quality features nonfinite')
    feature_names=list(qmod.v2.FEATURE_NAMES)+list(NEIGHBOR_NAMES); req(len(feature_names)==SOURCEBLIND_DIM,'source-blind feature names invalid')

    target=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],float)
    groups=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]
    folds=np.asarray([qmod.v1.deterministic_fold(g) for g in groups],int); weights=qmod.grouped_weights(groups)
    tie=[(hard_rank.get(fid,999999),fid) for fid in ids]

    def oof(x:np.ndarray)->np.ndarray:
        out=np.zeros(len(ids),float)
        for fold in range(5):
            tr=folds!=fold; te=folds==fold; req(tr.any() and te.any(),f'empty fold {fold}')
            m=qmod.model(); m.fit(x[tr],target[tr],sample_weight=weights[tr]); out[te]=m.predict(x[te])
            req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage {fold}')
        return out

    o34=oof(x34); o27=oof(x27)
    order34=[ids[i] for i in qmod.diversity_order(o34,cm,0.8,1.0,tie)]
    order27=[ids[i] for i in qmod.diversity_order(o27,cm,0.8,1.0,tie)]
    m34=qmod.v1.monotone_metrics(fams,order34,truths,eligible); assert_metrics(m34,QUALITY_CONTROL,'#839 quality control')
    m27=qmod.v1.monotone_metrics(fams,order27,truths,eligible)
    hard_metrics=qmod.v1.monotone_metrics(hard,hard_order,{fid:truths[fid] for fid in hard_order},eligible)
    viable=bool(int(m27['recovered_at_100'])>=75 and int(m27['recovered_at_50'])>=int(hard_metrics['recovered_at_50']) and float(m27['top100_dominant_precision'])>=float(hard_metrics['top100_dominant_precision'])-0.05 and int(m27['qualified_matches'])>=230)
    strict=bool(metric_key(m27)>metric_key(m34)); passed=bool(viable and strict)

    freeze={'verdict':'NOT_FROZEN_SOURCEBLIND_QUALITY_GMN_FAIL','model_sha256':None}
    if passed:
        model=qmod.model(); model.fit(x27,target,sample_weight=weights); path=a.output/'orbittrace_sourceblind_gmn_quality_extra.joblib'; joblib.dump(model,path)
        freeze={'verdict':'PASS_SOURCEBLIND_QUALITY_GMN_MODEL_FREEZE','model_sha256':sha(path),'feature_dimension':SOURCEBLIND_DIM,'feature_names':feature_names,'feature_name_sha256':hashlib.sha256('\n'.join(feature_names).encode()).hexdigest(),'training_examples':len(ids),'positive_target_examples':int(np.sum(target>0)),'training_feature_sha256':array_sha(x27),'target_sha256':array_sha(target),'weights_sha256':array_sha(weights),'deployment_diversity':{'lambda':0.8,'scale':1.0,'family_deletion':False,'complete_backfill':True}}

    result={
        'stage':'GMN_TARGET_EXCLUDED_SOURCEBLIND_QUALITY_DIVERSITY_V1','verdict':'PASS_GMN_SOURCEBLIND_QUALITY_DIVERSITY_V1' if passed else 'FAIL_GMN_SOURCEBLIND_QUALITY_DIVERSITY_V1',
        'candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},'eligible_labels':len(eligible),
        'quality34_839_control':trimmed(m34),'sourceblind27':trimmed(m27),'sourceblind27_order_sha256':order_sha(order27),'sourceblind27_viable':viable,'strict_improvement_over_839':strict,
        'generic_feature_dimension':GENERIC_DIM,'neighbor_feature_dimension':6,'sourceblind_feature_dimension':SOURCEBLIND_DIM,'sourceblind_feature_names':feature_names,'removed_source_suffix':list(SOURCE_SUFFIX),'source_specific_features_used':False,
        'full_model_freeze':freeze,'parameter_search':False,'partial_source_feature_restoration':False,'source_quota_selected':False,'family_deletion':False,
        'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND),
    }
    (a.output/'GMN_SOURCEBLIND_QUALITY_DIVERSITY_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (a.output/'FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'quality34_839_control':result['quality34_839_control'],'sourceblind27':result['sourceblind27'],'viable':viable,'strict_improvement_over_839':strict,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
