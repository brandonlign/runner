#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN
import hdbscan

YEARS=(2022,2023); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3)
EXPECTED_COUNTS={'2022':315024,'2023':423658}; EXPECTED_TOTAL=738682
INTERNAL_PRE_SHA='7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
PROTOCOL_BLOB='4cc4458394f0c7816fc99d3aa8f4479c5bc419f7'

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
    ap=argparse.ArgumentParser()
    for n in ('protocol','geometry','internal-prelabel','output'): ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(blob(a.protocol)==PROTOCOL_BLOB,'protocol changed')
    req(sha(a.internal_prelabel)==INTERNAL_PRE_SHA,'internal-mass prelabel changed')
    g=json.loads(a.geometry.read_text()); req(g['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry role')
    req(g['events_total']==EXPECTED_TOTAL and g['events_by_year']==EXPECTED_COUNTS,'geometry counts')
    req(g['blind_exclusion']==list(BLIND) and g['shower_truth_exported'] is False,'geometry firewall')
    events=list(g['events']); req(len(events)==EXPECTED_TOTAL,'geometry rows')
    req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected row in geometry')
    by_id={str(e['id']):e for e in events}; req(len(by_id)==EXPECTED_TOTAL,'duplicate geometry id')
    pre=json.loads(a.internal_prelabel.read_text())
    req(pre.get('schema')=='ORBITTRACE_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL','wrong internal schema')
    req(pre.get('shower_truth_used') is False and pre.get('target_information_access') is False and pre.get('target_region_events_accessed') is False,'internal prelabel firewall')
    subsets={(int(s['denominator']),int(s['bucket'])):s for s in pre['subsets']}
    req(set(subsets)=={(d,b) for d in DENOMS for b in BUCKETS},'panel set changed')
    out_subsets=[]; panels={}
    for d in DENOMS:
      for b in BUCKETS:
        s=subsets[(d,b)]; succ=list(s['successor_candidates'])
        req([int(x['internal_mass_rank']) for x in succ]==list(range(1,len(succ)+1)),f'rank discontinuity d{d}b{b}')
        annual_ids={str(y):[str(x) for x in s['annual_event_ids'][str(y)]] for y in YEARS}
        req(len(set(annual_ids['2022']).intersection(annual_ids['2023']))==0,f'annual overlap d{d}b{b}')
        req(len(set(annual_ids['2022']).union(annual_ids['2023']))==int(s['event_count']),f'event count d{d}b{b}')
        req(all(eid in by_id for y in YEARS for eid in annual_ids[str(y)]),f'panel id missing geometry d{d}b{b}')
        out_subsets.append({'denominator':d,'bucket':b,'event_count':int(s['event_count']),'successor_candidates':succ,'annual_event_ids':annual_ids})
        for y in YEARS:
            ids=sorted(annual_ids[str(y)]); rows=[by_id[eid] for eid in ids]
            req(all(int(e['year'])==y for e in rows),f'year mismatch d{d}b{b}y{y}')
            req(len(rows)>=5,f'panel too small d{d}b{b}y{y}')
            z=geo(rows); universe=hashlib.sha256('\n'.join(ids).encode()).hexdigest()
            tree=cKDTree(z); dist,_=tree.query(z,k=5,p=2.0,eps=0.0,workers=1); d4=np.asarray(dist[:,4],float)
            eps=float(np.quantile(d4,0.23,method='linear')); req(np.isfinite(eps) and eps>0,'bad Sugar epsilon')
            sl=DBSCAN(eps=eps,min_samples=5,metric='euclidean',algorithm='kd_tree',n_jobs=1).fit_predict(z); sc,snoise=clusters_from_labels(ids,sl)
            hm=hdbscan.HDBSCAN(min_cluster_size=100,min_samples=100,metric='euclidean',cluster_selection_method='eom',cluster_selection_epsilon=0.0,allow_single_cluster=False,algorithm='boruvka_kdtree',core_dist_n_jobs=1,approx_min_span_tree=True,gen_min_span_tree=False,prediction_data=False)
            hl=hm.fit_predict(z); hc,hnoise=clusters_from_labels(ids,hl)
            key=f'd{d}_b{b}_y{y}'
            panels[key]={'denominator':d,'bucket':b,'year':y,'event_count':len(ids),'event_universe_sha256':universe,
              'sugar2017':{'method':'Sugar2017_DBSCAN_central_value_core','min_samples':5,'epsilon_rule':'23rd percentile exact fourth-nearest-neighbor distance','epsilon':eps,'cluster_count':len(sc),'noise_count':snoise,'clusters':sc},
              'hdbscan2025':{'method':'PenaAsensioFerrari2025_GEO_EOM_100','min_cluster_size':100,'min_samples':100,'cluster_count':len(hc),'noise_count':hnoise,'clusters':hc}}
            print(json.dumps({'panel':key,'events':len(ids),'sugar_clusters':len(sc),'hdbscan_clusters':len(hc)}),flush=True)
    payload={'schema':'ORBITTRACE_INTERNAL_MASS_GMN_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH','scientific_role':'TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH','blind_exclusion':list(BLIND),'internal_prelabel_sha256':INTERNAL_PRE_SHA,'geometry_events_total':EXPECTED_TOTAL,'geometry_events_by_year':EXPECTED_COUNTS,'subsets':out_subsets,'panels':panels,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'asfn_efn_event_level_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':'PASS_INTERNAL_MASS_GMN_SPARSE_LITERATURE_PRETRUTH_V1','sha256':sha(a.output),'panel_count':len(panels)},sort_keys=True),flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
