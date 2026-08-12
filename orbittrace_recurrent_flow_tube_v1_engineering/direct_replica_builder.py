#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Any

import numpy as np


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


def perturb_with_existing_exact_cache(mod: Any, events: list[dict[str, Any]], replica: int) -> list[dict[str, Any]]:
    """Use the established exact-output perturbation cache only during perturb()."""
    if replica == 0:
        return events
    original_unit = mod.unit
    lon = np.asarray([e["lon"] for e in events], float)
    lat = np.asarray([e["lat"] for e in events], float)
    base_uv = original_unit(lon, lat)
    if len(events):
        probes = sorted({0, len(events) // 3, (2 * len(events)) // 3, len(events) - 1})
        for i in probes:
            scalar = original_unit(np.asarray([lon[i]], float), np.asarray([lat[i]], float))[0]
            if not np.array_equal(scalar, base_uv[i]):
                raise RuntimeError("vectorized frozen unit output is not bit-identical to singleton output")
    unit_cache = {(float(lo), float(la)): row.copy() for lo, la, row in zip(lon, lat, base_uv)}

    def perturb_unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
        lo = np.asarray(lon_deg)
        la = np.asarray(lat_deg)
        if lo.ndim == 1 and la.ndim == 1 and len(lo) == len(la) == 1:
            row = unit_cache.get((float(lo[0]), float(la[0])))
            if row is not None:
                return row.reshape(1, 3)
        return original_unit(lo, la)

    mod.unit = perturb_unit
    try:
        return mod.perturb(events, replica)
    finally:
        mod.unit = original_unit


def build_one_replica(
    mod: Any,
    events: list[dict[str, Any]],
    replica: int,
    dead: Any,
    pair: Any,
) -> tuple[int, list[tuple[Any, ...]], list[tuple[Any, ...]], dict[str, Any]]:
    """Construct one exact RFT replica without atom-stage cache bookkeeping."""
    started = time.monotonic()
    replica_events = perturb_with_existing_exact_cache(mod, events, replica)

    # Fail closed on both substitutions against the frozen implementation.
    pair.assert_pair_equivalence(mod, replica_events)
    dead.assert_probe_equivalence(mod, replica_events)

    original_atoms = mod.atoms
    original_pair_d = mod.pair_d
    fast_pair_d, pair_stats = pair.make_exact_cached_pair_d(mod)
    mod.atoms = lambda rows: dead.atoms_without_dead_medoid(mod, rows)
    mod.pair_d = fast_pair_d
    try:
        atom_list = mod.atoms(replica_events)
        owned = mod.build_tubes(atom_list, ownership=True)
        unowned = mod.build_tubes(atom_list, ownership=False)
    finally:
        mod.pair_d = original_pair_d
        mod.atoms = original_atoms

    stats = {
        "replica": replica,
        "atoms": len(atom_list),
        "owned_tubes": len(owned),
        "unowned_tubes": len(unowned),
        "dead_medoid_elision": True,
        "dead_medoid_probe_equivalent": True,
        "exact_pair_cache": True,
        "exact_pair_probe_equivalent": True,
        "exact_pair_vector_hits": int(pair_stats["vector_hits"]),
        "exact_pair_vector_misses": int(pair_stats["vector_misses"]),
        "exact_pair_calls": int(pair_stats["pair_calls"]),
        "atom_stage_unit_cache_disabled": True,
        "pair_result_cache_disabled": True,
        "elapsed_seconds": time.monotonic() - started,
    }
    return replica, _packed_tubes(owned), _packed_tubes(unowned), stats
