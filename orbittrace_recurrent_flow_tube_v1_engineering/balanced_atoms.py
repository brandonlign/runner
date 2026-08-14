#!/usr/bin/env python3
from __future__ import annotations

import argparse, gzip, hashlib, importlib.util, json, math, sys, time
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np

FROZEN_BLOB='a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
WRAPPER_BLOB='8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
SHARDS=4

def req(ok,msg):
    if not ok: raise RuntimeError(msg)
def blob(path):
    b=path.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(path,name,expected):
    req(blob(path)==expected,f'{name} changed'); spec=importlib.util.spec_from_file_location(name,path); req(spec and spec.loader,f'cannot load {path}'); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def read_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)
def write_gz(path,obj):
    with gzip.open(path,'wt',encoding='utf-8',newline='') as f:json.dump(obj,f,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atom_dict(a):return {'aid':a.aid,'bin_index':int(a.bin_index),'center':float(a.center),'members':list(a.members),'u':[float(x) for x in np.asarray(a.u)],'logv':float(a.logv),'medoid_residual':float(a.medoid_residual)}

def assignment(events,mod):
    counts=Counter(int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH)) for e in events)
    loads=[0]*SHARDS; bins=[set() for _ in range(SHARDS)]
    for b,n in sorted(counts.items(),key=lambda kv:(-(kv[1]**2),kv[0])):
        s=min(range(SHARDS),key=lambda j:(loads[j],j)); bins[s].add(b); loads[s]+=n*n
    return bins,loads,counts

def main():
    p=argparse.ArgumentParser(); p.add_argument('--frozen-source',type=Path,required=True);p.add_argument('--wrapper',type=Path,required=True);p.add_argument('--events',type=Path,required=True);p.add_argument('--replica',type=int,required=True);p.add_argument('--shard',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(0<=a.replica<=16 and 0<=a.shard<SHARDS,'invalid matrix coordinate')
    mod=load(a.frozen_source,'rft_balanced_frozen',FROZEN_BLOB); wrapper=load(a.wrapper,'rft_balanced_wrapper',WRAPPER_BLOB); events=read_gz(a.events)
    req(all(not(mod.BLIND[0]<=float(e['sol'])<=mod.BLIND[1]) for e in events),'protected event in input')
    bins,loads,counts=assignment(events,mod); chosen=bins[a.shard]
    rep=events if a.replica==0 else mod.perturb(events,a.replica)
    selected=[e for e in rep if int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH)) in chosen]
    req(len(selected)==sum(counts[b] for b in chosen),'bin assignment/event count changed under perturbation')
    original_unit,original_pair=mod.unit,mod.pair_d; unit_cache={}; pair_cache={}; calls=0;misses=0
    def cu(lon_deg,lat_deg):
        lon=np.asarray(lon_deg);lat=np.asarray(lat_deg)
        if lon.ndim==lat.ndim==1 and len(lon)==len(lat)==1:
            key=(float(lon[0]),float(lat[0]));row=unit_cache.get(key)
            if row is not None:return row.reshape(1,3)
            out=original_unit(lon,lat);unit_cache[key]=out[0].copy();return out
        out=original_unit(lon,lat)
        if lon.ndim==lat.ndim==1 and len(lon)==len(lat)==len(out):
            for lo,la,row in zip(lon,lat,out):unit_cache[(float(lo),float(la))]=row.copy()
        return out
    def pd(x,y):
        nonlocal calls,misses;calls+=1;key=(id(x),id(y))
        if key in pair_cache:return pair_cache[key]
        misses+=1;v=original_pair(x,y);pair_cache[key]=v;return v
    mod.unit=cu;mod.pair_d=pd;t0=time.monotonic()
    try: atoms=wrapper._accelerated_atoms(mod,selected)
    finally: mod.unit=original_unit;mod.pair_d=original_pair
    rows=[atom_dict(x) for x in atoms]; req(len({x['aid'] for x in rows})==len(rows),'duplicate atom id')
    out=a.output/f'atoms_r{a.replica:02d}_s{a.shard}.json.gz';write_gz(out,rows)
    assign_payload={'shard_loads_n2':loads,'shard_bin_counts':[len(x) for x in bins],'shard_event_counts':[sum(counts[b] for b in x) for x in bins]}
    assign_sha=hashlib.sha256(json.dumps(assign_payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    stats={'replica':a.replica,'shard':a.shard,'input_events':len(events),'shard_events':len(selected),'atoms':len(rows),'pair_d_calls':calls,'pair_d_original_evaluations':misses,'elapsed_seconds':time.monotonic()-t0,'atom_file_sha256':sha256(out),'assignment_sha256':assign_sha,**assign_payload}
    (a.output/f'atoms_r{a.replica:02d}_s{a.shard}_stats.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n');print(json.dumps(stats));return 0
if __name__=='__main__':raise SystemExit(main())
