#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
RADIUS=1.0
EXPECTED=(226,1075,3203,4504)
EXPECTED_ACTIVE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
EXPECTED_P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
EXPECTED_P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
EXPECTED_P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
PANELS=('A10','B10','C20','D20')
EXPECTED_PANEL_META={
 'A10':(0.10,'URC-GENERATOR-STRESS-A'),
 'B10':(0.10,'URC-GENERATOR-STRESS-B'),
 'C20':(0.20,'URC-GENERATOR-STRESS-C'),
 'D20':(0.20,'URC-GENERATOR-STRESS-D'),
}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def circular_diff(a:float,b:float)->float: return abs((float(a)-float(b)+180.0)%360.0-180.0)
def pair_distance(a:dict[str,Any],b:dict[str,Any],support:Any,base:Any)->float:
    ds=[]
    for year in YEARS:
        ca=a.get('centroids',{}).get(str(year)); cb=b.get('centroids',{}).get(str(year))
        if ca is None or cb is None: return math.inf
        ds.append(float(support.centroid_distance(ca,cb,base)))
    return max(ds)

def source_bins(families:list[dict[str,Any]])->dict[int,list[dict[str,Any]]]:
    bins:dict[int,list[dict[str,Any]]]=defaultdict(list)
    for f in families:
        c=f.get('centroids',{}).get('2022'); req(c is not None,f"missing 2022 centroid {f.get('family_id')}")
        bins[int(math.floor(float(c['sol'])))%360].append(f)
    return dict(bins)

def nearest_distance(f:dict[str,Any],bins:dict[int,list[dict[str,Any]]],support:Any,base:Any)->float:
    c=f['centroids']['2022']; center=int(math.floor(float(c['sol'])))%360; best=math.inf
    for off in range(-7,8):
        for g in bins.get((center+off)%360,[]):
            c2=g['centroids']['2022']
            if circular_diff(c['sol'],c2['sol'])>7.0: continue
            if abs(float(c['ecl_lat'])-float(c2['ecl_lat']))>4.0: continue
            if abs(float(c['vg'])-float(c2['vg']))>4.0: continue
            d=pair_distance(f,g,support,base)
            if d<best: best=d
    return float(best)

def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    vals=np.asarray([float(r['target']) for r in rows],dtype=float)
    return {
      'families':len(rows),
      'positive_families':int(sum(bool(r['positive']) for r in rows)),
      'target_mean':float(np.mean(vals)) if len(vals) else 0.0,
      'target_q90':float(np.quantile(vals,0.90)) if len(vals) else 0.0,
      'target_max':float(np.max(vals)) if len(vals) else 0.0,
      'target_gt_0_5_families':int(sum(float(r['target'])>0.5 for r in rows)),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--active-ranker-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--p19-result-json',type=Path,required=True)
    p.add_argument('--p19-prelabel-json',type=Path,required=True)
    p.add_argument('--p20-result-json',type=Path,required=True)
    p.add_argument('--p20-prelabel-json',type=Path,required=True)
    p.add_argument('--panel-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha(a.active_ranker_source)==EXPECTED_ACTIVE_SHA,'#839 source changed')
    req(sha(a.p19_result_json)==EXPECTED_P19_RESULT_SHA,'P19 result changed'); req(sha(a.p19_prelabel_json)==EXPECTED_P19_PRELABEL_SHA,'P19 prelabel changed')
    req(sha(a.p20_result_json)==EXPECTED_P20_RESULT_SHA,'P20 result changed'); req(sha(a.p20_prelabel_json)==EXPECTED_P20_PRELABEL_SHA,'P20 prelabel changed')
    ranker=load_module(a.active_ranker_source,'frozen_839_stability_diag')
    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    original={'hard':p19['hard_families'],'p19':p19['soft_families'],'p20':p20['soft_families']}
    req((len(original['hard']),len(original['p19']),len(original['p20']),sum(map(len,original.values())))==EXPECTED,'original universe changed')

    panels={}
    for panel in PANELS:
        path=a.panel_root/panel/'panel_prelabel_payload.json.gz'; req(path.is_file(),f'missing panel {panel}')
        with gzip.open(path,'rt') as fh: payload=json.load(fh)
        frac,salt=EXPECTED_PANEL_META[panel]; req(payload['panel']==panel and abs(float(payload['fraction'])-frac)<1e-12 and payload['salt']==salt,f'{panel} metadata changed')
        panels[panel]={'hard':payload['hard_families'],'p19':payload['p19_soft_families'],'p20':payload['p20_soft_families']}

    ranker.v1.mult.YEARS=YEARS; ranker.v1.mult.MONTH_KEYS=MONTH_KEYS; ranker.v1.mult.TOP_K=100
    runtime=ranker.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-thinning-family-stability-diagnostic-v1'; support.RANKING_VARIANTS=('persistence',)
    req(float(support.BLIND_LOW)==BLIND[0] and float(support.BLIND_HIGH)==BLIND[1],'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a)

    # Freeze all label-free stability values before catalogue labels are parsed.
    panel_bins={panel:{src:source_bins(panels[panel][src]) for src in original} for panel in PANELS}
    stability_rows=[]
    for src,fams in original.items():
        for f in fams:
            per={}; nearest={}
            for panel in PANELS:
                d=nearest_distance(f,panel_bins[panel][src],support,base); nearest[panel]=d if math.isfinite(d) else None; per[panel]=bool(d<=RADIUS)
            stability_rows.append({'family_id':str(f['family_id']),'source':src,'stability':int(sum(per.values())),'panel_persistence':per,'nearest_distance':nearest})
    stability_sha=hashlib.sha256(json.dumps(stability_rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

    # Truth enters only after the complete stability table is fixed.
    scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS),'GMN years changed'); req([x['key'] for x in sources]==list(MONTH_KEYS),'GMN months changed')
    eligible=ranker.v1.eligible_labels(labels); fam_by_id={str(f['family_id']):f for fams in original.values() for f in fams}
    rows=[]
    for s in stability_rows:
        t=ranker.v1.family_truth(fam_by_id[s['family_id']],labels,eligible)
        rows.append({**s,'positive':bool(t['positive']),'target':float(t['f1']) if t['positive'] else 0.0})

    source_bins_out={}
    for src in original:
        src_rows=[r for r in rows if r['source']==src]
        source_bins_out[src]={str(k):summarize([r for r in src_rows if r['stability']==k]) for k in range(5)}
    p20_hi=[r for r in rows if r['source']=='p20' and float(r['target'])>0.5]
    p20_hi_hist={str(k):int(sum(r['stability']==k for r in p20_hi)) for k in range(5)}
    overall_hist={src:{str(k):int(sum(r['source']==src and r['stability']==k for r in rows)) for k in range(5)} for src in original}
    result={
      'stage':'GMN_TARGET_EXCLUDED_THINNING_FAMILY_STABILITY_DIAGNOSTIC_V1',
      'agreement_radius':RADIUS,
      'agreement_semantics':'exact #843 maximum annual inherited centroid distance; same generator source',
      'panels':{p:{'fraction':EXPECTED_PANEL_META[p][0],'salt':EXPECTED_PANEL_META[p][1],'family_counts':{s:len(panels[p][s]) for s in original}} for p in PANELS},
      'original_counts':{s:len(original[s]) for s in original},
      'stability_table_sha256':stability_sha,
      'stability_histogram':overall_hist,
      'source_by_exact_stability':source_bins_out,
      'p20_target_gt_0_5_family_count':len(p20_hi),
      'p20_target_gt_0_5_stability_histogram':p20_hi_hist,
      'eligible_recurrent_labels':len(eligible),
      'diagnostic_only':True,
      'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':list(BLIND),
    }
    (a.output/'GMN_THINNING_FAMILY_STABILITY_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
