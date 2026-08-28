#!/usr/bin/env python3
"""Orbit-level adjudication of locked-RRF discovery leads against current MDC and GMN labels.

The frozen locked-RRF catalogue supplies candidate identities. This script does not
rerun, tune, merge, or rerank that catalogue. It resolves exact candidate event IDs
back to the GMN monthly files, measures their orbital coherence, compares their
medoid orbit to every complete IAU MDC mean solution, and compares them to nearby
GMN events already labelled as the most relevant known shower.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader

ORBIT_COLUMNS = ["e", "q_au", "i_deg", "peri_deg", "node_deg"]
OBS_COLUMNS = ["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s"]
QUALITY_COLUMNS = ["num_stat", "medianfiterr_arcsec"]
ID_COLUMN = "unique_trajectory_identifier"


def finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def circ_diff(a: Any, b: Any) -> np.ndarray:
    return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float) + 180.0) % 360.0 - 180.0


def circ_mean(values: np.ndarray) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def perihelion_vector(orbits: np.ndarray) -> np.ndarray:
    inc = np.deg2rad(orbits[:, 2])
    arg = np.deg2rad(orbits[:, 3])
    node = np.deg2rad(orbits[:, 4])
    return np.column_stack([
        np.cos(node) * np.cos(arg) - np.sin(node) * np.sin(arg) * np.cos(inc),
        np.sin(node) * np.cos(arg) + np.cos(node) * np.sin(arg) * np.cos(inc),
        np.sin(arg) * np.sin(inc),
    ])


def d_sh_matrix(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    """Southworth-Hawkins D_SH using plane and eccentricity-vector angles."""
    a = np.asarray(a, dtype=float)
    b = a if b is None else np.asarray(b, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1, n1 = np.deg2rad(a[:, 2])[:, None], np.deg2rad(a[:, 4])[:, None]
    i2, n2 = np.deg2rad(b[:, 2])[None, :], np.deg2rad(b[:, 4])[None, :]
    plane = np.arccos(np.clip(np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(n1 - n2), -1.0, 1.0))
    p1, p2 = perihelion_vector(a), perihelion_vector(b)
    peri = np.arccos(np.clip(p1 @ p2.T, -1.0, 1.0))
    d2 = (
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * np.sin(plane / 2.0)) ** 2
        + (((e1 + e2) / 2.0) * 2.0 * np.sin(peri / 2.0)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))


def valid_orbit_mask(frame: pd.DataFrame) -> np.ndarray:
    values = frame[ORBIT_COLUMNS].to_numpy(float)
    valid = np.isfinite(values).all(axis=1)
    valid &= (values[:, 0] >= 0.0) & (values[:, 0] < 1.5)
    valid &= (values[:, 1] > 0.0) & (values[:, 1] < 2.0)
    valid &= (values[:, 2] >= 0.0) & (values[:, 2] <= 180.0)
    return valid


def orbit_medoid(orbits: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    matrix = d_sh_matrix(orbits)
    median_each = np.median(matrix, axis=1)
    idx = int(np.argmin(median_each))
    d = matrix[idx]
    upper = matrix[np.triu_indices(len(matrix), 1)] if len(matrix) > 1 else np.asarray([0.0])
    return orbits[idx], {
        "medoid_index": idx,
        "median_to_medoid": float(np.median(d)),
        "q90_to_medoid": float(np.quantile(d, 0.90)),
        "max_to_medoid": float(np.max(d)),
        "pairwise_median": float(np.median(upper)),
        "pairwise_q90": float(np.quantile(upper, 0.90)),
    }


def obs_center(frame: pd.DataFrame) -> dict[str, float]:
    sol = frame["sol_lon_deg"].to_numpy(float)
    slon = circ_diff(frame["lamgeo_deg"].to_numpy(float), sol)
    return {
        "sol": circ_mean(sol),
        "sun_lon": circ_mean(slon),
        "ecl_lat": float(np.median(frame["betgeo_deg"].to_numpy(float))),
        "vg": float(np.median(frame["vgeo_km_s"].to_numpy(float))),
    }


def spherical_sep_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    cosine = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def obs_delta(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    radiant = spherical_sep_deg(a["sun_lon"], a["ecl_lat"], b["sun_lon"], b["ecl_lat"])
    solar = abs(float(circ_diff(a["sol"], b["sol"])))
    dv = abs(a["vg"] - b["vg"])
    scaled = math.sqrt((solar / 7.0) ** 2 + (radiant / 6.0) ** 2 + (dv / 5.0) ** 2)
    return {"solar_deg": solar, "radiant_deg": radiant, "speed_km_s": dv, "scaled": scaled}


def normalize_iau_number(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip().upper()
    if text.endswith(".0"):
        text = text[:-2]
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    try:
        return int(match.group())
    except ValueError:
        return None


def read_month(key: str) -> pd.DataFrame:
    print(f"Downloading GMN {key}", flush=True)
    frame = reader.read_data(dd.get_monthly_file_content_by_date(key), output_camel_case=True).reset_index(drop=False)
    missing = [c for c in [ID_COLUMN, "iau_code", *OBS_COLUMNS, *ORBIT_COLUMNS] if c not in frame.columns]
    if missing:
        raise RuntimeError(f"GMN {key} missing columns {missing}; available={list(frame.columns)}")
    for column in [*OBS_COLUMNS, *ORBIT_COLUMNS, *QUALITY_COLUMNS]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame[ID_COLUMN] = frame[ID_COLUMN].astype(str)
    return frame


def quality_mask(frame: pd.DataFrame) -> np.ndarray:
    valid = np.isfinite(frame[OBS_COLUMNS].to_numpy(float)).all(axis=1)
    if "num_stat" in frame.columns:
        valid &= frame["num_stat"].fillna(0).to_numpy(float) >= 2.0
    if "medianfiterr_arcsec" in frame.columns:
        valid &= frame["medianfiterr_arcsec"].fillna(9999).to_numpy(float) <= 180.0
    return valid


def flatten_mdc(document: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for shower in document.get("data", []):
        for solution in shower.get("solution", []) or []:
            orbit_values = [finite(solution.get(k)) for k in ["e", "q", "inc", "peri", "node"]]
            if any(v is None for v in orbit_values):
                continue
            output.append({
                "iau_no": str(shower.get("IAUNo") or "").strip(),
                "code": str(shower.get("Code") or "").strip(),
                "name": str(shower.get("Name") or shower.get("ProvName") or "").strip(),
                "adno": str(solution.get("AdNo") or "").strip(),
                "status": str(solution.get("s") if solution.get("s") is not None else shower.get("s") or "").strip(),
                "activity": str(solution.get("activity") or "").strip(),
                "LoSb": finite(solution.get("LoSb")),
                "LoSe": finite(solution.get("LoSe")),
                "LoS": finite(solution.get("LoS")),
                "S_LoR": finite(solution.get("S_LoR")),
                "LaR": finite(solution.get("LaR")),
                "Vg": finite(solution.get("Vg")),
                "orbit": [float(v) for v in orbit_values],
                "N": finite(solution.get("N")),
            })
    return output


def mdc_orbit_matches(medoid: np.ndarray, solutions: list[dict[str, Any]], limit: int = 15) -> list[dict[str, Any]]:
    mdc_orbits = np.asarray([s["orbit"] for s in solutions], dtype=float)
    distances = d_sh_matrix(medoid[None, :], mdc_orbits)[0]
    order = np.argsort(distances)[:limit]
    result = []
    for idx in order:
        item = dict(solutions[int(idx)])
        item["d_sh"] = float(distances[int(idx)])
        result.append(item)
    return result


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float:
    # Treat implausibly broad/reversed intervals conservatively as a mean-LoS comparison.
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


def observational_mdc_matches(center: dict[str, float], solutions: list[dict[str, Any]], limit: int = 15) -> list[dict[str, Any]]:
    candidates = []
    for s in solutions:
        if None in {s["LoS"], s["S_LoR"], s["LaR"], s["Vg"]}:
            continue
        timing = interval_distance(center["sol"], s["LoSb"], s["LoSe"], s["LoS"])
        radiant = spherical_sep_deg(center["sun_lon"], center["ecl_lat"], float(s["S_LoR"]), float(s["LaR"]))
        dv = abs(center["vg"] - float(s["Vg"]))
        score = math.sqrt((timing / 15.0) ** 2 + (radiant / 10.0) ** 2 + (dv / 8.0) ** 2)
        item = dict(s)
        item.update({"obs_score": score, "timing_delta_deg": timing, "radiant_sep_deg": radiant, "speed_delta_km_s": dv})
        candidates.append(item)
    candidates.sort(key=lambda x: x["obs_score"])
    return candidates[:limit]


def label_counts(frame: pd.DataFrame) -> dict[str, int]:
    count = Counter()
    for value in frame["iau_code"].tolist():
        number = normalize_iau_number(value)
        count["SPORADIC" if number in {None, -1, 0} else str(number)] += 1
    return dict(count.most_common())


def candidate_adjudication(rank: int, scan: dict[str, Any], all_months: dict[str, pd.DataFrame], solutions: list[dict[str, Any]]) -> dict[str, Any]:
    family_id = scan["rankings"]["locked_rrf"][rank - 1]
    family = next(f for f in scan["families"] if f["family_id"] == family_id)
    event_ids = set(map(str, family["event_ids"]))
    month_keys = sorted({f"{event_id[:4]}-{event_id[4:6]}" for event_id in event_ids})
    candidate_parts = []
    month_diagnostics = {}
    for key in month_keys:
        frame = all_months[key]
        part = frame[frame[ID_COLUMN].isin(event_ids)].copy()
        candidate_parts.append(part)
        month_diagnostics[key] = {"rows": int(len(frame)), "matched_candidate_ids": int(len(part))}
    candidate = pd.concat(candidate_parts, ignore_index=True)
    found_ids = set(candidate[ID_COLUMN].astype(str))
    missing_ids = sorted(event_ids - found_ids)
    if missing_ids:
        raise RuntimeError(f"rank {rank} missing exact candidate IDs: {missing_ids}")
    candidate = candidate.loc[quality_mask(candidate)].reset_index(drop=True)
    orbit_candidate = candidate.loc[valid_orbit_mask(candidate)].reset_index(drop=True)
    if len(orbit_candidate) < max(8, int(0.8 * len(candidate))):
        raise RuntimeError(f"rank {rank} insufficient valid candidate orbits {len(orbit_candidate)}/{len(candidate)}")

    center = obs_center(candidate)
    candidate_orbits = orbit_candidate[ORBIT_COLUMNS].to_numpy(float)
    medoid, internal = orbit_medoid(candidate_orbits)
    orbit_matches = mdc_orbit_matches(medoid, solutions)
    obs_matches = observational_mdc_matches(center, solutions)

    # Relevant known shower is the best observational current-MDC match. Use all of
    # that shower's complete solutions for orbit comparison, not just one solution.
    relevant = obs_matches[0]
    relevant_no = normalize_iau_number(relevant["iau_no"])
    relevant_code = relevant["code"]
    relevant_solutions = [s for s in solutions if (relevant_no is not None and normalize_iau_number(s["iau_no"]) == relevant_no) or (relevant_code and s["code"] == relevant_code)]
    rel_orbits = np.asarray([s["orbit"] for s in relevant_solutions], dtype=float)
    rel_d = d_sh_matrix(medoid[None, :], rel_orbits)[0] if len(rel_orbits) else np.asarray([])
    relevant_solution_distances = []
    for s, d in sorted(zip(relevant_solutions, rel_d), key=lambda pair: pair[1]):
        item = dict(s)
        item["d_sh"] = float(d)
        relevant_solution_distances.append(item)

    # Local empirical GMN neighborhood around the candidate center. This includes
    # labelled and sporadic rows, but the known-shower empirical comparison below
    # uses only rows carrying the relevant IAU numerical label.
    local_parts = []
    for key in month_keys:
        frame = all_months[key]
        mask = quality_mask(frame)
        sol = frame["sol_lon_deg"].to_numpy(float)
        sun_lon = circ_diff(frame["lamgeo_deg"].to_numpy(float), sol)
        mask &= np.abs(circ_diff(sol, center["sol"])) <= 15.0
        mask &= np.abs(circ_diff(sun_lon, center["sun_lon"])) <= 15.0
        mask &= np.abs(frame["betgeo_deg"].to_numpy(float) - center["ecl_lat"]) <= 15.0
        mask &= np.abs(frame["vgeo_km_s"].to_numpy(float) - center["vg"]) <= 8.0
        local_parts.append(frame.loc[mask].copy())
    local = pd.concat(local_parts, ignore_index=True)
    local_labels = label_counts(local)

    known_mask = np.asarray([normalize_iau_number(v) == relevant_no for v in local["iau_code"].tolist()], dtype=bool) if relevant_no is not None else np.zeros(len(local), dtype=bool)
    empirical_known = local.loc[known_mask].copy()
    empirical: dict[str, Any] = {
        "iau_no": relevant_no,
        "code": relevant_code,
        "local_labeled_count": int(len(empirical_known)),
        "local_label_counts": local_labels,
    }
    if len(empirical_known) >= 4:
        empirical_center = obs_center(empirical_known)
        empirical["center"] = empirical_center
        empirical["candidate_to_empirical_center"] = obs_delta(center, empirical_center)
        empirical_orbit_rows = empirical_known.loc[valid_orbit_mask(empirical_known)].reset_index(drop=True)
        empirical["valid_orbit_count"] = int(len(empirical_orbit_rows))
        if len(empirical_orbit_rows) >= 4:
            empirical_orbits = empirical_orbit_rows[ORBIT_COLUMNS].to_numpy(float)
            empirical_medoid, empirical_internal = orbit_medoid(empirical_orbits)
            candidate_to_empirical_medoid = float(d_sh_matrix(medoid[None, :], empirical_medoid[None, :])[0, 0])
            candidate_events_to_empirical = d_sh_matrix(candidate_orbits, empirical_medoid[None, :])[:, 0]
            empirical_events_to_candidate = d_sh_matrix(empirical_orbits, medoid[None, :])[:, 0]
            empirical.update({
                "orbit_medoid": empirical_medoid.tolist(),
                "orbit_internal": empirical_internal,
                "candidate_medoid_to_empirical_medoid_d_sh": candidate_to_empirical_medoid,
                "candidate_events_to_empirical_medoid_d_sh": {
                    "median": float(np.median(candidate_events_to_empirical)),
                    "q10": float(np.quantile(candidate_events_to_empirical, 0.10)),
                    "q90": float(np.quantile(candidate_events_to_empirical, 0.90)),
                    "fraction_le_0_15": float(np.mean(candidate_events_to_empirical <= 0.15)),
                },
                "empirical_events_to_candidate_medoid_d_sh": {
                    "median": float(np.median(empirical_events_to_candidate)),
                    "q10": float(np.quantile(empirical_events_to_candidate, 0.10)),
                    "q90": float(np.quantile(empirical_events_to_candidate, 0.90)),
                    "fraction_le_0_15": float(np.mean(empirical_events_to_candidate <= 0.15)),
                },
            })

    # Also explicitly report Andromedids for rank 96, because the preliminary
    # current-MDC screen identified 18/AND as its closest plausible association.
    explicit: dict[str, Any] = {}
    for iau_no, code in ([(18, "AND")] if rank == 96 else [(709, "LCM"), (308, "PIP")] if rank == 294 else []):
        group = [s for s in solutions if normalize_iau_number(s["iau_no"]) == iau_no or s["code"] == code]
        if not group:
            continue
        d = d_sh_matrix(medoid[None, :], np.asarray([s["orbit"] for s in group], dtype=float))[0]
        records = []
        for s, value in sorted(zip(group, d), key=lambda pair: pair[1]):
            item = dict(s); item["d_sh"] = float(value); records.append(item)
        explicit[f"{iau_no}_{code}"] = records

    return {
        "rank": rank,
        "family_id": family_id,
        "family_years": family["years"],
        "family_event_count": family["event_count"],
        "resolved_quality_event_count": int(len(candidate)),
        "valid_orbit_count": int(len(orbit_candidate)),
        "month_diagnostics": month_diagnostics,
        "observational_center": center,
        "orbit_medoid": medoid.tolist(),
        "orbit_internal_coherence": internal,
        "nearest_mdc_by_d_sh": orbit_matches,
        "nearest_mdc_by_observables": obs_matches,
        "relevant_known_shower": {
            "iau_no": relevant_no,
            "code": relevant_code,
            "name": relevant["name"],
            "best_observational_match": relevant,
            "all_complete_solution_d_sh": relevant_solution_distances,
        },
        "empirical_gmn_comparison": empirical,
        "explicit_comparisons": explicit,
    }


def render(result: dict[str, Any]) -> str:
    lines = [
        "# OrbitTrace orbit-level discovery-lead adjudication",
        "",
        f"MDC snapshot: **{result['mdc_version']}**. Locked-RRF scan artifact SHA-256: `{result['scan_zip_sha256']}`.",
        "",
        "Candidate identities and ranks are frozen from the earlier target-free locked-RRF scan. This step only adjudicates known-shower association.",
        "",
    ]
    for c in result["candidates"]:
        lines += [
            f"## Rank {c['rank']} `{c['family_id']}`",
            "",
            f"Years {c['family_years']}; {c['family_event_count']} frozen family events; {c['valid_orbit_count']} valid resolved orbits.",
            "",
            f"Observed center: λ☉ {c['observational_center']['sol']:.2f}°, SLoR {c['observational_center']['sun_lon']:.2f}°, β {c['observational_center']['ecl_lat']:.2f}°, Vg {c['observational_center']['vg']:.2f} km/s.",
            "",
            f"Internal D_SH: median-to-medoid {c['orbit_internal_coherence']['median_to_medoid']:.3f}, q90 {c['orbit_internal_coherence']['q90_to_medoid']:.3f}, pairwise median {c['orbit_internal_coherence']['pairwise_median']:.3f}.",
            "",
            "### Nearest complete MDC mean orbits",
            "",
            "| D_SH | IAU | code | solution | status | name |",
            "|---:|---:|---|---:|---:|---|",
        ]
        for m in c["nearest_mdc_by_d_sh"][:10]:
            lines.append(f"| {m['d_sh']:.3f} | {m['iau_no']} | {m['code']} | {m['adno']} | {m['status']} | {m['name']} |")
        lines += ["", "### Empirical GMN comparison", ""]
        e = c["empirical_gmn_comparison"]
        lines.append(f"Closest observational MDC shower: {e.get('iau_no')}/{e.get('code')}. Nearby GMN rows carrying that label: {e.get('local_labeled_count', 0)}.")
        if "candidate_to_empirical_center" in e:
            d = e["candidate_to_empirical_center"]
            lines.append(f"Candidate vs empirical labeled-shower center: radiant {d['radiant_deg']:.2f}°, ΔVg {d['speed_km_s']:.2f} km/s, Δλ☉ {d['solar_deg']:.2f}°.")
        if "candidate_medoid_to_empirical_medoid_d_sh" in e:
            lines.append(f"Candidate medoid vs empirical labeled-shower medoid: D_SH {e['candidate_medoid_to_empirical_medoid_d_sh']:.3f}.")
            x = e["candidate_events_to_empirical_medoid_d_sh"]
            lines.append(f"Candidate events to empirical medoid: median D_SH {x['median']:.3f}, q10 {x['q10']:.3f}, q90 {x['q90']:.3f}, fraction ≤0.15 {x['fraction_le_0_15']:.3f}.")
        if c["explicit_comparisons"]:
            lines += ["", "### Explicit suspected-shower orbit comparisons", ""]
            for key, rows in c["explicit_comparisons"].items():
                best = rows[0]
                lines.append(f"- {key}: best complete MDC solution {best['adno']} has D_SH **{best['d_sh']:.3f}**.")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    parser.add_argument("--mdc", required=True)
    parser.add_argument("--ranks", nargs="+", type=int, default=[96, 294])
    parser.add_argument("--scan-zip-sha256", default="unknown")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    path = Path(args.scan)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(Path(args.mdc).read_text(encoding="utf-8"))
    solutions = flatten_mdc(mdc)
    if len(solutions) < 1000:
        raise RuntimeError(f"too few complete MDC solutions: {len(solutions)}")

    months = set()
    for rank in args.ranks:
        family_id = scan["rankings"]["locked_rrf"][rank - 1]
        family = next(f for f in scan["families"] if f["family_id"] == family_id)
        months.update(f"{event_id[:4]}-{event_id[4:6]}" for event_id in family["event_ids"])
    all_months = {key: read_month(key) for key in sorted(months)}

    candidates = [candidate_adjudication(rank, scan, all_months, solutions) for rank in args.ranks]
    result = {
        "version": "2026-08-28-v1",
        "mdc_version": str(mdc.get("version") or "unknown"),
        "complete_mdc_solution_count": len(solutions),
        "scan_zip_sha256": args.scan_zip_sha256,
        "ranks": args.ranks,
        "candidates": candidates,
    }
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "ORBIT_ADJUDICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = render(result)
    (out / "ORBIT_ADJUDICATION.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
