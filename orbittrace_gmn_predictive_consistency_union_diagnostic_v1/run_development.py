#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

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
V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
PREDICTIVE_SOURCE_BLOB='25d91e92c41f83416ad87766c2d96884c30b714c'
CONTROL={'recovered_at_25':22,'recovered_at_50':40,'recovered_at_100':75,'recovered_at_500':159,'qualified_matches':256,'top100_dominant_precision':0.7645689180574315,'mrr':0.019037817654898162}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def trimmed(m:dict[str,Any])->dict[str,Any]: return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def assert_control(m:dict[str,Any])->None:
    for k,v in CONTROL.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-12,f'#839 baseline {k} changed: {m[k]} != {v}')
        else: req(int(m[k])==int(v),f'#839 baseline {k} changed: {m[k]} != {v}')


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True)
    p.add_argument('--predictive-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed')
    req(sha(a.v8_result_json)==V8_SHA,'v8 input changed')
    req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 inputs changed')
    req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 inputs changed')
    # Git blob SHA is verified by workflow; content hash here ensures the exact already-passed implementation is used at runtime.
    qmod=load_module(a.quality_source,'frozen_839_predictive_union')
    pred=load_module(a.predictive_source,'frozen_predictive_hard_pass')

    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; hard_order=list(map(str,p19['hard_order'])); fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})
    hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-predictive-consistency-union-diagnostic-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN panel changed')

    # Complete label-free predictive vector/order for all candidate types.
    lookup=qmod.v2.event_lookup(scan)
    feature_rows=[]
    for f in fams:
        feature_rows.append({'family_id':str(f['family_id']),'source':source[str(f['family_id'])],'features':pred.predictive_features(f,lookup)})
    predictive_order=pred.rank_predictive(feature_rows)
    req(len(predictive_order)==len(ids) and set(predictive_order)==set(ids),'predictive union order invalid')
    prelabel={'scope':'GMN 2022/2023 target-excluded full-union predictive consistency','candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},'families':feature_rows,'predictive_order_sha256':order_sha(predictive_order),'blind_exclusion':list(BLIND),'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    prelabel_path=a.output/'GMN_PREDICTIVE_CONSISTENCY_UNION_PRELABEL.json'; prelabel_path.write_text(json.dumps(prelabel,indent=2,sort_keys=True,allow_nan=False)+'\n'); prelabel_sha=sha(prelabel_path)

    # Exact active #839 grouped-OOF baseline over the immutable full union.
    eligible=qmod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    cm=qmod.centroid_matrix(fams); nf=qmod.neighbor_features(cm)
    x=[]
    for i,f in enumerate(fams):
        fid=str(f['family_id']); src=source[fid]
        srcf=[float(src=='hard'),float(src=='p19'),float(src=='p20')]
        p20f=[float(f.get('p20_cross_year_distance',0.0)),math.log1p(max(int(f.get('p20_min_anchor_count',0)),0)),float(f.get('p20_min_bin_strength',0.0)),float(f.get('p20_min_quartet_score',0.0))]
        x.append(qmod.v1.structural_features(f,hard_rank)+qmod.v2.cohesion_features(f,lookup,support,base)+srcf+p20f+nf[i].tolist())
    x=np.asarray(x,float); req(x.shape==(len(fams),34) and np.isfinite(x).all(),'active quality feature matrix changed')
    target=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],float)
    groups=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]
    folds=np.asarray([qmod.v1.deterministic_fold(g) for g in groups],int); weights=qmod.grouped_weights(groups); oof=np.zeros(len(ids),float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any(),f'empty fold {fold}')
        req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage {fold}')
        m=qmod.model(); m.fit(x[tr],target[tr],sample_weight=weights[tr]); oof[te]=m.predict(x[te])
    tie=[(hard_rank.get(fid,999999),fid) for fid in ids]
    baseline_order=[ids[i] for i in qmod.diversity_order(oof,cm,0.8,1.0,tie)]
    baseline=qmod.v1.monotone_metrics(fams,baseline_order,truths,eligible); assert_control(baseline)

    fused_order=pred.equal_rank_fusion(baseline_order,predictive_order)
    fused=qmod.v1.monotone_metrics(fams,fused_order,truths,eligible)
    gates={
      'recovered_at_100_strictly_better':int(fused['recovered_at_100'])>75,
      'recovered_at_50_not_worse':int(fused['recovered_at_50'])>=40,
      'recovered_at_25_not_worse':int(fused['recovered_at_25'])>=22,
      'top100_precision_not_worse':float(fused['top100_dominant_precision'])>=CONTROL['top100_dominant_precision'],
      'mrr_not_worse':float(fused['mrr'])>=CONTROL['mrr'],
    }
    passed=all(gates.values()); verdict='PASS_GMN_PREDICTIVE_CONSISTENCY_UNION_SIGNAL' if passed else 'FAIL_GMN_PREDICTIVE_CONSISTENCY_UNION_SIGNAL'
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_FULL_UNION_TRANSFER_DIAGNOSTIC_ONLY','candidate_counts':prelabel['candidate_counts'],'baseline':trimmed(baseline),'fused':trimmed(fused),'pass_gates':gates,'prelabel_sha256':prelabel_sha,'baseline_order_sha256':order_sha(baseline_order),'predictive_order_sha256':order_sha(predictive_order),'fused_order_sha256':order_sha(fused_order),'parameter_search':False,'family_deletion':False,'membership_changed':False,'candidate_generation_recomputed':False,'source_identity_in_predictive_score':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':list(BLIND),'claim_boundary':'PASS authorizes one separately frozen full-universe SonotaCo successor; FAIL blocks the dormant v61 benchmark.'}
    (a.output/'GMN_PREDICTIVE_CONSISTENCY_UNION_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'baseline25':baseline['recovered_at_25'],'fused25':fused['recovered_at_25'],'baseline50':baseline['recovered_at_50'],'fused50':fused['recovered_at_50'],'baseline100':baseline['recovered_at_100'],'fused100':fused['recovered_at_100'],'baseline_precision':baseline['top100_dominant_precision'],'fused_precision':fused['top100_dominant_precision'],'baseline_mrr':baseline['mrr'],'fused_mrr':fused['mrr'],'gates':gates,'prelabel_sha256':prelabel_sha},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
