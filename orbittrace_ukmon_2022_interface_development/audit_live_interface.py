#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import requests

URL='https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval=20220814'
REQUIRED=('orbname','_sol','_ra_t','_dc_t','_vg','_q','_e','_incl','_peri','_node')
BLIND_LOW=20.0; BLIND_HIGH=55.0

def finite(v):
    try: x=float(v)
    except Exception: return None
    return x if math.isfinite(x) else None

def extract_rows(payload):
    if isinstance(payload,list) and all(isinstance(x,dict) for x in payload): return payload,'top_level_list'
    if isinstance(payload,dict):
        for key in ('data','results','matches','summary'):
            value=payload.get(key)
            if isinstance(value,list) and all(isinstance(x,dict) for x in value): return value,f'dict_list:{key}'
        if payload and all(isinstance(v,dict) for v in payload.values()):
            rows=[]
            for key,value in payload.items():
                row=dict(value); row.setdefault('orbname',str(key)); rows.append(row)
            return rows,'dict_of_records'
    raise RuntimeError(f'unrecognized summary JSON structure: {type(payload).__name__}')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--interface-json',required=True,type=Path); p.add_argument('--freshness-json',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    iface=json.loads(a.interface_json.read_text()); fresh=json.loads(a.freshness_json.read_text())
    if iface['verdict']!='PASS_UKMON_DOCUMENTED_INTERFACE_ADJUDICATION': raise RuntimeError('interface docs prerequisite failed')
    if fresh['verdict']!='PASS_UKMON_2024_2025_REPO_SCIENTIFIC_FRESHNESS_AUDIT': raise RuntimeError('freshness prerequisite failed')
    if fresh['potential_exposure_hit_count']!=0: raise RuntimeError('reserved-year exposure appeared')

    response=requests.get(URL,timeout=120,headers={'User-Agent':'OrbitTrace-UKMON-interface-audit/1.0'})
    response.raise_for_status(); payload=response.json(); rows,shape=extract_rows(payload)
    if len(rows)<5: raise RuntimeError(f'too few documented-date rows: {len(rows)}')

    # First scientific inspection per row is solar longitude. Blind-range rows kill the audit
    # before any radiant/speed/orbit field is converted.
    sols=[]
    for index,row in enumerate(rows):
        sol=finite(row.get('_sol'))
        if sol is None: continue
        if BLIND_LOW <= sol <= BLIND_HIGH:
            raise RuntimeError(f'blind-range row appeared at response index {index}; no later fields inspected')
        sols.append(sol)

    n=len(rows)
    presence={key:sum(key in row and row.get(key) not in (None,'') for row in rows) for key in REQUIRED}
    if any(presence[key]/n < .95 for key in REQUIRED): raise RuntimeError(f'required-key completeness below 95%: {presence}')
    names=[str(row['orbname']).strip() for row in rows]
    if any(not x for x in names) or len(set(names))!=len(names): raise RuntimeError('orbname missing or nonunique')

    fields={key:[finite(row.get(key)) for row in rows] for key in REQUIRED if key!='orbname'}
    finite_counts={key:sum(v is not None for v in vals) for key,vals in fields.items()}
    for key in ('_sol','_ra_t','_dc_t','_vg'):
        if finite_counts[key]/n < .95: raise RuntimeError(f'{key} finite fraction below 95%')
    for key in ('_q','_e','_incl','_peri','_node'):
        if finite_counts[key]/n < .80: raise RuntimeError(f'{key} finite fraction below 80%')

    def valid_fraction(key,pred):
        vals=[v for v in fields[key] if v is not None]
        return sum(pred(v) for v in vals)/len(vals) if vals else 0.0
    gates={
      'rows_at_least_5':n>=5,
      'all_required_keys_95pct':all(presence[k]/n>=.95 for k in REQUIRED),
      'orbname_unique_nonempty':len(set(names))==n and all(names),
      'sol_range':valid_fraction('_sol',lambda x:0<=x<360)>=.95,
      'ra_range':valid_fraction('_ra_t',lambda x:0<=x<360)>=.95,
      'dec_range':valid_fraction('_dc_t',lambda x:-90<=x<=90)>=.95,
      'vg_kms_range':valid_fraction('_vg',lambda x:5<x<75)>=.95,
      'orbit_q_positive':valid_fraction('_q',lambda x:x>0)>=.95,
      'orbit_e_nonnegative':valid_fraction('_e',lambda x:x>=0)>=.95,
      'incl_range':valid_fraction('_incl',lambda x:0<=x<=180)>=.95,
      'blind_interval_absent':all(not (BLIND_LOW<=x<=BLIND_HIGH) for x in sols),
    }
    verdict='PASS_UKMON_2022_LIVE_INTERFACE_DEVELOPMENT' if all(gates.values()) else 'FAIL_UKMON_2022_LIVE_INTERFACE_DEVELOPMENT'
    ranges={key:{'min':min(v for v in vals if v is not None),'max':max(v for v in vals if v is not None)} for key,vals in fields.items() if any(v is not None for v in vals)}
    result={'verdict':verdict,'url':URL,'documented_example_date':'2022-08-14','response_shape':shape,'row_count':n,'required_key_presence':presence,'finite_counts':finite_counts,'numeric_ranges':ranges,'gates':gates,'reserved_2024_2025_access':False,'orbittrace_target_information_access':False,'method_evaluation_performed':False,'claim_boundary':'Live parser/interface development on the UKMON-documented 2022-08-14 example date only. Reserved 2024/2025 years were not requested; no v6 method result was computed.'}
    (a.output/'ukmon_2022_live_interface_development.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
if __name__=='__main__': main()
