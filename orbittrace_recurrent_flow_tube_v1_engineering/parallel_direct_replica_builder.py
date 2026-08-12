#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Any


def build_one_replica_parallel(
    mod: Any,
    events: list[dict[str, Any]],
    replica: int,
    dead: Any,
    pair: Any,
    direct: Any,
    pbin: Any,
) -> tuple[int, list[tuple[Any, ...]], list[tuple[Any, ...]], dict[str, Any]]:
    """Exact direct replica construction with independent atom bins forked."""
    started = time.monotonic()
    replica_events = direct.perturb_with_existing_exact_cache(mod, events, replica)

    pair.assert_pair_equivalence(mod, replica_events)
    dead.assert_probe_equivalence(mod, replica_events)
    pbin.assert_parallel_probe_equivalence(mod, replica_events, dead)

    original_pair_d = mod.pair_d
    fast_pair_d, pair_stats = pair.make_exact_cached_pair_d(mod)
    mod.pair_d = fast_pair_d
    try:
        atom_list = pbin.atoms_parallel_bins(mod, replica_events, dead)
        owned = mod.build_tubes(atom_list, ownership=True)
        unowned = mod.build_tubes(atom_list, ownership=False)
    finally:
        mod.pair_d = original_pair_d

    stats = {
        "replica": replica,
        "atoms": len(atom_list),
        "owned_tubes": len(owned),
        "unowned_tubes": len(unowned),
        "dead_medoid_elision": True,
        "dead_medoid_probe_equivalent": True,
        "exact_pair_cache": True,
        "exact_pair_probe_equivalent": True,
        "parallel_bin_atomization": True,
        "parallel_bin_probe_equivalent": True,
        "atom_stage_unit_cache_disabled": True,
        "pair_result_cache_disabled": True,
        "parent_exact_pair_vector_hits": int(pair_stats["vector_hits"]),
        "parent_exact_pair_vector_misses": int(pair_stats["vector_misses"]),
        "parent_exact_pair_calls": int(pair_stats["pair_calls"]),
        "elapsed_seconds": time.monotonic() - started,
    }
    return replica, direct._packed_tubes(owned), direct._packed_tubes(unowned), stats
