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
PURITY_SHA256='7bbaa13b90ba10eb41f708b5aec6ebebd83e9c7c34018aa3f973b4aec086b96a'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
PURITY_SPEC={'kind':'hgb','leaves':31}
EXPECTED_971={
    'recovered_at_25':24,
    'recovered_at_50':47,
    'recovered_at_100':81,
    'recovered_at_500':166,
    'qualified_matches':256,
    'top100_dominant_precision':0.8534939929790234,
    'mrr':0.02094738537699626,
}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()
def strings_sha(xs:list[str])->str: return hashlib.sha256('\n'.join(xs).encode()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--purity-source',type=Path,required=True)
    p.add_argument('--pr971-result',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--p19-result-json',type=Path,required=True)
    p.add_argument('--p19-prelabel-json',type=Path,required=True)
    p.add_argument('--p20-result-json',type=Path,required=True)
    p.add_argument('--p20-prelabel-json',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha(a.purity_source)==PURITY_SHA256,'#840 purity source changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 input changed')
    req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 input changed')

    r971=json.loads(a.pr971_result.read_text())
    req(r971['verdict']=='FAIL_GMN_QUALITY_PURITY_DUALHEAD_FUSION_V1','#971 frozen verdict changed')
    diag=next(x for x in r971['variants'] if x['variant']=='purity_diversity')
    req(diag['viable'] is True,'#971 purity-diversity viability changed')
    for k,v in EXPECTED_971.items():
        cur=diag['metrics'][k]
        if isinstance(v,float): req(abs(float(cur)-v)<1e-12,f'#971 purity-diversity metric changed: {k}')
        else: req(int(cur)==v,f'#971 purity-diversity metric changed: {k}')

    mod=load_module(a.purity_source,'frozen_840_v29_fit')
    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; fams=hard+s19+s20; hard_order=list(map(str,p19['hard_order']))
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})
    hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    mod.v1.mult.YEARS=YEARS; mod.v1.mult.MONTH_KEYS=MONTH_KEYS; mod.v1.mult.TOP_K=100
    runtime=mod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-v29-purity-diversity-gmn-freeze-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN development panel changed')

    eligible=mod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:mod.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    lookup=mod.v2.event_lookup(scan)
    x=np.asarray([
        mod.v1.structural_features(f,hard_rank)+mod.v2.cohesion_features(f,lookup,support,base)+mod.source_features(f,source[str(f['family_id'])])
        for f in fams
    ],dtype=float)
    req(x.shape==(4504,len(mod.FEATURE_NAMES)) and np.isfinite(x).all(),'purity feature matrix changed')
    y=np.asarray([int(truths[fid]['positive']) for fid in ids],dtype=int); req(np.unique(y).size==2,'purity target degenerate')
    groups=[mod.strict_group(fid,truths[fid]) for fid in ids]
    weights=mod.v2.diversity_weights(ids,truths,y)
    req(np.isfinite(weights).all() and np.all(weights>0),'training weights invalid')

    model=mod.fit(mod.make_model(PURITY_SPEC),x,y,weights)
    model_path=a.output/'orbittrace_v29_gmn_purity_hgb31.joblib'; joblib.dump(model,model_path)
    feature_names=list(map(str,mod.FEATURE_NAMES))
    manifest={
        'verdict':'PASS_V29_GMN_PURITY_DIVERSITY_MODEL_FREEZE',
        'selection_source_pr':971,
        'selection_source_run':31435769113,
        'selection_source_artifact':9080977251,
        'selected_architecture':'exact #840 HGB31 purity probability + exact #839 geometric diversity',
        'candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},
        'eligible_labels':len(eligible),
        'training_examples':len(ids),
        'positive_examples':int(y.sum()),
        'feature_dimension':int(x.shape[1]),
        'feature_names':feature_names,
        'feature_names_sha256':strings_sha(feature_names),
        'family_order_sha256':strings_sha(ids),
        'training_feature_sha256':array_sha(x),
        'training_target_sha256':array_sha(y),
        'training_weights_sha256':array_sha(np.asarray(weights,dtype=float)),
        'model_sha256':sha(model_path),
        'model_spec':{'kind':'HistGradientBoostingClassifier','learning_rate':0.05,'max_iter':250,'max_leaf_nodes':31,'l2_regularization':1.0,'random_state':20260809},
        'deployment_diversity':{'lambda':0.8,'scale':1.0,'family_deletion':False,'complete_backfill':True},
        'quality_fusion':False,'consensus_fusion':False,'event_jaccard_suppression':False,'source_quota':False,'threshold_search':False,'parameter_search':False,
        'in_sample_score_used_for_selection':False,
        'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND),
    }
    (a.output/'V29_GMN_PURITY_DIVERSITY_MODEL_FREEZE.json').write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
