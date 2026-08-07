#!/usr/bin/env python3
"""Identify only AMOR LS tokens that violate the strict terminal-comma decimal grammar."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

import requests

YEARS=(1996,1998)
URLS={1996:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1996.zip',1998:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1998.zip'}
SHA={1996:'d2444969fff5f99bd74f94b5742f07f36a6ce5dec040adf4832bf7e8ea116de1',1998:'f65a562d37d55d0d751d30213350dc333a3620717d3236436a35154e73c3f054'}
MEMBER={1996:'amor1996.csv',1998:'amor1998.csv'}
HEADER=('DB','IC','Yr','Mn','Day','LS','RA','dRA','DECL','dDECL','Vg','Vh','q','e','a','i','arg','nod')
NUMERIC_CORE=re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$')


def require(c:bool,m:str)->None:
    if not c: raise RuntimeError(m)


def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def strict_ls_matches(token:bytes)->bool:
    try: text=token.decode('ascii','strict')
    except Exception: return False
    return text.endswith(',') and not text.endswith(',,') and bool(NUMERIC_CORE.fullmatch(text[:-1]))


def classify(text:str)->str:
    if text in {',','.,','*,','**,','?,'}: return 'missing_marker_like_terminal_comma'
    if text.endswith(',') and NUMERIC_CORE.fullmatch(text[:-1]): return 'valid_decimal_terminal_comma'
    if text.endswith(','): return 'other_terminal_comma'
    if NUMERIC_CORE.fullmatch(text): return 'decimal_missing_terminal_comma'
    return 'other'


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--structure-json',required=True,type=Path); ap.add_argument('--ls-json',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    s=json.loads(args.structure_json.read_text()); l=json.loads(args.ls_json.read_text())
    require(s['verdict']=='PASS_AMOR_1990_1999_STRUCTURE_AUDIT' and s['selected_years']==[1996,1998],'structure prerequisite changed')
    require(l['verdict']=='PASS_AMOR_LS_FORMAT_DIAGNOSTIC' and l['fields_accessed']==['LS'],'LS prerequisite changed')
    require(l['date_radiant_speed_orbit_access'] is False and l['detector_family_ranking_access'] is False and l['target_information_access'] is False,'LS prerequisite boundary changed')

    root=args.output/'_raw'; root.mkdir(exist_ok=True)
    results=[]
    try:
        for year in YEARS:
            path=root/f'amor{year}.zip'
            with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-AMOR-LS-anomaly-diagnostic/1.0'}) as response:
                response.raise_for_status()
                with path.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):
                        if chunk: f.write(chunk)
            require(file_sha(path)==SHA[year],f'{year} archive SHA changed')
            width18=0; anomalies=[]
            with zipfile.ZipFile(path) as zf, zf.open(MEMBER[year],'r') as fh:
                for physical_row,raw in enumerate(fh,start=1):
                    if not raw.strip(): continue
                    tokens=raw.strip().split()
                    if physical_row==1:
                        require(tuple(t.decode('utf-8','strict') for t in tokens)==HEADER,f'{year} header changed')
                        continue
                    if len(tokens)!=18: continue
                    width18 += 1
                    token=tokens[5]
                    if strict_ls_matches(token): continue
                    text=token.decode('ascii','replace')
                    anomalies.append({
                        'physical_row':physical_row,
                        'ls_token':text,
                        'syntax_class':classify(text),
                        'token_length':len(text),
                        'character_codes':[ord(ch) for ch in text],
                    })
            results.append({'year':year,'width18_rows':width18,'strict_ls_match_rows':width18-len(anomalies),'anomaly_count':len(anomalies),'anomalies':anomalies})

        result={
            'verdict':'PASS_AMOR_LS_ANOMALY_DIAGNOSTIC',
            'selected_years':[1996,1998],
            'fields_accessed':['LS'],
            'results':results,
            'date_radiant_speed_orbit_access':False,
            'detector_family_ranking_access':False,
            'target_information_access':False,
            'claim_boundary':'Only nonconforming LS tokens and their physical row numbers were identified. No other AMOR field, detector result, family, ranking, orbit, or OrbitTrace target information was accessed.',
        }
        args.output.joinpath('amor_ls_anomaly_diagnostic.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    finally:
        shutil.rmtree(root,ignore_errors=True)

if __name__=='__main__': raise SystemExit(main())
