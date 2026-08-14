#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

FROZEN_SCIENCE_BLOB = 'a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
ENGINEERING_WRAPPER_BLOB = '8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
QUALITY_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_SHA = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
YEAR = 2022
BLIND = (20.0, 55.0)


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def load(path: Path, name: str, expected_blob: str | None = None) -> Any:
    if expected_blob is not None:
        req(git_blob_sha(path) == expected_blob, f'{name} blob changed')
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def atom_equal(a: Any, b: Any) -> bool:
    return bool(
        a.aid == b.aid
        and int(a.bin_index) == int(b.bin_index)
        and float(a.center) == float(b.center)
        and tuple(a.members) == tuple(b.members)
        and np.array_equal(np.asarray(a.u), np.asarray(b.u))
        and float(a.logv) == float(b.logv)
        and float(a.medoid_residual) == float(b.medoid_residual)
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--frozen-source', type=Path, required=True)
    p.add_argument('--engineering-wrapper', type=Path, required=True)
    p.add_argument('--quality-source', type=Path, required=True)
    p.add_argument('--support-source-parts', type=Path, required=True)
    p.add_argument('--candidate-payload', type=Path, required=True)
    p.add_argument('--baseline-payload', type=Path, required=True)
    p.add_argument('--scorer-parts', type=Path, required=True)
    p.add_argument('--v8-result-json', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(a.frozen_source) == FROZEN_SCIENCE_BLOB, 'frozen science changed')
    req(git_blob_sha(a.engineering_wrapper) == ENGINEERING_WRAPPER_BLOB, 'engineering wrapper changed')
    req(sha256(a.quality_source) == QUALITY_SHA, '#839 utility changed')
    req(sha256(a.v8_result_json) == V8_SHA, 'v8 runtime support changed')

    mod = load(a.frozen_source, 'rft_equivalence_frozen', FROZEN_SCIENCE_BLOB)
    wrapper = load(a.engineering_wrapper, 'rft_equivalence_wrapper', ENGINEERING_WRAPPER_BLOB)
    req(str(getattr(wrapper, 'FROZEN_SCIENCE_BLOB_SHA', '')) == FROZEN_SCIENCE_BLOB, 'wrapper science pin changed')

    qmod = mod.load_module(a.quality_source, 'rft_equivalence_839')
    qmod.v1.mult.YEARS = mod.YEARS
    qmod.v1.mult.MONTH_KEYS = mod.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = mod.YEARS
    support.MONTH_KEYS = mod.MONTH_KEYS
    support.CORPUS = 'orbittrace-rft-v1-batched-kd-equivalence-audit'
    support.RANKING_VARIANTS = ('persistence',)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, 'target firewall changed')
    setattr(a, 'fixed4_baseline_json', a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, _hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == [YEAR], f'wrong years loaded: {sorted(scan)}')
    req([x['key'] for x in sources] == list(mod.MONTH_KEYS), 'source months changed')

    raw = list(scan[YEAR])
    events = [mod.normalize_event(row) for row in raw]
    req(len(events) == len(raw), 'normalization changed event count')
    req(all(str(e['id']).startswith(str(YEAR)) for e in events), 'non-2022 event reached audit')
    req(all(not (BLIND[0] <= float(e['sol']) <= BLIND[1]) for e in events), 'protected event reached audit')

    by_bin: dict[int, list[dict[str, Any]]] = mod.defaultdict(list)
    for e in events:
        idx = int(math.floor((e['coord'] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[idx].append(e)

    frozen_atoms = mod.atoms
    original_unit = mod.unit
    original_pair_d = mod.pair_d
    unit_cache: dict[tuple[float, float], np.ndarray] = {}
    pair_cache: dict[tuple[int, int], float] = {}
    pair_calls = 0
    pair_original = 0

    def cached_unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
        lon = np.asarray(lon_deg)
        lat = np.asarray(lat_deg)
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == 1 and len(lat) == 1:
            key = (float(lon[0]), float(lat[0]))
            cached = unit_cache.get(key)
            if cached is not None:
                return cached.reshape(1, 3)
            out = original_unit(lon, lat)
            unit_cache[key] = out[0].copy()
            return out
        out = original_unit(lon, lat)
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == len(lat) == len(out):
            for lo, la, row in zip(lon, lat, out):
                unit_cache[(float(lo), float(la))] = row.copy()
        return out

    def memo_pair_d(x: dict[str, Any], y: dict[str, Any]) -> float:
        nonlocal pair_calls, pair_original
        pair_calls += 1
        key = (id(x), id(y))
        if key in pair_cache:
            return pair_cache[key]
        pair_original += 1
        value = original_pair_d(x, y)
        pair_cache[key] = value
        return value

    mod.unit = cached_unit
    mod.pair_d = memo_pair_d

    bin_reports: list[dict[str, Any]] = []
    total_scalar_queries = 0
    total_atoms = 0
    started = time.monotonic()
    try:
        for ordinal, bidx in enumerate(sorted(by_bin), start=1):
            rows = by_bin[bidx]
            if len(rows) < mod.MIN_ATOM:
                bin_reports.append({'bin_index': bidx, 'rows': len(rows), 'skipped_small_bin': True, 'atoms': 0})
                continue

            lon = np.asarray([r['lon'] for r in rows], float)
            lat = np.asarray([r['lat'] for r in rows], float)
            vg = np.asarray([r['vg'] for r in rows], float)
            uv = mod.unit(lon, lat)
            transformed = np.column_stack((
                uv / (2.0 * math.sin(math.radians(3.0) / 2.0)),
                np.log(vg) / math.log(1.08),
            ))
            tree = mod.cKDTree(transformed)
            bulk = tree.query_ball_point(transformed, r=1.02)
            req(len(bulk) == len(rows), f'bulk candidate count mismatch bin {bidx}')
            candidate_links = 0
            for i in range(len(rows)):
                scalar = tree.query_ball_point(transformed[i], r=1.02)
                total_scalar_queries += 1
                req(set(map(int, scalar)) == set(map(int, bulk[i])), f'KD candidate-set mismatch bin {bidx} row {i}')
                candidate_links += len(scalar)

            before_calls = pair_calls
            before_original = pair_original
            t0 = time.monotonic()
            scalar_atoms = frozen_atoms(rows)
            scalar_seconds = time.monotonic() - t0
            t1 = time.monotonic()
            batch_atoms = wrapper._accelerated_atoms(mod, rows)
            batch_seconds = time.monotonic() - t1
            req(len(scalar_atoms) == len(batch_atoms), f'atom count mismatch bin {bidx}')
            for j, (fa, ba) in enumerate(zip(scalar_atoms, batch_atoms)):
                req(atom_equal(fa, ba), f'atom mismatch bin {bidx} index {j} aid={fa.aid}/{ba.aid}')

            total_atoms += len(scalar_atoms)
            report = {
                'bin_index': bidx,
                'rows': len(rows),
                'skipped_small_bin': False,
                'candidate_links_including_self': candidate_links,
                'atoms': len(scalar_atoms),
                'scalar_seconds': scalar_seconds,
                'batched_seconds_with_shared_exact_pair_cache': batch_seconds,
                'pair_d_calls_delta': pair_calls - before_calls,
                'pair_d_original_evaluations_delta': pair_original - before_original,
            }
            bin_reports.append(report)
            print({'RFT_BATCH_EQUIVALENCE_BIN': ordinal, 'of': len(by_bin), **report}, flush=True)
    finally:
        mod.unit = original_unit
        mod.pair_d = original_pair_d

    result = {
        'verdict': 'PASS_RFT_V1_BATCHED_KD_ATOM_EQUIVALENCE',
        'role': 'ENGINEERING_IDENTITY_AUDIT_ONLY',
        'year': YEAR,
        'events': len(events),
        'source_month_count': len(sources),
        'bin_count': len(by_bin),
        'atom_count': total_atoms,
        'scalar_kdtree_queries_audited': total_scalar_queries,
        'pair_d_calls': pair_calls,
        'pair_d_original_evaluations': pair_original,
        'pair_d_cache_hits': pair_calls - pair_original,
        'elapsed_seconds': time.monotonic() - started,
        'all_kdtree_candidate_sets_exact': True,
        'all_atom_fields_exact': True,
        'scientific_endpoint_computed': False,
        'tube_construction_computed': False,
        'perturbation_persistence_computed': False,
        'shower_recovery_metric_computed': False,
        'candidate_score_computed': False,
        'labels_used_in_computed_quantity': False,
        'blind_exclusion': [20.0, 55.0],
        'gmn_2023_access': False,
        'sonotaco_2013_2014_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'frozen_science_blob': FROZEN_SCIENCE_BLOB,
        'engineering_wrapper_blob': ENGINEERING_WRAPPER_BLOB,
        'quality_sha256': sha256(a.quality_source),
        'v8_sha256': sha256(a.v8_result_json),
        'bins': bin_reports,
    }
    out = a.output / 'RFT_V1_BATCHED_KD_EQUIVALENCE.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bins'}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
