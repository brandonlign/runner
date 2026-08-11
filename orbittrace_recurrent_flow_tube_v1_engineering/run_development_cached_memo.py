#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import math
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# Git blob SHA of the reviewed cached runner this wrapper is allowed to extend.
CACHED_RUNNER_BLOB_SHA = "2a599c6e8247eb819a1090591d586526eda6c0c1"
FROZEN_SCIENCE_BLOB_SHA = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"

_WORKER_MOD: Any | None = None
_WORKER_EVENTS: list[dict[str, Any]] | None = None


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_module_pinned(path: Path, name: str, expected_blob: str, label: str) -> Any:
    if git_blob_sha(path) != expected_blob:
        raise RuntimeError(f"{label} changed")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    # importlib's normal import path registers a module before executing it.
    # dataclasses relies on that invariant through cls.__module__. Preserve the
    # same import semantics here without changing the loaded source at all.
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def load_cached_runner(path: Path) -> Any:
    return load_module_pinned(path, "rft_cached_runner", CACHED_RUNNER_BLOB_SHA, "cached engineering runner")


def load_frozen_science(path: Path) -> Any:
    # The frozen source identifier is a Git blob SHA, matching the workflow's
    # git hash-object pin.
    return load_module_pinned(path, "rft_v1_frozen", FROZEN_SCIENCE_BLOB_SHA, "frozen RFT v1 source")


def _packed_tubes(tubes: list[Any]) -> list[tuple[Any, ...]]:
    # Return only primitive values across the process boundary. This avoids any
    # dependency on pickling dynamically loaded dataclass types.
    return [
        (
            t.tid,
            tuple(t.atom_ids),
            tuple(t.members),
            int(t.strata),
            float(t.span),
            tuple(float(x) for x in t.transition_costs),
        )
        for t in tubes
    ]


def _replica_worker(replica: int) -> tuple[int, list[tuple[Any, ...]], list[tuple[Any, ...]], dict[str, Any]]:
    """Run one frozen perturbation/atom/tube construction with exact memoization.

    Scientific functions remain the frozen RFT functions. The only substitutions
    are deterministic caches: `unit()` reuses values previously produced by the
    frozen `unit()` for identical floating inputs, and `pair_d()` reuses the float
    previously produced by the frozen `pair_d()` for the same ordered object pair.
    """
    mod = _WORKER_MOD
    events = _WORKER_EVENTS
    if mod is None or events is None:
        raise RuntimeError("RFT engineering worker globals were not initialized")

    started = time.monotonic()
    original_unit = mod.unit
    original_pair_d = mod.pair_d
    unit_cache: dict[tuple[float, float], np.ndarray] = {}
    pair_cache: dict[tuple[int, int], float] = {}
    unit_hits = 0
    unit_misses = 0
    pair_calls = 0
    pair_misses = 0

    def cached_unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
        nonlocal unit_hits, unit_misses
        lon = np.asarray(lon_deg)
        lat = np.asarray(lat_deg)
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == 1 and len(lat) == 1:
            key = (float(lon[0]), float(lat[0]))
            row = unit_cache.get(key)
            if row is not None:
                unit_hits += 1
                return row.reshape(1, 3)
            unit_misses += 1
            out = original_unit(lon, lat)
            unit_cache[key] = out[0].copy()
            return out

        out = original_unit(lon, lat)
        # `unit()` is elementwise. Cache the exact frozen outputs already
        # computed by this call so later singleton pair-distance calls avoid
        # repeated trigonometric allocations without recomputing any value.
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == len(lat) == len(out):
            for lo, la, row in zip(lon, lat, out):
                unit_cache[(float(lo), float(la))] = row.copy()
        return out

    def memo_pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
        nonlocal pair_calls, pair_misses
        pair_calls += 1
        key = (id(a), id(b))
        value = pair_cache.get(key)
        if value is None:
            pair_misses += 1
            value = original_pair_d(a, b)
            pair_cache[key] = value
        return value

    mod.unit = cached_unit
    mod.pair_d = memo_pair_d
    try:
        if replica == 0:
            replica_events = events
        else:
            # Seed the cache using one vectorized call to the *frozen* unit()
            # and verify representative rows are bit-identical to its singleton
            # form before perturbation is allowed to use the cached values.
            lon = np.asarray([e["lon"] for e in events], float)
            lat = np.asarray([e["lat"] for e in events], float)
            base_uv = original_unit(lon, lat)
            if len(events):
                probes = sorted({0, len(events) // 3, (2 * len(events)) // 3, len(events) - 1})
                for i in probes:
                    scalar = original_unit(np.asarray([lon[i]], float), np.asarray([lat[i]], float))[0]
                    if not np.array_equal(scalar, base_uv[i]):
                        raise RuntimeError("vectorized frozen unit output is not bit-identical to singleton output")
            for lo, la, row in zip(lon, lat, base_uv):
                unit_cache[(float(lo), float(la))] = row.copy()
            replica_events = mod.perturb(events, replica)

        atom_list = mod.atoms(replica_events)
        owned = mod.build_tubes(atom_list, ownership=True)
        unowned = mod.build_tubes(atom_list, ownership=False)
    finally:
        mod.unit = original_unit
        mod.pair_d = original_pair_d

    stats = {
        "replica": replica,
        "atoms": len(atom_list),
        "owned_tubes": len(owned),
        "unowned_tubes": len(unowned),
        "unit_cache_entries": len(unit_cache),
        "unit_cache_hits": unit_hits,
        "unit_cache_misses": unit_misses,
        "pair_d_calls": pair_calls,
        "pair_d_original_evaluations": pair_misses,
        "pair_d_cache_hits": pair_calls - pair_misses,
        "elapsed_seconds": time.monotonic() - started,
    }
    return replica, _packed_tubes(owned), _packed_tubes(unowned), stats


def parallel_memoized_build_cache(mod: Any, events: list[dict[str, Any]]) -> tuple[dict[int, list[Any]], dict[tuple[int, bool], list[Any]]]:
    """Build all frozen replica tube sets concurrently without changing science.

    Each replica is scientifically independent. Completion order is deliberately
    discarded: tube caches are reassembled by replica number before the frozen
    downstream persistence logic sees them.
    """
    global _WORKER_MOD, _WORKER_EVENTS
    _WORKER_MOD = mod
    _WORKER_EVENTS = events

    replicas = list(range(0, mod.PERTURB_REPLICAS + 1))
    available = os.cpu_count() or 1
    requested = int(os.environ.get("RFT_ENGINEERING_WORKERS", "4"))
    workers = max(1, min(requested, available, len(replicas)))
    methods = mp.get_all_start_methods()
    if "fork" not in methods:
        workers = 1

    print({
        "engineering_parallel_replicas": len(replicas),
        "engineering_workers": workers,
        "multiprocessing_start_methods": methods,
    }, flush=True)

    packed: dict[int, tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]] = {}
    stats_by_replica: dict[int, dict[str, Any]] = {}

    if workers == 1:
        results = map(_replica_worker, replicas)
        for replica, owned, unowned, stats in results:
            packed[replica] = (owned, unowned)
            stats_by_replica[replica] = stats
            print({"RFT_ENGINEERING_REPLICA_COMPLETE": stats}, flush=True)
    else:
        ctx = mp.get_context("fork")
        with ctx.Pool(processes=workers) as pool:
            for replica, owned, unowned, stats in pool.imap_unordered(_replica_worker, replicas, chunksize=1):
                packed[replica] = (owned, unowned)
                stats_by_replica[replica] = stats
                print({"RFT_ENGINEERING_REPLICA_COMPLETE": stats}, flush=True)

    if sorted(packed) != replicas:
        raise RuntimeError(f"incomplete RFT replica cache: {sorted(packed)}")

    # Atom objects are intentionally not retained: the cached scientific runner
    # never reads atom_cache after construction. Avoiding 17 retained atom lists
    # lowers peak memory while preserving its existing return contract.
    atom_cache: dict[int, list[Any]] = {replica: [] for replica in replicas}
    tube_cache: dict[tuple[int, bool], list[Any]] = {}
    for replica in replicas:
        owned, unowned = packed[replica]
        tube_cache[(replica, True)] = [mod.Tube(*values) for values in owned]
        tube_cache[(replica, False)] = [mod.Tube(*values) for values in unowned]

    print({
        "engineering_replica_stats": [stats_by_replica[r] for r in replicas],
        "engineering_total_worker_seconds": sum(float(stats_by_replica[r]["elapsed_seconds"]) for r in replicas),
    }, flush=True)
    return atom_cache, tube_cache


def main() -> int:
    here = Path(__file__).resolve().parent
    cached_path = here / "run_development_cached.py"
    cached = load_cached_runner(cached_path)
    cached.load_frozen = load_frozen_science
    cached.build_cache = parallel_memoized_build_cache
    return int(cached.main())


if __name__ == "__main__":
    raise SystemExit(main())
