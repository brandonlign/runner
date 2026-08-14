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
from pathlib import Path
from typing import Any

import numpy as np

FROZEN_BLOB='a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
WRAPPER_BLOB='8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
FAST_PAIR_BLOB='5c6e914849a24bc2683c7e7e86e5f34f80834df4'
SHARDS=8

def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def blob(path:Path)->str:
    b=path.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(path:Path,name:str,expected:str)->Any:
    req(blob(path)==expected,f'{name} blob changed')
    spec=importlib.util.spec_from_file_location(name,path);req(spec is not None and spec.loader is not None,f'cannot load {path}')
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def read_gz(path:Path)->Any:
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)
def atom_equal(a:Any,b:Any)->bool:
    return bool(a.aid==b.aid and int(a.bin_index)==int(b.bin_index) and float(a.center)==float(b.center) and tuple(a.members)==tuple(b.members) and np.array_equal(np.asarray(a.u),np.asarray(b.u)) and float(a.logv)==float(b.logv) and float(a.medoid_residual)==float(b.medoid_residual))

def compare_bin(mod:Any,wrapper:Any,fast_mod:Any,rows:list[dict[str,Any]],bidx:int)->dict[str,Any]:
    if len(rows)<mod.MIN_ATOM:
        return {'bin_index':bidx,'rows':len(rows),'atoms':0,'scalar_queries':0,'exact':True,'elapsed_seconds':0.0}
    lon=np.asarray([r['lon'] for r in rows],float);lat=np.asarray([r['lat'] for r in rows],float);vg=np.asarray([r['vg'] for r in rows],float)
    uv=mod.unit(lon,lat)
    transformed=np.column_stack((uv/(2.0*math.sin(math.radians(3.0)/2.0)),np.log(vg)/math.log(1.08)))
    tree=mod.cKDTree(transformed);bulk=tree.query_ball_point(transformed,r=1.02);req(len(bulk)==len(rows),f'bulk query count mismatch bin {bidx}')
    for i in range(len(rows)):
        scalar=tree.query_ball_point(transformed[i],r=1.02)
        req(set(map(int,scalar))==set(map(int,bulk[i])),f'candidate-set mismatch bin {bidx} row {i}')
    exact_fast=fast_mod.build_exact_fast_pair_d(mod,rows)
    original_pair=mod.pair_d
    cache:dict[tuple[int,int],float]={}
    def memo(a:dict[str,Any],b:dict[str,Any])->float:
        key=(id(a),id(b))
        if key in cache:return cache[key]
        value=exact_fast(a,b);cache[key]=value;return value
    mod.pair_d=memo;started=time.monotonic()
    try:
        scalar_atoms=mod.atoms(rows)
        batch_atoms=wrapper._accelerated_atoms(mod,rows)
    finally:
        mod.pair_d=original_pair
    req(len(scalar_atoms)==len(batch_atoms),f'atom count mismatch bin {bidx}')
    for i,(a,b) in enumerate(zip(scalar_atoms,batch_atoms)):
        req(atom_equal(a,b),f'atom mismatch bin {bidx} index {i}')
    return {'bin_index':bidx,'rows':len(rows),'atoms':len(scalar_atoms),'scalar_queries':len(rows),'ordered_pair_cache_entries':len(cache),'exact':True,'elapsed_seconds':time.monotonic()-started}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--frozen-source',type=Path,required=True);p.add_argument('--wrapper',type=Path,required=True);p.add_argument('--fast-pair-source',type=Path,required=True);p.add_argument('--events',type=Path,required=True);p.add_argument('--assignment',type=Path,required=True);p.add_argument('--shard',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();req(0<=a.shard<SHARDS,'invalid shard');a.output.mkdir(parents=True,exist_ok=True)
    mod=load(a.frozen_source,'rft_fast_atom_equiv_frozen',FROZEN_BLOB);wrapper=load(a.wrapper,'rft_fast_atom_equiv_wrapper',WRAPPER_BLOB);fast_mod=load(a.fast_pair_source,'rft_fast_atom_equiv_pair',FAST_PAIR_BLOB)
    events=read_gz(a.events);assignment=json.loads(a.assignment.read_text());req(int(assignment['shards'])==SHARDS,'assignment shard count changed');req(len(events)==315024,'prepared event count changed');req(all(not(20.0<=float(e['sol'])<=55.0) for e in events),'protected event present')
    expected=list(map(int,assignment['shard_bins'][a.shard]));counts={int(k):int(v) for k,v in assignment['bin_counts'].items()};by={b:[] for b in expected}
    for e in events:
        b=int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH))
        if b in by:by[b].append(e)
    req(sorted(by)==expected,'assigned bin set changed')
    reports=[];started=time.monotonic()
    for ordinal,b in enumerate(expected,1):
        req(len(by[b])==counts[b],f'bin count changed {b}')
        r=compare_bin(mod,wrapper,fast_mod,by[b],b);reports.append(r);print({'FAST_ATOM_EQUIV_SHARD':a.shard,'bin':ordinal,'of':len(expected),**r},flush=True)
    out={'verdict':'PASS_RFT_V1_COMPOSITIONAL_FAST_ATOM_EQUIVALENCE_SHARD','role':'ENGINEERING_IDENTITY_AUDIT_SHARD_ONLY','shard':a.shard,'assigned_bins':expected,'passed_bins':[r['bin_index'] for r in reports],'atoms':sum(r['atoms'] for r in reports),'scalar_queries':sum(r['scalar_queries'] for r in reports),'elapsed_seconds':time.monotonic()-started,'all_candidate_sets_exact':True,'all_atom_fields_exact':True,'scientific_endpoint_computed':False,'tubes_computed':False,'labels_used':False,'gmn_2023_access':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':[20.0,55.0],'bins':reports}
    (a.output/f'fast_atom_equiv_shard_{a.shard}.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bins'},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
