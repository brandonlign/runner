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
from scipy.stats import rankdata

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base

YEARS=(2013,2014)
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_ORIGINAL_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_V19_FAMILY_SHA={
 'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
 'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}
CATEGORICAL_COLUMNS={0,21,22,23}
VARIANTS=('relative_quality','relative_v19_rank_sum','v19_control')


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_sha(obj: Any)->str: return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def dump(path: Path,obj: Any)->str:
    path.parent.mkdir(parents=True,exist_ok=True); raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def relative_transform(x: np.ndarray)->np.ndarray:
    x=np.asarray(x,dtype=np.float64); require(x.ndim==2 and x.shape[1]==34 and len(x)>=2 and np.all(np.isfinite(x)),'invalid feature matrix')
    out=np.empty_like(x); den=float(len(x)-1)
    for j in range(x.shape[1]):
        out[:,j]=x[:,j] if j in CATEGORICAL_COLUMNS else (rankdata(x[:,j],method='average')-1.0)/den
    require(np.all(np.isfinite(out)),'relative features nonfinite'); return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--original-model',type=Path,required=True)
    p.add_argument('--relative-model',type=Path,required=True); p.add_argument('--model-freeze',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.ranker_source)==EXPECTED_RANKER_SHA,'#839 ranker source changed')
    require(sha(a.original_model)==EXPECTED_ORIGINAL_MODEL_SHA,'original #853 model changed')
    freeze=json.loads(a.model_freeze.read_text()); require(freeze['verdict']=='PASS_V21_FULL_GMN_MODEL_FREEZE','v21 GMN model not frozen')
    require(sha(a.relative_model)==freeze['model_sha256'],'v21 relative model hash changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for y in YEARS:
        require(raw[y] and all(int(r['year'])==y for r in raw[y]),f'invalid {y} rows')
        require(all(not (forbidden & {str(k).lower() for k in r}) for r in raw[y]),'truth-bearing field reached v21 application')
    canonical=v15_application.validate_pair(YEARS,raw)

    runtime,support,base,_=load_support_base(
        p19_module=type('Shim',(),{'mult':v17.MULT})(),support_source_parts=a.support_source_parts,
        candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,
    )
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed'); support.CORPUS=p19.CORPUS
    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    s19,_=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    s20=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)['soft_families']
    fams=hard['hard_families']+s19+s20
    sources=['hard']*len(hard['hard_families'])+['p19']*len(s19)+['p20']*len(s20)
    ids=[str(f['family_id']) for f in fams]; source_by_id={fid:src for fid,src in zip(ids,sources)}
    require(len(ids)==len(set(ids))==len(source_by_id),'family universe collision')
    ranker=load_module(a.ranker_source,'frozen_839_v21_apply')
    x_raw,cm,tie=urc_application.build_feature_matrix(
        families=fams,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,years=YEARS,
        support=support,base=base,frozen_ranker_module=ranker,
    )
    x=relative_transform(x_raw); model=joblib.load(a.relative_model)
    if hasattr(model,'set_params'): model.set_params(n_jobs=1)
    scores=np.asarray(model.predict(x),dtype=np.float64); require(scores.shape==(len(fams),) and np.all(np.isfinite(scores)),'invalid relative predictions')
    rel_idx=ranker.diversity_order(scores,cm,0.8,1.0,tie); relative_order=[ids[i] for i in rel_idx]

    original=urc_application.score_and_rank(
        model_path=a.original_model,families=fams,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,
        years=YEARS,support=support,base=base,frozen_ranker_module=ranker,
    )
    consensus_order,_=v19.raw_consensus_order(fams,sources,support,base)
    v19_order=list(v19.fusion_orders(list(original['order']),consensus_order)['rank_sum'])
    fused=list(v19.fusion_orders(relative_order,v19_order)['rank_sum'])
    orders={'relative_quality':relative_order,'relative_v19_rank_sum':fused,'v19_control':v19_order}

    by={str(f['family_id']):f for f in fams}; rows=[]
    for variant in VARIANTS:
        order=orders[variant]; ordered=[]
        for rank,fid in enumerate(order,start=1):
            f=by[fid]; ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by_id[fid]})
        expanded,md=v17.expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)
        fsha=canonical_sha(expanded)
        if variant=='v19_control': require(fsha==EXPECTED_V19_FAMILY_SHA[a.comparator],f'{a.comparator} v19 control changed')
        payload={
            'method':'OrbitTrace v21 catalogue-relative quality ranking exposed development','variant':variant,
            'comparator_pair':a.comparator,'years':list(YEARS),'families':expanded,'family_count':len(expanded),
            'relative_model_sha256':freeze['model_sha256'],'relative_feature_sha256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),
            'order_sha256':hashlib.sha256('\n'.join(order).encode()).hexdigest(),'membership_diagnostics':md,
            'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
        }
        pth=a.output/variant/'candidate_primary_output.json'; psha=dump(pth,payload)
        rows.append({'variant':variant,'candidate_output_sha256':psha,'families_sha256':fsha,'order_sha256':payload['order_sha256']})
    manifest={
        'verdict':'PASS_V21_ALL_VARIANTS_PRETRUTH_FREEZE','comparator':a.comparator,'variants':rows,
        'successor_variants':['relative_quality','relative_v19_rank_sum'],'v19_control':'v19_control',
        'sonotaco_training_labels_used':False,'feature_selection_search':False,'model_hyperparameter_search':False,'fusion_weight_search':False,
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V21_PRETRUTH_VARIANT_MANIFEST.json',manifest); print(json.dumps(manifest,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
