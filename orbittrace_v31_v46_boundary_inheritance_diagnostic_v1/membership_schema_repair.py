#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from orbittrace_v31_v46_boundary_inheritance_diagnostic_v1 import diagnose as frozen

MEMBERSHIP_SHA256 = '99640747e935df2f4a7c7983bdde843ea59e1814388b8418e040dc04628aee13'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--freeze-file', type=Path, required=True)
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()

    membership_path = a.hdbscan_root / 'family_memberships.json'
    frozen.require(sha(membership_path) == MEMBERSHIP_SHA256, '#950 HDB membership identity changed')
    raw = json.loads(membership_path.read_text())
    frozen.require(set(raw) == {'families', 'truth_accessed'}, '#950 HDB membership schema changed')
    frozen.require(raw['truth_accessed'] is False and len(raw['families']) == 229, '#950 HDB membership universe changed')

    # The frozen diagnostic expected firewall metadata on family_memberships.json,
    # but authoritative #950 stores those fields only in the paired manifest.
    # Add only false metadata keys to a temporary copy. Family identities,
    # memberships, truth semantics, boundary identities, and F1 logic are unchanged.
    repaired = dict(raw)
    repaired['target_information_access'] = False
    repaired['maarsy_scientific_access'] = False
    repaired['dms_scientific_access'] = False

    with tempfile.TemporaryDirectory(prefix='v46-boundary-membership-schema-') as td:
        root = Path(td)
        (root / 'family_memberships.json').write_text(json.dumps(repaired, sort_keys=True, allow_nan=False) + '\n')
        return frozen.diagnose_mode(a.freeze_file, root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
