#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
GEOMETRIC_RADIUS=1.0
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_V19_RANK_SUM_FAMILY_SHA={
    'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}
VARIANTS=('cross_source_firstpass','all_source_firstpass','rank_sum_control')


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path: Path,obj: Any)->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot load {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def adjacency_from_edges(
    n: int,
    edges: list[tuple[float,int,int]],
    sources: list[str],
    *,
    cross_source_only: bool,
)->list[set[int]]:
    out=[set() for _ in range(n)]
    for d,i,j in edges:
        require(d<=GEOMETRIC_RADIUS+1e-12,'unexpected edge beyond fixed radius')
        if cross_source_only and sources[i]==sources[j]:
            continue
        out[i].add(j); out[j].add(i)
    return out


def firstpass_with_backfill(
    base_order: list[str],
    ids: list[str],
    adj: list[set[int]],
)->tuple[list[str],dict[str,Any]]:
    require(len(base_order)==len(ids) and set(base_order)==set(ids),'first-pass universe mismatch')
    pos={fid:i for i,fid in enumerate(ids)}
    accepted: list[str]=[]
    deferred: list[str]=[]
    accepted_idx:set[int]=set()
    for fid in base_order:
        i=pos[fid]
        if any(j in accepted_idx for j in adj[i]):
            deferred.append(fid)
        else:
            accepted.append(fid)
            accepted_idx.add(i)
    out=accepted+deferred
    require(len(out)==len(ids) and set(out)==set(ids),'first-pass backfill lost candidates')
    return out,{
        'input_family_count':len(ids),
        'first_pass_count':len(accepted),
        'deferred_backfill_count':len(deferred),
        'first_pass_sha256':hashlib.sha256('\n'.join(accepted).encode()).hexdigest(),
        'full_order_sha256':hashlib.sha256('\n'.join(out).encode()).hexdigest(),
        'family_deletion':False,
        'budget_specific_logic':False,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--active-ranker-source',type=Path,required=True); p.add_argument('--model-joblib',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.active_ranker_source)==EXPECTED_RANKER_SHA,'#839 ranker source changed')
    require(sha(a.model_joblib)==EXPECTED_MODEL_SHA,'#853 serialized model changed')
    require(abs(float(v19.CONSENSUS_RADIUS)-GEOMETRIC_RADIUS)<1e-15,'v19/#843 radius identity changed')
    require(abs(float(v19.CONSENSUS_QUALITY_WEIGHT)-2.0)<1e-15,'v19/#843 source-quality weight changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(x['year'])==year for x in raw[year]),f'invalid {year} rows')
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v20 candidate generation')
    canonical=v15_application.validate_pair(YEARS,raw)

    runtime,support,base,_=load_support_base(
        p19_module=type('Shim',(),{'mult':v17.MULT})(),
        support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,
    )
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed')
    support.CORPUS=p19.CORPUS

    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    p19_soft,p19_diag=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    p20_result=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)
    p20_soft=p20_result['soft_families']
    union=hard['hard_families']+p19_soft+p20_soft
    sources=['hard']*len(hard['hard_families'])+['p19']*len(p19_soft)+['p20']*len(p20_soft)
    ids=[str(f['family_id']) for f in union]
    source_by_id={fid:src for fid,src in zip(ids,sources)}
    require(len(ids)==len(set(ids))==len(source_by_id),'union family IDs collide')

    frozen_ranker=load_module(a.active_ranker_source,'frozen_active_urc_v20')
    quality=urc_application.score_and_rank(
        model_path=a.model_joblib,families=union,source_by_id=source_by_id,hard_order=hard['hard_order'],
        scan_by_year=canonical,years=YEARS,support=support,base=base,frozen_ranker_module=frozen_ranker,
    )
    quality_order=list(quality['order'])
    consensus_order,consensus_diag=v19.raw_consensus_order(union,sources,support,base)
    rank_sum=list(v19.fusion_orders(quality_order,consensus_order)['rank_sum'])

    edges=v19.build_edges(union,support,base)
    all_adj=adjacency_from_edges(len(union),edges,sources,cross_source_only=False)
    cross_adj=adjacency_from_edges(len(union),edges,sources,cross_source_only=True)
    cross_order,cross_diag=firstpass_with_backfill(rank_sum,ids,cross_adj)
    all_order,all_diag=firstpass_with_backfill(rank_sum,ids,all_adj)
    cross_edge_count=sum(1 for _d,i,j in edges if sources[i]!=sources[j])
    orders={
        'cross_source_firstpass':cross_order,
        'all_source_firstpass':all_order,
        'rank_sum_control':rank_sum,
    }
    diagnostics={
        'fixed_radius':GEOMETRIC_RADIUS,
        'direct_edge_count':len(edges),
        'cross_source_direct_edge_count':cross_edge_count,
        'cross_source_firstpass':cross_diag,
        'all_source_firstpass':all_diag,
        'base_rank_sum_order_sha256':hashlib.sha256('\n'.join(rank_sum).encode()).hexdigest(),
        'source_pr_for_geometry':843,
        'source_pr_for_rank_sum':943,
    }

    by_id={str(f['family_id']):f for f in union}
    variant_rows=[]
    for variant in VARIANTS:
        order=orders[variant]
        ordered=[]
        for rank,fid in enumerate(order,start=1):
            f=by_id[fid]
            ordered.append({'family_id':fid,'rank':rank,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by_id[fid]})
        expanded,membership_diag=v17.expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)
        family_sha=canonical_sha(expanded)
        if variant=='rank_sum_control':
            require(family_sha==EXPECTED_V19_RANK_SUM_FAMILY_SHA[a.comparator],f'{a.comparator} v19 rank-sum control identity failed')
        payload={
            'method':'OrbitTrace v20 geometric first-pass exposed development',
            'variant':variant,'comparator_pair':a.comparator,'years':list(YEARS),
            'family_count':len(expanded),'families':expanded,
            'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
            'quality_order_sha256':hashlib.sha256('\n'.join(quality_order).encode()).hexdigest(),
            'consensus_order_sha256':consensus_diag['order_sha256'],
            'base_rank_sum_order_sha256':diagnostics['base_rank_sum_order_sha256'],
            'variant_order_sha256':hashlib.sha256('\n'.join(order).encode()).hexdigest(),
            'geometric_firstpass_diagnostics':diagnostics,
            'membership_diagnostics':membership_diag,
            'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
        }
        out=a.output/variant/'candidate_primary_output.json'; payload_sha=dump(out,payload)
        variant_rows.append({
            'variant':variant,'candidate_output_sha256':payload_sha,'families_sha256':family_sha,
            'order_sha256':payload['variant_order_sha256'],'membership_total_new':membership_diag['total_new_members'],
        })

    manifest={
        'verdict':'PASS_V20_ALL_VARIANTS_PRETRUTH_FREEZE','comparator':a.comparator,'years':list(YEARS),
        'variants':variant_rows,'successor_variants':['cross_source_firstpass','all_source_firstpass'],
        'v19_control':'rank_sum_control',
        'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
        'geometric_firstpass_diagnostics':diagnostics,
        'radius_search':False,'budget_specific_logic':False,'family_deletion':False,
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V20_PRETRUTH_VARIANT_MANIFEST.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k!='variants'},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
