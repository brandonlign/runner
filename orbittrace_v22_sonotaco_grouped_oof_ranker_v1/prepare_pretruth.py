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
from scipy.stats import rankdata

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_V19_FAMILY_SHA={
    'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}
CATEGORICAL_COLUMNS={0,21,22,23}
FEATURE_DIM=71


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def array_sha(x: np.ndarray)->str:
    a=np.ascontiguousarray(x)
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def dump(path: Path,obj: Any)->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def rank_percentile(order: list[str],ids: list[str])->np.ndarray:
    require(len(order)==len(ids) and set(order)==set(ids),'rank percentile universe mismatch')
    pos={fid:i for i,fid in enumerate(order)}; den=float(max(len(ids)-1,1))
    return np.asarray([pos[fid]/den for fid in ids],dtype=np.float64)

def relative_noncat(x: np.ndarray)->np.ndarray:
    x=np.asarray(x,dtype=np.float64); require(x.ndim==2 and x.shape[1]==34 and len(x)>=2,'bad raw feature matrix')
    cols=[]; den=float(len(x)-1)
    for j in range(x.shape[1]):
        if j in CATEGORICAL_COLUMNS: continue
        cols.append((rankdata(x[:,j],method='average')-1.0)/den)
    out=np.column_stack(cols); require(out.shape==(len(x),30) and np.all(np.isfinite(out)),'bad relative noncat features'); return out

def consensus_graph_features(families: list[dict[str,Any]],sources: list[str],support: Any,base: Any)->np.ndarray:
    edges=v19.build_edges(families,support,base); adj=[set([i]) for i in range(len(families))]
    for d,i,j in edges:
        require(d<=v19.CONSENSUS_RADIUS+1e-12,'consensus edge beyond frozen radius'); adj[i].add(j); adj[j].add(i)
    source_pct=v19.source_rank_percentiles(sources); rows=[]
    for i in range(len(families)):
        nb=adj[i]; degree=len(nb)-1; cross=sum(sources[j]!=sources[i] for j in nb); nsrc=len({sources[j] for j in nb})-1
        rows.append([math.log1p(degree),math.log1p(cross),float(nsrc),float(source_pct[i])])
    out=np.asarray(rows,dtype=np.float64); require(out.shape==(len(families),4) and np.all(np.isfinite(out)),'bad consensus graph features'); return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--original-model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.ranker_source)==EXPECTED_RANKER_SHA,'#839 ranker source changed'); require(sha(a.original_model)==EXPECTED_MODEL_SHA,'#853 model changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}; forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(x['year'])==year for x in raw[year]),f'invalid {year} rows')
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v22 pretruth stage')
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
    fams=hard['hard_families']+s19+s20; sources=['hard']*len(hard['hard_families'])+['p19']*len(s19)+['p20']*len(s20)
    ids=[str(f['family_id']) for f in fams]; require(len(ids)==len(set(ids)),'family IDs collide'); source_by_id={fid:src for fid,src in zip(ids,sources)}

    ranker=load_module(a.ranker_source,'frozen_839_v22_pretruth')
    xraw,centroids,tie=urc_application.build_feature_matrix(
        families=fams,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,years=YEARS,
        support=support,base=base,frozen_ranker_module=ranker,
    )
    original=urc_application.score_and_rank(
        model_path=a.original_model,families=fams,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,
        years=YEARS,support=support,base=base,frozen_ranker_module=ranker,
    )
    qorder=list(original['order']); corder,cdiag=v19.raw_consensus_order(fams,sources,support,base); v19order=list(v19.fusion_orders(qorder,corder)['rank_sum'])

    xrel=relative_noncat(xraw); graph=consensus_graph_features(fams,sources,support,base)
    priors=np.column_stack([rank_percentile(qorder,ids),rank_percentile(corder,ids),rank_percentile(v19order,ids)])
    x=np.column_stack([xraw,xrel,priors,graph]).astype(np.float64,copy=False)
    require(x.shape==(len(fams),FEATURE_DIM) and np.all(np.isfinite(x)),'v22 feature matrix invalid')

    by={str(f['family_id']):f for f in fams}; ordered=[]
    for rank,fid in enumerate(v19order,start=1):
        f=by[fid]; ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by_id[fid]})
    expanded,md=v17.expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)
    require(canonical_sha(expanded)==EXPECTED_V19_FAMILY_SHA[a.comparator],f'{a.comparator} exact v19 expanded membership identity failed')
    expanded_by={str(f['family_id']):f for f in expanded}; require(set(expanded_by)==set(ids),'expanded family universe changed')
    aligned_expanded=[expanded_by[fid] for fid in ids]

    np.save(a.output/'features.npy',x,allow_pickle=False); np.save(a.output/'centroids.npy',np.asarray(centroids,dtype=np.float64),allow_pickle=False)
    meta={
        'comparator':a.comparator,'years':list(YEARS),'family_ids':ids,'sources':sources,
        'tie_rank':[int(t[0]) for t in tie],'v19_order':v19order,'quality_order':qorder,'consensus_order':corder,
        'feature_dimension':FEATURE_DIM,'feature_blocks':{'raw_839':34,'relative_noncat_839':30,'rank_percentiles':3,'consensus_graph':4},
        'feature_sha256':array_sha(x),'centroid_sha256':array_sha(np.asarray(centroids,dtype=np.float64)),
        'v19_family_sha256':canonical_sha(expanded),'membership_diagnostics':md,'consensus_diagnostics':cdiag,
        'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(s19),'p20':len(s20),'union':len(fams)},
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'family_memberships.json',{'families':aligned_expanded,'truth_accessed':False}); dump(a.output/'V22_PRETRUTH_FEATURE_MANIFEST.json',meta)
    print(json.dumps({k:v for k,v in meta.items() if k not in {'family_ids','sources','tie_rank','v19_order','quality_order','consensus_order'}},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
