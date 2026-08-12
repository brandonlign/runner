#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MEMO_BLOB = "8a10e18daa6ba5bf99864a67e8cd059704695735"
CACHED_BLOB = "2a599c6e8247eb819a1090591d586526eda6c0c1"
FROZEN_BLOB = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"
DEAD_MEDOID_BLOB = "c448055e500baf761a88a8823ae051ae59e9e436"
EXACT_PAIR_BLOB = "b30ecc155e16feecb122a51eded91027b8275019"
DIRECT_BLOB = "0277fe069835ca832e82124ba4cc88a06f8021fe"
PBIN_BLOB = "c02fa5a8a8e692a6aa74c733df055d16adae313f"
PDIRECT_BLOB = "d03852db92b4a10e58d77d21f5524374e531d01b"
SCHEMA = "RFT_V1_ENGINEERING_REPLICA_SHARD_V1"


class ShardComplete(Exception):
    pass


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--replica", type=int, required=True)
    pre.add_argument("--shard-output", type=Path, required=True)
    a, remaining = pre.parse_known_args(sys.argv[1:])

    here = Path(__file__).resolve().parent
    paths = {
        "memo": (here / "run_development_cached_memo.py", MEMO_BLOB),
        "cached": (here / "run_development_cached.py", CACHED_BLOB),
        "dead": (here / "dead_medoid_atomizer.py", DEAD_MEDOID_BLOB),
        "pair": (here / "exact_pair_cache.py", EXACT_PAIR_BLOB),
        "direct": (here / "direct_replica_builder.py", DIRECT_BLOB),
        "pbin": (here / "parallel_bin_atomizer.py", PBIN_BLOB),
        "pdirect": (here / "parallel_direct_replica_builder.py", PDIRECT_BLOB),
    }
    for label, (path, expected) in paths.items():
        if blob(path) != expected:
            raise RuntimeError(f"engineering source pin changed: {label}")

    memo = load(paths["memo"][0], "rft_parallel_shard_memo")
    dead = load(paths["dead"][0], "rft_parallel_dead_medoid")
    pair = load(paths["pair"][0], "rft_parallel_exact_pair")
    direct = load(paths["direct"][0], "rft_parallel_direct")
    pbin = load(paths["pbin"][0], "rft_parallel_bin_atomizer")
    pdirect = load(paths["pdirect"][0], "rft_parallel_direct_builder")
    cached = memo.load_cached_runner(paths["cached"][0])
    cached.load_frozen = memo.load_frozen_science

    def shard_cache(mod: Any, events: list[dict[str, Any]]):
        if blob(Path(sys.argv[sys.argv.index("--frozen-source") + 1])) != FROZEN_BLOB:
            raise RuntimeError("frozen science source changed")
        if not (0 <= a.replica <= mod.PERTURB_REPLICAS):
            raise RuntimeError(f"invalid replica {a.replica}")
        replica, owned, unowned, stats = pdirect.build_one_replica_parallel(
            mod, events, a.replica, dead, pair, direct, pbin
        )
        event_sha = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
        payload = {
            "schema": SCHEMA,
            "replica": replica,
            "event_count": len(events),
            "event_order_sha256": event_sha,
            "frozen_science_blob": FROZEN_BLOB,
            "cached_runner_blob": CACHED_BLOB,
            "memo_wrapper_blob": MEMO_BLOB,
            "dead_medoid_atomizer_blob": DEAD_MEDOID_BLOB,
            "exact_pair_cache_blob": EXACT_PAIR_BLOB,
            "direct_replica_builder_blob": DIRECT_BLOB,
            "parallel_bin_atomizer_blob": PBIN_BLOB,
            "parallel_direct_builder_blob": PDIRECT_BLOB,
            "blind_exclusion": list(mod.BLIND),
            "target_information_access": False,
            "target_region_events_accessed": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
            "sonotaco_2013_2014_access": False,
            "gmn_2023_access": False,
            "owned_tubes": owned,
            "unowned_tubes": unowned,
            "stats": stats,
        }
        a.shard_output.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(a.shard_output, "wt", encoding="utf-8", compresslevel=6) as fh:
            json.dump(payload, fh, sort_keys=True, separators=(",", ":"), allow_nan=False)
            fh.write("\n")
        print(json.dumps({"RFT_PARALLEL_REPLICA_SHARD_COMPLETE": replica, "stats": stats}, sort_keys=True), flush=True)
        raise ShardComplete

    cached.build_cache = shard_cache
    sys.argv = [sys.argv[0]] + remaining
    try:
        cached.main()
    except ShardComplete:
        return 0
    raise RuntimeError("cached runner unexpectedly passed parallel shard interception")


if __name__ == "__main__":
    raise SystemExit(main())
