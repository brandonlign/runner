#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import types
from pathlib import Path
from typing import Any

import numpy as np

from rectangular_dsh import rectangular_pairwise_dsh

YEARS=(2022,2023)
BLIND=(20.0,55.0)
EXPECTED_P2_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
EXPECTED_DSH_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def sha256_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def compatible_exact_header_positions(text:str)->tuple[list[str],dict[str,int]]:
    candidates:list[list[str]]=[]
    for raw_line in text.splitlines():
        line=raw_line.lstrip('\ufeff \t')
        if not line.startswith('#'):
            continue
        body=line[1:].strip()
        fields=[field.strip() for field in body.split(';')]
        if fields and fields[0]=='Unique trajectory':
            candidates.append(fields)
    require(len(candidates)==1,f'raw schema header not unique after whitespace normalization: {len(candidates)}')
    fields=candidates[0]
    def exact(name:str)->int:
        hits=[idx for idx,field in enumerate(fields) if field==name]
        require(len(hits)==1,f'raw schema field {name!r} not unique: {hits}')
        return hits[0]
    positions={'id':exact('Unique trajectory'),'sol':exact('Sol lon'),'q':exact('q'),'e':exact('e'),'i':exact('i'),'peri':exact('peri'),'node':exact('node')}
    require(len(set(positions.values()))==len(positions),f'raw schema positions overlap: {positions}')
    q_upper=[idx for idx,field in enumerate(fields) if field=='Q']
    require(len(q_upper)==1 and q_upper[0]!=positions['q'],'q/Q schema identity changed')
    return fields,positions


def arrays(ids:list[str],orbit_by_id:dict[str,dict[str,float]])->dict[str,np.ndarray]:
    return {
        'q':np.asarray([orbit_by_id[x]['q'] for x in ids],dtype=np.float64),
        'e':np.asarray([orbit_by_id[x]['e'] for x in ids],dtype=np.float64),
        'i':np.asarray([orbit_by_id[x]['i'] for x in ids],dtype=np.float64),
        'peri':np.asarray([orbit_by_id[x]['peri'] for x in ids],dtype=np.float64),
        'node':np.asarray([orbit_by_id[x]['node'] for x in ids],dtype=np.float64),
    }


def exact_cross(dsh:Any,left:dict[str,np.ndarray],right:dict[str,np.ndarray])->np.ndarray:
    combined={k:np.concatenate((left[k],right[k])) for k in ('q','e','i','peri','node')}
    m=dsh.pairwise_dsh(combined['q'],combined['e'],combined['i'],combined['peri'],combined['node'])
    return np.asarray(m[:len(left['q']),len(left['q']):],dtype=np.float64)


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--p2-source',required=True,type=Path)
    ap.add_argument('--dsh-comparator',required=True,type=Path)
    ap.add_argument('--base-runner',required=True,type=Path)
    ap.add_argument('--support-source-parts',required=True,type=Path)
    ap.add_argument('--candidate-payload',required=True,type=Path)
    ap.add_argument('--baseline-payload',required=True,type=Path)
    ap.add_argument('--scorer-parts',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args()
    require(sha256_file(a.p2_source)==EXPECTED_P2_SHA256,'canonical P2 source changed')
    require(sha256_file(a.dsh_comparator)==EXPECTED_DSH_SHA256,'frozen D_SH source changed')
    p2=load(a.p2_source,'rect_audit_p2')
    # Identical implementation-only raw-header compatibility used by authoritative P6-P8.
    p2.exact_header_positions=compatible_exact_header_positions
    dsh=load(a.dsh_comparator,'rect_audit_dsh')
    old=load(a.base_runner,'rect_audit_base')
    support=old.load_support_module(a.support_source_parts)
    require(float(support.BLIND_LOW)==BLIND[0] and float(support.BLIND_HIGH)==BLIND[1],'blind interval changed')
    source_args=types.SimpleNamespace(candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    _,base,_=support.load_sources(source_args)
    scan_by_year,_,_hidden_labels,_sources=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),'development year universe changed')
    require(all(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in scan_by_year[y]) for y in YEARS),'target interval entered rectangular audit')
    orbit_by_id,orbit_audits=p2.parse_target_excluded_orbits(scan_by_year,support)
    require(bool(orbit_by_id),'empty target-excluded orbit universe')

    ids_by_year={y:sorted(str(e['id']) for e in scan_by_year[y] if str(e['id']) in orbit_by_id) for y in YEARS}
    require(all(len(ids_by_year[y])>=128 for y in YEARS),'insufficient target-excluded audit orbit universe')
    panels=[]
    sizes=((1,1),(2,3),(5,4),(10,7),(25,11),(64,16),(64,64),(127,31))
    def hashed(ids:list[str],salt:str)->list[str]:
        return sorted(ids,key=lambda x:hashlib.sha256((salt+'|'+x).encode()).digest())
    panel_index=0
    for ly,ry in ((2022,2022),(2022,2023),(2023,2022),(2023,2023)):
        for rep in range(5):
            left_pool=hashed(ids_by_year[ly],f'L{ly}-{ry}-{rep}')
            right_pool=hashed(ids_by_year[ry],f'R{ly}-{ry}-{rep}')
            for nl,nr in sizes:
                left_ids=left_pool[:nl]; right_ids=right_pool[:nr]
                if ly==ry:
                    left_set=set(left_ids)
                    right_ids=[x for x in right_pool if x not in left_set][:nr]
                require(len(left_ids)==nl and len(right_ids)==nr,'deterministic panel construction failed')
                left=arrays(left_ids,orbit_by_id); right=arrays(right_ids,orbit_by_id)
                expected=exact_cross(dsh,left,right); observed=rectangular_pairwise_dsh(left,right)
                require(expected.shape==observed.shape,'rectangular shape mismatch')
                equal=bool(np.array_equal(expected,observed))
                max_abs=float(np.max(np.abs(expected-observed))) if expected.size else 0.0
                require(equal,f'rectangular D_SH differs from frozen square cross-slice panel={panel_index} max_abs={max_abs!r}')
                panels.append({'panel':panel_index,'left_year':ly,'right_year':ry,'left_n':nl,'right_n':nr,'array_equal':equal,'max_abs_difference':max_abs})
                panel_index+=1

    result={
        'classification':'RECTANGULAR_DSH_EXACT_EQUIVALENCE_TARGET_EXCLUDED_AUDIT',
        'years':list(YEARS),
        'blind_exclusion':list(BLIND),
        'p2_source_sha256':EXPECTED_P2_SHA256,
        'dsh_source_sha256':EXPECTED_DSH_SHA256,
        'target_excluded_valid_orbit_count':len(orbit_by_id),
        'target_excluded_valid_orbit_count_by_year':{str(y):len(ids_by_year[y]) for y in YEARS},
        'panels_tested':len(panels),
        'all_bitwise_equal':all(x['array_equal'] for x in panels),
        'maximum_absolute_difference':max(x['max_abs_difference'] for x in panels),
        'panels':panels,
        'orbit_parse_audits':orbit_audits,
        'known_shower_label_values_used':False,
        'target_region_orbits_used':False,
        'scientific_parameter_changed':False,
        'header_whitespace_compatibility_same_as_authoritative_p6_p8':True,
    }
    require(result['panels_tested']==160,'audit panel count changed')
    require(result['all_bitwise_equal'] and result['maximum_absolute_difference']==0.0,'rectangular equivalence failed')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f"PASS_RECTANGULAR_DSH_EXACT_EQUIVALENCE_TARGET_EXCLUDED panels={result['panels_tested']} orbits={len(orbit_by_id)}",flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
