#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Any


def build_one_uv_parallel_replica(
    mod: Any,
    events: list[dict[str, Any]],
    replica: int,
    dead: Any,
    uvmod: Any,
    direct: Any,
    puv: Any,
) -> tuple[int, list[tuple[Any, ...]], list[tuple[Any, ...]], dict[str, Any]]:
    """Build one frozen RFT replica via exact UV reuse and independent-bin forks."""
    started = time.monotonic()
    replica_events = direct.perturb_with_existing_exact_cache(mod, events, replica)

    # Fail closed before the full computation. These checks establish both
    # scientific equivalence to the frozen atom logic and exact preservation of
    # sorted-bin decomposition under multiprocessing.
    puv.assert_parallel_uv_probe_equivalence(mod, replica_events, uvmod, dead)

    atom_started = time.monotonic()
    atom_list = puv.atoms_parallel_uv_bins(mod, replica_events, uvmod)
    atom_seconds = time.monotonic() - atom_started

    tube_started = time.monotonic()
    owned = mod.build_tubes(atom_list, ownership=True)
    unowned = mod.build_tubes(atom_list, ownership=False)
    tube_seconds = time.monotonic() - tube_started

    stats = {
        "replica": replica,
        "atoms": len(atom_list),
        "owned_tubes": len(owned),
        "unowned_tubes": len(unowned),
        "dead_medoid_elision": True,
        "uv_direct_pair_distance": True,
        "uv_direct_probe_equivalent": True,
        "parallel_uv_bin_atomization": True,
        "parallel_uv_bin_probe_equivalent": True,
        "pair_result_cache_disabled": True,
        "atom_stage_singleton_unit_recompute_disabled": True,
        "atom_seconds": atom_seconds,
        "tube_seconds": tube_seconds,
        "elapsed_seconds": time.monotonic() - started,
    }
    return replica, direct._packed_tubes(owned), direct._packed_tubes(unowned), stats
