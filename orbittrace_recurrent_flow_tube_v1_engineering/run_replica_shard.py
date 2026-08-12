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
    memo_path = here / "run_development_cached_memo.py"
    cached_path = here / "run_development_cached.py"
    if blob(memo_path) != MEMO_BLOB or blob(cached_path) != CACHED_BLOB:
        raise RuntimeError("engineering source pin changed")
    memo = load(memo_path, "rft_shard_memo")
    cached = memo.load_cached_runner(cached_path)
    cached.load_frozen = memo.load_frozen_science

    def shard_cache(mod: Any, events: list[dict[str, Any]]):
        if blob(Path(sys.argv[sys.argv.index("--frozen-source") + 1])) != FROZEN_BLOB:
            raise RuntimeError("frozen science source changed")
        if not (0 <= a.replica <= mod.PERTURB_REPLICAS):
            raise RuntimeError(f"invalid replica {a.replica}")
        memo._WORKER_MOD = mod
        memo._WORKER_EVENTS = events
        replica, owned, unowned, stats = memo._replica_worker(a.replica)
        event_sha = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
        payload = {
            "schema": SCHEMA,
            "replica": replica,
            "event_count": len(events),
            "event_order_sha256": event_sha,
            "frozen_science_blob": FROZEN_BLOB,
            "cached_runner_blob": CACHED_BLOB,
            "memo_wrapper_blob": MEMO_BLOB,
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
        print(json.dumps({"RFT_REPLICA_SHARD_COMPLETE": replica, "stats": stats}, sort_keys=True), flush=True)
        raise ShardComplete

    cached.build_cache = shard_cache
    sys.argv = [sys.argv[0]] + remaining
    try:
        cached.main()
    except ShardComplete:
        return 0
    raise RuntimeError("cached runner unexpectedly passed shard interception")


if __name__ == "__main__":
    raise SystemExit(main())
