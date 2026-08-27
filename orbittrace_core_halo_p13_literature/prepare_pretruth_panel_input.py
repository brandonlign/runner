#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS=(2023,2025)
BLIND_LOW=20.0
BLIND_HIGH=55.0


def require(ok:bool,message:str)->None:
    if not ok:
        raise RuntimeError(message)


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--archive-2023',required=True,type=Path)
    p.add_argument('--archive-2025',required=True,type=Path)
    p.add_argument('--manifest-2023',required=True,type=Path)
    p.add_argument('--manifest-2025',required=True,type=Path)
    p.add_argument('--exact-row-runner',required=True,type=Path)
    p.add_argument('--orbit-reader',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    exact=load_module(args.exact_row_runner,'p13_matched_exact_row')
    orbit=load_module(args.orbit_reader,'p13_matched_orbit_reader')
    require(tuple(exact.YEARS)==YEARS,'exact-row year universe changed')
    require(float(exact.BLIND_LOW)==BLIND_LOW and float(exact.BLIND_HIGH)==BLIND_HIGH,'exact-row blind interval changed')

    support=exact.load_support_module(args.support_source_parts)
    source_args=argparse.Namespace(candidate_payload=args.candidate_payload,baseline_payload=args.baseline_payload,scorer_parts=args.scorer_parts)
    _,base,_=support.load_sources(source_args)
    v8=exact.load_exact_v8_runtime()
    family_support=exact.load_exact_family_support()

    archives={2023:args.archive_2023,2025:args.archive_2025}
    manifests={2023:args.manifest_2023,2025:args.manifest_2025}
    scan:dict[int,list[dict[str,Any]]]={}
    orbit_by_id:dict[str,dict[str,float]]={}
    geometry_audits=[]; orbit_audits=[]; manifest_hashes={}
    all_ids:set[str]=set()
    for year in YEARS:
        manifest=exact.read_strict_manifest(manifests[year])
        require(manifest['panel']==args.panel and int(manifest['year'])==year,'strict manifest panel/year changed')
        require(manifest['competitor_cluster_values_accessed'] is False,'competitor cluster values entered strict manifest')
        require(manifest['known_shower_truth_accessed'] is False,'truth values entered strict manifest')
        allowed=set(map(str,manifest['event_ids']))
        require(len(allowed)==int(manifest['event_count']),'strict manifest ID count mismatch')
        rows,audit=exact.read_exact_geometry(year,archives[year],allowed,base)
        ids={str(e['id']) for e in rows}
        require(ids==allowed,'exact-row geometry universe differs from strict manifest')
        require(all(not(BLIND_LOW<=float(e['sol'])<=BLIND_HIGH) for e in rows),'target interval entered exact-row scan')
        scan[year]=rows; geometry_audits.append(audit); all_ids |= ids
        orbits=orbit.read_exact_orbits(year,archives[year],allowed)
        require(set(orbits)==allowed,'exact-row orbit universe differs from strict manifest')
        orbit_by_id.update(orbits)
        orbit_audits.append({'year':year,'requested':len(allowed),'read':len(orbits),'archive_sha256':sha256_file(archives[year])})
        manifest_hashes[str(year)]=sha256_file(manifests[year])

    require(set(orbit_by_id)==all_ids,'combined orbit universe mismatch')
    v8_panel=exact.run_v8_panel(args.panel,scan,support,base,v8,family_support)
    families=v8_panel['families']; order=list(map(str,v8_panel['multiplicity_order']))
    require(len(families)>0 and len(order)==len(families),'P13 core panel is empty or rank-incomplete')
    require(set(order)=={str(f['family_id']) for f in families},'P13 core rank universe mismatch')
    core_payload=[{'family_id':str(f['family_id']),'event_ids':sorted(map(str,f['event_ids']))} for f in families]
    core_payload.sort(key=lambda r:r['family_id'])
    payload={
        'classification':'P13 matched-literature pretruth core panel input',
        'panel':args.panel,
        'years':list(YEARS),
        'blind_exclusion':[BLIND_LOW,BLIND_HIGH],
        'competitor_cluster_values_accessed':False,
        'known_shower_truth_accessed':False,
        'parameter_search':False,
        'manifest_sha256':manifest_hashes,
        'scan_by_year':{str(y):scan[y] for y in YEARS},
        'orbit_by_id':orbit_by_id,
        'geometry_audits':geometry_audits,
        'orbit_audits':orbit_audits,
        'core_families':families,
        'multiplicity_order':order,
        'core_family_count':len(families),
        'core_pretruth_sha256':canonical_sha(core_payload),
        'exact_v8_panel_summary':{k:v for k,v in v8_panel.items() if k not in {'families','multiplicity_order'}},
    }
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    out=args.output/f'p13_{args.panel}_core_panel_input.json.gz'
    out.write_bytes(gzip.compress(raw))
    (args.output/f'p13_{args.panel}_core_panel_input.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n')
    (args.output/f'p13_{args.panel}_core_ids.sha256').write_text(payload['core_pretruth_sha256']+'\n')
    print('P13_MATCHED_CORE_PANEL_FROZEN',args.panel,json.dumps({'families':len(families),'core_pretruth_sha256':payload['core_pretruth_sha256'],'rows':{str(y):len(scan[y]) for y in YEARS}},sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
