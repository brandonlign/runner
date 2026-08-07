#!/usr/bin/env python3
"""Guarded execution transform for the frozen 2017/2019 score/label holdout."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ORIGINAL_GIT_BLOB = 'a4128e0620dcf1242fe90bb6758c96d46caf0119'

REPLACEMENTS = [
    ('"""Fresh target-excluded SonotaCo 2015/2017 validation of multiplicity ranking."""',
     '"""Locked score/label-unseen SonotaCo 2017/2019 validation of multiplicity ranking."""'),
    ('YEARS = (2015, 2017)', 'YEARS = (2017, 2019)'),
    ('CORPUS = "sonotaco-2015-2017-sparse-support-multiplicity-external"',
     'CORPUS = "sonotaco-2017-2019-sparse-support-multiplicity-score-label-holdout"'),
    ('ARCHIVE_URLS = {\n    2015: "https://sonotaco.jp/doc/SNMv3/015a.zip",\n    2017: "https://sonotaco.jp/doc/SNMv3/017a.zip",\n}',
     'ARCHIVE_URLS = {\n    2017: "https://www.astro.sk/iaumdcDB/PDA/SNMv3/017a.zip",\n    2019: "https://www.astro.sk/iaumdcDB/public/data/SNMv3/019a.zip",\n}'),
    ('EXPECTED_MEMBERS = {\n    2015: "015a/_U2_20150101_S.csv",\n    2017: "017a/_U2_20170101_S.csv",\n}',
     'EXPECTED_MEMBERS = {\n    2017: "017a/_U2_20170101_S.csv",\n    2019: "019a/_U2_20190101_S.csv",\n}'),
    ('PARSER_SHA256 = {\n    2015: "88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3",\n    2017: "bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3",\n}',
     'PARSER_SHA256 = {\n    2017: "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",\n    2019: "301a711e4de43566ba434f2d4a94fc38a85714a33dcee45e26cb19340101ea43",\n}'),
    ('p.add_argument("--parser-2015", required=True, type=Path)\n    p.add_argument("--parser-2017", required=True, type=Path)',
     'p.add_argument("--parser-2017", required=True, type=Path)\n    p.add_argument("--parser-2019", required=True, type=Path)'),
    ('parsed = function(archive_path, base, mapping_audit)',
     'parsed = function(archive_path, mapping_audit, base)'),
    ('require(sha256_file(args.parser_2015) == PARSER_SHA256[2015], "2015 parser hash changed")\n    require(sha256_file(args.parser_2017) == PARSER_SHA256[2017], "2017 parser hash changed")',
     'require(sha256_file(args.parser_2017) == PARSER_SHA256[2017], "2017 parser hash changed")\n    require(sha256_file(args.parser_2019) == PARSER_SHA256[2019], "2019 parser hash changed")'),
    ('parser_modules = {\n        2015: load_module(args.parser_2015, "orbittrace_frozen_sonotaco_2015_parser"),\n        2017: load_module(args.parser_2017, "orbittrace_frozen_sonotaco_2017_parser"),\n    }',
     'parser_modules = {\n        2017: load_module(args.parser_2017, "orbittrace_frozen_sonotaco_2017_parser"),\n        2019: load_module(args.parser_2019, "orbittrace_frozen_sonotaco_2019_parser"),\n    }'),
    ('# FIRST ACCESS TO THE FRESH SONOTACO 2015/2017 ARCHIVES.',
     '# FIRST SCIENTIFIC LABEL/SCORE ACCESS FOR THE LOCKED SONOTACO 2017/2019 HOLDOUT.'),
    ('"Fresh repo-history-unexposed SonotaCo 2015/2017 target-excluded external catalogue-ranking validation. "',
     '"Prospectively locked score/label-unseen SonotaCo 2017/2019 target-excluded external catalogue-ranking evaluation. "'),
    ('"# OrbitTrace multiplicity — fresh SonotaCo 2015/2017 external validation",',
     '"# OrbitTrace multiplicity — SonotaCo 2017/2019 locked score/label holdout",'),
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--original-runner', required=True, type=Path)
    known, rest = p.parse_known_args()
    source = known.original_runner.read_text()

    patched = source
    applied = []
    for old, new in REPLACEMENTS:
        count = patched.count(old)
        if count != 1:
            raise RuntimeError(f'expected exactly one frozen replacement occurrence, found {count}: {old[:100]!r}')
        patched = patched.replace(old, new)
        applied.append({'old': old, 'new': new})

    # Scientific constants/gates must remain byte-identical textually.
    required_unchanged = [
        'MIN_SUPPORTED_BINS = 24',
        'MIN_SCAN_EVENTS = 1000',
        'MIN_CALIBRATION_EVENTS = 1000',
        'MIN_QUALIFIED = 30',
        'MIN_HEAD = 30',
        'MIN_TAIL = 30',
        'DEVELOPMENT_FAMILIES = 197',
        'DEVELOPMENT_TOP_K = 100',
        '"calibration": 128',
        '"shortlist": 64',
        '"audit_shortlist": 128',
        '"min_anchor_count": 2',
        '"max_quartets_per_bin": 512',
        '"min_component_events": 4',
        '"min_component_quartets": 2',
        '"min_family_years": 2',
        '"family_link_radius": 1.5',
        'm_recovery >= b_recovery + 1',
        'm_recovery >= required_vs_fixed4',
        'float(metrics["multiplicity"]["topk_dominant_precision"]) >= 0.50',
        'required_vs_fixed4 = int(math.ceil(0.90 * f_recovery))',
        'k = (DEVELOPMENT_TOP_K * n_families + DEVELOPMENT_FAMILIES - 1) // DEVELOPMENT_FAMILIES',
    ]
    for token in required_unchanged:
        if source.count(token) != 1 or patched.count(token) != 1:
            raise RuntimeError(f'frozen scientific token changed/missing: {token}')

    if '2015' in patched or '015a' in patched:
        # No old panel identifier may survive into execution.
        raise RuntimeError('old 2015 panel identifier survived guarded transform')

    out = Path('/tmp/orbittrace_sonotaco_2017_2019_scoreholdout.py')
    out.write_text(patched)
    compile(patched, str(out), 'exec')
    audit = Path('output/score_label_holdout_transform_audit.txt')
    audit.parent.mkdir(exist_ok=True)
    audit.write_text(
        f'original_sha256={sha256_bytes(source.encode())}\n'
        f'patched_sha256={sha256_bytes(patched.encode())}\n'
        f'replacement_count={len(applied)}\n'
        'scientific_gate_change=false\n'
        'target_information_access=false\n'
    )
    print('PASS_2017_2019_SCORE_LABEL_HOLDOUT_GUARDED_TRANSFORM', flush=True)
    os.execv(sys.executable, [sys.executable, str(out), *rest])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
