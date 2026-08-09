#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import math
import zipfile
from pathlib import Path

YEARS=(2023,2025)
MEMBERS={2023:'023a/_U2_20230101_S.csv',2025:'025a/_U2_20250101_S.csv'}
ARCHIVE_SHA256={2023:'9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430',2025:'f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52'}
BLIND_LOW=20.0
BLIND_HIGH=55.0
EXPECTED_ORBIT_INDICES={'q':14,'e':16,'peri':18,'node':20,'i':21}
EXPECTED_SHARED_INDICES={'soldeg':3,'radeg':4,'dedeg':6,'vgkms':8,'qau':14,'e':16,'perideg':18,'nodedeg':20,'incldeg':21,'shower':38}
EXPECTED_HEADER_COUNTS={2023:46,2025:43}

def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)

def sha256_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm_header(value:str)->str:
    return ''.join(ch.lower() for ch in value.strip().lstrip('\ufeff') if ch.isalnum())

def read_exact_orbits(year:int,archive:Path,requested:set[str])->dict[str,dict[str,float]]:
    require(year in YEARS,'unsupported P3 matched year')
    require(sha256_file(archive)==ARCHIVE_SHA256[year],f'archive hash changed {year}')
    prefix=f'SNM{year}:'; row_indices:dict[int,str]={}
    for event_id in requested:
        require(event_id.startswith(prefix),f'wrong-year P3 orbit id {event_id}'); index=int(event_id.split(':',1)[1]); require(index>=0 and index not in row_indices,f'invalid/duplicate P3 orbit id {event_id}'); row_indices[index]=event_id
    found:dict[str,dict[str,float]]={}
    with zipfile.ZipFile(archive) as zf:
        require(MEMBERS[year] in zf.namelist(),f'missing P3 orbit archive member {MEMBERS[year]}')
        with zf.open(MEMBERS[year]) as raw:
            reader=csv.reader(io.TextIOWrapper(raw,encoding='utf-8-sig',newline='')); header=next(reader)
            while header and header[-1].strip()=='': header=header[:-1]
            require(len(header)==EXPECTED_HEADER_COUNTS[year],f'SNMv3 header count changed {year}: {len(header)}'); names=[norm_header(x) for x in header]
            for name,index in EXPECTED_SHARED_INDICES.items(): require(index<len(names) and names[index]==name,f'SNMv3 shared header index changed {year} {name}: {names[index] if index<len(names) else None}')
            for row_index,raw_row in enumerate(reader):
                if row_index not in row_indices: continue
                row=list(raw_row)
                while len(row)>len(header) and row[-1].strip()=='': row.pop()
                event_id=row_indices[row_index]; require(len(row)>max(EXPECTED_ORBIT_INDICES.values()),f'short requested P3 orbit row {event_id}')
                try:
                    q=float(row[14]); e=float(row[16]); peri=float(row[18]); node=float(row[20]); inc=float(row[21]); sol=float(row[3])%360.0
                except Exception as exc:
                    raise RuntimeError(f'P2_MATCHED_INPUT_INELIGIBLE_ORBIT_UNPARSEABLE {event_id}') from exc
                require(not(BLIND_LOW<=sol<=BLIND_HIGH),f'P3 exact-row orbit enters excluded interval {event_id}'); require(all(math.isfinite(x) for x in (q,e,peri,node,inc)),f'P2_MATCHED_INPUT_INELIGIBLE_ORBIT_NONFINITE {event_id}'); require(q>0.0 and 0.0<=e<2.0 and 0.0<=inc<=180.0,f'P2_MATCHED_INPUT_INELIGIBLE_ORBIT_PHYSICAL {event_id}'); found[event_id]={'q':q,'e':e,'i':inc,'peri':peri%360.0,'node':node%360.0}
    missing=sorted(requested-set(found),key=lambda x:int(x.split(':',1)[1])); require(not missing,f'P2_MATCHED_INPUT_INELIGIBLE_ORBIT_MISSING n={len(missing)} first={missing[:10]}'); require(len(found)==len(requested),f'P3 exact-row orbit count mismatch {year}'); return found
