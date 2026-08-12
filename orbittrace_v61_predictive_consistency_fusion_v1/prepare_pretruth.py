#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v15_canonical_application_v1 import application as v15_application

YEARS = (2013, 2014)
BLIND = (20.0, 55.0)
EXPECTED = {
    "sugar": {
        "count": 267,
        "membership_sha": "be5f559f27c1a18dcda28c20b6197278473cdb458ddfd29ec61bc468e33c352a",
        "manifest_sha": "5946c946e22b0d9807802cee6c69d202c515a291716545d97bfca5533f9c5aad",
    },
    "hdbscan": {
        "count": 229,
        "membership_sha": "99640747e935df2f4a7c7983bdde843ea59e1814388b8418e040dc04628aee13",
        "manifest_sha": "dbb9acc3adbfb15b42f633e36e400bf7e0082765077cbf0f51a0ddcb81af1ea0",
    },
}


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--route", choices=sorted(EXPECTED), required=True)
    p.add_argument("--rows-2013", type=Path, required=True)
    p.add_argument("--rows-2014", type=Path, required=True)
    p.add_argument("--membership-json", type=Path, required=True)
    p.add_argument("--manifest-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def signed_circular_delta(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def circular_mean_deg(values: list[float]) -> float:
    req(bool(values), "circular mean of empty values")
    r = np.radians(np.asarray(values, dtype=float))
    s = float(np.mean(np.sin(r)))
    c = float(np.mean(np.cos(r)))
    req(math.isfinite(s) and math.isfinite(c) and math.hypot(s, c) > 1e-12, "degenerate circular mean")
    return float(math.degrees(math.atan2(s, c)) % 360.0)


def unit(lon_deg: float, lat_deg: float) -> np.ndarray:
    lon = math.radians(float(lon_deg))
    lat = math.radians(float(lat_deg))
    return np.asarray([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    ], dtype=float)


def angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))


def normalize_event(row: dict[str, Any]) -> dict[str, float]:
    sol = float(row["sol"]) % 360.0
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected-region event reached v61 predictor: {row['id']}")
    lon = float(row["sun_lon"])
    lat = float(row["ecl_lat"])
    vg = float(row["vg"])
    req(all(math.isfinite(x) for x in (sol, lon, lat, vg)) and vg > 0.0, f"invalid event observables: {row['id']}")
    return {"sol": sol, "lon": lon, "lat": lat, "vg": vg}


def physical_residual(actual: dict[str, float], pred_u: np.ndarray, pred_logv: float) -> float:
    ua = unit(actual["lon"], actual["lat"])
    radiant = angle_deg(ua, pred_u) / 3.0
    speed = abs(math.log(actual["vg"]) - float(pred_logv)) / math.log(1.08)
    return float(math.hypot(radiant, speed))


def loo_year(rows: list[dict[str, float]]) -> dict[str, Any]:
    n = len(rows)
    req(n >= 1, "recurrent family missing annual members")
    center_sol = circular_mean_deg([r["sol"] for r in rows])

    static_u = np.mean(np.asarray([unit(r["lon"], r["lat"]) for r in rows], dtype=float), axis=0)
    norm = float(np.linalg.norm(static_u))
    req(math.isfinite(norm) and norm > 1e-12, "degenerate static radiant")
    static_u /= norm
    static_logv = float(np.mean([math.log(r["vg"]) for r in rows]))
    static_residuals = [physical_residual(r, static_u, static_logv) for r in rows]

    if n < 4:
        pred = list(static_residuals)
        learned = 0.0
    else:
        pred = []
        for held in range(n):
            train = [i for i in range(n) if i != held]
            x = np.asarray([signed_circular_delta(rows[i]["sol"], center_sol) / 10.0 for i in train], dtype=float)
            design = np.column_stack([np.ones(len(train), dtype=float), x])
            target = np.column_stack([
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[0] for i in train], dtype=float),
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[1] for i in train], dtype=float),
                np.asarray([unit(rows[i]["lon"], rows[i]["lat"])[2] for i in train], dtype=float),
                np.asarray([math.log(rows[i]["vg"]) for i in train], dtype=float),
            ])
            coef, *_ = np.linalg.lstsq(design, target, rcond=None)
            xh = signed_circular_delta(rows[held]["sol"], center_sol) / 10.0
            yh = np.asarray([1.0, xh], dtype=float) @ coef
            pu = np.asarray(yh[:3], dtype=float)
            pnorm = float(np.linalg.norm(pu))
            req(math.isfinite(pnorm) and pnorm > 1e-12, "degenerate predictive radiant")
            pu /= pnorm
            req(math.isfinite(float(yh[3])), "nonfinite predictive log speed")
            pred.append(physical_residual(rows[held], pu, float(yh[3])))
        learned = 1.0

    def q90(values: list[float]) -> float:
        return float(np.quantile(values, 0.90))

    return {
        "n": n,
        "center_sol": center_sol,
        "learned": learned,
        "pred_median": float(np.median(pred)),
        "pred_q90": q90(pred),
        "pred_max": float(max(pred)),
        "static_median": float(np.median(static_residuals)),
        "static_q90": q90(static_residuals),
    }


def predictive_features(family: dict[str, Any], lookup: dict[int, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    annual: list[dict[str, Any]] = []
    member_ids = list(map(str, family["event_ids"]))
    seen: set[str] = set()
    for year in YEARS:
        ids = [eid for eid in member_ids if eid in lookup[year]]
        seen.update(ids)
        rows = [normalize_event(lookup[year][eid]) for eid in ids]
        annual.append(loo_year(rows))
    req(seen == set(member_ids), f"family member absent from canonical route rows: {family['family_id']}")
    pred_q90_max = float(max(a["pred_q90"] for a in annual))
    pred_median_max = float(max(a["pred_median"] for a in annual))
    pred_max_max = float(max(a["pred_max"] for a in annual))
    static_q90_max = float(max(a["static_q90"] for a in annual))
    gain = float(static_q90_max - pred_q90_max)
    learned_fraction = float(sum(a["learned"] * a["n"] for a in annual) / sum(a["n"] for a in annual))
    return {
        "pred_q90_max": pred_q90_max,
        "pred_median_max": pred_median_max,
        "pred_max_max": pred_max_max,
        "static_q90_max": static_q90_max,
        "q90_gain": gain,
        "learned_fraction": learned_fraction,
        "annual": {str(y): a for y, a in zip(YEARS, annual)},
    }


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    exp = EXPECTED[a.route]
    req(sha(a.membership_json) == exp["membership_sha"], f"{a.route} immutable membership payload changed")
    req(sha(a.manifest_json) == exp["manifest_sha"], f"{a.route} immutable manifest changed")

    raw = {2013: json.loads(a.rows_2013.read_text()), 2014: json.loads(a.rows_2014.read_text())}
    forbidden = {"label", "shower", "truth", "known_shower", "native_background", "sporadic"}
    for year in YEARS:
        req(raw[year] and all(int(x["year"]) == year for x in raw[year]), f"invalid {year} label-free rows")
        req(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]), "truth-bearing field reached v61 pretruth stage")
    canonical = v15_application.validate_pair(YEARS, raw)
    lookup = {year: {str(row["id"]): row for row in canonical[year]} for year in YEARS}

    manifest = json.loads(a.manifest_json.read_text())
    payload = json.loads(a.membership_json.read_text())
    req(manifest["truth_accessed"] is False and payload["truth_accessed"] is False, "truth-bearing immutable payload")
    families = payload["families"]
    ids = list(map(str, manifest["family_ids"]))
    req(len(families) == len(ids) == int(exp["count"]), f"{a.route} family count changed")
    req([str(f["family_id"]) for f in families] == ids and len(set(ids)) == len(ids), f"{a.route} family alignment changed")

    rows: list[dict[str, Any]] = []
    for family in families:
        rows.append({"family_id": str(family["family_id"]), "features": predictive_features(family, lookup)})
    predictive_order = [
        str(r["family_id"])
        for r in sorted(rows, key=lambda r: (
            float(r["features"]["pred_q90_max"]),
            float(r["features"]["pred_median_max"]),
            -float(r["features"]["q90_gain"]),
            str(r["family_id"]),
        ))
    ]
    req(len(predictive_order) == len(set(predictive_order)) == len(ids) and set(predictive_order) == set(ids), "invalid predictive order")

    out = {
        "scientific_stage": "EXPOSED_SONOTACO_V61_PREDICTIVE_PRETRUTH",
        "route": a.route,
        "years": list(YEARS),
        "candidate_count": len(ids),
        "feature_rule": "exact GMN diagnostic LOO affine radiant-unit-vector + log(vg) predictor; physical residual; worst-year q90/median; q90 gain",
        "predictive_order": predictive_order,
        "predictive_order_sha256": order_sha(predictive_order),
        "families": rows,
        "truth_accessed": False,
        "parameter_search": False,
        "membership_changed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    path = a.output / f"V61_{a.route.upper()}_PREDICTIVE_PRETRUTH.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "route": a.route,
        "candidate_count": len(ids),
        "predictive_order_sha256": out["predictive_order_sha256"],
        "pretruth_sha256": sha(path),
        "truth_accessed": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
