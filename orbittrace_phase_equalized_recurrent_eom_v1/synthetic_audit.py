#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from orbittrace_phase_equalized_recurrent_eom_v1.phase_equalization import (
    ARC_LENGTH,
    ARC_ORIGIN,
    BLIND_HIGH,
    BLIND_LOW,
    equalize_phase,
    equalized_events,
)

PASS = "PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_SYNTHETIC_AUDIT"
FAIL = "FAIL_PHASE_EQUALIZED_RECURRENT_EOM_V1_SYNTHETIC_AUDIT"


def event(eid: str, sol: float, year: int = 2022, lon: float = 10.0, lat: float = 2.0, vg: float = 30.0):
    return {"id": eid, "sol": sol, "year": year, "lon": lon, "lat": lat, "vg": vg}


def sha_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(a, dtype="<f8").tobytes()).hexdigest()


def raises(fn) -> bool:
    try:
        fn()
    except RuntimeError:
        return True
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    fixture = [
        event("a", 60.0),
        event("b", 60.0, year=2023, lon=200.0, lat=-20.0, vg=55.0),
        event("c", 100.0),
        event("d", 200.0),
        event("e", 350.0),
        event("f", 10.0),
    ]
    r = equalize_phase(fixture)

    # Exact pooled empirical mid-distribution expectation on the accessible arc.
    # Unwrapped s values: 5,5,45,145,295,315. N=6.
    expected_u = np.array([2/12, 2/12, 5/12, 7/12, 9/12, 11/12], dtype=np.float64)
    expected_eq = np.mod(ARC_ORIGIN + ARC_LENGTH * expected_u, 360.0)

    perm = [4, 1, 5, 2, 0, 3]
    permuted = [fixture[i] for i in perm]
    rp = equalize_phase(permuted)
    by_id = {permuted[i]["id"]: float(rp.equalized_sol[i]) for i in range(len(permuted))}
    original_by_id = {fixture[i]["id"]: float(r.equalized_sol[i]) for i in range(len(fixture))}

    nuisance = [dict(x) for x in fixture]
    for i, row in enumerate(nuisance):
        row["year"] = 2023 if row["year"] == 2022 else 2022
        row["lon"] = row["lon"] + 71.0 + i
        row["lat"] = row["lat"] - 13.0 - i
        row["vg"] = row["vg"] + 4.5 + i
        row["id"] = "nuisance-" + row["id"]
    rn = equalize_phase(nuisance)

    transformed_events, _ = equalized_events(fixture)
    nonphase_preserved = all(
        transformed_events[i][k] == fixture[i][k]
        for i in range(len(fixture))
        for k in ("id", "year", "lon", "lat", "vg")
    )

    order = np.argsort(r.unwrapped_s, kind="mergesort")
    eq_unwrapped = np.mod(r.equalized_sol - ARC_ORIGIN, 360.0)
    monotone = bool(np.all(np.diff(eq_unwrapped[order]) >= 0.0))

    checks = {
        "constants_exact": BLIND_LOW == 20.0 and BLIND_HIGH == 55.0 and ARC_ORIGIN == 55.0 and ARC_LENGTH == 325.0,
        "expected_midrank_mapping_exact": bool(np.array_equal(r.equalized_sol, expected_eq)),
        "ties_identical": bool(r.equalized_sol[0] == r.equalized_sol[1]),
        "permutation_invariant_by_event": by_id == original_by_id,
        "nuisance_fields_do_not_change_warp": bool(np.array_equal(r.equalized_sol, rn.equalized_sol)),
        "protected_gap_preserved": bool(not np.any((r.equalized_sol >= BLIND_LOW) & (r.equalized_sol <= BLIND_HIGH))),
        "accessible_order_preserved": monotone,
        "nonphase_event_fields_preserved": nonphase_preserved,
        "phase_transform_nonidentity_on_fixture": bool(not np.array_equal(r.raw_sol, r.equalized_sol)),
        "blind_low_rejected": raises(lambda: equalize_phase([event("x", 20.0)])),
        "blind_high_rejected": raises(lambda: equalize_phase([event("x", 55.0)])),
        "blind_interior_rejected": raises(lambda: equalize_phase([event("x", 30.0)])),
        "nonfinite_rejected": raises(lambda: equalize_phase([event("x", float("nan"))])),
    }
    passed = all(checks.values())
    result = {
        "verdict": PASS if passed else FAIL,
        "checks": checks,
        "raw_sol_sha256": sha_array(r.raw_sol),
        "unwrapped_s_sha256": sha_array(r.unwrapped_s),
        "equalized_sol_sha256": sha_array(r.equalized_sol),
        "gmn_accessed": False,
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "asfn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "PHASE_EQUALIZED_RECURRENT_EOM_V1_SYNTHETIC_AUDIT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
