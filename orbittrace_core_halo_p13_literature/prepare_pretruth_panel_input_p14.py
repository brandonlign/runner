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
P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_SUPPORT_BLOB='dfb58023ce26583a532ea5342cde051ff288d44c'


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
    p.add_argument('--p14-rank-module',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def load_panel_manifest(path:Path,panel:str,year:int)->dict[str,Any]:
    m=json.loads(path.read_text()); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==canonical_sha(m),f'{panel} {year} strict manifest hash mismatch')
    require(m['classification']=='P13 matched-literature strict panel-year ID-only manifest','wrong strict manifest class')
    require(m['panel']==panel and int(m['year'])==year,'strict manifest panel/year changed')
    require(m['blind_exclusion']==[BLIND_LOW,BLIND_HIGH],'strict manifest blind interval changed')
    require(m['competitor_cluster_values_accessed'] is False and m['known_shower_truth_accessed'] is False,'values entered strict manifest')
    ids=list(map(str,m['event_ids'])); require(len(ids)==int(m['event_count']) and len(ids)==len(set(ids)),f'{panel} {year} strict ID count invalid')
    require(all(x.startswith(f'SNM{year}:') for x in ids),f'{panel} {year} strict ID prefix invalid')
    return m


def install_p14_rank(exact:Any,p14:Any)->tuple[Any,Any,dict[str,Any]]:
    mult=exact.v8.mult
    require(int(mult.EPISODE_SIZE)==128,'P14 matched episode size changed')
    original_score=mult.score_families; original_rank=mult.rank_scored
    state:dict[str,Any]={}
    immutable=types.SimpleNamespace(EPISODE_SIZE=int(mult.EPISODE_SIZE),score_families=original_score,rank_scored=original_rank)

    def score_families(families: list[dict[str,Any]], scan_by_year: dict[int,list[dict[str,Any]]], runtime:Any, base:Any):
        rows,full_order,audit=p14.score_and_complete_rank(families,scan_by_year,runtime,base,immutable)
        state.clear(); state.update({'full_order':list(map(str,full_order)),'audit':audit,'scored_ids':{str(r['family_id']) for r in rows}})
        return rows,{
            'families_requested':int(audit['families_requested']),
            'families_scored':int(audit['families_scored']),
            'families_unscorable':int(audit['families_unscorable']),
            'episode_count':2*int(audit['families_scored']),
            'episode_sizes':[128] if audit['families_scored'] else [],
            'p14_support_safe_rank':audit,
            'fabricated_scores':False,
            'episode_size_relaxed':False,
        }

    def rank_scored(scored:list[dict[str,Any]],method:str)->list[str]:
        if method!='multiplicity': return list(map(str,original_rank(scored,method)))
        require(state and {str(r['family_id']) for r in scored}==state['scored_ids'],'P14 matched scoring/ranking state drift')
        return list(state['full_order'])

    mult.score_families=score_families; mult.rank_scored=rank_scored
    return original_score,original_rank,state


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    exact=load_module(a.exact_row_runner,'p14_exact_rows'); orbit=load_module(a.orbit_reader,'p14_exact_orbits'); p14=load_module(a.p14_rank_module,'p14_support_safe_rank')
    require(int(p14.EPISODE_SIZE)==128,'P14 support-safe source episode size changed')
    require(tuple(exact.YEARS)==YEARS,'exact-row year universe changed')
    require(float(exact.BLIND_LOW)==BLIND_LOW and float(exact.BLIND_HIGH)==BLIND_HIGH,'exact-row blind interval changed')

    runtime=exact.v8.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    require(float(support.BLIND_LOW)==BLIND_LOW and float(support.BLIND_HIGH)==BLIND_HIGH,'support blind interval changed')
    support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS='sonotaco-exact-row-literature-pairwise'; support.RANKING_VARIANTS=exact.RAW_FIXED4_RANKING_VARIANTS
    srcargs=types.SimpleNamespace(support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    _candidate,base,_scorer=support.load_sources(srcargs)
    exact.v8.YEARS=YEARS; exact.v8.MONTH_KEYS=tuple(); exact.v8.mult.YEARS=YEARS; exact.v8.mult.MONTH_KEYS=tuple()

    archives={2023:a.archive_2023,2025:a.archive_2025}; manifests={2023:a.manifest_2023,2025:a.manifest_2025}
    scan:dict[int,list[dict[str,Any]]]={}; orbit_by_id:dict[str,dict[str,float]]={}; geometry_audits=[]; orbit_audits=[]; manifest_hashes={}; all_ids:set[str]=set()
    for year in YEARS:
        m=load_panel_manifest(manifests[year],a.panel,year); allowed=set(map(str,m['event_ids']))
        rows=exact.read_exact_geometry(year,archives[year],allowed,base); ids={str(e['id']) for e in rows}
        require(ids==allowed,'exact-row geometry universe differs from strict manifest'); require(all(not(BLIND_LOW<=float(e['sol'])<=BLIND_HIGH) for e in rows),'target interval entered exact-row scan')
        scan[year]=rows; all_ids|=ids; geometry_audits.append({'year':year,'requested':len(allowed),'read':len(rows),'archive_sha256':sha256_file(archives[year]),'label_value_accessed':False})
        orbits=orbit.read_exact_orbits(year,archives[year],allowed); require(set(orbits)==allowed,'exact-row orbit universe differs from strict manifest')
        orbit_by_id.update(orbits); orbit_audits.append({'year':year,'requested':len(allowed),'read':len(orbits),'archive_sha256':sha256_file(archives[year]),'label_value_accessed':False})
        manifest_hashes[str(year)]=sha256_file(manifests[year])
    require(set(orbit_by_id)==all_ids,'combined orbit universe mismatch')

    original_score,original_rank,state=install_p14_rank(exact,p14)
    try:
        v8_panel=exact.run_v8_panel(a.panel,scan,support,runtime,base)
    finally:
        exact.v8.mult.score_families=original_score; exact.v8.mult.rank_scored=original_rank
    require(state and 'audit' in state,'P14 rank audit not produced')
    rank_audit=state['audit']; require(int(rank_audit['families_requested'])==len(v8_panel['families']),'P14 requested family count drift')
    require(int(rank_audit['families_scored'])+int(rank_audit['families_unscorable'])==len(v8_panel['families']),'P14 rank accounting incomplete')
    require(rank_audit['fabricated_scores'] is False and rank_audit['episode_size_relaxed'] is False,'P14 fail-closed semantics changed')

    families=v8_panel['families']; order=list(map(str,v8_panel['multiplicity_order']))
    require(len(families)>0 and len(order)==len(families),'P14 core panel empty/rank incomplete'); require(set(order)=={str(f['family_id']) for f in families},'P14 core rank universe mismatch')
    if rank_audit['families_unscorable']:
        tail=sorted(str(x['family_id']) for x in rank_audit['unscorable_families']); require(order[-len(tail):]==tail,'P14 unscorable core not at fail-closed tail')
    core_payload=[{'family_id':str(f['family_id']),'event_ids':sorted(map(str,f['event_ids']))} for f in families]; core_payload.sort(key=lambda r:r['family_id'])
    payload={
        'classification':'P13 matched-literature pretruth core panel input','architecture':'P14_SUPPORT_SAFE_MULTIPLICITY_RANK',
        'p14_source_commit':P14_COMMIT,'p14_support_blob':P14_SUPPORT_BLOB,'panel':a.panel,'years':list(YEARS),'blind_exclusion':[BLIND_LOW,BLIND_HIGH],
        'competitor_cluster_values_accessed':False,'known_shower_truth_accessed':False,'parameter_search':False,
        'manifest_sha256':manifest_hashes,'scan_by_year':{str(y):scan[y] for y in YEARS},'orbit_by_id':orbit_by_id,
        'geometry_audits':geometry_audits,'orbit_audits':orbit_audits,'core_families':families,'multiplicity_order':order,
        'core_family_count':len(families),'core_pretruth_sha256':canonical_sha(core_payload),'p14_support_safe_rank':rank_audit,
        'exact_v8_panel_summary':{k:v for k,v in v8_panel.items() if k not in {'families','multiplicity_order'}},
        'transport_interface':'exact P13-compatible core transport schema plus promoted P14 fail-closed total-order completion; freeze before any truth/cluster value',
    }
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode(); out=a.output/f'p13_{a.panel}_core_panel_input.json.gz'; out.write_bytes(gzip.compress(raw))
    (a.output/f'p13_{a.panel}_core_panel_input.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n'); (a.output/f'p13_{a.panel}_core_ids.sha256').write_text(payload['core_pretruth_sha256']+'\n')
    (a.output/f'p14_{a.panel}_rank_pretruth.json').write_text(json.dumps(rank_audit,indent=2,sort_keys=True)+'\n'); (a.output/f'p14_{a.panel}_rank_pretruth.sha256').write_text(canonical_sha(rank_audit)+'\n')
    print('P14_MATCHED_CORE_PANEL_FROZEN',a.panel,json.dumps({'families':len(families),'scored':rank_audit['families_scored'],'unscorable':rank_audit['families_unscorable'],'core_pretruth_sha256':payload['core_pretruth_sha256'],'rows':{str(y):len(scan[y]) for y in YEARS}},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
