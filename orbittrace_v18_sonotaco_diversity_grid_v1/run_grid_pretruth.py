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

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
LAMBDAS=(0.0,0.2,0.4,0.6,0.8)
SCALES=(0.75,1.0,1.5)
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path: Path,obj: Any)->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def tag(lam: float,scale: float)->str:
    def f(x: float)->str:
        s=(f'{x:.2f}').rstrip('0').rstrip('.')
        return s.replace('.','p')
    return f'lambda_{f(lam)}__scale_{f(scale)}'

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot load {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--active-ranker-source',type=Path,required=True); p.add_argument('--model-joblib',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.active_ranker_source)==EXPECTED_RANKER_SHA,'#839 ranker source changed')
    require(sha(a.model_joblib)==EXPECTED_MODEL_SHA,'#853 serialized model changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(x['year'])==year for x in raw[year]),f'invalid {year} rows')
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v18 candidate generation')
    canonical=v15_application.validate_pair(YEARS,raw)

    runtime,support,base,_=load_support_base(
        p19_module=type('Shim',(),{'mult':v17.MULT})(),
        support_source_parts=a.support_source_parts,
        candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,
        scorer_parts=a.scorer_parts,
    )
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed')
    support.CORPUS=p19.CORPUS

    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    p19_soft,p19_diag=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    p20_result=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)
    p20_soft=p20_result['soft_families']
    union=hard['hard_families']+p19_soft+p20_soft
    source_by_id={str(f['family_id']):'hard' for f in hard['hard_families']}
    source_by_id.update({str(f['family_id']):'p19' for f in p19_soft})
    source_by_id.update({str(f['family_id']):'p20' for f in p20_soft})
    require(len(source_by_id)==len(union),'union family IDs collide')

    ranker=load_module(a.active_ranker_source,'frozen_active_urc_v18')
    X,centroid_matrix,tie=urc_application.build_feature_matrix(
        families=union,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,
        years=YEARS,support=support,base=base,frozen_ranker_module=ranker,
    )
    model=joblib.load(a.model_joblib)
    require(int(getattr(model,'n_features_in_',-1))==urc_application.EXPECTED_FEATURES,'model feature count changed')
    serialized_n_jobs=getattr(model,'n_jobs',None)
    if hasattr(model,'set_params') and serialized_n_jobs is not None: model.set_params(n_jobs=1)
    scores=np.asarray(model.predict(X),dtype=np.float64)
    require(scores.shape==(len(union),) and np.all(np.isfinite(scores)),'invalid quality predictions')
    ids=[str(f['family_id']) for f in union]; by_id={str(f['family_id']):f for f in union}

    configs=[]
    for lam in LAMBDAS:
        for scale in SCALES:
            cfg=tag(lam,scale)
            order_idx=ranker.diversity_order(scores,centroid_matrix,float(lam),float(scale),tie)
            require(len(order_idx)==len(union) and len(set(order_idx))==len(union),'invalid diversity order')
            order=[ids[i] for i in order_idx]
            ordered=[]
            for rank,fid in enumerate(order,start=1):
                f=by_id[fid]
                ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by_id[fid]})
            expanded,membership_diag=v17.expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)
            payload={
                'method':'OrbitTrace v18 exposed diversity-grid candidate',
                'comparator_pair':a.comparator,'years':list(YEARS),'family_count':len(expanded),'families':expanded,
                'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
                'hard_order_method':'v15 median-rank consensus over adaptive caps 128/96/64','hard_order_sha256':canonical_sha(hard['hard_order']),
                'ranker_model_sha256':EXPECTED_MODEL_SHA,'ranker_source_sha256':EXPECTED_RANKER_SHA,
                'quality_prediction_sha256':urc_application.array_sha256(scores),
                'feature_matrix_sha256':urc_application.array_sha256(X),
                'diversity_lambda':float(lam),'diversity_scale':float(scale),
                'diversity_order_sha256':hashlib.sha256('\n'.join(order).encode()).hexdigest(),
                'membership_diagnostics':membership_diag,
                'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
            }
            out_path=a.output/cfg/'candidate_primary_output.json'
            payload_sha=dump(out_path,payload)
            configs.append({'tag':cfg,'lambda':float(lam),'scale':float(scale),'candidate_output_sha256':payload_sha,'order_sha256':payload['diversity_order_sha256'],'membership_total_new':membership_diag['total_new_members']})

    require(len(configs)==15 and len({x['tag'] for x in configs})==15,'grid size changed')
    v17_cfg=next(x for x in configs if abs(x['lambda']-0.8)<1e-15 and abs(x['scale']-1.0)<1e-15)
    manifest={
        'verdict':'PASS_V18_ALL_15_PRETRUTH_GRID_OUTPUTS_FROZEN','comparator':a.comparator,'years':list(YEARS),
        'grid':{'lambdas':list(LAMBDAS),'scales':list(SCALES),'count':15},'configs':configs,
        'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
        'v17_config_tag':v17_cfg['tag'],'v17_config_lambda':0.8,'v17_config_scale':1.0,
        'feature_matrix_sha256':urc_application.array_sha256(X),'quality_prediction_sha256':urc_application.array_sha256(scores),
        'p19_diagnostics_sha256':canonical_sha(p19_diag),'p20_diagnostics_sha256':canonical_sha(p20_result['soft_diagnostics']),
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V18_PRETRUTH_GRID_MANIFEST.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k!='configs'},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
