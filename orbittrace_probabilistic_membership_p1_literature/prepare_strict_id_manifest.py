#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

YEARS = (2023, 2025)
BLIND_EXCLUSION = (20.0, 55.0)
HDBSCAN_SHA256 = {
    2023: '35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',
    2025: '8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3',
}
SUGAR_SHA256 = {
    2023: '2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',
    2025: '77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e',
}
EXPECTED_COUNTS = {
    'hdbscan': {2023: 26460, 2025: 19658},
    'sugar': {2023: 30414, 2025: 23200},
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def hdbscan_ids_only(path: Path, year: int) -> list[str]:
    """Extract only the event-id token from each JSONL row; never JSON-decode any other field."""
    require(sha256_file(path) == HDBSCAN_SHA256[year], f'HDBSCAN {year} artifact hash changed')
    text = gzip.decompress(path.read_bytes()).decode('utf-8')
    lines = text.splitlines()
    pattern = re.compile(r'"(?:event_id|id)"\s*:\s*"(SNM' + str(year) + r':\d+)"')
    out: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        hits = pattern.findall(line)
        require(len(hits) == 1, f'HDBSCAN {year} event-id token not unique line {line_number}')
        out.append(hits[0])
    require(len(out) == EXPECTED_COUNTS['hdbscan'][year], f'HDBSCAN {year} row count changed')
    require(len(out) == len(set(out)), f'HDBSCAN {year} duplicate event IDs')
    return out


def extract_json_array_for_key_without_parsing_rest(text: str, key: str) -> Any:
    """Decode exactly one JSON value beginning after key; later object values remain unparsed."""
    token = json.dumps(key)
    require(text.count(token) == 1, f'JSON key {key!r} not unique')
    start = text.index(token) + len(token)
    while start < len(text) and text[start].isspace():
        start += 1
    require(start < len(text) and text[start] == ':', f'missing colon after {key}')
    start += 1
    while start < len(text) and text[start].isspace():
        start += 1
    value, _end = json.JSONDecoder().raw_decode(text, start)
    return value


def sugar_ids_only(path: Path, year: int) -> list[str]:
    """Decode only the event_ids JSON array; no other object value is decoded or inspected."""
    require(sha256_file(path) == SUGAR_SHA256[year], f'Sugar {year} artifact hash changed')
    text = gzip.decompress(path.read_bytes()).decode('utf-8')
    raw_ids = extract_json_array_for_key_without_parsing_rest(text, 'event_ids')
    require(isinstance(raw_ids, list), f'Sugar {year} event_ids is not an array')
    out = [str(x) for x in raw_ids]
    require(len(out) == EXPECTED_COUNTS['sugar'][year], f'Sugar {year} row count changed')
    require(len(out) == len(set(out)), f'Sugar {year} duplicate event IDs')
    require(all(x.startswith(f'SNM{year}:') for x in out), f'Sugar {year} wrong-year event ID')
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--hdbscan-2023', required=True, type=Path)
    p.add_argument('--hdbscan-2025', required=True, type=Path)
    p.add_argument('--sugar-2023', required=True, type=Path)
    p.add_argument('--sugar-2025', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()

    paths = {
        'hdbscan': {2023: args.hdbscan_2023, 2025: args.hdbscan_2025},
        'sugar': {2023: args.sugar_2023, 2025: args.sugar_2025},
    }
    panels: dict[str, dict[str, Any]] = {'hdbscan': {}, 'sugar': {}}
    for year in YEARS:
        hids = hdbscan_ids_only(paths['hdbscan'][year], year)
        sids = sugar_ids_only(paths['sugar'][year], year)
        panels['hdbscan'][str(year)] = {'scan_ids': hids, 'scan_count': len(hids)}
        panels['sugar'][str(year)] = {'scan_ids': sids, 'scan_count': len(sids)}

    payload = {
        'classification': 'P1 matched-literature strict pretruth ID-only manifest',
        'years': list(YEARS),
        'blind_exclusion': list(BLIND_EXCLUSION),
        'competitor_cluster_values_parsed': False,
        'known_shower_truth_values_parsed': False,
        'native_shower_tokens_parsed': False,
        'panels': panels,
        'input_hashes': {
            'hdbscan_2023': sha256_file(args.hdbscan_2023),
            'hdbscan_2025': sha256_file(args.hdbscan_2025),
            'sugar_2023': sha256_file(args.sugar_2023),
            'sugar_2025': sha256_file(args.sugar_2025),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    args.output.with_suffix(args.output.suffix + '.sha256').write_text(canonical_sha(payload) + '\n')
    print('PASS_P1_STRICT_PRETRUTH_ID_ONLY_MANIFEST')
    print('manifest_sha256', canonical_sha(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
