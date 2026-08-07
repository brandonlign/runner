#!/usr/bin/env python3
"""Corrected structure-only SAAMER 2020/2021 audit; no scientific values are read."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

import requests

YEARS=(2020,2021)
URLS={
    2020:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2020.zip',
    2021:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2021.zip',
}
REQUIRED_NORMALIZED={'ls','ra','dec','vg','sh'}
MIN_ROWS=100_000


def norm(s:str)->str:
    return re.sub(r'[^a-z0-9]+','',s.lstrip('\ufeff').strip().lower())


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def safe_name(name:str)->bool:
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not name.startswith(('/', '\\'))


def download(year:int,outdir:Path)->Path:
    path=outdir/f'iaumdcSAAMER{year}.zip'
    with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-SAAMER-structural-audit/1.1'}) as r:
        r.raise_for_status()
        with path.open('wb') as fh:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: fh.write(chunk)
    return path


def detect_delimiter(first:str)->str:
    candidates=[';','\t',',','|']
    counts={d:first.count(d) for d in candidates}
    d=max(counts,key=counts.get)
    if counts[d] < 4:
        raise RuntimeError(f'cannot identify delimiter from header counts {counts}')
    return d


def inspect(year:int,archive:Path)->dict:
    with zipfile.ZipFile(archive) as zf:
        bad=zf.testzip()
        names=zf.namelist()
        regular=[n for n in names if not n.endswith('/') and zf.getinfo(n).file_size>0]
        member_meta=[{'name':n,'uncompressed_bytes':zf.getinfo(n).file_size,'compressed_bytes':zf.getinfo(n).compress_size} for n in regular]
        if len(regular)!=1:
            return {
                'year':year,'url':URLS[year],'archive_sha256':sha256_file(archive),'archive_bytes':archive.stat().st_size,
                'regular_members':member_meta,'container_gate_failure':'expected_exactly_one_regular_member',
                'scientific_values_read':False,'shower_label_values_read':False,
            }
        member=regular[0]
        if not safe_name(member): raise RuntimeError(f'{year}: unsafe member {member}')
        with zf.open(member,'r') as raw:
            text=io.TextIOWrapper(raw,encoding='utf-8-sig',newline='')
            first=text.readline()
            if not first: raise RuntimeError(f'{year}: empty tabular member')
            delimiter=detect_delimiter(first)
            header=[x.strip() for x in next(csv.reader([first],delimiter=delimiter))]
            width=len(header)
            normalized=[norm(x) for x in header]
            row_count=0; malformed=0
            reader=csv.reader(text,delimiter=delimiter)
            for row in reader:
                # Structural-only: do not inspect row token contents. Empty physical lines
                # arrive as []; all nonempty records are used only for len(row).
                if not row: continue
                row_count += 1
                malformed += int(len(row)!=width)
        gates={
            'zip_crc':bad is None,
            'safe_paths':all(safe_name(n) for n in names),
            'exactly_one_regular_member':len(regular)==1,
            'nonempty_unique_header':bool(header) and all(header) and len(set(header))==len(header),
            'required_method_fields_present':REQUIRED_NORMALIZED.issubset(set(normalized)),
            'at_least_100000_rows':row_count>=MIN_ROWS,
            'zero_malformed_width_rows':malformed==0,
        }
        return {
            'year':year,'url':URLS[year],'archive_sha256':sha256_file(archive),'archive_bytes':archive.stat().st_size,
            'regular_members':member_meta,'member':member,'delimiter':repr(delimiter),'header':header,'normalized_header':normalized,
            'header_count':width,'row_count':row_count,'malformed_width_rows':malformed,'gates':gates,
            'scientific_values_read':False,'shower_label_values_read':False,
        }


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--freshness-json',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    fresh=json.loads(args.freshness_json.read_text())
    assert fresh['verdict']=='PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    assert fresh['potential_exposure_hit_count']==0
    assert fresh['catalogue_access_this_audit'] is False and fresh['scientific_value_access_this_audit'] is False
    assert fresh['label_access_this_audit'] is False and fresh['target_information_access'] is False

    archives=args.output/'archives'; archives.mkdir(exist_ok=True)
    years=[]
    try:
        for year in YEARS:
            path=download(year,archives); years.append(inspect(year,path))
        complete=all('gates' in x for x in years)
        gates={
            'both_years_structurally_decoded':complete,
            'all_year_gates':complete and all(all(x['gates'].values()) for x in years),
            'same_header':complete and years[0]['header']==years[1]['header'],
            'same_delimiter':complete and years[0]['delimiter']==years[1]['delimiter'],
        }
        verdict='PASS_SAAMER_2020_2021_STRUCTURAL_TRANSPORT_AUDIT' if all(gates.values()) else 'FAIL_SAAMER_2020_2021_STRUCTURAL_TRANSPORT_AUDIT'
        result={
            'verdict':verdict,'years':years,'gates':gates,
            'scientific_values_read':False,'shower_label_values_read':False,'target_information_access':False,
            'excluded_target_interval_values_read':False,
            'structural_information_read':['archive bytes/hash','ZIP CRC/member metadata','first-record header','delimiter','row count','row width'],
            'claim_boundary':'No post-header token value was inspected, converted, retained, compared, printed, or used. A pass authorizes only source-only parser and sampling preregistration before first scientific-value access.',
        }
        (args.output/'saamer_2020_2021_structural_audit_corrected.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        if verdict.startswith('FAIL_'): raise SystemExit(1)
        return 0
    finally:
        if archives.exists():
            for path in archives.iterdir(): path.unlink()
            archives.rmdir()


if __name__=='__main__': raise SystemExit(main())
