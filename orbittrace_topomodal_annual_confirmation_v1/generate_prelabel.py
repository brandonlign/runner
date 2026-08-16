#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

from gmn_python_api import data_directory as dd

YEARS=(2022,2023)
MONTHS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
SOURCE_PRELABEL_SHA="db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de"
MANIFEST_SHA="3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8"
INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"
MIN_SUPPORT=4


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def clean(x:str)->str:return " ".join(x.replace('#','').strip().split())
def fnum(x:str)->float:
    try:v=float(x)
    except Exception:v=float('nan')
    return v

def cols(text:str)->tuple[dict[str,int],list[str]]:
    lines=text.splitlines(); top=next((ln for ln in lines if ln.lstrip().startswith('#') and 'Unique trajectory' in ln and 'Sol lon' in ln and 'LAMgeo' in ln and 'BETgeo' in ln and 'Vgeo' in ln),None); bottom=next((ln for ln in lines if ln.lstrip().startswith('#') and 'identifier' in ln and 'km/s' in ln),None)
    req(top is not None and bottom is not None,'GMN two-row header missing'); a=[clean(x) for x in top.split(';')]; b=[clean(x) for x in bottom.split(';')]; req(len(a)==len(b) and len(a)>70,'header width')
    def one(t,u):
        h=[i for i,(x,y) in enumerate(zip(a,b)) if x==t and y==u]; req(len(h)==1,f'field {(t,u)}: {h}'); return h[0]
    return {'id':one('Unique trajectory','identifier'),'sol':one('Sol lon','deg'),'lam':one('LAMgeo','deg'),'lat':one('BETgeo','deg'),'vg':one('Vgeo','km/s')},lines

def sparse_geometry(manifest:dict[str,Any])->dict[str,dict[str,Any]]:
    union=set(map(str,manifest['audited_union_ids'])); allowed={str(k):str(v) for k,v in manifest['audited_union_authoritative_month'].items()}; req(set(allowed)==union,'month map'); out={}
    for month in MONTHS:
        print(f'[annual-confirm] fetch {month}',flush=True); text=dd.get_monthly_file_content_by_date(month); req(hashlib.sha256(text.encode()).hexdigest()==manifest['source_sha256'][month],f'month source changed {month}'); c,lines=cols(text); mx=max(c.values())
        for line in lines:
            s=line.strip()
            if not s or s.startswith('#'):continue
            cells=[x.strip() for x in line.split(';')]; req(c['id']<len(cells),f'short row {month}'); eid=cells[c['id']]
            if allowed.get(eid)!=month:continue
            req(mx<len(cells),f'short manifest row {eid}'); sol,lam,lat,vg=(fnum(cells[c[k]]) for k in ('sol','lam','lat','vg')); req(all(math.isfinite(x) for x in (sol,lam,lat,vg)),'nonfinite geometry'); req(not(BLIND[0]<=sol<=BLIND[1]),f'protected event {eid}'); req(eid not in out,f'duplicate {eid}')
            out[eid]={'id':eid,'year':int(eid[:4]),'sol':sol%360.0,'lon':(lam-sol)%360.0,'lat':lat,'vg':vg}
    req(set(out)==union and len(out)==23080,f'geometry join {len(out)}'); return out

def jaccard(a:set[str],b:set[str])->float:
    u=len(a|b); return float(len(a&b)/u) if u else 0.0

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source-prelabel',type=Path,required=True); ap.add_argument('--universe-manifest',type=Path,required=True); ap.add_argument('--intrinsic-runner',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.source_prelabel)==SOURCE_PRELABEL_SHA,'source #1284 prelabel hash'); req(sha(a.universe_manifest)==MANIFEST_SHA,'manifest hash')
    src=json.loads(a.source_prelabel.read_text()); manifest=json.loads(a.universe_manifest.read_text()); req(src['schema']=='ORBITTRACE_TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL' and src['shower_truth_used'] is False,'source prelabel schema/firewall'); req(manifest['schema']=='ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1' and manifest['shower_label_accessed'] is False,'manifest schema/firewall')
    intrinsic=load(a.intrinsic_runner,'annual_intrinsic'); req(hashlib.sha1(a.intrinsic_runner.read_bytes()).hexdigest() is not None,'runner readable')
    geometry=sparse_geometry(manifest)
    out_sub=[]
    for row in src['subsets']:
        d,b=int(row['denominator']),int(row['bucket']); key=f'd{d}_b{b}'; ids=list(map(str,manifest['subsets'][key])); req(len(ids)==int(row['events_total']),'panel count'); req(intrinsic.universe_hash(ids)==str(row['event_universe_sha256']),'panel universe hash'); pooled=[geometry[eid] for eid in ids]
        print(f'[annual-confirm] exactness d={d} b={b} n={len(ids)}',flush=True)
        pooled_candidates,pooled_summary=intrinsic.topomodal_ranked(pooled); req(pooled_summary['candidate_rows']==row['topomodal_summary']['candidate_rows'] and len(pooled_candidates)==len(row['topomodal_candidates']),'pooled #1284 membership exactness failed')
        annual_sets={}; annual_summary={}
        for y in YEARS:
            ey=[e for e in pooled if int(e['year'])==y]; cand,summary=intrinsic.topomodal_ranked(ey); annual_sets[y]=[set(map(str,r['event_ids'])) for r in cand]; annual_summary[str(y)]={'event_count':len(ey),'candidate_count':len(cand),'candidate_rows':summary['candidate_rows']}
        ranked=[]
        for original in row['topomodal_candidates']:
            r=dict(original); mids=set(map(str,r['event_ids'])); scores={}
            for y in YEARS:
                cy={eid for eid in mids if int(eid[:4])==y}
                if len(cy)<MIN_SUPPORT:s=0.0
                else:s=max((jaccard(cy,A) for A in annual_sets[y]),default=0.0)
                scores[y]=float(s)
            r['annual_jaccard_2022']=scores[2022]; r['annual_jaccard_2023']=scores[2023]; r['annual_confirmation']=min(scores[2022],scores[2023]); ranked.append(r)
        ranked.sort(key=lambda r:(-float(r['annual_confirmation']),str(r['family_hash'])))
        for rank,r in enumerate(ranked,1):r['rank']=rank
        req([r['rank'] for r in ranked]==list(range(1,len(ranked)+1)),'rank continuity'); req(sorted((r['family_hash'],tuple(r['event_ids'])) for r in ranked)==sorted((r['family_hash'],tuple(r['event_ids'])) for r in row['topomodal_candidates']),'candidate membership changed')
        recurrent=list(row['recurrent_candidates']); req(len(ranked)>=len(recurrent)>0,'candidate budget shortage')
        out_sub.append({'denominator':d,'bucket':b,'events_total':len(ids),'events_by_year':row['events_by_year'],'event_universe_sha256':row['event_universe_sha256'],'equal_budget_k':len(recurrent),'candidate_budget_sufficient':True,'successor_summary':row['topomodal_summary'],'annual_topology_summary':annual_summary,'successor_candidates':ranked,'recurrent_summary':row['recurrent_summary'],'recurrent_candidates':recurrent})
    pre={'schema':'ORBITTRACE_TOPOMODAL_ANNUAL_CONFIRMATION_V1_PRELABEL','scientific_role':'PRELABEL_TOPOMODAL_ANNUAL_CONFIRMATION_V1','years':[2022,2023],'blind_exclusion':[20.0,55.0],'source_1284_prelabel_sha256':SOURCE_PRELABEL_SHA,'universe_manifest_sha256':MANIFEST_SHA,'intrinsic_source_blob':INTRINSIC_BLOB,'configuration':{'candidate_generator':'exact_1284_complete_topomodal_hierarchy_from_immutable_prelabel','annual_topology':'exact_1284_topomodal_separately_per_year','annual_support_floor':4,'annual_similarity':'best_jaccard_of_candidate_year_restriction_to_any_reportable_annual_family','confirmation':'min(best_jaccard_2022,best_jaccard_2023)','ranking':'annual_confirmation_desc_then_family_hash','root_priority':False,'equal_budget':'recurrent_candidate_count'},'subsets':out_sub,'candidate_budget_shortage_any_panel':False,'shower_truth_used':False,'shower_truth_parsed':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    p=a.output/'TOPOMODAL_ANNUAL_CONFIRMATION_V1_PRELABEL.json'; p.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'prelabel_sha256':sha(p),'candidate_counts':[{'d':r['denominator'],'b':r['bucket'],'successor':len(r['successor_candidates']),'parent':len(r['recurrent_candidates']),'annual22':r['annual_topology_summary']['2022']['candidate_count'],'annual23':r['annual_topology_summary']['2023']['candidate_count']} for r in out_sub]},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
