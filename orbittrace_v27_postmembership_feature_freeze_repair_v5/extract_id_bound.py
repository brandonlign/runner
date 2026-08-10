#!/usr/bin/env python3
"""Family-ID-bound v27 post-membership feature extractor.

The untouched v22 builder emits implementation arrays in its raw family-generation order. That
order is not a scientific catalogue identity and can differ while the exact v19 catalogue and
expanded memberships remain identical. This extractor therefore binds base rows by family ID,
checks each same-run array against its own manifest, and uses the stable v19 expanded-catalogue
hash plus per-family expanded event-set equality as the scientific identity.

No feature, membership, candidate, ranking, or truth semantics are changed.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require
from orbittrace_v27_postmembership_feature_freeze_repair_v2 import extract_postfeatures as helper

YEARS=(2013,2014)
TOP_K=100
BASE_DIM=71
POST_DIM=16
COMBINED_DIM=87
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_V19_FAMILY_SHA={
    'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}
POST_FEATURE_NAMES=(
    'expanded_member_count_min_year','expanded_member_count_max_year','expanded_member_count_year_balance',
    'expanded_member_distance_median','expanded_member_distance_q90','expanded_member_distance_max','expanded_year_q90_distance_max',
    'log1p_core_member_count','log1p_added_member_count','added_to_core_ratio',
    'accepted_d2_median','accepted_d2_q90','accepted_trajectory_residual_median','accepted_trajectory_residual_q90',
    'accepted_neglog_joint_p_median','accepted_neglog_joint_p_q90',
)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--base-root',type=Path,required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--original-model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(helper.sha(a.ranker_source)==EXPECTED_RANKER_SHA,'#839 ranker source changed')
    require(helper.sha(a.original_model)==EXPECTED_MODEL_SHA,'#853 model changed')

    # Consume the exact untouched v22 build. Implementation arrays are self-bound to its manifest.
    meta=json.loads((a.base_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    family_payload=json.loads((a.base_root/'family_memberships.json').read_text())
    base_features=np.load(a.base_root/'features.npy',allow_pickle=False)
    centroids=np.load(a.base_root/'centroids.npy',allow_pickle=False)
    require(meta['feature_dimension']==BASE_DIM,'same-run base feature dimension changed')
    require(base_features.shape==(len(meta['family_ids']),BASE_DIM),'same-run feature shape changed')
    require(centroids.shape==(len(meta['family_ids']),8),'same-run centroid shape changed')
    require(helper.array_sha(base_features)==meta['feature_sha256'],'same-run feature/manifest hash mismatch')
    require(helper.array_sha(centroids)==meta['centroid_sha256'],'same-run centroid/manifest hash mismatch')
    require(meta['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[a.comparator],'stable v19 expanded catalogue identity changed')
    require(meta['truth_accessed'] is False and meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False,'same-run base firewall changed')
    require(family_payload['truth_accessed'] is False,'same-run family payload is truth-bearing')
    frozen_families=family_payload['families']
    base_ids=list(map(str,meta['family_ids']))
    require([str(f['family_id']) for f in frozen_families]==base_ids,'same-run family payload/base ID alignment changed')
    require(len(base_ids)==len(set(base_ids)),'same-run base IDs collide')
    frozen_by={str(f['family_id']):f for f in frozen_families}

    # Restore only label-free rows and independently reconstruct the scientific core universe.
    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(x['year'])==year for x in raw[year]),f'invalid {year} rows')
        require(all(not(forbidden&{str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v27 extractor')
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
    reconstructed_ids=[str(f['family_id']) for f in fams]
    require(len(reconstructed_ids)==len(set(reconstructed_ids)),'reconstructed family IDs collide')
    require(set(reconstructed_ids)==set(base_ids),'reconstructed family-ID universe differs from same-run base')
    source_by={fid:src for fid,src in zip(reconstructed_ids,sources)}
    core_by={str(f['family_id']):f for f in fams}

    # Reproduce exact v19 scientific order independent of raw implementation row ordering.
    ranker=helper.load_module(a.ranker_source,'frozen_839_v27_idbound')
    original=urc_application.score_and_rank(
        model_path=a.original_model,families=fams,source_by_id=source_by,hard_order=hard['hard_order'],
        scan_by_year=canonical,years=YEARS,support=support,base=base,frozen_ranker_module=ranker,
    )
    qorder=list(original['order'])
    corder,_=v19.raw_consensus_order(fams,sources,support,base)
    v19order=list(v19.fusion_orders(qorder,corder)['rank_sum'])
    require(v19order==list(map(str,meta['v19_order'])),'exact v19 stage-1 order differs from same-run base')

    ordered=[]
    for rank,fid in enumerate(v19order,start=1):
        f=core_by[fid]
        ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by[fid]})
    expanded,accepted,membership_diag=helper.instrumented_expand(ordered,canonical)
    require(helper.canonical_sha(expanded)==EXPECTED_V19_FAMILY_SHA[a.comparator],'instrumented v19 expansion changed stable catalogue identity')
    expanded_by={str(f['family_id']):f for f in expanded}
    require(set(expanded_by)==set(frozen_by),'expanded/frozen family-ID universe differs')
    # Scientific equality is per-family final membership/rank/source, not raw storage-list order.
    for fid in base_ids:
        cur=expanded_by[fid]; old=frozen_by[fid]
        require(int(cur['rank'])==int(old['rank']),f'expanded rank mismatch: {fid}')
        require(str(cur.get('source'))==str(old.get('source')),f'expanded source mismatch: {fid}')
        require(set(map(str,cur['event_ids']))==set(map(str,old['event_ids'])),f'expanded member-set mismatch: {fid}')

    top_ids=v19order[:TOP_K]
    base_index={fid:i for i,fid in enumerate(base_ids)}
    event_lookup={str(row['id']):row for year in YEARS for row in canonical[year]}
    post_rows=[]; top_payload=[]
    for fid in top_ids:
        core=core_by[fid]
        final_ids=sorted(set(map(str,expanded_by[fid]['event_ids'])))
        core_ids=set(map(str,core['event_ids'])); added_ids=set(final_ids)-core_ids
        require(core_ids.issubset(set(final_ids)),f'core member removed: {fid}')
        ff=copy.deepcopy(core); ff['event_ids']=final_ids
        cohesion=helper.cohesion_features(ff,event_lookup,support,base)
        expansion=[math.log1p(len(core_ids)),math.log1p(len(added_ids)),float(len(added_ids)/max(len(core_ids),1))]
        conf=accepted.get(fid,[])
        d2=[float(x['d2']) for x in conf]
        residual=[float(x['trajectory_residual']) for x in conf]
        neglogp=[-math.log(float(x['joint_conformal_p'])) for x in conf]
        d2m,d2q=helper.qpair(d2,1.5); rm,rq=helper.qpair(residual,1.5); pm,pq=helper.qpair(neglogp,-math.log(0.05))
        row=[float(x) for x in cohesion+expansion+[d2m,d2q,rm,rq,pm,pq]]
        require(len(row)==POST_DIM and all(math.isfinite(x) for x in row),f'bad post-membership row: {fid}')
        post_rows.append(row)
        top_payload.append({
            'family_id':fid,'v19_rank':int(expanded_by[fid]['rank']),'source':str(expanded_by[fid]['source']),
            'core_member_count':len(core_ids),'added_member_count':len(added_ids),'final_member_count':len(final_ids),
            'accepted_confidence_records':len(conf),'final_event_ids':final_ids,
        })

    xpost=np.asarray(post_rows,dtype=np.float64)
    xbase_top=base_features[[base_index[fid] for fid in top_ids]]
    xcombined=np.column_stack([xbase_top,xpost]).astype(np.float64,copy=False)
    require(xpost.shape==(TOP_K,POST_DIM),'post-membership feature shape changed')
    require(xcombined.shape==(TOP_K,COMBINED_DIM),'combined feature shape changed')
    require(np.all(np.isfinite(xcombined)),'nonfinite v27 combined features')

    np.save(a.output/'base_features_top100.npy',xbase_top,allow_pickle=False)
    np.save(a.output/'post_membership_features_top100.npy',xpost,allow_pickle=False)
    np.save(a.output/'combined_features_top100.npy',xcombined,allow_pickle=False)
    helper.dump(a.output/'expanded_top100_families.json',{
        'families':top_payload,'truth_accessed':False,'target_information_access':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,
    })
    manifest={
        'verdict':'PASS_V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE',
        'scientific_stage':'V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE_ONLY',
        'comparator_route':a.comparator,'years':list(YEARS),
        'stage1_builder_blob':'046795db6913c6831a0643abf30ce20055ef3024',
        'stage1_raw_array_order_scientifically_binding':False,
        'stage1_family_identity_key':'family_id',
        'stage1_top100_family_ids':top_ids,
        'base_feature_dimension':BASE_DIM,'post_membership_feature_dimension':POST_DIM,'combined_feature_dimension':COMBINED_DIM,
        'post_membership_feature_names':list(POST_FEATURE_NAMES),
        'same_run_base_feature_sha256':meta['feature_sha256'],
        'same_run_centroid_sha256':meta['centroid_sha256'],
        'stable_v19_expanded_family_sha256':EXPECTED_V19_FAMILY_SHA[a.comparator],
        'base_features_top100_sha256':helper.array_sha(xbase_top),
        'post_membership_features_top100_sha256':helper.array_sha(xpost),
        'combined_features_top100_sha256':helper.array_sha(xcombined),
        'expanded_top100_family_payload_sha256':helper.canonical_sha(top_payload),
        'membership_diagnostics':membership_diag,
        'per_family_expanded_membership_identity_pass':True,
        'successor_model_trained':False,'literature_evaluation_performed':False,
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    helper.dump(a.output/'V27_POSTMEMBERSHIP_FEATURE_MANIFEST.json',manifest)
    print(json.dumps({
        'verdict':manifest['verdict'],'route':a.comparator,
        'post_membership_features_top100_sha256':manifest['post_membership_features_top100_sha256'],
        'combined_features_top100_sha256':manifest['combined_features_top100_sha256'],
        'stable_v19_identity_pass':True,'per_family_membership_identity_pass':True,'truth_accessed':False,
    },indent=2,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
