#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,importlib.util,json,math,sys,time
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
FROZEN_BLOB='a5d5371f0c30a9c57ee4d8756ea41f454cd86301';FAST_PAIR_BLOB='5c6e914849a24bc2683c7e7e86e5f34f80834df4';CHUNKED_BLOB='17cab3c6abc80faa0087da66ce6ea80cfa5ac8cd';PIECES=3

def req(ok,msg):
    if not ok:raise RuntimeError(msg)
def blob(path):
    b=path.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(path,name,expected):
    req(blob(path)==expected,f'{name} changed');spec=importlib.util.spec_from_file_location(name,path);req(spec and spec.loader,f'cannot load {path}');m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def read_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)
def write_gz(path,obj):
    with gzip.open(path,'wt',encoding='utf-8',newline='') as f:json.dump(obj,f,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def bidx(mod,e):return int(math.floor((float(e['coord'])-mod.BLIND[1])/mod.BIN_WIDTH))
def assignment(mod,events):
    counts=Counter(bidx(mod,e) for e in events if bidx(mod,e)%4==3);pieces=[[] for _ in range(PIECES)];loads=[0]*PIECES
    for b,n in sorted(counts.items(),key=lambda kv:(-(kv[1]**2),kv[0])):
        p=min(range(PIECES),key=lambda j:(loads[j],j));pieces[p].append(int(b));loads[p]+=int(n)**2
    for x in pieces:x.sort()
    return pieces,loads,dict(counts)
def atom_dict(a):return {'aid':a.aid,'bin_index':int(a.bin_index),'center':float(a.center),'members':list(a.members),'u':[float(x) for x in np.asarray(a.u)],'logv':float(a.logv),'medoid_residual':float(a.medoid_residual)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--frozen-source',type=Path,required=True);p.add_argument('--fast-pair-source',type=Path,required=True);p.add_argument('--chunked-source',type=Path,required=True);p.add_argument('--events',type=Path,required=True);p.add_argument('--replica',type=int,required=True);p.add_argument('--piece',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();req(0<=a.replica<=16 and 0<=a.piece<PIECES,'invalid matrix');a.output.mkdir(parents=True,exist_ok=True)
    mod=load(a.frozen_source,'rft_chunked_repair_frozen',FROZEN_BLOB);fast=load(a.fast_pair_source,'rft_chunked_repair_fast',FAST_PAIR_BLOB);chunked=load(a.chunked_source,'rft_chunked_repair_atoms',CHUNKED_BLOB);events=read_gz(a.events);req(all(not(mod.BLIND[0]<=float(e['sol'])<=mod.BLIND[1]) for e in events),'protected event')
    pieces,loads,counts=assignment(mod,events);chosen=set(pieces[a.piece]);rep=events if a.replica==0 else mod.perturb(events,a.replica);selected=[e for e in rep if bidx(mod,e) in chosen];req(len(selected)==sum(counts[b] for b in chosen),'piece event count changed')
    pair=fast.build_exact_fast_pair_d(mod,selected);started=time.monotonic();atoms=chunked.exact_chunked_atoms(mod,selected,pair);rows=[atom_dict(x) for x in atoms];req(len({x['aid'] for x in rows})==len(rows),'duplicate atom');req(all(int(x['bin_index']) in chosen for x in rows),'wrong bin atom')
    out=a.output/f'atoms_r{a.replica:02d}_s3p{a.piece}.json.gz';write_gz(out,rows);payload={'piece_bins':pieces,'piece_n2_loads':loads,'piece_event_counts':[sum(counts[b] for b in x) for x in pieces]};assign_sha=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest();stats={'replica':a.replica,'piece':a.piece,'input_events':len(events),'selected_events':len(selected),'atoms':len(rows),'elapsed_seconds':time.monotonic()-started,'atom_file_sha256':sha(out),'assignment_sha256':assign_sha,'chunk_rows':int(chunked.QUERY_CHUNK),'fast_pair_source_blob':FAST_PAIR_BLOB,'global_pair_value_cache':False,**payload};(a.output/f'atoms_r{a.replica:02d}_s3p{a.piece}_stats.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n');print(json.dumps(stats,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
