#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

YEAR = 2022
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED_REPLICAS = tuple(range(17))
SHARD_SCHEMA = "RFT_V1_ENGINEERING_REPLICA_SHARD_V1"
FROZEN_V1_BLOB = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"
CACHED_V1_BLOB = "2a599c6e8247eb819a1090591d586526eda6c0c1"
MEMO_V1_BLOB = "8a10e18daa6ba5bf99864a67e8cd059704695735"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def read_shards(root: Path) -> dict[int, dict[str, Any]]:
    shards: dict[int, dict[str, Any]] = {}
    for path in sorted(root.rglob("rft_v1_replica_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            p = json.load(fh)
        req(p.get("schema") == SHARD_SCHEMA, f"bad shard schema: {path}")
        replica = int(p["replica"])
        req(replica not in shards, f"duplicate shard {replica}")
        req(p.get("frozen_science_blob") == FROZEN_V1_BLOB, f"frozen science pin mismatch shard {replica}")
        req(p.get("cached_runner_blob") == CACHED_V1_BLOB, f"cached runner pin mismatch shard {replica}")
        req(p.get("memo_wrapper_blob") == MEMO_V1_BLOB, f"memo wrapper pin mismatch shard {replica}")
        req(p.get("blind_exclusion") == [20.0, 55.0], f"blind mismatch shard {replica}")
        for key in (
            "target_information_access",
            "target_region_events_accessed",
            "maarsy_scientific_access",
            "dms_scientific_access",
            "sonotaco_2013_2014_access",
            "gmn_2023_access",
        ):
            req(p.get(key) is False, f"unauthorized access flag {key} shard {replica}")
        shards[replica] = p
    req(tuple(sorted(shards)) == EXPECTED_REPLICAS, f"incomplete shard set {sorted(shards)}")
    req(len({int(p["event_count"]) for p in shards.values()}) == 1, "shards disagree on event count")
    req(len({str(p["event_order_sha256"]) for p in shards.values()}) == 1, "shards disagree on event order")
    return shards


def unpack_tubes(mod: Any, shard: dict[str, Any], key: str) -> list[Any]:
    return [
        mod.Tube(
            str(v[0]),
            tuple(v[1]),
            tuple(v[2]),
            int(v[3]),
            float(v[4]),
            tuple(float(x) for x in v[5]),
        )
        for v in shard[key]
    ]


def persistence_against_replicas(
    mod: Any,
    base_tubes: list[Any],
    replica_tubes: dict[int, list[Any]],
) -> dict[str, float]:
    """Exact v1 survival fraction, accelerated only by an overlap index.

    A Jaccard value >= 0.5 necessarily has nonzero member overlap, so tubes with
    no shared event can be skipped exactly. Early exit occurs only after the
    preregistered survival condition has already become true for that replica.
    """
    indexes: dict[int, tuple[list[set[str]], dict[str, list[int]]]] = {}
    for replica in range(1, 17):
        sets = [set(map(str, t.members)) for t in replica_tubes[replica]]
        inv: dict[str, list[int]] = defaultdict(list)
        for j, members in enumerate(sets):
            for eid in members:
                inv[eid].append(j)
        indexes[replica] = (sets, inv)

    out: dict[str, float] = {}
    for i, tube in enumerate(base_tubes):
        base = set(map(str, tube.members))
        survive = 0
        for replica in range(1, 17):
            sets, inv = indexes[replica]
            candidate_idx: set[int] = set()
            for eid in base:
                candidate_idx.update(inv.get(eid, ()))
            hit = False
            for j in sorted(candidate_idx):
                other = sets[j]
                inter = len(base & other)
                if inter == 0:
                    continue
                jac = inter / len(base | other)
                if jac >= float(mod.PERSIST_JACCARD) - 1e-15:
                    hit = True
                    break
            survive += int(hit)
        out[str(tube.tid)] = float(survive / int(mod.PERTURB_REPLICAS))
        if (i + 1) % 500 == 0:
            print(f"RFT2 persistence {i+1}/{len(base_tubes)}", flush=True)
    return out


def build_soft_candidates(
    mod: Any,
    base_tubes: list[Any],
    replica_tubes: dict[int, list[Any]],
    lookup: dict[str, dict[str, Any]],
    namespace: str,
) -> dict[str, Any]:
    persistence = persistence_against_replicas(mod, base_tubes, replica_tubes)
    provisional: list[dict[str, Any]] = []
    for tube in base_tubes:
        members, med_res = mod.fit_trim(tube, lookup, do_trim=True)
        if len(members) < int(mod.MIN_EVENTS):
            continue
        med_trans = float(np.median(tube.transition_costs)) if tube.transition_costs else 0.0
        coherence = (
            math.log1p(len(members))
            * math.log1p(int(tube.strata))
            / (1.0 + med_trans + float(med_res))
        )
        provisional.append(
            {
                "tube_id": str(tube.tid),
                "members": tuple(map(str, members)),
                "persistence": float(persistence[str(tube.tid)]),
                "coherence": float(coherence),
                "strata": int(tube.strata),
                "span": float(tube.span),
                "median_transition_cost": med_trans,
                "median_trajectory_residual": float(med_res),
                "representative_cost": float(med_trans + float(med_res)),
            }
        )

    # Frozen exact-member duplicate collapse after trimming.
    best: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in provisional:
        key = tuple(row["members"])
        current = best.get(key)
        new_key = (float(row["representative_cost"]), str(row["tube_id"]))
        if current is None or new_key < (float(current["representative_cost"]), str(current["tube_id"])):
            best[key] = row

    fams: list[dict[str, Any]] = []
    for members, row in best.items():
        family_id = hashlib.sha256((f"{namespace}|" + "|".join(members)).encode()).hexdigest()[:20]
        fams.append(
            {
                "family_id": family_id,
                "event_ids": list(members),
                "persistence": float(row["persistence"]),
                "coherence": float(row["coherence"]),
                "strata": int(row["strata"]),
                "span": float(row["span"]),
                "median_transition_cost": float(row["median_transition_cost"]),
                "median_trajectory_residual": float(row["median_trajectory_residual"]),
                "source_tube_id": str(row["tube_id"]),
            }
        )

    coherence_order = [
        f["family_id"]
        for f in sorted(fams, key=lambda f: (-float(f["coherence"]), str(f["family_id"])))
    ]
    persistence_order = [
        f["family_id"]
        for f in sorted(fams, key=lambda f: (-float(f["persistence"]), str(f["family_id"])))
    ]
    cr = {fid: i + 1 for i, fid in enumerate(coherence_order)}
    pr = {fid: i + 1 for i, fid in enumerate(persistence_order)}
    fused_order = sorted(
        coherence_order,
        key=lambda fid: (cr[fid] + pr[fid], cr[fid], fid),
    )
    by_id = {str(f["family_id"]): f for f in fams}
    return {
        "fused": [by_id[fid] for fid in fused_order],
        "coherence_only": [by_id[fid] for fid in coherence_order],
        "persistence_only": [by_id[fid] for fid in persistence_order],
        "orders": {
            "fused": fused_order,
            "coherence_only": coherence_order,
            "persistence_only": persistence_order,
        },
        "base_tubes": len(base_tubes),
        "posttrim_candidates_before_dedup": len(provisional),
        "deduplicated_candidates": len(fams),
    }


def metric_public(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--shards-dir", type=Path, required=True)
    p.add_argument("--frozen-source", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob(a.frozen_source) == FROZEN_V1_BLOB, "frozen RFT v1 source changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "#839 runtime utility source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN runtime support artifact changed")
    shards = read_shards(a.shards_dir)

    mod = load_module(a.frozen_source, "rft_v2_frozen_v1_science")
    req(int(mod.PERTURB_REPLICAS) == 16, "RFT perturbation count changed")
    req(abs(float(mod.PERSIST_JACCARD) - 0.50) < 1e-15, "RFT Jaccard threshold changed")
    req(int(mod.MIN_EVENTS) == 10, "RFT min event count changed")
    req(abs(float(mod.TRAJECTORY_TRIM) - 2.5) < 1e-15, "RFT trajectory trim changed")

    qmod = load_module(a.quality_source, "rft_v2_frozen_839_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-flow-tube-v2-development-2022-only"
    support.RANKING_VARIANTS = ("soft_evidence_flow",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == [YEAR], f"GMN development runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN 2022 source list changed")

    raw = list(scan[YEAR])
    events = [mod.normalize_event(row) for row in raw]
    req(len(events) == len(raw) == int(shards[0]["event_count"]), "v2 event count differs from shards")
    event_order = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
    req(event_order == str(shards[0]["event_order_sha256"]), "v2 event order differs from shards")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")
    req(all(str(e["id"]).startswith(str(YEAR)) for e in events), "non-2022 event reached v2")
    req(all(str(eid).startswith(str(YEAR)) for eid in hidden), "non-2022 label reached v2 scoring payload")
    lookup = {str(e["id"]): e for e in events}

    unowned = {r: unpack_tubes(mod, shards[r], "unowned_tubes") for r in EXPECTED_REPLICAS}
    owned = {r: unpack_tubes(mod, shards[r], "owned_tubes") for r in EXPECTED_REPLICAS}

    # No hidden labels are referenced by candidate construction or ordering below.
    main_build = build_soft_candidates(mod, unowned[0], unowned, lookup, "RFT2")
    owned_build = build_soft_candidates(mod, owned[0], owned, lookup, "RFT2OWNED")

    prelabel = {
        "scientific_stage": "RFT_V2_GMN2022_PRELABEL_SOFT_EVIDENCE_FLOW",
        "events": len(events),
        "event_order_sha256": event_order,
        "main_hypothesis_generator": "frozen_v1_unowned_cheapest_successor_paths",
        "main_candidate_count": int(main_build["deduplicated_candidates"]),
        "main_base_tubes": int(main_build["base_tubes"]),
        "main_posttrim_before_dedup": int(main_build["posttrim_candidates_before_dedup"]),
        "owned_ablation_candidate_count": int(owned_build["deduplicated_candidates"]),
        "orders": {
            "main_fused": main_build["orders"]["fused"],
            "coherence_only": main_build["orders"]["coherence_only"],
            "persistence_only": main_build["orders"]["persistence_only"],
            "owned_soft_evidence": owned_build["orders"]["fused"],
        },
        "order_sha256": {
            "main_fused": order_sha(main_build["orders"]["fused"]),
            "coherence_only": order_sha(main_build["orders"]["coherence_only"]),
            "persistence_only": order_sha(main_build["orders"]["persistence_only"]),
            "owned_soft_evidence": order_sha(owned_build["orders"]["fused"]),
        },
        "main_candidates": main_build["fused"],
        "owned_ablation_candidates": owned_build["fused"],
        "labels_enter_candidate_generation": False,
        "parameter_search": False,
        "persistence_cutoff": False,
        "fusion_weight_search": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2023_access": False,
    }
    prelabel_path = a.output / "RFT_V2_GMN2022_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha256(prelabel_path)
    print(json.dumps({
        "RFT_V2_PRELABEL_FROZEN": prelabel_sha,
        "main_candidates": prelabel["main_candidate_count"],
        "main_order_sha256": prelabel["order_sha256"]["main_fused"],
        "owned_ablation_candidates": prelabel["owned_ablation_candidate_count"],
    }, sort_keys=True), flush=True)

    # Truth enters only here, after the complete candidate universe/order is durable on disk and hashed.
    main_metrics = mod.metrics(main_build["fused"], hidden)
    coherence_metrics = mod.metrics(main_build["coherence_only"], hidden)
    persistence_metrics = mod.metrics(main_build["persistence_only"], hidden)
    owned_metrics = mod.metrics(owned_build["fused"], hidden)

    top = main_build["fused"][:100]
    high_persist_share = float(np.mean([float(f["persistence"]) >= 0.75 for f in top])) if top else 0.0
    viable = bool(
        int(main_metrics["qualified_matches"]) >= 120
        and int(main_metrics["recovered_at_100"]) >= 55
        and float(main_metrics["top100_dominant_precision"]) >= 0.60
        and float(main_metrics["fragmentation_median_top500"]) <= 3.0
    )
    verdict = "PASS_RFT_V2_GMN2022_DEVELOPMENT_VIABILITY" if viable else "FAIL_RFT_V2_GMN2022_DEVELOPMENT_VIABILITY"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY",
        "events": len(events),
        "retained_candidates": len(main_build["fused"]),
        "metrics": main_metrics,
        "top100_persistence_ge_0p75_share_descriptive": high_persist_share,
        "ablations": {
            "coherence_only": coherence_metrics,
            "owned_soft_evidence": owned_metrics,
            "persistence_only": persistence_metrics,
        },
        "binding_gates": {
            "qualified_ge_120": bool(int(main_metrics["qualified_matches"]) >= 120),
            "recovered_at_100_ge_55": bool(int(main_metrics["recovered_at_100"]) >= 55),
            "top100_precision_ge_0p60": bool(float(main_metrics["top100_dominant_precision"]) >= 0.60),
            "fragmentation_median_le_3": bool(float(main_metrics["fragmentation_median_top500"]) <= 3.0),
        },
        "prelabel_sha256": prelabel_sha,
        "candidate_order_sha256": prelabel["order_sha256"]["main_fused"],
        "labels_enter_candidate_generation": False,
        "parameter_search": False,
        "persistence_cutoff": False,
        "fusion_weight_search": False,
        "post_result_rescue_authorized": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2023_access": False,
    }
    result_path = a.output / "RFT_V2_GMN2022_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events": len(events),
        "candidates": len(main_build["fused"]),
        "metrics": metric_public(main_metrics),
        "binding_gates": result["binding_gates"],
        "descriptive_high_persist_share": high_persist_share,
        "ablations": {k: metric_public(v) for k, v in result["ablations"].items()},
    }, indent=2, sort_keys=True, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
