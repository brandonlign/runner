#!/usr/bin/env python3
"""AMOR parser diagnostic after the blind cut, restricted to Yr/Mn/RA/DECL/Vg syntax."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import requests

YEARS=(1996,1998)
URLS={1996:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1996.zip',1998:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1998.zip'}
SHA={1996:'d2444969fff5f99bd74f94b5742f07f36a6ce5dec040adf4832bf7e8ea116de1',1998:'f65a562d37d55d0d751d30213350dc333a3620717d3236436a35154e73c3f054'}
MEMBER={1996:'amor1996.csv',1998:'amor1998.csv'}
HEADER=('DB','IC','Yr','Mn','Day','LS','RA','dRA','DECL','dDECL','Vg','Vh','q','e','a','i','arg','nod')
FIELD_INDEX={'Yr':2,'Mn':3,'RA':6,'DECL':8,'Vg':10}
NUMERIC_CORE=re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$')
BLIND_LOW=20.0; BLIND_HIGH=55.0


def require(c:bool,m:str)->None:
    if not c: raise RuntimeError(m)


def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def strict_comma_decimal(token:bytes)->float|None:
    try: text=token.decode('ascii','strict')
    except Exception: return None
    if not text.endswith(',') or text.endswith(',,'): return None
    core=text[:-1]
    if not NUMERIC_CORE.fullmatch(core): return None
    try: value=float(core)
    except Exception: return None
    return value if math.isfinite(value) else None


def classify_raw(token:bytes)->str:
    try: text=token.decode('ascii','strict')
    except Exception: return 'non_ascii'
    if text.endswith(',') and not text.endswith(',,') and NUMERIC_CORE.fullmatch(text[:-1]): return 'decimal_plus_single_terminal_comma'
    if NUMERIC_CORE.fullmatch(text): return 'plain_decimal'
    if text.endswith(','): return 'other_terminal_comma'
    return 'other'


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--structure-json',required=True,type=Path); ap.add_argument('--ls-json',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    s=json.loads(args.structure_json.read_text()); lsdiag=json.loads(args.ls_json.read_text())
    require(s['verdict']=='PASS_AMOR_1990_1999_STRUCTURE_AUDIT' and s['selected_years']==[1996,1998],'structure prerequisite changed')
    require(s['scientific_token_conversion_performed'] is False and s['target_information_access'] is False,'structure boundary changed')
    require(lsdiag['verdict']=='PASS_AMOR_LS_FORMAT_DIAGNOSTIC','LS diagnostic did not pass')
    require(lsdiag['fields_accessed']==['LS'] and lsdiag['date_radiant_speed_orbit_access'] is False,'LS diagnostic boundary changed')
    require(lsdiag['target_information_access'] is False,'LS diagnostic target boundary changed')
    for row in lsdiag['results']:
        require(int(row['direct_float_success'])==0,'unexpected direct LS float success')
        require(int(row['direct_float_failure'])==int(row['width18_data_rows']),'LS diagnostic population changed')
        require(all(str(x).endswith(',') for x in row['first_30_unique_ls_tokens']),'LS examples do not support terminal-comma decoder')

    root=args.output/'_raw'; root.mkdir(exist_ok=True)
    out=[]
    try:
        for year in YEARS:
            path=root/f'amor{year}.zip'
            with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-AMOR-postblind-format-diagnostic/1.0'}) as response:
                response.raise_for_status()
                with path.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):
                        if chunk: f.write(chunk)
            require(file_sha(path)==SHA[year],f'{year} archive SHA changed')

            width18=0; ls_decode_fail=0; blind_removed=0; postblind=0
            stats={name:{'classes':Counter(),'examples':[],'seen':set()} for name in FIELD_INDEX}
            with zipfile.ZipFile(path) as zf, zf.open(MEMBER[year],'r') as fh:
                for physical_row,raw in enumerate(fh,start=1):
                    if not raw.strip(): continue
                    tokens=raw.strip().split()
                    if physical_row==1:
                        require(tuple(t.decode('utf-8','strict') for t in tokens)==HEADER,f'{year} header changed')
                        continue
                    if len(tokens)!=18: continue
                    width18 += 1

                    # First and only value conversion before the blind cut.
                    sol=strict_comma_decimal(tokens[5])
                    if sol is None or not (0.0 <= sol < 360.0):
                        ls_decode_fail += 1; continue
                    if BLIND_LOW <= sol <= BLIND_HIGH:
                        blind_removed += 1; continue

                    postblind += 1
                    # Outside the blind interval only: syntax inspection, no numeric conversion.
                    for name,idx in FIELD_INDEX.items():
                        token=tokens[idx]
                        text=token.decode('ascii','replace')
                        stats[name]['classes'][classify_raw(token)] += 1
                        if text not in stats[name]['seen'] and len(stats[name]['examples'])<20:
                            stats[name]['seen'].add(text); stats[name]['examples'].append(text)

            require(width18>0 and ls_decode_fail==0,f'{year} source-proven LS decoder failed on {ls_decode_fail}/{width18}')
            require(postblind>0,f'{year} no post-blind rows')
            field_results={}
            for name in FIELD_INDEX:
                classes=dict(stats[name]['classes'])
                field_results[name]={
                    'syntax_classes':classes,
                    'first_20_unique_tokens':stats[name]['examples'],
                    'all_postblind_tokens_decimal_plus_single_terminal_comma':classes=={'decimal_plus_single_terminal_comma':postblind},
                    'numeric_conversion_performed':False,
                }
            out.append({
                'year':year,'width18_rows':width18,'ls_decode_fail':ls_decode_fail,
                'blind_removed_before_geometry_or_date_syntax':blind_removed,'postblind_rows_inspected':postblind,
                'field_results':field_results,
            })

        result={
            'verdict':'PASS_AMOR_POSTBLIND_GEOMETRY_FORMAT_DIAGNOSTIC',
            'selected_years':[1996,1998],
            'ls_decoder':'strict decimal core plus exactly one terminal comma',
            'blind_exclusion':[20.0,55.0],
            'postblind_fields_syntax_inspected':['Yr','Mn','RA','DECL','Vg'],
            'results':out,
            'orbit_fields_accessed':False,
            'detector_family_ranking_access':False,
            'target_information_access':False,
            'claim_boundary':'LS alone was numerically decoded first; 20-55 was removed immediately. Only outside that interval were Yr/Mn/RA/DECL/Vg token syntaxes inspected, without numeric conversion. No orbit, detector, family, ranking, or OrbitTrace target information was accessed.',
        }
        args.output.joinpath('amor_postblind_geometry_format_diagnostic.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    finally:
        shutil.rmtree(root,ignore_errors=True)

if __name__=='__main__': raise SystemExit(main())
