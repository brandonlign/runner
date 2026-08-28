#!/usr/bin/env python3
"""Compute-only mirror of orbittrace-raw TWO_YEAR_EXPANSION_PROTOCOL.

Scientific source-of-truth is ``brandonlign/orbittrace-raw`` on branch
``research/prospective-discovery-20260828``.  This runner copy exists only to
execute the frozen protocol while private raw Actions are unavailable.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from orbittrace_new_discovery_screen import heldout_local_null as held

ID = held.ID
OBS = held.OBS
ORBIT = held.ORBIT
HELDOUT_YEARS = held.HELDOUT_YEARS
OBS_SCALES = held.OBS_SCALES
D_MAX = held.D_MAX


def finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def status_number(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def flatten_mdc(mdc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for shower in mdc.get("data", []):
        for solution in shower.get("solution", []) or []:
            orbit_values = [finite(solution.get(key)) for key in ("e", "q", "incl", "peri", "node")]
            orbit = None if any(value is None for value in orbit_values) else [float(value) for value in orbit_values]
            rows.append({
                "iau_no": str(shower.get("IAUNo") or "").strip(),
                "code": str(shower.get("Code") or "").strip(),
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
            })
    return rows


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float:
    if start is not None and end is not None:
        span = (end - start) % 360.0
        if span <= 120.0:
            offset = (value - start) % 360.0
            if offset <= span:
                return 0.0
            return min(abs(float(held.circ_diff(value, start))), abs(float(held.circ_diff(value, end))))
    if center is not None:
        return abs(float(held.circ_diff(value, center)))
    return 180.0


def spherical_sep(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    cosine = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def family_year_counts(family: dict[str, Any]) -> dict[int, int]:
    return dict(Counter(int(str(event_id)[:4]) for event_id in family["event_ids"]))


def weighted_circ(values: list[float], weights: list[float]) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float))
    w = np.asarray(weights, dtype=float)
    return float(np.rad2deg(np.arctan2(np.sum(w * np.sin(radians)), np.sum(w * np.cos(radians)))) % 360.0)


def family_centroid(family: dict[str, Any]) -> dict[str, float]:
    counts = family_year_counts(family)
    rows = [(centroid, float(counts.get(int(year), 1))) for year, centroid in family["centroids"].items()]
    weights = [weight for _centroid, weight in rows]
    return {
        "sol": weighted_circ([float(row["sol"]) for row, _ in rows], weights),
        "sun_lon": weighted_circ([float(row["sun_lon"]) for row, _ in rows], weights),
        "ecl_lat": float(np.average([float(row["ecl_lat"]) for row, _ in rows], weights=weights)),
        "vg": float(np.average([float(row["vg"]) for row, _ in rows], weights=weights)),
    }


def observational_matches(center: dict[str, float], mdc_rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    assessed = []
    for row in mdc_rows:
        timing = interval_distance(center["sol"], row["LoSb"], row["LoSe"], row["LoS"])
        if None not in {row["S_LoR"], row["LaR"], row["Vg"]}:
            radiant = spherical_sep(center["sun_lon"], center["ecl_lat"], row["S_LoR"], row["LaR"])
            speed = abs(center["vg"] - row["Vg"])
            score = math.sqrt((timing / 12.0) ** 2 + (radiant / 10.0) ** 2 + (speed / 8.0) ** 2)
            close = timing <= 12.0 and radiant <= 10.0 and speed <= 8.0
        else:
            radiant = speed = score = None
            close = False
        item = dict(row)
        item.update({
            "timing_delta_deg": timing,
            "radiant_sep_deg": radiant,
            "speed_delta_km_s": speed,
            "obs_score": score,
            "observational_close": close,
        })
        assessed.append(item)
    assessed.sort(key=lambda row: (
        not row["observational_close"],
        float("inf") if row["obs_score"] is None else row["obs_score"],
        row["timing_delta_deg"],
    ))
    return assessed[:limit]


def known_association(center: dict[str, float], medoid: np.ndarray, mdc_rows: list[dict[str, Any]], limit: int = 15) -> dict[str, Any]:
    complete = [(index, row) for index, row in enumerate(mdc_rows) if row["orbit"] is not None]
    d_by_index: dict[int, float] = {}
    if complete:
        d = held.d_sh_matrix(medoid[None, :], np.asarray([row["orbit"] for _index, row in complete], dtype=float))[0]
        d_by_index = {index: float(value) for (index, _row), value in zip(complete, d)}
    rows = []
    for index, row in enumerate(mdc_rows):
        timing = interval_distance(center["sol"], row["LoSb"], row["LoSe"], row["LoS"])
        if None not in {row["S_LoR"], row["LaR"], row["Vg"]}:
            radiant = spherical_sep(center["sun_lon"], center["ecl_lat"], row["S_LoR"], row["LaR"])
            speed = abs(center["vg"] - row["Vg"])
            score = math.sqrt((timing / 12.0) ** 2 + (radiant / 10.0) ** 2 + (speed / 8.0) ** 2)
            obs_close = timing <= 12.0 and radiant <= 10.0 and speed <= 8.0
        else:
            radiant = speed = score = None
            obs_close = False
        ds = d_by_index.get(index)
        orbit_close = ds is not None and ds <= 0.12 and timing <= 20.0
        broad_orbit_close = ds is not None and ds <= 0.20 and timing <= 30.0
        item = dict(row)
        item.update({
            "d_sh": ds,
            "timing_delta_deg": timing,
            "radiant_sep_deg": radiant,
            "speed_delta_km_s": speed,
            "obs_score": score,
            "observational_close": obs_close,
            "orbit_close": orbit_close,
            "broad_orbit_close": broad_orbit_close,
            "plausible": obs_close or orbit_close or broad_orbit_close,
        })
        rows.append(item)
    rows.sort(key=lambda row: (
        not row["plausible"],
        float("inf") if row["obs_score"] is None else row["obs_score"],
        float("inf") if row["d_sh"] is None else row["d_sh"],
    ))
    return {
        "plausible_any_status": any(row["plausible"] for row in rows),
        "best": rows[:limit],
        "nearest_orbit": sorted(
            [row for row in rows if row["d_sh"] is not None],
            key=lambda row: row["d_sh"],
        )[:limit],
    }


def source_warning(center: dict[str, float]) -> dict[str, Any]:
    sources = {
        "HELION": (342.0, 0.0), "ANTIHELION": (198.0, 0.0),
        "NORTH_APEX": (271.0, 20.0), "SOUTH_APEX": (273.0, -20.0),
        "NORTH_TOROIDAL": (270.0, 60.0), "SOUTH_TOROIDAL": (270.0, -60.0),
    }
    rows = [{"source": name, "separation_deg": spherical_sep(center["sun_lon"], center["ecl_lat"], lon, lat)} for name, (lon, lat) in sources.items()]
    rows.sort(key=lambda row: row["separation_deg"])
    return {"within_25_deg": rows[0]["separation_deg"] <= 25.0, "nearest": rows[0]}


def center_from_frame(frame: pd.DataFrame) -> dict[str, float]:
    values = held.template_center(frame)
    return {"sol": float(values[0]), "sun_lon": float(values[1]), "ecl_lat": float(values[2]), "vg": float(values[3])}


def q99(values: np.ndarray) -> int:
    return int(np.quantile(values.astype(float), 0.99, method="higher")) if len(values) else 0


def validate_heldout(
    family: dict[str, Any], exact_valid: pd.DataFrame, orbit_medoid: np.ndarray,
    current_codes: set[str], cache: dict[tuple[int, int], pd.DataFrame],
) -> dict[str, Any]:
    candidate_ids = set(map(str, family["event_ids"]))
    search_years = sorted({int(event_id[:4]) for event_id in candidate_ids})
    months = sorted({int(event_id[4:6]) for event_id in candidate_ids})
    center = held.template_center(exact_valid)

    heldout_frames: dict[int, pd.DataFrame] = {}
    for year in HELDOUT_YEARS:
        frame = concat_months([year], months, cache)
        mask = held.quality_orbit_mask(frame) & held.residual_mask(frame, current_codes)
        heldout_frames[year] = frame.loc[mask].reset_index(drop=True)

    candidate_counts = {}
    candidate_ids_by_year = {}
    for year in HELDOUT_YEARS:
        count, ids = held.count_one_template(center, orbit_medoid, heldout_frames[year])
        candidate_counts[year] = count
        candidate_ids_by_year[year] = ids

    search_frame = concat_months(search_years, months, cache)
    mask = held.quality_orbit_mask(search_frame) & held.residual_mask(search_frame, current_codes)
    search_residual = search_frame.loc[mask & ~search_frame[ID].isin(candidate_ids)].reset_index(drop=True)
    pseudo_centers, pseudo_orbits, pseudo_ids = held.local_seed_templates(search_residual, center)
    count_cols = [held.batch_template_counts(pseudo_centers, pseudo_orbits, heldout_frames[year]) for year in HELDOUT_YEARS]
    pseudo_counts = np.column_stack(count_cols) if len(pseudo_centers) else np.empty((0, 3), dtype=np.int64)
    pseudo_s2 = np.sort(pseudo_counts, axis=1)[:, 1] if len(pseudo_counts) else np.asarray([], dtype=np.int64)
    pseudo_t = pseudo_counts.sum(axis=1) if len(pseudo_counts) else np.asarray([], dtype=np.int64)
    candidate_vector = np.asarray([candidate_counts[year] for year in HELDOUT_YEARS], dtype=np.int64)
    candidate_s2 = int(np.sort(candidate_vector)[1])
    candidate_t = int(candidate_vector.sum())
    q99_s2 = q99(pseudo_s2)
    conditional_t = pseudo_t[pseudo_s2 == q99_s2] if len(pseudo_s2) else np.asarray([], dtype=np.int64)
    q99_t = q99(conditional_t)
    minimum = candidate_s2 >= 2 and candidate_t >= 5
    beats = candidate_s2 > q99_s2 or (candidate_s2 == q99_s2 and candidate_t > q99_t)
    top_indices = sorted(range(len(pseudo_centers)), key=lambda i: (-int(pseudo_s2[i]), -int(pseudo_t[i]), pseudo_ids[i]))[:20]
    return {
        "heldout_counts": {str(year): int(candidate_counts[year]) for year in HELDOUT_YEARS},
        "heldout_event_ids": {str(year): candidate_ids_by_year[year] for year in HELDOUT_YEARS},
        "heldout_residual_rows": {str(year): int(len(heldout_frames[year])) for year in HELDOUT_YEARS},
        "candidate_S2": candidate_s2,
        "candidate_T": candidate_t,
        "minimum_confirmation": minimum,
        "pseudo_template_count": int(len(pseudo_centers)),
        "null_S2_q99_higher": q99_s2,
        "null_T_q99_higher_given_S2_q99": q99_t,
        "null_S2_max": int(pseudo_s2.max()) if len(pseudo_s2) else 0,
        "null_T_max": int(pseudo_t.max()) if len(pseudo_t) else 0,
        "null_S2_histogram": {str(v): int(np.sum(pseudo_s2 == v)) for v in np.unique(pseudo_s2)},
        "beats_local_null": beats,
        "pass_heldout_gate": bool(minimum and beats),
        "top_pseudo_templates": [{
            "seed_event_id": pseudo_ids[i], "counts": [int(v) for v in pseudo_counts[i].tolist()],
            "S2": int(pseudo_s2[i]), "T": int(pseudo_t[i]),
        } for i in top_indices],
    }


def load_month(year: int, month: int, cache: dict[tuple[int, int], pd.DataFrame]) -> pd.DataFrame:
    key = (year, month)
    if key not in cache:
        cache[key] = held.read_month(f"{year}-{month:02d}") if False else held.read_month(year, month)
        cache[key]["source_year"] = year
        cache[key]["source_month"] = month
    return cache[key]


def concat_months(years: list[int], months: list[int], cache: dict[tuple[int, int], pd.DataFrame]) -> pd.DataFrame:
    frame = pd.concat([load_month(year, month, cache) for year in years for month in months], ignore_index=True)
    return frame.drop_duplicates(ID).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--mdc", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    opener = gzip.open if args.scan.suffix == ".gz" else open
    with opener(args.scan, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(args.mdc.read_text())
    mdc_rows = flatten_mdc(mdc)
    current_codes = {str(shower.get("Code") or "").strip().upper() for shower in mdc.get("data", []) if str(shower.get("Code") or "").strip()}

    selected = []
    for family in sorted(scan["families"], key=lambda f: int(f["locked_rrf_rank"])):
        counts = family_year_counts(family)
        if int(family["year_count"]) != 2 or int(family["event_count"]) < 10 or min(counts.values()) < 4:
            continue
        centroid = family_centroid(family)
        matches = observational_matches(centroid, mdc_rows)
        if any(match["observational_close"] for match in matches):
            continue
        selected.append((family, centroid, matches))

    cache: dict[tuple[int, int], pd.DataFrame] = {}
    rows = []
    physical_survivors = []
    for family, centroid, centroid_matches in selected:
        event_ids = set(map(str, family["event_ids"]))
        years = sorted({int(event_id[:4]) for event_id in event_ids})
        months = sorted({int(event_id[4:6]) for event_id in event_ids})
        search = concat_months(years, months, cache)
        exact = search[search[ID].isin(event_ids)].copy().reset_index(drop=True)
        found = set(exact[ID].astype(str))
        missing = sorted(event_ids - found)
        quality = exact.loc[held.quality_orbit_mask(exact)].reset_index(drop=True)
        fraction = len(quality) / max(1, int(family["event_count"]))
        row = {
            "rank": int(family["locked_rrf_rank"]), "family_id": family["family_id"],
            "search_years": years, "search_months": months, "frozen_event_count": int(family["event_count"]),
            "year_counts": {str(k): int(v) for k, v in sorted(family_year_counts(family).items())},
            "centroid_center": centroid, "centroid_nearest_mdc": centroid_matches[:5],
            "missing_exact_ids": missing, "valid_orbit_count": int(len(quality)), "valid_orbit_fraction": fraction,
            "sporadic_source": source_warning(centroid),
        }
        if missing or len(quality) < 8 or fraction < 0.80:
            row["physical_gate"] = {"pass": False, "reason": "RESOLUTION_OR_ORBIT_COMPLETENESS"}
            rows.append(row)
            continue
        orbit_medoid, internal = held.orbit_medoid(quality[ORBIT].to_numpy(float))
        exact_center = center_from_frame(quality)
        association = known_association(exact_center, orbit_medoid, mdc_rows)
        coherent = internal["median_to_medoid"] <= 0.08 and internal["q90_to_medoid"] <= 0.16
        no_known = not association["plausible_any_status"]
        physical_pass = bool(coherent and no_known)
        row.update({
            "exact_center": exact_center, "orbit_medoid": orbit_medoid.tolist(), "internal_d_sh": internal,
            "known_association": association, "sporadic_source": source_warning(exact_center),
            "physical_gate": {
                "pass": physical_pass,
                "median_d_sh_le_0_08": internal["median_to_medoid"] <= 0.08,
                "q90_d_sh_le_0_16": internal["q90_to_medoid"] <= 0.16,
                "no_any_status_mdc_association": no_known,
            },
        })
        rows.append(row)
        if physical_pass:
            physical_survivors.append((row, family, quality, orbit_medoid))

    # Only now touch 2019-2021 for physical survivors.
    for row, family, quality, orbit_medoid in physical_survivors:
        row["heldout_validation"] = validate_heldout(family, quality, orbit_medoid, current_codes, cache)

    leads = [row for row, _f, _q, _o in physical_survivors if row["heldout_validation"]["pass_heldout_gate"]]
    result = {
        "version": "two-year-locked-rrf-expansion-v1",
        "protocol_id": "orbittrace-raw/TWO_YEAR_EXPANSION_PROTOCOL@f168a754",
        "mdc_version": mdc.get("version"), "mdc_shower_count": mdc.get("count"), "mdc_solution_rows": len(mdc_rows),
        "centroid_veto_survivor_count": len(selected), "physical_gate_survivor_count": len(physical_survivors),
        "heldout_pass_count": len(leads), "heldout_pass_ranks": [row["rank"] for row in leads],
        "candidates": rows,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "two_year_lane.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Two-year locked-RRF expansion", "",
        f"MDC {result['mdc_version']}; centroid-veto survivors {len(selected)}; physical survivors {len(physical_survivors)}; held-out leads {len(leads)}.", "",
        "| rank | family | years | N | Dmed | Dq90 | source | physical | heldout | S2/T | null99 | final |",
        "|---:|---|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for row in rows:
        internal = row.get("internal_d_sh", {})
        source = row["sporadic_source"]["nearest"]
        validation = row.get("heldout_validation")
        heldout_text = str(validation["heldout_counts"]) if validation else "—"
        st = f"{validation['candidate_S2']}/{validation['candidate_T']}" if validation else "—"
        null = f"{validation['null_S2_q99_higher']}/{validation['null_T_q99_higher_given_S2_q99']}" if validation else "—"
        final = "PASS" if validation and validation["pass_heldout_gate"] else ("FAIL" if validation else "—")
        lines.append(
            f"| {row['rank']} | `{row['family_id']}` | {row['search_years']} | {row['frozen_event_count']} | "
            f"{internal.get('median_to_medoid', float('nan')):.3f} | {internal.get('q90_to_medoid', float('nan')):.3f} | "
            f"{source['source']} ({source['separation_deg']:.1f}°) | {'PASS' if row['physical_gate']['pass'] else 'FAIL'} | "
            f"{heldout_text} | {st} | {null} | {final} |"
        )
    markdown = "\n".join(lines) + "\n"
    (args.out / "TWO_YEAR_LANE.md").write_text(markdown)
    print(markdown, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
