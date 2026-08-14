#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

FROZEN_BLOB = 'a5d5371f0c30a9c57ee4d8756ea41f454cd86301'
FAST_PAIR_BLOB = 'TO_BE_PINNED_BY_WORKFLOW'


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_events(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        events = json.load(handle)
    req(isinstance(events, list) and events, 'empty prepared event list')
    return events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-source', type=Path, required=True)
    parser.add_argument('--fast-pair-source', type=Path, required=True)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(args.frozen_source) == FROZEN_BLOB, 'frozen RFT science changed')
    mod = load(args.frozen_source, 'rft_fast_pair_equiv_frozen')
    fast_mod = load(args.fast_pair_source, 'rft_fast_pair_equiv_impl')
    events = read_events(args.events)
    req(all(str(event['id']).startswith('2022') for event in events), 'non-2022 event in prepared input')
    req(all(not (20.0 <= float(event['sol']) <= 55.0) for event in events), 'protected event in prepared input')

    by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        bidx = int(math.floor((float(event['coord']) - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[bidx].append(event)

    bin_reports = []
    total_pairs = 0
    for bidx in sorted(by_bin):
        rows = by_bin[bidx]
        fast = fast_mod.build_exact_fast_pair_d(mod, rows)
        n = len(rows)
        positions = sorted({
            0,
            min(1, n - 1),
            n // 5,
            n // 3,
            n // 2,
            (2 * n) // 3,
            (4 * n) // 5,
            max(0, n - 2),
            n - 1,
        })
        comparisons = 0
        for i in positions:
            for j in positions:
                if i == j:
                    continue
                original = mod.pair_d(rows[i], rows[j])
                accelerated = fast(rows[i], rows[j])
                req(original == accelerated, f'pair_d float mismatch bin {bidx} ordered pair {i},{j}: {original!r} != {accelerated!r}')
                comparisons += 1
        # Also cover deterministic short-range index neighbors outside the probe cross-product.
        stride = max(1, n // 97)
        for i in range(0, n, stride):
            for delta in (1, 2, 5):
                j = i + delta
                if j >= n:
                    continue
                original = mod.pair_d(rows[i], rows[j])
                accelerated = fast(rows[i], rows[j])
                req(original == accelerated, f'pair_d float mismatch bin {bidx} neighbor pair {i},{j}')
                original_reverse = mod.pair_d(rows[j], rows[i])
                accelerated_reverse = fast(rows[j], rows[i])
                req(original_reverse == accelerated_reverse, f'pair_d reverse float mismatch bin {bidx} neighbor pair {j},{i}')
                comparisons += 2
        total_pairs += comparisons
        bin_reports.append({'bin_index': int(bidx), 'rows': n, 'ordered_pairs_compared': comparisons, 'exact': True})

    result = {
        'verdict': 'PASS_RFT_V1_FAST_ORDERED_PAIR_D_EQUIVALENCE_AUDIT',
        'role': 'ZERO_ENDPOINT_ENGINEERING_IDENTITY_AUDIT_ONLY',
        'events': len(events),
        'bin_count': len(by_bin),
        'ordered_pairs_compared': total_pairs,
        'all_compared_floats_bitwise_equal': True,
        'reverse_pair_reuse_authorized': False,
        'scientific_endpoint_computed': False,
        'atoms_computed': False,
        'tubes_computed': False,
        'labels_used': False,
        'gmn_2023_access': False,
        'sonotaco_2013_2014_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
        'frozen_science_blob': FROZEN_BLOB,
        'fast_pair_source_blob': git_blob_sha(args.fast_pair_source),
        'bins': bin_reports,
    }
    output = args.output / 'RFT_V1_FAST_PAIR_D_EQUIVALENCE.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bins'}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
