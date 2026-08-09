#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import types
from pathlib import Path
from typing import Any

YEARS=(2023,2025)
BLIND_LOW=20.0
BLIND_HIGH=55.0


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--archive-2023',required=True,type=Path); p.add_argument('--archive-2025',required=True,type=Path)
    p.add_argument('--manifest-2023',required=True,type=Path); p.add_argument('--manifest-2025',required=True,type=Path)
    p.add_argument('--exact-row-runner',required=True,type=Path); p.add_argument('--orbit-reader',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def load_panel_manifest(path:Path,panel:str,year:int)->dict[str,Any]:
    m=json.loads(path.read_text())
    side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==canonical_sha(m),f'{panel} {year} strict manifest hash mismatch')
    require(m['classification']=='P13 matched-literature strict panel-year ID-only manifest','wrong P13 strict manifest class')
    require(m['panel']==panel and int(m['year'])==year,'strict manifest panel/year changed')
    require(m['blind_exclusion']==[BLIND_LOW,BLIND_HIGH],'strict manifest blind interval changed')
    require(m['competitor_cluster_values_accessed'] is False and m['known_shower_truth_accessed'] is False,'values entered strict manifest')
    ids=list(map(str,m['event_ids'])); require(len(ids)==int(m['event_count']) and len(ids)==len(set(ids)),f'{panel} {year} strict ID count invalid')
    require(all(x.startswith(f'SNM{year}:') for x in ids),f'{panel} {year} strict ID prefix invalid')
    return m


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    exact=load_module(a.exact_row_runner,'p13_exact_rows_v2'); orbit=load_module(a.orbit_reader,'p13_exact_orbits_v2')
    require(tuple(exact.YEARS)==YEARS,'exact-row year universe changed')
    require(float(exact.BLIND_LOW)==BLIND_LOW and float(exact.BLIND_HIGH)==BLIND_HIGH,'exact-row blind interval changed')

    # Exact proven P3 matched-literature initialization, but stop at immutable v8 core.
    runtime=exact.v8.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    require(float(support.BLIND_LOW)==BLIND_LOW and float(support.BLIND_HIGH)==BLIND_HIGH,'support blind interval changed')
    support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS='sonotaco-exact-row-literature-pairwise'; support.RANKING_VARIANTS=exact.RAW_FIXED4_RANKING_VARIANTS
    srcargs=types.SimpleNamespace(support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    _candidate,base,_scorer=support.load_sources(srcargs)
    exact.v8.YEARS=YEARS; exact.v8.MONTH_KEYS=tuple(); exact.v8.mult.YEARS=YEARS; exact.v8.mult.MONTH_KEYS=tuple()

    archives={2023:a.archive_2023,2025:a.archive_2025}; manifests={2023:a.manifest_2023,2025:a.manifest_2025}
    scan:dict[int,list[dict[str,Any]]]={}; orbit_by_id:dict[str,dict[str,float]]={}; geometry_audits=[]; orbit_audits=[]; manifest_hashes={}; all_ids:set[str]=set()
    for year in YEARS:
        m=load_panel_manifest(manifests[year],a.panel,year); allowed=set(map(str,m['event_ids']))
        rows=exact.read_exact_geometry(year,archives[year],allowed,base)
        ids={str(e['id']) for e in rows}; require(ids==allowed,'exact-row geometry universe differs from strict manifest')
        require(all(not(BLIND_LOW<=float(e['sol'])<=BLIND_HIGH) for e in rows),'target interval entered exact-row scan')
        scan[year]=rows; all_ids|=ids
        geometry_audits.append({'year':year,'requested':len(allowed),'read':len(rows),'archive_sha256':sha256_file(archives[year]),'label_value_accessed':False})
        orbits=orbit.read_exact_orbits(year,archives[year],allowed); require(set(orbits)==allowed,'exact-row orbit universe differs from strict manifest')
        orbit_by_id.update(orbits); orbit_audits.append({'year':year,'requested':len(allowed),'read':len(orbits),'archive_sha256':sha256_file(archives[year]),'label_value_accessed':False})
        manifest_hashes[str(year)]=sha256_file(manifests[year])
    require(set(orbit_by_id)==all_ids,'combined orbit universe mismatch')

    v8_panel=exact.run_v8_panel(a.panel,scan,support,runtime,base)
    families=v8_panel['families']; order=list(map(str,v8_panel['multiplicity_order']))
    require(len(families)>0 and len(order)==len(families),'P13 core panel empty/rank incomplete')
    require(set(order)=={str(f['family_id']) for f in families},'P13 core rank universe mismatch')
    core_payload=[{'family_id':str(f['family_id']),'event_ids':sorted(map(str,f['event_ids']))} for f in families]; core_payload.sort(key=lambda r:r['family_id'])
    payload={
        'classification':'P13 matched-literature pretruth core panel input','panel':a.panel,'years':list(YEARS),'blind_exclusion':[BLIND_LOW,BLIND_HIGH],
        'competitor_cluster_values_accessed':False,'known_shower_truth_accessed':False,'parameter_search':False,
        'manifest_sha256':manifest_hashes,'scan_by_year':{str(y):scan[y] for y in YEARS},'orbit_by_id':orbit_by_id,
        'geometry_audits':geometry_audits,'orbit_audits':orbit_audits,'core_families':families,'multiplicity_order':order,
        'core_family_count':len(families),'core_pretruth_sha256':canonical_sha(core_payload),
        'exact_v8_panel_summary':{k:v for k,v in v8_panel.items() if k not in {'families','multiplicity_order'}},
        'transport_interface':'exact preserved P3 matched pretruth v8 initialization; stop at immutable core before any truth/cluster value',
    }
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode(); out=a.output/f'p13_{a.panel}_core_panel_input.json.gz'; out.write_bytes(gzip.compress(raw))
    (a.output/f'p13_{a.panel}_core_panel_input.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n'); (a.output/f'p13_{a.panel}_core_ids.sha256').write_text(payload['core_pretruth_sha256']+'\n')
    print('P13_MATCHED_CORE_PANEL_V2_FROZEN',a.panel,json.dumps({'families':len(families),'core_pretruth_sha256':payload['core_pretruth_sha256'],'rows':{str(y):len(scan[y]) for y in YEARS}},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
