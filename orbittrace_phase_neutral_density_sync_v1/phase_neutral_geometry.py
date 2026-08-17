from __future__ import annotations

import math
from typing import Any

import numpy as np

BLIND = (20.0, 55.0)
SPEED_SCALE = 72.0


def phase_neutral_geo_matrix(events: list[dict[str, Any]]) -> np.ndarray:
    """Frozen GEO4 representation for phase-neutral density-sync v1.

    Solar longitude is intentionally excluded from the distance matrix. It is
    still checked here so protected-window events fail closed rather than being
    silently accepted by the phase-neutral transform.
    """
    if not events:
        return np.empty((0, 4), dtype=float)

    lon = []
    lat = []
    vg = []
    for event in events:
        sol = float(event["sol"])
        lo = float(event["lon"])
        la = float(event["lat"])
        speed = float(event["vg"])
        if not all(math.isfinite(x) for x in (sol, lo, la, speed)):
            raise ValueError("phase-neutral geometry requires finite sol/lon/lat/vg")
        sol %= 360.0
        if BLIND[0] <= sol <= BLIND[1]:
            raise ValueError("protected solar-longitude event reached phase-neutral geometry")
        if speed <= 0.0:
            raise ValueError("phase-neutral geometry requires positive geocentric speed")
        lon.append(lo)
        lat.append(la)
        vg.append(speed)

    lon_a = np.radians(np.asarray(lon, dtype=float))
    lat_a = np.radians(np.asarray(lat, dtype=float))
    vg_a = np.asarray(vg, dtype=float)
    X = np.column_stack((
        np.sin(lon_a) * np.cos(lat_a),
        np.cos(lon_a) * np.cos(lat_a),
        np.sin(lat_a),
        vg_a / SPEED_SCALE,
    ))
    if X.shape != (len(events), 4) or not np.isfinite(X).all():
        raise RuntimeError("phase-neutral GEO4 matrix construction failed")
    return X
