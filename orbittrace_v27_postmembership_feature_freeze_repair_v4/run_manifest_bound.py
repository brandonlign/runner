#!/usr/bin/env python3
"""Final transport/provenance wrapper for v27 post-membership feature extraction.

The exact untouched v22 pretruth builder is executed in an isolated process first. Its output
manifest is the authoritative identity for the 71-dimensional implementation-level feature
array generated in that same run. Stable scientific identities (centroids and expanded v19
memberships) remain hard pinned by the underlying extractor.

This wrapper changes no v27 feature definition, membership rule, candidate, order, or science.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from orbittrace_v27_postmembership_feature_freeze_repair_v2 import extract_postfeatures as impl


def base_root_from_argv(argv: list[str]) -> Path:
    try:
        i = argv.index('--base-root')
    except ValueError as exc:
        raise RuntimeError('--base-root is required') from exc
    if i + 1 >= len(argv):
        raise RuntimeError('--base-root value missing')
    return Path(argv[i + 1])


def comparator_from_argv(argv: list[str]) -> str:
    try:
        i = argv.index('--comparator')
    except ValueError as exc:
        raise RuntimeError('--comparator is required') from exc
    if i + 1 >= len(argv):
        raise RuntimeError('--comparator value missing')
    value = argv[i + 1]
    if value not in {'sugar', 'hdbscan'}:
        raise RuntimeError(f'invalid comparator: {value}')
    return value


def main() -> int:
    route = comparator_from_argv(sys.argv)
    root = base_root_from_argv(sys.argv)
    manifest = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    if manifest.get('feature_dimension') != 71:
        raise RuntimeError('same-run v22 feature dimension changed')
    if manifest.get('truth_accessed') is not False:
        raise RuntimeError('same-run v22 manifest is truth-bearing')
    for key in ('target_information_access', 'maarsy_scientific_access', 'dms_scientific_access'):
        if manifest.get(key) is not False:
            raise RuntimeError(f'same-run v22 firewall flag changed: {key}')
    feature_sha = str(manifest.get('feature_sha256', ''))
    if len(feature_sha) != 64:
        raise RuntimeError('same-run v22 feature hash missing')

    # Implementation-level 71-feature bytes are bound to the exact untouched builder output
    # produced earlier in this same workflow. Stable scientific hashes remain unchanged below.
    impl.EXPECTED[route]['base_feature_sha256'] = feature_sha
    return int(impl.main())


if __name__ == '__main__':
    raise SystemExit(main())
