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

YEARS=(2013,2014)
EXPECTED_FEATURE_DIM=71
PREDICTIVE_SOURCE_BLOB='25d91e92c41f83416ad87766c2d96884c30b714c'
FORBIDDEN={'label','shower','shower_id','truth','truth_id','truth_label','known_shower','native_background','sporadic','target_id','target_member'}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def load_rows(path:Path,year:int)->list[dict[str,Any]]:
    rows=json.loads(path.read_text()); req(isinstance(rows,list) and rows,f'empty rows {path}')
    seen=set(); out=[]
    for row in rows:
        keys={str(k).lower() for k in row}; req(not (keys & FORBIDDEN),f'truth-bearing field in pretruth rows: {sorted(keys & FORBIDDEN)}')
        for k in ('id','year','sol','sun_lon','ecl_lat','vg'): req(k in row,f'missing canonical field {k}')
        req(int(row['year'])==year,f'row year mismatch {row.get("id")}')
        eid=str(row['id']); req(eid and eid not in seen,f'duplicate pretruth event {eid}'); seen.add(eid)
        vals=[float(row[k]) for k in ('sol','sun_lon','ecl_lat','vg')]; req(all(math.isfinite(v) for v in vals) and vals[-1]>0,f'bad pretruth geometry {eid}')
        out.append({'id':eid,'year':year,'sol':vals[0],'sun_lon':vals[1],'ecl_lat':vals[2],'vg':vals[3]})
    return out


def route_predictive(root:Path, rows13:Path, rows14:Path, pred:Any)->dict[str,Any]:
    meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
    req(meta['truth_accessed'] is False and fp['truth_accessed'] is False and int(meta['feature_dimension'])==EXPECTED_FEATURE_DIM,'invalid immutable pretruth payload')
    fams=fp['families']; ids=list(map(str,meta['family_ids'])); req([str(f['family_id']) for f in fams]==ids,'family alignment changed')
    C=np.load(root/'centroids.npy',allow_pickle=False); req(C.shape==(len(ids),8) and np.isfinite(C).all(),'centroid matrix changed')
    rows={2013:load_rows(rows13,2013),2014:load_rows(rows14,2014)}; lookup={}
    for year in YEARS:
        for r in rows[year]: req(r['id'] not in lookup,f'duplicate event across years {r["id"]}'); lookup[r['id']]=r
    feature_rows=[]
    for i,f in enumerate(fams):
        annual=[]; all_members=list(map(str,f['event_ids']))
        for yi,year in enumerate(YEARS):
            yr=[]
            for eid in all_members:
                req(eid in lookup,f'candidate member absent from immutable label-free rows: {eid}')
                if int(lookup[eid]['year'])==year: yr.append(lookup[eid])
            center_sol=float(C[i,0 if yi==0 else 4])
            annual.append(pred.loo_year(yr,center_sol))
        pq=float(max(a['pred_q90'] for a in annual)); pm=float(max(a['pred_median'] for a in annual)); px=float(max(a['pred_max'] for a in annual)); sq=float(max(a['static_q90'] for a in annual)); gain=float(sq-pq)
        learned=float(sum(a['learned']*a['n'] for a in annual)/max(sum(a['n'] for a in annual),1))
        feature_rows.append({'family_id':ids[i],'features':{'pred_q90_max':pq,'pred_median_max':pm,'pred_max_max':px,'static_q90_max':sq,'q90_gain':gain,'learned_fraction':learned,'annual':annual}})
    order=pred.rank_predictive(feature_rows); req(len(order)==len(ids) and set(order)==set(ids),'invalid predictive route order')
    return {'candidate_count':len(ids),'family_universe_sha256':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest(),'predictive_order':order,'predictive_order_sha256':order_sha(order),'features':feature_rows,'truth_accessed':False}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True); p.add_argument('--sugar-rows-2013',type=Path,required=True); p.add_argument('--sugar-rows-2014',type=Path,required=True); p.add_argument('--hdbscan-rows-2013',type=Path,required=True); p.add_argument('--hdbscan-rows-2014',type=Path,required=True); p.add_argument('--predictive-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); pred=load_module(a.predictive_source,'v61_frozen_gmn_predictive')
    routes={'sugar':route_predictive(a.sugar_root,a.sugar_rows_2013,a.sugar_rows_2014,pred),'hdbscan':route_predictive(a.hdbscan_root,a.hdbscan_rows_2013,a.hdbscan_rows_2014,pred)}
    result={'verdict':'PASS_V61_PRETRUTH_PREDICTIVE_ORDER_FREEZE','scientific_role':'SONOTACO_PRETRUTH_IMPLEMENTATION_OF_GMN_AUTHORIZED_RULE','routes':routes,'predictive_rule':'exact GMN leave-one-out affine radiant-unit-vector plus log(vg) physical residual; lexicographic q90/median/gain','parameter_search':False,'family_deletion':False,'truth_accessed':False,'sonotaco_truth_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    path=a.output/'V61_PRETRUTH_PREDICTIVE_ORDER.json'; path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'sugar_candidates':routes['sugar']['candidate_count'],'hdbscan_candidates':routes['hdbscan']['candidate_count'],'sugar_order_sha256':routes['sugar']['predictive_order_sha256'],'hdbscan_order_sha256':routes['hdbscan']['predictive_order_sha256'],'result_sha256':sha(path)},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
