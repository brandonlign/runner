#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))

EXPECTED_BASELINE_GZIP_SHA256 = "6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100"
EXPECTED_BASELINE_INNER_SHA256 = "7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53"
EXPECTED_BASELINE_CANDIDATES = 8469
EXPECTED_EVENT_COUNT = 549636

EXPECTED_METHOD_BLOB = "3d2d47c72f703a95713c4f17979f38a8aa3ac75c"
EXPECTED_SEED_BLOB = "140f21736ea6615fe111e02d91eaa99b19422da7"
EXPECTED_QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
EXPECTED_V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_BLIND_PART_BLOBS = {
    "part00.b64": "ed5c488fb4bf0ed5ae4b1c43f4cfb008501936e1",
    "part01.b64": "65b96befa5726581af74ad11d982fee18de0e4e7",
    "part02.b64": "04175711594c46d67cdb759cbee3a3e93819ce8d",
    "part03.b64": "2b890713e681f3b2372b29577cd66997dada8e07",
}
EXPECTED_BLIND_SOURCE_BYTES = 24135


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def decode_blind_loader(parts_root: Path, output: Path) -> Any:
    parts = sorted(parts_root.glob("part*.b64"))
    req([p.name for p in parts] == list(EXPECTED_BLIND_PART_BLOBS), f"blind source parts changed: {[p.name for p in parts]}")
    for part in parts:
        req(git_blob(part) == EXPECTED_BLIND_PART_BLOBS[part.name], f"blind source blob changed: {part.name}")
    encoded = "".join("".join(p.read_text().split()) for p in parts)
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    req(len(raw) == EXPECTED_BLIND_SOURCE_BYTES, f"blind loader byte count changed: {len(raw)}")
    output.write_bytes(raw)
    return load_module(output, "m2d_final_target_blind_catalogue_loader")


def normalize_catalogue_event(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(row["id"]),
        "year": int(row["year"]),
        "sol": float(row["sol"]),
        "lon": float(row["sun_lon"]),
        "lat": float(row["ecl_lat"]),
        "vg": float(row["vg"]),
    }
    req(out["year"] in YEARS, f"unexpected year for {out['id']}")
    req(all(math.isfinite(float(out[k])) for k in ("sol", "lon", "lat", "vg")), f"nonfinite event {out['id']}")
    req(out["vg"] > 0.0, f"nonpositive speed {out['id']}")
    return out


def load_baseline(path: Path) -> tuple[dict[str, Any], str, str]:
    gz = path.read_bytes()
    gzip_sha = sha256_bytes(gz)
    req(gzip_sha == EXPECTED_BASELINE_GZIP_SHA256, f"baseline gzip SHA changed: {gzip_sha}")
    raw = gzip.decompress(gz)
    inner_sha = sha256_bytes(raw)
    req(inner_sha == EXPECTED_BASELINE_INNER_SHA256, f"baseline inner SHA changed: {inner_sha}")
    pre = json.loads(raw)
    req(pre["schema"] == "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH", "wrong baseline schema")
    req(pre["scientific_role"] == "TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL", "wrong baseline scientific role")
    req(pre["configuration"]["years"] == [2022, 2023], "wrong baseline years")
    req(pre["configuration"]["target_interval_exclusion"] is None, "baseline excluded a target interval")
    req(pre["shower_truth_used"] is False, "baseline used shower truth")
    req(pre["orbittrace_target_information_access"] is False, "baseline used target information")
    req(pre["orbittrace_canonical_members_access"] is False, "baseline used canonical members")
    req(pre["prior_orbittrace_reveal_access"] is False, "baseline used prior reveal")
    req(pre["post_result_parameter_search"] is False, "baseline used post-result parameter search")
    req(pre["candidate_count"] == len(pre["candidates"]) == EXPECTED_BASELINE_CANDIDATES, "baseline candidate count changed")
    req([int(c["rank"]) for c in pre["candidates"]] == list(range(1, EXPECTED_BASELINE_CANDIDATES + 1)), "baseline rank order changed")
    return pre, gzip_sha, inner_sha


def parent_identity(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(
        (
            str(int(candidate["rank"]))
            + "|"
            + str(candidate["family_hash"])
            + "|"
            + "|".join(sorted(map(str, candidate["event_ids"])))
        ).encode()
    ).hexdigest()


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parent = np.asarray([int(r["parent_member_count"]) for r in rows], dtype=float)
    seed = np.asarray([int(r["seed_member_count"]) for r in rows], dtype=float)
    halo = np.asarray([int(r["halo_member_count"]) for r in rows], dtype=float)
    return {
        "candidate_count": len(rows),
        "nonempty_seed_count": int(np.sum(seed > 0)),
        "nonempty_halo_count": int(np.sum(halo > 0)),
        "strict_seed_regrowth_count": int(np.sum(halo > seed)),
        "mean_parent_members": float(np.mean(parent)),
        "mean_seed_members": float(np.mean(seed)),
        "mean_halo_members": float(np.mean(halo)),
        "median_parent_members": float(np.median(parent)),
        "median_seed_members": float(np.median(seed)),
        "median_halo_members": float(np.median(halo)),
        "max_parent_members": int(np.max(parent)),
        "max_seed_members": int(np.max(seed)),
        "max_halo_members": int(np.max(halo)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-pretruth", type=Path, required=True)
    ap.add_argument("--blind-source-parts", type=Path, required=True)
    ap.add_argument("--method-source", type=Path, required=True)
    ap.add_argument("--seed-source", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--scratch-loader", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.scratch_loader.parent.mkdir(parents=True, exist_ok=True)

    req(git_blob(a.method_source) == EXPECTED_METHOD_BLOB, "frozen drift-halo method source changed")
    req(git_blob(a.seed_source) == EXPECTED_SEED_BLOB, "frozen fixed4 seed source changed")
    req(sha256(a.quality_source) == EXPECTED_QUALITY_SHA256, "frozen runtime utility changed")
    req(sha256(a.v8_result_json) == EXPECTED_V8_SHA256, "frozen v8 support artifact changed")

    method = load_module(a.method_source, "m2d_final_target_frozen_halo_method")
    seed = load_module(a.seed_source, "m2d_final_target_frozen_fixed4_seed")
    req(tuple(method.YEARS) == YEARS, "method years changed")
    req(abs(float(method.SOL_SCALE_DEG) - 5.0) < 1e-15, "solar-longitude scale changed")
    req(abs(float(method.RADIANT_SCALE_DEG) - 4.0) < 1e-15, "radiant scale changed")
    req(abs(float(method.SPEED_LOG_SCALE) - math.log(1.1)) < 1e-15, "speed scale changed")
    req(abs(float(method.CONFIDENCE) - 0.95) < 1e-15 and int(method.DIMENSION) == 3, "halo confidence/dimension changed")
    req(abs(float(method.CHI2_THRESHOLD) - 7.814727903251179) < 1e-12, "chi-square threshold changed")
    req(int(seed.ANCHOR_MULTIPLICITY) == 2 and int(seed.NEAREST_OTHERS) == 3, "fixed4 seed constants changed")

    baseline, baseline_gzip_sha, baseline_inner_sha = load_baseline(a.baseline_pretruth)

    blind = decode_blind_loader(a.blind_source_parts, a.scratch_loader)
    blind.YEARS = YEARS
    blind.MONTH_KEYS = MONTH_KEYS
    blind_args = types.SimpleNamespace(
        candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,
        scorer_parts=a.scorer_parts,
    )
    _blind_candidate, blind_base, _blind_scorer = blind.load_sources(blind_args)
    by_year, catalogue_sources = blind.parse_catalogue(blind_base)
    req(sorted(by_year) == list(YEARS), f"blind catalogue years changed: {sorted(by_year)}")
    rows: list[dict[str, Any]] = []
    for year in YEARS:
        rows.extend(normalize_catalogue_event(e) for e in by_year[year])
    req(len(rows) == EXPECTED_EVENT_COUNT, f"blind catalogue event count changed: {len(rows)}")
    by_id = {str(e["id"]): e for e in rows}
    req(len(by_id) == EXPECTED_EVENT_COUNT, "duplicate IDs in blind catalogue")
    req(all(str(eid) in by_id for c in baseline["candidates"] for eid in c["event_ids"]), "baseline parent references event absent from blind catalogue")

    q = load_module(a.quality_source, "m2d_final_target_quality_runtime")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-fixed4-drift-halo-v1-final-blind-target-application"
    support.RANKING_VARIANTS = ("persistence",)
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    req(callable(getattr(support, "exact_anchor_distances", None)), "exact fixed4 anchor-distance function missing")

    halo_rows: list[dict[str, Any]] = []
    parent_order: list[dict[str, Any]] = []
    for index, original in enumerate(baseline["candidates"], 1):
        rank = int(original["rank"])
        req(rank == index, f"baseline rank discontinuity at {index}")
        parent_ids = sorted(map(str, original["event_ids"]))
        req(len(parent_ids) == len(set(parent_ids)) == int(original["member_count"]), f"parent membership mismatch rank {rank}")
        candidate = dict(original)
        candidate["internal_mass_rank"] = rank
        candidate["family_id"] = str(original["family_hash"])
        h = method.candidate_halo(candidate, by_id, seed, support, base)
        req(int(h["rank"]) == rank, f"halo rank drift {rank}")
        req(str(h["family_hash"]) == str(original["family_hash"]), f"halo family-hash drift {rank}")
        req(int(h["envelope_member_count"]) == len(parent_ids), f"halo parent-size drift {rank}")
        req(set(h["halo_event_ids"]).issubset(parent_ids), f"halo escaped parent at rank {rank}")
        req(set(h["seed_event_ids"]).issubset(h["halo_event_ids"]), f"seed not retained at rank {rank}")

        row = {
            "rank": rank,
            "family_hash": str(original["family_hash"]),
            "parent_identity_sha256": parent_identity(original),
            "parent_member_count": len(parent_ids),
            "parent_event_ids": parent_ids,
            "internal_2d_mass": float(original["internal_2d_mass"]),
            "modal_contrast": float(original["modal_contrast"]),
            "window_centers": list(original.get("window_centers", [])),
            "seed_member_count": int(h["seed_member_count"]),
            "seed_event_ids": list(h["seed_event_ids"]),
            "halo_member_count": int(h["halo_member_count"]),
            "halo_event_ids": list(h["halo_event_ids"]),
            "annual": h["annual"],
        }
        halo_rows.append(row)
        parent_order.append(
            {
                "rank": rank,
                "family_hash": str(original["family_hash"]),
                "parent_identity_sha256": row["parent_identity_sha256"],
            }
        )
        if rank <= 10 or rank % 100 == 0:
            print(
                json.dumps(
                    {
                        "rank": rank,
                        "parent": row["parent_member_count"],
                        "seed": row["seed_member_count"],
                        "halo": row["halo_member_count"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    req([r["rank"] for r in halo_rows] == list(range(1, EXPECTED_BASELINE_CANDIDATES + 1)), "final halo order changed")
    baseline_order = [
        {
            "rank": int(c["rank"]),
            "family_hash": str(c["family_hash"]),
            "parent_identity_sha256": parent_identity(c),
        }
        for c in baseline["candidates"]
    ]
    req(parent_order == baseline_order, "complete parent order changed")

    parent_order_sha = sha256_bytes(json.dumps(parent_order, separators=(",", ":"), sort_keys=True).encode())
    payload = {
        "schema": "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_FINAL_TARGET_PRETRUTH",
        "scientific_role": "COMPLETE_ALREADY_BLIND_M2D_RANKING_WITH_FROZEN_FIXED4_SEEDED_95PCT_OAS_DRIFT_HALOS_BEFORE_TARGET_REFERENCE_ACCESS",
        "years": list(YEARS),
        "baseline_pretruth_gzip_sha256": baseline_gzip_sha,
        "baseline_pretruth_inner_sha256": baseline_inner_sha,
        "baseline_candidate_count": EXPECTED_BASELINE_CANDIDATES,
        "blind_catalogue_event_count": EXPECTED_EVENT_COUNT,
        "catalogue_sources": catalogue_sources,
        "frozen_method_source_blob": EXPECTED_METHOD_BLOB,
        "frozen_seed_source_blob": EXPECTED_SEED_BLOB,
        "quality_source_sha256": EXPECTED_QUALITY_SHA256,
        "v8_result_sha256": EXPECTED_V8_SHA256,
        "fixed4_anchor_multiplicity": 2,
        "fixed4_neighbor_count": 3,
        "solar_longitude_scale_deg": 5.0,
        "radiant_scale_deg": 4.0,
        "speed_log_scale": math.log(1.1),
        "confidence": 0.95,
        "dimension": 3,
        "chi2_threshold": float(method.CHI2_THRESHOLD),
        "drift_fit_rule": "annual_unweighted_affine_sun_centered_radiant_speed_numpy_lstsq_rcond_none_rank_lt2_zero_slope",
        "covariance_rule": "sklearn_OAS_on_three_dimensional_seed_drift_residuals",
        "selection_rule": "retain_fixed4_seed_union_parent_envelope_events_with_mahalanobis_sq_le_chi2_95pct_df3",
        "parent_rank_changed": False,
        "parent_membership_changed": False,
        "parent_order_sha256": parent_order_sha,
        "candidate_count": len(halo_rows),
        "halos": halo_rows,
        "summary": summarize(halo_rows),
        "target_reference_access": False,
        "target_information_used": False,
        "target_coordinates_accessed": False,
        "canonical_target_ids_accessed": False,
        "prior_target_reveal_artifact_accessed": False,
        "target_aware_parent_selection": False,
        "reranking_used": False,
        "family_merge_used": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "verdict": "PASS_M2D_FIXED4_DRIFT_HALO_V1_FINAL_TARGET_PRETRUTH_SEALED",
                "sha256": sha256(a.output),
                "summary": payload["summary"],
                "parent_order_sha256": parent_order_sha,
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
