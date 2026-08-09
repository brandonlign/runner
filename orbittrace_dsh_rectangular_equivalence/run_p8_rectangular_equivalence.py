#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_dsh_rectangular_equivalence.rectangular_dsh import rectangular_pairwise_dsh

EXPECTED_P8_SOURCE = Path('/tmp/run_p8.py')


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
    positions = {'id': exact('Unique trajectory'),'sol': exact('Sol lon'),'q': exact('q'),'e': exact('e'),'i': exact('i'),'peri': exact('peri'),'node': exact('node')}
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == 'Q']
    require(len(q_upper) == 1 and q_upper[0] != positions['q'], 'q/Q schema identity changed')
    return fields, positions


def load_p8() -> Any:
    require(EXPECTED_P8_SOURCE.is_file(), f'P8 runtime missing: {EXPECTED_P8_SOURCE}')
    spec = importlib.util.spec_from_file_location('orbittrace_p8_rect_equiv_runtime', EXPECTED_P8_SOURCE)
    require(spec is not None and spec.loader is not None, 'cannot load P8 runtime')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def accelerated_min_exact_dsh_to_source_factory(module: Any):
    def accelerated_min_exact_dsh_to_source(event_ids: list[str], source_seed_ids: list[str], orbit_by_id: dict[str, dict[str, float]], dsh: Any) -> np.ndarray:
        # `dsh` is intentionally accepted for signature identity but the exact frozen
        # formula has already been audited into rectangular_pairwise_dsh.
        del dsh
        require(bool(source_seed_ids), 'empty source orbit set')
        require(all(eid in orbit_by_id for eid in source_seed_ids), 'source seed missing valid orbit')
        require(all(eid in orbit_by_id for eid in event_ids), 'candidate event missing valid orbit')
        source = [orbit_by_id[eid] for eid in source_seed_ids]
        right = {
            'q': np.asarray([o['q'] for o in source], dtype=np.float64),
            'e': np.asarray([o['e'] for o in source], dtype=np.float64),
            'i': np.asarray([o['i'] for o in source], dtype=np.float64),
            'peri': np.asarray([o['peri'] for o in source], dtype=np.float64),
            'node': np.asarray([o['node'] for o in source], dtype=np.float64),
        }
        result = np.empty(len(event_ids), dtype=np.float64)
        batch_size = int(module.DSH_BATCH_SIZE)
        require(batch_size > 0, 'invalid inherited DSH batch size')
        for start in range(0, len(event_ids), batch_size):
            ids = event_ids[start:start + batch_size]
            candidate = [orbit_by_id[eid] for eid in ids]
            left = {
                'q': np.asarray([o['q'] for o in candidate], dtype=np.float64),
                'e': np.asarray([o['e'] for o in candidate], dtype=np.float64),
                'i': np.asarray([o['i'] for o in candidate], dtype=np.float64),
                'peri': np.asarray([o['peri'] for o in candidate], dtype=np.float64),
                'node': np.asarray([o['node'] for o in candidate], dtype=np.float64),
            }
            cross = rectangular_pairwise_dsh(left, right)
            b = len(candidate)
            require(cross.shape == (b, len(source)), 'rectangular D_SH cross shape changed')
            result[start:start + b] = np.min(cross, axis=1)
        require(np.all(np.isfinite(result)), 'non-finite D_SH feature')
        return result
    return accelerated_min_exact_dsh_to_source


def self_test() -> None:
    names=['Unique trajectory','Beginning','Beginning','IAU','IAU','Sol lon','App LST','RAgeo','+/-','DECgeo','+/-','LAMgeo','+/-','BETgeo','+/-','Vgeo','+/-','LAMhel','+/-','BEThel','+/-','Vhel','+/-','a','+/-','e','+/-','i','+/-','peri','+/-','node','+/-','Pi','+/-','b','+/-','q','+/-','f','+/-','M','+/-','Q']
    expected={'id':0,'sol':5,'q':37,'e':25,'i':27,'peri':29,'node':31}
    for prefix in ('# ','#  ','\ufeff#  ',' \t#\t'):
        fields,positions=compatible_exact_header_positions(prefix+';'.join(names)+'\nrow;ignored')
        require(fields==names,'header normalization changed fields')
        require(positions==expected,f'header normalization changed positions: {positions}')
    print('PASS_P8_RECTANGULAR_FULL_EQUIVALENCE_WRAPPER_SELF_TEST')


def main() -> int:
    self_test()
    module=load_p8()
    module.exact_header_positions=compatible_exact_header_positions
    module.min_exact_dsh_to_source=accelerated_min_exact_dsh_to_source_factory(module)
    print(f'P8_RECTANGULAR_EQUIVALENCE_DSH_BATCH_SIZE={module.DSH_BATCH_SIZE}', flush=True)
    return int(module.main())


if __name__=='__main__':
    raise SystemExit(main())
