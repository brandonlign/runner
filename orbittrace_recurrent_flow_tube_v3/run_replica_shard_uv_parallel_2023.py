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

YEAR = 2023
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
MEMO_BLOB = "8a10e18daa6ba5bf99864a67e8cd059704695735"
CACHED_BLOB = "2a599c6e8247eb819a1090591d586526eda6c0c1"
FROZEN_BLOB = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"
DEAD_BLOB = "c448055e500baf761a88a8823ae051ae59e9e436"
UV_BLOB = "f14302fcc8258c16e514859cf927e895942853c1"
DIRECT_BLOB = "0277fe069835ca832e82124ba4cc88a06f8021fe"
PUV_BLOB = "4ecaa880c4212bed9baf719268704cf816fe3593"
BUILDER_BLOB = "a94343f87c6021eb7da03dcf095378272fea97d3"
SCHEMA = "RFT_V3_GMN2023_OWNED_REPLICA_SHARD_V1"


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

    here = Path(__file__).resolve().parents[1] / "orbittrace_recurrent_flow_tube_v1_engineering"
    paths = {
        "memo": (here / "run_development_cached_memo.py", MEMO_BLOB),
        "cached": (here / "run_development_cached.py", CACHED_BLOB),
        "dead": (here / "dead_medoid_atomizer.py", DEAD_BLOB),
        "uv": (here / "uv_direct_atomizer.py", UV_BLOB),
        "direct": (here / "direct_replica_builder.py", DIRECT_BLOB),
        "puv": (here / "parallel_uv_bin_atomizer.py", PUV_BLOB),
        "builder": (here / "uv_parallel_replica_builder.py", BUILDER_BLOB),
    }
    for label, (path, expected) in paths.items():
        if blob(path) != expected:
            raise RuntimeError(f"engineering source pin changed: {label}")

    memo = load(paths["memo"][0], "rft_v3_2023_memo")
    dead = load(paths["dead"][0], "rft_v3_2023_dead")
    uvmod = load(paths["uv"][0], "rft_v3_2023_uv")
    direct = load(paths["direct"][0], "rft_v3_2023_direct")
    puv = load(paths["puv"][0], "rft_v3_2023_parallel_uv")
    builder = load(paths["builder"][0], "rft_v3_2023_builder")
    cached = memo.load_cached_runner(paths["cached"][0])

    def load_frozen_2023(path: Path) -> Any:
        mod = memo.load_frozen_science(path)
        mod.YEAR = YEAR
        mod.YEARS = YEARS
        mod.MONTH_KEYS = MONTH_KEYS
        if tuple(mod.BLIND) != (20.0, 55.0):
            raise RuntimeError("frozen target blind changed")
        return mod

    cached.load_frozen = load_frozen_2023

    def shard_cache(mod: Any, events: list[dict[str, Any]]):
        frozen_path = Path(sys.argv[sys.argv.index("--frozen-source") + 1])
        if blob(frozen_path) != FROZEN_BLOB:
            raise RuntimeError("frozen science source changed")
        if mod.YEAR != YEAR or tuple(mod.YEARS) != YEARS or tuple(mod.MONTH_KEYS) != MONTH_KEYS:
            raise RuntimeError("heldout year/source list changed")
        if not (0 <= a.replica <= mod.PERTURB_REPLICAS):
            raise RuntimeError(f"invalid replica {a.replica}")

        replica, owned, _unowned, stats = builder.build_one_uv_parallel_replica(
            mod, events, a.replica, dead, uvmod, direct, puv
        )
        event_sha = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
        payload = {
            "schema": SCHEMA,
            "scientific_role": "TARGET_EXCLUDED_GMN_2023_HELDOUT_ENGINEERING_CACHE_ONLY",
            "replica": replica,
            "event_count": len(events),
            "event_order_sha256": event_sha,
            "frozen_science_blob": FROZEN_BLOB,
            "cached_runner_blob": CACHED_BLOB,
            "memo_wrapper_blob": MEMO_BLOB,
            "dead_medoid_atomizer_blob": DEAD_BLOB,
            "uv_direct_atomizer_blob": UV_BLOB,
            "direct_replica_builder_blob": DIRECT_BLOB,
            "parallel_uv_bin_atomizer_blob": PUV_BLOB,
            "uv_parallel_builder_blob": BUILDER_BLOB,
            "heldout_year": YEAR,
            "blind_exclusion": list(mod.BLIND),
            "target_information_access": False,
            "target_region_events_accessed": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
            "sonotaco_2013_2014_access": False,
            "gmn_2022_reused_for_selection_after_holdout": False,
            "gmn_2023_access": True,
            "owned_tubes": owned,
            "stats": stats,
        }
        a.shard_output.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(a.shard_output, "wt", encoding="utf-8", compresslevel=6) as fh:
            json.dump(payload, fh, sort_keys=True, separators=(",", ":"), allow_nan=False)
            fh.write("\n")
        print(json.dumps({"RFT_V3_2023_OWNED_REPLICA_SHARD_COMPLETE": replica, "stats": stats}, sort_keys=True), flush=True)
        raise ShardComplete

    cached.build_cache = shard_cache
    sys.argv = [sys.argv[0]] + remaining
    try:
        cached.main()
    except ShardComplete:
        return 0
    raise RuntimeError("cached runner unexpectedly passed v3 2023 shard interception")


if __name__ == "__main__":
    raise SystemExit(main())
