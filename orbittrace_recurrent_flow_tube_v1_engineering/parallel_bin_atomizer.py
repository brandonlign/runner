#!/usr/bin/env python3
from __future__ import annotations

import multiprocessing as mp
import os
from collections import defaultdict
from typing import Any

_MOD: Any | None = None
_DEAD: Any | None = None
_BY_BIN: dict[int, list[dict[str, Any]]] | None = None


def _pack_atom(a: Any) -> tuple[Any, ...]:
    return (
        str(a.aid),
        int(a.bin_index),
        float(a.center),
        tuple(a.members),
        a.u.copy(),
        float(a.logv),
        float(a.medoid_residual),
    )


def _bin_worker(bidx: int) -> tuple[int, list[tuple[Any, ...]]]:
    mod = _MOD
    dead = _DEAD
    by_bin = _BY_BIN
    if mod is None or dead is None or by_bin is None:
        raise RuntimeError("parallel atom worker globals were not initialized")
    rows = by_bin[bidx]
    atoms = dead.atoms_without_dead_medoid(mod, rows)
    if any(int(a.bin_index) != bidx for a in atoms):
        raise RuntimeError(f"bin-local atomizer escaped bin {bidx}")
    return bidx, [_pack_atom(a) for a in atoms]


def atoms_parallel_bins(mod: Any, events: list[dict[str, Any]], dead: Any, workers: int | None = None) -> list[Any]:
    """Exact dead-medoid atomizer with independent solar-longitude bins forked.

    Frozen atoms() has no cross-bin state: neighbor search, reciprocal graph, and
    connected components are all built independently inside each bin, then the
    outputs are appended in sorted bin order. This function preserves precisely
    that decomposition and ordering.
    """
    by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        idx = int(mod.math.floor((e["coord"] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[idx].append(e)
    bins = sorted(by_bin)
    if not bins:
        return []

    methods = mp.get_all_start_methods()
    requested = workers if workers is not None else int(os.environ.get("RFT_BIN_WORKERS", "4"))
    count = max(1, min(int(requested), len(bins), os.cpu_count() or 1))
    if "fork" not in methods or count == 1:
        return dead.atoms_without_dead_medoid(mod, events)

    global _MOD, _DEAD, _BY_BIN
    _MOD = mod
    _DEAD = dead
    _BY_BIN = by_bin
    packed_by_bin: dict[int, list[tuple[Any, ...]]] = {}
    try:
        ctx = mp.get_context("fork")
        with ctx.Pool(processes=count) as pool:
            for bidx, packed in pool.imap_unordered(_bin_worker, bins, chunksize=1):
                packed_by_bin[bidx] = packed
    finally:
        _MOD = None
        _DEAD = None
        _BY_BIN = None

    if sorted(packed_by_bin) != bins:
        raise RuntimeError("parallel atomizer returned incomplete bin set")
    out: list[Any] = []
    for bidx in bins:
        for values in packed_by_bin[bidx]:
            out.append(mod.Atom(*values))
    return out


def _atom_signature(a: Any) -> tuple[Any, ...]:
    return (a.aid, a.bin_index, a.center, a.members, a.logv, a.u.tobytes())


def assert_parallel_probe_equivalence(mod: Any, events: list[dict[str, Any]], dead: Any, sample_size: int = 6000) -> None:
    """Fail closed unless serial and parallel dead-medoid atoms match on a spread probe."""
    if len(events) <= sample_size:
        probe = list(events)
    else:
        step = max(1, len(events) // sample_size)
        probe = list(events[::step][:sample_size])
    serial = dead.atoms_without_dead_medoid(mod, probe)
    parallel = atoms_parallel_bins(mod, probe, dead, workers=min(4, os.cpu_count() or 1))
    if len(serial) != len(parallel):
        raise RuntimeError("parallel-bin probe changed atom count")
    for i, (a, b) in enumerate(zip(serial, parallel)):
        if _atom_signature(a) != _atom_signature(b):
            raise RuntimeError(f"parallel-bin probe changed atom {i}")
