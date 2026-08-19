#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import zipfile
from pathlib import Path

from orbittrace_v15_dms_coverage_eligibility_v1 import audit_coverage as parent

EXPECTED_ROWS = 910
EXPECTED_WIDTH = 42
DATE_INDICES = {"year": 2, "month": 3, "day": 4}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.strip().lower())


def finite_float(s: str, name: str) -> float:
    try:
        x = float(s.strip())
    except ValueError as exc:
        raise RuntimeError(f"invalid DMS {name}") from exc
    req(math.isfinite(x), f"non-finite DMS {name}")
    return x


def parse_date(row: list[str]) -> tuple[int, int, float]:
    req(len(row) == EXPECTED_WIDTH, "DMS compact row width changed")
    yf = finite_float(row[DATE_INDICES["year"]], "year")
    mf = finite_float(row[DATE_INDICES["month"]], "month")
    day = finite_float(row[DATE_INDICES["day"]], "day")
    y = int(round(yf)); m = int(round(mf))
    req(abs(yf-y) <= 1e-9 and y in parent.YEARS, "invalid DMS year")
    req(abs(mf-m) <= 1e-9 and 1 <= m <= 12, "invalid DMS month")
    req(0.0 < day < 32.0, "invalid DMS decimal day")
    return y, m, day


def julian_date(y: int, m: int, day: float) -> float:
    yy, mm = y, m
    if mm <= 2:
        yy -= 1; mm += 12
    a = math.floor(yy / 100)
    b = 2 - a + math.floor(a / 4)
    return (math.floor(365.25 * (yy + 4716))
            + math.floor(30.6001 * (mm + 1))
            + day + b - 1524.5)


def sind(x: float) -> float:
    return math.sin(math.radians(x))


def solar_longitude(y: int, m: int, day: float) -> float:
    jd = julian_date(y, m, day)
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + t * (36000.76983 + 0.0003032 * t)
    ms = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    c = ((1.914602 - t * (0.004817 + 0.000014 * t)) * sind(ms)
         + (0.019993 - 0.000101 * t) * sind(2.0 * ms)
         + 0.000289 * sind(3.0 * ms))
    true_long = l0 + c
    omega = 125.04 - 1934.136 * t
    return (true_long - 0.00569 - 0.00478 * sind(omega)) % 360.0


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); return p.parse_args()


def main() -> int:
    a=parse_args()
    archive_url,page_sha=parent.discover_archive_url(); archive=parent.fetch(archive_url)
    req(archive[:4] == b'PK\x03\x04', 'official DMS payload is not ZIP')
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        members=[i for i in zf.infolist() if not i.is_dir() and i.file_size>0 and i.filename.lower().endswith(('.csv','.txt','.dat'))]
        req(len(members)==1, f'expected one DMS member, got {len(members)}')
        info=members[0]; raw=zf.read(info.filename); text,encoding=parent.decode_text(raw)
    req(encoding in {'utf-8-sig','utf-8'}, f'unexpected encoding {encoding}')
    rows=[r for r in csv.reader(io.StringIO(text),delimiter=';') if r and any(c.strip() for c in r)]
    req(len(rows)==EXPECTED_ROWS, f'DMS row count changed {len(rows)}'); req({len(r) for r in rows}=={EXPECTED_WIDTH}, 'DMS width changed')
    h0,h1=rows[:2]
    req(norm(h0[2]) in {'yr','year'} or norm(h1[2]) in {'yr','year'}, 'year header changed')
    req(norm(h0[3]) in {'mn','month'} or norm(h1[3]) in {'mn','month'}, 'month header changed')
    req(norm(h0[4]) in {'day','decday'} or norm(h1[4]) in {'day','decday'}, 'day header changed')
    data=rows[2:]; req(len(data)==parent.OFFICIAL_ORBIT_COUNT,'DMS 908-row cardinality changed')

    counts={y:0 for y in parent.YEARS}; bins={y:set() for y in parent.YEARS}; quadrants={y:set() for y in parent.YEARS}
    for row in data:
        y,m,day=parse_date(row); ls=solar_longitude(y,m,day)
        if parent.SEALED_LOWER <= ls <= parent.SEALED_UPPER: continue
        counts[y]+=1; bins[y].add(int(math.floor(ls/10.0))%36); quadrants[y].add(int(math.floor(ls/90.0))%4)
    years={}
    for y in parent.YEARS:
        gates={'usable_rows_at_least_80':counts[y]>=parent.MIN_ROWS,'occupied_10deg_bins_at_least_12':len(bins[y])>=parent.MIN_BINS_10,'occupied_quadrants_at_least_3':len(quadrants[y])>=parent.MIN_QUADRANTS}
        years[y]={'usable_target_excluded_rows':counts[y],'occupied_10deg_bin_count':len(bins[y]),'occupied_quadrant_count':len(quadrants[y]),'gates':gates,'eligible':all(gates.values())}
    pair=parent.choose_pair(years); verdict='ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE' if pair is not None else 'INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR'
    out={'verdict':verdict,'catalogue':'DMS1991-1998','official_video_page':parent.OFFICIAL_VIDEO_PAGE,'official_video_page_sha256':page_sha,'archive_sha256':parent.sha256(archive),'archive_bytes':len(archive),'member_basename':Path(info.filename).name,'member_sha256':parent.sha256(raw),'member_bytes':len(raw),'text_encoding':encoding,'schema_mode':'compact_date_derived_solar_longitude_v1','row_width':EXPECTED_WIDTH,'parsed_row_count':len(data),'allowed_data_fields':['Yr','Mn','Day'],'solar_longitude_source':'deterministic_date_derived_apparent_geocentric_solar_longitude_v1','year_gates':{'minimum_target_excluded_rows':parent.MIN_ROWS,'minimum_occupied_10deg_bins':parent.MIN_BINS_10,'minimum_occupied_quadrants':parent.MIN_QUADRANTS,'consecutive_pair_required':True},'years':{str(y):years[y] for y in parent.YEARS},'reserved_pair':list(pair) if pair else None,'sealed_interval':'20deg-55deg inclusive; derived-LS rows ignored and exclusion count intentionally not emitted','scientific_fields_accessed':False,'radiant_accessed':False,'velocity_accessed':False,'orbital_elements_accessed':False,'shower_labels_accessed':False,'v15_executed':False,'comparators_executed':False,'sonotaco_2013_2014_access':False,'maarsy_access':False,'orbittrace_target_information_access':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return 0

if __name__=='__main__': raise SystemExit(main())
