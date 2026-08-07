#!/usr/bin/env python3
"""Post-access AMOR parser diagnostic restricted to the first allowed field, LS."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import requests

YEARS=(1996,1998)
URLS={
    1996:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1996.zip',
    1998:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1998.zip',
}
SHA={
    1996:'d2444969fff5f99bd74f94b5742f07f36a6ce5dec040adf4832bf7e8ea116de1',
    1998:'f65a562d37d55d0d751d30213350dc333a3620717d3236436a35154e73c3f054',
}
MEMBER={1996:'amor1996.csv',1998:'amor1998.csv'}
HEADER=('DB','IC','Yr','Mn','Day','LS','RA','dRA','DECL','dDECL','Vg','Vh','q','e','a','i','arg','nod')
WIDTH17={1996:546,1998:371}
WIDTH18={1996:128665,1998:111789} # includes header


def require(c:bool,m:str)->None:
    if not c: raise RuntimeError(m)


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def direct_float(token:str)->float|None:
    try: value=float(token)
    except Exception: return None
    return value


def classify(token:str)->str:
    if re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',token): return 'decimal_or_scientific'
    if re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)[Dd][+-]?\d+',token): return 'fortran_D_exponent'
    if re.fullmatch(r'[+-]?\d+:\d+(?::\d+(?:\.\d*)?)?',token): return 'colon_sexagesimal_like'
    if re.fullmatch(r'[+-]?\d+(?:\.\d*)?[A-Za-z]+',token): return 'numeric_with_alpha_suffix'
    if re.fullmatch(r'[-+*.?]+',token): return 'missing_marker_like'
    return 'other'


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--structure-json',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    s=json.loads(args.structure_json.read_text())
    require(s['verdict']=='PASS_AMOR_1990_1999_STRUCTURE_AUDIT','structure audit failed')
    require(s['selected_years']==[1996,1998],'selected years changed')
    require(s['scientific_token_conversion_performed'] is False,'structure audit scientific boundary changed')
    by={int(a['year']):a for a in s['archives']}
    for year in YEARS:
        a=by[year]; m=a['members'][0]
        require(a['archive_sha256']==SHA[year],f'{year} SHA changed')
        require(m['name']==MEMBER[year],f'{year} member changed')
        require(m['delimiter_class']=='whitespace',f'{year} delimiter changed')
        require(m['header_tokens']==list(HEADER),f'{year} header changed')
        require(m['token_width_counts']=={'17':WIDTH17[year],'18':WIDTH18[year]},f'{year} widths changed')

    root=args.output/'_raw'; root.mkdir(exist_ok=True)
    results=[]
    try:
        for year in YEARS:
            path=root/f'amor{year}.zip'
            with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-AMOR-LS-format-diagnostic/1.0'}) as response:
                response.raise_for_status()
                with path.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):
                        if chunk: f.write(chunk)
            require(sha256(path)==SHA[year],f'{year} archive SHA mismatch')
            total_width18_data=0; direct_ok=0
            classes=Counter(); lengths=Counter(); charsets=Counter(); examples=[]; unique_examples=set()
            with zipfile.ZipFile(path) as zf, zf.open(MEMBER[year],'r') as fh:
                for physical_row,raw in enumerate(fh,start=1):
                    if not raw.strip(): continue
                    tokens=raw.strip().split()
                    if physical_row==1:
                        require(tuple(t.decode('utf-8','strict') for t in tokens)==HEADER,f'{year} header mismatch')
                        continue
                    if len(tokens)!=18: continue
                    total_width18_data += 1
                    # Sole scientific-value access in this diagnostic: token 5 (LS).
                    token=tokens[5].decode('ascii','replace')
                    if direct_float(token) is not None: direct_ok += 1
                    classes[classify(token)] += 1
                    lengths[len(token)] += 1
                    charsets[''.join(sorted(set(token)))] += 1
                    if token not in unique_examples and len(examples)<30:
                        unique_examples.add(token); examples.append(token)
            results.append({
                'year':year,
                'width18_data_rows':total_width18_data,
                'direct_float_success':direct_ok,
                'direct_float_failure':total_width18_data-direct_ok,
                'syntax_classes':dict(classes),
                'token_lengths':{str(k):v for k,v in sorted(lengths.items())},
                'character_set_patterns_top20':charsets.most_common(20),
                'first_30_unique_ls_tokens':examples,
                'fields_accessed':['LS'],
                'other_scientific_fields_interpreted':False,
            })
        result={
            'verdict':'PASS_AMOR_LS_FORMAT_DIAGNOSTIC',
            'selected_years':[1996,1998],
            'results':results,
            'fields_accessed':['LS'],
            'date_radiant_speed_orbit_access':False,
            'detector_family_ranking_access':False,
            'target_information_access':False,
            'claim_boundary':'Post-access parser diagnostic restricted to the first protocol-authorized AMOR scientific field LS. No date, radiant, speed, orbit, detector, family, ranking, or OrbitTrace target information was accessed.',
        }
        args.output.joinpath('amor_ls_format_diagnostic.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    finally:
        import shutil; shutil.rmtree(root,ignore_errors=True)

if __name__=='__main__': raise SystemExit(main())
