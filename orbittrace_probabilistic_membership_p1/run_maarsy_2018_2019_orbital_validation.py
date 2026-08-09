#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import fisher_exact

from orbittrace_probabilistic_membership_p1 import maarsy_2018_2019_transport as transport

YEARS=transport.YEARS
DSH_THRESHOLD=0.05
MIN_YEAR_COMPONENT=4
MIN_FAMILY_PRECISION=0.50
MIN_Q_SEED=30
MIN_VALID_ADDITIONS=200
MIN_ADDITION_FAMILIES=30
MIN_VALID_CONTROLS=200
MIN_ADDITION_PRECISION=0.60
MIN_CONTROL_ADVANTAGE=0.15
MAX_FISHER_P=0.01
MIN_COHERENT_SUPPORT_RATIO=1.20


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot load {path}')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class UnionFind:
    def __init__(self,n:int): self.parent=list(range(n)); self.size=[1]*n
    def find(self,x:int)->int:
        while self.parent[x]!=x: self.parent[x]=self.parent[self.parent[x]]; x=self.parent[x]
        return x
    def union(self,a:int,b:int)->None:
        a=self.find(a); b=self.find(b)
        if a==b:return
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a; self.size[a]+=self.size[b]


def dsh_values(ids_a:list[str],ids_b:list[str],orbits:dict[str,dict[str,float]],dsh:Any)->np.ndarray:
    if not ids_a or not ids_b: return np.empty((len(ids_a),len(ids_b)),dtype=np.float64)
    a=[orbits[e] for e in ids_a]; b=[orbits[e] for e in ids_b]
    q=np.asarray([x['q'] for x in a]+[x['q'] for x in b]); ecc=np.asarray([x['e'] for x in a]+[x['e'] for x in b]); inc=np.asarray([x['i'] for x in a]+[x['i'] for x in b]); arg=np.asarray([x['arg'] for x in a]+[x['arg'] for x in b]); node=np.asarray([x['node'] for x in a]+[x['node'] for x in b])
    matrix=dsh.pairwise_dsh(q,ecc,inc,arg,node)
    return np.asarray(matrix[:len(a),len(a):],dtype=np.float64)


def corroborate_family(event_ids:list[str],orbits:dict[str,dict[str,float]],dsh:Any)->dict[str,Any]:
    ids=list(map(str,event_ids)); valid=[eid for eid in ids if eid in orbits]
    best=[]; best_counts={}
    if len(valid)>=2:
        vals=[orbits[e] for e in valid]; matrix=dsh.pairwise_dsh([x['q'] for x in vals],[x['e'] for x in vals],[x['i'] for x in vals],[x['arg'] for x in vals],[x['node'] for x in vals])
        uf=UnionFind(len(valid)); ii,jj=np.where(np.triu(np.asarray(matrix)<DSH_THRESHOLD,k=1))
        for a,b in zip(ii.tolist(),jj.tolist()): uf.union(int(a),int(b))
        groups:dict[int,list[str]]={}
        for i,eid in enumerate(valid): groups.setdefault(uf.find(i),[]).append(eid)
        candidates=[]
        for comp in groups.values():
            counts=Counter(transport.parse_event_id(eid)[0] for eid in comp)
            if all(counts.get(y,0)>=MIN_YEAR_COMPONENT for y in YEARS): candidates.append((len(comp)/len(ids),len(comp),sorted(comp),dict(counts)))
        if candidates: _precision,_size,best,best_counts=max(candidates,key=lambda x:(x[0],x[1],x[2]))
    precision=len(best)/len(ids) if ids else 0.0; ok=bool(best and precision>=MIN_FAMILY_PRECISION and all(best_counts.get(y,0)>=MIN_YEAR_COMPONENT for y in YEARS))
    return {'family_event_count':len(ids),'valid_orbit_count':len(valid),'largest_cross_year_dsh_component':len(best),'component_event_ids':best,'component_year_counts':{str(y):int(best_counts.get(y,0)) for y in YEARS},'orbital_corroboration_precision':precision,'orbitally_corroborated':ok}


def consistency(pair:dict[str,Any],seed_by_family:dict[str,list[str]],orbits:dict[str,dict[str,float]],dsh:Any)->tuple[bool|None,dict[str,Any]]:
    eid=str(pair['event_id']); fid=str(pair['family_id']); year=int(pair['year']); opposite=YEARS[1] if year==YEARS[0] else YEARS[0]
    opposite_seeds=[sid for sid in seed_by_family[fid] if transport.parse_event_id(sid)[0]==opposite and sid in orbits]
    if eid not in orbits or not opposite_seeds: return None,{'event_id':eid,'family_id':fid,'year':year,'opposite_year':opposite,'valid_pair':False,'valid_opposite_seed_orbits':len(opposite_seeds),'min_dsh':None,'consistent':None}
    matrix=dsh_values([eid],opposite_seeds,orbits,dsh); value=float(np.min(matrix)); good=value<DSH_THRESHOLD
    return good,{'event_id':eid,'family_id':fid,'year':year,'opposite_year':opposite,'valid_pair':True,'valid_opposite_seed_orbits':len(opposite_seeds),'min_dsh':value,'consistent':good}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--preorbit',required=True,type=Path); p.add_argument('--preorbit-sha',required=True,type=Path); p.add_argument('--dsh-comparator',required=True,type=Path); p.add_argument('--output',required=True,type=Path); args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    raw=json.loads(args.preorbit.read_text()); stored=args.preorbit_sha.read_text().strip(); frozen=str(raw.pop('preorbit_canonical_sha256')); require(stored==frozen==canonical_sha(raw),'preorbit freeze changed'); raw['preorbit_canonical_sha256']=frozen
    require(raw['schema']=='orbittrace-p1-maarsy-2018-2019-preorbit-freeze-v1' and raw['verdict']=='PASS_P1_MAARSY_2018_2019_GEOMETRY_MEMBERSHIP_FREEZE','preorbit geometry/membership did not pass')
    require(raw['years']==list(YEARS) and raw['blind_exclusion']==[20.0,55.0],'preorbit identity changed'); require(raw['orbit_access'] is False and raw['label_access'] is False and raw['target_information_access'] is False,'preorbit firewall changed')
    require(all(raw['integrity_and_geometry_power_gates'].values()),'preorbit integrity/power gate changed')
    dsh=load_module(args.dsh_comparator,'p1_maarsy_dsh'); require(abs(float(dsh.RUD2014_DSH_THRESHOLD)-DSH_THRESHOLD)<1e-15,'D_SH threshold changed')
    seed_families=raw['v8_seed_families']; expanded=raw['p1_expanded_families']; order=list(map(str,raw['v8_multiplicity_order'])); require([str(f['family_id']) for f in seed_families]==order and [str(f['family_id']) for f in expanded]==order,'ranking/family order changed')
    seed_by_family={str(f['family_id']):list(map(str,f['event_ids'])) for f in seed_families}; expanded_by_family={str(f['family_id']):list(map(str,f['event_ids'])) for f in expanded}
    audit=raw['p1_membership_audit']; additions=list(audit['addition_pairs']); controls=list(audit['deterministic_shell_controls'])
    needed=set().union(*(set(v) for v in seed_by_family.values()),*(set(v) for v in expanded_by_family.values()),{str(p['event_id']) for p in controls})
    # FIRST orbit access: exact IDs were already frozen above.
    orbits,orbit_audit=transport.read_needed_orbits(needed,args.output)
    seed_corr={fid:corroborate_family(seed_by_family[fid],orbits,dsh) for fid in order}; p1_corr={fid:corroborate_family(expanded_by_family[fid],orbits,dsh) for fid in order}
    q_seed=sum(row['orbitally_corroborated'] for row in seed_corr.values()); q_p1=sum(row['orbitally_corroborated'] for row in p1_corr.values())
    coherent_seed=sum(int(row['largest_cross_year_dsh_component']) for row in seed_corr.values() if row['orbitally_corroborated']); coherent_p1=sum(int(row['largest_cross_year_dsh_component']) for row in p1_corr.values() if row['orbitally_corroborated'])
    addition_rows=[]; add_good=0; add_bad=0; add_families=set()
    for pair in additions:
        value,row=consistency(pair,seed_by_family,orbits,dsh); addition_rows.append(row)
        if value is None: continue
        add_families.add(str(pair['family_id'])); add_good+=int(value); add_bad+=int(not value)
    control_rows=[]; ctl_good=0; ctl_bad=0
    for pair in controls:
        value,row=consistency(pair,seed_by_family,orbits,dsh); control_rows.append(row)
        if value is None: continue
        ctl_good+=int(value); ctl_bad+=int(not value)
    valid_add=add_good+add_bad; valid_ctl=ctl_good+ctl_bad; precision_a=add_good/valid_add if valid_add else 0.0; precision_c=ctl_good/valid_ctl if valid_ctl else 0.0
    fisher_p=float(fisher_exact([[add_good,add_bad],[ctl_good,ctl_bad]],alternative='greater').pvalue) if valid_add and valid_ctl else 1.0
    order_sha=canonical_sha(order); integrity={'immutable_preorbit_payload':True,'only_frozen_ids_read_from_orbit_archive':orbit_audit['needed_family_events']==len(needed),'all_needed_archive_members_found':orbit_audit['needed_archive_members']==orbit_audit['seen_needed_archive_members'],'native_kepler_semantics':orbit_audit['native_kepler_mapping']==['a_m','e','i_deg','omega_deg','Omega_deg','nu_deg'] and orbit_audit['au_m']==149_597_870_700.0,'kepler_std_unopened':orbit_audit['kepler_std_opened'] is False,'geometry_unopened_in_orbit_stage':orbit_audit['geometry_fields_opened_this_stage'] is False,'D_SH_threshold_005':abs(float(dsh.RUD2014_DSH_THRESHOLD)-0.05)<1e-15,'multiplicity_ranking_unchanged':canonical_sha(list(map(str,raw['v8_multiplicity_order'])))==order_sha,'membership_nonrecursive':raw['new_members_can_seed_growth'] is False,'no_parameter_search':raw['parameter_search'] is False,'no_target_information':orbit_audit['target_information_access'] is False}
    power={'Q_seed_at_least_30':q_seed>=MIN_Q_SEED,'at_least_200_valid_orbit_additions':valid_add>=MIN_VALID_ADDITIONS,'additions_span_at_least_30_families':len(add_families)>=MIN_ADDITION_FAMILIES,'at_least_200_valid_shell_controls':valid_ctl>=MIN_VALID_CONTROLS}
    science={'Q_P1_no_loss':q_p1>=q_seed,'addition_orbital_precision_at_least_060':precision_a>=MIN_ADDITION_PRECISION,'addition_precision_advantage_at_least_015':precision_a>=precision_c+MIN_CONTROL_ADVANTAGE,'fisher_one_sided_p_at_most_001':fisher_p<=MAX_FISHER_P,'coherent_support_growth_at_least_20pct':coherent_p1>=MIN_COHERENT_SUPPORT_RATIO*coherent_seed,'multiplicity_ranking_byte_semantics_unchanged':canonical_sha(list(map(str,raw['v8_multiplicity_order'])))==order_sha,'membership_nonrecursive':raw['new_members_can_seed_growth'] is False}
    if not all(integrity.values()): verdict='FAIL_P1_MAARSY_2018_2019_EXTERNAL_INTEGRITY'
    elif not all(power.values()): verdict='INCONCLUSIVE_P1_MAARSY_2018_2019_EXTERNAL_POWER'
    elif all(science.values()): verdict='PASS_P1_MAARSY_2018_2019_EXTERNAL_VALIDATION'
    else: verdict='FAIL_P1_MAARSY_2018_2019_EXTERNAL_VALIDATION'
    result={'schema':'orbittrace-p1-maarsy-2018-2019-external-validation-v1','verdict':verdict,'configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'D_SH_threshold':DSH_THRESHOLD,'minimum_year_component':MIN_YEAR_COMPONENT,'family_orbital_precision_floor':MIN_FAMILY_PRECISION,'Q_seed_power_floor':MIN_Q_SEED,'valid_addition_power_floor':MIN_VALID_ADDITIONS,'addition_family_power_floor':MIN_ADDITION_FAMILIES,'valid_control_power_floor':MIN_VALID_CONTROLS,'addition_precision_floor':MIN_ADDITION_PRECISION,'control_advantage_floor':MIN_CONTROL_ADVANTAGE,'fisher_p_ceiling':MAX_FISHER_P,'coherent_support_ratio_floor':MIN_COHERENT_SUPPORT_RATIO,'parameter_search':False,'alternate_control_resampling':False,'alternate_year_or_subset_search':False},'preorbit_canonical_sha256':frozen,'Q_seed':q_seed,'Q_P1':q_p1,'coherent_seed_members':coherent_seed,'coherent_P1_members':coherent_p1,'valid_addition_pairs':valid_add,'addition_families':len(add_families),'addition_consistent':add_good,'addition_inconsistent':add_bad,'precision_A':precision_a,'valid_control_pairs':valid_ctl,'control_consistent':ctl_good,'control_inconsistent':ctl_bad,'precision_C':precision_c,'fisher_one_sided_p':fisher_p,'integrity_gates':integrity,'power_gates':power,'scientific_gates':science,'orbit_read_audit':orbit_audit,'target_information_access':False}
    (args.output/'p1_maarsy_2018_2019_external_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); (args.output/'p1_maarsy_2018_2019_family_corroboration.json').write_text(json.dumps({'seed':seed_corr,'p1':p1_corr},sort_keys=True)+'\n'); (args.output/'p1_maarsy_2018_2019_pair_corroboration.json').write_text(json.dumps({'additions':addition_rows,'controls':control_rows},sort_keys=True)+'\n')
    print(json.dumps({'verdict':verdict,'Q_seed':q_seed,'Q_P1':q_p1,'valid_additions':valid_add,'addition_families':len(add_families),'precision_A':precision_a,'valid_controls':valid_ctl,'precision_C':precision_c,'fisher_p':fisher_p,'coherent_seed_members':coherent_seed,'coherent_P1_members':coherent_p1},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
