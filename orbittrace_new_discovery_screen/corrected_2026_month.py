#!/usr/bin/env python3
"""Compute one month of the raw CORRECTED_2026_TRANSFER_PROTOCOL.

All detector and adjudication functions are inherited from the already-frozen
corrected all-season compute mirror.  Only the temporal split changes:
2026 discovery, 2025+2024 untouched validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from orbittrace_new_discovery_screen import corrected_allseason_month as base

DISCOVERY_YEAR = 2026
VALIDATION_YEARS = (2025, 2024)


def local_pseudo_null(
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    validation: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    data, raw = discovery["data"], discovery["raw"]
    center = np.asarray(candidate["center"], dtype=float)
    candidate_ids = set(map(str, candidate["member_ids_2025"]))
    radiant = np.asarray(
        [
            base.spherical_sep(
                float(lon) % 360.0,
                float(beta),
                float(center[0]) % 360.0,
                float(center[1]),
            )
            for lon, beta in zip(raw[:, 0], raw[:, 1])
        ],
        dtype=float,
    )
    mask = (
        base.valid_orbits(data)
        & (np.abs(base.circ_diff(data["sol_lon_deg"].to_numpy(float), center[3])) <= 20.0)
        & (radiant <= 25.0)
        & (np.abs(data["vgeo_km_s"].to_numpy(float) - center[2]) <= 10.0)
        & (~data["unique_trajectory_identifier"].astype(str).isin(candidate_ids).to_numpy())
    )
    seeds = data.loc[mask].reset_index(drop=True)
    seed_sol = seeds["sol_lon_deg"].to_numpy(float)
    seed_slon = base.circ_diff(seeds["lamgeo_deg"].to_numpy(float), seed_sol)
    centers = np.column_stack(
        [
            seed_slon,
            seeds["betgeo_deg"].to_numpy(float),
            seeds["vgeo_km_s"].to_numpy(float),
            seed_sol,
        ]
    )
    orbits = seeds[base.ORBIT_COLUMNS].to_numpy(float)
    seed_ids = seeds["unique_trajectory_identifier"].astype(str).tolist()
    sigma = np.asarray(candidate["sigma_raw"], dtype=float)
    first = np.zeros(len(seeds), dtype=np.int64)
    second = np.zeros(len(seeds), dtype=np.int64)
    for index, (seed_center, orbit) in enumerate(zip(centers, orbits)):
        first[index] = base.template_count(seed_center, orbit, sigma, validation[2025])
        second[index] = base.template_count(seed_center, orbit, sigma, validation[2024])
    recurrence = np.minimum(first, second)
    totals = first + second
    candidate_r = min(
        int(candidate["validation"]["2025"]["members"]),
        int(candidate["validation"]["2024"]["members"]),
    )
    candidate_t = (
        int(candidate["validation"]["2025"]["members"])
        + int(candidate["validation"]["2024"]["members"])
    )
    q99_r = int(np.quantile(recurrence, 0.99, method="higher")) if len(recurrence) else 0
    tied = totals[recurrence == q99_r]
    q99_t = int(np.quantile(tied, 0.99, method="higher")) if len(tied) else 0
    passed = candidate_r > q99_r or (candidate_r == q99_r and candidate_t > q99_t)
    order = sorted(
        range(len(seeds)),
        key=lambda idx: (-int(recurrence[idx]), -int(totals[idx]), seed_ids[idx]),
    )[:20]
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
                "n2025": int(first[idx]),
                "n2024": int(second[idx]),
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
    if not 1 <= month <= 7:
        raise SystemExit("2026 transfer protocol freezes months 1..7 only")
    args.out.mkdir(parents=True, exist_ok=True)

    response = requests.get(base.MDC_URL, timeout=90)
    response.raise_for_status()
    mdc = response.json()
    catalog, current_codes = base.flatten_mdc(mdc)
    if len(catalog) < 1800:
        raise RuntimeError(f"unexpectedly small MDC solution set: {len(catalog)}")

    discovery = base.prepare(base.load_month(DISCOVERY_YEAR, month), DISCOVERY_YEAR, month, current_codes)
    candidates = base.scan_discovery(discovery, month, catalog)
    validation_cache = (
        {
            year: base.prepare(base.load_month(year, month), year, month, current_codes)
            for year in VALIDATION_YEARS
        }
        if candidates
        else {}
    )

    final: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, 1):
        print(
            f"Validating 2026 candidate {index}/{len(candidates)} "
            f"cluster={candidate['cluster']} N={candidate['members_2025']}",
            flush=True,
        )
        candidate["validation"] = {
            str(year): base.validate(candidate, year, validation_cache[year])
            for year in VALIDATION_YEARS
        }
        both = all(item["passed"] for item in candidate["validation"].values())
        candidate["clone_stability"] = (
            base.clone_stability(candidate) if both else {"passed": False, "not_run": True}
        )
        pre_local = bool(both and candidate["clone_stability"]["passed"])
        candidate["pre_local_null_survivor"] = pre_local
        candidate["local_pseudo_template_null"] = (
            local_pseudo_null(candidate, discovery, validation_cache)
            if pre_local
            else {"not_run": True, "pass": False}
        )
        candidate["corrected_2026_lead"] = bool(
            pre_local and candidate["local_pseudo_template_null"]["pass"]
        )
        if candidate["corrected_2026_lead"]:
            final.append(candidate)

    result = {
        "stage": "corrected_2026_transfer_discovery_month_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/CORRECTED_2026_TRANSFER_PROTOCOL.md",
        "month": month,
        "discovery_year": DISCOVERY_YEAR,
        "validation_years": list(VALIDATION_YEARS),
        "mdc_version": mdc.get("version"),
        "mdc_shower_count": mdc.get("count"),
        "mdc_solution_rows_including_incomplete_orbits": len(catalog),
        "quality_residuals_2026": int(len(discovery["data"])),
        "discovery_catalog_survivors": int(len(candidates)),
        "pre_local_null_survivors": int(sum(c["pre_local_null_survivor"] for c in candidates)),
        "final_leads": int(len(final)),
        "verdict": "DISCOVERY_LEAD" if final else "NO_DISCOVERY_LEAD",
        "candidates": [serializable(candidate) for candidate in candidates],
    }
    json_path = args.out / f"corrected_2026_month_{month:02d}.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        f"# Corrected 2026 transfer month {month:02d}",
        "",
        f"MDC **{mdc.get('version')}**. 2026 residual rows: **{len(discovery['data'])}**.",
        f"Discovery/catalog survivors: **{len(candidates)}**. Final leads: **{len(final)}**.",
        "",
        "| cluster | N2026 | solar | SLoR | beta | Vg | Dmed | source | nearest MDC | N25/p25 | N24/p24 | local | final |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for candidate in candidates:
        center = candidate["center"]
        best = candidate["nearest_mdc"].get("best", {})
        source = candidate["sporadic_source"]["nearest"]
        v25 = candidate["validation"]["2025"]
        v24 = candidate["validation"]["2024"]
        lines.append(
            f"| {candidate['cluster']} | {candidate['members_2025']} | {center[3]:.2f} | {center[0]:.2f} | "
            f"{center[1]:.2f} | {center[2]:.2f} | {candidate['orbit_median_d']:.3f} | "
            f"{source['source']} ({source['separation_deg']:.1f}) | {best.get('iau_no','')}/{best.get('code','')} | "
            f"{v25['members']}/{v25['p']:.3f} | {v24['members']}/{v24['p']:.3f} | "
            f"{candidate['local_pseudo_template_null'].get('pass', False)} | {candidate['corrected_2026_lead']} |"
        )
    md_path = args.out / f"CORRECTED_2026_MONTH_{month:02d}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
