#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

FROZEN_BLOB='a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
CACHED_BLOB='2a599c6e8247eb819a1090591d586526eda6c0c1'
WRAPPER_BLOB='8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
SHARDS=4


def req(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(path:Path)->str:
    b=path.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def load(path:Path,name:str,expected_blob:str|None=None)->Any:
    if expected_blob is not None: req(blob(path)==expected_blob,f'{name} blob changed')
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot load {path}')
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

def write_gz(path:Path,obj:Any)->None:
    with gzip.open(path,'wt',encoding='utf-8',newline='') as f: json.dump(obj,f,sort_keys=True,separators=(',',':'),allow_nan=False)
def read_gz(path:Path)->Any:
    with gzip.open(path,'rt',encoding='utf-8') as f: return json.load(f)

def atom_dict(a:Any)->dict[str,Any]:
    return {'aid':a.aid,'bin_index':int(a.bin_index),'center':float(a.center),'members':list(a.members),'u':[float(x) for x in np.asarray(a.u)],'logv':float(a.logv),'medoid_residual':float(a.medoid_residual)}
def atom_obj(mod:Any,d:dict[str,Any])->Any:
    return mod.Atom(str(d['aid']),int(d['bin_index']),float(d['center']),tuple(map(str,d['members'])),np.asarray(d['u'],dtype=float),float(d['logv']),float(d['medoid_residual']))
def tube_dict(t:Any)->dict[str,Any]:
    return {'tid':t.tid,'atom_ids':list(t.atom_ids),'members':list(t.members),'strata':int(t.strata),'span':float(t.span),'transition_costs':[float(x) for x in t.transition_costs]}
def tube_obj(mod:Any,d:dict[str,Any])->Any:
    return mod.Tube(str(d['tid']),tuple(map(str,d['atom_ids'])),tuple(map(str,d['members'])),int(d['strata']),float(d['span']),tuple(float(x) for x in d['transition_costs']))

def load_science(path:Path)->Any: return load(path,'rft_sharded_frozen',FROZEN_BLOB)

def parse_exact_events(a:argparse.Namespace)->tuple[Any,list[dict[str,Any]],dict[str,str],list[dict[str,Any]]]:
    mod=load_science(a.frozen_source)
    req(sha256(a.quality_source)==QUALITY_SHA,'#839 utility changed'); req(sha256(a.v8_result_json)==V8_SHA,'v8 support changed')
    qmod=mod.load_module(a.quality_source,'rft_sharded_839')
    qmod.v1.mult.YEARS=mod.YEARS; qmod.v1.mult.MONTH_KEYS=mod.MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=mod.YEARS; support.MONTH_KEYS=mod.MONTH_KEYS; support.CORPUS='orbittrace-recurrent-flow-tube-v1-development-2022-only'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==mod.BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base)
    req(sorted(scan)==[mod.YEAR],f'wrong years: {sorted(scan)}'); req([x['key'] for x in sources]==list(mod.MONTH_KEYS),'source months changed')
    raw=list(scan[mod.YEAR]); events=[mod.normalize_event(row) for row in raw]
    req(len(events)==len(raw),'normalization count changed'); req(all(not(mod.BLIND[0]<=e['sol']<=mod.BLIND[1]) for e in events),'protected event survived'); req(all(str(e['id']).startswith(str(mod.YEAR)) for e in events),'non-2022 event')
    req(all(str(eid).startswith(str(mod.YEAR)) for eid in hidden),'non-2022 label')
    return mod,events,{str(k):str(v) for k,v in hidden.items()},sources

def cmd_prepare(a:argparse.Namespace)->int:
    a.output.mkdir(parents=True,exist_ok=True); mod,events,hidden,sources=parse_exact_events(a)
    ids=[str(e['id']) for e in events]; req(len(ids)==len(set(ids)),'duplicate normalized event id')
    write_gz(a.output/'events.json.gz',events); write_gz(a.output/'hidden.json.gz',hidden)
    manifest={'role':'RFT_V1_SHARDED_ENGINEERING_INTERMEDIATE_ONLY','year':mod.YEAR,'events':len(events),'labels':len(hidden),'source_month_count':len(sources),'event_id_order_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),'blind_exclusion':list(mod.BLIND),'gmn_2023_access':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'PREPARE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); print(json.dumps(manifest,indent=2)); return 0

def cmd_atoms(a:argparse.Namespace)->int:
    req(0<=a.replica<=16,'invalid replica'); req(0<=a.shard<SHARDS,'invalid shard'); a.output.mkdir(parents=True,exist_ok=True)
    mod=load_science(a.frozen_source); wrapper=load(a.wrapper,'rft_sharded_wrapper',WRAPPER_BLOB); events=read_gz(a.events)
    req(all(not(mod.BLIND[0]<=float(e['sol'])<=mod.BLIND[1]) for e in events),'protected event in intermediate')
    rep_events=events if a.replica==0 else mod.perturb(events,a.replica)
    selected=[e for e in rep_events if int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH))%SHARDS==a.shard]
    expected=sum(1 for e in rep_events if int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH))%SHARDS==a.shard); req(len(selected)==expected,'shard assignment mismatch')
    original_unit,original_pair=mod.unit,mod.pair_d; unit_cache={}; pair_cache={}; calls=0; misses=0
    def cached_unit(lon_deg,lat_deg):
        lon=np.asarray(lon_deg); lat=np.asarray(lat_deg)
        if lon.ndim==lat.ndim==1 and len(lon)==len(lat)==1:
            key=(float(lon[0]),float(lat[0])); row=unit_cache.get(key)
            if row is not None:return row.reshape(1,3)
            out=original_unit(lon,lat); unit_cache[key]=out[0].copy(); return out
        out=original_unit(lon,lat)
        if lon.ndim==lat.ndim==1 and len(lon)==len(lat)==len(out):
            for lo,la,row in zip(lon,lat,out): unit_cache[(float(lo),float(la))]=row.copy()
        return out
    def memo_pair(x,y):
        nonlocal calls,misses; calls+=1; key=(id(x),id(y))
        if key in pair_cache:return pair_cache[key]
        misses+=1; v=original_pair(x,y); pair_cache[key]=v; return v
    mod.unit=cached_unit; mod.pair_d=memo_pair; t0=time.monotonic()
    try: atoms=wrapper._accelerated_atoms(mod,selected)
    finally: mod.unit=original_unit; mod.pair_d=original_pair
    rows=[atom_dict(x) for x in atoms]; req(len({x['aid'] for x in rows})==len(rows),'duplicate atom id in shard')
    out=a.output/f'atoms_r{a.replica:02d}_s{a.shard}.json.gz'; write_gz(out,rows)
    stats={'replica':a.replica,'shard':a.shard,'input_events':len(events),'shard_events':len(selected),'atoms':len(rows),'pair_d_calls':calls,'pair_d_original_evaluations':misses,'elapsed_seconds':time.monotonic()-t0,'atom_file_sha256':sha256(out)}
    (a.output/f'atoms_r{a.replica:02d}_s{a.shard}_stats.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n'); print(json.dumps(stats)); return 0

def cmd_tubes(a:argparse.Namespace)->int:
    req(0<=a.replica<=16,'invalid replica'); a.output.mkdir(parents=True,exist_ok=True); mod=load_science(a.frozen_source)
    atoms=[]; shard_counts=[]
    for s in range(SHARDS):
        path=a.atom_dir/f'atoms_r{a.replica:02d}_s{s}.json.gz'; req(path.exists(),f'missing atom shard {path}'); rows=read_gz(path); shard_counts.append(len(rows)); atoms.extend(atom_obj(mod,x) for x in rows)
    req(len({x.aid for x in atoms})==len(atoms),'duplicate atom id after shard combine')
    t0=time.monotonic(); owned=mod.build_tubes(atoms,ownership=True); unowned=mod.build_tubes(atoms,ownership=False)
    payload={'replica':a.replica,'shard_atom_counts':shard_counts,'atoms':len(atoms),'owned':[tube_dict(t) for t in owned],'unowned':[tube_dict(t) for t in unowned]}
    out=a.output/f'tubes_r{a.replica:02d}.json.gz'; write_gz(out,payload)
    stats={'replica':a.replica,'atoms':len(atoms),'owned_tubes':len(owned),'unowned_tubes':len(unowned),'elapsed_seconds':time.monotonic()-t0,'tube_file_sha256':sha256(out)}
    (a.output/f'tubes_r{a.replica:02d}_stats.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n'); print(json.dumps(stats)); return 0

def trim_metrics(m:dict[str,Any])->dict[str,Any]: return m

def cmd_final(a:argparse.Namespace)->int:
    a.output.mkdir(parents=True,exist_ok=True); mod=load_science(a.frozen_source); cached=load(a.cached_runner,'rft_sharded_cached',CACHED_BLOB)
    events=read_gz(a.events); hidden=read_gz(a.hidden); req(all(not(mod.BLIND[0]<=float(e['sol'])<=mod.BLIND[1]) for e in events),'protected event in final')
    tube_cache={}; tube_stats=[]
    for r in range(mod.PERTURB_REPLICAS+1):
        path=a.tube_dir/f'tubes_r{r:02d}.json.gz'; req(path.exists(),f'missing tube replica {r}'); p=read_gz(path); req(int(p['replica'])==r,f'replica identity mismatch {r}')
        tube_cache[(r,True)]=[tube_obj(mod,x) for x in p['owned']]; tube_cache[(r,False)]=[tube_obj(mod,x) for x in p['unowned']]; tube_stats.append({'replica':r,'atoms':int(p['atoms']),'owned_tubes':len(p['owned']),'unowned_tubes':len(p['unowned'])})
    fams=cached.generate_cached(mod,events,tube_cache,ownership=True,do_trim=True,do_persistence=True); m=mod.metrics(fams,hidden)
    ab_owner=mod.metrics(cached.generate_cached(mod,events,tube_cache,ownership=False,do_trim=True,do_persistence=True),hidden)
    ab_persist=mod.metrics(cached.generate_cached(mod,events,tube_cache,ownership=True,do_trim=True,do_persistence=False),hidden)
    ab_trim=mod.metrics(cached.generate_cached(mod,events,tube_cache,ownership=True,do_trim=False,do_persistence=True),hidden)
    ptop=[float(f['persistence']) for f in fams[:100]]; high=float(np.mean([x>=0.75 for x in ptop])) if ptop else 0.0
    viable=bool(int(m['qualified_matches'])>=120 and int(m['recovered_at_100'])>=55 and float(m['top100_dominant_precision'])>=0.60 and float(m['fragmentation_median_top500'])<=3.0 and high>=0.75)
    verdict='PASS_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY' if viable else 'FAIL_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY'
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY','execution_role':'SHARDED_ENGINEERING_NONAUTHORITATIVE_PENDING_EQUIVALENCE','events':len(events),'retained_candidates':len(fams),'metrics':m,'top100_persistence_ge_0p75_share':high,'ablations':{'no_path_ownership':ab_owner,'no_perturbation_persistence':ab_persist,'no_trajectory_trim':ab_trim},'frozen_constants':{'bin_width_deg':mod.BIN_WIDTH,'knn':mod.KNN,'min_atom':mod.MIN_ATOM,'min_strata':mod.MIN_STRATA,'min_span_deg':mod.MIN_SPAN,'min_events':mod.MIN_EVENTS,'perturb_replicas':mod.PERTURB_REPLICAS,'perturb_radiant_sigma_deg':mod.PERTURB_RAD_DEG,'perturb_speed_sigma_frac':mod.PERTURB_SPEED_FRAC,'persistence_jaccard':mod.PERSIST_JACCARD,'persistence_min':mod.PERSIST_MIN,'trajectory_trim':mod.TRAJECTORY_TRIM},'blind_exclusion':list(mod.BLIND),'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'sonotaco_2013_2014_access':False,'gmn_2023_access':False,'candidate_order_sha256':hashlib.sha256('\n'.join(f['family_id'] for f in fams).encode()).hexdigest(),'tube_replica_stats':tube_stats,'cached_generate_equivalence_authorizer':{'run':31815566243,'artifact':9224847857,'digest':'sha256:75ca0bf59e3b1cff29d5480097c1a2d4455c88d65db2edb633a7426eccb1b4cb'}}
    rp=a.output/'RFT_V1_GMN2022_SHARDED_ENGINEERING.json'; cp=a.output/'rft_v1_gmn2022_sharded_candidates.json'; rp.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); cp.write_text(json.dumps(fams,indent=2,sort_keys=True,allow_nan=False)+'\n')
    report={'role':'SHARDED_ENGINEERING_NONAUTHORITATIVE_PENDING_ATOM_EQUIVALENCE','scientific_changes':False,'replicas':17,'shards_per_replica':SHARDS,'result_sha256':sha256(rp),'candidates_sha256':sha256(cp),'frozen_science_blob':FROZEN_BLOB,'cached_runner_blob':CACHED_BLOB,'wrapper_blob':WRAPPER_BLOB,'gmn_2023_access':False,'sonotaco_access':False}
    (a.output/'SHARDED_ENGINEERING_REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({'verdict':verdict,'metrics':m,'engineering':report},indent=2)); return 0

def common_data_args(p:argparse.ArgumentParser)->None:
    p.add_argument('--frozen-source',type=Path,required=True); p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True); p.add_argument('--v8-result-json',type=Path,required=True)

def main()->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    x=sub.add_parser('prepare'); common_data_args(x); x.add_argument('--output',type=Path,required=True)
    x=sub.add_parser('atoms'); x.add_argument('--frozen-source',type=Path,required=True); x.add_argument('--wrapper',type=Path,required=True); x.add_argument('--events',type=Path,required=True); x.add_argument('--replica',type=int,required=True); x.add_argument('--shard',type=int,required=True); x.add_argument('--output',type=Path,required=True)
    x=sub.add_parser('tubes'); x.add_argument('--frozen-source',type=Path,required=True); x.add_argument('--atom-dir',type=Path,required=True); x.add_argument('--replica',type=int,required=True); x.add_argument('--output',type=Path,required=True)
    x=sub.add_parser('final'); x.add_argument('--frozen-source',type=Path,required=True); x.add_argument('--cached-runner',type=Path,required=True); x.add_argument('--events',type=Path,required=True); x.add_argument('--hidden',type=Path,required=True); x.add_argument('--tube-dir',type=Path,required=True); x.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); return {'prepare':cmd_prepare,'atoms':cmd_atoms,'tubes':cmd_tubes,'final':cmd_final}[a.cmd](a)

if __name__=='__main__': raise SystemExit(main())
