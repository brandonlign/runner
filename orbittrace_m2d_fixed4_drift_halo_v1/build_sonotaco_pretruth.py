#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

YEARS = (2013, 2014)
PARENT_RANKED_SHA256 = "9be0e77d650cabd94eccf0623f005705bb86e84793c76190b0065621631f2ecd"
PARENT_RANKED_BLOB = "e558023e9bb00f75e34a83b84e578012176ce721"
GMN_METHOD_BLOB = "3d2d47c72f703a95713c4f17979f38a8aa3ac75c"
SEED_SOURCE_BLOB = "140f21736ea6615fe111e02d91eaa99b19422da7"
BASELINE_RUNNER_BLOB = "b44e0222e08ae4e85f0ea9a91c95f7b9141f3fb9"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_COMMON = {2013: 15988, 2014: 13258}
EXPECTED_TOTAL = 29246
EXPECTED_CANDIDATES = 888


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    env = [int(r["envelope_member_count"]) for r in rows]
    seed = [int(r["seed_member_count"]) for r in rows]
    halo = [int(r["halo_member_count"]) for r in rows]
    import numpy as np
    e = np.asarray(env, dtype=float); s = np.asarray(seed, dtype=float); h = np.asarray(halo, dtype=float)
    return {
        "candidate_count": len(rows),
        "nonempty_seed_count": int(np.sum(s > 0)),
        "nonempty_halo_count": int(np.sum(h > 0)),
        "halo_strictly_regrows_seed_count": int(np.sum(h > s)),
        "mean_envelope_members": float(np.mean(e)) if len(e) else 0.0,
        "mean_seed_members": float(np.mean(s)) if len(s) else 0.0,
        "mean_halo_members": float(np.mean(h)) if len(h) else 0.0,
        "median_envelope_members": float(np.median(e)) if len(e) else 0.0,
        "median_seed_members": float(np.median(s)) if len(s) else 0.0,
        "median_halo_members": float(np.median(h)) if len(h) else 0.0,
        "max_envelope_members": int(np.max(e)) if len(e) else 0,
        "max_seed_members": int(np.max(s)) if len(s) else 0,
        "max_halo_members": int(np.max(h)) if len(h) else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--parent-ranked", type=Path, required=True)
    ap.add_argument("--method-source", type=Path, required=True)
    ap.add_argument("--seed-source", type=Path, required=True)
    ap.add_argument("--baseline-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.parent_ranked) == PARENT_RANKED_SHA256, "baseline SonotaCo ranked pretruth changed")
    req(blob(a.parent_ranked) == PARENT_RANKED_BLOB, "baseline SonotaCo ranked pretruth blob changed")
    req(blob(a.method_source) == GMN_METHOD_BLOB, "GMN method source changed")
    req(blob(a.seed_source) == SEED_SOURCE_BLOB, "fixed4 seed source changed")
    req(blob(a.baseline_runner) == BASELINE_RUNNER_BLOB, "SonotaCo baseline helper changed")
    req(sha(a.quality_source) == QUALITY_SHA256, "quality runtime changed")
    req(sha(a.v8_result_json) == V8_SHA256, "v8 artifact changed")

    parent = json.loads(a.parent_ranked.read_text())
    req(parent["scientific_role"] == "ZERO_LABEL_EXACT_INTERNAL_MASS_RANKING", "wrong parent role")
    req(parent["truth_used"] is False and parent["shower_labels_accessed"] is False and parent["post_result_parameter_search"] is False, "parent ranking firewall")
    ranked = list(parent["candidates"])
    req(len(ranked) == int(parent["candidate_count"]) == EXPECTED_CANDIDATES, "parent candidate count changed")
    req([int(r["internal_mass_rank"]) for r in ranked] == list(range(1, EXPECTED_CANDIDATES + 1)), "parent rank sequence changed")

    baseline = load(a.baseline_runner, "drift_sonotaco_baseline_helper")
    pooled, ids_by_year, universe = baseline.merge_common(a.rows_root)
    req(len(pooled) == EXPECTED_TOTAL, "common universe size changed")
    req(universe["common_counts"] == {str(y): EXPECTED_COMMON[y] for y in YEARS}, "common year counts changed")
    by_id = {str(r["id"]): baseline.support_event(r) for r in pooled}
    req(len(by_id) == EXPECTED_TOTAL, "duplicate common-universe IDs")
    req(all(int(by_id[eid]["year"]) in YEARS for eid in by_id), "unexpected year")
    req(all(str(eid) in by_id for c in ranked for eid in c["event_ids"]), "parent member absent from common universe")

    method = load(a.method_source, "frozen_gmn_drift_halo_method")
    seed_builder = load(a.seed_source, "frozen_fixed4_seed_sonotaco")
    method.YEARS = YEARS
    seed_builder.YEARS = YEARS
    req(method.CONFIDENCE == 0.95 and method.DIMENSION == 3, "method confidence changed")
    req(method.SOL_SCALE_DEG == 5.0 and method.RADIANT_SCALE_DEG == 4.0, "method physical scales changed")
    req(seed_builder.ANCHOR_MULTIPLICITY == 2 and seed_builder.NEAREST_OTHERS == 3, "seed constants changed")

    q = load(a.quality_source, "drift_sonotaco_quality")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.CORPUS = "orbittrace-m2d-fixed4-drift-halo-v1-sonotaco-transfer"
    support.RANKING_VARIANTS = ("persistence",)
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)

    halos: list[dict[str, Any]] = []
    for pos, candidate in enumerate(ranked, 1):
        row = method.candidate_halo(candidate, by_id, seed_builder, support, base)
        req(row["rank"] == pos, f"rank mismatch {pos}")
        req(row["family_id"] == str(candidate["family_id"]) and row["family_hash"] == str(candidate["family_hash"]), f"identity mismatch {pos}")
        req(set(row["seed_event_ids"]).issubset(str(x) for x in candidate["event_ids"]), f"seed escaped parent {pos}")
        req(set(row["halo_event_ids"]).issubset(str(x) for x in candidate["event_ids"]), f"halo escaped parent {pos}")
        req(set(row["seed_event_ids"]).issubset(row["halo_event_ids"]), f"seed not retained {pos}")
        halos.append(row)
        if pos % 50 == 0 or pos == len(ranked):
            print(json.dumps({"completed": pos, "total": len(ranked)}, sort_keys=True), flush=True)

    payload = {
        "schema": "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH",
        "scientific_role": "NO_RETUNING_SONOTACO_BASELINE_M2D_FIXED4_SEED_OAS_95PCT_DRIFT_HALOS_FROZEN_BEFORE_TRUTH",
        "parent_ranked_sha256": PARENT_RANKED_SHA256,
        "parent_ranked_blob": PARENT_RANKED_BLOB,
        "gmndev_method_blob": GMN_METHOD_BLOB,
        "fixed4_seed_source_blob": SEED_SOURCE_BLOB,
        "baseline_runner_blob": BASELINE_RUNNER_BLOB,
        "common_universe": universe,
        "candidate_count": EXPECTED_CANDIDATES,
        "halos": halos,
        "summary": summarize(halos),
        "confidence": 0.95,
        "chi2_df": 3,
        "chi2_threshold": float(method.CHI2_THRESHOLD),
        "solar_longitude_scale_deg": float(method.SOL_SCALE_DEG),
        "radiant_scale_deg": float(method.RADIANT_SCALE_DEG),
        "speed_log_scale": float(method.SPEED_LOG_SCALE),
        "parent_discovery_membership_changed": False,
        "parent_rank_changed": False,
        "truth_artifact_downloaded": False,
        "truth_used": False,
        "shower_labels_accessed": False,
        "target_information_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH", "sha256": sha(a.output), "summary": payload["summary"]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
