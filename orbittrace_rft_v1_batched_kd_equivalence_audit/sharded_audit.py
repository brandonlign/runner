#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

FROZEN_SCIENCE_BLOB = 'a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
ENGINEERING_WRAPPER_BLOB = '8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
QUALITY_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_SHA = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
YEAR = 2022
BLIND = (20.0, 55.0)
SHARDS = 8


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


def write_gz(path: Path, obj: Any) -> None:
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as handle:
        json.dump(obj, handle, sort_keys=True, separators=(',', ':'), allow_nan=False)


def read_gz(path: Path) -> Any:
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        return json.load(handle)


def bin_index(mod: Any, event: dict[str, Any]) -> int:
    return int(math.floor((float(event['coord']) - mod.BLIND[1]) / mod.BIN_WIDTH))


def balanced_assignment(mod: Any, events: list[dict[str, Any]]) -> tuple[list[list[int]], list[int], dict[int, int]]:
    counts = Counter(bin_index(mod, event) for event in events)
    loads = [0 for _ in range(SHARDS)]
    bins: list[list[int]] = [[] for _ in range(SHARDS)]
    for bidx, count in sorted(counts.items(), key=lambda item: (-(item[1] ** 2), item[0])):
        shard = min(range(SHARDS), key=lambda s: (loads[s], s))
        bins[shard].append(int(bidx))
        loads[shard] += int(count) ** 2
    for row in bins:
        row.sort()
    return bins, loads, dict(counts)


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


def parse_exact_events(args: argparse.Namespace) -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]:
    req(git_blob_sha(args.frozen_source) == FROZEN_SCIENCE_BLOB, 'frozen science changed')
    req(sha256(args.quality_source) == QUALITY_SHA, '#839 utility changed')
    req(sha256(args.v8_result_json) == V8_SHA, 'v8 runtime support changed')
    mod = load(args.frozen_source, 'rft_sharded_equiv_frozen', FROZEN_SCIENCE_BLOB)
    qmod = mod.load_module(args.quality_source, 'rft_sharded_equiv_839')
    qmod.v1.mult.YEARS = mod.YEARS
    qmod.v1.mult.MONTH_KEYS = mod.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = mod.YEARS
    support.MONTH_KEYS = mod.MONTH_KEYS
    support.CORPUS = 'orbittrace-rft-v1-sharded-batched-kd-equivalence'
    support.RANKING_VARIANTS = ('persistence',)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, 'target firewall changed')
    setattr(args, 'fixed4_baseline_json', args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _cal, _hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == [YEAR], f'wrong years loaded: {sorted(scan)}')
    req([row['key'] for row in sources] == list(mod.MONTH_KEYS), 'source months changed')
    raw = list(scan[YEAR])
    events = [mod.normalize_event(row) for row in raw]
    req(len(events) == len(raw), 'normalization changed event count')
    req(all(str(event['id']).startswith(str(YEAR)) for event in events), 'non-2022 event reached audit')
    req(all(not (BLIND[0] <= float(event['sol']) <= BLIND[1]) for event in events), 'protected event reached audit')
    req(len({str(event['id']) for event in events}) == len(events), 'duplicate normalized event id')
    return mod, events, sources


def cmd_prepare(args: argparse.Namespace) -> int:
    args.output.mkdir(parents=True, exist_ok=True)
    mod, events, sources = parse_exact_events(args)
    bins, loads, counts = balanced_assignment(mod, events)
    covered = sorted(b for row in bins for b in row)
    req(len(covered) == len(set(covered)) == len(counts), 'bin assignment is not exact')
    req(covered == sorted(counts), 'bin assignment misses a bin')
    assignment = {
        'role': 'RFT_V1_SHARDED_BATCHED_KD_EQUIVALENCE_EXECUTION_ONLY',
        'year': YEAR,
        'events': len(events),
        'source_month_count': len(sources),
        'shards': SHARDS,
        'shard_bins': bins,
        'shard_n2_loads': loads,
        'bin_counts': {str(k): int(v) for k, v in sorted(counts.items())},
        'all_bins': covered,
        'blind_exclusion': [20.0, 55.0],
        'scientific_endpoint_computed': False,
        'labels_used_in_computed_quantity': False,
        'gmn_2023_access': False,
        'sonotaco_2013_2014_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    write_gz(args.output / 'events.json.gz', events)
    (args.output / 'assignment.json').write_text(json.dumps(assignment, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in assignment.items() if k not in ('bin_counts', 'shard_bins', 'all_bins')}, indent=2, sort_keys=True))
    print('shard_bin_counts', [len(row) for row in bins])
    return 0


def compare_one_bin(mod: Any, wrapper: Any, rows: list[dict[str, Any]], bidx: int) -> dict[str, Any]:
    if len(rows) < mod.MIN_ATOM:
        return {
            'bin_index': bidx,
            'rows': len(rows),
            'skipped_small_bin': True,
            'scalar_kdtree_queries_audited': 0,
            'atoms': 0,
            'exact': True,
            'elapsed_seconds': 0.0,
        }

    lon = np.asarray([row['lon'] for row in rows], dtype=float)
    lat = np.asarray([row['lat'] for row in rows], dtype=float)
    vg = np.asarray([row['vg'] for row in rows], dtype=float)
    uv = mod.unit(lon, lat)
    transformed = np.column_stack((
        uv / (2.0 * math.sin(math.radians(3.0) / 2.0)),
        np.log(vg) / math.log(1.08),
    ))
    tree = mod.cKDTree(transformed)
    bulk = tree.query_ball_point(transformed, r=1.02)
    req(len(bulk) == len(rows), f'batched candidate count mismatch bin {bidx}')
    for i in range(len(rows)):
        scalar = tree.query_ball_point(transformed[i], r=1.02)
        req(set(map(int, scalar)) == set(map(int, bulk[i])), f'KD candidate set mismatch bin {bidx} row {i}')

    frozen_atoms = mod.atoms
    original_unit = mod.unit
    original_pair = mod.pair_d
    unit_cache: dict[tuple[float, float], np.ndarray] = {}
    pair_cache: dict[tuple[int, int], float] = {}
    pair_calls = 0
    pair_original = 0

    def cached_unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
        lon_arr = np.asarray(lon_deg)
        lat_arr = np.asarray(lat_deg)
        if lon_arr.ndim == 1 and lat_arr.ndim == 1 and len(lon_arr) == len(lat_arr) == 1:
            key = (float(lon_arr[0]), float(lat_arr[0]))
            existing = unit_cache.get(key)
            if existing is not None:
                return existing.reshape(1, 3)
            out = original_unit(lon_arr, lat_arr)
            unit_cache[key] = out[0].copy()
            return out
        out = original_unit(lon_arr, lat_arr)
        if lon_arr.ndim == 1 and lat_arr.ndim == 1 and len(lon_arr) == len(lat_arr) == len(out):
            for lo, la, vector in zip(lon_arr, lat_arr, out):
                unit_cache[(float(lo), float(la))] = vector.copy()
        return out

    def memo_pair(x: dict[str, Any], y: dict[str, Any]) -> float:
        nonlocal pair_calls, pair_original
        pair_calls += 1
        key = (id(x), id(y))
        if key in pair_cache:
            return pair_cache[key]
        pair_original += 1
        value = original_pair(x, y)
        pair_cache[key] = value
        return value

    mod.unit = cached_unit
    mod.pair_d = memo_pair
    started = time.monotonic()
    try:
        scalar_atoms = frozen_atoms(rows)
        batch_atoms = wrapper._accelerated_atoms(mod, rows)
    finally:
        mod.unit = original_unit
        mod.pair_d = original_pair
    req(len(scalar_atoms) == len(batch_atoms), f'atom count mismatch bin {bidx}')
    for index, (scalar_atom, batch_atom) in enumerate(zip(scalar_atoms, batch_atoms)):
        req(atom_equal(scalar_atom, batch_atom), f'atom field mismatch bin {bidx} index {index}')
    return {
        'bin_index': bidx,
        'rows': len(rows),
        'skipped_small_bin': False,
        'scalar_kdtree_queries_audited': len(rows),
        'atoms': len(scalar_atoms),
        'pair_d_calls': pair_calls,
        'pair_d_original_evaluations': pair_original,
        'pair_d_cache_hits': pair_calls - pair_original,
        'exact': True,
        'elapsed_seconds': time.monotonic() - started,
    }


def cmd_shard(args: argparse.Namespace) -> int:
    req(0 <= args.shard < SHARDS, 'invalid shard')
    args.output.mkdir(parents=True, exist_ok=True)
    req(git_blob_sha(args.frozen_source) == FROZEN_SCIENCE_BLOB, 'frozen science changed')
    req(git_blob_sha(args.engineering_wrapper) == ENGINEERING_WRAPPER_BLOB, 'engineering wrapper changed')
    mod = load(args.frozen_source, 'rft_sharded_equiv_compare_frozen', FROZEN_SCIENCE_BLOB)
    wrapper = load(args.engineering_wrapper, 'rft_sharded_equiv_compare_wrapper', ENGINEERING_WRAPPER_BLOB)
    events = read_gz(args.events)
    assignment = json.loads(args.assignment.read_text())
    req(int(assignment['shards']) == SHARDS, 'shard count changed')
    expected_bins = list(map(int, assignment['shard_bins'][args.shard]))
    expected_counts = {int(k): int(v) for k, v in assignment['bin_counts'].items()}
    by_bin: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        bidx = bin_index(mod, event)
        if bidx in expected_bins:
            by_bin.setdefault(bidx, []).append(event)
    req(sorted(by_bin) == expected_bins, f'shard {args.shard} bin set mismatch')
    for bidx in expected_bins:
        req(len(by_bin[bidx]) == expected_counts[bidx], f'shard {args.shard} bin {bidx} event count mismatch')

    started = time.monotonic()
    reports = []
    for ordinal, bidx in enumerate(expected_bins, start=1):
        report = compare_one_bin(mod, wrapper, by_bin[bidx], bidx)
        reports.append(report)
        print({'RFT_EQUIV_SHARD': args.shard, 'bin': ordinal, 'of': len(expected_bins), **report}, flush=True)
    result = {
        'verdict': 'PASS_RFT_V1_BATCHED_KD_ATOM_EQUIVALENCE_SHARD',
        'role': 'ENGINEERING_IDENTITY_AUDIT_SHARD_ONLY',
        'shard': args.shard,
        'assigned_bins': expected_bins,
        'passed_bins': [int(row['bin_index']) for row in reports if row['exact']],
        'events_in_assigned_bins': sum(int(row['rows']) for row in reports),
        'atoms': sum(int(row['atoms']) for row in reports),
        'scalar_kdtree_queries_audited': sum(int(row['scalar_kdtree_queries_audited']) for row in reports),
        'all_kdtree_candidate_sets_exact': True,
        'all_atom_fields_exact': True,
        'elapsed_seconds': time.monotonic() - started,
        'scientific_endpoint_computed': False,
        'tube_construction_computed': False,
        'labels_used_in_computed_quantity': False,
        'blind_exclusion': [20.0, 55.0],
        'gmn_2023_access': False,
        'sonotaco_2013_2014_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'bins': reports,
    }
    (args.output / f'equivalence_shard_{args.shard}.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bins'}, indent=2, sort_keys=True), flush=True)
    return 0


def common_parser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--frozen-source', type=Path, required=True)
    parser.add_argument('--quality-source', type=Path, required=True)
    parser.add_argument('--support-source-parts', type=Path, required=True)
    parser.add_argument('--candidate-payload', type=Path, required=True)
    parser.add_argument('--baseline-payload', type=Path, required=True)
    parser.add_argument('--scorer-parts', type=Path, required=True)
    parser.add_argument('--v8-result-json', type=Path, required=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    common_parser_args(prep)
    prep.add_argument('--output', type=Path, required=True)
    shard = sub.add_parser('shard')
    shard.add_argument('--frozen-source', type=Path, required=True)
    shard.add_argument('--engineering-wrapper', type=Path, required=True)
    shard.add_argument('--events', type=Path, required=True)
    shard.add_argument('--assignment', type=Path, required=True)
    shard.add_argument('--shard', type=int, required=True)
    shard.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        return cmd_prepare(args)
    return cmd_shard(args)


if __name__ == '__main__':
    raise SystemExit(main())
