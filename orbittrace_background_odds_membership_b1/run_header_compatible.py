#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

B1_SOURCE=Path(__file__).with_name('run_development.py')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def compatible_exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    candidates: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.lstrip('\ufeff \t')
        if not line.startswith('#'):
            continue
        body = line[1:].strip()
        fields = [field.strip() for field in body.split(';')]
        if fields and fields[0] == 'Unique trajectory':
            candidates.append(fields)
    require(len(candidates) == 1, f"raw schema header not unique after whitespace normalization: {len(candidates)}")
    fields = candidates[0]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f"raw schema field {name!r} not unique: {hits}")
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
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == 'Q']
    require(len(q_upper) == 1 and q_upper[0] != positions['q'], 'q/Q schema identity changed')
    return fields, positions


def self_test() -> None:
    names = ['Unique trajectory','Beginning','Beginning','IAU','IAU','Sol lon','App LST','RAgeo','+/-','DECgeo','+/-','LAMgeo','+/-','BETgeo','+/-','Vgeo','+/-','LAMhel','+/-','BEThel','+/-','Vhel','+/-','a','+/-','e','+/-','i','+/-','peri','+/-','node','+/-','Pi','+/-','b','+/-','q','+/-','f','+/-','M','+/-','Q']
    expected = {'id':0,'sol':5,'q':37,'e':25,'i':27,'peri':29,'node':31}
    for prefix in ('# ', '#  ', '\ufeff#  ', ' \t#\t'):
        fields, positions = compatible_exact_header_positions(prefix + ';'.join(names) + '\nrow;ignored')
        require(fields == names, 'header whitespace normalization changed fields')
        require(positions == expected, f'header whitespace normalization changed positions: {positions}')
    print('PASS_B1_P10_HEADER_WHITESPACE_COMPAT_SELF_TEST')


def load_b1() -> Any:
    require(B1_SOURCE.is_file(), f'frozen B1 source missing: {B1_SOURCE}')
    spec=importlib.util.spec_from_file_location('orbittrace_b1_frozen_runtime',B1_SOURCE)
    require(spec is not None and spec.loader is not None,'cannot load frozen B1 runtime')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    self_test()
    b1=load_b1()
    b1.raw_header_positions=compatible_exact_header_positions
    print('PASS_B1_PREEXISTING_P10_HEADER_SCHEMA_TRANSPORT_ACTIVE')
    return int(b1.main())


if __name__=='__main__':
    raise SystemExit(main())
