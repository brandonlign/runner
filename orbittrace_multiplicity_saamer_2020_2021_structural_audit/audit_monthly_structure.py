#!/usr/bin/env python3
"""SAAMER monthly-DAT structure audit. Reads schema metadata and line shapes only."""
from __future__ import annotations

import argparse
import collections
import hashlib
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
EXPECTED_ARCHIVE_SHA={
    2020:'208938b6ed6c504d77eb96ae1d9a867f5957fcba48076fd1bac9632c24ff4933',
    2021:'41a1aa7d568c98f273087fd2648cf6e9aa365373bf25b3db36d54ea987dd727c',
}
REQUIRED_LEGEND_FIELDS=('LS','RA','DEC','Vg','Sh')
MONTHS=('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')


def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def safe(name:str)->bool:
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not name.startswith(('/', '\\'))


def download(year:int,out:Path)->Path:
    path=out/f'iaumdcSAAMER{year}.zip'
    with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-SAAMER-structure/1.2'}) as r:
        r.raise_for_status()
        with path.open('wb') as fh:
            for chunk in r.iter_content(1024*1024):
                if chunk: fh.write(chunk)
    return path


def month_key(name:str):
    m=re.fullmatch(r'SAA([a-z]{3})(\d{4})\.dat',PurePosixPath(name).name,re.I)
    if not m: return None
    mon=m.group(1).lower(); year=int(m.group(2))
    if mon not in MONTHS: return None
    return year,MONTHS.index(mon)+1


def inspect(year:int,path:Path)->dict:
    archive_sha=sha_file(path)
    if archive_sha!=EXPECTED_ARCHIVE_SHA[year]:
        raise RuntimeError(f'{year}: archive SHA changed: {archive_sha}')
    with zipfile.ZipFile(path) as zf:
        bad=zf.testzip(); names=zf.namelist()
        regular=[n for n in names if not n.endswith('/') and zf.getinfo(n).file_size>0]
        legends=[n for n in regular if PurePosixPath(n).name.lower()=='legend.inf']
        dat=[n for n in regular if month_key(n) is not None]
        other=[n for n in regular if n not in legends and n not in dat]
        if len(legends)!=1:
            raise RuntimeError(f'{year}: expected one legend.inf, got {legends}')
        legend_bytes=zf.read(legends[0])
        legend_text=legend_bytes.decode('utf-8',errors='strict')
        # Schema metadata only. Field-name checks are word-boundary based.
        legend_fields={f: bool(re.search(rf'(?<![A-Za-z0-9]){re.escape(f)}(?![A-Za-z0-9])',legend_text,re.I)) for f in REQUIRED_LEGEND_FIELDS}

        monthly=[]; year_rows=0; total_shape_lines=0; token_hist=collections.Counter(); length_hist=collections.Counter()
        for member in sorted(dat,key=lambda n:month_key(n)):
            row_count=0; local_tokens=collections.Counter(); min_len=None; max_len=0
            with zf.open(member,'r') as fh:
                for raw in fh:
                    raw=raw.rstrip(b'\r\n')
                    if not raw: continue
                    row_count += 1; year_rows += 1; total_shape_lines += 1
                    n_tokens=len(raw.split())
                    n_bytes=len(raw)
                    local_tokens[n_tokens]+=1; token_hist[n_tokens]+=1; length_hist[n_bytes]+=1
                    min_len=n_bytes if min_len is None else min(min_len,n_bytes)
                    max_len=max(max_len,n_bytes)
            modal_token,modal_count=local_tokens.most_common(1)[0] if local_tokens else (None,0)
            monthly.append({
                'member':member,'month_key':list(month_key(member)),'rows':row_count,
                'modal_whitespace_token_count':modal_token,
                'modal_token_fraction':(modal_count/row_count if row_count else 0.0),
                'distinct_token_counts':len(local_tokens),'min_line_bytes':min_len,'max_line_bytes':max_len,
            })
        modal_token,modal_count=token_hist.most_common(1)[0] if token_hist else (None,0)
        expected_months={(year,m) for m in range(1,13)}
        found={month_key(n) for n in dat}
        if year==2020:
            expected_months.add((2019,12))
        gates={
            'zip_crc':bad is None,
            'safe_paths':all(safe(n) for n in names),
            'one_legend':len(legends)==1,
            'no_unexpected_regular_members':not other,
            'expected_month_members':found==expected_months,
            'required_legend_fields':all(legend_fields.values()),
            'at_least_100000_total_rows':year_rows>=100000,
            'dominant_token_shape_at_least_0_99':(modal_count/year_rows if year_rows else 0.0)>=0.99,
            'every_month_nonempty':all(m['rows']>0 for m in monthly),
        }
        return {
            'year':year,'archive_sha256':archive_sha,'archive_bytes':path.stat().st_size,
            'legend_member':legends[0],'legend_sha256':hashlib.sha256(legend_bytes).hexdigest(),
            'legend_text':legend_text,'legend_required_field_presence':legend_fields,
            'monthly_members':monthly,'total_rows':year_rows,
            'modal_whitespace_token_count':modal_token,'modal_token_fraction':(modal_count/year_rows if year_rows else 0.0),
            'distinct_line_byte_lengths':len(length_hist),'gates':gates,
        }


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--freshness-json',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    fresh=json.loads(a.freshness_json.read_text())
    assert fresh['verdict']=='PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    assert fresh['potential_exposure_hit_count']==0
    archives=a.output/'archives'; archives.mkdir(exist_ok=True)
    try:
        years=[]
        for y in YEARS:
            path=download(y,archives); years.append(inspect(y,path))
        gates={
            'all_year_gates':all(all(x['gates'].values()) for x in years),
            'same_legend_sha':years[0]['legend_sha256']==years[1]['legend_sha256'],
            'same_modal_token_count':years[0]['modal_whitespace_token_count']==years[1]['modal_whitespace_token_count'],
        }
        verdict='PASS_SAAMER_2020_2021_MONTHLY_STRUCTURAL_AUDIT' if all(gates.values()) else 'FAIL_SAAMER_2020_2021_MONTHLY_STRUCTURAL_AUDIT'
        result={
            'verdict':verdict,'years':years,'gates':gates,
            'scientific_values_read':False,'shower_label_values_read':False,
            'target_information_access':False,'excluded_target_interval_values_read':False,
            'schema_metadata_read':True,
            'data_line_operations_permitted':['physical nonempty-line count','byte length','whitespace-token count'],
            'claim_boundary':'legend.inf is schema metadata. For .dat meteor records, no token content was decoded, retained, compared, printed, classified, or used; only opaque line/token counts were aggregated.',
        }
        (a.output/'saamer_2020_2021_monthly_structural_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
        if verdict.startswith('FAIL_'): raise SystemExit(1)
        return 0
    finally:
        if archives.exists():
            for pth in archives.iterdir(): pth.unlink()
            archives.rmdir()

if __name__=='__main__': raise SystemExit(main())
