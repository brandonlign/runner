#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
from typing import Any
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CORE_PATH=ROOT/'orbittrace_physcore_hdbscan_v1'/'run_pretruth.py'
spec=importlib.util.spec_from_file_location('frozen_physcore_hdbscan_v1_core',CORE_PATH)
if spec is None or spec.loader is None: raise RuntimeError('cannot load frozen PhysCore source')
core=importlib.util.module_from_spec(spec); sys.modules[spec.name]=core; spec.loader.exec_module(core)

BLIND=(20.0,55.0)

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,o:Any)->str:
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); p.write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--pair',choices=('hdbscan','sugar','dsh'),required=True); ap.add_argument('--year',type=int,choices=(2013,2014),required=True); ap.add_argument('--rows',type=Path,required=True); ap.add_argument('--hdbscan-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rows=json.loads(a.rows.read_text()); req(isinstance(rows,list) and rows,'empty rows'); req(all(not(BLIND[0]<=float(r['sol'])<=BLIND[1]) for r in rows),'protected row present'); req(all('shower' not in r and 'truth' not in r for r in rows),'truth-bearing field present')
    by={str(r['id']):r for r in rows}; req(len(by)==len(rows),'duplicate row IDs')
    hp=a.hdbscan_dir/'comparator_primary_output.json'; hm=a.hdbscan_dir/'comparator_source_manifest.json'; h=json.loads(hp.read_text()); fams=h['families']; req(int(h['retained_family_count'])==len(fams) and len(fams)>0,'invalid parent family count')
    out=[]; audits=[]
    for rank,f in enumerate(fams,1):
        parent_ids=[str(x) for x in f['member_ids']]; req(len(parent_ids)==len(set(parent_ids)) and set(parent_ids)<=set(by),'bad parent membership')
        pr=[by[x] for x in parent_ids]; active=core.physcore(pr); refined=sorted(parent_ids[i] for i in active); fallback=len(refined)<core.MIN_SUPPORT_INCLUDING_SELF; ids=sorted(parent_ids) if fallback else refined
        req(len(ids)>=4 and set(ids)<=set(parent_ids),'invalid refined membership')
        out.append({'family_id':f'PCH{a.year}_{rank:03d}','rank':rank,'parent_family_id':str(f['family_id']),'event_ids':ids,'member_count':len(ids),'parent_member_count':len(parent_ids),'fallback_to_parent':fallback})
        audits.append({'parent_family_id':str(f['family_id']),'parent_member_count':len(parent_ids),'refined_member_count':len(ids),'retained_fraction':len(ids)/len(parent_ids),'fallback_to_parent':fallback})
    req(any(x['refined_member_count']<x['parent_member_count'] for x in audits),'no strict refinement')
    payload={'schema':'ORBITTRACE_PHYSCORE_HDBSCAN_V1_TRANSFER_PRETRUTH','method':'PhysCore-HDBSCAN v1','pair':a.pair,'year':a.year,'family_count':len(out),'families':out,'audit':audits,'configuration':{'h_sol':core.H_SOL,'h_rad':core.H_RAD,'h_logv':core.H_LOGV,'radius':core.RADIUS,'min_support_including_self':core.MIN_SUPPORT_INCLUDING_SELF,'peeling':'maximal_3_core','split_components':False,'fallback':'parent_if_core_lt_4'},'frozen_core_source_sha256':sha(CORE_PATH),'transfer_source_sha256':sha(Path(__file__)),'row_json_sha256':sha(a.rows),'hdbscan_primary_output_sha256':sha(hp),'hdbscan_source_manifest_sha256':sha(hm),'truth_accessed':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    outsha=dump(a.output/f'physcore_{a.pair}_{a.year}.json',payload)
    dump(a.output/f'physcore_{a.pair}_{a.year}_manifest.json',{'pair':a.pair,'year':a.year,'candidate_output_sha256':outsha,'frozen_core_source_sha256':payload['frozen_core_source_sha256'],'transfer_source_sha256':payload['transfer_source_sha256'],'truth_accessed':False,'target_information_access':False})
    print(json.dumps({'pair':a.pair,'year':a.year,'families':len(out),'strict_refinements':sum(x['refined_member_count']<x['parent_member_count'] for x in audits),'mean_retained_fraction':float(np.mean([x['retained_fraction'] for x in audits])),'candidate_sha256':outsha},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
