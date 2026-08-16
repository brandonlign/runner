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
from gmn_python_api import data_directory as dd

YEARS=(2022,2023)
MONTHS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
BUCKETS=(0,1,2,3)
STRUCTURAL_SHA="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
MANIFEST_SHA="3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8"
INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"
MIN_SUPPORT=4


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f"cannot import {path}"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def clean(x:str)->str:return " ".join(x.replace("#","").strip().split())
def fnum(x:str)->float:
    try:v=float(x)
    except Exception:v=float('nan')
    return v

def geometry_columns(text:str)->tuple[dict[str,int],list[str]]:
    lines=text.splitlines()
    top=next((ln for ln in lines if ln.lstrip().startswith('#') and 'Unique trajectory' in ln and 'Sol lon' in ln and 'LAMgeo' in ln and 'BETgeo' in ln and 'Vgeo' in ln),None)
    bottom=next((ln for ln in lines if ln.lstrip().startswith('#') and 'identifier' in ln and 'km/s' in ln),None)
    req(top is not None and bottom is not None,'GMN two-row schema header not found')
    a=[clean(x) for x in top.split(';')]; b=[clean(x) for x in bottom.split(';')]; req(len(a)==len(b) and len(a)>70,'unexpected header width')
    def one(t:str,u:str)->int:
        hits=[i for i,(x,y) in enumerate(zip(a,b)) if x==t and y==u]; req(len(hits)==1,f'header field {(t,u)} not unique: {hits}'); return hits[0]
    return {'id':one('Unique trajectory','identifier'),'sol':one('Sol lon','deg'),'lon':one('LAMgeo','deg'),'lat':one('BETgeo','deg'),'vg':one('Vgeo','km/s')},lines

def load_sparse_geometry(manifest:dict[str,Any])->list[dict[str,Any]]:
    union=set(map(str,manifest['audited_union_ids'])); allowed={str(k):str(v) for k,v in manifest['audited_union_authoritative_month'].items()}; req(set(allowed)==union,'manifest month map')
    seen=set(); events=[]
    for month in MONTHS:
        print(f'[orbital-prelabel] geometry fetch {month}',flush=True)
        text=dd.get_monthly_file_content_by_date(month); req(hashlib.sha256(text.encode()).hexdigest()==manifest['source_sha256'][month],f'monthly source changed {month}')
        c,lines=geometry_columns(text); mx=max(c.values())
        for line in lines:
            s=line.strip()
            if not s or s.startswith('#'):continue
            cells=[x.strip() for x in line.split(';')]; req(c['id']<len(cells),f'short ID row {month}'); eid=cells[c['id']]
            # Crucial firewall: no scientific field is parsed for any row outside the immutable sparse manifest.
            if allowed.get(eid)!=month:continue
            req(mx<len(cells),f'short manifest row {month}: {eid}')
            sol,lon,lat,vg=(fnum(cells[c[k]]) for k in ('sol','lon','lat','vg'))
            req(all(math.isfinite(x) for x in (sol,lon,lat,vg)),f'nonfinite manifest geometry {eid}')
            req(0.0<=sol<=360.0 and 0.0<=lon<=360.0 and -90.0<=lat<=90.0 and 5.0<=vg<=75.0,f'invalid manifest geometry {eid}')
            req(not(BLIND[0]<=sol<=BLIND[1]),f'protected event entered orbital prelabel {eid}'); req(eid not in seen,f'duplicate manifest event {eid}')
            seen.add(eid); events.append({'id':eid,'year':int(eid[:4]),'sol':sol%360.0,'lon':lon,'lat':lat,'vg':vg})
    req(seen==union and len(events)==23080,f'sparse geometry join mismatch {len(events)} of {len(union)}'); return events

def dsh2(a:dict[str,float],b:dict[str,float])->float:
    e1,q1=float(a['e']),float(a['q_au']); e2,q2=float(b['e']),float(b['q_au'])
    i1,w1,o1=map(math.radians,(float(a['i_deg']),float(a['peri_deg']),float(a['node_deg'])))
    i2,w2,o2=map(math.radians,(float(b['i_deg']),float(b['peri_deg']),float(b['node_deg'])))
    ci=math.cos(i1)*math.cos(i2)+math.sin(i1)*math.sin(i2)*math.cos(o1-o2); I=math.acos(max(-1.0,min(1.0,ci)))
    dO=o2-o1; sgn=1.0 if abs(dO)<=math.pi else -1.0; den=math.cos(I/2.0); req(abs(den)>1e-14,'degenerate antiparallel orbital planes')
    x=math.cos((i2+i1)/2.0)*math.sin(dO/2.0)/den; x=max(-1.0,min(1.0,x)); Pi=w2-w1+sgn*2.0*math.asin(x)
    value=(q1-q2)**2+(e1-e2)**2+(2.0*math.sin(I/2.0))**2+(((e1+e2)/2.0)*2.0*math.sin(Pi/2.0))**2
    req(math.isfinite(value) and value>=-1e-14,'invalid D_SH^2'); return max(0.0,float(value))
def frechet(members:list[str],mapping:dict[str,dict[str,float]])->tuple[float,str,str]:
    ids=sorted(map(str,members)); n=len(ids); req(n>=MIN_SUPPORT,'sub-support candidate'); req(all(eid in mapping and mapping[eid] is not None for eid in ids),'candidate missing orbit')
    sums=[0.0]*n; h=hashlib.sha256()
    for j in range(n):
        for k in range(j+1,n):
            d=dsh2(mapping[ids[j]],mapping[ids[k]]); sums[j]+=d; sums[k]+=d; h.update(f'{ids[j]}|{ids[k]}={float(d).hex()}\n'.encode())
    means=[x/float(n-1) for x in sums]; best=min(means); med=min(ids[j] for j,v in enumerate(means) if abs(v-best)<=1e-15); return float(best),med,h.hexdigest()
def orbital_order(rows:list[dict[str,Any]],mapping:dict[str,dict[str,float]])->list[dict[str,Any]]:
    out=[]
    for src in rows:
        ids=list(map(str,src['event_ids'])); energy,med,pairsha=frechet(ids,mapping); r=dict(src); r['family_id']=hashlib.sha256(('ORBF1|'+'|'.join(sorted(ids))).encode()).hexdigest()[:20]; r['orbital_frechet_energy']=energy; r['orbital_medoid_event_id']=med; r['pairwise_dsh2_sha256']=pairsha; out.append(r)
    out.sort(key=lambda r:(0 if bool(r['is_root']) else 1,float(r['orbital_frechet_energy']),str(r['family_hash'])))
    for rank,r in enumerate(out,1):r['rank']=rank
    req([int(r['rank']) for r in out]==list(range(1,len(out)+1)),'rank continuity'); return out

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('intrinsic-runner','structural-runner','structural-result-json','orbit-mapping','availability-result','universe-manifest','parent-runner'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.structural_result_json)==STRUCTURAL_SHA,'#1284 structural artifact changed'); req(sha(a.universe_manifest)==MANIFEST_SHA,'sparse manifest changed')
    availability=json.loads(a.availability_result.read_text()); req(availability['verdict']=='PASS_TOPOMODAL_ORBIT_AVAILABILITY_V1' and all(v['all_events_usable'] for v in availability['subset_stats'].values()),'orbit availability not activated')
    req(sha(a.orbit_mapping)==availability['orbit_mapping_sha256'],'orbit mapping hash'); mapping=json.loads(a.orbit_mapping.read_text()); req(len(mapping)==23080 and all(v is not None for v in mapping.values()),'orbit mapping incomplete')
    manifest=json.loads(a.universe_manifest.read_text()); req(manifest['schema']=='ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1' and manifest['blind_exclusion']==[20.0,55.0] and manifest['shower_label_accessed'] is False,'manifest firewall')
    intrinsic=load(a.intrinsic_runner,'orbf_intrinsic'); structural=load(a.structural_runner,'orbf_structural'); parent=load(a.parent_runner,'orbf_parent')
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,'parent constants')
    events=load_sparse_geometry(manifest); byid={str(e['id']):e for e in events}; req(len(byid)==23080,'duplicate sparse IDs')
    expected={(int(r['denominator']),int(r['bucket'])):r for r in json.loads(a.structural_result_json.read_text())['fits']}; req(set(expected)=={(d,b) for d in (128,1024) for b in BUCKETS},'structural panel set')
    subsets=[]; runtime={}
    for d in (128,1024):
        for b in BUCKETS:
            key=f'd{d}_b{b}'; wanted=set(map(str,manifest['subsets'][key])); sub=[e for e in events if str(e['id']) in wanted]; req(len(sub)==len(wanted)==int(expected[(d,b)]['events_total']),f'panel count {key}')
            sid=[str(e['id']) for e in sub]; sy=np.asarray([int(e['year']) for e in sub],dtype=np.int64); sx=parent.geo_matrix(sub); req(all(np.any(sy==y) for y in YEARS),'panel lost year')
            print(f'[orbital-prelabel] d={d} b={b} n={len(sub)} topomodal/recurrent',flush=True)
            original,ss=intrinsic.topomodal_ranked(sub); par,ps=intrinsic.recurrent_ranked(parent,sx,sy,sid); ex=expected[(d,b)]
            req(ss['candidate_rows']==ex['topomodal']['candidate_rows'] and len(original)==int(ex['topomodal']['candidate_count']),'#1284 topomodal membership mismatch')
            req(ps['candidate_rows']==ex['recurrent_eom']['candidate_rows'] and len(par)==int(ex['recurrent_eom']['candidate_count']),'recurrent comparator mismatch')
            succ=orbital_order(original,mapping); budget=len(succ)>=len(par)
            subsets.append({'denominator':d,'bucket':b,'events_total':len(sid),'events_by_year':{str(y):int(np.sum(sy==y)) for y in YEARS},'event_universe_sha256':intrinsic.universe_hash(sid),'equal_budget_k':len(par),'candidate_budget_sufficient':budget,'successor_summary':ss,'recurrent_summary':ps,'successor_candidates':succ,'recurrent_candidates':par})
            runtime[(d,b)]={'succ_sets':[frozenset(r['event_ids']) for r in succ],'par_sets':[frozenset(r['event_ids']) for r in par],'ids':frozenset(sid)}
    cross=[]; svals=[]; pvals=[]; wins=0
    for b in BUCKETS:
        c=runtime[(128,b)]; f=runtime[(1024,b)]; sm=structural.cross_scale_metrics(c['succ_sets'],f['succ_sets'],f['ids']); pm=structural.cross_scale_metrics(c['par_sets'],f['par_sets'],f['ids']); sv=float(sm['fine_to_coarse_mean_best_jaccard']); pv=float(pm['fine_to_coarse_mean_best_jaccard']); wins+=int(sv>pv); svals.extend(float(x) for x in sm['fine_to_coarse_scores']); pvals.extend(float(x) for x in pm['fine_to_coarse_scores']); cross.append({'bucket':b,'successor':sm,'recurrent_eom':pm,'strict_win':sv>pv})
    cross_summary={'successor_pooled_fine_to_coarse_mean_best_jaccard':float(np.mean(svals)),'recurrent_pooled_fine_to_coarse_mean_best_jaccard':float(np.mean(pvals)),'successor_strict_bucket_wins':wins}
    pre={'schema':'ORBITTRACE_TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL','scientific_role':'PRELABEL_TOPOMODAL_ORBITAL_FRECHET_V1','years':[2022,2023],'blind_exclusion':[20.0,55.0],'structural_result_sha256':STRUCTURAL_SHA,'orbit_mapping_sha256':availability['orbit_mapping_sha256'],'universe_manifest_sha256':MANIFEST_SHA,'intrinsic_source_blob':INTRINSIC_BLOB,'configuration':{'candidate_generator':'exact_1284_complete_topomodal_hierarchy','density':'exact_1284_radius_degree_over_subset_n','graph':'exact_1284_physical_radius_1','min_candidate_support':4,'orbital_dissimilarity':'Southworth_Hawkins_D_SH_squared_exact_appendix_formula','orbital_center':'observed_member_Frechet_medoid','orbital_energy':'minimum_mean_D_SH_squared_to_all_other_candidate_members','ranking':'roots_first_then_orbital_frechet_energy_ascending_then_family_hash','equal_budget':'recurrent_candidate_count'},'subsets':subsets,'cross_scale':{'pairs':cross,**cross_summary},'candidate_budget_shortage_any_panel':any(not bool(x['candidate_budget_sufficient']) for x in subsets),'shower_truth_used':False,'shower_truth_parsed':False,'iau_number_parsed':False,'iau_code_parsed':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    req(pre['candidate_budget_shortage_any_panel'] is False,'candidate budget shortage')
    out=a.output/'TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL.json'; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'prelabel_sha256':sha(out),'orbit_mapping_sha256':availability['orbit_mapping_sha256'],'cross_scale':cross_summary,'candidate_counts':[{"d":x['denominator'],"b":x['bucket'],"successor":len(x['successor_candidates']),"parent":len(x['recurrent_candidates'])} for x in subsets]},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
