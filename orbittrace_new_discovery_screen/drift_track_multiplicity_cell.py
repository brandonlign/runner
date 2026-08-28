#!/usr/bin/env python3
"""Exact per-month multiplicity reconstruction for the frozen 2026 drift search."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import requests

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as drift
from orbittrace_new_discovery_screen import drift_track_2026_discovery as disc

VARIANT = "A_EOM_5_3"


def exact_local(track, discovery, validation, candidate_validation):
    seeds = disc.local_seed_pool(track, discovery)
    if len(seeds) == 0:
        return {"status": "LOCAL_NULL_INSUFFICIENT", "pseudo_track_count": 0, "original_gate_pass": False}
    data = discovery["data"]
    sol_u = discovery["sol_unwrapped"]
    pred_slon, pred_beta, pred_vg = disc.track_predictions(track, sol_u)
    rc = min(int(candidate_validation["2025"]["members"]), int(candidate_validation["2024"]["members"]))
    tc = int(candidate_validation["2025"]["members"]) + int(candidate_validation["2024"]["members"])
    r = np.zeros(len(seeds), dtype=np.int64)
    t = np.zeros(len(seeds), dtype=np.int64)
    for j, seed_index in enumerate(seeds):
        seed_sol_u = float(sol_u[seed_index])
        slon_offset = float(base.circ_diff(discovery["slon"][seed_index], pred_slon[seed_index]))
        beta_offset = float(discovery["beta"][seed_index] - pred_beta[seed_index])
        vg_offset = float(discovery["vg"][seed_index] - pred_vg[seed_index])
        time_shift = seed_sol_u - float(track["reference_sol_unwrapped"])
        seed_orbit = data.iloc[int(seed_index)][base.ORBIT_COLUMNS].to_numpy(dtype=float)
        counts = []
        for year in disc.VALIDATION_YEARS:
            selected, _ = disc.fixed_track_membership(
                track,
                validation[year],
                float(discovery["sol_reference"]),
                seed_orbit,
                interval_center_shift=time_shift,
                intercept_offsets=(slon_offset, beta_offset, vg_offset),
            )
            counts.append(int(selected.sum()))
        r[j] = min(counts)
        t[j] = sum(counts)
    q99_r = int(np.quantile(r, 0.99, method="higher"))
    tied = t[r == q99_r]
    q99_t = int(np.quantile(tied, 0.99, method="higher")) if len(tied) else 0
    gate_mask = (r > q99_r) | ((r == q99_r) & (t > q99_t))
    candidate_gate = bool(rc > q99_r or (rc == q99_r and tc > q99_t))
    at_least_candidate = (r > rc) | ((r == rc) & (t >= tc))
    empirical_p = float((1 + int(at_least_candidate.sum())) / (1 + len(r)))
    return {
        "status": "EXECUTED",
        "pseudo_track_count": int(len(r)),
        "candidate_R": int(rc),
        "candidate_T": int(tc),
        "q99_R": int(q99_r),
        "q99_T": int(q99_t),
        "original_gate_pass": candidate_gate,
        "pseudo_original_gate_pass_count": int(gate_mask.sum()),
        "pseudo_original_gate_pass_fraction": float(gate_mask.mean()),
        "pseudo_at_least_candidate_count": int(at_least_candidate.sum()),
        "empirical_candidate_p": empirical_p,
        "null_R_max": int(r.max()),
        "null_T_max": int(t.max()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    month = int(args.month)
    if month not in range(1, 8):
        raise SystemExit("month must be 1..7")
    args.out.mkdir(parents=True, exist_ok=True)

    response = requests.get(base.MDC_URL, timeout=90)
    response.raise_for_status()
    mdc = response.json()
    catalog, current_codes = base.flatten_mdc(mdc)
    discovery = disc.prepare_residual(disc.DISCOVERY_YEAR, month, current_codes)
    tracks, _diag = drift.tracks_for_variant(discovery, VARIANT)
    validation_cache = None
    tests = []
    physical_n = both_n = clone_n = 0
    for index, track in enumerate(tracks):
        physical = disc.physical_adjudication(track, discovery, catalog)
        if not physical["pass"]:
            continue
        physical_n += 1
        if validation_cache is None:
            validation_cache = {year: disc.prepare_residual(year, month, current_codes) for year in disc.VALIDATION_YEARS}
        validation = {
            str(year): disc.validate_track(track, validation_cache[year], float(discovery["sol_reference"]))
            for year in disc.VALIDATION_YEARS
        }
        if not all(v["passed"] for v in validation.values()):
            continue
        both_n += 1
        frame = disc.candidate_frame(track, discovery)
        clones = disc.clone_stability(track, frame, month, index)
        if not clones["passed"]:
            continue
        clone_n += 1
        lead_id = disc.stable_id(track["event_ids"])
        local = exact_local(track, discovery, validation_cache, validation)
        tests.append({"lead_id": lead_id, "track_index": int(index), "local": local})
        print(month, lead_id, local, flush=True)

    result = {
        "stage": "drift_track_multiplicity_month_v1",
        "protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_MULTIPLICITY_AUDIT.md",
        "month": month,
        "variant": VARIANT,
        "tracks_generated": int(len(tracks)),
        "physical_survivors": int(physical_n),
        "both_year_survivors": int(both_n),
        "clone_survivors": int(clone_n),
        "local_tests": int(len(tests)),
        "tests": tests,
    }
    (args.out / f"multiplicity_month_{month:02d}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
