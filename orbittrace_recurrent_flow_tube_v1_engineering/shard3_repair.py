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

FROZEN_BLOB = 'a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
WRAPPER_BLOB = '8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa'
PIECES = 3


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def load(path: Path, name: str, expected_blob: str) -> Any:
    req(git_blob_sha(path) == expected_blob, f'{name} blob changed')
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_gz(path: Path) -> Any:
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        return json.load(handle)


def write_gz(path: Path, obj: Any) -> None:
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as handle:
        json.dump(obj, handle, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bin_index(mod: Any, event: dict[str, Any]) -> int:
    return int(math.floor((float(event['coord']) - mod.BLIND[1]) / mod.BIN_WIDTH))


def repair_assignment(mod: Any, events: list[dict[str, Any]]) -> tuple[list[list[int]], list[int], dict[int, int]]:
    counts = Counter(bin_index(mod, event) for event in events if bin_index(mod, event) % 4 == 3)
    pieces: list[list[int]] = [[] for _ in range(PIECES)]
    loads = [0 for _ in range(PIECES)]
    for bidx, count in sorted(counts.items(), key=lambda item: (-(item[1] ** 2), item[0])):
        piece = min(range(PIECES), key=lambda p: (loads[p], p))
        pieces[piece].append(int(bidx))
        loads[piece] += int(count) ** 2
    for row in pieces:
        row.sort()
    return pieces, loads, dict(counts)


def atom_dict(atom: Any) -> dict[str, Any]:
    return {
        'aid': atom.aid,
        'bin_index': int(atom.bin_index),
        'center': float(atom.center),
        'members': list(atom.members),
        'u': [float(x) for x in np.asarray(atom.u)],
        'logv': float(atom.logv),
        'medoid_residual': float(atom.medoid_residual),
    }


def cmd_atoms(args: argparse.Namespace) -> int:
    req(0 <= args.replica <= 16, 'invalid replica')
    req(0 <= args.piece < PIECES, 'invalid piece')
    args.output.mkdir(parents=True, exist_ok=True)
    mod = load(args.frozen_source, 'rft_shard3_repair_frozen', FROZEN_BLOB)
    wrapper = load(args.wrapper, 'rft_shard3_repair_wrapper', WRAPPER_BLOB)
    events = read_gz(args.events)
    req(all(not (mod.BLIND[0] <= float(event['sol']) <= mod.BLIND[1]) for event in events), 'protected event in prepared input')
    pieces, loads, counts = repair_assignment(mod, events)
    chosen = set(pieces[args.piece])
    expected_all = sorted(counts)
    actual_all = sorted(b for row in pieces for b in row)
    req(actual_all == expected_all and len(actual_all) == len(set(actual_all)), 'repair bin assignment invalid')
    replica_events = events if args.replica == 0 else mod.perturb(events, args.replica)
    selected = [event for event in replica_events if bin_index(mod, event) in chosen]
    req(len(selected) == sum(counts[b] for b in chosen), 'repair piece event count changed under perturbation')

    original_unit = mod.unit
    original_pair = mod.pair_d
    unit_cache: dict[tuple[float, float], np.ndarray] = {}
    pair_cache: dict[tuple[int, int], float] = {}
    pair_calls = 0
    pair_original = 0

    def cached_unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
        lon = np.asarray(lon_deg)
        lat = np.asarray(lat_deg)
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == len(lat) == 1:
            key = (float(lon[0]), float(lat[0]))
            existing = unit_cache.get(key)
            if existing is not None:
                return existing.reshape(1, 3)
            out = original_unit(lon, lat)
            unit_cache[key] = out[0].copy()
            return out
        out = original_unit(lon, lat)
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == len(lat) == len(out):
            for lo, la, vector in zip(lon, lat, out):
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
        atoms = wrapper._accelerated_atoms(mod, selected)
    finally:
        mod.unit = original_unit
        mod.pair_d = original_pair
    rows = [atom_dict(atom) for atom in atoms]
    req(len({row['aid'] for row in rows}) == len(rows), 'duplicate atom ID in repair piece')
    req(all(int(row['bin_index']) in chosen for row in rows), 'atom escaped assigned repair piece')
    output = args.output / f'atoms_r{args.replica:02d}_s3p{args.piece}.json.gz'
    write_gz(output, rows)
    assignment_payload = {
        'piece_bins': pieces,
        'piece_n2_loads': loads,
        'piece_event_counts': [sum(counts[b] for b in row) for row in pieces],
    }
    assignment_sha = hashlib.sha256(json.dumps(assignment_payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    stats = {
        'replica': args.replica,
        'piece': args.piece,
        'input_events': len(events),
        'selected_events': len(selected),
        'atoms': len(rows),
        'pair_d_calls': pair_calls,
        'pair_d_original_evaluations': pair_original,
        'elapsed_seconds': time.monotonic() - started,
        'atom_file_sha256': sha256(output),
        'assignment_sha256': assignment_sha,
        **assignment_payload,
    }
    (args.output / f'atoms_r{args.replica:02d}_s3p{args.piece}_stats.json').write_text(json.dumps(stats, indent=2, sort_keys=True) + '\n')
    print(json.dumps(stats, sort_keys=True), flush=True)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    req(0 <= args.replica <= 16, 'invalid replica')
    args.output.mkdir(parents=True, exist_ok=True)
    mod = load(args.frozen_source, 'rft_shard3_merge_frozen', FROZEN_BLOB)
    events = read_gz(args.events)
    pieces, _loads, counts = repair_assignment(mod, events)
    expected_bins = sorted(counts)
    rows: list[dict[str, Any]] = []
    produced_bins: set[int] = set()
    assignment_shas: set[str] = set()
    for piece in range(PIECES):
        path = args.piece_dir / f'atoms_r{args.replica:02d}_s3p{piece}.json.gz'
        stats_path = args.piece_dir / f'atoms_r{args.replica:02d}_s3p{piece}_stats.json'
        req(path.exists() and stats_path.exists(), f'missing repair piece {piece}')
        stats = json.loads(stats_path.read_text())
        req(int(stats['replica']) == args.replica and int(stats['piece']) == piece, 'repair piece identity mismatch')
        req(list(map(int, stats['piece_bins'][piece])) == pieces[piece], f'repair piece {piece} bin assignment changed')
        assignment_shas.add(str(stats['assignment_sha256']))
        part = read_gz(path)
        req(all(int(row['bin_index']) in set(pieces[piece]) for row in part), f'repair piece {piece} contains wrong bin')
        produced_bins.update(int(row['bin_index']) for row in part)
        rows.extend(part)
    req(len(assignment_shas) == 1, 'repair pieces disagree on assignment')
    req(len({row['aid'] for row in rows}) == len(rows), 'duplicate atom ID after shard-3 repair merge')
    # Empty-atom bins need not appear in produced atom rows; assignment coverage is proven from the stats.
    assigned_bins = sorted(b for piece_bins in pieces for b in piece_bins)
    req(assigned_bins == expected_bins and len(assigned_bins) == len(set(assigned_bins)), 'repair assignment does not exactly cover original shard 3 bins')
    req(produced_bins.issubset(set(expected_bins)), 'merged atom contains non-shard3 bin')
    rows.sort(key=lambda row: (int(row['bin_index']), str(row['aid'])))
    output = args.output / f'atoms_r{args.replica:02d}_s3.json.gz'
    write_gz(output, rows)
    result = {
        'verdict': 'PASS_RFT_V1_SHARD3_REPAIR_MERGE',
        'replica': args.replica,
        'repair_pieces': PIECES,
        'original_shard3_bins': expected_bins,
        'atoms': len(rows),
        'assignment_sha256': next(iter(assignment_shas)),
        'merged_atom_file_sha256': sha256(output),
        'scientific_changes': False,
    }
    (args.output / f'atoms_r{args.replica:02d}_s3_merge.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    atoms = sub.add_parser('atoms')
    atoms.add_argument('--frozen-source', type=Path, required=True)
    atoms.add_argument('--wrapper', type=Path, required=True)
    atoms.add_argument('--events', type=Path, required=True)
    atoms.add_argument('--replica', type=int, required=True)
    atoms.add_argument('--piece', type=int, required=True)
    atoms.add_argument('--output', type=Path, required=True)
    merge = sub.add_parser('merge')
    merge.add_argument('--frozen-source', type=Path, required=True)
    merge.add_argument('--events', type=Path, required=True)
    merge.add_argument('--piece-dir', type=Path, required=True)
    merge.add_argument('--replica', type=int, required=True)
    merge.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'atoms':
        return cmd_atoms(args)
    return cmd_merge(args)


if __name__ == '__main__':
    raise SystemExit(main())
