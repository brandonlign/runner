#!/usr/bin/env python3
"""Value-free MAARSY normalization primitives for the frozen external access contract.

This module has no HDF5/file/network loader by design. The scientific runner must
perform the staged reads described in PROTOCOL.md and pass only the permitted arrays.
"""
from __future__ import annotations

import hashlib
from typing import Iterable, Sequence

import numpy as np

AU_M = 149_597_870_700.0
BLIND_LOW = 20.0
BLIND_HIGH = 55.0


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def wrap180(value: float) -> float:
    out = (float(value) + 180.0) % 360.0 - 180.0
    return 180.0 if out == -180.0 and float(value) > 0 else out


def blind_keep_mask(sun_lon_deg: Sequence[float] | np.ndarray) -> np.ndarray:
    """First-value-stage operation: return rows outside the inclusive 20–55 firewall."""
    sol = np.asarray(sun_lon_deg, dtype=np.float64)
    require(sol.ndim == 1, "sun_lon must be one-dimensional")
    require(np.isfinite(sol).all(), "sun_lon contains nonfinite values")
    require(((sol >= 0.0) & (sol < 360.0)).all(), "sun_lon is not degree-valued in [0,360)")
    return ~((sol >= BLIND_LOW) & (sol <= BLIND_HIGH))


def stable_event_id(year: int, archive_member: str, row_index_0based: int) -> str:
    require(year in (2020, 2021), "MAARSY year outside permanent external pair")
    require(bool(archive_member), "archive member identity missing")
    require(int(row_index_0based) >= 0, "row index negative")
    return f"MAARSY|{year}|{archive_member}|{int(row_index_0based)}"


def normalize_retained_geometry(
    *,
    year: int,
    archive_member: str,
    retained_row_indices: Sequence[int],
    retained_sun_lon_deg: Sequence[float] | np.ndarray,
    retained_slon_deg: Sequence[float] | np.ndarray,
    retained_slat_deg: Sequence[float] | np.ndarray,
    retained_vels_km_s: Sequence[Sequence[float]] | np.ndarray,
) -> list[dict[str, float | str]]:
    """Normalize only already-retained rows; this function never receives blinded rows."""
    require(year in (2020, 2021), "MAARSY year outside permanent external pair")
    idx = np.asarray(retained_row_indices, dtype=np.int64)
    sol = np.asarray(retained_sun_lon_deg, dtype=np.float64)
    slon = np.asarray(retained_slon_deg, dtype=np.float64)
    slat = np.asarray(retained_slat_deg, dtype=np.float64)
    vels = np.asarray(retained_vels_km_s, dtype=np.float64)
    n = len(idx)
    require(idx.ndim == sol.ndim == slon.ndim == slat.ndim == 1, "retained scalar arrays must be one-dimensional")
    require(len(sol) == len(slon) == len(slat) == n, "retained geometry row counts differ")
    require(vels.ndim == 2 and vels.shape[0] == n and vels.shape[1] >= 2, "vels is not row-aligned vectors")
    require(np.isfinite(sol).all() and np.isfinite(slon).all() and np.isfinite(slat).all() and np.isfinite(vels).all(), "retained geometry contains nonfinite values")
    require(((sol >= 0.0) & (sol < 360.0)).all(), "retained sun_lon is not degree-valued")
    require((idx >= 0).all() and len(set(int(x) for x in idx)) == n, "retained row indices invalid/duplicate")
    require((~((sol >= BLIND_LOW) & (sol <= BLIND_HIGH))).all(), "blinded solar-longitude row reached geometry normalization")
    speed = np.linalg.norm(vels, axis=1)
    require((speed > 0.0).all() and np.isfinite(speed).all(), "geocentric speed invalid")
    rows: list[dict[str, float | str]] = []
    for j in range(n):
        rows.append({
            "id": stable_event_id(year, archive_member, int(idx[j])),
            "sol": float(sol[j]),
            "sun_lon": float(wrap180(float(slon[j]))),
            "ecl_lat": float(slat[j]),
            "vg": float(speed[j]),
        })
    return rows


def proposal_manifest_sha256(event_ids: Iterable[str]) -> str:
    ids = sorted(str(x) for x in event_ids)
    require(len(ids) == len(set(ids)), "proposal manifest contains duplicate event IDs")
    return hashlib.sha256(("\n".join(ids) + ("\n" if ids else "")).encode()).hexdigest()


def normalize_frozen_proposal_orbits(
    *,
    event_ids: Sequence[str],
    kepler_rows: Sequence[Sequence[float]] | np.ndarray,
) -> dict[str, dict[str, float]]:
    """Map only an already-frozen proposal-ID subset to exact D_SH orbital fields."""
    ids = [str(x) for x in event_ids]
    kep = np.asarray(kepler_rows, dtype=np.float64)
    require(len(ids) == len(set(ids)), "orbit proposal IDs duplicate")
    require(kep.ndim == 2 and kep.shape == (len(ids), 6), "kepler subset must be exact (n,6)")
    require(np.isfinite(kep).all(), "kepler subset contains nonfinite values")
    out: dict[str, dict[str, float]] = {}
    for eid, row in zip(ids, kep):
        a_m, ecc, inc, omega, node, _true_anomaly = [float(x) for x in row]
        require(a_m != 0.0, f"zero semimajor axis for {eid}")
        require(0.0 <= ecc < 2.0, f"eccentricity outside frozen representable range for {eid}")
        a_au = a_m / AU_M
        out[eid] = {
            "q": float(abs(a_au * (1.0 - ecc))),
            "e": ecc,
            "i": inc,
            "peri": float(omega % 360.0),
            "node": float(node % 360.0),
        }
    return out
