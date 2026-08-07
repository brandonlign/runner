#!/usr/bin/env python3
"""AMOR 1990-1999 structure-only audit. Never decodes meteor-record token values."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

YEARS=tuple(range(1990,2000))
INDEX_URL='https://ceres.ta3.sk/iaumdcdb//dataDBs/radio_offline/index.php'
MIN_OPAQUE_ROWS=10000


def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def safe(name:str)->bool:
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not name.startswith(('/', '\\'))


def resolve_archive_urls()->tuple[dict[int,str],dict]:
    response=requests.get(INDEX_URL,timeout=120,headers={'User-Agent':'OrbitTrace-AMOR-structure/1.0'})
    response.raise_for_status()
    html=response.content
    soup=BeautifulSoup(html,'html.parser')
    urls={}
    labels={}
    for year in YEARS:
        expected=f'AMOR {year} - ZIP archive'
        matches=[]
        for anchor in soup.find_all('a',href=True):
            label=' '.join(anchor.get_text(' ',strip=True).split())
            if label==expected:
                matches.append(urljoin(response.url,anchor['href']))
        if len(matches)!=1:
            raise RuntimeError(f'{year}: expected one exact official AMOR archive link, got {matches}')
        urls[year]=matches[0]
        labels[year]=expected
    return urls,{
        'index_url_requested':INDEX_URL,
        'index_final_url':response.url,
        'index_sha256':hashlib.sha256(html).hexdigest(),
        'exact_link_labels':labels,
    }


def download(year:int,url:str,root:Path)->Path:
    path=root/f'amor-{year}.zip'
    with requests.get(url,timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-AMOR-structure/1.0'}) as response:
        response.raise_for_status()
        with path.open('wb') as fh:
            for chunk in response.iter_content(1024*1024):
                if chunk:
                    fh.write(chunk)
    return path


def opaque_line_shape(zf:zipfile.ZipFile,member:str)->dict:
    rows=0
    token_hist=collections.Counter()
    byte_hist=collections.Counter()
    min_len=None; max_len=0
    with zf.open(member,'r') as fh:
        for raw in fh:
            raw=raw.rstrip(b'\r\n')
            if not raw:
                continue
            # The bytes are never decoded or numerically interpreted.
            rows+=1
            n_tokens=len(raw.split())
            n_bytes=len(raw)
            token_hist[n_tokens]+=1
            byte_hist[n_bytes]+=1
            min_len=n_bytes if min_len is None else min(min_len,n_bytes)
            max_len=max(max_len,n_bytes)
    modal_token,modal_count=token_hist.most_common(1)[0] if token_hist else (None,0)
    return {
        'rows':rows,
        'modal_whitespace_token_count':modal_token,
        'modal_token_fraction':(modal_count/rows if rows else 0.0),
        'distinct_token_counts':len(token_hist),
        'token_count_histogram':{str(k):int(v) for k,v in sorted(token_hist.items())},
        'distinct_line_byte_lengths':len(byte_hist),
        'min_line_bytes':min_len,
        'max_line_bytes':max_len,
    }


def inspect_archive(year:int,path:Path,url:str)->dict:
    archive_sha=sha_file(path)
    with zipfile.ZipFile(path) as zf:
        bad=zf.testzip()
        names=zf.namelist()
        regular=[n for n in names if not n.endswith('/') and zf.getinfo(n).file_size>0]
        one_line=[n for n in regular if PurePosixPath(n).suffix.lower()=='.1l']
        member_meta=[{
            'member':n,
            'bytes':int(zf.getinfo(n).file_size),
            'suffix':PurePosixPath(n).suffix.lower(),
        } for n in regular]
        one_line_audits=[]
        for member in one_line:
            shape=opaque_line_shape(zf,member)
            one_line_audits.append({'member':member,**shape})
        primary=one_line_audits[0] if len(one_line_audits)==1 else None
        gates={
            'zip_crc':bad is None,
            'safe_paths':all(safe(n) for n in names),
            'at_least_one_regular_member':bool(regular),
            'exactly_one_reduced_single_line_member':len(one_line)==1,
            'reduced_member_at_least_10000_rows':bool(primary and primary['rows']>=MIN_OPAQUE_ROWS),
            'reduced_member_single_token_shape':bool(primary and primary['distinct_token_counts']==1),
            'reduced_member_modal_shape_fraction_1':bool(primary and abs(float(primary['modal_token_fraction'])-1.0)<1e-15),
        }
        structurally_valid=all(gates.values())
        return {
            'year':year,
            'url':url,
            'archive_sha256':archive_sha,
            'archive_bytes':path.stat().st_size,
            'regular_members':member_meta,
            'reduced_single_line_members':one_line_audits,
            'opaque_record_count':(int(primary['rows']) if primary else None),
            'opaque_modal_token_count':(int(primary['modal_whitespace_token_count']) if primary and primary['modal_whitespace_token_count'] is not None else None),
            'gates':gates,
            'structurally_valid':structurally_valid,
        }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--freshness-json',required=True,type=Path)
    p.add_argument('--development-pass-json',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)

    freshness=json.loads(args.freshness_json.read_text())
    if freshness['verdict']!='PASS_AMOR_1990_1999_REPO_SCIENTIFIC_FRESHNESS_AUDIT':
        raise RuntimeError('AMOR freshness prerequisite did not pass')
    if freshness['potential_exposure_hit_count']!=0:
        raise RuntimeError('AMOR freshness prerequisite contains exposure hits')
    if any(freshness[k] for k in ('catalogue_access_this_audit','scientific_value_access_this_audit','label_access_this_audit','target_information_access')):
        raise RuntimeError('AMOR freshness boundary changed')

    development=json.loads(args.development_pass_json.read_text())
    if development.get('verdict')!='PASS_MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT':
        raise RuntimeError('v8 development has not passed; AMOR archive access is prohibited')
    if not all(development.get('integrity_gates',{}).values()) or not all(development.get('scientific_gates',{}).values()):
        raise RuntimeError('v8 development pass gates incomplete')

    urls,index_meta=resolve_archive_urls()
    raw_root=args.output/'_archives'; raw_root.mkdir(exist_ok=True)
    try:
        years=[]
        for year in YEARS:
            path=download(year,urls[year],raw_root)
            years.append(inspect_archive(year,path,urls[year]))
            print(f'AMOR structure {year}: valid={years[-1]["structurally_valid"]} rows={years[-1]["opaque_record_count"]}',flush=True)

        valid=[item for item in years if item['structurally_valid']]
        valid.sort(key=lambda item:(-int(item['opaque_record_count']),int(item['year'])))
        selected=[int(item['year']) for item in valid[:2]] if len(valid)>=2 else []
        selected_token_counts={int(item['opaque_modal_token_count']) for item in valid[:2]} if len(valid)>=2 else set()
        gates={
            'at_least_two_structurally_valid_years':len(valid)>=2,
            'selected_pair_has_same_opaque_token_count':len(selected_token_counts)==1 if len(valid)>=2 else False,
            'selected_pair_exactly_metadata_rule_top_two':selected==[int(item['year']) for item in valid[:2]] if len(valid)>=2 else False,
        }
        verdict='PASS_AMOR_STRUCTURE_AND_PANEL_SELECTION' if all(gates.values()) else 'FAIL_AMOR_STRUCTURE_AND_PANEL_SELECTION'
        result={
            'verdict':verdict,
            'index_metadata':index_meta,
            'years':years,
            'valid_years_ranked_by_opaque_count':[int(item['year']) for item in valid],
            'selected_external_years':selected,
            'selection_rule':'structurally valid >=10000 opaque rows; descending opaque row count; tie earlier year; select first two',
            'gates':gates,
            'scientific_values_read':False,
            'shower_label_values_read':False,
            'orbital_values_read':False,
            'target_information_access':False,
            'excluded_target_interval_values_read':False,
            'schema_documentation_source':'IAU MDC radio reduced single-line format; archive audit reads record bytes only for physical line/byte/token counts',
            'claim_boundary':'AMOR ZIP containers and opaque record shapes were inspected only after a passed v8 development artifact. No meteor token value was decoded or scientifically interpreted. The selected future year pair is determined solely by structural validity and opaque row count.',
        }
        (args.output/'amor_structure_and_panel_selection.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        if verdict.startswith('FAIL_'):
            raise SystemExit(1)
        return 0
    finally:
        if raw_root.exists():
            for child in raw_root.iterdir():
                child.unlink()
            raw_root.rmdir()


if __name__=='__main__':
    raise SystemExit(main())
