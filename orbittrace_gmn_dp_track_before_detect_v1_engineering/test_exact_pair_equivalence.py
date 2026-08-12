#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "orbittrace_gmn_dp_track_before_detect_v1" / "run_development.py"
WRAPPER = ROOT / "orbittrace_gmn_dp_track_before_detect_v1_engineering" / "exact_pair_runner.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def compare_case(frozen, pair_fn, lon, lat, vg):
    u = frozen.unit(np.asarray(lon, float), np.asarray(lat, float))
    logv = np.log(np.asarray(vg, float))
    x = frozen.transform(u, logv)
    tree = cKDTree(x)
    old = frozen.exact_radius_counts(tree, x, u, logv, u, logv, subtract_self=True)
    new = pair_fn(tree, x, u, logv, u, logv, subtract_self=True)
    if not np.array_equal(old, new):
        bad = np.flatnonzero(old != new)[:20]
        raise AssertionError(f"count mismatch at {bad.tolist()}: old={old[bad].tolist()} new={new[bad].tolist()}")
    return int(old.sum())


def main() -> int:
    frozen = load(FROZEN, "dptbd_equiv_frozen")
    wrapper = load(WRAPPER, "dptbd_equiv_wrapper")
    pair_fn = wrapper.exact_pair_radius_counts_factory(frozen)

    total = 0
    # Deterministic random clouds across broad radiant/speed support.
    for seed, n in ((1, 64), (7, 257), (19, 701), (101, 1200)):
        rng = np.random.default_rng(seed)
        lon = rng.uniform(-180.0, 180.0, n)
        lat = np.degrees(np.arcsin(rng.uniform(-1.0, 1.0, n)))
        vg = np.exp(rng.uniform(np.log(10.0), np.log(75.0), n))
        total += compare_case(frozen, pair_fn, lon, lat, vg)

    # Dense cloud exercises many overlapping neighbor lists.
    rng = np.random.default_rng(20260812)
    n = 900
    lon = 45.0 + rng.normal(0.0, 1.1, n)
    lat = -12.0 + rng.normal(0.0, 1.1, n)
    vg = 36.0 * np.exp(rng.normal(0.0, 0.025, n))
    total += compare_case(frozen, pair_fn, lon, lat, vg)

    # Boundary/degeneracy cases: duplicate states, exactly 3 degrees radiant,
    # exactly 8% speed, and combinations just inside/outside the physical radius.
    lon = np.asarray([0.0, 0.0, 3.0, 3.0000001, 0.0, 0.0, 2.0, -2.0])
    lat = np.zeros(len(lon))
    vg = np.asarray([30.0, 30.0, 30.0, 30.0, 32.4, 32.400001, 31.0, 29.0])
    total += compare_case(frozen, pair_fn, lon, lat, vg)

    print(f"PASS_DP_TBD_EXACT_PAIR_RADIUS_EQUIVALENCE total_directed_neighbor_counts={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
