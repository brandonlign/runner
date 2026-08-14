#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

FROZEN_BLOB='a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
CACHED_BLOB='2a599c6e8247eb819a1090591d586526eda6c0c1'


def req(ok: bool, msg: str) -> None:
    if not ok: raise RuntimeError(msg)


def blob(path: Path) -> str:
    b=path.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()


def load(path: Path, name: str, expected: str) -> Any:
    req(blob(path)==expected,f'{name} blob changed')
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot load {path}')
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m


def canon(x: Any) -> bytes:
    return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--frozen-source',type=Path,required=True); p.add_argument('--cached-runner',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    mod=load(a.frozen_source,'rft_generate_equiv_frozen',FROZEN_BLOB)
    cached=load(a.cached_runner,'rft_generate_equiv_cached',CACHED_BLOB)

    # Exact linear synthetic radiant/speed path -> zero trim residual for base members.
    events=[]
    for i in range(24):
        events.append({'id':f'E{i:02d}','coord':100.0+i*0.25,'sol':100.0+i*0.25,'lon':120.0,'lat':10.0,'vg':30.0})
    ids=[e['id'] for e in events]
    base_a=mod.Tube('A',('a0','a1','a2'),tuple(ids[:12]),3,6.0,(0.10,0.20))
    base_b=mod.Tube('B',('b0','b1','b2'),tuple(ids[8:20]),3,6.0,(0.20,0.30))
    base_c=mod.Tube('C',('c0','c1','c2'),tuple(ids[2:16]),3,6.0,(0.05,0.15))
    base_d=mod.Tube('D',('d0','d1','d2'),tuple(ids[10:24]),3,6.0,(0.15,0.25))

    tube_cache={}
    tube_cache[(0,True)]=[base_a,base_b]
    tube_cache[(0,False)]=[base_c,base_d]
    for r in range(1,mod.PERTURB_REPLICAS+1):
        # A/C always survive. B/D survive only 7/16 -> below frozen 0.50 threshold.
        good_b = r <= 7
        good_d = r <= 7
        ra=mod.Tube(f'RA{r}',('x',),tuple(ids[:12]),3,6.0,(0.1,))
        rb_members=tuple(ids[8:20]) if good_b else tuple(f'X{r}_{j}' for j in range(12))
        rb=mod.Tube(f'RB{r}',('x',),rb_members,3,6.0,(0.1,))
        rc=mod.Tube(f'RC{r}',('x',),tuple(ids[2:16]),3,6.0,(0.1,))
        rd_members=tuple(ids[10:24]) if good_d else tuple(f'Y{r}_{j}' for j in range(14))
        rd=mod.Tube(f'RD{r}',('x',),rd_members,3,6.0,(0.1,))
        tube_cache[(r,True)]=[ra,rb]
        tube_cache[(r,False)]=[rc,rd]

    old_atoms,old_build,old_perturb=mod.atoms,mod.build_tubes,mod.perturb
    current_replica={'value':0}
    def fake_perturb(_events,replica): current_replica['value']=replica; return events
    def fake_atoms(_events): return [('replica',current_replica['value'])]
    def fake_build(atom_list,ownership=True): return tube_cache[(int(atom_list[0][1]),bool(ownership))]
    mod.atoms=fake_atoms; mod.build_tubes=fake_build; mod.perturb=fake_perturb

    modes=[
        ('primary',True,True,True),
        ('no_path_ownership',False,True,True),
        ('no_persistence',True,True,False),
        ('no_trim',True,False,True),
    ]
    results={}
    try:
        for name,ownership,do_trim,do_persistence in modes:
            current_replica['value']=0
            frozen=mod.generate(events,ownership=ownership,do_trim=do_trim,do_persistence=do_persistence)
            current_replica['value']=0
            got=cached.generate_cached(mod,events,tube_cache,ownership=ownership,do_trim=do_trim,do_persistence=do_persistence)
            req(frozen==got,f'object mismatch {name}')
            req(canon(frozen)==canon(got),f'canonical JSON mismatch {name}')
            results[name]={'outputs':len(got),'sha256':hashlib.sha256(canon(got)).hexdigest(),'exact':True}
    finally:
        mod.atoms,mod.build_tubes,mod.perturb=old_atoms,old_build,old_perturb

    req(results['primary']['outputs']==1,'fixture did not exercise persistence rejection primary')
    req(results['no_path_ownership']['outputs']==1,'fixture did not exercise persistence rejection ownership ablation')
    req(results['no_persistence']['outputs']==2,'fixture did not exercise persistence-disabled retention')
    out={
        'verdict':'PASS_RFT_V1_CACHED_GENERATE_SEMANTIC_EQUIVALENCE',
        'role':'SYNTHETIC_ENGINEERING_IDENTITY_AUDIT_ONLY',
        'modes':results,
        'frozen_science_blob':FROZEN_BLOB,'cached_runner_blob':CACHED_BLOB,
        'catalogue_access':False,'labels_access':False,'scientific_endpoint_computed':False,
        'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'gmn_2023_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    (a.output/'RFT_V1_CACHED_GENERATE_EQUIVALENCE.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
