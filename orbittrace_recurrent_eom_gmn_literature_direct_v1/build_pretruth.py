#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN
import hdbscan

YEARS=(2022,2023); BLIND=(20.0,55.0)
EXPECTED_COUNTS={'2022':315024,'2023':423658}; EXPECTED_TOTAL=738682
PROTOCOL_BLOB='dd88ced3e13e371d7d1976f4cbe6c8ba67ad4964'
REC_PRE_SHA='e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1'
REC_RES_SHA='433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p:Path)->str:
    b=p.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def geo(rows:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(e['sol']) for e in rows],float)); lon=np.radians(np.asarray([float(e['lon']) for e in rows],float)); lat=np.radians(np.asarray([float(e['lat']) for e in rows],float)); vg=np.asarray([float(e['vg']) for e in rows],float); cl=np.cos(lat)
    z=np.column_stack([np.cos(sol),np.sin(sol),np.sin(lon)*cl,np.cos(lon)*cl,np.sin(lat),vg/72.0]).astype(np.float64)
    req(z.shape==(len(rows),6) and np.all(np.isfinite(z)),'invalid GEO vector'); return z

def clusters_from_labels(ids:list[str],labels:np.ndarray)->tuple[list[dict[str,Any]],int]:
    labels=np.asarray(labels,int); out=[]
    for lab in sorted(int(x) for x in set(labels.tolist()) if int(x)>=0):
        ix=np.flatnonzero(labels==lab); mids=sorted(ids[int(i)] for i in ix)
        out.append({'cluster_id':lab,'member_count':len(mids),'event_ids':mids})
    return out,int(np.sum(labels<0))

def main()->int:
    ap=argparse.ArgumentParser();
    for n in ('protocol','geometry','recurrent-prelabel','recurrent-result','output'): ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(blob(a.protocol)==PROTOCOL_BLOB,'protocol changed'); req(sha(a.recurrent_prelabel)==REC_PRE_SHA,'recurrent prelabel changed'); req(sha(a.recurrent_result)==REC_RES_SHA,'recurrent result changed')
    g=json.loads(a.geometry.read_text()); req(g['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry role'); req(g['events_total']==EXPECTED_TOTAL and g['events_by_year']==EXPECTED_COUNTS,'geometry counts'); req(g['blind_exclusion']==list(BLIND) and g['shower_truth_exported'] is False,'geometry firewall')
    events=list(g['events']); req(len(events)==EXPECTED_TOTAL,'geometry rows'); req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected row');
    rec=json.loads(a.recurrent_prelabel.read_text()); rr=json.loads(a.recurrent_result.read_text()); req(rr['verdict']=='PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT','recurrent binding not pass'); rc=list(rec['successor_candidates']); req(len(rc)==2097,'recurrent candidate count changed')
    panels={};
    for y in YEARS:
        rows=sorted([e for e in events if int(e['year'])==y],key=lambda e:str(e['id'])); req(len(rows)==EXPECTED_COUNTS[str(y)],f'year count {y}'); ids=[str(e['id']) for e in rows]; z=geo(rows); universe=hashlib.sha256('\n'.join(ids).encode()).hexdigest()
        print(f'[literature] {y} Sugar 4NN epsilon',flush=True)
        tree=cKDTree(z); d,_=tree.query(z,k=5,p=2.0,eps=0.0,workers=1); d4=np.asarray(d[:,4],float); eps=float(np.quantile(d4,0.23,method='linear')); req(np.isfinite(eps) and eps>0,'bad Sugar epsilon')
        print(f'[literature] {y} Sugar DBSCAN eps={eps}',flush=True)
        sl=DBSCAN(eps=eps,min_samples=5,metric='euclidean',algorithm='kd_tree',n_jobs=1).fit_predict(z); sc,snoise=clusters_from_labels(ids,sl)
        print(f'[literature] {y} HDBSCAN GEO100',flush=True)
        hm=hdbscan.HDBSCAN(min_cluster_size=100,min_samples=100,metric='euclidean',cluster_selection_method='eom',cluster_selection_epsilon=0.0,allow_single_cluster=False,algorithm='boruvka_kdtree',core_dist_n_jobs=1,approx_min_span_tree=True,gen_min_span_tree=False,prediction_data=False)
        hl=hm.fit_predict(z); hc,hnoise=clusters_from_labels(ids,hl)
        panels[str(y)]={'event_count':len(ids),'event_universe_sha256':universe,'sugar':{'method':'Sugar2017_DBSCAN_central_value_core','min_samples':5,'epsilon_rule':'23rd percentile exact fourth-nearest-neighbor distance','epsilon':eps,'cluster_count':len(sc),'noise_count':snoise,'clusters':sc},'hdbscan2025':{'method':'PenaAsensioFerrari2025_GEO_EOM_100','min_cluster_size':100,'min_samples':100,'cluster_count':len(hc),'noise_count':hnoise,'clusters':hc}}
        print(json.dumps({'year':y,'sugar_clusters':len(sc),'sugar_noise':snoise,'hdbscan_clusters':len(hc),'hdbscan_noise':hnoise}),flush=True)
    payload={'schema':'ORBITTRACE_RECURRENT_EOM_GMN_LITERATURE_DIRECT_V1_PRETRUTH','scientific_role':'TARGET_EXCLUDED_GMN_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH','blind_exclusion':list(BLIND),'events_total':EXPECTED_TOTAL,'events_by_year':EXPECTED_COUNTS,'recurrent_binding_run_id':31827903547,'recurrent_binding_artifact_id':9229646556,'recurrent_candidates':rc,'panels':panels,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'asfn_efn_event_level_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':'PASS_GMN_LITERATURE_DIRECT_V1_PRETRUTH','sha256':sha(a.output),'years':{y:{'sugar_clusters':panels[y]['sugar']['cluster_count'],'hdbscan_clusters':panels[y]['hdbscan2025']['cluster_count']} for y in panels}},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
