#!/usr/bin/env python3
"""Target-excluded GMN diagnostic for candidate-internal predictive consistency.

This diagnostic asks whether a fixed, label-free leave-one-out physical prediction score can
improve the frozen hard-family GMN order without using source identity, SonotaCo, or protected
OrbitTrace information. It is diagnostic-only: a PASS may motivate a separately frozen
transferable successor, while a FAIL closes this exact mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

import run_urc_union_ranker as q

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
CORPUS = "orbittrace-gmn-predictive-consistency-diagnostic-v1"
EXPECTED_HARD = 226
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "quality_source",
        "support_source_parts",
        "candidate_payload",
        "baseline_payload",
        "scorer_parts",
        "v8_result_json",
        "p19_prelabel_json",
        "output",
    ):
        p.add_argument("--" + name.replace("_", "-"), dest=name, type=Path, required=True)
    return p.parse_args()


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_field(row: dict[str, Any], names: Iterable[str]) -> float:
    for name in names:
        if name in row and row[name] is not None:
            value = float(row[name])
            if math.isfinite(value):
                return value
    raise RuntimeError(f"event missing required aliases {tuple(names)}; keys={sorted(row)[:40]}")


def normalize_event(row: dict[str, Any]) -> dict[str, float]:
    sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
    req(not (BLIND[0] <= sol <= BLIND[1]), "protected-region event reached predictive diagnostic")
    lon = event_field(row, ("sun_lon", "sun_centered_longitude", "sun_centered_lon", "lam_sce"))
    lat = event_field(row, ("ecl_lat", "ecliptic_latitude", "lat_sce", "beta"))
    vg = event_field(row, ("vg", "v_g", "geocentric_speed", "velocity"))
    req(vg > 0.0, "nonpositive geocentric speed")
    return {"sol": sol, "lon": lon, "lat": lat, "vg": vg}


def signed_circular_delta(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def unit(lon_deg: float, lat_deg: float) -> np.ndarray:
    lon = math.radians(lon_deg)
    lat = math.radians(lat_deg)
    return np.asarray([math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)], float)


def angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))


def physical_residual(actual: dict[str, float], pred_u: np.ndarray, pred_logv: float) -> float:
    ua = unit(actual["lon"], actual["lat"])
    radiant = angle_deg(ua, pred_u) / 3.0
    speed = abs(math.log(actual["vg"]) - float(pred_logv)) / math.log(1.08)
    return float(math.hypot(radiant, speed))


def loo_year(rows: list[dict[str, float]], center_sol: float) -> dict[str, Any]:
    n = len(rows)
    static_u = np.mean(np.asarray([unit(r["lon"], r["lat"]) for r in rows], float), axis=0) if rows else np.asarray([1.0, 0.0, 0.0])
    norm = float(np.linalg.norm(static_u))
    if norm > 0.0:
        static_u = static_u / norm
    static_logv = float(np.mean([math.log(r["vg"]) for r in rows])) if rows else 0.0
    static_residuals = [physical_residual(r, static_u, static_logv) for r in rows]

    # Exact fallback for sparse annual membership: no learned drift; the static residual becomes
    # the predictive residual and the learned fraction is zero. No family is removed.
    if n < 4:
        pred = list(static_residuals)
        learned = 0.0
    else:
        pred = []
        for held in range(n):
            train = [i for i in range(n) if i != held]
            x = np.asarray([signed_circular_delta(rows[i]["sol"], center_sol) / 10.0 for i in train], float)
            design = np.column_stack([np.ones(len(train), float), x])
            target = np.column_stack([
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[0] for i in train], float),
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[1] for i in train], float),
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[2] for i in train], float),
                np.asarray([math.log(rows[i]["vg"]) for i in train], float),
            ])
            coef, *_ = np.linalg.lstsq(design, target, rcond=None)
            xh = signed_circular_delta(rows[held]["sol"], center_sol) / 10.0
            yh = np.asarray([1.0, xh], float) @ coef
            pu = np.asarray(yh[:3], float)
            pnorm = float(np.linalg.norm(pu))
            req(math.isfinite(pnorm) and pnorm > 1e-12, "degenerate predictive radiant")
            pu /= pnorm
            req(math.isfinite(float(yh[3])), "nonfinite predictive log speed")
            pred.append(physical_residual(rows[held], pu, float(yh[3])))
        learned = 1.0

    def q90(values: list[float]) -> float:
        return float(np.quantile(values, 0.90)) if values else 10.0

    return {
        "n": n,
        "learned": learned,
        "pred_median": float(np.median(pred)) if pred else 10.0,
        "pred_q90": q90(pred),
        "pred_max": float(max(pred)) if pred else 10.0,
        "static_median": float(np.median(static_residuals)) if static_residuals else 10.0,
        "static_q90": q90(static_residuals),
    }


def predictive_features(family: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    annual = []
    centroids = family.get("centroids", {})
    for year in YEARS:
        c = centroids.get(str(year))
        req(c is not None, f"missing annual centroid for {family['family_id']} {year}")
        ids = [str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year]
        rows = []
        for eid in ids:
            req(eid in lookup, f"candidate member missing from target-excluded scan: {eid}")
            rows.append(normalize_event(lookup[eid]))
        annual.append(loo_year(rows, float(c["sol"])))
    pred_q90_max = float(max(a["pred_q90"] for a in annual))
    pred_median_max = float(max(a["pred_median"] for a in annual))
    pred_max_max = float(max(a["pred_max"] for a in annual))
    static_q90_max = float(max(a["static_q90"] for a in annual))
    gain = float(static_q90_max - pred_q90_max)
    learned_fraction = float(sum(a["learned"] * a["n"] for a in annual) / max(sum(a["n"] for a in annual), 1))
    return {
        "pred_q90_max": pred_q90_max,
        "pred_median_max": pred_median_max,
        "pred_max_max": pred_max_max,
        "static_q90_max": static_q90_max,
        "q90_gain": gain,
        "learned_fraction": learned_fraction,
        "annual": annual,
    }


def rank_predictive(rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(row["family_id"])
        for row in sorted(
            rows,
            key=lambda r: (
                float(r["features"]["pred_q90_max"]),
                float(r["features"]["pred_median_max"]),
                -float(r["features"]["q90_gain"]),
                str(r["family_id"]),
            ),
        )
    ]


def equal_rank_fusion(hard_order: list[str], predictive_order: list[str]) -> list[str]:
    req(set(hard_order) == set(predictive_order) and len(hard_order) == len(predictive_order), "order universe mismatch")
    h = {fid: i + 1 for i, fid in enumerate(hard_order)}
    p = {fid: i + 1 for i, fid in enumerate(predictive_order)}
    return sorted(hard_order, key=lambda fid: (h[fid] + p[fid], h[fid], fid))


def metric_subset(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == QUALITY_SHA, "active GMN ranker source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "v8 target-excluded result changed")
    req(sha(a.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 prelabel universe changed")

    payload = json.loads(a.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    req(len(hard) == EXPECTED_HARD and len(hard_order) == EXPECTED_HARD, "hard family count changed")
    ids = [str(f["family_id"]) for f in hard]
    req(len(set(ids)) == EXPECTED_HARD and set(ids) == set(hard_order), "hard family identity changed")

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    req(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_labels, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), "GMN years changed")
    req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month panel changed")

    # Build the complete candidate-internal feature vector before any truth-derived operation.
    lookup = q.v2.event_lookup(scan)
    feature_rows = []
    for i, family in enumerate(hard, start=1):
        feature_rows.append({
            "family_id": str(family["family_id"]),
            "hard_rank": i,
            "features": predictive_features(family, lookup),
        })
    prelabel = {
        "scope": "GMN 2022/2023 target-excluded hard-family predictive consistency",
        "blind_exclusion": list(BLIND),
        "feature_definition": "annual leave-one-out affine drift in radiant unit-vector plus log(vg); exact physical residual; lexicographic predictive order",
        "families": feature_rows,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GMN_PREDICTIVE_CONSISTENCY_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    predictive_order = rank_predictive(feature_rows)
    fused_order = equal_rank_fusion(hard_order, predictive_order)

    # Development truth is used only now, after the exact feature vector and both orders exist.
    eligible = q.v1.eligible_labels(hidden_labels)
    by = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by[fid], hidden_labels, eligible) for fid in ids}
    base_metrics = q.v1.monotone_metrics(hard, hard_order, truths, eligible)
    pred_metrics = q.v1.monotone_metrics(hard, predictive_order, truths, eligible)
    fused_metrics = q.v1.monotone_metrics(hard, fused_order, truths, eligible)

    passed = (
        int(fused_metrics["recovered_at_100"]) > int(base_metrics["recovered_at_100"])
        and int(fused_metrics["recovered_at_50"]) >= int(base_metrics["recovered_at_50"])
        and float(fused_metrics["top100_dominant_precision"]) >= float(base_metrics["top100_dominant_precision"])
        and float(fused_metrics["mrr"]) >= float(base_metrics["mrr"])
    )
    verdict = "PASS_GMN_PREDICTIVE_CONSISTENCY_SIGNAL" if passed else "FAIL_GMN_PREDICTIVE_CONSISTENCY_SIGNAL"
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_MECHANISM_DIAGNOSTIC_ONLY",
        "candidate_count": EXPECTED_HARD,
        "blind_exclusion": list(BLIND),
        "prelabel_sha256": prelabel_sha,
        "hard_order_sha256": hashlib.sha256("\n".join(hard_order).encode()).hexdigest(),
        "predictive_order_sha256": hashlib.sha256("\n".join(predictive_order).encode()).hexdigest(),
        "fused_order_sha256": hashlib.sha256("\n".join(fused_order).encode()).hexdigest(),
        "baseline": metric_subset(base_metrics),
        "predictive_only": metric_subset(pred_metrics),
        "equal_rank_fusion": metric_subset(fused_metrics),
        "pass_gates": {
            "recovered_at_100_strictly_better": int(fused_metrics["recovered_at_100"]) > int(base_metrics["recovered_at_100"]),
            "recovered_at_50_not_worse": int(fused_metrics["recovered_at_50"]) >= int(base_metrics["recovered_at_50"]),
            "top100_precision_not_worse": float(fused_metrics["top100_dominant_precision"]) >= float(base_metrics["top100_dominant_precision"]),
            "mrr_not_worse": float(fused_metrics["mrr"]) >= float(base_metrics["mrr"]),
        },
        "parameter_search": False,
        "family_deletion": False,
        "membership_changed": False,
        "candidate_generation_recomputed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "claim_boundary": "Diagnostic only. PASS can motivate one separately frozen successor; FAIL permanently closes this exact predictive-order plus equal-rank-fusion mechanism.",
    }
    out = a.output / "GMN_PREDICTIVE_CONSISTENCY_DIAGNOSTIC_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "GMN_PREDICTIVE_CONSISTENCY_DIAGNOSTIC_V1.md").write_text(
        "# GMN predictive consistency diagnostic v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- baseline @100/@50: `{base_metrics['recovered_at_100']}` / `{base_metrics['recovered_at_50']}`\n"
        f"- fused @100/@50: `{fused_metrics['recovered_at_100']}` / `{fused_metrics['recovered_at_50']}`\n"
        f"- baseline/fused top100 precision: `{base_metrics['top100_dominant_precision']:.6f}` / `{fused_metrics['top100_dominant_precision']:.6f}`\n"
        f"- baseline/fused MRR: `{base_metrics['mrr']:.8f}` / `{fused_metrics['mrr']:.8f}`\n"
        f"- prelabel SHA-256: `{prelabel_sha}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "baseline100": base_metrics["recovered_at_100"],
        "fused100": fused_metrics["recovered_at_100"],
        "baseline50": base_metrics["recovered_at_50"],
        "fused50": fused_metrics["recovered_at_50"],
        "baseline_precision": base_metrics["top100_dominant_precision"],
        "fused_precision": fused_metrics["top100_dominant_precision"],
        "baseline_mrr": base_metrics["mrr"],
        "fused_mrr": fused_metrics["mrr"],
        "prelabel_sha256": prelabel_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
