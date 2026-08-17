#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase_neutral_geometry import phase_neutral_geo_matrix


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    base = [
        {"id":"a","year":2022,"sol":10.0,"lon":123.0,"lat":5.0,"vg":31.0},
        {"id":"b","year":2023,"sol":100.0,"lon":245.0,"lat":-12.0,"vg":47.0},
        {"id":"c","year":2022,"sol":300.0,"lon":1.0,"lat":40.0,"vg":22.0},
    ]
    X = phase_neutral_geo_matrix(base)
    req(X.shape == (3,4), "wrong GEO4 shape")
    req(np.isfinite(X).all(), "nonfinite GEO4")

    phase_changed = [dict(x) for x in base]
    phase_changed[0]["sol"] = 200.0
    phase_changed[1]["sol"] = 250.0
    phase_changed[2]["sol"] = 60.0
    Xp = phase_neutral_geo_matrix(phase_changed)
    phase_invariant = bool(np.array_equal(X, Xp))
    req(phase_invariant, "solar longitude changed GEO4 representation")

    year_changed = [dict(x) for x in base]
    year_changed[0]["year"] = 2023
    year_changed[1]["year"] = 2022
    Xy = phase_neutral_geo_matrix(year_changed)
    year_invariant = bool(np.array_equal(X, Xy))
    req(year_invariant, "year identity entered GEO4 representation")

    radiant_changed = [dict(x) for x in base]
    radiant_changed[0]["lon"] += 2.0
    Xr = phase_neutral_geo_matrix(radiant_changed)
    radiant_sensitive = bool(not np.array_equal(X, Xr))
    req(radiant_sensitive, "radiant longitude failed to change GEO4")

    speed_changed = [dict(x) for x in base]
    speed_changed[0]["vg"] += 1.0
    Xv = phase_neutral_geo_matrix(speed_changed)
    speed_sensitive = bool(not np.array_equal(X, Xv))
    req(speed_sensitive, "speed failed to change GEO4")

    perm = [2,0,1]
    Xperm = phase_neutral_geo_matrix([base[i] for i in perm])
    permutation_equivariant = bool(np.array_equal(Xperm, X[perm]))
    req(permutation_equivariant, "GEO4 not permutation equivariant")

    protected_rejected = False
    try:
        bad = [dict(base[0])]
        bad[0]["sol"] = 30.0
        phase_neutral_geo_matrix(bad)
    except ValueError:
        protected_rejected = True
    req(protected_rejected, "protected-window row was accepted")

    nonfinite_rejected = False
    try:
        bad = [dict(base[0])]
        bad[0]["vg"] = float("nan")
        phase_neutral_geo_matrix(bad)
    except ValueError:
        nonfinite_rejected = True
    req(nonfinite_rejected, "nonfinite row was accepted")

    result = {
        "verdict":"PASS_PHASE_NEUTRAL_GEO4_SYNTHETIC_AUDIT",
        "tests":{
            "shape_3x4": True,
            "finite": True,
            "solar_phase_invariant": phase_invariant,
            "year_invariant": year_invariant,
            "radiant_sensitive": radiant_sensitive,
            "speed_sensitive": speed_sensitive,
            "permutation_equivariant": permutation_equivariant,
            "protected_window_rejected": protected_rejected,
            "nonfinite_rejected": nonfinite_rejected,
        },
        "gmn_access":False,
        "truth_access":False,
        "sonotaco_access":False,
        "target_information_access":False,
        "target_region_events_accessed":False,
        "amos_access":False,
        "maarsy_scientific_access":False,
        "dms_scientific_access":False,
    }
    path=a.output/"PHASE_NEUTRAL_GEO4_SYNTHETIC_AUDIT.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
