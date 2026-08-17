#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree

BLIND=(20.0,55.0)
H_SOL=2.0*math.sin(math.radians(5.0)/2.0)
H_RAD=2.0*math.sin(math.radians(4.0)/2.0)
H_LOGV=math.log(1.1)
RADIUS=1.0
MIN_SUPPORT_INCLUDING_SELF=4
EXPECTED_COUNTS={2013:11,2014:9}

def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,obj:Any)->str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); p.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def embedding(rows:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(r['sol']) for r in rows])); lon=np.radians(np.asarray([float(r['sun_lon']) for r in rows])); lat=np.radians(np.asarray([float(r['ecl_lat']) for r in rows])); vg=np.asarray([float(r['vg']) for r in rows])
    req(np.all(np.isfinite(vg)) and np.all(vg>0),'bad speed'); c=np.cos(lat)
    z=np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,c*np.cos(lon)/H_RAD,c*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV])
    req(np.all(np.isfinite(z)),'bad embedding'); return z
def physcore(rows:list[dict[str,Any]])->set[int]:
    z=embedding(rows); neigh=cKDTree(z).query_ball_point(z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)
    adj=[set(int(j) for j in rr if int(j)!=i) for i,rr in enumerate(neigh)]
    active=set(range(len(rows)))
    while True:
        remove=sorted(i for i in active if sum(j in active for j in adj[i]) < MIN_SUPPORT_INCLUDING_SELF-1)
        if not remove: break
        active.difference_update(remove)
    return active

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--year',type=int,choices=(2013,2014),required=True); ap.add_argument('--rows',type=Path,required=True); ap.add_argument('--hdbscan-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rows=json.loads(a.rows.read_text()); req(isinstance(rows,list) and rows,'empty rows'); req(all(not(BLIND[0]<=float(r['sol'])<=BLIND[1]) for r in rows),'protected row present'); req(all('shower' not in r and 'truth' not in r for r in rows),'truth field present')
    by={str(r['id']):r for r in rows}; req(len(by)==len(rows),'duplicate row IDs')
    hp=a.hdbscan_dir/'comparator_primary_output.json'; hm=a.hdbscan_dir/'comparator_source_manifest.json'; h=json.loads(hp.read_text()); fams=h['families']; req(int(h['retained_family_count'])==EXPECTED_COUNTS[a.year]==len(fams),'HDBSCAN family count changed')
    out=[]; audits=[]
    for rank,f in enumerate(fams,1):
        parent_ids=[str(x) for x in f['member_ids']]; req(len(parent_ids)==len(set(parent_ids)) and set(parent_ids)<=set(by),'bad parent membership')
        pr=[by[x] for x in parent_ids]; active=physcore(pr); refined_ids=sorted(parent_ids[i] for i in active)
        fallback=len(refined_ids)<MIN_SUPPORT_INCLUDING_SELF
        ids=sorted(parent_ids) if fallback else refined_ids
        req(len(ids)>=4 and set(ids)<=set(parent_ids),'invalid refined membership')
        out.append({'family_id':f'PCH{a.year}_{rank:03d}','rank':rank,'parent_family_id':str(f['family_id']),'event_ids':ids,'member_count':len(ids),'parent_member_count':len(parent_ids),'fallback_to_parent':fallback})
        audits.append({'parent_family_id':str(f['family_id']),'parent_member_count':len(parent_ids),'refined_member_count':len(ids),'retained_fraction':len(ids)/len(parent_ids),'fallback_to_parent':fallback})
    req(any(x['refined_member_count']<x['parent_member_count'] for x in audits),'no strict refinement')
    payload={'schema':'ORBITTRACE_PHYSCORE_HDBSCAN_V1_PRETRUTH','method':'PhysCore-HDBSCAN v1','year':a.year,'family_count':len(out),'families':out,'audit':audits,'configuration':{'h_sol':H_SOL,'h_rad':H_RAD,'h_logv':H_LOGV,'radius':RADIUS,'min_support_including_self':MIN_SUPPORT_INCLUDING_SELF,'peeling':'maximal_3_core','split_components':False,'fallback':'parent_if_core_lt_4'},'row_json_sha256':sha(a.rows),'hdbscan_primary_output_sha256':sha(hp),'hdbscan_source_manifest_sha256':sha(hm),'truth_accessed':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    outsha=dump(a.output/f'physcore_{a.year}.json',payload)
    dump(a.output/f'physcore_{a.year}_manifest.json',{'year':a.year,'candidate_output_sha256':outsha,'source_file':'orbittrace_physcore_hdbscan_v1/run_pretruth.py','truth_accessed':False,'target_information_access':False})
    print(json.dumps({'year':a.year,'families':len(out),'strict_refinements':sum(x['refined_member_count']<x['parent_member_count'] for x in audits),'mean_retained_fraction':float(np.mean([x['retained_fraction'] for x in audits])),'candidate_sha256':outsha},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
