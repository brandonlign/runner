#!/usr/bin/env python3
"""Structure-only SAAMER 2020/2021 audit. Never inspects meteor data-column values."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath

import requests

YEARS=(2020,2021)
URLS={
    2020:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2020.zip',
    2021:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2021.zip',
}
REQUIRED_METHOD_FIELDS={'LS','RA','DEC','Vg','Sh'}
REQUIRED_ID_DATE_FIELDS={'DB','IC','Yr','Mn','Day'}
MIN_ROWS=100_000


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name:str)->bool:
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not name.startswith(('/', '\\'))


def download(year:int,outdir:Path)->Path:
    path=outdir/f'iaumdcSAAMER{year}.zip'
    with requests.get(URLS[year],timeout=300,stream=True,headers={'User-Agent':'OrbitTrace-SAAMER-structural-audit/1.0'}) as r:
        r.raise_for_status()
        with path.open('wb') as fh:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: fh.write(chunk)
    return path


def detect_delimiter(header_line:str)->str:
    candidates=[';','\t',',']
    counts={d:header_line.count(d) for d in candidates}
    delimiter=max(counts,key=counts.get)
    if counts[delimiter] < 4:
        raise RuntimeError(f'cannot identify tabular delimiter from header counts {counts}')
    return delimiter


def inspect(year:int,archive:Path)->dict:
    with zipfile.ZipFile(archive) as zf:
        bad=zf.testzip()
        names=zf.namelist()
        csv_members=[n for n in names if n.lower().endswith('.csv')]
        if len(csv_members)!=1:
            raise RuntimeError(f'{year}: expected exactly one CSV member, got {csv_members[:20]}')
        member=csv_members[0]
        if not safe_name(member):
            raise RuntimeError(f'{year}: unsafe member {member}')
        info=zf.getinfo(member)
        with zf.open(member,'r') as raw:
            text=io.TextIOWrapper(raw,encoding='utf-8-sig',newline='')
            first=text.readline()
            if not first:
                raise RuntimeError(f'{year}: empty CSV')
            delimiter=detect_delimiter(first)
            header=next(csv.reader([first],delimiter=delimiter))
            header=[x.strip() for x in header]
            row_count=0
            malformed=0
            # Structural-only: each row is tokenized solely to count columns. No token
            # content is converted, retained, compared, printed, or used scientifically.
            reader=csv.reader(text,delimiter=delimiter)
            width=len(header)
            for row in reader:
                if not row or not any(field != '' for field in row):
                    continue
                row_count += 1
                malformed += int(len(row)!=width)
    gates={
        'zip_crc':bad is None,
        'safe_paths':all(safe_name(n) for n in names),
        'exactly_one_csv_member':len(csv_members)==1,
        'nonempty_unique_header':bool(header) and all(header) and len(set(header))==len(header),
        'required_method_fields':REQUIRED_METHOD_FIELDS.issubset(set(header)),
        'required_id_date_fields':REQUIRED_ID_DATE_FIELDS.issubset(set(header)),
        'at_least_100000_rows':row_count>=MIN_ROWS,
        'zero_malformed_width_rows':malformed==0,
    }
    return {
        'year':year,
        'url':URLS[year],
        'archive_bytes':archive.stat().st_size,
        'archive_sha256':sha256_file(archive),
        'member':member,
        'member_uncompressed_bytes':info.file_size,
        'member_compressed_bytes':info.compress_size,
        'delimiter':repr(delimiter),
        'header':header,
        'header_count':len(header),
        'row_count':row_count,
        'malformed_width_rows':malformed,
        'gates':gates,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--freshness-json',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    fresh=json.loads(args.freshness_json.read_text())
    assert fresh['verdict']=='PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    assert fresh['potential_exposure_hit_count']==0
    assert fresh['catalogue_access_this_audit'] is False
    assert fresh['scientific_value_access_this_audit'] is False
    assert fresh['label_access_this_audit'] is False
    assert fresh['target_information_access'] is False

    archives=args.output/'archives'; archives.mkdir(exist_ok=True)
    results=[]
    for year in YEARS:
        path=download(year,archives)
        results.append(inspect(year,path))

    gates={
        'years_exact':[x['year'] for x in results]==list(YEARS),
        'all_year_gates':all(all(x['gates'].values()) for x in results),
        'same_header':results[0]['header']==results[1]['header'],
        'same_delimiter':results[0]['delimiter']==results[1]['delimiter'],
    }
    verdict='PASS_SAAMER_2020_2021_STRUCTURAL_TRANSPORT_AUDIT' if all(gates.values()) else 'FAIL_SAAMER_2020_2021_STRUCTURAL_TRANSPORT_AUDIT'
    result={
        'verdict':verdict,
        'years':results,
        'gates':gates,
        'scientific_values_read':False,
        'shower_label_values_read':False,
        'target_information_access':False,
        'excluded_target_interval_values_read':False,
        'structural_information_read':['archive bytes/hash','ZIP CRC/member names','CSV delimiter/header','row count','row width'],
        'claim_boundary':'This audit transports the raw SAAMER archives but does not inspect any meteor data-column value, shower-label value, detector score, or target-region content. A pass authorizes only source-only parser/method pre-registration before first scientific-value access.',
    }
    (args.output/'saamer_2020_2021_structural_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    # Archive bytes are deliberately not uploaded by this audit; only hashes/structure are retained.
    for path in archives.iterdir(): path.unlink()
    archives.rmdir()
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
    return 0


if __name__=='__main__': raise SystemExit(main())
