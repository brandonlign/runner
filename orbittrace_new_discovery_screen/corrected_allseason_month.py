#!/usr/bin/env python3
"""Compute-only mirror of the raw corrected all-season discovery protocol.

Scientific source of truth:
  brandonlign/orbittrace-raw
  pipeline/discovery_search/CORRECTED_ALLSEASON_PROTOCOL.md

This runner evaluates one calendar month at a time so all twelve discovery
months can execute independently. Candidate generation keeps the legacy 2025
HDBSCAN settings; adjudication uses canonical Southworth-Hawkins D_SH, the
current MDC with all statuses/incomplete-orbit rows, no hard sporadic-source
mask, complete 2024+2023 validation, and a local pseudo-template recurrence
null for every both-year survivor.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader
from sklearn.cluster import HDBSCAN

SEED = 20260731
DISCOVERY_YEAR = 2025
VALIDATION_YEARS = (2024, 2023)
MDC_URL = "https://ceresiaumdc.ta3.sk/downloads/lists_shw_data/streamfulldata.json"
FEATURE_SCALES = np.asarray([3.5, 3.0, 2.5, 2.5], dtype=float)
MIN_CLUSTER_SIZE = 12
MIN_SAMPLES = 4
MAX_MONTH_ROWS = 150000
MAX_CLUSTER_SIZE = 300
MAX_SCALED_RMS = 1.35
MAX_SOLAR_SIGMA_DEG = 2.5
MIN_MEMBERSHIP_PROB = 0.35
MIN_NIGHTS = 4
MIN_STATIONS = 6
MAX_ONE_NIGHT_FRACTION = 0.50
MAX_ONE_STATION_SET_FRACTION = 0.50
SPLIT_PERMUTATIONS = 199
ORBIT_NULL_DRAWS = 199
VALIDATION_NULL_DRAWS = 499
CLONE_DRAWS = 500
MAX_ORBIT_MEDIAN_D = 0.10
MAX_ORBIT_Q90_D = 0.20
MAX_ORBIT_NULL_P = 0.01
MIN_VALIDATION_MEMBERS = 8
MIN_VALIDATION_NIGHTS = 3
MIN_VALIDATION_STATIONS = 5
MAX_VALIDATION_P = 0.01
MAX_VALIDATION_MEDIAN_D = 0.12
MIN_CLONE_PASS_FRACTION = 0.80

BASE_COLUMNS = [
    "unique_trajectory_identifier",
    "beginning_utc_time",
    "iau_code",
    "sol_lon_deg",
    "lamgeo_deg",
    "betgeo_deg",
    "vgeo_km_s",
    "e",
    "q_au",
    "i_deg",
    "peri_deg",
    "node_deg",
    "sigma_9",
    "sigma_15",
    "sigma_10",
    "sigma_11",
    "sigma_12",
    "medianfiterr_arcsec",
    "num_stat",
    "participating_stations",
]
ORBIT_COLUMNS = ["e", "q_au", "i_deg", "peri_deg", "node_deg"]
SIGMA_COLUMNS = ["sigma_9", "sigma_15", "sigma_10", "sigma_11", "sigma_12"]
SPORADIC_SOURCES = {
    "HELION": (342.0, 0.0),
    "ANTIHELION": (198.0, 0.0),
    "NORTH_APEX": (271.0, 20.0),
    "SOUTH_APEX": (273.0, -20.0),
    "NORTH_TOROIDAL": (270.0, 60.0),
    "SOUTH_TOROIDAL": (270.0, -60.0),
}


def circ_diff(value: Any, center: Any) -> np.ndarray:
    return (np.asarray(value, dtype=float) - np.asarray(center, dtype=float) + 180.0) % 360.0 - 180.0


def circ_center(values: np.ndarray) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def finite(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def station_tokens(value: Any) -> set[str]:
    return {token for token in re.split(r"[^A-Za-z0-9]+", str(value).upper()) if len(token) >= 4}


def spherical_sep(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    cosine = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def d_sh_matrix(left: np.ndarray, right: np.ndarray | None = None) -> np.ndarray:
    """Canonical published Southworth-Hawkins D_SH."""
    a = np.asarray(left, dtype=float)
    b = a if right is None else np.asarray(right, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1 = np.deg2rad(a[:, 2])[:, None]
    i2 = np.deg2rad(b[:, 2])[None, :]
    node_delta = (
        np.deg2rad(a[:, 4])[:, None] - np.deg2rad(b[:, 4])[None, :] + np.pi
    ) % (2.0 * np.pi) - np.pi
    cos_plane = np.clip(
        np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(node_delta),
        -1.0,
        1.0,
    )
    plane = np.arccos(cos_plane)
    denominator = np.maximum(np.cos(plane / 2.0), np.finfo(float).eps)
    common = np.cos((i1 + i2) / 2.0) * np.sin(node_delta / 2.0) / denominator
    peri_delta = (
        np.deg2rad(a[:, 3])[:, None]
        - np.deg2rad(b[:, 3])[None, :]
        + 2.0 * np.arcsin(np.clip(common, -1.0, 1.0))
        + np.pi
    ) % (2.0 * np.pi) - np.pi
    mean_e = (e1 + e2) / 2.0
    d2 = (
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * np.sin(plane / 2.0)) ** 2
        + (mean_e * 2.0 * np.sin(peri_delta / 2.0)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))


def valid_orbits(frame: pd.DataFrame) -> np.ndarray:
    values = frame[ORBIT_COLUMNS].to_numpy(float)
    valid = np.isfinite(values).all(axis=1)
    valid &= (values[:, 0] >= 0.0) & (values[:, 0] < 1.5)
    valid &= (values[:, 1] > 0.0) & (values[:, 1] < 2.0)
    valid &= (values[:, 2] >= 0.0) & (values[:, 2] <= 180.0)
    return valid


def orbit_summary(orbits: np.ndarray) -> dict[str, Any]:
    matrix = d_sh_matrix(orbits)
    idx = int(np.argmin(np.median(matrix, axis=1)))
    distances = matrix[idx]
    return {
        "medoid": np.asarray(orbits[idx], dtype=float),
        "median_d": float(np.median(distances)),
        "q90_d": float(np.quantile(distances, 0.90)),
    }


def flatten_mdc(document: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
    rows: list[dict[str, Any]] = []
    codes: set[str] = set()
    for shower in document.get("data", []):
        code = str(shower.get("Code") or "").strip().upper()
        if code:
            codes.add(code)
        for solution in shower.get("solution", []) or []:
            orbit_values = [finite(solution.get(key)) for key in ("e", "q", "incl", "peri", "node")]
            orbit = None if any(value is None for value in orbit_values) else np.asarray(orbit_values, dtype=float)
            rows.append(
                {
                    "iau_no": str(shower.get("IAUNo") or "").strip(),
                    "code": code,
                    "name": str(shower.get("Name") or shower.get("ProvName") or "").strip(),
                    "solution": str(solution.get("AdNo") or "").strip(),
                    "status": str(solution.get("s") if solution.get("s") is not None else shower.get("s") or "").strip(),
                    "LoSb": finite(solution.get("LoSb")),
                    "LoSe": finite(solution.get("LoSe")),
                    "LoS": finite(solution.get("LoS")),
                    "S_LoR": finite(solution.get("S_LoR")),
                    "LaR": finite(solution.get("LaR")),
                    "Vg": finite(solution.get("Vg")),
                    "orbit": orbit,
                }
            )
    return rows, codes


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float:
    if start is not None and end is not None:
        span = (end - start) % 360.0
        if span <= 120.0:
            offset = (value - start) % 360.0
            if offset <= span:
                return 0.0
            return min(abs(float(circ_diff(value, start))), abs(float(circ_diff(value, end))))
    if center is not None:
        return abs(float(circ_diff(value, center)))
    return 180.0


def known_association(center: np.ndarray, medoid: np.ndarray, catalog: list[dict[str, Any]]) -> dict[str, Any]:
    complete_indices = [index for index, item in enumerate(catalog) if item["orbit"] is not None]
    orbit_dist: dict[int, float] = {}
    if complete_indices:
        matrix = np.asarray([catalog[index]["orbit"] for index in complete_indices], dtype=float)
        values = d_sh_matrix(np.asarray(medoid, dtype=float)[None, :], matrix)[0]
        orbit_dist = {index: float(value) for index, value in zip(complete_indices, values)}
    assessed: list[dict[str, Any]] = []
    for index, item in enumerate(catalog):
        timing = interval_distance(float(center[3]), item["LoSb"], item["LoSe"], item["LoS"])
        if None not in {item["S_LoR"], item["LaR"], item["Vg"]}:
            radiant = spherical_sep(float(center[0]) % 360.0, float(center[1]), float(item["S_LoR"]), float(item["LaR"]))
            speed = abs(float(center[2]) - float(item["Vg"]))
            obs_score = math.sqrt((timing / 12.0) ** 2 + (radiant / 10.0) ** 2 + (speed / 8.0) ** 2)
            observational = timing <= 12.0 and radiant <= 10.0 and speed <= 8.0
        else:
            radiant = None
            speed = None
            obs_score = None
            observational = False
        d = orbit_dist.get(index)
        orbit_close = d is not None and d <= 0.12 and timing <= 20.0
        broad_orbit_close = d is not None and d <= 0.20 and timing <= 30.0
        row = {
            **{k: v for k, v in item.items() if k != "orbit"},
            "d_sh": d,
            "timing_delta_deg": float(timing),
            "radiant_sep_deg": radiant,
            "speed_delta_km_s": speed,
            "obs_score": obs_score,
            "observational_close": bool(observational),
            "orbit_close": bool(orbit_close),
            "broad_orbit_close": bool(broad_orbit_close),
            "plausible": bool(observational or orbit_close or broad_orbit_close),
        }
        assessed.append(row)
    assessed.sort(
        key=lambda row: (
            not row["plausible"],
            float("inf") if row["obs_score"] is None else row["obs_score"],
            float("inf") if row["d_sh"] is None else row["d_sh"],
            row["timing_delta_deg"],
        )
    )
    return {
        "matched": bool(any(row["plausible"] for row in assessed)),
        "best": assessed[0] if assessed else {},
        "best_evidence": assessed[:12],
    }


def source_warning(center: np.ndarray) -> dict[str, Any]:
    rows = [
        {"source": name, "separation_deg": spherical_sep(float(center[0]) % 360.0, float(center[1]), lon, lat)}
        for name, (lon, lat) in SPORADIC_SOURCES.items()
    ]
    rows.sort(key=lambda row: row["separation_deg"])
    return {"within_25_deg": bool(rows[0]["separation_deg"] <= 25.0), "nearest": rows[0], "all": rows}


def load_month(year: int, month: int) -> pd.DataFrame:
    key = f"{year}-{month:02d}"
    print(f"Downloading GMN {key}", flush=True)
    return reader.read_data(dd.get_monthly_file_content_by_date(key), output_camel_case=True).reset_index(drop=False)


def code_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().upper()
    return "" if text in {"", "<NA>", "NAN", "NONE", "SPORADIC", "SPO", "-1", "0"} else text


def prepare(frame: pd.DataFrame, year: int, month: int, current_codes: set[str]) -> dict[str, Any]:
    missing = [column for column in BASE_COLUMNS if column not in frame.columns]
    if missing:
        raise RuntimeError(f"GMN {year}-{month:02d} missing columns: {missing}")
    data = frame[BASE_COLUMNS].copy()
    numeric = [
        "sol_lon_deg",
        "lamgeo_deg",
        "betgeo_deg",
        "vgeo_km_s",
        *ORBIT_COLUMNS,
        *SIGMA_COLUMNS,
        "medianfiterr_arcsec",
        "num_stat",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    valid = np.isfinite(data[["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s"]].to_numpy(float)).all(axis=1)
    valid &= data["sol_lon_deg"].between(0, 360).to_numpy()
    valid &= data["lamgeo_deg"].between(0, 360).to_numpy()
    valid &= data["betgeo_deg"].between(-90, 90).to_numpy()
    valid &= data["vgeo_km_s"].between(5, 75).to_numpy()
    valid &= (data["num_stat"].fillna(0).to_numpy(float) >= 2)
    valid &= (data["medianfiterr_arcsec"].fillna(9999).to_numpy(float) <= 180)
    recognized = np.asarray([code_text(value) in current_codes for value in data["iau_code"].tolist()], dtype=bool)
    data = data.loc[valid & ~recognized].reset_index(drop=True)
    if len(data) > MAX_MONTH_ROWS:
        data = data.sample(MAX_MONTH_ROWS, random_state=SEED + year * 100 + month).sort_index().reset_index(drop=True)
    center_sol = circ_center(data["sol_lon_deg"].to_numpy(float))
    raw = np.column_stack(
        [
            circ_diff(data["lamgeo_deg"].to_numpy(float), data["sol_lon_deg"].to_numpy(float)),
            data["betgeo_deg"].to_numpy(float),
            data["vgeo_km_s"].to_numpy(float),
            circ_diff(data["sol_lon_deg"].to_numpy(float), center_sol),
        ]
    )
    scaled = raw / FEATURE_SCALES[None, :]
    parsed = pd.to_datetime(data["beginning_utc_time"], errors="coerce", utc=True, format="mixed")
    nights = parsed.dt.floor("D").astype("int64").to_numpy()
    return {"data": data, "raw": raw, "scaled": scaled, "center_sol": center_sol, "nights": nights}


def robust_sigma(values: np.ndarray, minimum: np.ndarray) -> np.ndarray:
    center = np.median(values, axis=0)
    sigma = np.median(np.abs(values - center[None, :]), axis=0) * 1.4826
    return np.maximum(sigma, minimum)


def density_test(train: np.ndarray, test: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    center = np.median(train, axis=0)
    sigma = robust_sigma(train, np.asarray([0.20, 0.20, 0.20, 0.20]))
    observed = int(np.sum(np.sum(((test - center) / sigma) ** 2, axis=1) <= 9.0))
    null = []
    for _ in range(SPLIT_PERMUTATIONS):
        perm = test.copy()
        perm[:, 3] = test[rng.permutation(len(test)), 3]
        null.append(int(np.sum(np.sum(((perm - center) / sigma) ** 2, axis=1) <= 9.0)))
    p = (1 + sum(value >= observed for value in null)) / (SPLIT_PERMUTATIONS + 1)
    return {"observed": observed, "p": float(p), "null_q95": float(np.percentile(null, 95))}


def orbit_null(data: pd.DataFrame, member_orbits: np.ndarray, sol: float, width: float, rng: np.random.Generator) -> dict[str, Any]:
    mask = valid_orbits(data) & (np.abs(circ_diff(data["sol_lon_deg"].to_numpy(float), sol)) <= width)
    local = data.loc[mask]
    if len(local) < len(member_orbits) * 3:
        return {"p": 1.0, "pool": int(len(local))}
    values = local[ORBIT_COLUMNS].to_numpy(float)
    observed = orbit_summary(member_orbits)["median_d"]
    null = []
    for _ in range(ORBIT_NULL_DRAWS):
        sample = values[rng.choice(len(values), size=len(member_orbits), replace=False)]
        null.append(orbit_summary(sample)["median_d"])
    p = (1 + sum(value <= observed for value in null)) / (ORBIT_NULL_DRAWS + 1)
    return {"p": float(p), "pool": int(len(local)), "null_q05": float(np.percentile(null, 5))}


def scan_discovery(prepared: dict[str, Any], month: int, catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data, raw, scaled, nights = prepared["data"], prepared["raw"], prepared["scaled"], prepared["nights"]
    print(f"2025-{month:02d}: scanning {len(data):,} quality residuals", flush=True)
    model = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        cluster_selection_method="leaf",
        leaf_size=60,
        n_jobs=-1,
    )
    assignments = model.fit_predict(scaled)
    probabilities = np.asarray(model.probabilities_, dtype=float)
    candidates: list[dict[str, Any]] = []
    for cluster in [int(value) for value in np.unique(assignments) if int(value) >= 0]:
        members = np.flatnonzero(assignments == cluster)
        if not MIN_CLUSTER_SIZE <= len(members) <= MAX_CLUSTER_SIZE:
            continue
        points = scaled[members]
        center_scaled = np.median(points, axis=0)
        rms = float(np.sqrt(np.mean(np.sum((points - center_scaled) ** 2, axis=1))))
        sigma_raw = robust_sigma(raw[members], np.asarray([0.3, 0.3, 0.3, 0.3]))
        solar_sigma = float(sigma_raw[3])
        if rms > MAX_SCALED_RMS or solar_sigma > MAX_SOLAR_SIGMA_DEG:
            continue
        mean_prob = float(np.mean(probabilities[members]))
        if mean_prob < MIN_MEMBERSHIP_PROB:
            continue
        member_nights = nights[members]
        unique_nights, night_counts = np.unique(member_nights, return_counts=True)
        if len(unique_nights) < MIN_NIGHTS or night_counts.max() / len(members) > MAX_ONE_NIGHT_FRACTION:
            continue
        station_sets = data.iloc[members]["participating_stations"].fillna("").astype(str)
        all_stations = set().union(*(station_tokens(value) for value in station_sets))
        if len(all_stations) < MIN_STATIONS or station_sets.value_counts(normalize=True).iloc[0] > MAX_ONE_STATION_SET_FRACTION:
            continue
        member_frame = data.iloc[members].reset_index(drop=True)
        orbit_mask = valid_orbits(member_frame)
        if int(orbit_mask.sum()) < MIN_CLUSTER_SIZE or float(orbit_mask.mean()) < 0.80:
            continue
        member_orbits = member_frame.loc[orbit_mask, ORBIT_COLUMNS].to_numpy(float)
        orbit = orbit_summary(member_orbits)
        if orbit["median_d"] > MAX_ORBIT_MEDIAN_D or orbit["q90_d"] > MAX_ORBIT_Q90_D:
            continue
        ordered_nights = {value: index for index, value in enumerate(sorted(unique_nights.tolist()))}
        split_a_members = np.asarray([ordered_nights[value] % 2 == 0 for value in member_nights])
        split_a_all = np.asarray([ordered_nights.get(value, 0) % 2 == 0 for value in nights])
        if int(split_a_members.sum()) < 5 or int((~split_a_members).sum()) < 5:
            continue
        rng = np.random.default_rng(SEED + month * 10000 + cluster)
        a_to_b = density_test(scaled[members][split_a_members], scaled[~split_a_all], rng)
        b_to_a = density_test(scaled[members][~split_a_members], scaled[split_a_all], rng)
        if min(a_to_b["observed"], b_to_a["observed"]) < 4 or max(a_to_b["p"], b_to_a["p"]) > 0.01:
            continue
        center_raw = center_scaled * FEATURE_SCALES
        absolute_center = np.asarray(
            [
                center_raw[0],
                center_raw[1],
                center_raw[2],
                (prepared["center_sol"] + center_raw[3]) % 360.0,
            ],
            dtype=float,
        )
        null = orbit_null(data, member_orbits, float(absolute_center[3]), max(3 * solar_sigma, 1.5), rng)
        if null["p"] > MAX_ORBIT_NULL_P:
            continue
        association = known_association(absolute_center, orbit["medoid"], catalog)
        if association["matched"]:
            continue
        score = (
            math.log1p(len(members))
            + mean_prob
            - rms
            - solar_sigma / 4.0
            - orbit["median_d"] * 5.0
            - max(a_to_b["p"], b_to_a["p"]) * 10.0
        )
        candidates.append(
            {
                "month": int(month),
                "cluster": int(cluster),
                "members_2025": int(len(members)),
                "center": absolute_center.tolist(),
                "sigma_raw": sigma_raw.tolist(),
                "scaled_rms": rms,
                "solar_sigma_deg": solar_sigma,
                "mean_probability": mean_prob,
                "nights_2025": int(len(unique_nights)),
                "stations_2025": int(len(all_stations)),
                "orbit_medoid": orbit["medoid"].tolist(),
                "orbit_median_d": orbit["median_d"],
                "orbit_q90_d": orbit["q90_d"],
                "orbit_null": null,
                "split_a_to_b": a_to_b,
                "split_b_to_a": b_to_a,
                "nearest_mdc": association,
                "sporadic_source": source_warning(absolute_center),
                "score": float(score),
                "member_ids_2025": member_frame["unique_trajectory_identifier"].astype(str).tolist(),
                "member_rows_2025": member_frame,
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    deduped: list[dict[str, Any]] = []
    for candidate in candidates:
        c = np.asarray(candidate["center"], dtype=float)
        duplicate = False
        for kept in deduped:
            k = np.asarray(kept["center"], dtype=float)
            distance = math.sqrt(
                (float(circ_diff(c[0], k[0])) / 3.5) ** 2
                + ((c[1] - k[1]) / 3.0) ** 2
                + ((c[2] - k[2]) / 2.5) ** 2
                + (float(circ_diff(c[3], k[3])) / 2.5) ** 2
            )
            if distance < 1.0:
                duplicate = True
                break
        if not duplicate:
            deduped.append(candidate)
    print(f"2025-{month:02d}: discovery/catalog survivors={len(deduped)}", flush=True)
    return deduped


def validate(candidate: dict[str, Any], year: int, prepared: dict[str, Any]) -> dict[str, Any]:
    data, raw, nights = prepared["data"], prepared["raw"], prepared["nights"]
    center = np.asarray(candidate["center"], dtype=float)
    sigma = np.maximum(np.asarray(candidate["sigma_raw"], dtype=float), np.asarray([0.5, 0.5, 0.5, 0.5]))
    rad_score = (
        (circ_diff(raw[:, 0], center[0]) / sigma[0]) ** 2
        + ((raw[:, 1] - center[1]) / sigma[1]) ** 2
        + ((raw[:, 2] - center[2]) / sigma[2]) ** 2
    )
    orbit_mask = valid_orbits(data)
    orbit_dist = np.full(len(data), np.inf, dtype=float)
    orbit_dist[orbit_mask] = d_sh_matrix(
        data.loc[orbit_mask, ORBIT_COLUMNS].to_numpy(float),
        np.asarray(candidate["orbit_medoid"], dtype=float)[None, :],
    )[:, 0]
    local = (rad_score <= 9.0) & (orbit_dist <= 0.20)
    width = max(3.0 * sigma[3], 1.0)
    temporal = np.abs(circ_diff(data["sol_lon_deg"].to_numpy(float), center[3])) <= width
    selected = local & temporal & (orbit_dist <= 0.15)
    observed = int(selected.sum())
    unique_nights = int(len(np.unique(nights[selected]))) if observed else 0
    stations = (
        set().union(*(station_tokens(value) for value in data.loc[selected, "participating_stations"].fillna("")))
        if observed
        else set()
    )
    median_d = float(np.median(orbit_dist[selected])) if observed else None
    all_sol = data["sol_lon_deg"].to_numpy(float)
    local_count = int(local.sum())
    rng = np.random.default_rng(SEED + year * 10000 + int(candidate["month"]) * 100 + int(candidate["cluster"]))
    null = []
    for _ in range(VALIDATION_NULL_DRAWS):
        sampled_sol = all_sol[rng.choice(len(all_sol), size=local_count, replace=False)] if local_count <= len(all_sol) else all_sol
        null.append(int(np.sum(np.abs(circ_diff(sampled_sol, center[3])) <= width)))
    p = (1 + sum(value >= observed for value in null)) / (VALIDATION_NULL_DRAWS + 1)
    passed = (
        observed >= MIN_VALIDATION_MEMBERS
        and unique_nights >= MIN_VALIDATION_NIGHTS
        and len(stations) >= MIN_VALIDATION_STATIONS
        and p <= MAX_VALIDATION_P
        and median_d is not None
        and median_d <= MAX_VALIDATION_MEDIAN_D
    )
    return {
        "year": int(year),
        "members": observed,
        "local_pool": local_count,
        "nights": unique_nights,
        "stations": int(len(stations)),
        "p": float(p),
        "null_q99": float(np.percentile(null, 99)),
        "median_d": median_d,
        "passed": bool(passed),
        "member_ids": data.loc[selected, "unique_trajectory_identifier"].astype(str).tolist(),
    }


def clone_stability(candidate: dict[str, Any]) -> dict[str, Any]:
    frame = candidate["member_rows_2025"]
    mask = valid_orbits(frame)
    values = frame.loc[mask, ORBIT_COLUMNS].to_numpy(float)
    sigmas = frame.loc[mask, SIGMA_COLUMNS].to_numpy(float)
    sigmas = np.nan_to_num(np.abs(sigmas), nan=0.0, posinf=0.0, neginf=0.0)
    sigmas = np.minimum(sigmas, np.asarray([0.10, 0.10, 10.0, 20.0, 5.0])[None, :])
    rng = np.random.default_rng(SEED + int(candidate["month"]) * 100 + int(candidate["cluster"]))
    passed = 0
    medians = []
    for _ in range(CLONE_DRAWS):
        clone = values + rng.normal(size=values.shape) * sigmas
        clone[:, 0] = np.clip(clone[:, 0], 0, 1.49)
        clone[:, 1] = np.clip(clone[:, 1], 0.01, 1.99)
        clone[:, 2] = np.clip(clone[:, 2], 0, 180)
        clone[:, 3:] %= 360.0
        summary = orbit_summary(clone)
        medians.append(summary["median_d"])
        if summary["median_d"] <= MAX_ORBIT_MEDIAN_D and summary["q90_d"] <= MAX_ORBIT_Q90_D:
            passed += 1
    fraction = passed / CLONE_DRAWS
    return {
        "draws": int(CLONE_DRAWS),
        "pass_fraction": float(fraction),
        "median_of_clone_medians": float(np.median(medians)),
        "passed": bool(fraction >= MIN_CLONE_PASS_FRACTION),
    }


def template_count(center: np.ndarray, orbit: np.ndarray, sigma: np.ndarray, prepared: dict[str, Any]) -> int:
    data, raw = prepared["data"], prepared["raw"]
    widths = np.maximum(np.asarray(sigma, dtype=float), np.asarray([0.5, 0.5, 0.5, 0.5]))
    rad_score = (
        (circ_diff(raw[:, 0], center[0]) / widths[0]) ** 2
        + ((raw[:, 1] - center[1]) / widths[1]) ** 2
        + ((raw[:, 2] - center[2]) / widths[2]) ** 2
    )
    temporal = np.abs(circ_diff(data["sol_lon_deg"].to_numpy(float), center[3])) <= max(3.0 * widths[3], 1.0)
    pre = np.flatnonzero((rad_score <= 9.0) & temporal & valid_orbits(data))
    if len(pre) == 0:
        return 0
    distance = d_sh_matrix(
        data.iloc[pre][ORBIT_COLUMNS].to_numpy(float),
        np.asarray(orbit, dtype=float)[None, :],
    )[:, 0]
    return int(np.sum(distance <= 0.15))


def local_pseudo_null(candidate: dict[str, Any], discovery: dict[str, Any], validation: dict[int, dict[str, Any]]) -> dict[str, Any]:
    data, raw = discovery["data"], discovery["raw"]
    center = np.asarray(candidate["center"], dtype=float)
    candidate_ids = set(map(str, candidate["member_ids_2025"]))
    radiant = np.asarray(
        [spherical_sep(float(lon) % 360.0, float(beta), float(center[0]) % 360.0, float(center[1])) for lon, beta in zip(raw[:, 0], raw[:, 1])],
        dtype=float,
    )
    mask = (
        valid_orbits(data)
        & (np.abs(circ_diff(data["sol_lon_deg"].to_numpy(float), center[3])) <= 20.0)
        & (radiant <= 25.0)
        & (np.abs(data["vgeo_km_s"].to_numpy(float) - center[2]) <= 10.0)
        & (~data["unique_trajectory_identifier"].astype(str).isin(candidate_ids).to_numpy())
    )
    seeds = data.loc[mask].reset_index(drop=True)
    seed_sol = seeds["sol_lon_deg"].to_numpy(float)
    seed_slon = circ_diff(seeds["lamgeo_deg"].to_numpy(float), seed_sol)
    centers = np.column_stack([seed_slon, seeds["betgeo_deg"].to_numpy(float), seeds["vgeo_km_s"].to_numpy(float), seed_sol])
    orbits = seeds[ORBIT_COLUMNS].to_numpy(float)
    seed_ids = seeds["unique_trajectory_identifier"].astype(str).tolist()
    sigma = np.asarray(candidate["sigma_raw"], dtype=float)
    n2024 = np.zeros(len(seeds), dtype=np.int64)
    n2023 = np.zeros(len(seeds), dtype=np.int64)
    for index, (seed_center, orbit) in enumerate(zip(centers, orbits)):
        n2024[index] = template_count(seed_center, orbit, sigma, validation[2024])
        n2023[index] = template_count(seed_center, orbit, sigma, validation[2023])
    recurrence = np.minimum(n2024, n2023)
    totals = n2024 + n2023
    candidate_r = min(int(candidate["validation"]["2024"]["members"]), int(candidate["validation"]["2023"]["members"]))
    candidate_t = int(candidate["validation"]["2024"]["members"]) + int(candidate["validation"]["2023"]["members"])
    q99_r = int(np.quantile(recurrence, 0.99, method="higher")) if len(recurrence) else 0
    tied = totals[recurrence == q99_r]
    q99_t = int(np.quantile(tied, 0.99, method="higher")) if len(tied) else 0
    passed = candidate_r > q99_r or (candidate_r == q99_r and candidate_t > q99_t)
    order = sorted(range(len(seeds)), key=lambda idx: (-int(recurrence[idx]), -int(totals[idx]), seed_ids[idx]))[:20]
    return {
        "pseudo_template_count": int(len(seeds)),
        "candidate_R": int(candidate_r),
        "candidate_T": int(candidate_t),
        "null_R_q99_higher": int(q99_r),
        "null_T_q99_higher_given_R_q99": int(q99_t),
        "null_R_max": int(recurrence.max()) if len(recurrence) else 0,
        "null_T_max": int(totals.max()) if len(totals) else 0,
        "pass": bool(passed),
        "top_pseudo_templates": [
            {
                "seed_event_id": seed_ids[idx],
                "n2024": int(n2024[idx]),
                "n2023": int(n2023[idx]),
                "R": int(recurrence[idx]),
                "T": int(totals[idx]),
            }
            for idx in order
        ],
    }


def serializable(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if key != "member_rows_2025"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    month = int(args.month)
    if not 1 <= month <= 12:
        raise SystemExit("month must be 1..12")
    args.out.mkdir(parents=True, exist_ok=True)

    response = requests.get(MDC_URL, timeout=90)
    response.raise_for_status()
    mdc = response.json()
    catalog, current_codes = flatten_mdc(mdc)
    if len(catalog) < 1800:
        raise RuntimeError(f"unexpectedly small MDC solution set: {len(catalog)}")
    print(f"MDC {mdc.get('version')}: {len(catalog)} solution rows, {len(current_codes)} codes", flush=True)

    discovery = prepare(load_month(DISCOVERY_YEAR, month), DISCOVERY_YEAR, month, current_codes)
    candidates = scan_discovery(discovery, month, catalog)
    validation_cache = {
        year: prepare(load_month(year, month), year, month, current_codes) for year in VALIDATION_YEARS
    } if candidates else {}

    final: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, 1):
        print(f"Validating {index}/{len(candidates)} cluster={candidate['cluster']} N={candidate['members_2025']}", flush=True)
        candidate["validation"] = {
            str(year): validate(candidate, year, validation_cache[year]) for year in VALIDATION_YEARS
        }
        both = all(item["passed"] for item in candidate["validation"].values())
        candidate["clone_stability"] = clone_stability(candidate) if both else {"passed": False, "not_run": True}
        pre_local = bool(both and candidate["clone_stability"]["passed"])
        candidate["pre_local_null_survivor"] = pre_local
        if pre_local:
            candidate["local_pseudo_template_null"] = local_pseudo_null(candidate, discovery, validation_cache)
        else:
            candidate["local_pseudo_template_null"] = {"not_run": True, "pass": False}
        candidate["corrected_allseason_lead"] = bool(pre_local and candidate["local_pseudo_template_null"]["pass"])
        if candidate["corrected_allseason_lead"]:
            final.append(candidate)
        print(
            f"  2024={candidate['validation']['2024']['passed']} "
            f"2023={candidate['validation']['2023']['passed']} "
            f"clone={candidate['clone_stability'].get('passed')} "
            f"local={candidate['local_pseudo_template_null'].get('pass')} "
            f"final={candidate['corrected_allseason_lead']}",
            flush=True,
        )

    result = {
        "stage": "corrected_allseason_residual_discovery_month_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/CORRECTED_ALLSEASON_PROTOCOL.md",
        "month": month,
        "discovery_year": DISCOVERY_YEAR,
        "validation_years": list(VALIDATION_YEARS),
        "mdc_version": mdc.get("version"),
        "mdc_shower_count": mdc.get("count"),
        "mdc_solution_rows_including_incomplete_orbits": len(catalog),
        "quality_residuals_2025": int(len(discovery["data"])),
        "discovery_catalog_survivors": int(len(candidates)),
        "pre_local_null_survivors": int(sum(c["pre_local_null_survivor"] for c in candidates)),
        "final_leads": int(len(final)),
        "verdict": "DISCOVERY_LEAD" if final else "NO_DISCOVERY_LEAD",
        "candidates": [serializable(candidate) for candidate in candidates],
    }
    json_path = args.out / f"corrected_allseason_month_{month:02d}.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        f"# Corrected all-season month {month:02d}",
        "",
        f"MDC **{mdc.get('version')}**. 2025 residual rows: **{len(discovery['data'])}**.",
        f"Discovery/catalog survivors: **{len(candidates)}**. Final leads: **{len(final)}**.",
        "",
        "| cluster | N2025 | solar | SLoR | beta | Vg | Dmed | source | nearest MDC | N24/p24 | N23/p23 | local | final |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for candidate in candidates:
        center = candidate["center"]
        best = candidate["nearest_mdc"].get("best", {})
        source = candidate["sporadic_source"]["nearest"]
        v24 = candidate["validation"]["2024"]
        v23 = candidate["validation"]["2023"]
        lines.append(
            f"| {candidate['cluster']} | {candidate['members_2025']} | {center[3]:.2f} | {center[0]:.2f} | "
            f"{center[1]:.2f} | {center[2]:.2f} | {candidate['orbit_median_d']:.3f} | "
            f"{source['source']} ({source['separation_deg']:.1f}) | {best.get('iau_no','')}/{best.get('code','')} | "
            f"{v24['members']}/{v24['p']:.3f} | {v23['members']}/{v23['p']:.3f} | "
            f"{candidate['local_pseudo_template_null'].get('pass', False)} | {candidate['corrected_allseason_lead']} |"
        )
    md_path = args.out / f"CORRECTED_ALLSEASON_MONTH_{month:02d}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
