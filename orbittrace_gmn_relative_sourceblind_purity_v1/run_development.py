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
from scipy.stats import rankdata

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED=(226,1075,3203,4504)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
PURITY_BLOB='976ae788ec76a2da7035735ea62118c7289adc5e'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
QUALITY_CONTROL={'recovered_at_25':22,'recovered_at_50':40,'recovered_at_100':75,'recovered_at_500':159,'qualified_matches':256,'top100_dominant_precision':0.7645689180574315,'mrr':0.019037817654898162}
RAW21_CONTROL={'recovered_at_25':24,'recovered_at_50':47,'recovered_at_100':82,'recovered_at_500':165,'qualified_matches':256,'top100_dominant_precision':0.8558407874228419,'mrr':0.021025165849542556}
PURITY_SPEC={'kind':'hgb','leaves':31}
GENERIC_DIM=21
CATEGORICAL_COLUMNS={0}


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
def relative_transform(x:np.ndarray)->np.ndarray:
    x=np.asarray(x,dtype=np.float64); req(x.ndim==2 and x.shape[1]==GENERIC_DIM and len(x)>=2 and np.all(np.isfinite(x)),'invalid raw source-blind feature matrix')
    out=np.empty_like(x); den=float(len(x)-1)
    for j in range(x.shape[1]):
        if j in CATEGORICAL_COLUMNS: out[:,j]=x[:,j]
        else: out[:,j]=(rankdata(x[:,j],method='average')-1.0)/den
    req(np.all(np.isfinite(out)),'relative transform nonfinite'); return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--purity-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 inputs changed')
    req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 inputs changed')
    qmod=load_module(a.quality_source,'frozen_839_relative_sourceblind_control'); pmod=load_module(a.purity_source,'frozen_840_relative_sourceblind')

    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; hard_order=list(map(str,p19['hard_order'])); fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})
    hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-relative-sourceblind-purity-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN panel changed')

    eligible=qmod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    cm=qmod.centroid_matrix(fams); tie=[(hard_rank.get(fid,999999),fid) for fid in ids]

    # Exact #839 quality control.
    lookup_q=qmod.v2.event_lookup(scan); nf=qmod.neighbor_features(cm); xq=[]
    for i,f in enumerate(fams):
        fid=str(f['family_id']); src=source[fid]; srcf=[float(src=='hard'),float(src=='p19'),float(src=='p20')]
        p20f=[float(f.get('p20_cross_year_distance',0.0)),math.log1p(max(int(f.get('p20_min_anchor_count',0)),0)),float(f.get('p20_min_bin_strength',0.0)),float(f.get('p20_min_quartet_score',0.0))]
        xq.append(qmod.v1.structural_features(f,hard_rank)+qmod.v2.cohesion_features(f,lookup_q,support,base)+srcf+p20f+nf[i].tolist())
    xq=np.asarray(xq,float); yq=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],float)
    gq=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]; fq=np.asarray([qmod.v1.deterministic_fold(g) for g in gq],int); wq=qmod.grouped_weights(gq); oq=np.zeros(len(ids),float)
    for fold in range(5):
        tr=fq!=fold; te=fq==fold; m=qmod.model(); m.fit(xq[tr],yq[tr],sample_weight=wq[tr]); oq[te]=m.predict(xq[te]); req({gq[i] for i in np.where(tr)[0]}.isdisjoint({gq[i] for i in np.where(te)[0]}),f'quality group leakage {fold}')
    qorder=[ids[i] for i in qmod.diversity_order(oq,cm,0.8,1.0,tie)]; qmetrics=qmod.v1.monotone_metrics(fams,qorder,truths,eligible); assert_metrics(qmetrics,QUALITY_CONTROL,'#839 quality control')

    # Exact raw source-blind #977 control and sole relative candidate.
    req(len(tuple(pmod.v2.FEATURE_NAMES))==GENERIC_DIM,'generic feature dimension changed')
    lookup_p=pmod.v2.event_lookup(scan)
    xraw=np.asarray([pmod.v1.structural_features(f,hard_rank)+pmod.v2.cohesion_features(f,lookup_p,support,base) for f in fams],float)
    req(xraw.shape==(len(fams),GENERIC_DIM) and np.isfinite(xraw).all(),'raw source-blind matrix invalid')
    xrel=relative_transform(xraw)
    yp=np.asarray([int(truths[fid]['positive']) for fid in ids],int); req(np.unique(yp).size==2,'purity target degenerate')
    gp=[pmod.strict_group(fid,truths[fid]) for fid in ids]; fp=np.asarray([pmod.v2.deterministic_fold(g) for g in gp],int); wp=pmod.v2.diversity_weights(ids,truths,yp)
    def purity_oof(x:np.ndarray)->np.ndarray:
        out=np.zeros(len(ids),float)
        for fold in range(5):
            tr=fp!=fold; te=fp==fold; req(tr.any() and te.any() and np.unique(yp[tr]).size==2,f'invalid purity fold {fold}')
            model=pmod.fit(pmod.make_model(PURITY_SPEC),x[tr],yp[tr],wp[tr]); out[te]=pmod.probability(model,x[te]); req({gp[i] for i in np.where(tr)[0]}.isdisjoint({gp[i] for i in np.where(te)[0]}),f'purity group leakage {fold}')
        return out
    oraw=purity_oof(xraw); orel=purity_oof(xrel)
    order_raw=[ids[i] for i in qmod.diversity_order(oraw,cm,0.8,1.0,tie)]; order_rel=[ids[i] for i in qmod.diversity_order(orel,cm,0.8,1.0,tie)]
    metrics_raw=qmod.v1.monotone_metrics(fams,order_raw,truths,eligible); assert_metrics(metrics_raw,RAW21_CONTROL,'#977 raw source-blind control')
    metrics_rel=qmod.v1.monotone_metrics(fams,order_rel,truths,eligible)
    hard_metrics=qmod.v1.monotone_metrics(hard,hard_order,{fid:truths[fid] for fid in hard_order},eligible)
    viable=bool(int(metrics_rel['recovered_at_100'])>=75 and int(metrics_rel['recovered_at_50'])>=int(hard_metrics['recovered_at_50']) and float(metrics_rel['top100_dominant_precision'])>=float(hard_metrics['top100_dominant_precision'])-0.05 and int(metrics_rel['qualified_matches'])>=230)
    strict=bool(metric_key(metrics_rel)>metric_key(qmetrics)); passed=bool(viable and strict)

    freeze={'verdict':'NOT_FROZEN_RELATIVE_SOURCEBLIND_GMN_FAIL','model_sha256':None}
    if passed:
        model=pmod.fit(pmod.make_model(PURITY_SPEC),xrel,yp,wp); path=a.output/'orbittrace_relative_sourceblind_gmn_purity_hgb31.joblib'; joblib.dump(model,path)
        names=list(pmod.v2.FEATURE_NAMES); freeze={'verdict':'PASS_RELATIVE_SOURCEBLIND_GMN_MODEL_FREEZE','model_sha256':sha(path),'feature_dimension':GENERIC_DIM,'feature_names':names,'feature_name_sha256':hashlib.sha256('\n'.join(map(str,names)).encode()).hexdigest(),'categorical_columns':sorted(CATEGORICAL_COLUMNS),'relative_transform':'average-tie empirical percentile (rank-1)/(N-1)','training_examples':len(ids),'positive_examples':int(yp.sum()),'raw_training_feature_sha256':array_sha(xraw),'relative_training_feature_sha256':array_sha(xrel),'target_sha256':array_sha(yp),'weights_sha256':array_sha(wp),'deployment_diversity':{'lambda':0.8,'scale':1.0,'family_deletion':False,'complete_backfill':True}}

    result={'stage':'GMN_TARGET_EXCLUDED_RELATIVE_SOURCEBLIND_PURITY_V1','verdict':'PASS_GMN_RELATIVE_SOURCEBLIND_PURITY_V1' if passed else 'FAIL_GMN_RELATIVE_SOURCEBLIND_PURITY_V1','candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},'eligible_labels':len(eligible),'quality_839_control':trimmed(qmetrics),'raw21_977_control':trimmed(metrics_raw),'relative21':trimmed(metrics_rel),'relative21_order_sha256':order_sha(order_rel),'relative21_viable':viable,'strict_improvement_over_839':strict,'feature_dimension':GENERIC_DIM,'feature_names':list(pmod.v2.FEATURE_NAMES),'categorical_columns':sorted(CATEGORICAL_COLUMNS),'relative_transform':'average-tie empirical percentile (rank-1)/(N-1)','source_specific_features_used':False,'full_model_freeze':freeze,'parameter_search':False,'alternate_transform_search':False,'source_quota_selected':False,'family_deletion':False,'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND)}
    (a.output/'GMN_RELATIVE_SOURCEBLIND_PURITY_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); (a.output/'FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'quality_839_control':result['quality_839_control'],'raw21_977_control':result['raw21_977_control'],'relative21':result['relative21'],'viable':viable,'strict_improvement_over_839':strict,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
