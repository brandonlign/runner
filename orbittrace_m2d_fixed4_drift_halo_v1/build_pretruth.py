#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import chi2
from sklearn.covariance import OAS

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
FAIR_PRETRUTH_SHA256 = "8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SEED_SOURCE_BLOB = "140f21736ea6615fe111e02d91eaa99b19422da7"
EXPECTED_COUNTS = {"2022": 315024, "2023": 423658}
EXPECTED_TOTAL = 738682
SOL_SCALE_DEG = 5.0
RADIANT_SCALE_DEG = 4.0
SPEED_LOG_SCALE = math.log(1.1)
CONFIDENCE = 0.95
DIMENSION = 3
CHI2_THRESHOLD = float(chi2.ppf(CONFIDENCE, df=DIMENSION))


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


def wrap_signed_deg(x: np.ndarray | float) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    return ((arr + 180.0) % 360.0) - 180.0


def circular_mean_deg(values: list[float]) -> float:
    a = np.deg2rad(np.asarray(values, dtype=float))
    req(len(a) > 0 and np.all(np.isfinite(a)), "invalid circular mean input")
    s, c = float(np.mean(np.sin(a))), float(np.mean(np.cos(a)))
    req(abs(s) + abs(c) > 1e-15, "undefined circular mean")
    return float(np.rad2deg(math.atan2(s, c)) % 360.0)


def transform(rows: list[dict[str, Any]], centers: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    req(rows, "empty transform rows")
    sol = wrap_signed_deg([float(e["sol"]) - centers["sol_deg"] for e in rows]) / SOL_SCALE_DEG
    lon = wrap_signed_deg([float(e["lon"]) - centers["lon_deg"] for e in rows]) / RADIANT_SCALE_DEG
    lat = (np.asarray([float(e["lat"]) for e in rows]) - centers["lat_deg"]) / RADIANT_SCALE_DEG
    vg = np.asarray([float(e["vg"]) for e in rows], dtype=float)
    req(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    speed = np.log(vg / centers["vg_km_s"]) / SPEED_LOG_SCALE
    x = np.column_stack([np.ones(len(rows), dtype=float), sol])
    y = np.column_stack([lon, lat, speed])
    req(np.all(np.isfinite(x)) and np.all(np.isfinite(y)), "nonfinite transformed rows")
    return x, y


def annual_halo(envelope_rows: list[dict[str, Any]], seed_ids: list[str]) -> dict[str, Any]:
    envelope_rows = sorted(envelope_rows, key=lambda e: str(e["id"]))
    envelope_ids = [str(e["id"]) for e in envelope_rows]
    seed_set = set(str(x) for x in seed_ids)
    req(seed_set.issubset(envelope_ids), "seed escaped annual envelope")
    seed_rows = [e for e in envelope_rows if str(e["id"]) in seed_set]
    req(len(seed_rows) == len(seed_set), "seed row mismatch")
    if len(seed_rows) < 4:
        return {
            "seed_event_ids": sorted(seed_set),
            "seed_member_count": len(seed_rows),
            "halo_event_ids": [],
            "halo_member_count": 0,
            "fit_status": "INSUFFICIENT_FIXED4_SEED_LT4",
            "event_scores": [],
        }

    centers = {
        "sol_deg": circular_mean_deg([float(e["sol"]) for e in seed_rows]),
        "lon_deg": circular_mean_deg([float(e["lon"]) for e in seed_rows]),
        "lat_deg": float(np.mean([float(e["lat"]) for e in seed_rows])),
        "vg_km_s": float(np.exp(np.mean(np.log([float(e["vg"]) for e in seed_rows])))),
    }
    sx, sy = transform(seed_rows, centers)
    rank = int(np.linalg.matrix_rank(sx))
    if rank >= 2:
        beta = np.linalg.lstsq(sx, sy, rcond=None)[0]
        fit_rule = "unweighted_numpy_lstsq_rcond_none"
    else:
        beta = np.vstack([np.mean(sy, axis=0), np.zeros(DIMENSION, dtype=float)])
        fit_rule = "rank_lt2_zero_slope_arithmetic_mean_intercept"
    seed_residual = sy - sx @ beta
    req(seed_residual.shape == (len(seed_rows), DIMENSION), "seed residual shape")
    oas = OAS(store_precision=True, assume_centered=False).fit(seed_residual)
    covariance = np.asarray(oas.covariance_, dtype=float)
    precision = np.asarray(oas.precision_, dtype=float)
    location = np.asarray(oas.location_, dtype=float)
    req(covariance.shape == (DIMENSION, DIMENSION) and precision.shape == covariance.shape, "OAS shape")
    req(np.all(np.isfinite(covariance)) and np.all(np.isfinite(precision)) and np.all(np.isfinite(location)), "OAS nonfinite")

    ex, ey = transform(envelope_rows, centers)
    residual = ey - ex @ beta
    delta = residual - location[None, :]
    d2 = np.einsum("ij,jk,ik->i", delta, precision, delta)
    req(d2.shape == (len(envelope_rows),) and np.all(np.isfinite(d2)), "Mahalanobis nonfinite")
    d2 = np.maximum(d2, 0.0)
    selected = {envelope_ids[i] for i, v in enumerate(d2) if float(v) <= CHI2_THRESHOLD}
    selected.update(seed_set)
    halo = sorted(selected)
    scores = [
        {
            "event_id": envelope_ids[i],
            "mahalanobis_sq": float(d2[i]),
            "inside_95pct_ellipsoid": bool(float(d2[i]) <= CHI2_THRESHOLD),
            "is_fixed4_seed": bool(envelope_ids[i] in seed_set),
            "selected": bool(envelope_ids[i] in selected),
        }
        for i in range(len(envelope_rows))
    ]
    return {
        "seed_event_ids": sorted(seed_set),
        "seed_member_count": len(seed_rows),
        "halo_event_ids": halo,
        "halo_member_count": len(halo),
        "fit_status": "FIT",
        "centers": centers,
        "design_rank": rank,
        "fit_rule": fit_rule,
        "beta_intercept_slope": np.asarray(beta, dtype=float).tolist(),
        "seed_residual_location": location.tolist(),
        "oas_covariance": covariance.tolist(),
        "oas_precision": precision.tolist(),
        "oas_shrinkage": float(oas.shrinkage_),
        "chi2_confidence": CONFIDENCE,
        "chi2_df": DIMENSION,
        "chi2_threshold": CHI2_THRESHOLD,
        "event_scores": scores,
    }


def candidate_halo(candidate: dict[str, Any], by_id: dict[str, dict[str, Any]], seed_builder: Any, support: Any, base: Any) -> dict[str, Any]:
    envelope = sorted(str(x) for x in candidate["event_ids"])
    req(len(envelope) == len(set(envelope)) == int(candidate["member_count"]), "parent membership mismatch")
    exact_seed = seed_builder.candidate_core(candidate, by_id, support, base)
    req(exact_seed["family_id"] == str(candidate["family_id"]) and exact_seed["rank"] == int(candidate["internal_mass_rank"]), "seed identity drift")
    annual: dict[str, Any] = {}
    combined_seed: set[str] = set()
    combined_halo: set[str] = set()
    for y in YEARS:
        rows = [by_id[eid] for eid in envelope if int(by_id[eid]["year"]) == y]
        seed_ids = list(exact_seed["annual"][str(y)]["event_ids"])
        h = annual_halo(rows, seed_ids)
        annual[str(y)] = h
        combined_seed.update(h["seed_event_ids"])
        combined_halo.update(h["halo_event_ids"])
    req(combined_seed == set(exact_seed["core_event_ids"]), "combined seed mismatch")
    req(combined_halo.issubset(envelope), "halo escaped parent envelope")
    req(combined_seed.issubset(combined_halo), "seed not retained in halo")
    return {
        "family_id": str(candidate["family_id"]),
        "family_hash": str(candidate["family_hash"]),
        "rank": int(candidate["internal_mass_rank"]),
        "envelope_member_count": len(envelope),
        "seed_event_ids": sorted(combined_seed),
        "seed_member_count": len(combined_seed),
        "halo_event_ids": sorted(combined_halo),
        "halo_member_count": len(combined_halo),
        "annual": annual,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    env = np.asarray([int(r["envelope_member_count"]) for r in rows], dtype=float)
    seed = np.asarray([int(r["seed_member_count"]) for r in rows], dtype=float)
    halo = np.asarray([int(r["halo_member_count"]) for r in rows], dtype=float)
    return {
        "candidate_count": len(rows),
        "nonempty_seed_count": int(np.sum(seed > 0)),
        "nonempty_halo_count": int(np.sum(halo > 0)),
        "halo_strictly_regrows_seed_count": int(np.sum(halo > seed)),
        "mean_envelope_members": float(np.mean(env)) if len(env) else 0.0,
        "mean_seed_members": float(np.mean(seed)) if len(seed) else 0.0,
        "mean_halo_members": float(np.mean(halo)) if len(halo) else 0.0,
        "median_envelope_members": float(np.median(env)) if len(env) else 0.0,
        "median_seed_members": float(np.median(seed)) if len(seed) else 0.0,
        "median_halo_members": float(np.median(halo)) if len(halo) else 0.0,
        "max_envelope_members": int(np.max(env)) if len(env) else 0,
        "max_seed_members": int(np.max(seed)) if len(seed) else 0,
        "max_halo_members": int(np.max(halo)) if len(halo) else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair-pretruth", type=Path, required=True)
    ap.add_argument("--geometry", type=Path, required=True)
    ap.add_argument("--seed-source", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_PRETRUTH_SHA256, "fair pretruth changed")
    req(blob(a.seed_source) == SEED_SOURCE_BLOB, "fixed4 seed source changed")
    req(sha(a.quality_source) == QUALITY_SHA256, "quality runtime changed")
    req(sha(a.v8_result_json) == V8_SHA256, "v8 artifact changed")
    req(abs(CHI2_THRESHOLD - 7.814727903251179) < 1e-12, "chi-square runtime changed")

    fair = json.loads(a.fair_pretruth.read_text())
    req(fair["scientific_role"] == "TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "wrong fair role")
    req(fair["shower_truth_used"] is False and fair["target_information_access"] is False and fair["target_region_events_accessed"] is False, "fair firewall")
    geom = json.loads(a.geometry.read_text())
    req(geom["scientific_role"] == "LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY", "wrong geometry role")
    req(int(geom["events_total"]) == EXPECTED_TOTAL and geom["events_by_year"] == EXPECTED_COUNTS, "geometry counts changed")
    req(geom["blind_exclusion"] == list(BLIND) and geom["shower_truth_exported"] is False, "geometry firewall")
    events = list(geom["events"])
    req(len(events) == EXPECTED_TOTAL and all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected geometry")
    by_id = {str(e["id"]): e for e in events}
    req(len(by_id) == EXPECTED_TOTAL, "duplicate geometry IDs")

    seed_builder = load(a.seed_source, "m2d_fixed4_seed_frozen_v1")
    req(seed_builder.ANCHOR_MULTIPLICITY == 2 and seed_builder.NEAREST_OTHERS == 3, "seed constants changed")
    q = load(a.quality_source, "m2d_fixed4_drift_halo_quality")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-fixed4-drift-halo-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "support firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)

    subsets: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for subset in fair["subsets"]:
        d, b = int(subset["denominator"]), int(subset["bucket"])
        parents = list(subset["successor_candidates"])
        req([int(x["internal_mass_rank"]) for x in parents] == list(range(1, len(parents) + 1)), f"rank drift d{d}b{b}")
        rows: list[dict[str, Any]] = []
        for pos, candidate in enumerate(parents, 1):
            req(all(str(eid) in by_id for eid in candidate["event_ids"]), f"missing geometry d{d}b{b} rank{pos}")
            row = candidate_halo(candidate, by_id, seed_builder, support, base)
            req(row["rank"] == pos, f"rank mismatch d{d}b{b} rank{pos}")
            rows.append(row)
            all_rows.append(row)
        s = summarize(rows)
        subsets.append({
            "denominator": d,
            "bucket": b,
            "event_count": int(subset["event_count"]),
            "annual_event_ids": subset["annual_event_ids"],
            "parent_candidate_count": len(parents),
            "halos": rows,
            "summary": s,
        })
        print(json.dumps({"panel": f"d{d}_b{b}", **s}, sort_keys=True), flush=True)

    payload = {
        "schema": "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_IMMUTABLE_M2D_ENVELOPE_FIXED4_SEED_OAS_95PCT_DRIFT_HALO_FROZEN_BEFORE_TRUTH",
        "fair_pretruth_sha256": FAIR_PRETRUTH_SHA256,
        "geometry_sha256": sha(a.geometry),
        "fixed4_seed_source_blob": SEED_SOURCE_BLOB,
        "quality_source_sha256": QUALITY_SHA256,
        "v8_result_sha256": V8_SHA256,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "solar_longitude_scale_deg": SOL_SCALE_DEG,
        "radiant_scale_deg": RADIANT_SCALE_DEG,
        "speed_log_scale": SPEED_LOG_SCALE,
        "confidence": CONFIDENCE,
        "dimension": DIMENSION,
        "chi2_threshold": CHI2_THRESHOLD,
        "drift_fit_rule": "annual_unweighted_affine_sun_centered_radiant_speed_numpy_lstsq_rcond_none_rank_lt2_zero_slope",
        "covariance_rule": "sklearn_OAS_on_three_dimensional_seed_drift_residuals",
        "selection_rule": "retain_fixed4_seed_union_parent_envelope_events_with_mahalanobis_sq_le_chi2_95pct_df3",
        "subsets": subsets,
        "overall_summary": summarize(all_rows),
        "parent_discovery_membership_changed": False,
        "parent_rank_changed": False,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "external_survey_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH", "sha256": sha(a.output), "overall": payload["overall_summary"]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
