#!/usr/bin/env python3
"""Structure-only CAMSv3 2017/2018 transport audit; reads no scientific/label values."""
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

BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
YEARS = (2017, 2018)
REQUIRED = {"Yr", "Mn", "Dayy", "LS", "RA", "DECL", "Vg", "sh"}
MIN_STRUCTURAL_ROWS = 10_000


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and not name.startswith(("/", "\\"))


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lstrip("\ufeff").strip().lower())


def inspect_year(year: int, canonical_header: list[str]) -> dict:
    basename = f"iaumdcCAMSv3_{year}.csv"
    url = f"{BASE}/{basename}.zip"
    response = requests.get(url, timeout=300, headers={"User-Agent":"OrbitTrace-CAMS-structural-audit/1.0"})
    response.raise_for_status()
    raw = response.content
    archive_sha = sha(raw)

    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        bad = zf.testzip()
        names = zf.namelist()
        csv_members = [n for n in names if n.lower().endswith('.csv')]
        matches = [n for n in csv_members if PurePosixPath(n).name == basename]
        if len(matches) != 1:
            raise RuntimeError(f"{year}: expected exactly one {basename!r}; members={names}")
        member = matches[0]
        member_bytes = zf.read(member)

    # Structural-only CSV pass: inspect header and field counts only. No data-column
    # token is converted, compared, classified, retained, or emitted.
    reader = csv.reader(io.TextIOWrapper(io.BytesIO(member_bytes), encoding='utf-8-sig', newline=''), delimiter=';')
    try:
        header = [x.lstrip('\ufeff').strip() for x in next(reader)]
    except StopIteration as exc:
        raise RuntimeError(f"{year}: empty CSV") from exc
    row_count = 0
    malformed = 0
    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue
        row_count += 1
        malformed += int(len(row) != len(header))

    gates = {
        'zip_crc': bad is None,
        'safe_paths': all(safe_name(n) for n in names),
        'exactly_one_expected_csv_basename': len(matches) == 1,
        'exact_canonical_header': header == canonical_header,
        'unique_nonempty_header': bool(header) and all(header) and len(set(header)) == len(header),
        'required_geometry_and_label_fields_present': REQUIRED.issubset(set(header)),
        'at_least_10000_rows': row_count >= MIN_STRUCTURAL_ROWS,
        'zero_malformed_width_rows': malformed == 0,
    }
    return {
        'year': year,
        'url': url,
        'archive_bytes': len(raw),
        'archive_sha256': archive_sha,
        'member_path': member,
        'member_basename': PurePosixPath(member).name,
        'member_sha256': sha(member_bytes),
        'row_count': row_count,
        'header_count': len(header),
        'header': header,
        'normalized_header': [norm(x) for x in header],
        'malformed_width_rows': malformed,
        'gates': gates,
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--prior-structural-json', required=True, type=Path)
    p.add_argument('--freshness-json', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args=p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    prior=json.loads(args.prior_structural_json.read_text())
    freshness=json.loads(args.freshness_json.read_text())
    assert prior['verdict']=='PASS_CAMSV3_STRUCTURAL_FEASIBILITY_V2'
    assert prior['scientific_values_read'] is False
    assert prior['label_values_read'] is False
    assert freshness['verdict']=='PASS_CAMSV3_2017_2018_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
    assert freshness['catalogue_access_this_audit'] is False
    assert freshness['scientific_value_access_this_audit'] is False
    assert freshness['label_access_this_audit'] is False
    assert freshness['target_information_access'] is False
    canonical=prior['canonical_header']
    assert len(canonical)==63
    assert REQUIRED.issubset(set(canonical))

    years=[inspect_year(y, canonical) for y in YEARS]
    gates={
        'both_years_present':[x['year'] for x in years]==list(YEARS),
        'all_structural_gates':all(all(x['gates'].values()) for x in years),
        'identical_header_between_2017_2018':years[0]['header']==years[1]['header'],
        'identical_to_frozen_2011_2016_header':all(x['header']==canonical for x in years),
    }
    verdict='PASS_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_AUDIT' if all(gates.values()) else 'FAIL_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_AUDIT'
    result={
        'verdict':verdict,
        'years':years,
        'canonical_header_sha256':sha(json.dumps(canonical,separators=(',',':')).encode()),
        'gates':gates,
        'scientific_values_read':False,
        'label_values_read':False,
        'target_information_access':False,
        'excluded_target_interval_values_read':False,
        'structural_fields_examined':['archive bytes/hash','ZIP CRC/path/member identity','header','row count','row width'],
        'claim_boundary':'This gate establishes transport/schema compatibility only. No CAMSv3 2017/2018 data-column value or shower-label token was inspected, and no scientific detector score was computed.',
    }
    (args.output/'camsv3_2017_2018_structural_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'):
        raise SystemExit(1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
