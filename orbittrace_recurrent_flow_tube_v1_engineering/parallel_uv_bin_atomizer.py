#!/usr/bin/env python3
from __future__ import annotations

import multiprocessing as mp
import os
from collections import defaultdict
from typing import Any

_MOD: Any | None = None
_UV: Any | None = None
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
    uvmod = _UV
    by_bin = _BY_BIN
    if mod is None or uvmod is None or by_bin is None:
        raise RuntimeError("parallel UV atom worker globals were not initialized")
    rows = by_bin[bidx]
    atoms = uvmod.atoms_uv_direct(mod, rows)
    if any(int(a.bin_index) != bidx for a in atoms):
        raise RuntimeError(f"UV-direct bin atomizer escaped bin {bidx}")
    return bidx, [_pack_atom(a) for a in atoms]


def atoms_parallel_uv_bins(
    mod: Any,
    events: list[dict[str, Any]],
    uvmod: Any,
    *,
    workers: int | None = None,
) -> list[Any]:
    """Exact UV-direct atomization with independent frozen 2-degree bins forked.

    Frozen RFT groups all events by bin before any neighbor operation. No edge,
    component, medoid, or atom state crosses a bin. Therefore each bin can be
    evaluated independently and concatenated in the identical sorted-bin order.
    """
    by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        idx = int(mod.math.floor((e["coord"] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[idx].append(e)
    bins = sorted(by_bin)
    if not bins:
        return []

    requested = workers if workers is not None else int(os.environ.get("RFT_BIN_WORKERS", "4"))
    count = max(1, min(int(requested), len(bins), os.cpu_count() or 1))
    if "fork" not in mp.get_all_start_methods() or count == 1:
        return uvmod.atoms_uv_direct(mod, events)

    global _MOD, _UV, _BY_BIN
    _MOD = mod
    _UV = uvmod
    _BY_BIN = by_bin
    packed_by_bin: dict[int, list[tuple[Any, ...]]] = {}
    try:
        ctx = mp.get_context("fork")
        with ctx.Pool(processes=count) as pool:
            for bidx, packed in pool.imap_unordered(_bin_worker, bins, chunksize=1):
                packed_by_bin[bidx] = packed
    finally:
        _MOD = None
        _UV = None
        _BY_BIN = None

    if sorted(packed_by_bin) != bins:
        raise RuntimeError("parallel UV atomizer returned incomplete bin set")

    out: list[Any] = []
    for bidx in bins:
        for values in packed_by_bin[bidx]:
            out.append(mod.Atom(*values))
    return out


def _signature(a: Any) -> tuple[Any, ...]:
    return (a.aid, a.bin_index, a.center, a.members, a.logv, a.u.tobytes())


def assert_parallel_uv_probe_equivalence(
    mod: Any,
    events: list[dict[str, Any]],
    uvmod: Any,
    dead: Any,
    sample_size: int = 6000,
) -> None:
    """Fail closed on both science equivalence and parallel decomposition."""
    if len(events) <= sample_size:
        probe = list(events)
    else:
        step = max(1, len(events) // sample_size)
        probe = list(events[::step][:sample_size])

    # First prove UV-direct atomization matches the exact dead-medoid reference.
    uvmod.assert_atom_probe_equivalence(mod, probe, dead, sample_size=len(probe))
    serial = uvmod.atoms_uv_direct(mod, probe)
    parallel = atoms_parallel_uv_bins(
        mod,
        probe,
        uvmod,
        workers=min(4, os.cpu_count() or 1),
    )
    if len(serial) != len(parallel):
        raise RuntimeError("parallel UV probe changed atom count")
    for i, (a, b) in enumerate(zip(serial, parallel)):
        if _signature(a) != _signature(b):
            raise RuntimeError(f"parallel UV probe changed atom {i}")
