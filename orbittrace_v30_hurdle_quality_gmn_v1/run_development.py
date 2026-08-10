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
PURITY_SHA256='7bbaa13b90ba10eb41f708b5aec6ebebd83e9c7c34018aa3f973b4aec086b96a'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
QUALITY_CONTROL={'recovered_at_25':22,'recovered_at_50':40,'recovered_at_100':75,'recovered_at_500':159,'qualified_matches':256,'top100_dominant_precision':0.7645689180574315}
PURITY_CONTROL={'recovered_at_25':24,'recovered_at_50':47,'recovered_at_100':81,'recovered_at_500':166,'qualified_matches':256,'top100_dominant_precision':0.8534939929790234,'mrr':0.02094738537699626}
PURITY_SPEC={'kind':'hgb','leaves':31}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def metric_key(m:dict[str,Any])->tuple[float,...]: return (float(m['recovered_at_100']),float(m['recovered_at_50']),float(m['recovered_at_25']),float(m['top100_dominant_precision']),float(m['mrr']))
def trimmed(m:dict[str,Any])->dict[str,Any]: return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def check_control(m:dict[str,Any],expected:dict[str,Any],name:str)->None:
    for k,v in expected.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-12,f'{name} control mismatch {k}: {m[k]} != {v}')
        else: req(int(m[k])==int(v),f'{name} control mismatch {k}: {m[k]} != {v}')


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--purity-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed'); req(sha(a.purity_source)==PURITY_SHA256,'#840 source changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 inputs changed'); req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 inputs changed')
    qmod=load_module(a.quality_source,'frozen_839_v30'); pmod=load_module(a.purity_source,'frozen_840_v30')

    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; hard_order=list(map(str,p19['hard_order'])); fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20}); hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-v30-hurdle-quality-gmn-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN panel changed')

    eligible=qmod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    cm=qmod.centroid_matrix(fams); nf=qmod.neighbor_features(cm); lookup_q=qmod.v2.event_lookup(scan)
    xq=[]
    for i,f in enumerate(fams):
        fid=str(f['family_id']); src=source[fid]; srcf=[float(src=='hard'),float(src=='p19'),float(src=='p20')]
        p20f=[float(f.get('p20_cross_year_distance',0.0)),math.log1p(max(int(f.get('p20_min_anchor_count',0)),0)),float(f.get('p20_min_bin_strength',0.0)),float(f.get('p20_min_quartet_score',0.0))]
        xq.append(qmod.v1.structural_features(f,hard_rank)+qmod.v2.cohesion_features(f,lookup_q,support,base)+srcf+p20f+nf[i].tolist())
    xq=np.asarray(xq,float); req(xq.shape[0]==4504 and np.isfinite(xq).all(),'quality features invalid')
    yq=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],float)

    lookup_p=pmod.v2.event_lookup(scan)
    xp=np.asarray([pmod.v1.structural_features(f,hard_rank)+pmod.v2.cohesion_features(f,lookup_p,support,base)+pmod.source_features(f,source[str(f['family_id'])]) for f in fams],float)
    req(xp.shape[0]==4504 and np.isfinite(xp).all(),'purity features invalid')
    yp=np.asarray([int(truths[fid]['positive']) for fid in ids],int); req(int(yp.sum())==2017,'positive family count changed')

    # One strict grouping/fold assignment for both heads; near-miss shower groups remain together.
    groups=[pmod.strict_group(fid,truths[fid]) for fid in ids]; folds=np.asarray([pmod.v2.deterministic_fold(g) for g in groups],int)
    purity_weights=pmod.v2.diversity_weights(ids,truths,yp); quality_weights=qmod.grouped_weights(groups)
    op=np.zeros(len(ids),float); oq_cond=np.zeros(len(ids),float)
    fold_diag=[]
    for fold in range(5):
        train=folds!=fold; test=folds==fold; positive_train=train & (yp==1)
        req(test.any() and positive_train.any() and np.unique(yp[train]).size==2,f'invalid fold {fold}')
        train_groups={groups[i] for i in np.where(train)[0]}; test_groups={groups[i] for i in np.where(test)[0]}; req(train_groups.isdisjoint(test_groups),f'group leakage fold {fold}')
        pm=pmod.fit(pmod.make_model(PURITY_SPEC),xp[train],yp[train],purity_weights[train]); op[test]=pmod.probability(pm,xp[test])
        qm=qmod.model(); qm.fit(xq[positive_train],yq[positive_train],sample_weight=quality_weights[positive_train]); oq_cond[test]=qm.predict(xq[test])
        fold_diag.append({'fold':fold,'train_examples':int(train.sum()),'test_examples':int(test.sum()),'positive_conditional_train_examples':int(positive_train.sum()),'train_groups':len(train_groups),'test_groups':len(test_groups)})
    req(np.isfinite(op).all() and np.isfinite(oq_cond).all(),'OOF predictions nonfinite')
    hurdle=op*oq_cond; req(np.isfinite(hurdle).all(),'hurdle score nonfinite')

    # Reproduce #839 quality control independently on its exact grouping.
    gq=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]; fq=np.asarray([qmod.v1.deterministic_fold(g) for g in gq],int); wq=qmod.grouped_weights(gq); oq=np.zeros(len(ids),float)
    for fold in range(5):
        tr=fq!=fold; te=fq==fold; m=qmod.model(); m.fit(xq[tr],yq[tr],sample_weight=wq[tr]); oq[te]=m.predict(xq[te])
    tie=[(hard_rank.get(fid,999999),fid) for fid in ids]
    qorder=[ids[i] for i in qmod.diversity_order(oq,cm,0.8,1.0,tie)]
    porder=[ids[i] for i in qmod.diversity_order(op,cm,0.8,1.0,tie)]
    horder=[ids[i] for i in qmod.diversity_order(hurdle,cm,0.8,1.0,tie)]
    hard_metrics=qmod.v1.monotone_metrics(hard,hard_order,{fid:truths[fid] for fid in hard_order},eligible)
    quality_metrics=qmod.v1.monotone_metrics(fams,qorder,truths,eligible); purity_metrics=qmod.v1.monotone_metrics(fams,porder,truths,eligible); hurdle_metrics=qmod.v1.monotone_metrics(fams,horder,truths,eligible)
    check_control(quality_metrics,QUALITY_CONTROL,'#839 quality'); check_control(purity_metrics,PURITY_CONTROL,'#971 purity')

    viable=(int(hurdle_metrics['recovered_at_100'])>=75 and int(hurdle_metrics['recovered_at_50'])>=int(hard_metrics['recovered_at_50']) and float(hurdle_metrics['top100_dominant_precision'])>=float(hard_metrics['top100_dominant_precision'])-0.05 and int(hurdle_metrics['qualified_matches'])>=230)
    passed=bool(viable and metric_key(hurdle_metrics)>metric_key(purity_metrics))
    full={'verdict':'NOT_FROZEN_V30_GMN_FAIL','purity_model_sha256':None,'conditional_quality_model_sha256':None}
    if passed:
        pm=pmod.fit(pmod.make_model(PURITY_SPEC),xp,yp,purity_weights); qm=qmod.model(); pos=yp==1; qm.fit(xq[pos],yq[pos],sample_weight=quality_weights[pos])
        pp=a.output/'v30_gmn_purity_hgb31.joblib'; qp=a.output/'v30_gmn_conditional_quality_extratrees.joblib'; joblib.dump(pm,pp); joblib.dump(qm,qp)
        full={'verdict':'PASS_V30_GMN_FULL_HURDLE_MODELS_FREEZE','purity_model_sha256':sha(pp),'conditional_quality_model_sha256':sha(qp),'purity_feature_dimension':int(xp.shape[1]),'conditional_quality_feature_dimension':int(xq.shape[1]),'training_examples':len(ids),'positive_conditional_training_examples':int(pos.sum()),'deployment_score':'purity_probability * conditional_positive_F1_prediction','diversity':{'lambda':0.8,'scale':1.0,'complete_backfill':True}}
    result={'stage':'V30_TARGET_EXCLUDED_GMN_HURDLE_QUALITY_DEVELOPMENT','verdict':'PASS_V30_GMN_HURDLE_QUALITY_DEVELOPMENT' if passed else 'FAIL_V30_GMN_HURDLE_QUALITY_DEVELOPMENT','candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},'eligible_labels':len(eligible),'folds':fold_diag,'quality_control':trimmed(quality_metrics),'purity_control':trimmed(purity_metrics),'hurdle_metrics':trimmed(hurdle_metrics),'hurdle_comparison_key':list(metric_key(hurdle_metrics)),'purity_comparison_key':list(metric_key(purity_metrics)),'strict_improvement_over_v29_purity':bool(metric_key(hurdle_metrics)>metric_key(purity_metrics)),'viable':bool(viable),'hurdle_order_sha256':order_sha(horder),'purity_oof_sha256':array_sha(op),'conditional_quality_oof_sha256':array_sha(oq_cond),'hurdle_score_sha256':array_sha(hurdle),'full_model_freeze':full,'parameter_search':False,'post_result_second_search':False,'sonotaco_2013_2014_access':False,'oracle_976_rank_identity_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND)}
    (a.output/'V30_GMN_HURDLE_QUALITY_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); (a.output/'V30_FULL_MODEL_FREEZE.json').write_text(json.dumps(full,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':result['verdict'],'quality':result['quality_control'],'purity':result['purity_control'],'hurdle':result['hurdle_metrics'],'full':full},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
