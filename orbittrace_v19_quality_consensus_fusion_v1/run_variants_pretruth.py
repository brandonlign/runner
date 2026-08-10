#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
CONSENSUS_RADIUS=1.0
CONSENSUS_QUALITY_WEIGHT=2.0
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_V17_FAMILY_SHA={
    'sugar':'f019263cc23db60156324e0d24d327e3468638e3ef041b1aba7bd50dd0b03ca7',
    'hdbscan':'3010de4819e16d218f083b8d645c2443f7d2d3dfc81723f488a97150a49358ed',
}
VARIANTS=('consensus_only','rank_sum','rank_product','v17_control')


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

def circular_diff(a: float,b: float)->float:
    return abs((float(a)-float(b)+180.0)%360.0-180.0)

def pair_distance(a: dict[str,Any],b: dict[str,Any],support: Any,base: Any)->float:
    ds=[]
    for year in YEARS:
        ca=a.get('centroids',{}).get(str(year)); cb=b.get('centroids',{}).get(str(year))
        if ca is None or cb is None:
            return math.inf
        ds.append(float(support.centroid_distance(ca,cb,base)))
    return max(ds)

def candidate_bins(families: list[dict[str,Any]])->dict[int,list[int]]:
    bins: dict[int,list[int]]=defaultdict(list)
    first=str(YEARS[0])
    for i,f in enumerate(families):
        c=f.get('centroids',{}).get(first)
        require(c is not None,f'missing {first} centroid: {f["family_id"]}')
        bins[int(math.floor(float(c['sol'])))%360].append(i)
    return bins

def build_edges(families: list[dict[str,Any]],support: Any,base: Any)->list[tuple[float,int,int]]:
    bins=candidate_bins(families); edges=[]; seen=set(); first=str(YEARS[0])
    for i,f in enumerate(families):
        c=f['centroids'][first]; center=int(math.floor(float(c['sol'])))%360
        for off in range(-7,8):
            for j in bins.get((center+off)%360,[]):
                if j<=i or (i,j) in seen: continue
                seen.add((i,j)); g=families[j]; c2=g['centroids'][first]
                if circular_diff(c['sol'],c2['sol'])>7.0: continue
                if abs(float(c['ecl_lat'])-float(c2['ecl_lat']))>4.0: continue
                if abs(float(c['vg'])-float(c2['vg']))>4.0: continue
                d=pair_distance(f,g,support,base)
                if d<=CONSENSUS_RADIUS: edges.append((float(d),i,j))
    return edges

def source_rank_percentiles(sources: list[str])->list[float]:
    totals=Counter(sources); seen=Counter(); out=[]
    for src in sources:
        seen[src]+=1
        out.append((seen[src]-1)/max(totals[src]-1,1))
    return out

def raw_consensus_order(families: list[dict[str,Any]],sources: list[str],support: Any,base: Any)->tuple[list[str],dict[str,Any]]:
    edges=build_edges(families,support,base)
    adj=[set([i]) for i in range(len(families))]
    for d,i,j in edges:
        require(d<=CONSENSUS_RADIUS+1e-12,'edge radius violation')
        adj[i].add(j); adj[j].add(i)
    source_pct=source_rank_percentiles(sources); scores=[]
    for i,f in enumerate(families):
        nb=adj[i]; nb_sources={sources[j] for j in nb}; cross=sum(sources[j]!=sources[i] for j in nb); degree=len(nb)-1
        score=(
            3.0*(len(nb_sources)-1)
            +1.5*math.log1p(cross)
            +0.35*math.log1p(degree)
            -CONSENSUS_QUALITY_WEIGHT*source_pct[i]
        )
        scores.append((score,len(nb_sources),cross,degree,-source_pct[i],str(f['family_id']),i))
    scores.sort(reverse=True)
    order=[str(families[row[-1]]['family_id']) for row in scores]
    diag={
        'source_pr':843,
        'source_result_run':31343198282,
        'source_result_artifact':9046478671,
        'radius':CONSENSUS_RADIUS,
        'source_quality_weight':CONSENSUS_QUALITY_WEIGHT,
        'edge_count':len(edges),
        'families_with_cross_source_neighbor':sum(any(sources[j]!=sources[i] for j in adj[i]) for i in range(len(families))),
        'order_sha256':hashlib.sha256('\n'.join(order).encode()).hexdigest(),
        'pre_suppression_score_only':True,
        'family_deletion':False,
    }
    return order,diag

def fusion_orders(quality_order: list[str],consensus_order: list[str])->dict[str,list[str]]:
    require(set(quality_order)==set(consensus_order),'fusion universes differ')
    q={fid:i+1 for i,fid in enumerate(quality_order)}; c={fid:i+1 for i,fid in enumerate(consensus_order)}
    rank_sum=sorted(quality_order,key=lambda fid:(q[fid]+c[fid],q[fid],c[fid],fid))
    rank_product=sorted(quality_order,key=lambda fid:(q[fid]*c[fid],q[fid]+c[fid],q[fid],c[fid],fid))
    return {'consensus_only':list(consensus_order),'rank_sum':rank_sum,'rank_product':rank_product,'v17_control':list(quality_order)}


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
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v19 candidate generation')
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
    source_by_id={str(f['family_id']):src for f,src in zip(union,sources)}
    require(len(source_by_id)==len(union),'union family IDs collide')

    frozen_ranker=load_module(a.active_ranker_source,'frozen_active_urc_v19')
    quality=urc_application.score_and_rank(
        model_path=a.model_joblib,families=union,source_by_id=source_by_id,hard_order=hard['hard_order'],
        scan_by_year=canonical,years=YEARS,support=support,base=base,frozen_ranker_module=frozen_ranker,
    )
    quality_order=list(quality['order'])
    consensus_order,consensus_diag=raw_consensus_order(union,sources,support,base)
    orders=fusion_orders(quality_order,consensus_order)
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
        if variant=='v17_control':
            require(family_sha==EXPECTED_V17_FAMILY_SHA[a.comparator],f'{a.comparator} v17 control family identity failed')
        payload={
            'method':'OrbitTrace v19 quality-consensus fusion development',
            'variant':variant,'comparator_pair':a.comparator,'years':list(YEARS),'family_count':len(expanded),'families':expanded,
            'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
            'quality_order_sha256':hashlib.sha256('\n'.join(quality_order).encode()).hexdigest(),
            'consensus_order_sha256':consensus_diag['order_sha256'],
            'variant_order_sha256':hashlib.sha256('\n'.join(order).encode()).hexdigest(),
            'consensus_diagnostics':consensus_diag,
            'membership_diagnostics':membership_diag,
            'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
        }
        out=a.output/variant/'candidate_primary_output.json'; payload_sha=dump(out,payload)
        variant_rows.append({'variant':variant,'candidate_output_sha256':payload_sha,'families_sha256':family_sha,'order_sha256':payload['variant_order_sha256'],'membership_total_new':membership_diag['total_new_members']})

    manifest={
        'verdict':'PASS_V19_ALL_VARIANTS_PRETRUTH_FREEZE','comparator':a.comparator,'years':list(YEARS),
        'variants':variant_rows,'successor_variants':['consensus_only','rank_sum','rank_product'],'v17_control':'v17_control',
        'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
        'consensus_diagnostics':consensus_diag,
        'rank_fusion_parameter_search':False,
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V19_PRETRUTH_VARIANT_MANIFEST.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k!='variants'},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
