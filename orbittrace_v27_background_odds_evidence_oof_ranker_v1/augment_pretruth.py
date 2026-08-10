#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import b1_runtime as b1
from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
BASE_FEATURE_DIM=71
ODDS_DIM=2
FEATURE_DIM=73
EXPECTED_V19_FAMILY_SHA={
    'sugar':'911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    'hdbscan':'7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
}
REQUIRED_ORBIT_FIELDS=('q','e','inc','peri','node')


def array_sha(x: np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path: Path,obj: Any)->str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def orbit_tuple(row: dict[str,Any])->tuple[float,float,float,float,float]:
    vals=tuple(float(row[k]) for k in REQUIRED_ORBIT_FIELDS)
    require(all(math.isfinite(x) for x in vals),f'non-finite SonotaCo orbit: {row.get("id")}')
    return vals  # type: ignore[return-value]


def annual_b1_mean_log_odds(
    *,
    target_year: int,
    family: dict[str,Any],
    expanded_ids: list[str],
    original_ids: set[str],
    rows: dict[int,list[dict[str,Any]]],
    event_lookup: dict[int,dict[str,dict[str,Any]]],
    orbit_lookup: dict[int,dict[str,tuple[float,float,float,float,float]]],
)->tuple[float,dict[str,Any]]:
    source_year=YEARS[1] if target_year==YEARS[0] else YEARS[0]
    source_ids=sorted(original_ids & set(event_lookup[source_year]))
    require(len(source_ids)>=4,f'{family["family_id"]} source year {source_year} has <4 original seeds')
    source_events=[event_lookup[source_year][eid] for eid in source_ids]
    source_orbits=[orbit_lookup[source_year][eid] for eid in source_ids]

    trajectory=b1.v4.fit_trajectory(source_events)
    stream_d2=b1.v3.source_leave_one_out_d2(source_events)
    stream_residual=b1.v4.loo_residuals(source_events)
    stream_orbit=b1.orbit_loo_median(source_orbits)
    x_stream=b1.feature_matrix(stream_d2,stream_residual,stream_orbit)

    source_all=rows[source_year]
    source_sol=np.asarray([float(e['sol'])%360.0 for e in source_all],dtype=np.float64)
    src_mask=b1.v4.in_activity_arc(source_sol,[float(e['sol']) for e in source_events])
    source_id_set=set(source_ids)
    source_candidates=[source_all[int(i)] for i in np.flatnonzero(src_mask)]
    source_candidates=[e for e in source_candidates if str(e['id']) not in source_id_set]
    bg_events,x_bg,_bd2,_bres,_borb=b1.screened_features(source_candidates,source_events,trajectory,orbit_lookup[source_year],source_orbits)
    require(len(bg_events)>=4,f'{family["family_id"]} source year {source_year} has <4 screened local-field events')

    stream_model=b1.fit_gaussian(x_stream)
    background_model=b1.fit_gaussian(x_bg)
    log_prior_odds=math.log(len(source_events)/len(bg_events))

    target_ids=sorted(eid for eid in expanded_ids if eid in event_lookup[target_year])
    require(target_ids,f'{family["family_id"]} target year {target_year} has no fixed expanded members')
    target_events=[event_lookup[target_year][eid] for eid in target_ids]
    td1,td2=b1.v3.target_d1_d2(target_events,source_events)
    require(len(td1)==len(target_events) and len(td2)==len(target_events),'B1 target density shape mismatch')
    residual=b1.v4.trajectory_residuals(trajectory,target_events)
    orbital=b1.candidate_orbit_median(target_ids,orbit_lookup[target_year],source_orbits)
    x_target=b1.feature_matrix(np.asarray(td2,dtype=np.float64),np.asarray(residual,dtype=np.float64),np.asarray(orbital,dtype=np.float64))
    log_odds=log_prior_odds+b1.gaussian_logpdf(stream_model,x_target)-b1.gaussian_logpdf(background_model,x_target)
    require(len(log_odds)==len(target_ids) and np.all(np.isfinite(log_odds)),'non-finite B1 fixed-member log odds')
    return float(np.mean(log_odds)),{
        'target_year':target_year,'source_year':source_year,'source_seed_count':len(source_ids),
        'source_background_count':len(bg_events),'fixed_target_member_count':len(target_ids),
        'mean_log_posterior_odds':float(np.mean(log_odds)),
        'median_log_posterior_odds':float(np.median(log_odds)),
        'min_log_posterior_odds':float(np.min(log_odds)),
        'max_log_posterior_odds':float(np.max(log_odds)),
        'target_acceptance_cutoff_applied':False,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--v22-root',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    meta=json.loads((a.v22_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); membership=json.loads((a.v22_root/'family_memberships.json').read_text())
    require(meta['comparator']==a.comparator and meta['feature_dimension']==BASE_FEATURE_DIM,'wrong v22 route/feature identity')
    require(meta['truth_accessed'] is False and membership['truth_accessed'] is False,'truth-bearing v22 payload')
    require(meta['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[a.comparator],'v19 expanded family identity changed')
    x71=np.load(a.v22_root/'features.npy',allow_pickle=False); require(x71.shape==(len(meta['family_ids']),BASE_FEATURE_DIM) and array_sha(x71)==meta['feature_sha256'],'invalid base feature matrix')
    expanded=membership['families']; ids=list(map(str,meta['family_ids'])); require([str(f['family_id']) for f in expanded]==ids,'expanded membership alignment changed')
    by_expanded={str(f['family_id']):f for f in expanded}; v19_order=list(map(str,meta['v19_order'])); require(set(v19_order)==set(ids) and len(v19_order)==len(ids),'v19 order universe changed'); require(canonical_sha([by_expanded[fid] for fid in v19_order])==EXPECTED_V19_FAMILY_SHA[a.comparator],'expanded family identity changed')

    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(r['year'])==year for r in raw[year]),f'invalid rows {year}')
        require(all(not (forbidden & {str(k).lower() for k in r}) for r in raw[year]),'truth-bearing field reached v27 pretruth augmentation')
        require(all(not (20.0<=float(r['sol'])%360.0<=55.0) for r in raw[year]),f'protected target interval present in {year} rows')
        require(all(all(k in r for k in REQUIRED_ORBIT_FIELDS) for r in raw[year]),f'missing orbital fields in {year}')
    canonical=v15_application.validate_pair(YEARS,raw)

    runtime,support,base,_=load_support_base(p19_module=type('Shim',(),{'mult':v17.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20); require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed'); support.CORPUS=p19.CORPUS
    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    s19,_=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    s20=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)['soft_families']
    originals=hard['hard_families']+s19+s20; original_by_id={str(f['family_id']):f for f in originals}; require(set(original_by_id)==set(ids) and len(original_by_id)==len(ids),'reconstructed candidate universe differs')

    event_lookup={y:{str(r['id']):r for r in raw[y]} for y in YEARS}; orbit_lookup={y:{str(r['id']):orbit_tuple(r) for r in raw[y]} for y in YEARS}
    require(all(len(event_lookup[y])==len(raw[y]) for y in YEARS),'duplicate SonotaCo row IDs')

    evidence=[]; source_seed_counts=[]; background_counts=[]; member_counts=[]; family_diag=[]
    for idx,fid in enumerate(ids,start=1):
        ef=by_expanded[fid]; orig=original_by_id[fid]; original_ids=set(map(str,orig['event_ids'])); expanded_ids=list(map(str,ef['event_ids']))
        annual=[]; diags=[]
        for y in YEARS:
            val,diag=annual_b1_mean_log_odds(target_year=y,family=orig,expanded_ids=expanded_ids,original_ids=original_ids,rows=raw,event_lookup=event_lookup,orbit_lookup=orbit_lookup)
            annual.append(val); diags.append(diag); source_seed_counts.append(diag['source_seed_count']); background_counts.append(diag['source_background_count']); member_counts.append(diag['fixed_target_member_count'])
        evidence.append(annual); family_diag.append({'family_id':fid,'annual':diags})
        if idx%25==0 or idx==len(ids): print(f'V27_B1_EVIDENCE_PROGRESS comparator={a.comparator} family={idx}/{len(ids)}',flush=True)

    odds=np.asarray(evidence,dtype=np.float64); require(odds.shape==(len(ids),ODDS_DIM) and np.all(np.isfinite(odds)),'v27 odds matrix invalid')
    x73=np.column_stack([x71,odds]).astype(np.float64,copy=False); require(x73.shape==(len(ids),FEATURE_DIM) and np.all(np.isfinite(x73)),'v27 feature matrix invalid')
    np.save(a.output/'background_odds_evidence.npy',odds,allow_pickle=False); np.save(a.output/'features_v27.npy',x73,allow_pickle=False)
    out={
        'scientific_stage':'V27_FIXED_MEMBERSHIP_B1_BACKGROUND_ODDS_PRETRUTH_FEATURE_FREEZE','comparator':a.comparator,'years':list(YEARS),'family_ids':ids,
        'base_feature_dimension':BASE_FEATURE_DIM,'background_odds_dimension':ODDS_DIM,'feature_dimension':FEATURE_DIM,
        'base_feature_sha256':array_sha(x71),'background_odds_evidence_sha256':array_sha(odds),'feature_sha256':array_sha(x73),
        'background_odds_source':'exact frozen B1 stream-vs-local-field Gaussian posterior model; continuous evidence only',
        'annual_feature_definition':'arithmetic mean transferred B1 log posterior odds across every exact fixed expanded member in that target year',
        'b1_event_acceptance_cutoff_used':False,'membership_changed':False,'aggregation_search':False,'b1_parameter_search':False,
        'source_seed_count_min':int(min(source_seed_counts)),'source_seed_count_median':float(np.median(source_seed_counts)),
        'source_background_count_min':int(min(background_counts)),'source_background_count_median':float(np.median(background_counts)),
        'fixed_member_count_min':int(min(member_counts)),'fixed_member_count_median':float(np.median(member_counts)),
        'protected_interval_rows':0,'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    dump(a.output/'V27_PRETRUTH_FEATURE_MANIFEST.json',out); dump(a.output/'V27_PRETRUTH_FAMILY_DIAGNOSTICS.json',{'comparator':a.comparator,'families':family_diag,'truth_accessed':False,'target_information_access':False})
    print(json.dumps(out,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
