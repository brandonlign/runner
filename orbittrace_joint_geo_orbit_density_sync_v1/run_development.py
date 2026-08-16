#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent
from recurrent_eom import eom_labels, selected_eom_nodes
from density_synchronous_eom import density_synchronous_stability

YEARS=parent.YEARS
MONTH_KEYS=parent.MONTH_KEYS
BLIND=parent.BLIND
MIN_CLUSTER_SIZE=parent.MIN_CLUSTER_SIZE
MIN_SAMPLES=parent.MIN_SAMPLES
WINNER_PRELABEL_SHA='efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993'
WINNER_RESULT_SHA='ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711'
WINNER_MEMBERSHIP_SHA='e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2'
BASELINE_TOTAL_AT100=179
REQUIRED_TOTAL_AT100=184
RAW_FIELDS=('q_au','q_au_','e','i_deg','peri_deg','node_deg')


def req(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray)->str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def finite(v: Any)->bool:
    try: return v is not None and math.isfinite(float(v))
    except (TypeError,ValueError): return False


def ordered_membership_sha(candidates: list[dict[str,Any]])->str:
    payload='\n'.join('|'.join(str(x) for x in row['event_ids']) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def orbit_vector(q: float,e: float,inc_deg: float,peri_deg: float,node_deg: float)->np.ndarray:
    inc=np.radians(float(inc_deg))
    omega=np.radians(float(peri_deg)%360.0)
    node=np.radians(float(node_deg)%360.0)
    si,ci=np.sin(inc),np.cos(inc)
    so,co=np.sin(omega),np.cos(omega)
    sO,cO=np.sin(node),np.cos(node)
    h=np.asarray([si*sO,-si*cO,ci],dtype=np.float64)
    p=np.asarray([
        cO*co-sO*so*ci,
        sO*co+cO*so*ci,
        so*si,
    ],dtype=np.float64)
    v=np.concatenate((np.asarray([float(q)],dtype=np.float64),h,float(e)*p))
    req(v.shape==(7,) and np.all(np.isfinite(v)),'nonfinite ORBIT7 vector')
    req(abs(float(np.linalg.norm(h))-1.0)<1e-12,'orbital-plane normal lost unit norm')
    return v


def candidates_from_sync(labels: np.ndarray,selected_nodes: tuple[int,...],events: list[dict[str,Any]],ordinary: dict[float,float],synchronous: dict[float,float])->list[dict[str,Any]]:
    positive=sorted(int(x) for x in np.unique(labels) if int(x)>=0)
    req(positive==list(range(len(selected_nodes))),'compact labels no longer map contiguously to selected nodes')
    out=[]
    for lab,node in enumerate(selected_nodes):
        idx=np.flatnonzero(labels==lab)
        members=tuple(sorted(str(events[int(i)]['id']) for i in idx))
        req(len(members)>=MIN_CLUSTER_SIZE,f'selected JOINT13 cluster below frozen minimum: node={node}')
        out.append({
            'family_id':parent.member_hash('JOINT13-DSEOM1',members),
            'node_id':int(node),'event_ids':list(members),'member_count':len(members),
            'synchronous_stability':float(synchronous[float(node)]),
            'ordinary_stability':float(ordinary[float(node)]),
        })
    out.sort(key=lambda f:(-float(f['synchronous_stability']),-float(f['ordinary_stability']),-int(f['member_count']),str(f['family_id'])))
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--winner-prelabel-json',type=Path,required=True)
    p.add_argument('--winner-result-json',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha(a.quality_source)==parent.QUALITY_SHA,'frozen GMN utility source changed')
    req(sha(a.v8_result_json)==parent.V8_RESULT_SHA,'frozen GMN support result changed')
    req(sha(a.winner_prelabel_json)==WINNER_PRELABEL_SHA,'binding winner prelabel changed')
    req(sha(a.winner_result_json)==WINNER_RESULT_SHA,'binding winner result changed')
    winner_pre=json.loads(a.winner_prelabel_json.read_text())
    winner_result=json.loads(a.winner_result_json.read_text())
    req(winner_pre['successor_ordered_membership_sha256']==WINNER_MEMBERSHIP_SHA,'winner membership hash changed')
    req(winner_result['successor_ordered_membership_sha256']==WINNER_MEMBERSHIP_SHA,'winner result membership hash changed')
    baseline=winner_result['successor_metrics']
    req(sum(int(baseline[str(y)]['recovered_at_100']) for y in YEARS)==BASELINE_TOTAL_AT100,'binding baseline total changed')
    req(int(baseline['2022']['recovered_at_100'])==89 and int(baseline['2023']['recovered_at_100'])==90,'binding annual @100 changed')

    qmod=parent.load_module(a.quality_source,'joint13_density_sync_frozen_gmn_utility')
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS='orbittrace-joint13-density-sync-v1-development-2022-2023-target-excluded'
    support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)

    safe_orbit_by_id: dict[str,dict[str,Any]]={}
    original=support.read_gmn_frame
    raw_rows=0; excluded_before_orbit=0; nonfinite_sol_rows=0; frame_count=0
    def wrapped(text: str):
        nonlocal raw_rows,excluded_before_orbit,nonfinite_sol_rows,frame_count
        frame=original(text); frame_count+=1; raw_rows+=len(frame)
        req('unique_trajectory_identifier' in frame.columns,'raw GMN ID column missing')
        req('sol_lon_deg' in frame.columns,'raw GMN solar-longitude column missing')
        sol=np.asarray(frame['sol_lon_deg'],dtype=float)%360.0
        finite_sol=np.isfinite(sol)
        safe_mask=finite_sol&~((sol>=BLIND[0])&(sol<=BLIND[1]))
        nonfinite_sol_rows+=int(np.sum(~finite_sol))
        excluded_before_orbit+=int(np.sum(finite_sol&~safe_mask))
        cols=['unique_trajectory_identifier']+[f for f in RAW_FIELDS if f in frame.columns]
        safe=frame.loc[safe_mask,cols]
        for row in safe.itertuples(index=False,name=None):
            eid=str(row[0])
            req(eid not in safe_orbit_by_id,f'duplicate safe raw trajectory ID: {eid}')
            safe_orbit_by_id[eid]={k:v for k,v in zip(cols[1:],row[1:])}
        return frame
    support.read_gmn_frame=wrapped
    scan,_cal,hidden_sealed,sources=support.parse_catalogue(base)
    req(frame_count==24,f'expected 24 GMN raw frames, got {frame_count}')
    req(sorted(scan)==list(YEARS),f'GMN runtime accessed wrong years: {sorted(scan)}')
    req([x['key'] for x in sources]==list(MONTH_KEYS),'GMN source list changed')

    accessible_events=[]
    for year in YEARS:
        raw=list(scan[year])
        rows=[parent.normalize_event(row,year) for row in raw]
        req(len(rows)==len(raw),f'event normalization changed {year} count')
        accessible_events.extend(rows)
    req(len(accessible_events)==738682,f'accessibile pooled event count changed: {len(accessible_events)}')
    req(len({e['id'] for e in accessible_events})==len(accessible_events),'duplicate accessible IDs')
    req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in accessible_events),'protected region survived parser')

    # GEO6 is exact inherited representation for all accessible events.
    geo=np.asarray(parent.geo_matrix(accessible_events),dtype=np.float64)
    req(geo.shape==(len(accessible_events),6) and np.all(np.isfinite(geo)),'GEO6 matrix changed or nonfinite')

    joint_events=[]; vectors=[]; missing_raw=0; incomplete=0; invalid=0; fallback_q=0
    eligible_by_year={y:0 for y in YEARS}
    for idx,e0 in enumerate(accessible_events):
        eid=str(e0['id']); raw=safe_orbit_by_id.get(eid)
        if raw is None:
            missing_raw+=1; continue
        q_primary=raw.get('q_au'); q_fallback=raw.get('q_au_')
        if finite(q_primary): q=float(q_primary)
        elif finite(q_fallback): q=float(q_fallback); fallback_q+=1
        else:
            incomplete+=1; continue
        if not all(finite(raw.get(f)) for f in ('e','i_deg','peri_deg','node_deg')):
            incomplete+=1; continue
        ecc=float(raw['e']); inc=float(raw['i_deg']); peri=float(raw['peri_deg']); node=float(raw['node_deg'])
        if not(q>0.0 and ecc>=0.0 and 0.0<=inc<=180.0):
            invalid+=1; continue
        ov=orbit_vector(q,ecc,inc,peri,node)
        j=np.concatenate((geo[idx],ov)).astype(np.float64,copy=False)
        req(j.shape==(13,) and np.all(np.isfinite(j)),'nonfinite JOINT13 vector')
        joint_events.append({'id':eid,'year':int(e0['year'])})
        vectors.append(j); eligible_by_year[int(e0['year'])]+=1
    req(len(vectors)>=100,'fewer than 100 joint-eligible events')
    X=np.vstack(vectors).astype(np.float64,copy=False)
    years=np.asarray([e['year'] for e in joint_events],dtype=np.int64)
    req(X.shape==(len(joint_events),13),'JOINT13 matrix shape mismatch')
    req(np.all(np.isfinite(X)),'nonfinite JOINT13 matrix')

    model=hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,min_samples=MIN_SAMPLES,metric='euclidean',
        cluster_selection_method='eom',cluster_selection_epsilon=0.0,
        allow_single_cluster=False,prediction_data=False,
    ).fit(X)
    tree=model.condensed_tree_._raw_tree
    frozen_tree_sha=tree_sha(tree)
    ordinary=compute_stability(tree)
    synchronous,_annual_parent,annual_reconstructed=density_synchronous_stability(tree,years)
    req(tree_sha(tree)==frozen_tree_sha,'density-sync kernel mutated JOINT13 condensed tree')
    labels=eom_labels(tree,synchronous)
    nodes=selected_eom_nodes(tree,synchronous)
    req(len(nodes)==len(set(int(x) for x in labels if int(x)>=0)),'JOINT13 selected-node/label count mismatch')
    candidates=candidates_from_sync(labels,nodes,joint_events,ordinary,synchronous)
    candidate_count=len(candidates); largest=max((int(x['member_count']) for x in candidates),default=0)
    membership_sha=ordered_membership_sha(candidates)
    structural={
        'at_least_100_candidates':candidate_count>=100,
        'largest_family_at_most_1pct_all_accessible':largest<=int(np.floor(0.01*len(accessible_events))),
        'differs_from_binding_winner':membership_sha!=WINNER_MEMBERSHIP_SHA,
    }

    prelabel={
        'scientific_role':'PRELABEL_FROZEN_JOINT13_DENSITY_SYNC_V1',
        'representation':'JOINT13_RAW_GEO6_PLUS_ORBIT7',
        'view_1':'EXACT_INHERITED_GEO6',
        'view_2':'ORBIT7_Q_PLANE_NORMAL_ECCENTRICITY_VECTOR',
        'relative_view_weight':None,
        'normalization_or_fitted_scale':None,
        'raw_field_contract':{'q_primary':'q_au','q_fallback':'q_au_','e':'e','inclination':'i_deg','perihelion_argument':'peri_deg','ascending_node':'node_deg'},
        'firewall_order':'raw_id_and_sol_only_then_20_55_exclusion_then_orbit_fields',
        'raw_rows':raw_rows,'raw_rows_excluded_before_orbit_access':excluded_before_orbit,'raw_rows_nonfinite_sol_not_orbit_accessed':nonfinite_sol_rows,
        'accessible_events':len(accessible_events),'joint_eligible_events':len(joint_events),
        'joint_eligible_by_year':{str(y):eligible_by_year[y] for y in YEARS},
        'missing_safe_raw_id_count':missing_raw,'incomplete_orbit_count':incomplete,'invalid_physical_orbit_count':invalid,'q_fallback_used_count':fallback_q,
        'condensed_tree_sha256':frozen_tree_sha,'selected_density_synchronous_nodes':list(nodes),
        'candidate_count':candidate_count,'largest_family_members':largest,
        'ordered_membership_sha256':membership_sha,'binding_winner_ordered_membership_sha256':WINNER_MEMBERSHIP_SHA,
        'structural_gates':structural,'candidates':candidates,
        'annual_reconstructed_eom':{str(k):list(v) for k,v in sorted(annual_reconstructed.items())},
        'hdbscan':{'min_cluster_size':MIN_CLUSTER_SIZE,'min_samples':MIN_SAMPLES,'metric':'euclidean','cluster_selection_method':'eom','cluster_selection_epsilon':0.0,'allow_single_cluster':False,'prediction_data':False},
        'known_shower_labels_indexed':False,'protected_row_orbit_fields_accessed':False,
        'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,
        'sonotaco_2013_2014_access':False,'asfn_access':False,'efn_access':False,'amos_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    prelabel_path=a.output/'JOINT13_DENSITY_SYNC_V1_PRELABEL.json'
    prelabel_path.write_text(json.dumps(prelabel,indent=2,sort_keys=True,allow_nan=False)+'\n')
    prelabel_sha=sha(prelabel_path)

    hidden=hidden_sealed
    ids_by_year={y:{str(e['id']) for e in accessible_events if int(e['year'])==y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),'label outside accessible GMN IDs')
    successor={str(y):parent.metrics(candidates,hidden,ids_by_year[y]) for y in YEARS}
    annual_gates={str(y):parent.annual_gate(baseline[str(y)],successor[str(y)]) for y in YEARS}
    successor_total=sum(int(successor[str(y)]['recovered_at_100']) for y in YEARS)
    gain=successor_total-BASELINE_TOTAL_AT100
    passed=bool(all(structural.values()) and successor_total>=REQUIRED_TOTAL_AT100 and all(all(g.values()) for g in annual_gates.values()))
    verdict='PASS_JOINT13_DENSITY_SYNC_V1_GMN_DEVELOPMENT' if passed else 'FAIL_JOINT13_DENSITY_SYNC_V1_GMN_DEVELOPMENT'
    result={
        'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY',
        'prelabel_sha256':prelabel_sha,'representation':prelabel['representation'],'relative_view_weight':None,'normalization_or_fitted_scale':None,
        'accessible_events':len(accessible_events),'joint_eligible_events':len(joint_events),'joint_eligible_by_year':prelabel['joint_eligible_by_year'],
        'candidate_count':candidate_count,'largest_family_members':largest,'ordered_membership_sha256':membership_sha,
        'binding_winner_ordered_membership_sha256':WINNER_MEMBERSHIP_SHA,'structural_gates':structural,
        'baseline_metrics':baseline,'successor_metrics':successor,'annual_gates':annual_gates,
        'baseline_total_recovered_at_100':BASELINE_TOTAL_AT100,'successor_total_recovered_at_100':successor_total,
        'recovered_at_100_gain':gain,'required_total_recovered_at_100':REQUIRED_TOTAL_AT100,'required_gain':5,
        'protected_row_orbit_fields_accessed':False,'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,
        'sonotaco_2013_2014_access':False,'asfn_access':False,'efn_access':False,'amos_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    (a.output/'JOINT13_DENSITY_SYNC_V1_GMN_DEVELOPMENT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({
        'verdict':verdict,'joint_eligible_events':len(joint_events),'joint_eligible_by_year':prelabel['joint_eligible_by_year'],
        'candidate_count':candidate_count,'largest_family_members':largest,'baseline_total_at100':BASELINE_TOTAL_AT100,'successor_total_at100':successor_total,'gain':gain,
        '2022':{k:successor['2022'][k] for k in ('recovered_at_50','recovered_at_100','top100_dominant_precision','mrr','fragmentation_median_top500')},
        '2023':{k:successor['2023'][k] for k in ('recovered_at_50','recovered_at_100','top100_dominant_precision','mrr','fragmentation_median_top500')},
    },indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
