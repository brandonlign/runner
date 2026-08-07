#!/usr/bin/env python3
"""Corrected staged AMOR diagnostic: LS grammar/range first, then post-blind geometry syntax."""
from __future__ import annotations

import argparse, hashlib, json, math, re, shutil, zipfile
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

def require(c,m):
    if not c: raise RuntimeError(m)

def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def strict_comma_decimal(token):
    try: text=token.decode('ascii','strict')
    except Exception: return None
    if not text.endswith(',') or text.endswith(',,'): return None
    core=text[:-1]
    if not NUMERIC_CORE.fullmatch(core): return None
    try: value=float(core)
    except Exception: return None
    return value if math.isfinite(value) else None

def classify_raw(token):
    try: text=token.decode('ascii','strict')
    except Exception: return 'non_ascii'
    if text.endswith(',') and not text.endswith(',,') and NUMERIC_CORE.fullmatch(text[:-1]): return 'decimal_plus_single_terminal_comma'
    if NUMERIC_CORE.fullmatch(text): return 'plain_decimal'
    if text.endswith(','): return 'other_terminal_comma'
    return 'other'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--structure-json',required=True,type=Path); ap.add_argument('--ls-json',required=True,type=Path); ap.add_argument('--ls-anomaly-json',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    s=json.loads(args.structure_json.read_text()); l=json.loads(args.ls_json.read_text()); a=json.loads(args.ls_anomaly_json.read_text())
    require(s['verdict']=='PASS_AMOR_1990_1999_STRUCTURE_AUDIT' and s['selected_years']==[1996,1998],'structure prerequisite changed')
    require(l['verdict']=='PASS_AMOR_LS_FORMAT_DIAGNOSTIC' and l['fields_accessed']==['LS'],'LS prerequisite changed')
    require(a['verdict']=='PASS_AMOR_LS_ANOMALY_DIAGNOSTIC' and a['fields_accessed']==['LS'],'LS anomaly prerequisite changed')
    require(all(int(x['anomaly_count'])==0 for x in a['results']),'LS grammar anomalies remain')
    require(l['date_radiant_speed_orbit_access'] is False and a['date_radiant_speed_orbit_access'] is False,'prior boundary changed')
    require(l['target_information_access'] is False and a['target_information_access'] is False,'prior target boundary changed')

    root=args.output/'_raw'; root.mkdir(exist_ok=True); results=[]
    try:
        for year in YEARS:
            path=root/f'amor{year}.zip'
            with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-AMOR-postblind-format-diagnostic-v2/1.0'}) as response:
                response.raise_for_status()
                with path.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):
                        if chunk: f.write(chunk)
            require(file_sha(path)==SHA[year],f'{year} archive SHA changed')
            width18=0; ls_grammar_fail=0; ls_range_invalid=0; blind_removed=0; postblind=0; range_invalid_examples=[]
            stats={name:{'classes':Counter(),'examples':[],'seen':set()} for name in FIELD_INDEX}
            with zipfile.ZipFile(path) as zf, zf.open(MEMBER[year],'r') as fh:
                for physical_row,raw in enumerate(fh,start=1):
                    if not raw.strip(): continue
                    tokens=raw.strip().split()
                    if physical_row==1:
                        require(tuple(t.decode('utf-8','strict') for t in tokens)==HEADER,f'{year} header changed'); continue
                    if len(tokens)!=18: continue
                    width18 += 1
                    sol=strict_comma_decimal(tokens[5])
                    if sol is None:
                        ls_grammar_fail += 1; continue
                    if not (0.0 <= sol < 360.0):
                        ls_range_invalid += 1
                        if len(range_invalid_examples)<10: range_invalid_examples.append({'physical_row':physical_row,'ls':sol})
                        continue
                    if BLIND_LOW <= sol <= BLIND_HIGH:
                        blind_removed += 1; continue
                    postblind += 1
                    for name,idx in FIELD_INDEX.items():
                        token=tokens[idx]; text=token.decode('ascii','replace'); stats[name]['classes'][classify_raw(token)] += 1
                        if text not in stats[name]['seen'] and len(stats[name]['examples'])<20:
                            stats[name]['seen'].add(text); stats[name]['examples'].append(text)
            require(width18>0 and ls_grammar_fail==0,f'{year} LS grammar failure {ls_grammar_fail}/{width18}')
            require(postblind>0,f'{year} no post-blind rows')
            field_results={}
            for name in FIELD_INDEX:
                classes=dict(stats[name]['classes'])
                field_results[name]={'syntax_classes':classes,'first_20_unique_tokens':stats[name]['examples'],'all_postblind_tokens_decimal_plus_single_terminal_comma':classes=={'decimal_plus_single_terminal_comma':postblind},'numeric_conversion_performed':False}
            results.append({'year':year,'width18_rows':width18,'ls_grammar_fail':ls_grammar_fail,'ls_range_invalid':ls_range_invalid,'ls_range_invalid_examples':range_invalid_examples,'blind_removed_before_geometry_or_date_syntax':blind_removed,'postblind_rows_inspected':postblind,'field_results':field_results})
        result={'verdict':'PASS_AMOR_POSTBLIND_GEOMETRY_FORMAT_DIAGNOSTIC_V2','selected_years':[1996,1998],'ls_decoder':'strict decimal core plus exactly one terminal comma','ls_range_rule':'drop if not 0<=LS<360 before any other field','blind_exclusion':[20.0,55.0],'postblind_fields_syntax_inspected':['Yr','Mn','RA','DECL','Vg'],'results':results,'orbit_fields_accessed':False,'detector_family_ranking_access':False,'target_information_access':False,'claim_boundary':'LS alone was numerically decoded first. Range-invalid LS rows were discarded, then 20-55 was removed. Only afterward were Yr/Mn/RA/DECL/Vg token syntaxes inspected without numeric conversion. No orbit, detector, family, ranking, or OrbitTrace target information was accessed.'}
        args.output.joinpath('amor_postblind_geometry_format_diagnostic_v2.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True)); return 0
    finally: shutil.rmtree(root,ignore_errors=True)
if __name__=='__main__': raise SystemExit(main())
