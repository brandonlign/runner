#!/usr/bin/env python3
"""Structure-only SAAMER 2022/2023 audit; meteor token values are never decoded."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

import requests

YEARS=(2022,2023)
URLS={
    2022:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2022.zip',
    2023:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2023.zip',
}
EXPECTED_LEGEND_SHA256='afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b'
EXPECTED_TOKEN_COUNT=16
MONTHS=('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')
EXPECTED_SCHEMA_FIELDS=('IC','Yr','Mn','Day','LS','HM','RA','DEC','Vg','Vh','q','e','a','i','arg','nod')


def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def safe(name:str)->bool:
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not name.startswith(('/', '\\'))


def month_key(name:str):
    m=re.fullmatch(r'SAA([a-z]{3})(\d{4})\.dat',PurePosixPath(name).name,re.I)
    if not m:
        return None
    mon=m.group(1).lower(); year=int(m.group(2))
    if mon not in MONTHS:
        return None
    return year,MONTHS.index(mon)+1


def download(year:int,root:Path)->Path:
    path=root/f'iaumdcSAAMER{year}.zip'
    with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-SAAMER-structure/2.0'}) as response:
        response.raise_for_status()
        with path.open('wb') as fh:
            for chunk in response.iter_content(1024*1024):
                if chunk:
                    fh.write(chunk)
    return path


def inspect(year:int,path:Path)->dict:
    archive_sha=sha_file(path)
    with zipfile.ZipFile(path) as zf:
        bad=zf.testzip(); names=zf.namelist()
        regular=[n for n in names if not n.endswith('/') and zf.getinfo(n).file_size>0]
        legends=[n for n in regular if PurePosixPath(n).name.lower()=='legend.inf']
        dat=[n for n in regular if month_key(n) is not None]
        other=[n for n in regular if n not in legends and n not in dat]
        if len(legends)!=1:
            raise RuntimeError(f'{year}: expected exactly one legend.inf, got {legends}')
        legend_bytes=zf.read(legends[0])
        legend_sha=hashlib.sha256(legend_bytes).hexdigest()
        legend_text=legend_bytes.decode('utf-8',errors='strict')
        # legend.inf is schema metadata, not a meteor record. Exact field-name presence is allowed.
        field_presence={
            field: bool(re.search(rf'(?<![A-Za-z0-9]){re.escape(field)}(?![A-Za-z0-9])',legend_text,re.I))
            for field in EXPECTED_SCHEMA_FIELDS
        }

        monthly=[]; total_rows=0; global_tokens=collections.Counter(); line_lengths=collections.Counter()
        for member in sorted(dat,key=lambda n:month_key(n)):
            local_tokens=collections.Counter(); rows=0; min_len=None; max_len=0
            with zf.open(member,'r') as fh:
                for raw in fh:
                    raw=raw.rstrip(b'\r\n')
                    if not raw:
                        continue
                    # Permitted meteor-record operations: opaque line count, byte count, whitespace-token count only.
                    rows+=1; total_rows+=1
                    token_count=len(raw.split()); byte_count=len(raw)
                    local_tokens[token_count]+=1; global_tokens[token_count]+=1; line_lengths[byte_count]+=1
                    min_len=byte_count if min_len is None else min(min_len,byte_count)
                    max_len=max(max_len,byte_count)
            monthly.append({
                'member':member,
                'month_key':list(month_key(member)),
                'rows':rows,
                'token_count_histogram':{str(k):int(v) for k,v in sorted(local_tokens.items())},
                'min_line_bytes':min_len,
                'max_line_bytes':max_len,
            })

        found={month_key(n) for n in dat}
        expected={(year,month) for month in range(1,13)}
        gates={
            'zip_crc':bad is None,
            'safe_paths':all(safe(n) for n in names),
            'one_legend':len(legends)==1,
            'legend_exactly_matches_preexisting_2020_2021_schema_hash':legend_sha==EXPECTED_LEGEND_SHA256,
            'all_expected_schema_fields_present_in_legend':all(field_presence.values()),
            'no_unexpected_regular_members':not other,
            'exact_12_nominal_year_month_members':found==expected,
            'every_month_nonempty':len(monthly)==12 and all(row['rows']>0 for row in monthly),
            'at_least_100000_total_rows':total_rows>=100000,
            'every_nonempty_meteor_row_exactly_16_whitespace_tokens':set(global_tokens)=={EXPECTED_TOKEN_COUNT},
        }
        return {
            'year':year,
            'url':URLS[year],
            'archive_sha256':archive_sha,
            'archive_bytes':path.stat().st_size,
            'legend_member':legends[0],
            'legend_sha256':legend_sha,
            'legend_schema_field_presence':field_presence,
            'monthly_members':monthly,
            'total_rows':total_rows,
            'global_token_count_histogram':{str(k):int(v) for k,v in sorted(global_tokens.items())},
            'distinct_line_byte_lengths':len(line_lengths),
            'gates':gates,
        }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--freshness-json',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)

    fresh=json.loads(args.freshness_json.read_text())
    if fresh['verdict']!='PASS_SAAMER_2022_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT':
        raise RuntimeError('freshness prerequisite did not pass')
    if fresh['potential_exposure_hit_count']!=0:
        raise RuntimeError('freshness prerequisite contains exposure hits')
    if any(fresh[key] for key in ('catalogue_access_this_audit','scientific_value_access_this_audit','label_access_this_audit','target_information_access')):
        raise RuntimeError('freshness audit boundary changed')

    raw_root=args.output/'_archives'; raw_root.mkdir(exist_ok=True)
    try:
        years=[]
        for year in YEARS:
            path=download(year,raw_root)
            years.append(inspect(year,path))
        gates={
            'all_year_structure_gates':all(all(item['gates'].values()) for item in years),
            'same_legend_sha_between_2022_2023':years[0]['legend_sha256']==years[1]['legend_sha256'],
            'same_token_shape_between_2022_2023':years[0]['global_token_count_histogram'].keys()==years[1]['global_token_count_histogram'].keys(),
        }
        verdict='PASS_SAAMER_2022_2023_STRUCTURAL_AUDIT' if all(gates.values()) else 'FAIL_SAAMER_2022_2023_STRUCTURAL_AUDIT'
        result={
            'verdict':verdict,
            'years':years,
            'gates':gates,
            'scientific_values_read':False,
            'shower_label_values_read':False,
            'orbital_values_read':False,
            'target_information_access':False,
            'excluded_target_interval_values_read':False,
            'schema_metadata_read':True,
            'meteor_record_operations_permitted':['physical nonempty-line count','byte length','whitespace-token count'],
            'claim_boundary':(
                'The ZIP bytes and legend.inf schema metadata were accessed to establish transport and structure. '
                'For every meteor DAT record, no token content was decoded, retained, compared, printed, or classified; only opaque line/token/byte counts were aggregated.'
            ),
        }
        (args.output/'saamer_2022_2023_structural_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        if verdict.startswith('FAIL_'):
            raise SystemExit(1)
        return 0
    finally:
        if raw_root.exists():
            for path in raw_root.iterdir():
                path.unlink()
            raw_root.rmdir()


if __name__=='__main__':
    raise SystemExit(main())
