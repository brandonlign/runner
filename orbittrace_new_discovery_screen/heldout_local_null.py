#!/usr/bin/env python3
"""Execute the orbittrace-raw preregistered 2019-2021 local recurrence null.

This is a compute-only mirror.  The scientific protocol/source-of-truth is
``pipeline/discovery_search/HELDOUT_LOCAL_NULL_PROTOCOL.md`` in the private
``brandonlign/orbittrace-raw`` research branch.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader

ID = "unique_trajectory_identifier"
OBS = ["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s"]
ORBIT = ["e", "q_au", "i_deg", "peri_deg", "node_deg"]
QUALITY = ["num_stat", "medianfiterr_arcsec"]
OBS_SCALES = np.asarray([2.5, 3.5, 3.0, 2.5], dtype=float)  # sol, SLoR, beta, Vg
D_MAX = 0.15
HELDOUT_YEARS = (2019, 2020, 2021)


def circ_diff(a: Any, b: Any) -> np.ndarray:
    return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float) + 180.0) % 360.0 - 180.0


def circ_mean(values: np.ndarray) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def spherical_sep_array(lon: np.ndarray, lat: np.ndarray, lon0: float, lat0: float) -> np.ndarray:
    l1 = np.deg2rad(np.asarray(lon, dtype=float))
    b1 = np.deg2rad(np.asarray(lat, dtype=float))
    l0, b0 = math.radians(float(lon0)), math.radians(float(lat0))
    cosine = np.sin(b1) * math.sin(b0) + np.cos(b1) * math.cos(b0) * np.cos(l1 - l0)
    return np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0)))


def d_sh_matrix(left: np.ndarray, right: np.ndarray | None = None) -> np.ndarray:
    """Canonical Southworth-Hawkins D_SH matrix."""
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


def orbit_medoid(orbits: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    matrix = d_sh_matrix(orbits)
    idx = int(np.argmin(np.median(matrix, axis=1)))
    to_medoid = matrix[idx]
    pairwise = matrix[np.triu_indices(len(matrix), 1)] if len(matrix) > 1 else np.asarray([0.0])
    return orbits[idx], {
        "median_to_medoid": float(np.median(to_medoid)),
        "q90_to_medoid": float(np.quantile(to_medoid, 0.90)),
        "pairwise_median": float(np.median(pairwise)),
        "pairwise_q90": float(np.quantile(pairwise, 0.90)),
    }


def read_month(year: int, month: int) -> pd.DataFrame:
    key = f"{year}-{month:02d}"
    print(f"Downloading GMN {key}", flush=True)
    frame = reader.read_data(dd.get_monthly_file_content_by_date(key), output_camel_case=True).reset_index(drop=False)
    required = [ID, "iau_code", *OBS, *ORBIT]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise RuntimeError(f"GMN {key} missing columns {missing}")
    for column in [*OBS, *ORBIT, *QUALITY]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame[ID] = frame[ID].astype(str)
    return frame


def quality_orbit_mask(frame: pd.DataFrame) -> np.ndarray:
    valid = np.isfinite(frame[[*OBS, *ORBIT]].to_numpy(float)).all(axis=1)
    if "num_stat" in frame.columns:
        valid &= frame["num_stat"].fillna(0).to_numpy(float) >= 2
    if "medianfiterr_arcsec" in frame.columns:
        valid &= frame["medianfiterr_arcsec"].fillna(9999).to_numpy(float) <= 180
    orbit = frame[ORBIT].to_numpy(float)
    valid &= (orbit[:, 0] >= 0.0) & (orbit[:, 0] < 1.5)
    valid &= (orbit[:, 1] > 0.0) & (orbit[:, 1] < 2.0)
    valid &= (orbit[:, 2] >= 0.0) & (orbit[:, 2] <= 180.0)
    return valid


def code_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().upper()
    return "" if text in {"<NA>", "NAN", "NONE"} else text


def residual_mask(frame: pd.DataFrame, current_codes: set[str]) -> np.ndarray:
    return np.asarray([code_text(value) not in current_codes for value in frame["iau_code"].tolist()], dtype=bool)


def obs_panel(frame: pd.DataFrame) -> np.ndarray:
    sol = frame["sol_lon_deg"].to_numpy(float)
    slon = circ_diff(frame["lamgeo_deg"].to_numpy(float), sol)
    return np.column_stack([sol, slon, frame["betgeo_deg"].to_numpy(float), frame["vgeo_km_s"].to_numpy(float)])


def template_center(frame: pd.DataFrame) -> np.ndarray:
    panel = obs_panel(frame)
    return np.asarray([
        circ_mean(panel[:, 0]),
        circ_mean(panel[:, 1]),
        float(np.median(panel[:, 2])),
        float(np.median(panel[:, 3])),
    ])


def obs_r2(panel: np.ndarray, center: np.ndarray) -> np.ndarray:
    return (
        (circ_diff(panel[:, 0], center[0]) / OBS_SCALES[0]) ** 2
        + (circ_diff(panel[:, 1], center[1]) / OBS_SCALES[1]) ** 2
        + ((panel[:, 2] - center[2]) / OBS_SCALES[2]) ** 2
        + ((panel[:, 3] - center[3]) / OBS_SCALES[3]) ** 2
    )


def count_one_template(center: np.ndarray, orbit: np.ndarray, frame: pd.DataFrame) -> tuple[int, list[str]]:
    if len(frame) == 0:
        return 0, []
    panel = obs_panel(frame)
    obs_mask = obs_r2(panel, center) <= 1.0
    indices = np.flatnonzero(obs_mask)
    if len(indices) == 0:
        return 0, []
    orbits = frame.iloc[indices][ORBIT].to_numpy(float)
    d = d_sh_matrix(np.asarray(orbit, dtype=float)[None, :], orbits)[0]
    keep_local = np.flatnonzero(d <= D_MAX)
    keep = indices[keep_local]
    return int(len(keep)), frame.iloc[keep][ID].astype(str).tolist()


def batch_template_counts(centers: np.ndarray, orbits: np.ndarray, frame: pd.DataFrame, batch_size: int = 24) -> np.ndarray:
    """Count fixed memberships for many pseudo-templates without a huge D matrix."""
    if len(centers) == 0 or len(frame) == 0:
        return np.zeros(len(centers), dtype=np.int64)
    target_panel = obs_panel(frame)
    target_orbits = frame[ORBIT].to_numpy(float)
    counts = np.zeros(len(centers), dtype=np.int64)
    for start in range(0, len(centers), batch_size):
        stop = min(len(centers), start + batch_size)
        c = centers[start:stop]
        # Shape: batch x target events.  Circular differences for the two angular axes.
        r2 = (
            (circ_diff(target_panel[None, :, 0], c[:, None, 0]) / OBS_SCALES[0]) ** 2
            + (circ_diff(target_panel[None, :, 1], c[:, None, 1]) / OBS_SCALES[1]) ** 2
            + ((target_panel[None, :, 2] - c[:, None, 2]) / OBS_SCALES[2]) ** 2
            + ((target_panel[None, :, 3] - c[:, None, 3]) / OBS_SCALES[3]) ** 2
        )
        for local_index, mask in enumerate(r2 <= 1.0):
            candidate_indices = np.flatnonzero(mask)
            if len(candidate_indices) == 0:
                continue
            ds = d_sh_matrix(orbits[start + local_index][None, :], target_orbits[candidate_indices])[0]
            counts[start + local_index] = int(np.sum(ds <= D_MAX))
    return counts


def local_seed_templates(frame: pd.DataFrame, candidate_center: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[str]]:
    panel = obs_panel(frame)
    radiant_sep = spherical_sep_array(panel[:, 1], panel[:, 2], candidate_center[1], candidate_center[2])
    mask = (
        (np.abs(circ_diff(panel[:, 0], candidate_center[0])) <= 20.0)
        & (radiant_sep <= 25.0)
        & (np.abs(panel[:, 3] - candidate_center[3]) <= 10.0)
    )
    selected = frame.loc[mask].reset_index(drop=True)
    return obs_panel(selected), selected[ORBIT].to_numpy(float), selected[ID].astype(str).tolist()


def q99_higher(values: np.ndarray) -> int:
    if len(values) == 0:
        return 0
    return int(np.quantile(np.asarray(values, dtype=float), 0.99, method="higher"))


def rotation_result(seed_year: int, candidate_counts: dict[int, int], heldout: dict[int, pd.DataFrame], candidate_center: np.ndarray) -> dict[str, Any]:
    compare_years = [year for year in HELDOUT_YEARS if year != seed_year]
    seed_frame = heldout[seed_year]
    centers, orbits, seed_ids = local_seed_templates(seed_frame, candidate_center)
    counts_a = batch_template_counts(centers, orbits, heldout[compare_years[0]])
    counts_b = batch_template_counts(centers, orbits, heldout[compare_years[1]])
    recurrence = np.minimum(counts_a, counts_b)
    totals = counts_a + counts_b
    q99_r = q99_higher(recurrence)
    candidate_r = min(candidate_counts[compare_years[0]], candidate_counts[compare_years[1]])
    candidate_t = candidate_counts[compare_years[0]] + candidate_counts[compare_years[1]]
    same_r = totals[recurrence == q99_r]
    q99_t_at_r = q99_higher(same_r) if len(same_r) else 0
    passed = candidate_r > q99_r or (candidate_r == q99_r and candidate_t > q99_t_at_r)
    return {
        "seed_year": seed_year,
        "compare_years": compare_years,
        "pseudo_template_count": int(len(centers)),
        "candidate_R": int(candidate_r),
        "candidate_T": int(candidate_t),
        "null_R_q99_higher": int(q99_r),
        "null_T_q99_higher_given_R_q99": int(q99_t_at_r),
        "null_R_max": int(recurrence.max()) if len(recurrence) else 0,
        "null_T_max": int(totals.max()) if len(totals) else 0,
        "null_R_histogram": {str(value): int(np.sum(recurrence == value)) for value in np.unique(recurrence)},
        "pass": bool(passed),
        "top_pseudo_templates": [
            {
                "seed_event_id": seed_ids[int(index)],
                "count_a": int(counts_a[int(index)]),
                "count_b": int(counts_b[int(index)]),
                "R": int(recurrence[int(index)]),
                "T": int(totals[int(index)]),
            }
            for index in np.argsort(np.column_stack([-recurrence, -totals])[:, 0])[:0]
        ],
    }


def candidate_result(rank: int, scan: dict[str, Any], current_codes: set[str]) -> dict[str, Any]:
    family_id = scan["rankings"]["locked_rrf"][rank - 1]
    family = next(item for item in scan["families"] if item["family_id"] == family_id)
    event_ids = set(map(str, family["event_ids"]))
    month_numbers = sorted({int(event_id[4:6]) for event_id in event_ids})
    if len(month_numbers) != 1:
        raise RuntimeError(f"rank {rank} unexpectedly spans multiple calendar months {month_numbers}")
    month = month_numbers[0]

    search_month_keys = sorted({(int(event_id[:4]), int(event_id[4:6])) for event_id in event_ids})
    search_frames = {(year, mon): read_month(year, mon) for year, mon in search_month_keys}
    member_parts = [frame[frame[ID].isin(event_ids)].copy() for frame in search_frames.values()]
    members = pd.concat(member_parts, ignore_index=True)
    found = set(members[ID].astype(str))
    missing = sorted(event_ids - found)
    if missing:
        raise RuntimeError(f"rank {rank} missing exact frozen events: {missing[:5]}")
    members = members.loc[quality_orbit_mask(members)].reset_index(drop=True)
    if len(members) < max(8, int(0.8 * len(event_ids))):
        raise RuntimeError(f"rank {rank} has insufficient valid frozen-member orbits {len(members)}/{len(event_ids)}")
    center = template_center(members)
    medoid, internal = orbit_medoid(members[ORBIT].to_numpy(float))

    heldout: dict[int, pd.DataFrame] = {}
    for year in HELDOUT_YEARS:
        frame = read_month(year, month)
        mask = quality_orbit_mask(frame) & residual_mask(frame, current_codes)
        heldout[year] = frame.loc[mask].reset_index(drop=True)

    candidate_counts: dict[int, int] = {}
    candidate_ids: dict[int, list[str]] = {}
    for year in HELDOUT_YEARS:
        count, ids = count_one_template(center, medoid, heldout[year])
        candidate_counts[year] = count
        candidate_ids[year] = ids

    rotations = [rotation_result(year, candidate_counts, heldout, center) for year in HELDOUT_YEARS]
    minimum_recurrence = all(candidate_counts[year] >= 2 for year in HELDOUT_YEARS)
    rotation_passes = sum(item["pass"] for item in rotations)
    passed = minimum_recurrence and rotation_passes >= 2
    return {
        "rank": rank,
        "family_id": family_id,
        "search_years": family["years"],
        "frozen_family_event_count": int(family["event_count"]),
        "valid_template_event_count": int(len(members)),
        "month": month,
        "template_center": {
            "sol": float(center[0]),
            "sun_lon": float(center[1]),
            "ecl_lat": float(center[2]),
            "vg": float(center[3]),
        },
        "orbit_medoid": medoid.tolist(),
        "template_internal_d_sh": internal,
        "heldout_residual_rows": {str(year): int(len(heldout[year])) for year in HELDOUT_YEARS},
        "heldout_candidate_match_counts": {str(year): int(candidate_counts[year]) for year in HELDOUT_YEARS},
        "heldout_candidate_event_ids": {str(year): candidate_ids[year] for year in HELDOUT_YEARS},
        "minimum_two_each_year": bool(minimum_recurrence),
        "rotations": rotations,
        "rotation_pass_count": int(rotation_passes),
        "pass_heldout_local_recurrence_gate": bool(passed),
    }


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Held-out local-source recurrence null",
        "",
        f"Current MDC: **{result['mdc_version']}**. Held-out years are 2019–2021. Membership and pass rules were frozen in orbittrace-raw before execution.",
        "",
    ]
    for candidate in result["candidates"]:
        c = candidate["template_center"]
        lines.extend([
            f"## Rank {candidate['rank']} `{candidate['family_id']}`",
            "",
            f"Template: λ☉ {c['sol']:.2f}°, SLoR {c['sun_lon']:.2f}°, β {c['ecl_lat']:.2f}°, Vg {c['vg']:.2f} km/s. "
            f"Frozen-template internal D_SH median {candidate['template_internal_d_sh']['median_to_medoid']:.3f}.",
            "",
            f"Held-out fixed-template matches: **{candidate['heldout_candidate_match_counts']}**.",
            "",
            "| pseudo seed year | comparison years | pseudo templates | candidate R | null R q99 | candidate T | conditional null T q99 | rotation pass |",
            "|---:|---|---:|---:|---:|---:|---:|---|",
        ])
        for rotation in candidate["rotations"]:
            lines.append(
                f"| {rotation['seed_year']} | {rotation['compare_years']} | {rotation['pseudo_template_count']} | "
                f"{rotation['candidate_R']} | {rotation['null_R_q99_higher']} | {rotation['candidate_T']} | "
                f"{rotation['null_T_q99_higher_given_R_q99']} | {'PASS' if rotation['pass'] else 'FAIL'} |"
            )
        lines.extend([
            "",
            f"Frozen gate: **{'PASS' if candidate['pass_heldout_local_recurrence_gate'] else 'FAIL'}** "
            f"({candidate['rotation_pass_count']}/3 null rotations passed; >=2 matches in every held-out year: {candidate['minimum_two_each_year']}).",
            "",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--mdc", type=Path, required=True)
    parser.add_argument("--ranks", type=int, nargs="+", default=[95, 105])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    opener = gzip.open if args.scan.suffix == ".gz" else open
    with opener(args.scan, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(args.mdc.read_text(encoding="utf-8"))
    current_codes = {
        str(shower.get("Code") or "").strip().upper()
        for shower in mdc.get("data", [])
        if str(shower.get("Code") or "").strip()
    }
    result = {
        "version": "heldout-local-null-v1-preregistered",
        "mdc_version": mdc.get("version"),
        "heldout_years": list(HELDOUT_YEARS),
        "membership": {
            "obs_scales": {"sol": 2.5, "sun_lon": 3.5, "ecl_lat": 3.0, "vg": 2.5},
            "obs_radius": 1.0,
            "d_sh_max": D_MAX,
        },
        "candidates": [candidate_result(rank, scan, current_codes) for rank in args.ranks],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "heldout_local_null.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    markdown = render(result)
    (args.out / "HELDOUT_LOCAL_NULL.md").write_text(markdown)
    print(markdown, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
