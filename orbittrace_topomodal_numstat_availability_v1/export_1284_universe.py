#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from gmn_python_api import data_directory as dd

YEARS=(2022,2023)
MONTHS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
SALT="ORBITTRACE_SCALE_STRESS_V1|"
EXPECTED={(128,0):5567,(128,1):5840,(128,2):5857,(128,3):5816,(1024,0):677,(1024,1):739,(1024,2):736,(1024,3):766}


def req(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def clean(x:str)->str:
    return " ".join(x.replace("#","").strip().split())


def header_indices(text:str)->tuple[int,int,int,int,int,list[str]]:
    lines=text.splitlines()
    top=next((ln for ln in lines if ln.lstrip().startswith('#') and 'Unique trajectory' in ln and 'Sol lon' in ln and 'LAMgeo' in ln and 'BETgeo' in ln and 'Vgeo' in ln),None)
    bottom=next((ln for ln in lines if ln.lstrip().startswith('#') and 'identifier' in ln and 'km/s' in ln),None)
    req(top is not None and bottom is not None,'GMN two-row schema header not found')
    a=[clean(x) for x in top.split(';')]; b=[clean(x) for x in bottom.split(';')]
    req(len(a)==len(b) and len(a)>70,'unexpected header width')
    def one(t:str,u:str)->int:
        hits=[i for i,(x,y) in enumerate(zip(a,b)) if x==t and y==u]
        req(len(hits)==1,f'header field {(t,u)} not unique: {hits}')
        return hits[0]
    return one('Unique trajectory','identifier'),one('Sol lon','deg'),one('LAMgeo','deg'),one('BETgeo','deg'),one('Vgeo','km/s'),lines


def fnum(s:str)->float:
    try:return float(s)
    except Exception:return float('nan')


def h64(eid:str)->int:
    return int.from_bytes(hashlib.sha256((SALT+eid).encode()).digest()[:8],'big')


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    seen=set(); selected=[]; selected_month={}; source_sha={}; monthly_counts={}
    for month in MONTHS:
        print(f'[universe] fetch {month}',flush=True)
        text=dd.get_monthly_file_content_by_date(month)
        source_sha[month]=hashlib.sha256(text.encode()).hexdigest()
        ci,cs,cl,cb,cv,lines=header_indices(text)
        raw=0; valid_count=0; dup=0
        for line in lines:
            s=line.strip()
            if not s or s.startswith('#'): continue
            raw+=1; cells=[x.strip() for x in line.split(';')]
            req(max(ci,cs,cl,cb,cv)<len(cells),f'short row {month}')
            eid=cells[ci]; sol=fnum(cells[cs]); lam=fnum(cells[cl]); bet=fnum(cells[cb]); vg=fnum(cells[cv])
            valid=all(map(math.isfinite,(sol,lam,bet,vg))) and 0.0<=sol<=360.0 and 0.0<=lam<=360.0 and -90.0<=bet<=90.0 and 5.0<=vg<=75.0 and not (BLIND[0]<=sol<=BLIND[1])
            if not valid: continue
            if eid in seen:
                dup+=1; continue
            seen.add(eid); valid_count+=1; selected.append(eid); selected_month[eid]=month
        monthly_counts[month]={'raw_rows':raw,'selected_rows_after_exact_1284_validity_and_blind':valid_count,'duplicate_rows_removed':dup}
    req(len(selected)==len(set(selected)),'duplicate selected IDs')
    subsets={}
    for d in (128,1024):
        for b in range(4):
            ids=sorted(e for e in selected if h64(e)%d==b)
            req(len(ids)==EXPECTED[(d,b)],f'exact #1284 subset mismatch d={d} b={b}: {len(ids)} != {EXPECTED[(d,b)]}')
            subsets[f'd{d}_b{b}']=ids
    union=sorted(set().union(*(set(subsets[f'd128_b{b}']) for b in range(4))))
    union_month={eid:selected_month[eid] for eid in union}
    manifest={'schema':'ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1','years':[2022,2023],'blind_exclusion':[20.0,55.0],'selection':'exact_frozen_1284_scan_geometry_validity_blind_duplicate_rules','expected_counts':{f'd{d}_b{b}':EXPECTED[(d,b)] for d in (128,1024) for b in range(4)},'subsets':subsets,'audited_union_ids':union,'audited_union_authoritative_month':union_month,'source_sha256':source_sha,'monthly_counts':monthly_counts,'num_stat_accessed':False,'shower_label_accessed':False,'station_identity_accessed':False,'station_geography_accessed':False,'geometry_values_emitted':False,'target_information_access':False}
    raw=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode(); sha=hashlib.sha256(raw).hexdigest(); (a.output/'EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1.json').write_bytes(raw); (a.output/'universe_manifest_sha256.txt').write_text(sha+'\n')
    print(json.dumps({'manifest_sha256':sha,'union_count':len(union),'counts':manifest['expected_counts']},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
