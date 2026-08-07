#!/usr/bin/env python3
"""One-shot UKMON 2024-2025 external validation of frozen label-free v6."""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import math
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import requests

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult
from orbittrace_label_free_v6_saamer_external import run_external_validation as prior

YEARS=(2024,2025)
BLIND_LOW=20.0
BLIND_HIGH=55.0
MAX_EVENTS_PER_BIN=10_000
TOP_K=100
MIN_SCANNABLE_BINS=24
MIN_FAMILIES=100
MIN_ORBITALLY_CORROBORATED=30
BROWN_EQ_TOL=1e-10
DSH_THRESHOLD=0.05
MIN_YEAR_ORBIT_MEMBERS=4
MIN_ORBITAL_PRECISION=0.50
MAX_WORKERS=6
DAILY_URL='https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval={yyyymmdd}'
PERIODS=('0-6','6-12','12-18','18-24')
REQUIRED_INTERFACE_KEYS=('orbname','_sol','_ra_t','_dc_t','_vg','_q','_e','_incl','_peri','_node')


def require(condition:bool,message:str)->None:
    if not condition:
        raise RuntimeError(message)


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--v6-result-json',required=True,type=Path)
    p.add_argument('--freshness-json',required=True,type=Path)
    p.add_argument('--interface-json',required=True,type=Path)
    p.add_argument('--dsh-comparator',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def finite(value:Any)->float|None:
    try:
        x=float(value)
    except Exception:
        return None
    return x if math.isfinite(x) else None


def dates_for_year(year:int)->list[date]:
    start=date(year,1,1); end=date(year+1,1,1)
    out=[]; current=start
    while current<end:
        out.append(current); current+=timedelta(days=1)
    return out


def extract_list_payload(payload:Any)->list[dict[str,Any]]|None:
    if isinstance(payload,list) and all(isinstance(row,dict) for row in payload):
        return payload
    return None


def request_json_list(url:str)->list[dict[str,Any]]|None:
    last_error=None
    for attempt in range(3):
        try:
            response=requests.get(url,timeout=120,headers={'User-Agent':'OrbitTrace-UKMON-v6-external/1.0'})
            if response.status_code==200:
                try:
                    rows=extract_list_payload(response.json())
                except Exception as exc:
                    last_error=f'JSON decode: {exc}'
                else:
                    if rows is not None:
                        return rows
                    last_error='non-list JSON payload'
            else:
                last_error=f'HTTP {response.status_code}'
        except Exception as exc:
            last_error=repr(exc)
        if attempt<2:
            time.sleep(1.0*(attempt+1))
    return None


def fetch_one_day(day:date)->dict[str,Any]:
    ymd=day.strftime('%Y%m%d')
    daily_url=DAILY_URL.format(yyyymmdd=ymd)
    rows=request_json_list(daily_url)
    fallback_used=False
    if rows is None:
        fallback_used=True
        rows=[]
        for period in PERIODS:
            url=daily_url+f'&period={period}'
            part=request_json_list(url)
            if part is None:
                raise RuntimeError(f'UKMON transport failed for {ymd} period {period}')
            rows.extend(part)
    return {'date':ymd,'rows':rows,'fallback_used':fallback_used}


def fetch_reserved_corpus(cache_root:Path)->tuple[dict[int,list[Path]],dict[str,Any]]:
    all_days=[day for year in YEARS for day in dates_for_year(year)]
    require(len(all_days)==731,'reserved calendar-day universe changed')
    cache_root.mkdir(parents=True,exist_ok=True)
    by_year={year:[] for year in YEARS}
    fallback_dates=[]; row_counts={}; completed=0

    def worker(day:date)->tuple[date,dict[str,Any]]:
        return day,fetch_one_day(day)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures={pool.submit(worker,day):day for day in all_days}
        results=[]
        for future in concurrent.futures.as_completed(futures):
            day=futures[future]
            payload=future.result()
            results.append((day,payload))
            completed+=1
            if completed%50==0 or completed==len(all_days):
                print(f'UKMON transport {completed}/{len(all_days)} dates',flush=True)

    for day,payload in sorted(results,key=lambda item:item[0]):
        ymd=payload['date']
        require(ymd==day.strftime('%Y%m%d'),'date payload identity changed')
        path=cache_root/f'{ymd}.json'
        path.write_text(json.dumps(payload['rows'],separators=(',',':'))+'\n',encoding='utf-8')
        by_year[day.year].append(path)
        row_counts[ymd]=len(payload['rows'])
        if payload['fallback_used']:
            fallback_dates.append(ymd)

    return by_year,{
        'dates_attempted':len(all_days),
        'dates_per_year':{str(year):len(by_year[year]) for year in YEARS},
        'fallback_dates':fallback_dates,
        'fallback_date_count':len(fallback_dates),
        'raw_summary_rows_per_year':{
            str(year):sum(row_counts[path.stem] for path in by_year[year]) for year in YEARS
        },
        'all_dates_materialized':all(len(by_year[year])==len(dates_for_year(year)) for year in YEARS),
    }


def stable_identity_hash(year:int,ymd:str,orbname:str)->int:
    payload=f'UKMON|{year}|{ymd}|{orbname}'.encode('utf-8')
    return int.from_bytes(hashlib.sha256(payload).digest(),'big',signed=False)


def parse_geometry_and_sample(year:int,paths:list[Path],base:Any)->tuple[list[dict[str,Any]],dict[str,Any]]:
    heaps={idx:[] for idx in range(36)}
    counts=Counter(); raw_rows=0; blind_removed=0; invalid_geometry=0
    seen_names=set(); duplicate_names=[]; eligible=0

    import heapq
    for path in sorted(paths):
        ymd=path.stem
        require(ymd.startswith(str(year)) and len(ymd)==8,f'wrong cached date for {year}: {ymd}')
        rows=json.loads(path.read_text())
        require(isinstance(rows,list) and all(isinstance(row,dict) for row in rows),f'{ymd} cache shape changed')
        for row in rows:
            raw_rows+=1
            orbname=str(row.get('orbname','')).strip()
            if not orbname:
                invalid_geometry+=1; continue
            # Solar longitude is the first scientific field interpreted.
            sol=finite(row.get('_sol'))
            if sol is None or not (0.0<=sol<360.0):
                invalid_geometry+=1; continue
            if BLIND_LOW<=sol<=BLIND_HIGH:
                blind_removed+=1; continue
            if orbname in seen_names:
                duplicate_names.append(orbname); continue
            seen_names.add(orbname)
            ra=finite(row.get('_ra_t')); dec=finite(row.get('_dc_t')); vg=finite(row.get('_vg'))
            if not (ra is not None and 0.0<=ra<360.0 and dec is not None and -90.0<=dec<=90.0 and vg is not None and 5.0<vg<75.0):
                invalid_geometry+=1; continue
            ecl_lon,ecl_lat=base.equatorial_to_ecliptic(ra,dec)
            event_id=f'UKMON|{year}|{ymd}|{orbname}'
            event={'id':event_id,'year':year,'sol':float(sol),'sun_lon':float(base.wrap180(float(ecl_lon)-float(sol))),'ecl_lat':float(ecl_lat),'vg':float(vg)}
            bin_index=int(sol//10.0)%36
            counts[bin_index]+=1; eligible+=1
            h=stable_identity_hash(year,ymd,orbname)
            item=(-h,event_id,event)
            heap=heaps[bin_index]
            if len(heap)<MAX_EVENTS_PER_BIN:
                heapq.heappush(heap,item)
            elif h < -heap[0][0]:
                heapq.heapreplace(heap,item)

    require(not duplicate_names,f'duplicate UKMON orbname within {year}: {duplicate_names[:5]}')
    events=[]; selected_by_bin={}
    for bin_index in range(36):
        chosen=[item[2] for item in heaps[bin_index]]
        chosen.sort(key=lambda event:str(event['id']))
        events.extend(chosen); selected_by_bin[str(bin_index)]=len(chosen)
    events.sort(key=lambda event:str(event['id']))
    return events,{
        'year':year,'raw_summary_rows':raw_rows,'blind_removed_before_radiant_speed':blind_removed,
        'invalid_geometry_rows':invalid_geometry,'duplicate_orbname_count':len(duplicate_names),
        'eligible_geometry_before_density_cap':eligible,
        'eligible_by_bin_before_cap':{str(k):int(v) for k,v in sorted(counts.items())},
        'selected_by_bin':selected_by_bin,'selected_events':len(events),'density_cap':MAX_EVENTS_PER_BIN,
        'density_selection':'10,000 smallest SHA256(UKMON|year|YYYYMMDD|orbname) per fixed 10-degree bin',
        'source_labels_read':False,'orbital_elements_interpreted':False,
    }


def parse_event_id(event_id:str)->tuple[int,str,str]:
    parts=event_id.split('|',3)
    require(len(parts)==4 and parts[0]=='UKMON',f'invalid UKMON event id: {event_id}')
    return int(parts[1]),parts[2],parts[3]


def read_orbits_after_rank_freeze(paths_by_year:dict[int,list[Path]],needed_ids:set[str])->tuple[dict[str,dict[str,float]],dict[str,Any]]:
    wanted={}
    for event_id in needed_ids:
        year,ymd,orbname=parse_event_id(event_id)
        wanted.setdefault((year,ymd),{})[orbname]=event_id
    path_lookup={(year,path.stem):path for year in YEARS for path in paths_by_year[year]}
    orbits={}; missing=0; target_guard_checks=0
    for key,rowmap in sorted(wanted.items()):
        path=path_lookup.get(key)
        require(path is not None,f'missing cached day for orbit reread: {key}')
        rows=json.loads(path.read_text())
        remaining=set(rowmap)
        for row in rows:
            orbname=str(row.get('orbname','')).strip()
            event_id=rowmap.get(orbname)
            if event_id is None: continue
            sol=finite(row.get('_sol')); target_guard_checks+=1
            require(sol is not None and not (BLIND_LOW<=sol<=BLIND_HIGH),f'target-range family event reached orbit reread: {event_id}')
            q=finite(row.get('_q')); e=finite(row.get('_e')); inc=finite(row.get('_incl')); peri=finite(row.get('_peri')); node=finite(row.get('_node'))
            if q is not None and q>0.0 and e is not None and e>=0.0 and inc is not None and 0.0<=inc<=180.0 and peri is not None and node is not None:
                orbits[event_id]={'q':float(q),'e':float(e),'i':float(inc),'arg':float(peri%360.0),'node':float(node%360.0)}
            remaining.discard(orbname)
        missing+=len(remaining)
    return orbits,{
        'needed_family_events':len(needed_ids),'valid_orbital_events':len(orbits),
        'invalid_or_missing_orbital_events':len(needed_ids)-len(orbits),'unmatched_orbname_count':missing,
        'target_guard_checks':target_guard_checks,'orbital_elements_interpreted_only_after_rank_freeze':True,
    }


def orbital_corroboration(families:list[dict[str,Any]],orbits:dict[str,dict[str,float]],dsh:Any)->tuple[dict[str,dict[str,Any]],dict[str,Any]]:
    rows={}; qualified=0; valid_fractions=[]
    for family in families:
        fid=str(family['family_id']); event_ids=[str(x) for x in family['event_ids']]
        valid_ids=[eid for eid in event_ids if eid in orbits]
        valid_fraction=len(valid_ids)/len(event_ids) if event_ids else 0.0; valid_fractions.append(valid_fraction)
        best=[]; best_counts={}
        if len(valid_ids)>=2:
            q=[orbits[eid]['q'] for eid in valid_ids]; e=[orbits[eid]['e'] for eid in valid_ids]
            inc=[orbits[eid]['i'] for eid in valid_ids]; peri=[orbits[eid]['arg'] for eid in valid_ids]; node=[orbits[eid]['node'] for eid in valid_ids]
            matrix=dsh.pairwise_dsh(q,e,inc,peri,node)
            forest=prior.UnionFind(len(valid_ids))
            ii,jj=np.where(np.triu(matrix<DSH_THRESHOLD,k=1))
            for left,right in zip(ii.tolist(),jj.tolist()): forest.union(int(left),int(right))
            groups={}
            for idx,eid in enumerate(valid_ids): groups.setdefault(forest.find(idx),[]).append(eid)
            candidates=[]
            for component in groups.values():
                yc=Counter(parse_event_id(eid)[0] for eid in component)
                if all(yc.get(year,0)>=MIN_YEAR_ORBIT_MEMBERS for year in YEARS):
                    precision=len(component)/len(event_ids) if event_ids else 0.0
                    candidates.append((precision,len(component),component,dict(yc)))
            if candidates:
                _prec,_size,best,best_counts=max(candidates,key=lambda item:(item[0],item[1],sorted(item[2])))
        precision=len(best)/len(event_ids) if event_ids else 0.0
        is_qualified=bool(best and precision>=MIN_ORBITAL_PRECISION and all(best_counts.get(year,0)>=MIN_YEAR_ORBIT_MEMBERS for year in YEARS))
        qualified+=int(is_qualified)
        rows[fid]={'family_id':fid,'family_event_count':len(event_ids),'valid_orbit_count':len(valid_ids),'valid_orbit_fraction':valid_fraction,'largest_cross_year_dsh_component':len(best),'component_year_counts':{str(year):int(best_counts.get(year,0)) for year in YEARS},'orbital_corroboration_precision':precision,'orbitally_corroborated':is_qualified,'dsh_threshold':DSH_THRESHOLD}
    return rows,{'family_count':len(families),'orbitally_corroborated_families':qualified,'median_valid_orbit_fraction':float(np.median(valid_fractions)) if valid_fractions else None,'minimum_valid_orbit_fraction':float(np.min(valid_fractions)) if valid_fractions else None}


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    v6_result=json.loads(args.v6_result_json.read_text())
    require(v6_result['verdict']=='PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT','v6 did not pass')
    require(all(v6_result['integrity_gates'].values()) and all(v6_result['scientific_gates'].values()),'v6 gates changed')
    require(v6_result['configuration']['max_quartets_per_bin']==512 and v6_result['configuration']['min_anchor_count']==2,'v6 proposal gates changed')
    require(v6_result['configuration']['first_shortlist']==64 and v6_result['configuration']['audit_shortlist']==128,'v6 shortlist changed')
    require(v6_result['configuration']['no_source_labels_in_proposal_generation'] is True,'v6 label-free boundary changed')

    freshness=json.loads(args.freshness_json.read_text())
    require(freshness['verdict']=='PASS_UKMON_2024_2025_REPO_SCIENTIFIC_FRESHNESS_AUDIT','UKMON freshness did not pass')
    require(freshness['potential_exposure_hit_count']==0,'UKMON reserved-year exposure appeared')
    interface=json.loads(args.interface_json.read_text())
    require(interface['verdict']=='PASS_UKMON_2022_LIVE_INTERFACE_DEVELOPMENT','UKMON live interface did not pass')
    require(interface['documented_example_date']=='2022-08-14' and interface['reserved_2024_2025_access'] is False,'interface reservation changed')
    require(all(interface['gates'].values()),'interface gate changed')

    require(all(mult.v3.self_test().values()),'multi-anchor v3 self-test failed')
    require(all(mult.brown.self_test().values()),'Brown self-test failed')
    runtime=mult.load_frozen_runtime(); support=runtime.load_support_module(args.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS='orbittrace-label-free-v6-ukmon-2024-2025-external'
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    require(float(support.BLIND_LOW)==BLIND_LOW and float(support.BLIND_HIGH)==BLIND_HIGH,'blind interval changed')
    require(int(support.MIN_FAMILY_YEARS)==2 and abs(float(support.FAMILY_LINK_RADIUS)-1.5)<1e-15,'family rules changed')
    require(int(support.MIN_COMPONENT_EVENTS)==4 and int(support.MIN_COMPONENT_QUARTETS)==2,'component gates changed')
    require(int(support.SHORTLIST_K)==64 and int(support.AUDIT_SHORTLIST_K)==128,'shortlists changed')
    require(int(support.MIN_ANCHOR_COUNT)==2 and int(support.MAX_QUARTETS_PER_BIN)==512,'proposal gates changed')
    setattr(args,'fixed4_baseline_json',args.v6_result_json)
    _candidate,base,_scorer=support.load_sources(args)
    require(abs(float(getattr(_candidate,'CANDIDATE_SCALE',4.0))-4.0)<1e-15,'candidate scale changed')
    dsh=prior.load_dsh_module(args.dsh_comparator)

    cache_root=args.output/'_ukmon_daily_cache'
    try:
        # FIRST RESERVED UKMON 2024/2025 DATA ACCESS occurs here after every method/gate above is frozen.
        paths_by_year,transport_audit=fetch_reserved_corpus(cache_root)
        require(transport_audit['dates_attempted']==731 and transport_audit['all_dates_materialized'],'calendar-date transport universe changed')

        scan_by_year={}; geometry_audits=[]
        for year in YEARS:
            events,audit=parse_geometry_and_sample(year,paths_by_year[year],base)
            scan_by_year[year]=events; geometry_audits.append(audit)
            print(f'UKMON {year}: raw={audit["raw_summary_rows"]} eligible={audit["eligible_geometry_before_density_cap"]} selected={audit["selected_events"]}',flush=True)

        components=[]; scan_audits=[]; retained_counts={}
        for year in YEARS:
            audit,passing,year_components=v6.label_free_scan_year(year,scan_by_year[year],support,base)
            scan_audits.append(audit); retained_counts[str(year)]=len(passing); components.extend(year_components)
            print(f'UKMON v6 {year}: quartets={len(passing)} components={len(year_components)}',flush=True)

        families,support_rankings=support.build_families(components,base)
        persistence_order=[str(value) for value in support_rankings['persistence']]
        family_ids=[str(family['family_id']) for family in families]
        require(set(persistence_order)==set(family_ids) and len(persistence_order)==len(family_ids),'persistence universe mismatch')

        mult.YEARS=YEARS; mult.TOP_K=TOP_K
        scored,scoring_summary=mult.score_families(families,scan_by_year,runtime,base)
        require(len(scored)==len(families),'not every recurrent family received score')
        rankings={'multiplicity':mult.rank_scored(scored,'multiplicity'),'brown':mult.rank_scored(scored,'brown'),'v3':mult.rank_scored(scored,'v3'),'label_free_persistence':persistence_order}
        require(all(set(order)==set(family_ids) for order in rankings.values()),'ranking universe changed')
        rankings_frozen_before_orbit_access=True

        # FIRST ORBITAL-ELEMENT INTERPRETATION: families/rankings already frozen.
        needed_ids={str(event_id) for family in families for event_id in family['event_ids']}
        orbits,orbit_read_audit=read_orbits_after_rank_freeze(paths_by_year,needed_ids)
        corroboration,orbital_summary=orbital_corroboration(families,orbits,dsh)
        metrics={name:prior.evaluate_ranking(order,corroboration) for name,order in rankings.items()}

        n=len(families); q=int(orbital_summary['orbitally_corroborated_families'])
        scannable=all(int(a['scannable_bin_count'])>=MIN_SCANNABLE_BINS for a in scan_audits)
        shortlist_exact=all(int(a['shortlist_audit_failures'])==0 for a in scan_audits)
        exact_years=all(sorted(int(y) for y in family['years'])==list(YEARS) for family in families)
        exact_episode_sizes=scoring_summary['episode_sizes']==[128] if families else False
        density_exact=all(all(int(value)<=MAX_EVENTS_PER_BIN for value in audit['selected_by_bin'].values()) and audit['density_cap']==MAX_EVENTS_PER_BIN for audit in geometry_audits)
        zero_labels=all(a['source_labels_read'] is False for a in geometry_audits) and all(a['source_labels_used_for_proposals'] is False for a in scan_audits)

        integrity_gates={
            'frozen_v6_freshness_interface_prerequisites':True,
            'exact_2024_2025_calendar_transport':transport_audit['dates_attempted']==731 and transport_audit['dates_per_year']=={'2024':366,'2025':365},
            'target_interval_removed_before_radiant_speed':all(a['blind_removed_before_radiant_speed']>=0 for a in geometry_audits),
            'zero_source_label_use':zero_labels,
            'rankings_frozen_before_orbital_interpretation':rankings_frozen_before_orbit_access and orbit_read_audit['orbital_elements_interpreted_only_after_rank_freeze'],
            'exact_10000_identity_hash_density_normalization':density_exact,
            'at_least_24_scannable_bins_each_year':scannable,
            'zero_shortlist_audit_mismatches':shortlist_exact,
            'all_recurrent_families_span_both_years':exact_years,
            'all_local_episode_sizes_exact_128':exact_episode_sizes,
            'brown_equivalence_within_1e_10':float(scoring_summary['max_brown_equivalence_difference'])<=BROWN_EQ_TOL,
            'at_least_100_recurrent_families':n>=MIN_FAMILIES,
            'at_least_30_orbitally_corroborated_families':q>=MIN_ORBITALLY_CORROBORATED,
        }
        m=int(metrics['multiplicity']['top_k_orbitally_corroborated']); b=int(metrics['brown']['top_k_orbitally_corroborated']); p=int(metrics['label_free_persistence']['top_k_orbitally_corroborated'])
        required_vs_persistence=int(math.ceil(0.90*p))
        scientific_gates={
            'multiplicity_topk_beats_brown_by_at_least_one':m>=b+1,
            'multiplicity_topk_at_least_90pct_persistence':m>=required_vs_persistence,
            'multiplicity_topk_hypergeometric_enrichment_p_le_005':float(metrics['multiplicity']['hypergeometric_enrichment_p'])<=0.05,
        }
        if not all(integrity_gates.values()):
            if not integrity_gates['at_least_100_recurrent_families'] or not integrity_gates['at_least_30_orbitally_corroborated_families']:
                verdict='INCONCLUSIVE_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_POWER'
            else:
                verdict='FAIL_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_INTEGRITY'
        elif all(scientific_gates.values()): verdict='PASS_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_VALIDATION'
        else: verdict='FAIL_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_VALIDATION'

        result={'verdict':verdict,'configuration':{'years':list(YEARS),'blind_exclusion':[BLIND_LOW,BLIND_HIGH],'daily_summary_route':DAILY_URL,'transport_period_fallback':list(PERIODS),'max_events_per_10deg_bin':MAX_EVENTS_PER_BIN,'density_selection':'smallest SHA256 of UKMON|year|YYYYMMDD|orbname','candidate_architecture':'frozen label-free sparse-support v6','primary_ranking':'worst-year multiplicity descending, geometric-mean multiplicity descending, family id','multiplicity':'(multi-anchor-v3-energy / Brown-peak)^2','orbital_validation':'largest cross-year D_SH<0.05 single-link component; >=4 events/year; >=0.50 family precision','top_k':TOP_K,'no_source_labels':True,'no_orbits_in_candidate_or_ranking':True,'scientific_gates_identical_to_saamer_external':True,'no_threshold_search':True,'no_density_search':True,'no_cap_search':True,'no_weight_search':True},'transport_audit':transport_audit,'geometry_audits':geometry_audits,'fixed4_scan_audits':scan_audits,'retained_quartet_counts':retained_counts,'family_count':n,'family_scoring_summary':scoring_summary,'orbit_read_audit':orbit_read_audit,'orbital_summary':orbital_summary,'metrics':metrics,'required_multiplicity_vs_persistence':required_vs_persistence,'integrity_gates':integrity_gates,'scientific_gates':scientific_gates,'claim_boundary':'One-shot external UKMON 2024-2025 validation of frozen label-free v6. UKMON 2024/2025 were reserved before any UKMON access; only 2022-08-14 was used for interface development. The 20-55 degree target interval was removed before radiant/speed interpretation; orbital elements were first interpreted after every discovery ranking was frozen. No OrbitTrace target information entered the run.'}
        (args.output/'ukmon_2024_2025_external_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        (args.output/'ukmon_2024_2025_rankings.json').write_text(json.dumps(rankings,indent=2)+'\n')
        (args.output/'ukmon_2024_2025_orbital_corroboration.json.gz').write_bytes(gzip.compress(json.dumps(corroboration,separators=(',',':')).encode()))
        (args.output/'ukmon_2024_2025_families.json.gz').write_bytes(gzip.compress(json.dumps(families,separators=(',',':')).encode()))
        (args.output/'ukmon_2024_2025_family_scores.json.gz').write_bytes(gzip.compress(json.dumps(scored,separators=(',',':')).encode()))
        k=min(TOP_K,n)
        lines=['# OrbitTrace label-free v6 UKMON 2024-2025 external validation','',f'Verdict: **`{verdict}`**','',f'- raw matched rows 2024/2025: **{transport_audit["raw_summary_rows_per_year"]["2024"]} / {transport_audit["raw_summary_rows_per_year"]["2025"]}**',f'- recurrent families: **{n}**',f'- orbitally corroborated families: **{q}**',f'- multiplicity top-{k} corroborated: **{m}**; enrichment p: **{metrics["multiplicity"]["hypergeometric_enrichment_p"]:.6g}**',f'- persistence top-{k}: **{p}**',f'- Brown top-{k}: **{b}**',f'- total-v3 top-{k}: **{metrics["v3"]["top_k_orbitally_corroborated"]}**',f'- daily transport fallback dates: **{transport_audit["fallback_date_count"]}**','', 'No source shower labels were used. Orbital elements were validation-only after ranking freeze.']
        (args.output/'UKMON_2024_2025_EXTERNAL_VALIDATION.md').write_text('\n'.join(lines)+'\n'); print('\n'.join(lines),flush=True)
        return 0
    finally:
        if cache_root.exists():
            for path in cache_root.iterdir(): path.unlink()
            cache_root.rmdir()

if __name__=='__main__': raise SystemExit(main())
