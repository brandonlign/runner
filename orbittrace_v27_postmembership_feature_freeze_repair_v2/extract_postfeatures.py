#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v16_v15_joint_conformal_membership_v1 import expand_candidate as jc
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS = (2013, 2014)
TOP_K = 100
BASE_DIM = 71
POST_DIM = 16
COMBINED_DIM = 87
EXPECTED_RANKER_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_MODEL_SHA = 'ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED = {
    'sugar': {
        'base_feature_sha256': '486c247d12bd769f281444b4b3b9adf0ec3cd517dc88485f3deccffd8e395f1f',
        'centroid_sha256': '6f920ede2497b0cd1a5a8e303a6e87a6217fc8919deb4c81b131b1e5a5f20e91',
        'expanded_family_sha256': '911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    },
    'hdbscan': {
        'base_feature_sha256': 'd25f5e7899b2ab5dba7e7c1d1f6269896fee34714492bb53264c659db32c310d',
        'centroid_sha256': '90504db13491ba83a4dffb35892d3bd87764827b99e497bc56c80425700eab79',
        'expanded_family_sha256': '7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
    },
}
POST_FEATURE_NAMES = (
    'expanded_member_count_min_year','expanded_member_count_max_year','expanded_member_count_year_balance',
    'expanded_member_distance_median','expanded_member_distance_q90','expanded_member_distance_max','expanded_year_q90_distance_max',
    'log1p_core_member_count','log1p_added_member_count','added_to_core_ratio',
    'accepted_d2_median','accepted_d2_q90','accepted_trajectory_residual_median','accepted_trajectory_residual_q90',
    'accepted_neglog_joint_p_median','accepted_neglog_joint_p_q90',
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()


def dump(path: Path,obj: Any)->str:
    path.parent.mkdir(parents=True,exist_ok=True); raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()


def load_module(path: Path,name: str)->Any:
    import importlib.util
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def cohesion_features(family: dict[str,Any],lookup: dict[str,dict[str,Any]],support: Any,base: Any)->list[float]:
    """Exact pure seven-feature formula from pre-SonotaCo URC-v2."""
    all_distances=[]; per_year_q90=[]; counts=[]; centroids=family.get('centroids',{})
    for year in YEARS:
        ids=[str(eid) for eid in family['event_ids'] if int(str(eid)[:4])==year]; counts.append(len(ids)); c=centroids.get(str(year)); distances=[]
        if c is not None:
            for eid in ids:
                row=lookup.get(eid); require(row is not None,f'member event absent from scan: {eid}')
                d=float(support.centroid_distance(row,c,base)); require(math.isfinite(d),f'nonfinite member distance {eid}')
                distances.append(d); all_distances.append(d)
        per_year_q90.append(float(np.quantile(distances,0.90)) if distances else 10.0)
    cmin,cmax=min(counts),max(counts)
    return [float(cmin),float(cmax),float(cmin/max(cmax,1)),float(np.median(all_distances)) if all_distances else 10.0,float(np.quantile(all_distances,0.90)) if all_distances else 10.0,float(max(all_distances)) if all_distances else 10.0,float(max(per_year_q90))]


def qpair(values:list[float],sentinel:float)->tuple[float,float]:
    if not values: return float(sentinel),float(sentinel)
    x=np.asarray(values,dtype=np.float64); require(np.all(np.isfinite(x)),'nonfinite confidence')
    return float(np.median(x)),float(np.quantile(x,0.90))


def instrumented_expand(families:list[dict[str,Any]],scan_by_year:dict[int,list[dict[str,Any]]])->tuple[list[dict[str,Any]],dict[str,list[dict[str,float]]],dict[str,Any]]:
    """Exact v17 assignment semantics with observational winning-confidence capture."""
    expanded=copy.deepcopy(families); lookup={y:{str(e['id']):e for e in scan_by_year[y]} for y in YEARS}
    original={str(f['family_id']):set(map(str,f['event_ids'])) for f in expanded}; rank_by={str(f['family_id']):int(f['rank']) for f in expanded}; by={str(f['family_id']):f for f in expanded}
    top={str(f['family_id']) for f in expanded if int(f['rank'])<=TOP_K}; accepted=defaultdict(list); diag={'new_members_by_year':{},'eligible_pairs_by_year':{},'confidence_observational_only':True}
    require((jc.ALPHA,jc.DENSITY_CEILING,jc.TRAJECTORY_CEILING,jc.ACTIVITY_PADDING_DEG)==(0.05,1.5,1.5,6.0),'conformal constants changed')
    for target_year in YEARS:
        source_year=YEARS[1] if target_year==YEARS[0] else YEARS[0]; target=scan_by_year[target_year]; target_sol=np.asarray([float(e['sol'])%360.0 for e in target]); best={}; eligible_pairs=0
        for fid in sorted(top,key=lambda x:(rank_by[x],x)):
            source_ids=sorted(original[fid]&set(lookup[source_year]))
            if len(source_ids)<4: continue
            source=[lookup[source_year][eid] for eid in source_ids]; sd2=jc.source_leave_one_out_d2(source); sr=jc.loo_residuals(source)
            source_scores=jc.fisher_nonconformity(jc.source_empirical_pvalues(sd2),jc.source_empirical_pvalues(sr)); model=jc.fit_trajectory(source)
            idx=np.flatnonzero(jc.in_activity_arc(target_sol,[float(e['sol']) for e in source])); candidates=[target[int(i)] for i in idx]
            d2=jc.target_d2(candidates,source); residual=jc.trajectory_residuals(model,candidates); scores=jc.fisher_nonconformity(jc.target_empirical_pvalues(d2,sd2),jc.target_empirical_pvalues(residual,sr)); joint=jc.joint_conformal_pvalues(scores,source_scores)
            for i,d,r,s,p in zip(idx.tolist(),d2.tolist(),residual.tolist(),scores.tolist(),joint.tolist()):
                eid=str(target[i]['id'])
                if eid in original[fid] or float(d)>1.5+1e-12 or float(r)>1.5+1e-12 or float(p)<=0.05+1e-15: continue
                eligible_pairs+=1; key=(-float(p),float(s),rank_by[fid],fid); old=best.get(eid)
                if old is None or key<old[0]: best[eid]=(key,fid,float(d),float(r),float(s),float(p))
        additions=defaultdict(list)
        for eid,(_key,fid,d,r,s,p) in best.items(): additions[fid].append(eid); accepted[fid].append({'d2':d,'trajectory_residual':r,'fisher_nonconformity':s,'joint_conformal_p':p})
        for fid,ids in additions.items(): by[fid]['event_ids']=sorted(set(map(str,by[fid]['event_ids']))|set(ids))
        diag['new_members_by_year'][str(target_year)]=len(best); diag['eligible_pairs_by_year'][str(target_year)]=eligible_pairs
    diag['total_new_members']=sum(diag['new_members_by_year'].values())
    return expanded,accepted,diag


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True); p.add_argument('--base-root',type=Path,required=True); p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True); p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--original-model',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); exp=EXPECTED[a.comparator]
    require(sha(a.ranker_source)==EXPECTED_RANKER_SHA and sha(a.original_model)==EXPECTED_MODEL_SHA,'ranker/model identity changed')

    # Stage-1 is consumed, not reconstructed: exact untouched v22 builder produced these files in a separate process.
    meta=json.loads((a.base_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); base_features=np.load(a.base_root/'features.npy',allow_pickle=False); centroids=np.load(a.base_root/'centroids.npy',allow_pickle=False); frozen_members=json.loads((a.base_root/'family_memberships.json').read_text())['families']
    require(meta['feature_dimension']==BASE_DIM and meta['truth_accessed'] is False,'bad exact base manifest'); require(array_sha(base_features)==exp['base_feature_sha256']==meta['feature_sha256'],'exact base feature hash failed'); require(array_sha(centroids)==exp['centroid_sha256']==meta['centroid_sha256'],'exact centroid hash failed'); require(meta['v19_family_sha256']==exp['expanded_family_sha256'],'exact base expanded hash failed'); require(canonical_sha(frozen_members)==exp['expanded_family_sha256'],'base family payload hash failed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}; forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS: require(all(not(forbidden&{str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached extractor')
    canonical=v15_application.validate_pair(YEARS,raw); runtime,support,base,_=load_support_base(p19_module=type('Shim',(),{'mult':v17.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20); require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed'); support.CORPUS=p19.CORPUS
    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime); s19,_=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19); s20=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)['soft_families']; fams=hard['hard_families']+s19+s20; sources=['hard']*len(hard['hard_families'])+['p19']*len(s19)+['p20']*len(s20); ids=[str(f['family_id']) for f in fams]; source_by={fid:src for fid,src in zip(ids,sources)}
    require(ids==list(map(str,meta['family_ids'])),'core family universe/order differs from exact base')
    ranker=load_module(a.ranker_source,'frozen_839_v27_extract'); original=urc_application.score_and_rank(model_path=a.original_model,families=fams,source_by_id=source_by,hard_order=hard['hard_order'],scan_by_year=canonical,years=YEARS,support=support,base=base,frozen_ranker_module=ranker); qorder=list(original['order']); corder,_=v19.raw_consensus_order(fams,sources,support,base); v19order=list(v19.fusion_orders(qorder,corder)['rank_sum']); require(v19order==list(map(str,meta['v19_order'])),'v19 stage-1 order differs from exact base')
    by={str(f['family_id']):f for f in fams}; ordered=[{'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,by[fid]['event_ids']))),'source':source_by[fid]} for rank,fid in enumerate(v19order,start=1)]
    expanded,accepted,membership_diag=instrumented_expand(ordered,canonical); require(canonical_sha(expanded)==exp['expanded_family_sha256'],'instrumented expansion differs from exact base membership'); require(expanded==frozen_members,'instrumented expanded payload not byte-for-science equal to exact base')

    top_ids=v19order[:TOP_K]; id_index={fid:i for i,fid in enumerate(ids)}; expanded_by={str(f['family_id']):f for f in expanded}; lookup={str(row['id']):row for y in YEARS for row in canonical[y]}; post=[]; top_payload=[]
    for fid in top_ids:
        core=by[fid]; final_ids=sorted(set(map(str,expanded_by[fid]['event_ids']))); core_ids=set(map(str,core['event_ids'])); added=set(final_ids)-core_ids
        ff=copy.deepcopy(core); ff['event_ids']=final_ids; cohesion=cohesion_features(ff,lookup,support,base); expansion=[math.log1p(len(core_ids)),math.log1p(len(added)),float(len(added)/max(len(core_ids),1))]
        conf=accepted.get(fid,[]); d2=[float(x['d2']) for x in conf]; res=[float(x['trajectory_residual']) for x in conf]; nlp=[-math.log(float(x['joint_conformal_p'])) for x in conf]; d2m,d2q=qpair(d2,1.5); rm,rq=qpair(res,1.5); pm,pq=qpair(nlp,-math.log(0.05)); row=[float(x) for x in cohesion+expansion+[d2m,d2q,rm,rq,pm,pq]]; require(len(row)==POST_DIM and all(math.isfinite(x) for x in row),'bad post feature row'); post.append(row); top_payload.append({'family_id':fid,'v19_rank':int(expanded_by[fid]['rank']),'source':str(expanded_by[fid]['source']),'core_member_count':len(core_ids),'added_member_count':len(added),'final_member_count':len(final_ids),'accepted_confidence_records':len(conf),'final_event_ids':final_ids})
    xpost=np.asarray(post,dtype=np.float64); xbase_top=base_features[[id_index[fid] for fid in top_ids]]; combined=np.column_stack([xbase_top,xpost]).astype(np.float64,copy=False); require(xpost.shape==(TOP_K,POST_DIM) and combined.shape==(TOP_K,COMBINED_DIM),'v27 feature shape failed'); require(np.all(np.isfinite(combined)),'nonfinite v27 features')
    np.save(a.output/'base_features_top100.npy',xbase_top,allow_pickle=False); np.save(a.output/'post_membership_features_top100.npy',xpost,allow_pickle=False); np.save(a.output/'combined_features_top100.npy',combined,allow_pickle=False); dump(a.output/'expanded_top100_families.json',{'families':top_payload,'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False})
    manifest={'verdict':'PASS_V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE','scientific_stage':'V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE_ONLY','comparator_route':a.comparator,'stage1_builder':'exact untouched v22 prepare_pretruth.py executed in separate process','stage1_top100_family_ids':top_ids,'base_feature_dimension':BASE_DIM,'post_membership_feature_dimension':POST_DIM,'combined_feature_dimension':COMBINED_DIM,'post_membership_feature_names':list(POST_FEATURE_NAMES),'base_feature_sha256_full_universe':array_sha(base_features),'centroid_sha256_full_universe':array_sha(centroids),'expanded_family_sha256_full_universe':canonical_sha(expanded),'base_features_top100_sha256':array_sha(xbase_top),'post_membership_features_top100_sha256':array_sha(xpost),'combined_features_top100_sha256':array_sha(combined),'expanded_top100_family_payload_sha256':canonical_sha(top_payload),'membership_diagnostics':membership_diag,'successor_model_trained':False,'literature_evaluation_performed':False,'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}; dump(a.output/'V27_POSTMEMBERSHIP_FEATURE_MANIFEST.json',manifest); print(json.dumps({'verdict':manifest['verdict'],'route':a.comparator,'combined_sha256':manifest['combined_features_top100_sha256'],'exact_base_identity':True,'exact_membership_identity':True,'truth_accessed':False},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
