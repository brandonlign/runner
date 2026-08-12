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

import numpy as np

YEAR = 2023
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED_REPLICAS = tuple(range(17))
SHARD_SCHEMA = "RFT_V3_GMN2023_OWNED_REPLICA_SHARD_V1"
DEV_RESULT_SHA256 = "d5ddbdf5f14a76588924f66a3cb138b888e83071fc3c29fd6522a374b44a37b6"
DEV_PRELABEL_SHA256 = "856c874b49be03a019c7f96780832ada8094b4771527478a4cac6afd3e150c35"
FROZEN_V1_BLOB = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"
V2_HELPER_BLOB = "4128d4d43a02dd583170d35d817866418f1fa880"
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


def authorize_development(result_path: Path, prelabel_path: Path) -> dict[str, Any]:
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
    req(int(owned["qualified_matches"]) >= 120, "owned-soft coverage qualification failed")
    req(int(owned["recovered_at_100"]) >= 55, "owned-soft top100 qualification failed")
    req(float(owned["top100_dominant_precision"]) >= 0.60, "owned-soft precision qualification failed")
    req(float(owned["fragmentation_median_top500"]) <= 3.0, "owned-soft fragmentation qualification failed")
    req(r["prelabel_sha256"] == DEV_PRELABEL_SHA256, "development result/prelabel linkage changed")
    req(pre["labels_enter_candidate_generation"] is False and r["labels_enter_candidate_generation"] is False, "development label firewall changed")
    req(pre["blind_exclusion"] == [20.0, 55.0] and r["blind_exclusion"] == [20.0, 55.0], "development blind changed")
    for key in ("target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "sonotaco_2013_2014_access", "gmn_2023_access"):
        req(pre[key] is False and r[key] is False, f"development authorizer has forbidden access: {key}")
    return {"result": r, "prelabel": pre}


def read_shards(root: Path) -> dict[int, dict[str, Any]]:
    shards: dict[int, dict[str, Any]] = {}
    for path in sorted(root.rglob("rft_v3_2023_replica_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            p = json.load(fh)
        req(p.get("schema") == SHARD_SCHEMA, f"bad heldout shard schema: {path}")
        replica = int(p["replica"])
        req(replica not in shards, f"duplicate heldout shard {replica}")
        req(p.get("scientific_role") == "TARGET_EXCLUDED_GMN_2023_HELDOUT_ENGINEERING_CACHE_ONLY", f"heldout shard role changed {replica}")
        req(p.get("frozen_science_blob") == FROZEN_V1_BLOB, f"frozen science pin mismatch shard {replica}")
        req(p.get("development_result_sha256") == DEV_RESULT_SHA256 and p.get("development_prelabel_sha256") == DEV_PRELABEL_SHA256, f"authorizer pin mismatch shard {replica}")
        req(p.get("heldout_year") == YEAR, f"heldout year changed shard {replica}")
        req(p.get("blind_exclusion") == [20.0, 55.0], f"blind mismatch shard {replica}")
        req(p.get("gmn_2023_access") is True, f"2023 access provenance missing shard {replica}")
        req(p.get("gmn_2022_reused_for_selection_after_holdout") is False, f"2022 reused after holdout shard {replica}")
        for key in ("target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "sonotaco_2013_2014_access"):
            req(p.get(key) is False, f"unauthorized access flag {key} shard {replica}")
        req("owned_tubes" in p and "unowned_tubes" not in p, f"v3 shard must contain owned hypotheses only: {replica}")
        shards[replica] = p
    req(tuple(sorted(shards)) == EXPECTED_REPLICAS, f"incomplete heldout shard set {sorted(shards)}")
    req(len({int(p["event_count"]) for p in shards.values()}) == 1, "heldout shards disagree on event count")
    req(len({str(p["event_order_sha256"]) for p in shards.values()}) == 1, "heldout shards disagree on event order")
    return shards


def unpack_tubes(mod: Any, shard: dict[str, Any]) -> list[Any]:
    return [
        mod.Tube(
            str(v[0]), tuple(v[1]), tuple(v[2]), int(v[3]), float(v[4]), tuple(float(x) for x in v[5])
        )
        for v in shard["owned_tubes"]
    ]


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--development-result", type=Path, required=True)
    p.add_argument("--development-prelabel", type=Path, required=True)
    p.add_argument("--shards-dir", type=Path, required=True)
    p.add_argument("--frozen-source", type=Path, required=True)
    p.add_argument("--v2-helper-source", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # Re-authorize exact development evidence before parsing heldout catalogue.
    authorize_development(a.development_result, a.development_prelabel)
    req(git_blob(a.frozen_source) == FROZEN_V1_BLOB, "frozen RFT geometry source changed")
    req(git_blob(a.v2_helper_source) == V2_HELPER_BLOB, "exact v2 soft-evidence helper changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "#839 runtime utility source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN runtime support artifact changed")
    shards = read_shards(a.shards_dir)

    mod = load_module(a.frozen_source, "rft_v3_frozen_geometry")
    mod.YEAR = YEAR
    mod.YEARS = YEARS
    mod.MONTH_KEYS = MONTH_KEYS
    req(tuple(mod.BLIND) == BLIND, "target blind changed")
    req(mod.BIN_WIDTH == 2.0 and mod.KNN == 4 and mod.MIN_ATOM == 4, "local atom constants changed")
    req(mod.MIN_STRATA == 3 and mod.MIN_SPAN == 6.0 and mod.MIN_EVENTS == 10, "tube constants changed")
    req(mod.PERTURB_REPLICAS == 16 and mod.PERTURB_RAD_DEG == 0.35 and mod.PERTURB_SPEED_FRAC == 0.01, "perturbation constants changed")
    req(mod.PERSIST_JACCARD == 0.50 and mod.TRAJECTORY_TRIM == 2.5, "persistence/trim constants changed")
    v2 = load_module(a.v2_helper_source, "rft_v3_exact_v2_soft_evidence")

    qmod = load_module(a.quality_source, "rft_v3_heldout_frozen_839_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-rft-v3-owned-soft-evidence-heldout-2023-only"
    support.RANKING_VARIANTS = ("owned_soft_evidence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == [YEAR], f"heldout runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN 2023 source list changed")

    raw = list(scan[YEAR])
    events = [mod.normalize_event(row) for row in raw]
    req(len(events) == len(raw) == int(shards[0]["event_count"]), "heldout event count differs from shards")
    event_order = hashlib.sha256("\n".join(str(e["id"]) for e in events).encode()).hexdigest()
    req(event_order == str(shards[0]["event_order_sha256"]), "heldout event order differs from shards")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")
    req(all(str(e["id"]).startswith(str(YEAR)) for e in events), "non-2023 event reached holdout")
    req(all(str(eid).startswith(str(YEAR)) for eid in hidden), "non-2023 label reached holdout")
    lookup = {str(e["id"]): e for e in events}
    owned = {r: unpack_tubes(mod, shards[r]) for r in EXPECTED_REPLICAS}

    # Exact preregistered v2 owned-soft-evidence helper and namespace/tie semantics.
    build = v2.build_soft_candidates(mod, owned[0], owned, lookup, "RFT2OWNED")
    order = list(map(str, build["orders"]["fused"]))
    prelabel = {
        "scientific_stage": "RFT_V3_GMN2023_HELDOUT_PRELABEL",
        "method_provenance": "exact preregistered RFT v2 owned_soft_evidence ablation",
        "events": len(events),
        "event_order_sha256": event_order,
        "candidate_count": int(build["deduplicated_candidates"]),
        "base_owned_tubes": int(build["base_tubes"]),
        "posttrim_before_dedup": int(build["posttrim_candidates_before_dedup"]),
        "candidate_namespace": "RFT2OWNED",
        "candidate_order": order,
        "candidate_order_sha256": order_sha(order),
        "candidates": build["fused"],
        "labels_enter_candidate_generation": False,
        "unowned_hypotheses_used": False,
        "persistence_cutoff": False,
        "parameter_search": False,
        "fusion_weight_search": False,
        "rerank_used": False,
        "blind_exclusion": [20.0, 55.0],
        "gmn_2023_access": True,
        "gmn_2022_reused_for_selection_after_holdout": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "sonotaco_2013_2014_access": False,
    }
    pre_path = a.output / "RFT_V3_GMN2023_HELDOUT_PRELABEL.json"
    pre_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    pre_sha = sha256(pre_path)
    print(json.dumps({"RFT_V3_GMN2023_PRELABEL_FROZEN": pre_sha, "candidate_count": len(order), "candidate_order_sha256": prelabel["candidate_order_sha256"]}, sort_keys=True), flush=True)

    # Heldout truth is used only after the complete candidate universe/order is durable and hashed.
    m = mod.metrics(build["fused"], hidden)
    gates = {
        "qualified_matches_ge_120": bool(int(m["qualified_matches"]) >= 120),
        "recovered_at_100_ge_58": bool(int(m["recovered_at_100"]) >= 58),
        "recovered_at_50_ge_35": bool(int(m["recovered_at_50"]) >= 35),
        "top100_dominant_precision_ge_0p65": bool(float(m["top100_dominant_precision"]) >= 0.65),
        "fragmentation_median_top500_le_3": bool(float(m["fragmentation_median_top500"]) <= 3.0),
    }
    passed = sum(bool(v) for v in gates.values())
    if passed == 5:
        verdict = "PASS_RFT_V3_GMN2023_HELDOUT"
    elif passed >= 4 and int(m["recovered_at_100"]) >= 52:
        verdict = "USEFUL_BUT_INSUFFICIENT_RFT_V3_GMN2023_HELDOUT"
    else:
        verdict = "FAIL_RFT_V3_GMN2023_HELDOUT"
    failures = {
        "coverage_failure": bool(int(m["qualified_matches"]) < 120),
        "ranking_failure": bool(int(m["qualified_matches"]) >= 120 and int(m["recovered_at_100"]) < 58),
        "fragmentation_failure": bool(float(m["fragmentation_median_top500"]) > 3.0),
        "purity_failure": bool(float(m["top100_dominant_precision"]) < 0.65),
    }
    high_persist_share = float(np.mean([float(f["persistence"]) >= 0.75 for f in build["fused"][:100]])) if build["fused"] else 0.0
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2023_ONE_SHOT_HELDOUT_ONLY",
        "method": "exact preregistered RFT v2 owned_soft_evidence variant promoted as v3",
        "development_result_sha256": DEV_RESULT_SHA256,
        "development_prelabel_sha256": DEV_PRELABEL_SHA256,
        "events": len(events),
        "retained_candidates": len(build["fused"]),
        "metrics": m,
        "numerical_gates": gates,
        "numerical_gates_passed": passed,
        "failure_classes": failures,
        "top100_persistence_ge_0p75_share_descriptive": high_persist_share,
        "heldout_prelabel_sha256": pre_sha,
        "candidate_order_sha256": prelabel["candidate_order_sha256"],
        "gmn_2023_ablation_run": False,
        "gmn_2022_reused_for_selection_after_holdout": False,
        "labels_enter_candidate_generation": False,
        "unowned_hypotheses_used": False,
        "persistence_cutoff": False,
        "parameter_search": False,
        "threshold_search": False,
        "score_change": False,
        "candidate_change": False,
        "rerank_used": False,
        "fusion_weight_search": False,
        "source_quota_selected": False,
        "post_result_rescue_authorized": False,
        "gmn_2023_access": True,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
    }
    result_path = a.output / "RFT_V3_GMN2023_HELDOUT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events": len(events),
        "candidates": len(build["fused"]),
        "metrics": {k: v for k, v in m.items() if k != "first_rank_by_label"},
        "numerical_gates": gates,
        "failure_classes": failures,
        "descriptive_high_persist_share": high_persist_share,
    }, indent=2, sort_keys=True, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
