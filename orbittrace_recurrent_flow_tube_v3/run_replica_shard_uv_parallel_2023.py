#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

YEAR = 2023
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
DEV_RESULT_SHA256 = "d5ddbdf5f14a76588924f66a3cb138b888e83071fc3c29fd6522a374b44a37b6"
DEV_PRELABEL_SHA256 = "856c874b49be03a019c7f96780832ada8094b4771527478a4cac6afd3e150c35"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def authorize_development(result_path: Path, prelabel_path: Path) -> None:
    # This function must complete before any GMN 2023 runtime/catalogue is loaded.
    req(sha256(result_path) == DEV_RESULT_SHA256, "RFT v3 development-result authorizer changed")
    req(sha256(prelabel_path) == DEV_PRELABEL_SHA256, "RFT v3 development-prelabel authorizer changed")
    r = json.loads(result_path.read_text())
    pre = json.loads(prelabel_path.read_text())
    req(r["verdict"] == "FAIL_RFT_V2_GMN2022_DEVELOPMENT_VIABILITY", "RFT v2 binding verdict was rewritten")
    owned = r["ablations"]["owned_soft_evidence"]
    exact = {
        "eligible_labels": 359,
        "qualified_matches": 133,
        "recovered_at_25": 18,
        "recovered_at_50": 33,
        "recovered_at_100": 60,
        "recovered_at_500": 120,
        "top100_dominant_precision": 0.6602954645802933,
        "mrr": 0.03157184203024598,
        "fragmentation_median_top500": 1.0,
    }
    for key, value in exact.items():
        if isinstance(value, float):
            req(math.isclose(float(owned[key]), value, rel_tol=0.0, abs_tol=1e-15), f"owned-soft development metric changed: {key}")
        else:
            req(int(owned[key]) == value, f"owned-soft development metric changed: {key}")
    req(int(owned["qualified_matches"]) >= 120, "owned-soft development coverage gate failed")
    req(int(owned["recovered_at_100"]) >= 55, "owned-soft development top100 gate failed")
    req(float(owned["top100_dominant_precision"]) >= 0.60, "owned-soft development precision gate failed")
    req(float(owned["fragmentation_median_top500"]) <= 3.0, "owned-soft development fragmentation gate failed")
    req(r["prelabel_sha256"] == DEV_PRELABEL_SHA256, "development result/prelabel linkage changed")
    req(pre["labels_enter_candidate_generation"] is False and r["labels_enter_candidate_generation"] is False, "development label firewall changed")
    req(pre["blind_exclusion"] == [20.0, 55.0] and r["blind_exclusion"] == [20.0, 55.0], "development blind changed")
    for key in ("target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "sonotaco_2013_2014_access", "gmn_2023_access"):
        req(pre[key] is False and r[key] is False, f"development authorizer has forbidden access: {key}")


def main() -> int:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--replica", type=int, required=True)
    pre.add_argument("--shard-output", type=Path, required=True)
    pre.add_argument("--development-result", type=Path, required=True)
    pre.add_argument("--development-prelabel", type=Path, required=True)
    a, remaining = pre.parse_known_args(sys.argv[1:])

    # Absolute pre-access authorizer. Nothing below this line may load GMN 2023
    # unless the exact preregistered GMN 2022 development evidence is intact.
    authorize_development(a.development_result, a.development_prelabel)
    print("PASS_RFT_V3_GMN2023_PREACCESS_AUTHORIZER", flush=True)

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
            "development_result_sha256": DEV_RESULT_SHA256,
            "development_prelabel_sha256": DEV_PRELABEL_SHA256,
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
