#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
BASE_FEATURE_DIM=71
EXPANDED_COHESION_DIM=7
FEATURE_DIM=78
EXPECTED_V19_FAMILY_SHA={
    'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def array_sha(x: np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path: Path,obj: Any)->str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--v22-root',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    meta=json.loads((a.v22_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    membership=json.loads((a.v22_root/'family_memberships.json').read_text())
    require(meta['comparator']==a.comparator and meta['feature_dimension']==BASE_FEATURE_DIM,'wrong v22 route/feature identity')
    require(meta['truth_accessed'] is False and membership['truth_accessed'] is False,'truth-bearing v22 payload')
    require(meta['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[a.comparator],'v19 expanded family identity changed')
    x71=np.load(a.v22_root/'features.npy',allow_pickle=False)
    require(x71.shape==(len(meta['family_ids']),BASE_FEATURE_DIM) and np.all(np.isfinite(x71)),'invalid base feature matrix')
    require(array_sha(x71)==meta['feature_sha256'],'base feature internal hash mismatch')
    expanded=membership['families']; ids=list(map(str,meta['family_ids']))
    require([str(f['family_id']) for f in expanded]==ids,'expanded membership alignment changed')
    # family_memberships.json is intentionally aligned to candidate-ID order for the feature matrix,
    # whereas v19_family_sha256 was frozen over the exact v19 rank-sum order. Verify the same
    # membership objects after reordering by the already-frozen v19 order; do not alter feature order.
    by_id={str(f['family_id']):f for f in expanded}
    v19_order=list(map(str,meta['v19_order']))
    require(len(v19_order)==len(ids) and set(v19_order)==set(ids),'v19 order/family universe changed')
    require(canonical_sha([by_id[fid] for fid in v19_order])==EXPECTED_V19_FAMILY_SHA[a.comparator],'expanded family canonical identity changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(r['year'])==year for r in raw[year]),f'invalid rows {year}')
        require(all(not (forbidden & {str(k).lower() for k in r}) for r in raw[year]),'truth-bearing field reached v26 pretruth augmentation')
    canonical=v15_application.validate_pair(YEARS,raw)

    runtime,support,base,_=load_support_base(
        p19_module=type('Shim',(),{'mult':v17.MULT})(),support_source_parts=a.support_source_parts,
        candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,
    )
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed'); support.CORPUS=p19.CORPUS

    # Reconstruct the exact pre-expansion families solely to recover their original frozen centroids.
    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    s19,_=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    s20=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)['soft_families']
    originals=hard['hard_families']+s19+s20
    original_by_id={str(f['family_id']):f for f in originals}
    require(len(original_by_id)==len(ids) and set(original_by_id)==set(ids),'reconstructed candidate universe differs')

    lookup,event_year=urc_application.event_lookup_pair(canonical,YEARS)
    extra=[]
    for ef in expanded:
        fid=str(ef['family_id']); orig=original_by_id[fid]
        temp={'family_id':fid,'event_ids':list(map(str,ef['event_ids'])),'centroids':orig['centroids']}
        row=urc_application.cohesion_features_pair(temp,lookup,event_year,YEARS,support,base)
        require(len(row)==EXPANDED_COHESION_DIM and all(np.isfinite(float(v)) for v in row),f'invalid expanded cohesion {fid}')
        extra.append(row)
    xextra=np.asarray(extra,dtype=np.float64)
    require(xextra.shape==(len(ids),EXPANDED_COHESION_DIM),'expanded cohesion matrix shape changed')
    x78=np.column_stack([x71,xextra]).astype(np.float64,copy=False)
    require(x78.shape==(len(ids),FEATURE_DIM) and np.all(np.isfinite(x78)),'v26 feature matrix invalid')

    np.save(a.output/'features_v26.npy',x78,allow_pickle=False)
    np.save(a.output/'expanded_cohesion.npy',xextra,allow_pickle=False)
    out={
        'scientific_stage':'V26_EXPANDED_MEMBERSHIP_COHESION_PRETRUTH_FEATURE_FREEZE',
        'comparator':a.comparator,'years':list(YEARS),'family_ids':ids,
        'base_feature_dimension':BASE_FEATURE_DIM,'expanded_cohesion_dimension':EXPANDED_COHESION_DIM,'feature_dimension':FEATURE_DIM,
        'base_feature_sha256':array_sha(x71),'expanded_cohesion_sha256':array_sha(xextra),'feature_sha256':array_sha(x78),
        'expanded_cohesion_source':'exact orbittrace_urc_unseen_ranker_v1.application.cohesion_features_pair (#839 v2 definition)',
        'expanded_cohesion_uses_exact_frozen_v19_memberships':True,
        'expanded_cohesion_uses_exact_preexpansion_candidate_centroids':True,
        'feature_search':False,'new_radius_or_quantile_search':False,
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V26_PRETRUTH_FEATURE_MANIFEST.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='family_ids'},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
