#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any

# Git blob SHA of the reviewed cached runner this wrapper is allowed to extend.
CACHED_RUNNER_BLOB_SHA = "2a599c6e8247eb819a1090591d586526eda6c0c1"
FROZEN_SCIENCE_BLOB_SHA = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"


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
    spec.loader.exec_module(mod)
    return mod


def load_cached_runner(path: Path) -> Any:
    return load_module_pinned(path, "rft_cached_runner", CACHED_RUNNER_BLOB_SHA, "cached engineering runner")


def load_frozen_science(path: Path) -> Any:
    # The frozen source identifier is a Git blob SHA, matching the workflow's
    # git hash-object pin. The earlier engineering wrapper mistakenly compared
    # it to a raw SHA-256 digest and therefore failed before scientific work.
    return load_module_pinned(path, "rft_v1_frozen", FROZEN_SCIENCE_BLOB_SHA, "frozen RFT v1 source")


def memoized_build_cache(mod: Any, events: list[dict[str, Any]]) -> tuple[dict[int, list[Any]], dict[tuple[int, bool], list[Any]]]:
    """Same cached construction as PR #1211 plus exact repeated-call memoization.

    For each perturbation replica, the first call for a particular ordered pair of
    event *objects* delegates to the frozen pair_d implementation unchanged. Any
    later call on that exact same ordered pair returns the already-computed float.
    The cache is cleared between replicas, so perturbed coordinates can never
    reuse a value from another replica.
    """
    atom_cache: dict[int, list[Any]] = {}
    tube_cache: dict[tuple[int, bool], list[Any]] = {}
    original_pair_d = mod.pair_d

    total_pair_calls = 0
    total_pair_misses = 0

    for replica in range(0, mod.PERTURB_REPLICAS + 1):
        replica_events = events if replica == 0 else mod.perturb(events, replica)
        pair_cache: dict[tuple[int, int], float] = {}

        def memo_pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
            nonlocal total_pair_calls, total_pair_misses
            total_pair_calls += 1
            key = (id(a), id(b))
            if key not in pair_cache:
                total_pair_misses += 1
                pair_cache[key] = original_pair_d(a, b)
            return pair_cache[key]

        mod.pair_d = memo_pair_d
        try:
            atom_list = mod.atoms(replica_events)
        finally:
            mod.pair_d = original_pair_d

        atom_cache[replica] = atom_list
        tube_cache[(replica, True)] = mod.build_tubes(atom_list, ownership=True)
        tube_cache[(replica, False)] = mod.build_tubes(atom_list, ownership=False)

    print({
        "engineering_pair_d_calls": total_pair_calls,
        "engineering_pair_d_original_evaluations": total_pair_misses,
        "engineering_pair_d_cache_hits": total_pair_calls - total_pair_misses,
    })
    return atom_cache, tube_cache


def main() -> int:
    here = Path(__file__).resolve().parent
    cached_path = here / "run_development_cached.py"
    cached = load_cached_runner(cached_path)
    cached.load_frozen = load_frozen_science
    cached.build_cache = memoized_build_cache
    return int(cached.main())


if __name__ == "__main__":
    raise SystemExit(main())
