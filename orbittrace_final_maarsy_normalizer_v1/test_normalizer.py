#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

from orbittrace_final_maarsy_normalizer_v1 import normalizer as n


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    sol = np.asarray([0.0, 19.999, 20.0, 37.0, 55.0, 55.001, 359.9])
    keep = n.blind_keep_mask(sol)
    require(keep.tolist() == [True, True, False, False, False, True, True], "inclusive firewall changed")

    rows = n.normalize_retained_geometry(
        year=2020,
        archive_member="data/2020/01/kep_collect.h5",
        retained_row_indices=[0, 5],
        retained_sun_lon_deg=[19.0, 56.0],
        retained_slon_deg=[181.0, -181.0],
        retained_slat_deg=[10.0, -20.0],
        retained_vels_km_s=[[3.0, 4.0, 0.0], [0.0, 0.0, 12.0]],
    )
    require(rows[0]["id"] == "MAARSY|2020|data/2020/01/kep_collect.h5|0", "event ID changed")
    require(rows[0]["sun_lon"] == -179.0 and rows[1]["sun_lon"] == 179.0, "wrap180 changed")
    require(rows[0]["vg"] == 5.0 and rows[1]["vg"] == 12.0, "velocity norm changed")

    ids = [str(rows[0]["id"]), str(rows[1]["id"])]
    s = n.proposal_manifest_sha256(ids)
    require(len(s) == 64 and s == n.proposal_manifest_sha256(reversed(ids)), "proposal hash not order canonical")

    kep = np.asarray([
        [n.AU_M, 0.5, 10.0, 370.0, -10.0, 99.0],
        [-2.0 * n.AU_M, 1.25, 20.0, -30.0, 725.0, -88.0],
    ])
    orb = n.normalize_frozen_proposal_orbits(event_ids=ids, kepler_rows=kep)
    require(abs(orb[ids[0]]["q"] - 0.5) < 1e-15, "elliptic q conversion changed")
    require(abs(orb[ids[1]]["q"] - 0.5) < 1e-15, "hyperbolic q absolute conversion changed")
    require(orb[ids[0]]["peri"] == 10.0 and orb[ids[0]]["node"] == 350.0, "orbit angle wrap changed")
    require(orb[ids[1]]["peri"] == 330.0 and orb[ids[1]]["node"] == 5.0, "negative orbit angle wrap changed")

    try:
        n.normalize_retained_geometry(
            year=2021,
            archive_member="x",
            retained_row_indices=[1],
            retained_sun_lon_deg=[55.0],
            retained_slon_deg=[0.0],
            retained_slat_deg=[0.0],
            retained_vels_km_s=[[1.0, 0.0, 0.0]],
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("blinded row was accepted by retained geometry normalizer")

    print("PASS_FINAL_MAARSY_NORMALIZER_V1_SYNTHETIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
