#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_probabilistic_membership_p1 import maarsy_2018_2019_transport as transport
from orbittrace_label_free_sparse_support_v6 import run_development as v8core
from orbittrace_pooled_year_centroid_v8 import run_development as v8comp

YEARS=transport.YEARS
MIN_RECURRENT_FAMILIES=100
P1_SOURCE_SHA256='e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508'
P1_TRANSFER_BLOB='498daf762bc82a664679998ea751feecff8033de'
V8_SOURCE_COMMIT='c9d6c44704013ba0c9430100e98a29a56b453304'


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def sha256_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def configure_years(module:Any)->None:
    for obj in (module,getattr(module,'mult',None)):
        if obj is None: continue
        if hasattr(obj,'YEARS'): obj.YEARS=YEARS
        if hasattr(obj,'MONTH_KEYS'): obj.MONTH_KEYS=tuple()


def reconstruct_promoted_v8(scan:dict[int,list[dict[str,Any]]],args:argparse.Namespace)->tuple[list[dict[str,Any]],list[str],dict[str,Any],Any]:
    configure_years(v8core); configure_years(v8comp); configure_years(v8comp.mult)
    require(all(v8comp.mult.v3.self_test().values()) and all(v8comp.mult.brown.self_test().values()),'promoted-v8 scorer self-test failed')
    runtime=v8comp.mult.load_frozen_runtime(); support=runtime.load_support_module(args.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS='orbittrace-p1-maarsy-2018-2019-external'
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    _candidate,base,_scorer=support.load_sources(args)
    components=[]; year_audits=[]
    for year in YEARS:
        audit,_passing,year_components=v8core.label_free_scan_year(year,scan[year],support,base)
        require(int(audit['scannable_bin_count'])>=24,f'insufficient promoted-v8 scannable bins {year}')
        year_audits.append(audit); components.extend(year_components)
    families,_support_rankings=support.build_families(components,base)
    by_component={str(c['component_id']):c for c in components}; lookup={y:{str(e['id']):e for e in scan[y]} for y in YEARS}
    for family in families:
        centers={}
        for year in YEARS:
            cs=[by_component[str(cid)] for cid in family['component_ids'] if int(by_component[str(cid)]['year'])==year]
            require(cs,f"family {family['family_id']} lacks {year} component")
            ids=sorted(set().union(*(set(map(str,c['event_ids'])) for c in cs)))
            require(ids and all(eid in lookup[year] for eid in ids),f"family {family['family_id']} seed lookup failed")
            centers[str(year)]=v8comp.pooled_centroid([lookup[year][eid] for eid in ids],support)
        family['centroids']=centers
    v8comp.mult.YEARS=YEARS; v8comp.mult.MONTH_KEYS=tuple(); v8comp.mult.TOP_K=100
    scored,scoring_summary=v8comp.mult.score_families(families,scan,runtime,base)
    order=[str(x) for x in v8comp.mult.rank_scored(scored,'multiplicity')]
    by_id={str(f['family_id']):f for f in families}
    require(len(order)==len(by_id) and set(order)==set(by_id),'promoted-v8 order/family universe mismatch')
    normalized=[]
    for rank,fid in enumerate(order,start=1):
        f=by_id[fid]; ids=sorted(set(map(str,f['event_ids'])))
        require(ids and sorted(map(int,f['years']))==list(YEARS),f'bad promoted-v8 family {fid}')
        normalized.append({'family_id':fid,'rank':rank,'years':list(YEARS),'event_ids':ids,'centroids':f['centroids']})
    return normalized,order,{'year_audits':year_audits,'scoring_summary':scoring_summary,'component_count':len(components),'family_count':len(normalized)},base


def exact_membership_with_audit(p1:Any,transfer:Any,families:list[dict[str,Any]],scan:dict[int,list[dict[str,Any]]],base:Any)->tuple[list[dict[str,Any]],dict[str,Any]]:
    require(float(p1.INNER_PROB)==0.99 and float(p1.OUTER_PROB)==0.9999,'P1 containment changed')
    require(float(p1.BACKGROUND_UPPER_CONFIDENCE)==0.95 and float(p1.MAP_THRESHOLD)==0.5,'P1 background/responsibility changed')
    transfer.YEARS=YEARS
    event_lookup={year:{str(e['id']):e for e in scan[year]} for year in YEARS}
    arrays={year:p1.event_arrays(scan[year]) for year in YEARS}
    global_seeds=set().union(*(set(map(str,f['event_ids'])) for f in families))
    inner_d2=float(p1.chi2.ppf(p1.INNER_PROB,4)); outer_d2=float(p1.chi2.ppf(p1.OUTER_PROB,4))
    inner_v=p1.volume4_from_d2(inner_d2); shell_v=p1.volume4_from_d2(outer_d2)-inner_v
    proposals_by_event:dict[str,list[dict[str,Any]]]=defaultdict(list)
    shell_pairs=[]; candidate_pairs=[]; family_model_audit=[]
    for family_index,family in enumerate(families):
        inv_cov,logdet,centers,cov_audit=transfer.p1_covariance_for_panel_family(p1,family,event_lookup,base)
        sqrt_det=math.exp(0.5*logdet)
        for year in YEARS:
            ids=arrays[year]['ids']; events=arrays[year]['events']; x=p1.residual_matrix(events,centers[year],base)
            d2=np.einsum('ij,jk,ik->i',x,inv_cov,x,optimize=True)
            nonseed=np.asarray([str(eid) not in global_seeds for eid in ids],dtype=bool)
            shell=nonseed&(d2>inner_d2)&(d2<=outer_d2); inner=nonseed&(d2<=inner_d2)
            n_shell=int(np.sum(shell)); n_inner=int(np.sum(inner))
            shell_upper=p1.poisson_rate_upper(n_shell,p1.BACKGROUND_UPPER_CONFIDENCE)
            lambda_bg=float(shell_upper/(sqrt_det*shell_v)); expected_bg=float(lambda_bg*sqrt_det*inner_v)
            seed_count=sum(str(eid) in event_lookup[year] for eid in family['event_ids'])
            excess=max(0.0,float(n_inner)-expected_bg); stream_total=(float(seed_count)+excess)/p1.INNER_PROB
            for idx in np.flatnonzero(shell).tolist():
                shell_pairs.append({'family_id':str(family['family_id']),'family_index':family_index,'year':year,'event_id':str(ids[idx]),'d2':float(d2[idx])})
            idxs=np.flatnonzero(inner)
            intensities=np.asarray([],dtype=np.float64)
            if idxs.size:
                normalizer=((2.0*math.pi)**-2)/sqrt_det; intensities=stream_total*normalizer*np.exp(-0.5*d2[idxs])
            for idx,intensity in zip(idxs.tolist(),intensities.tolist()):
                if intensity<=0.0: continue
                rec={'family_id':str(family['family_id']),'family_index':family_index,'year':year,'event_id':str(ids[idx]),'d2':float(d2[idx]),'stream_intensity':float(intensity),'background_intensity_upper':lambda_bg}
                candidate_pairs.append(rec); proposals_by_event[str(ids[idx])].append(dict(rec))
            family_model_audit.append({'family_id':str(family['family_id']),'year':year,'seed_count':int(seed_count),'n_inner_nonseed':n_inner,'n_shell_nonseed':n_shell,'background_intensity_upper':lambda_bg,'expected_background_inner':expected_bg,'estimated_nonseed_excess':float(excess),'estimated_stream_total':float(stream_total),**cov_audit})
    assignments={}; competition=[]
    for eid in sorted(proposals_by_event):
        props=proposals_by_event[eid]; require(eid not in global_seeds,'seed entered P1 competition')
        total_stream=float(sum(p['stream_intensity'] for p in props)); background=float(max(p['background_intensity_upper'] for p in props)); denom=total_stream+background
        ranked=sorted(props,key=lambda p:(-p['stream_intensity'],p['d2'],p['family_index'],p['family_id']))
        best=ranked[0]; posterior=float(best['stream_intensity']/denom) if denom>0 else 0.0
        assigned=posterior>p1.MAP_THRESHOLD
        competition.append({'event_id':eid,'year':int(best['year']),'proposal_count':len(props),'total_stream_intensity':total_stream,'background_intensity':background,'winning_family_id':str(best['family_id']),'winning_family_index':int(best['family_index']),'winning_posterior':posterior,'assigned':assigned,'proposals':ranked})
        if assigned: assignments[eid]={**best,'posterior':posterior}
    additions:dict[int,list[str]]=defaultdict(list)
    for eid,rec in assignments.items(): additions[int(rec['family_index'])].append(eid)
    expanded=[]
    for idx,family in enumerate(families):
        out=json.loads(json.dumps(family)); seeds=set(map(str,family['event_ids'])); added=sorted(set(additions.get(idx,[]))-global_seeds)
        out['p1_added_event_ids']=added; out['p1_added_event_count']=len(added); out['event_ids']=sorted(seeds|set(added)); out['event_count']=len(out['event_ids']); expanded.append(out)
    canonical_expanded,canonical_diag=transfer.apply_exact_p1_membership(p1,families,scan,base)
    require(canonical_sha(canonical_expanded)==canonical_sha(expanded),'audited P1 implementation differs from frozen exact P1 membership')
    require(int(canonical_diag['assigned_nonseed_events'])==len(assignments),'P1 assignment count differs from frozen implementation')
    assigned_ids=set(assignments)
    shell_by_family_year:dict[tuple[str,int],list[str]]=defaultdict(list)
    for pair in shell_pairs:
        if pair['event_id'] not in assigned_ids: shell_by_family_year[(str(pair['family_id']),int(pair['year']))].append(str(pair['event_id']))
    controls=[]; addition_pairs=[]
    for family in expanded:
        fid=str(family['family_id'])
        for year in YEARS:
            added=[eid for eid in family['p1_added_event_ids'] if int(transport.parse_event_id(eid)[0])==year]
            for eid in added: addition_pairs.append({'family_id':fid,'year':year,'event_id':eid})
            if not added: continue
            pool=sorted(set(shell_by_family_year.get((fid,year),[])),key=lambda eid:(hashlib.sha256((eid+fid).encode()).hexdigest(),eid))
            for eid in pool[:len(added)]: controls.append({'family_id':fid,'year':year,'event_id':eid,'selection_sha256':hashlib.sha256((eid+fid).encode()).hexdigest()})
    audit={'inner_d2':inner_d2,'outer_d2':outer_d2,'candidate_pairs':candidate_pairs,'shell_pairs':shell_pairs,'competition_responsibilities':competition,'assignments':[{**rec,'event_id':eid} for eid,rec in sorted(assignments.items())],'addition_pairs':addition_pairs,'deterministic_shell_controls':controls,'family_model_audit':family_model_audit,'canonical_frozen_membership_equivalence':True,'canonical_assigned_nonseed_events':int(canonical_diag['assigned_nonseed_events']),'control_hash_rule':'SHA256(canonical_event_id + canonical_family_id), ascending; up to additions per family/year'}
    return expanded,audit


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--p1-source',required=True,type=Path); p.add_argument('--p1-transfer-source',required=True,type=Path); p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path); p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path); p.add_argument('--output',required=True,type=Path); args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    require(sha256_file(args.p1_source)==P1_SOURCE_SHA256,'frozen P1 source changed')
    p1=load_module(args.p1_source,'p1_external_frozen'); transfer=load_module(args.p1_transfer_source,'p1_external_transfer'); transfer.YEARS=YEARS
    require(transport.YEARS==(2018,2019) and transport.BLIND_LOW==20.0 and transport.BLIND_HIGH==55.0 and transport.MAX_EVENTS_PER_BIN==10_000,'MAARSY transport constants changed')
    zenodo=transport.verify_zenodo_metadata(); scan,transport_audit=transport.stream_geometry(args.output)
    require(transport_audit['target_interval_radiant_speed_read'] is False and transport_audit['orbital_dataset_opened'] is False and transport_audit['labels_used'] is False and transport_audit['target_information_access'] is False,'geometry firewall failed')
    families,order,v8_audit,base=reconstruct_promoted_v8(scan,args)
    integrity={'complete_2018_2019_months':all(transport_audit['selected_months'][str(y)]==list(range(1,13)) for y in YEARS),'target_excluded_before_geometry_velocity':transport_audit['target_interval_radiant_speed_read'] is False,'identity_only_density_cap':all(all(int(v)<=10_000 for v in transport_audit['selected_by_bin_after_cap'][str(y)].values()) for y in YEARS),'no_orbit_access':transport_audit['orbital_dataset_opened'] is False,'no_labels':transport_audit['labels_used'] is False,'no_target_information':transport_audit['target_information_access'] is False,'promoted_v8_order_complete':len(order)==len(families) and [f['family_id'] for f in families]==order,'at_least_100_recurrent_seed_families':len(families)>=MIN_RECURRENT_FAMILIES}
    if not all(v for k,v in integrity.items() if k!='at_least_100_recurrent_seed_families'):
        verdict='FAIL_P1_MAARSY_2018_2019_EXTERNAL_INTEGRITY'; expanded=[]; membership_audit={}
    elif not integrity['at_least_100_recurrent_seed_families']:
        verdict='INCONCLUSIVE_P1_MAARSY_2018_2019_EXTERNAL_POWER'; expanded=[]; membership_audit={}
    else:
        expanded,membership_audit=exact_membership_with_audit(p1,transfer,families,scan,base); verdict='PASS_P1_MAARSY_2018_2019_GEOMETRY_MEMBERSHIP_FREEZE'
    payload={'schema':'orbittrace-p1-maarsy-2018-2019-preorbit-freeze-v1','verdict':verdict,'years':list(YEARS),'blind_exclusion':[20.0,55.0],'zenodo_metadata':zenodo,'transport_audit':transport_audit,'v8_seed_family_count':len(families),'v8_multiplicity_order':order,'v8_seed_families':families,'v8_audit':v8_audit,'p1_expanded_families':expanded,'p1_membership_audit':membership_audit,'integrity_and_geometry_power_gates':integrity,'orbit_access':False,'label_access':False,'target_information_access':False,'parameter_search':False,'new_members_can_seed_growth':False}
    digest=canonical_sha(payload); payload['preorbit_canonical_sha256']=digest
    out=args.output/'p1_maarsy_2018_2019_preorbit_freeze.json'; out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); (args.output/'p1_maarsy_2018_2019_preorbit_freeze.sha256').write_text(digest+'\n')
    print(json.dumps({'verdict':verdict,'v8_seed_families':len(families),'p1_additions':len(membership_audit.get('addition_pairs',[])),'controls':len(membership_audit.get('deterministic_shell_controls',[])),'preorbit_sha256':digest},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
