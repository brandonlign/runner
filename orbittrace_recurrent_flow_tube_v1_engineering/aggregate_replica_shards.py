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


def read_shards(root: Path) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for path in sorted(root.rglob("rft_v1_replica_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            p = json.load(fh)
        if p.get("schema") != SCHEMA:
            raise RuntimeError(f"bad shard schema: {path}")
        r = int(p["replica"])
        if r in out:
            raise RuntimeError(f"duplicate shard {r}")
        if p.get("frozen_science_blob") != FROZEN_BLOB or p.get("cached_runner_blob") != CACHED_BLOB or p.get("memo_wrapper_blob") != MEMO_BLOB:
            raise RuntimeError(f"source pin mismatch in shard {r}")
        if p.get("blind_exclusion") != [20.0, 55.0]:
            raise RuntimeError(f"firewall mismatch in shard {r}")
        for key in ("target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "sonotaco_2013_2014_access", "gmn_2023_access"):
            if p.get(key) is not False:
                raise RuntimeError(f"unauthorized access flag {key} in shard {r}")
        out[r] = p
    return out


def main() -> int:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--shards-dir", type=Path, required=True)
    a, remaining = pre.parse_known_args(sys.argv[1:])
    shards = read_shards(a.shards_dir)
    expected = list(range(17))
    if sorted(shards) != expected:
        raise RuntimeError(f"incomplete shard set: {sorted(shards)}")
    if len({int(p["event_count"]) for p in shards.values()}) != 1 or len({str(p["event_order_sha256"]) for p in shards.values()}) != 1:
        raise RuntimeError("replica shards disagree on event universe")

    here = Path(__file__).resolve().parent
    memo_path = here / "run_development_cached_memo.py"
    cached_path = here / "run_development_cached.py"
    if blob(memo_path) != MEMO_BLOB or blob(cached_path) != CACHED_BLOB:
        raise RuntimeError("engineering source pin changed")
    memo = load(memo_path, "rft_aggregate_memo")
    cached = memo.load_cached_runner(cached_path)
    cached.load_frozen = memo.load_frozen_science

    expected_count = int(shards[0]["event_count"])
    expected_order = str(shards[0]["event_order_sha256"])

    def shard_cache(mod: Any, events: list[dict[str, Any]]):
        if len(events) != expected_count:
            raise RuntimeError("aggregator event count differs from shards")
        event_sha = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
        if event_sha != expected_order:
            raise RuntimeError("aggregator event order differs from shards")
        replicas = list(range(0, mod.PERTURB_REPLICAS + 1))
        if replicas != expected:
            raise RuntimeError("frozen perturbation count changed")
        atom_cache = {r: [] for r in replicas}
        tube_cache: dict[tuple[int, bool], list[Any]] = {}
        for r in replicas:
            for ownership, key in ((True, "owned_tubes"), (False, "unowned_tubes")):
                tube_cache[(r, ownership)] = [
                    mod.Tube(str(v[0]), tuple(v[1]), tuple(v[2]), int(v[3]), float(v[4]), tuple(float(x) for x in v[5]))
                    for v in shards[r][key]
                ]
        print(json.dumps({"RFT_MATRIX_SHARDS_ACCEPTED": replicas, "replica_stats": [shards[r]["stats"] for r in replicas]}, sort_keys=True), flush=True)
        return atom_cache, tube_cache

    cached.build_cache = shard_cache
    sys.argv = [sys.argv[0]] + remaining
    return int(cached.main())


if __name__ == "__main__":
    raise SystemExit(main())
