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
    return load_module_pinned(path, "rft_v1_frozen", FROZEN_SCIENCE_BLOB_SHA, "frozen RFT v1 source")


def _packed_tubes(tubes: list[Any]) -> list[tuple[Any, ...]]:
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


def _accelerated_atoms(mod: Any, events: list[dict[str, Any]]) -> list[Any]:
    """Exact frozen atoms() semantics with one implementation-only KD query change.

    Frozen atoms() calls cKDTree.query_ball_point once for every event. Here the
    same tree, transformed coordinates and radius are passed to SciPy in one
    batched query per solar-longitude bin. The returned candidate-list ordering
    is scientifically irrelevant because the frozen code subsequently computes
    exact pair_d for every candidate and sorts by (distance,event_id) before
    selecting KNN. All exact pair distances, reciprocal-neighbor logic,
    connected components, medoid rule, atom centers/members and IDs remain the
    frozen functions/rules.
    """
    by_bin: dict[int, list[dict[str, Any]]] = mod.defaultdict(list)
    for e in events:
        idx = int(math.floor((e["coord"] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[idx].append(e)

    out: list[Any] = []
    for bidx in sorted(by_bin):
        rows = by_bin[bidx]
        if len(rows) < mod.MIN_ATOM:
            continue
        lon = np.asarray([r["lon"] for r in rows], float)
        lat = np.asarray([r["lat"] for r in rows], float)
        vg = np.asarray([r["vg"] for r in rows], float)
        uv = mod.unit(lon, lat)
        transformed = np.column_stack((
            uv / (2.0 * math.sin(math.radians(3.0) / 2.0)),
            np.log(vg) / math.log(1.08),
        ))
        tree = mod.cKDTree(transformed)
        bulk_candidates = tree.query_ball_point(transformed, r=1.02)
        if len(bulk_candidates) != len(rows):
            raise RuntimeError("batched KD candidate count changed")

        # Deterministic implementation audit: prove the batched SciPy API gives
        # exactly the same candidate set as the frozen scalar API on several
        # positions in every nontrivial bin. Final KNN ordering is still driven
        # solely by the frozen exact pair_d sort below.
        if rows:
            probes = sorted({0, len(rows) // 3, (2 * len(rows)) // 3, len(rows) - 1})
            for i in probes:
                scalar = tree.query_ball_point(transformed[i], r=1.02)
                if set(map(int, scalar)) != set(map(int, bulk_candidates[i])):
                    raise RuntimeError(f"batched KD candidate set differs in bin {bidx} row {i}")

        neighbor_sets: list[list[int]] = []
        for i, candidates in enumerate(bulk_candidates):
            ds = []
            for raw_j in candidates:
                j = int(raw_j)
                if j == i:
                    continue
                d = mod.pair_d(rows[i], rows[j])
                if d <= 1.0 + 1e-12:
                    ds.append((d, mod.event_id(rows[j]), j))
            ds.sort(key=lambda x: (x[0], x[1]))
            neighbor_sets.append([j for _d, _eid, j in ds[:mod.KNN]])

        adj = [set() for _ in rows]
        for i, ns in enumerate(neighbor_sets):
            for j in ns:
                if i in neighbor_sets[j]:
                    adj[i].add(j)
                    adj[j].add(i)

        seen: set[int] = set()
        for seed in range(len(rows)):
            if seed in seen:
                continue
            stack = [seed]
            comp: list[int] = []
            seen.add(seed)
            while stack:
                i = stack.pop()
                comp.append(i)
                for j in sorted(adj[i]):
                    if j not in seen:
                        seen.add(j)
                        stack.append(j)
            if len(comp) < mod.MIN_ATOM:
                continue
            mids = []
            for i in comp:
                ds = [mod.pair_d(rows[i], rows[j]) for j in comp if j != i]
                mids.append((float(np.median(ds)) if ds else 0.0, mod.event_id(rows[i]), i))
            med_res, _mid, _med_idx = min(mids)
            uu = uv[comp].sum(axis=0)
            uu /= np.linalg.norm(uu)
            logv = float(np.median(np.log(vg[comp])))
            members = tuple(sorted(mod.event_id(rows[i]) for i in comp))
            aid = hashlib.sha256((f"{bidx}|" + "|".join(members)).encode()).hexdigest()[:16]
            out.append(mod.Atom(
                aid,
                bidx,
                mod.BLIND[1] + (bidx + 0.5) * mod.BIN_WIDTH,
                members,
                uu,
                logv,
                med_res,
            ))
    return out


def _replica_worker(replica: int) -> tuple[int, list[tuple[Any, ...]], list[tuple[Any, ...]], dict[str, Any]]:
    """Run one frozen perturbation/atom/tube construction with exact caching.

    Scientific functions remain frozen. The substitutions are implementation
    only: unit() output reuse for identical floating inputs, pair_d() reuse for
    the identical ordered object pair, and batched cKDTree radius queries whose
    candidate sets are audited against the frozen scalar API within every bin.
    """
    mod = _WORKER_MOD
    events = _WORKER_EVENTS
    if mod is None or events is None:
        raise RuntimeError("RFT engineering worker globals were not initialized")

    started = time.monotonic()
    original_unit = mod.unit
    original_pair_d = mod.pair_d
    original_atoms = mod.atoms
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
        if lon.ndim == 1 and lat.ndim == 1 and len(lon) == len(lat) == len(out):
            for lo, la, row in zip(lon, lat, out):
                unit_cache[(float(lo), float(la))] = row.copy()
        return out

    def memo_pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
        nonlocal pair_calls, pair_misses
        pair_calls += 1
        key = (id(a), id(b))
        if key in pair_cache:
            return pair_cache[key]
        pair_misses += 1
        value = original_pair_d(a, b)
        pair_cache[key] = value
        return value

    mod.unit = cached_unit
    mod.pair_d = memo_pair_d
    mod.atoms = lambda xs: _accelerated_atoms(mod, xs)
    try:
        if replica == 0:
            replica_events = events
        else:
            # Seed cached unit vectors using the frozen unit() itself. Probe
            # vectorized-vs-singleton equality before perturbation can reuse it.
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
        mod.atoms = original_atoms

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
        "batched_kdtree_radius_queries": True,
        "elapsed_seconds": time.monotonic() - started,
    }
    return replica, _packed_tubes(owned), _packed_tubes(unowned), stats


def parallel_memoized_build_cache(mod: Any, events: list[dict[str, Any]]) -> tuple[dict[int, list[Any]], dict[tuple[int, bool], list[Any]]]:
    """Build all frozen replica tube sets concurrently without changing science."""
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
        "engineering_batched_kdtree_radius_queries": True,
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
