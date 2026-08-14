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
FAST_PAIR_BLOB = '5c6e914849a24bc2683c7e7e86e5f34f80834df4'
PIECES = 3


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def load(path: Path, name: str, expected: str) -> Any:
    req(blob(path) == expected, f'{name} blob changed')
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


def assignment(mod: Any, events: list[dict[str, Any]]) -> tuple[list[list[int]], list[int], dict[int, int]]:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-source', type=Path, required=True)
    parser.add_argument('--wrapper', type=Path, required=True)
    parser.add_argument('--fast-pair-source', type=Path, required=True)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--replica', type=int, required=True)
    parser.add_argument('--piece', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    req(0 <= args.replica <= 16, 'invalid replica')
    req(0 <= args.piece < PIECES, 'invalid repair piece')
    args.output.mkdir(parents=True, exist_ok=True)

    mod = load(args.frozen_source, 'rft_shard3_fast_frozen', FROZEN_BLOB)
    wrapper = load(args.wrapper, 'rft_shard3_fast_wrapper', WRAPPER_BLOB)
    fast_mod = load(args.fast_pair_source, 'rft_shard3_fast_pair', FAST_PAIR_BLOB)
    events = read_gz(args.events)
    req(all(not (mod.BLIND[0] <= float(event['sol']) <= mod.BLIND[1]) for event in events), 'protected event in prepared input')
    pieces, loads, counts = assignment(mod, events)
    all_bins = sorted(b for piece_bins in pieces for b in piece_bins)
    req(all_bins == sorted(counts) and len(all_bins) == len(set(all_bins)), 'repair assignment does not exactly cover original shard-3 bins')
    chosen = set(pieces[args.piece])
    replica_events = events if args.replica == 0 else mod.perturb(events, args.replica)
    selected = [event for event in replica_events if bin_index(mod, event) in chosen]
    req(len(selected) == sum(counts[b] for b in chosen), 'repair piece event count changed under perturbation')

    exact_fast = fast_mod.build_exact_fast_pair_d(mod, selected)
    original_pair = mod.pair_d
    ordered_cache: dict[tuple[int, int], float] = {}
    pair_calls = 0
    pair_misses = 0

    def memo_fast_pair(a: dict[str, Any], b: dict[str, Any]) -> float:
        nonlocal pair_calls, pair_misses
        pair_calls += 1
        key = (id(a), id(b))
        if key in ordered_cache:
            return ordered_cache[key]
        pair_misses += 1
        value = exact_fast(a, b)
        ordered_cache[key] = value
        return value

    mod.pair_d = memo_fast_pair
    started = time.monotonic()
    try:
        atoms = wrapper._accelerated_atoms(mod, selected)
    finally:
        mod.pair_d = original_pair
    rows = [atom_dict(atom) for atom in atoms]
    req(len({row['aid'] for row in rows}) == len(rows), 'duplicate atom ID in repair piece')
    req(all(int(row['bin_index']) in chosen for row in rows), 'repair atom escaped assigned bins')

    output = args.output / f'atoms_r{args.replica:02d}_s3p{args.piece}.json.gz'
    write_gz(output, rows)
    assignment_payload = {
        'piece_bins': pieces,
        'piece_n2_loads': loads,
        'piece_event_counts': [sum(counts[b] for b in piece_bins) for piece_bins in pieces],
    }
    assignment_sha = hashlib.sha256(json.dumps(assignment_payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    result = {
        'replica': args.replica,
        'piece': args.piece,
        'input_events': len(events),
        'selected_events': len(selected),
        'atoms': len(rows),
        'ordered_pair_d_calls': pair_calls,
        'ordered_pair_d_original_fast_evaluations': pair_misses,
        'ordered_pair_d_cache_hits': pair_calls - pair_misses,
        'elapsed_seconds': time.monotonic() - started,
        'atom_file_sha256': sha256(output),
        'assignment_sha256': assignment_sha,
        'fast_pair_source_blob': FAST_PAIR_BLOB,
        'fast_pair_equivalence_authorizer_run': 31818476734,
        'reverse_pair_reuse': False,
        **assignment_payload,
    }
    (args.output / f'atoms_r{args.replica:02d}_s3p{args.piece}_stats.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
