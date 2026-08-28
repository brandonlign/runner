#!/usr/bin/env python3
"""Orbit-level screen of every family in the frozen locked-RRF catalogue.

The catalogue and its ranking remain untouched. This stage resolves the exact
frozen family IDs back to GMN trajectories, computes canonical Southworth-
Hawkins D_SH coherence, and cross-checks each family against the current IAU
MDC in both orbital and observed radiant/time/speed space.

This is a triage screen. A survivor is not a discovery until local-background,
selection-aware, and independent-data tests are completed.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader

from orbittrace_new_discovery_screen import adjudicate_orbits as base
from orbittrace_new_discovery_screen.adjudicate_orbits_v2 import canonical_d_sh_matrix


def read_month(key: str, wanted_ids: set[str]) -> pd.DataFrame:
    print(f"GMN {key}: downloading", flush=True)
    frame = reader.read_data(dd.get_monthly_file_content_by_date(key), output_camel_case=True).reset_index(drop=False)
    if base.ID_COLUMN not in frame.columns:
        raise RuntimeError(f"{key} missing {base.ID_COLUMN}")
    frame[base.ID_COLUMN] = frame[base.ID_COLUMN].astype(str)
    part = frame[frame[base.ID_COLUMN].isin(wanted_ids)].copy()
    for column in [*base.OBS_COLUMNS, *base.ORBIT_COLUMNS, *base.QUALITY_COLUMNS]:
        if column in part.columns:
            part[column] = pd.to_numeric(part[column], errors="coerce")
    print(f"GMN {key}: selected {len(part):,}/{len(wanted_ids):,} requested family rows", flush=True)
    return part


def circ_mean(values: np.ndarray) -> float:
    r = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(r).mean(), np.cos(r).mean())) % 360.0)


def obs_center(frame: pd.DataFrame) -> dict[str, float]:
    sol = frame["sol_lon_deg"].to_numpy(float)
    slon = base.circ_diff(frame["lamgeo_deg"].to_numpy(float), sol)
    return {
        "sol": circ_mean(sol),
        "sun_lon": circ_mean(slon),
        "ecl_lat": float(np.median(frame["betgeo_deg"].to_numpy(float))),
        "vg": float(np.median(frame["vgeo_km_s"].to_numpy(float))),
    }


def source_region(center: dict[str, float]) -> str | None:
    lon, beta, speed = center["sun_lon"], center["ecl_lat"], center["vg"]
    if abs(float(base.circ_diff(lon, 180.0))) <= 30.0 and abs(beta) <= 25.0 and speed < 40.0:
        return "ANTIHELION"
    if abs(float(base.circ_diff(lon, 0.0))) <= 30.0 and abs(beta) <= 25.0 and speed < 40.0:
        return "HELION"
    if abs(float(base.circ_diff(lon, 270.0))) <= 40.0 and abs(beta) <= 35.0 and speed >= 40.0:
        return "APEX"
    if abs(float(base.circ_diff(lon, 270.0))) <= 50.0 and abs(beta) > 30.0 and speed >= 35.0:
        return "TOROIDAL"
    return None


def spherical_sep_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    c = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float:
    if start is not None and end is not None:
        span = (end - start) % 360.0
        if span <= 120.0:
            offset = (value - start) % 360.0
            if offset <= span:
                return 0.0
            return min(abs(float(base.circ_diff(value, start))), abs(float(base.circ_diff(value, end))))
    if center is not None:
        return abs(float(base.circ_diff(value, center)))
    return 180.0


def obs_association(center: dict[str, float], solution: dict[str, Any]) -> dict[str, Any] | None:
    if None in {solution["LoS"], solution["S_LoR"], solution["LaR"], solution["Vg"]}:
        return None
    timing = interval_distance(center["sol"], solution["LoSb"], solution["LoSe"], solution["LoS"])
    radiant = spherical_sep_deg(center["sun_lon"], center["ecl_lat"], float(solution["S_LoR"]), float(solution["LaR"]))
    dv = abs(center["vg"] - float(solution["Vg"]))
    if timing <= 8.0 and radiant <= 6.0 and dv <= 5.0:
        tier = "STRONG"
    elif timing <= 15.0 and radiant <= 10.0 and dv <= 8.0:
        tier = "PLAUSIBLE"
    elif timing <= 25.0 and radiant <= 15.0 and dv <= 12.0:
        tier = "LOOSE"
    else:
        tier = "NONE"
    score = math.sqrt((timing / 15.0) ** 2 + (radiant / 10.0) ** 2 + (dv / 8.0) ** 2)
    return {
        "tier": tier,
        "score": score,
        "timing_delta_deg": timing,
        "radiant_sep_deg": radiant,
        "speed_delta_km_s": dv,
        "iau_no": solution["iau_no"],
        "code": solution["code"],
        "name": solution["name"],
        "adno": solution["adno"],
        "status": solution["status"],
        "activity": solution["activity"],
    }


def orbit_medoid(orbits: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    matrix = canonical_d_sh_matrix(orbits)
    medians = np.median(matrix, axis=1)
    index = int(np.argmin(medians))
    d = matrix[index]
    upper = matrix[np.triu_indices(len(matrix), 1)] if len(matrix) > 1 else np.asarray([0.0])
    return orbits[index], {
        "median_to_medoid": float(np.median(d)),
        "q90_to_medoid": float(np.quantile(d, 0.90)),
        "max_to_medoid": float(np.max(d)),
        "pairwise_median": float(np.median(upper)),
        "pairwise_q90": float(np.quantile(upper, 0.90)),
    }


def nearest_orbits(medoid: np.ndarray, solutions: list[dict[str, Any]], mdc_orbits: np.ndarray, k: int = 8) -> list[dict[str, Any]]:
    d = canonical_d_sh_matrix(medoid[None, :], mdc_orbits)[0]
    order = np.argsort(d)[:k]
    out = []
    for idx in order:
        s = solutions[int(idx)]
        out.append({
            "d_sh": float(d[int(idx)]),
            "iau_no": s["iau_no"],
            "code": s["code"],
            "name": s["name"],
            "adno": s["adno"],
            "status": s["status"],
            "activity": s["activity"],
        })
    return out


def nearest_observed(center: dict[str, float], solutions: list[dict[str, Any]], k: int = 8) -> list[dict[str, Any]]:
    matches = []
    for s in solutions:
        m = obs_association(center, s)
        if m is not None:
            matches.append(m)
    matches.sort(key=lambda x: (x["score"], x["radiant_sep_deg"], x["timing_delta_deg"]))
    return matches[:k]


def tier_value(value: str) -> int:
    return {"NONE": 0, "LOOSE": 1, "PLAUSIBLE": 2, "STRONG": 3}.get(value, 0)


def family_metric(family: dict[str, Any], rows: pd.DataFrame, solutions: list[dict[str, Any]], mdc_orbits: np.ndarray) -> dict[str, Any]:
    ids = set(map(str, family["event_ids"]))
    part = rows[rows[base.ID_COLUMN].astype(str).isin(ids)].copy().reset_index(drop=True)
    if len(part) != len(ids):
        found = set(part[base.ID_COLUMN].astype(str))
        missing = sorted(ids - found)
        raise RuntimeError(f"{family['family_id']} missing {len(missing)} IDs, examples={missing[:5]}")
    qmask = base.quality_mask(part)
    part = part.loc[qmask].reset_index(drop=True)
    orbit_mask = base.valid_orbit_mask(part)
    orbit_rows = part.loc[orbit_mask].reset_index(drop=True)
    if len(orbit_rows) < 4:
        return {
            "family_id": family["family_id"],
            "locked_rrf_rank": family["locked_rrf_rank"],
            "error": "fewer than 4 valid orbits",
        }

    center = obs_center(part)
    medoid, coherence = orbit_medoid(orbit_rows[base.ORBIT_COLUMNS].to_numpy(float))
    orbit_matches = nearest_orbits(medoid, solutions, mdc_orbits)
    obs_matches = nearest_observed(center, solutions)
    strongest_obs = max((tier_value(x["tier"]) for x in obs_matches), default=0)
    best_obs_tier = next((name for name, value in [("STRONG", 3), ("PLAUSIBLE", 2), ("LOOSE", 1), ("NONE", 0)] if strongest_obs == value), "NONE")

    # Candidate tiers are intentionally conservative. They only identify leads
    # worth deeper testing and are not formal novelty or shower-status claims.
    no_close_orbit = orbit_matches[0]["d_sh"] > 0.15
    no_broad_known_obs = strongest_obs < 2
    basic = family["year_count"] >= 3 and family["event_count"] >= 12
    coherent = coherence["median_to_medoid"] <= 0.15 and coherence["q90_to_medoid"] <= 0.25
    strong_coherent = coherence["median_to_medoid"] <= 0.10 and coherence["q90_to_medoid"] <= 0.18
    if basic and no_close_orbit and no_broad_known_obs and strong_coherent and family["year_count"] >= 4:
        lead_tier = "A"
    elif basic and no_close_orbit and no_broad_known_obs and coherent:
        lead_tier = "B"
    elif basic and no_close_orbit and no_broad_known_obs:
        lead_tier = "C"
    else:
        lead_tier = "NONE"

    return {
        "family_id": family["family_id"],
        "locked_rrf_rank": int(family["locked_rrf_rank"]),
        "year_count": int(family["year_count"]),
        "years": family["years"],
        "event_count": int(family["event_count"]),
        "valid_orbit_count": int(len(orbit_rows)),
        "ranking_scores": family["ranking_scores"],
        "ranks": family["ranks"],
        "observational_center": center,
        "sporadic_source_region": source_region(center),
        "orbit_medoid": medoid.tolist(),
        "orbit_coherence": coherence,
        "nearest_mdc_orbits": orbit_matches,
        "nearest_mdc_observed": obs_matches,
        "best_observed_association_tier": best_obs_tier,
        "lead_tier": lead_tier,
    }


def lead_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    tier = {"A": 0, "B": 1, "C": 2, "NONE": 3}.get(item.get("lead_tier", "NONE"), 3)
    source_penalty = 1 if item.get("sporadic_source_region") else 0
    orbit_gap = item.get("nearest_mdc_orbits", [{"d_sh": -1.0}])[0]["d_sh"]
    coh = item.get("orbit_coherence", {}).get("median_to_medoid", 999.0)
    return (tier, source_penalty, item.get("locked_rrf_rank", 99999), coh, -orbit_gap)


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Frozen locked-RRF catalogue orbit screen",
        "",
        f"Screened **{result['screened_family_count']}** frozen families against MDC **{result['mdc_version']}** using canonical D_SH.",
        "",
        "Lead tiers are triage only. Source-region membership is retained as a risk flag rather than used as an automatic veto.",
        "",
        "## Leads",
        "",
        "| tier | rank | family | yrs | n | source | internal D50 | internal D90 | nearest MDC orbit | D_SH | best obs tier |",
        "|---|---:|---|---:|---:|---|---:|---:|---|---:|---|",
    ]
    for x in result["leads"]:
        o = x["nearest_mdc_orbits"][0]
        lines.append(
            f"| {x['lead_tier']} | {x['locked_rrf_rank']} | `{x['family_id']}` | {x['year_count']} | {x['event_count']} | "
            f"{x['sporadic_source_region'] or ''} | {x['orbit_coherence']['median_to_medoid']:.3f} | {x['orbit_coherence']['q90_to_medoid']:.3f} | "
            f"{o['iau_no']}/{o['code']} | {o['d_sh']:.3f} | {x['best_observed_association_tier']} |"
        )
    lines += ["", "## Controls", ""]
    for rank in [46, 96]:
        c = next((x for x in result["families"] if x.get("locked_rrf_rank") == rank), None)
        if c and "nearest_mdc_orbits" in c:
            o = c["nearest_mdc_orbits"][0]
            b = c["nearest_mdc_observed"][0]
            lines.append(
                f"- Rank {rank} `{c['family_id']}`: nearest orbit {o['iau_no']}/{o['code']} D_SH={o['d_sh']:.3f}; "
                f"best observed match {b['iau_no']}/{b['code']} tier={b['tier']}."
            )
    lines += ["", "A lead must still pass empirical GMN-label review, same-source local-background/analogue tests, year-by-year drift/activity checks, and preferably an independent network before being described as a possible uncatalogued shower."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    parser.add_argument("--mdc", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scan-zip-sha256", default="unknown")
    args = parser.parse_args()

    scan_path = Path(args.scan)
    opener = gzip.open if scan_path.suffix == ".gz" else open
    with opener(scan_path, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(Path(args.mdc).read_text(encoding="utf-8"))
    solutions = base.flatten_mdc(mdc)
    mdc_orbits = np.asarray([s["orbit"] for s in solutions], dtype=float)

    wanted_by_month: dict[str, set[str]] = defaultdict(set)
    all_ids: set[str] = set()
    for family in scan["families"]:
        for event_id in map(str, family["event_ids"]):
            if event_id in all_ids:
                # Families should be disjoint after family linking. If not, keeping
                # one row in the global table is still fine, but record it later.
                pass
            all_ids.add(event_id)
            wanted_by_month[f"{event_id[:4]}-{event_id[4:6]}"].add(event_id)

    parts = [read_month(key, wanted) for key, wanted in sorted(wanted_by_month.items())]
    rows = pd.concat(parts, ignore_index=True)
    if rows[base.ID_COLUMN].astype(str).duplicated().any():
        duplicate_ids = rows.loc[rows[base.ID_COLUMN].astype(str).duplicated(), base.ID_COLUMN].astype(str).tolist()
        raise RuntimeError(f"duplicate resolved GMN IDs: {duplicate_ids[:10]}")
    resolved_ids = set(rows[base.ID_COLUMN].astype(str))
    missing = sorted(all_ids - resolved_ids)
    if missing:
        raise RuntimeError(f"failed to resolve {len(missing)} frozen IDs, examples={missing[:10]}")

    metrics = []
    for index, family in enumerate(scan["families"], start=1):
        if index % 50 == 0:
            print(f"families {index}/{len(scan['families'])}", flush=True)
        metrics.append(family_metric(family, rows, solutions, mdc_orbits))

    leads = [x for x in metrics if x.get("lead_tier") in {"A", "B", "C"}]
    leads.sort(key=lead_sort_key)
    tier_counts = Counter(x["lead_tier"] for x in leads)
    source_counts = Counter((x.get("sporadic_source_region") or "NONE") for x in leads)

    result = {
        "version": "2026-08-28-all-families-canonical-dsh-v1",
        "scan_zip_sha256": args.scan_zip_sha256,
        "mdc_version": str(mdc.get("version") or "unknown"),
        "complete_mdc_solution_count": len(solutions),
        "screened_family_count": len(metrics),
        "resolved_unique_event_count": len(resolved_ids),
        "lead_count": len(leads),
        "lead_tier_counts": dict(tier_counts),
        "lead_source_counts": dict(source_counts),
        "lead_definition": {
            "basic": ">=3 years and >=12 events",
            "known_orbit_veto": "nearest complete current MDC D_SH <= 0.15",
            "known_observed_veto": "STRONG or PLAUSIBLE broad timing/radiant/speed association",
            "A": ">=4 years, D50<=0.10, D90<=0.18",
            "B": "D50<=0.15, D90<=0.25",
            "C": "basic + no current MDC veto but weaker internal orbit coherence",
            "source_regions": "risk flag only, not veto",
        },
        "leads": leads,
        "families": metrics,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CATALOGUE_ORBIT_SCREEN.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = render(result)
    (out / "CATALOGUE_ORBIT_SCREEN.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
