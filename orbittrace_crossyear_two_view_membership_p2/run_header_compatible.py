#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

EXPECTED_CANONICAL_SOURCE = Path('/tmp/run_p2_canonical_v2.py')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def compatible_exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    """Parse the same exact GMN field names while tolerating comment-line whitespace only."""
    candidates: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.lstrip('\ufeff \t')
        if not line.startswith('#'):
            continue
        body = line[1:].strip()
        fields = [field.strip() for field in body.split(';')]
        if fields and fields[0] == 'Unique trajectory':
            candidates.append(fields)
    require(len(candidates) == 1, f'raw schema header not unique after whitespace normalization: {len(candidates)}')
    fields = candidates[0]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f'raw schema field {name!r} not unique: {hits}')
        return hits[0]

    positions = {
        'id': exact('Unique trajectory'),
        'sol': exact('Sol lon'),
        'q': exact('q'),
        'e': exact('e'),
        'i': exact('i'),
        'peri': exact('peri'),
        'node': exact('node'),
    }
    require(len(set(positions.values())) == len(positions), f'raw schema positions overlap: {positions}')
    q_upper = [idx for idx, field in enumerate(fields) if field == 'Q']
    require(len(q_upper) == 1 and q_upper[0] != positions['q'], 'q/Q schema identity changed')
    return fields, positions


def load_canonical() -> Any:
    require(EXPECTED_CANONICAL_SOURCE.is_file(), 'canonical P2 runtime missing')
    spec = importlib.util.spec_from_file_location('orbittrace_p2_canonical_v2_header_recovery', EXPECTED_CANONICAL_SOURCE)
    require(spec is not None and spec.loader is not None, 'cannot import canonical P2 runtime')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def self_test() -> None:
    canonical = '# Unique trajectory; Sol lon; q; Q; e; i; peri; node; extra\n'
    variants = (
        canonical,
        '   # Unique trajectory; Sol lon; q; Q; e; i; peri; node; extra\n',
        '#   Unique trajectory; Sol lon; q; Q; e; i; peri; node; extra\n',
        '\ufeff  #  Unique trajectory ; Sol lon ; q ; Q ; e ; i ; peri ; node ; extra\n',
    )
    expected = {'id': 0, 'sol': 1, 'q': 2, 'e': 4, 'i': 5, 'peri': 6, 'node': 7}
    for text in variants:
        fields, positions = compatible_exact_header_positions(text)
        require(positions == expected, f'header compatibility self-test positions changed: {positions}')
        require(fields[2] == 'q' and fields[3] == 'Q', 'q/Q self-test identity changed')

    # Reject only changes to the required scientific schema contract. Unrelated
    # extra columns are scientifically inert and are intentionally permitted by
    # the canonical position-based parser as long as all required names remain
    # unique and q/Q remain distinct.
    for bad in (
        '# Unique trajectory; Sol lon; q; e; i; peri; node\n',
        '# Unique trajectory; Sol lon; q; Q; e; i; peri; node\n# Unique trajectory; Sol lon; q; Q; e; i; peri; node\n',
        '# Unique trajectory; Sol lon; q; Q; e; i; peri; node; q\n',
    ):
        try:
            compatible_exact_header_positions(bad)
        except RuntimeError:
            pass
        else:
            raise RuntimeError('header compatibility self-test accepted a changed required schema')


def main() -> int:
    self_test()
    module = load_canonical()
    original = module.exact_header_positions
    # The only runtime substitution is comment/header whitespace normalization.
    module.exact_header_positions = compatible_exact_header_positions
    try:
        return int(module.main())
    finally:
        module.exact_header_positions = original


if __name__ == '__main__':
    raise SystemExit(main())
