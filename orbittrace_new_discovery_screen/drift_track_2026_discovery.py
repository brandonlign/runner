#!/usr/bin/env python3
"""Generic compute mirror for the frozen 2026 residual drift-track protocol.

The scientific protocol was committed in orbittrace-raw before the positive-
control benchmark completed.  This executable takes exactly one variant name;
the workflow may be created only after the benchmark's frozen selection rule
chooses that variant and passes its >=3/4 control sufficiency requirement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as drift

DISCOVERY_YEAR = 2026
VALIDATION_YEARS = (2025, 2024)
MAX_DISCOVERY_SPAN = 25.0
MAX_SLOPE_SLON = 2.0
MAX_SLOPE_BETA = 2.0
MAX_SLOPE_VG = 1.0
MIN_DISCOVERY_NIGHTS = 4
MIN_DISCOVERY_STATIONS = 6
MAX_DOMINANT_FRACTION = 0.50
MAX_DISCOVERY_D50 = 0.10
MAX_DISCOVERY_D90 = 0.20
VALIDATION_RADIUS2 = 4.0
VALIDATION_DMAX = 0.15
MIN_VALIDATION_N = 8
MIN_VALIDATION_NIGHTS = 3
MIN_VALIDATION_STATIONS = 5
MAX_VALIDATION_D50 = 0.12
CLONE_DRAWS = 500
MIN_CLONE_PASS = 0.80


def stable_id(event_ids: list[str]) -> str:
    payload = "|".join(sorted(map(str, event_ids))).encode()
    return "DT" + hashlib.sha256(payload).hexdigest()[:16]


def subset_prepared(prepared: dict[str, Any], keep: np.ndarray) -> dict[str, Any]:
    keep = np.asarray(keep, dtype=bool)
    data = prepared["data"].loc[keep].reset_index(drop=True)
    sol = data["sol_lon_deg"].to_numpy(float)
    slon = base.circ_diff(data["lamgeo_deg"].to_numpy(float), sol) % 360.0
    beta = data["betgeo_deg"].to_numpy(float)
    vg = data["vgeo_km_s"].to_numpy(float)
    reference = drift.circular_mean(sol)
    sol_u = drift.unwrap_about(sol, reference)
    return {
        "data": data,
        "sol": sol,
        "sol_unwrapped": sol_u,
        "sol_reference": reference,
        "slon": slon,
        "beta": beta,
        "vg": vg,
    }


def prepare_residual(year: int, month: int, current_codes: set[str]) -> dict[str, Any]:
    all_quality = drift.prepare_all_quality(base.load_month(year, month), year, month)
    data = all_quality["data"]
    recognized = np.asarray(
        [base.code_text(value) in current_codes for value in data["iau_code"].tolist()],
        dtype=bool,
    )
    return subset_prepared(all_quality, ~recognized)


def candidate_frame(track: dict[str, Any], prepared: dict[str, Any]) -> pd.DataFrame:
    wanted = set(map(str, track["event_ids"]))
    frame = prepared["data"].loc[
        prepared["data"]["unique_trajectory_identifier"].astype(str).isin(wanted)
    ].copy()
    if len(frame) != len(wanted):
        found = set(frame["unique_trajectory_identifier"].astype(str))
        missing = sorted(wanted - found)
        raise RuntimeError(f"track missing {len(missing)} event ids: {missing[:3]}")
    return frame.reset_index(drop=True)


def night_station_summary(frame: pd.DataFrame) -> dict[str, Any]:
    parsed = pd.to_datetime(frame["beginning_utc_time"], errors="coerce", utc=True, format="mixed")
    nights = parsed.dt.floor("D").astype(str)
    night_counts = nights.value_counts(dropna=False)
    station_sets = frame["participating_stations"].fillna("").astype(str)
    all_stations = set().union(*(base.station_tokens(value) for value in station_sets)) if len(frame) else set()
    station_set_fraction = float(station_sets.value_counts(normalize=True).iloc[0]) if len(frame) else 1.0
    return {
        "nights": int(nights.nunique()),
        "stations": int(len(all_stations)),
        "max_night_fraction": float(night_counts.iloc[0] / len(frame)) if len(frame) else 1.0,
        "max_station_set_fraction": station_set_fraction,
    }


def reference_center(track: dict[str, Any], prepared: dict[str, Any]) -> np.ndarray:
    ref_u = float(track["reference_sol_unwrapped"])
    ref_mod = ref_u % 360.0
    slon, beta, vg = drift.track_prediction(track, ref_mod, prepared)
    return np.asarray([slon, beta, vg, ref_mod], dtype=float)


def physical_adjudication(
    track: dict[str, Any],
    prepared: dict[str, Any],
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    frame = candidate_frame(track, prepared)
    ns = night_station_summary(frame)
    slopes = track["slopes"]
    center = reference_center(track, prepared)
    association = base.known_association(center, np.asarray(track["orbit_medoid"], dtype=float), catalog)
    source = base.source_warning(center)
    checks = {
        "span": 3.0 <= float(track["solar_span_deg"]) <= MAX_DISCOVERY_SPAN,
        "slope_slon": abs(float(slopes["slon_per_sol"])) <= MAX_SLOPE_SLON,
        "slope_beta": abs(float(slopes["beta_per_sol"])) <= MAX_SLOPE_BETA,
        "slope_vg": abs(float(slopes["vg_per_sol"])) <= MAX_SLOPE_VG,
        "nights": ns["nights"] >= MIN_DISCOVERY_NIGHTS,
        "night_dominance": ns["max_night_fraction"] <= MAX_DOMINANT_FRACTION,
        "stations": ns["stations"] >= MIN_DISCOVERY_STATIONS,
        "station_set_dominance": ns["max_station_set_fraction"] <= MAX_DOMINANT_FRACTION,
        "orbit_d50": float(track["orbit_median_d"]) <= MAX_DISCOVERY_D50,
        "orbit_d90": float(track["orbit_q90_d"]) <= MAX_DISCOVERY_D90,
        "known_association_clear": not bool(association["matched"]),
    }
    return {
        "pass": bool(all(checks.values())),
        "checks": checks,
        "night_station": ns,
        "reference_center": center.tolist(),
        "known_association": association,
        "sporadic_source": source,
    }


def track_predictions(track: dict[str, Any], sol_u: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dx = np.asarray(sol_u, dtype=float) - float(track["reference_sol_unwrapped"])
    slon = (float(track["reference_slon_unwrapped"]) + float(track["slopes"]["slon_per_sol"]) * dx) % 360.0
    beta = float(track["reference_beta"]) + float(track["slopes"]["beta_per_sol"]) * dx
    vg = float(track["reference_vg"]) + float(track["slopes"]["vg_per_sol"]) * dx
    return slon, beta, vg


def fixed_track_membership(
    track: dict[str, Any],
    prepared: dict[str, Any],
    discovery_sol_reference: float,
    orbit: np.ndarray,
    *,
    interval_center_shift: float = 0.0,
    intercept_offsets: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> tuple[np.ndarray, np.ndarray]:
    data = prepared["data"]
    sol_u = float(discovery_sol_reference) + base.circ_diff(
        data["sol_lon_deg"].to_numpy(float), float(discovery_sol_reference)
    )
    shift = float(interval_center_shift)
    low = float(track["solar_min_unwrapped"]) - 1.0 + shift
    high = float(track["solar_max_unwrapped"]) + 1.0 + shift
    in_time = (sol_u >= low) & (sol_u <= high)
    dx = sol_u - (float(track["reference_sol_unwrapped"]) + shift)
    pred_slon = (
        float(track["reference_slon_unwrapped"])
        + float(intercept_offsets[0])
        + float(track["slopes"]["slon_per_sol"]) * dx
    ) % 360.0
    pred_beta = (
        float(track["reference_beta"])
        + float(intercept_offsets[1])
        + float(track["slopes"]["beta_per_sol"]) * dx
    )
    pred_vg = (
        float(track["reference_vg"])
        + float(intercept_offsets[2])
        + float(track["slopes"]["vg_per_sol"]) * dx
    )
    residual_r2 = (
        (base.circ_diff(prepared["slon"], pred_slon) / 3.5) ** 2
        + ((prepared["beta"] - pred_beta) / 3.0) ** 2
        + ((prepared["vg"] - pred_vg) / 2.5) ** 2
    )
    orbit_valid = base.valid_orbits(data)
    d = np.full(len(data), np.inf, dtype=float)
    pre = np.flatnonzero(in_time & (residual_r2 <= VALIDATION_RADIUS2) & orbit_valid)
    if len(pre):
        d[pre] = base.d_sh_matrix(
            data.iloc[pre][base.ORBIT_COLUMNS].to_numpy(float),
            np.asarray(orbit, dtype=float)[None, :],
        )[:, 0]
    selected = in_time & (residual_r2 <= VALIDATION_RADIUS2) & (d <= VALIDATION_DMAX)
    return selected, d


def validate_track(
    track: dict[str, Any],
    prepared: dict[str, Any],
    discovery_sol_reference: float,
) -> dict[str, Any]:
    selected, d = fixed_track_membership(
        track,
        prepared,
        discovery_sol_reference,
        np.asarray(track["orbit_medoid"], dtype=float),
    )
    frame = prepared["data"].loc[selected].reset_index(drop=True)
    ns = night_station_summary(frame)
    count = int(selected.sum())
    d50 = float(np.median(d[selected])) if count else None
    passed = bool(
        count >= MIN_VALIDATION_N
        and ns["nights"] >= MIN_VALIDATION_NIGHTS
        and ns["stations"] >= MIN_VALIDATION_STATIONS
        and d50 is not None
        and d50 <= MAX_VALIDATION_D50
    )
    return {
        "members": count,
        "nights": ns["nights"],
        "stations": ns["stations"],
        "median_d_sh": d50,
        "passed": passed,
        "event_ids": frame["unique_trajectory_identifier"].astype(str).tolist(),
    }


def clone_stability(track: dict[str, Any], frame: pd.DataFrame, month: int, track_index: int) -> dict[str, Any]:
    valid = base.valid_orbits(frame)
    values = frame.loc[valid, base.ORBIT_COLUMNS].to_numpy(float)
    sigmas = frame.loc[valid, base.SIGMA_COLUMNS].to_numpy(float)
    sigmas = np.nan_to_num(np.abs(sigmas), nan=0.0, posinf=0.0, neginf=0.0)
    sigmas = np.minimum(sigmas, np.asarray([0.10, 0.10, 10.0, 20.0, 5.0])[None, :])
    rng = np.random.default_rng(base.SEED + month * 10000 + track_index)
    passed = 0
    medians = []
    for _ in range(CLONE_DRAWS):
        clone = values + rng.normal(size=values.shape) * sigmas
        clone[:, 0] = np.clip(clone[:, 0], 0.0, 1.49)
        clone[:, 1] = np.clip(clone[:, 1], 0.01, 1.99)
        clone[:, 2] = np.clip(clone[:, 2], 0.0, 180.0)
        clone[:, 3:] %= 360.0
        summary = base.orbit_summary(clone)
        medians.append(float(summary["median_d"]))
        if summary["median_d"] <= MAX_DISCOVERY_D50 and summary["q90_d"] <= MAX_DISCOVERY_D90:
            passed += 1
    fraction = passed / CLONE_DRAWS
    return {
        "draws": CLONE_DRAWS,
        "pass_fraction": float(fraction),
        "median_of_clone_medians": float(np.median(medians)),
        "passed": bool(fraction >= MIN_CLONE_PASS),
    }


def local_seed_pool(track: dict[str, Any], discovery: dict[str, Any]) -> np.ndarray:
    data = discovery["data"]
    candidate_ids = set(map(str, track["event_ids"]))
    sol_u = discovery["sol_unwrapped"]
    pred_slon, pred_beta, pred_vg = track_predictions(track, sol_u)
    radiant = np.asarray(
        [
            base.spherical_sep(float(a), float(b), float(c), float(d))
            for a, b, c, d in zip(discovery["slon"], discovery["beta"], pred_slon, pred_beta)
        ],
        dtype=float,
    )
    mask = (
        base.valid_orbits(data)
        & (np.abs(sol_u - float(track["reference_sol_unwrapped"])) <= 20.0)
        & (radiant <= 25.0)
        & (np.abs(discovery["vg"] - pred_vg) <= 10.0)
        & (~data["unique_trajectory_identifier"].astype(str).isin(candidate_ids).to_numpy())
    )
    return np.flatnonzero(mask)


def pseudo_track_null(
    track: dict[str, Any],
    discovery: dict[str, Any],
    validation: dict[int, dict[str, Any]],
    candidate_validation: dict[str, Any],
) -> dict[str, Any]:
    seeds = local_seed_pool(track, discovery)
    if len(seeds) == 0:
        return {"status": "LOCAL_NULL_INSUFFICIENT", "pseudo_track_count": 0, "pass": False}
    data = discovery["data"]
    sol_u = discovery["sol_unwrapped"]
    pred_slon, pred_beta, pred_vg = track_predictions(track, sol_u)
    candidate_r = min(
        int(candidate_validation["2025"]["members"]),
        int(candidate_validation["2024"]["members"]),
    )
    candidate_t = int(candidate_validation["2025"]["members"]) + int(candidate_validation["2024"]["members"])
    r_values = np.zeros(len(seeds), dtype=np.int64)
    t_values = np.zeros(len(seeds), dtype=np.int64)
    seed_ids = data.iloc[seeds]["unique_trajectory_identifier"].astype(str).tolist()
    for j, seed_index in enumerate(seeds):
        seed_sol_u = float(sol_u[seed_index])
        candidate_at_seed_slon = float(pred_slon[seed_index])
        slon_offset = float(base.circ_diff(discovery["slon"][seed_index], candidate_at_seed_slon))
        beta_offset = float(discovery["beta"][seed_index] - pred_beta[seed_index])
        vg_offset = float(discovery["vg"][seed_index] - pred_vg[seed_index])
        time_shift = seed_sol_u - float(track["reference_sol_unwrapped"])
        seed_orbit = data.iloc[int(seed_index)][base.ORBIT_COLUMNS].to_numpy(dtype=float)
        counts = []
        for year in VALIDATION_YEARS:
            selected, _d = fixed_track_membership(
                track,
                validation[year],
                float(discovery["sol_reference"]),
                seed_orbit,
                interval_center_shift=time_shift,
                intercept_offsets=(slon_offset, beta_offset, vg_offset),
            )
            counts.append(int(selected.sum()))
        r_values[j] = min(counts)
        t_values[j] = sum(counts)
    q99_r = int(np.quantile(r_values, 0.99, method="higher"))
    tied = t_values[r_values == q99_r]
    q99_t = int(np.quantile(tied, 0.99, method="higher")) if len(tied) else 0
    passed = candidate_r > q99_r or (candidate_r == q99_r and candidate_t > q99_t)
    order = sorted(
        range(len(seeds)),
        key=lambda idx: (-int(r_values[idx]), -int(t_values[idx]), seed_ids[idx]),
    )[:20]
    return {
        "status": "EXECUTED",
        "pseudo_track_count": int(len(seeds)),
        "candidate_R": int(candidate_r),
        "candidate_T": int(candidate_t),
        "null_R_q99_higher": int(q99_r),
        "null_T_q99_higher_given_R_q99": int(q99_t),
        "null_R_max": int(r_values.max()),
        "null_T_max": int(t_values.max()),
        "pass": bool(passed),
        "top_pseudo_tracks": [
            {"seed_event_id": seed_ids[idx], "R": int(r_values[idx]), "T": int(t_values[idx])}
            for idx in order
        ],
    }


def deduplicate(leads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(
        leads,
        key=lambda item: (
            -int(item["local_null"]["candidate_R"]),
            -int(item["local_null"]["candidate_T"]),
            -int(item["track"]["members"]),
            float(item["track"]["normalized_rms"]),
            item["lead_id"],
        ),
    )
    kept: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for lead in ordered:
        members = set(map(str, lead["track"]["event_ids"]))
        duplicate_of = None
        for other in kept:
            other_members = set(map(str, other["track"]["event_ids"]))
            overlap = len(members & other_members) / min(len(members), len(other_members))
            if overlap >= 0.50:
                duplicate_of = other["lead_id"]
                break
        if duplicate_of is None:
            kept.append(lead)
        else:
            copy = dict(lead)
            copy["duplicate_of"] = duplicate_of
            duplicates.append(copy)
    return kept, duplicates


def compact_assessment(item: dict[str, Any]) -> dict[str, Any]:
    track = dict(item["track"])
    # Final lead files preserve exact member IDs. Intermediate rejected tracks
    # keep compact summaries to avoid turning the raw workspace into a data dump.
    if not item.get("final_pre_dedup", False):
        track.pop("event_ids", None)
    out = dict(item)
    out["track"] = track
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--variant", choices=sorted(drift.VARIANTS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    month = int(args.month)
    if not 1 <= month <= 7:
        raise SystemExit("frozen 2026 drift protocol permits months 1..7 only")
    args.out.mkdir(parents=True, exist_ok=True)

    response = requests.get(base.MDC_URL, timeout=90)
    response.raise_for_status()
    mdc = response.json()
    catalog, current_codes = base.flatten_mdc(mdc)
    discovery = prepare_residual(DISCOVERY_YEAR, month, current_codes)
    print(
        f"2026-{month:02d}: residual rows={len(discovery['data'])}; variant={args.variant}; "
        f"MDC={mdc.get('version')}",
        flush=True,
    )
    tracks, generator_diagnostics = drift.tracks_for_variant(discovery, args.variant)
    print(f"  generated retained tracks={len(tracks)}", flush=True)

    assessments: list[dict[str, Any]] = []
    validation_cache: dict[int, dict[str, Any]] | None = None
    for index, track in enumerate(tracks):
        lead_id = stable_id(track["event_ids"])
        physical = physical_adjudication(track, discovery, catalog)
        item: dict[str, Any] = {
            "lead_id": lead_id,
            "track_index": int(index),
            "track": track,
            "physical": physical,
            "validation": None,
            "clone_stability": None,
            "local_null": None,
            "final_pre_dedup": False,
        }
        if not physical["pass"]:
            assessments.append(item)
            continue
        if validation_cache is None:
            validation_cache = {
                year: prepare_residual(year, month, current_codes) for year in VALIDATION_YEARS
            }
        validation = {
            str(year): validate_track(track, validation_cache[year], float(discovery["sol_reference"]))
            for year in VALIDATION_YEARS
        }
        item["validation"] = validation
        if not all(result["passed"] for result in validation.values()):
            assessments.append(item)
            continue
        frame = candidate_frame(track, discovery)
        clones = clone_stability(track, frame, month, index)
        item["clone_stability"] = clones
        if not clones["passed"]:
            assessments.append(item)
            continue
        local = pseudo_track_null(track, discovery, validation_cache, validation)
        item["local_null"] = local
        item["final_pre_dedup"] = bool(local.get("pass"))
        assessments.append(item)

    pre_dedup = [item for item in assessments if item["final_pre_dedup"]]
    leads, duplicates = deduplicate(pre_dedup)
    result = {
        "stage": "drift_track_2026_discovery_month_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_2026_DISCOVERY_PROTOCOL.md",
        "month": month,
        "variant": args.variant,
        "variant_config": drift.VARIANTS[args.variant],
        "mdc_version": mdc.get("version"),
        "mdc_shower_count": mdc.get("count"),
        "mdc_solution_rows": len(catalog),
        "residual_rows_2026": int(len(discovery["data"])),
        "generator_diagnostics": generator_diagnostics,
        "tracks_generated": int(len(tracks)),
        "physical_survivors": int(sum(bool(item["physical"]["pass"]) for item in assessments)),
        "both_year_survivors": int(
            sum(
                item["validation"] is not None
                and all(v["passed"] for v in item["validation"].values())
                for item in assessments
            )
        ),
        "pre_dedup_leads": int(len(pre_dedup)),
        "final_leads": int(len(leads)),
        "lead_ids": [item["lead_id"] for item in leads],
        "duplicate_lead_ids": [item["lead_id"] for item in duplicates],
        "assessments": [compact_assessment(item) for item in assessments],
        "final_lead_records": leads,
        "duplicates": duplicates,
    }
    json_path = args.out / f"drift_track_2026_month_{month:02d}.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        f"# 2026 drift-track discovery month {month:02d}",
        "",
        f"Variant: **{args.variant}**. MDC: **{mdc.get('version')}**. Residual rows: **{len(discovery['data'])}**.",
        f"Generated tracks: **{len(tracks)}**; physical survivors: **{result['physical_survivors']}**; "
        f"both-year survivors: **{result['both_year_survivors']}**; final leads: **{result['final_leads']}**.",
        "",
        "| id | N26 | span | dSLoR | dbeta | dVg | D50 | D90 | source | known clear | N25 | N24 | local R/T vs q99 | final |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---|---|",
    ]
    for item in assessments:
        track = item["track"]
        physical = item["physical"]
        source = physical["sporadic_source"]["nearest"]
        validation = item.get("validation") or {}
        v25 = validation.get("2025", {})
        v24 = validation.get("2024", {})
        local = item.get("local_null") or {}
        if local.get("status") == "EXECUTED":
            local_text = (
                f"{local['candidate_R']}/{local['candidate_T']} vs "
                f"{local['null_R_q99_higher']}/{local['null_T_q99_higher_given_R_q99']}"
            )
        else:
            local_text = local.get("status", "not run")
        lines.append(
            f"| {item['lead_id']} | {track['members']} | {track['solar_span_deg']:.2f} | "
            f"{track['slopes']['slon_per_sol']:.3f} | {track['slopes']['beta_per_sol']:.3f} | "
            f"{track['slopes']['vg_per_sol']:.3f} | {track['orbit_median_d']:.3f} | {track['orbit_q90_d']:.3f} | "
            f"{source['source']} ({source['separation_deg']:.1f}) | {physical['checks']['known_association_clear']} | "
            f"{v25.get('members',0)} | {v24.get('members',0)} | {local_text} | {item['final_pre_dedup']} |"
        )
    md_path = args.out / f"DRIFT_TRACK_2026_MONTH_{month:02d}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
