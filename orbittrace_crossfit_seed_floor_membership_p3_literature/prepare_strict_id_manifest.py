#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,json,re
from pathlib import Path
from typing import Any
YEARS=(2023,2025); BLIND_EXCLUSION=(20.0,55.0)
HDBSCAN_SHA256={2023:'35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',2025:'8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'}
SUGAR_SHA256={2023:'2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',2025:'77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e'}
EXPECTED_COUNTS={'hdbscan':{2023:26460,2025:19658},'sugar':{2023:30414,2025:23200}}
def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)
def sha256_file(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_sha(value:Any)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def hdbscan_ids_only(path:Path,year:int)->list[str]:
    require(sha256_file(path)==HDBSCAN_SHA256[year],f'HDBSCAN {year} artifact hash changed')
    lines=gzip.decompress(path.read_bytes()).decode().splitlines(); pattern=re.compile(r'"(?:event_id|id)"\s*:\s*"(SNM'+str(year)+r':\d+)"'); out=[]
    for n,line in enumerate(lines,1):
        hits=pattern.findall(line); require(len(hits)==1,f'HDBSCAN {year} event-id token not unique line {n}'); out.append(hits[0])
    require(len(out)==EXPECTED_COUNTS['hdbscan'][year] and len(out)==len(set(out)),f'HDBSCAN {year} ID universe changed'); return out
def one_json_value(text:str,key:str)->Any:
    token=json.dumps(key); require(text.count(token)==1,f'JSON key {key!r} not unique'); start=text.index(token)+len(token)
    while text[start].isspace(): start+=1
    require(text[start]==':',f'missing colon after {key}'); start+=1
    while text[start].isspace(): start+=1
    value,_=json.JSONDecoder().raw_decode(text,start); return value
def sugar_ids_only(path:Path,year:int)->list[str]:
    require(sha256_file(path)==SUGAR_SHA256[year],f'Sugar {year} artifact hash changed')
    raw=one_json_value(gzip.decompress(path.read_bytes()).decode(),'event_ids'); require(isinstance(raw,list),f'Sugar {year} event_ids not list')
    out=list(map(str,raw)); require(len(out)==EXPECTED_COUNTS['sugar'][year] and len(out)==len(set(out)),f'Sugar {year} ID universe changed'); require(all(x.startswith(f'SNM{year}:') for x in out),f'Sugar {year} wrong-year ID'); return out
def main()->int:
    p=argparse.ArgumentParser()
    for panel in ('hdbscan','sugar'):
        for year in YEARS: p.add_argument(f'--{panel}-{year}',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path); a=p.parse_args()
    paths={'hdbscan':{2023:a.hdbscan_2023,2025:a.hdbscan_2025},'sugar':{2023:a.sugar_2023,2025:a.sugar_2025}}; panels={'hdbscan':{},'sugar':{}}
    for y in YEARS:
        h=hdbscan_ids_only(paths['hdbscan'][y],y); s=sugar_ids_only(paths['sugar'][y],y)
        panels['hdbscan'][str(y)]={'scan_ids':h,'scan_count':len(h)}; panels['sugar'][str(y)]={'scan_ids':s,'scan_count':len(s)}
    payload={'classification':'P2 matched-literature strict pretruth ID-only manifest','years':list(YEARS),'blind_exclusion':list(BLIND_EXCLUSION),'competitor_cluster_values_parsed':False,'known_shower_truth_values_parsed':False,'native_shower_tokens_parsed':False,'panels':panels,'input_hashes':{f'{p}_{y}':sha256_file(paths[p][y]) for p in paths for y in YEARS}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(payload)+'\n'); print('PASS_P3_STRICT_PRETRUTH_ID_ONLY_MANIFEST'); return 0
if __name__=='__main__': raise SystemExit(main())
