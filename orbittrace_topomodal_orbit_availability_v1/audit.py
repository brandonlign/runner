#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from gmn_python_api import data_directory as dd

YEARS=(2022,2023)
MONTHS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
DENOMS=(128,1024)
BUCKETS=(0,1,2,3)
EXPECTED={(128,0):5567,(128,1):5840,(128,2):5857,(128,3):5816,(1024,0):677,(1024,1):739,(1024,2):736,(1024,3):766}


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def clean(x:str)->str:
    return " ".join(x.replace("#","").strip().split())

def parse_float(raw:str)->float|None:
    s=raw.strip()
    if s in {"","...","nan","NaN","None"}: return None
    try: x=float(s)
    except Exception: return None
    return x if math.isfinite(x) else None

def columns(text:str)->tuple[dict[str,int],list[str]]:
    lines=text.splitlines()
    top=next((ln for ln in lines if ln.lstrip().startswith('#') and 'Unique trajectory' in ln and 'Sol lon' in ln and 'Participating' in ln),None)
    bottom=next((ln for ln in lines if ln.lstrip().startswith('#') and 'identifier' in ln and 'stat' in ln and 'stations' in ln),None)
    req(top is not None and bottom is not None,'GMN monthly two-row schema header not found')
    a=[clean(x) for x in top.split(';')]; b=[clean(x) for x in bottom.split(';')]
    req(len(a)==len(b) and len(a)>70,f'unexpected header width {len(a)} vs {len(b)}')
    def one(t:str,u:str)->int:
        hits=[i for i,(x,y) in enumerate(zip(a,b)) if x==t and y==u]
        req(len(hits)==1,f'header field {(t,u)} not unique: {hits}')
        return hits[0]
    out={
        'id':one('Unique trajectory','identifier'),
        'sol':one('Sol lon','deg'),
        'e':one('e',''),
        'i':one('i','deg'),
        'peri':one('peri','deg'),
        'node':one('node','deg'),
        'q':one('q','AU'),
    }
    return out,lines

def parse_month(text:str,month:str,allowed_month:dict[str,str])->list[tuple[str,float,tuple[float|None,...]]]:
    c,lines=columns(text); out=[]
    mx=max(c.values())
    for line in lines:
        s=line.strip()
        if not s or s.startswith('#'): continue
        cells=[x.strip() for x in line.split(';')]
        req(c['id']<len(cells),f'short ID row {month}')
        eid=cells[c['id']]
        # No non-manifest scientific fields are parsed.
        if allowed_month.get(eid)!=month: continue
        req(mx<len(cells),f'short manifest row {month}: {eid}')
        req(re.fullmatch(r'[A-Za-z0-9_]+',eid) is not None,f'unsafe event id {eid!r}')
        sol=parse_float(cells[c['sol']]); req(sol is not None and 0.0<=sol<=360.0,f'invalid solar longitude {eid}')
        req(not(BLIND[0]<=sol<=BLIND[1]),f'protected event entered orbit manifest {eid}')
        vals=tuple(parse_float(cells[c[k]]) for k in ('e','q','i','peri','node'))
        out.append((eid,sol,vals))
    return out

def usable(v:tuple[float|None,...])->bool:
    e,q,i,peri,node=v
    return bool(e is not None and q is not None and i is not None and peri is not None and node is not None and e>=0.0 and q>=0.0 and 0.0<=i<=180.0)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--universe-manifest',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    raw=a.universe_manifest.read_bytes(); msha=hashlib.sha256(raw).hexdigest(); m=json.loads(raw)
    req(m['schema']=='ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1','manifest schema')
    req(m['years']==[2022,2023] and m['blind_exclusion']==[20.0,55.0],'manifest firewall')
    req(m['num_stat_accessed'] is False and m['shower_label_accessed'] is False,'manifest forbidden access')
    subset={(d,b):list(m['subsets'][f'd{d}_b{b}']) for d in DENOMS for b in BUCKETS}
    for k,ids in subset.items(): req(len(ids)==EXPECTED[k],f'subset count changed {k}')
    union=list(m['audited_union_ids']); req(len(union)==23080 and len(set(union))==23080,'union count/duplicate')
    monthmap={str(k):str(v) for k,v in m['audited_union_authoritative_month'].items()}; req(set(monthmap)==set(union),'month map')
    rows={}; month_sha={}
    for month in MONTHS:
        print(f'[orbit-availability] fetch {month}',flush=True)
        text=dd.get_monthly_file_content_by_date(month); month_sha[month]=hashlib.sha256(text.encode()).hexdigest()
        req(month_sha[month]==m['source_sha256'][month],f'monthly source changed {month}')
        for eid,sol,vals in parse_month(text,month,monthmap):
            req(eid not in rows,f'duplicate manifest ID {eid}'); rows[eid]=(int(eid[:4]),vals)
    req(set(rows)==set(union),f'orbit join coverage mismatch {len(rows)} of {len(union)}')
    year_stats={}
    for y in YEARS:
        ids=[eid for eid in union if rows[eid][0]==y]; good=[eid for eid in ids if usable(rows[eid][1])]
        year_stats[str(y)]={'requested':len(ids),'usable':len(good),'complete_fraction':len(good)/len(ids),'all_events_usable':len(good)==len(ids)}
    subset_stats={}
    for d in DENOMS:
        for b in BUCKETS:
            ids=subset[(d,b)]; good=[eid for eid in ids if usable(rows[eid][1])]
            subset_stats[f'd{d}_b{b}']={'requested':len(ids),'usable':len(good),'complete_fraction':len(good)/len(ids),'all_events_usable':len(good)==len(ids)}
    all_complete=all(x['all_events_usable'] for x in subset_stats.values()) and all(x['all_events_usable'] for x in year_stats.values())
    mapping={}
    for eid in union:
        vals=rows[eid][1]
        mapping[eid]=({'e':vals[0],'q_au':vals[1],'i_deg':vals[2],'peri_deg':vals[3]%360.0,'node_deg':vals[4]%360.0} if usable(vals) else None)
    mapraw=(json.dumps(mapping,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode(); mapsha=hashlib.sha256(mapraw).hexdigest()
    verdict='PASS_TOPOMODAL_ORBIT_AVAILABILITY_V1' if all_complete else 'FAIL_TOPOMODAL_ORBIT_AVAILABILITY_V1'
    result={
      'schema':'ORBITTRACE_TOPOMODAL_ORBIT_AVAILABILITY_V1','verdict':verdict,'years':[2022,2023],'blind_exclusion':[20.0,55.0],
      'activation_requires_complete_fraction':1.0,'expected_subset_counts':{f'd{d}_b{b}':EXPECTED[(d,b)] for d in DENOMS for b in BUCKETS},
      'audited_union_count':len(union),'year_stats':year_stats,'subset_stats':subset_stats,'orbit_mapping_sha256':mapsha,'universe_manifest_sha256':msha,'monthly_raw_sha256':month_sha,
      'fields_parsed':['unique_trajectory_identifier','sol_lon_deg','e','q_au','i_deg','peri_deg','node_deg'],
      'iau_number_parsed':False,'iau_code_parsed':False,'shower_truth_parsed':False,'orbit_fields_parsed_only_for_manifest_ids':True,
      'target_information_access':False,'target_region_orbit_emitted_or_used':False,'candidate_ranking_computed':False,'d_sh_computed':False,
      'sonotaco_scientific_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
      'post_result_parameter_search':False
    }
    (a.output/'TOPOMODAL_ORBIT_AVAILABILITY_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (a.output/'audited_union_orbit_mapping.json').write_bytes(mapraw)
    print(json.dumps({'verdict':verdict,'year_stats':year_stats,'subset_stats':subset_stats,'orbit_mapping_sha256':mapsha,'universe_manifest_sha256':msha},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
