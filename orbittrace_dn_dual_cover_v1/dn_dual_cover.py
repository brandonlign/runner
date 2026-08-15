from __future__ import annotations

import hashlib
from typing import Any, Iterable

import numpy as np

EARTH_SPEED_KM_S = 29.7
MIN_CLUSTER_SIZE = 10


def _as_vector(values: Iterable[float], name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1 or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite 1-D vector")
    return arr


def dn_coordinates(
    solar_longitude_deg: Iterable[float],
    sun_centered_radiant_lon_deg: Iterable[float],
    ecliptic_latitude_deg: Iterable[float],
    vg_km_s: Iterable[float],
) -> dict[str, np.ndarray]:
    """Convert locked GMN geocentric observables to published D_N variables.

    The stored Sun-centred longitude is L = lambda_radiant-lambda_sun.
    In the Valsecchi frame (x anti-Sun, y Earth-motion, z ecliptic north),
    geocentric velocity is opposite the radiant, so

        Ux/u = cos(beta) cos(L)
        Uy/u = cos(beta) sin(L)
        Uz/u = -sin(beta).

    D_N uses u, cos(theta)=Uy/u, phi=atan2(Ux,Uz), and encounter
    longitude. Stored solar longitude differs from Earth heliocentric encounter
    longitude by a common pi shift, which cancels from all pairwise D_N chord
    terms; we therefore use the stored solar longitude directly.
    """
    sol = _as_vector(solar_longitude_deg, "solar_longitude_deg")
    lon = _as_vector(sun_centered_radiant_lon_deg, "sun_centered_radiant_lon_deg")
    lat = _as_vector(ecliptic_latitude_deg, "ecliptic_latitude_deg")
    vg = _as_vector(vg_km_s, "vg_km_s")
    n = sol.size
    if lon.size != n or lat.size != n or vg.size != n:
        raise ValueError("D_N observable vectors have unequal lengths")
    if np.any(vg <= 0.0):
        raise ValueError("D_N requires positive geocentric speeds")

    lam = np.radians(np.mod(sol, 360.0))
    L = np.radians(lon)
    beta = np.radians(lat)
    cb = np.cos(beta)
    ux_hat = cb * np.cos(L)
    uy_hat = cb * np.sin(L)
    uz_hat = -np.sin(beta)
    norm = np.sqrt(ux_hat * ux_hat + uy_hat * uy_hat + uz_hat * uz_hat)
    if not np.allclose(norm, 1.0, rtol=0.0, atol=2e-14):
        raise RuntimeError("derived D_N velocity directions are not unit vectors")

    transverse = np.hypot(ux_hat, uz_hat)
    if np.any(transverse == 0.0):
        raise RuntimeError("D_N phi undefined for velocity exactly parallel to Earth motion")
    phi = np.arctan2(ux_hat, uz_hat)
    u = vg / EARTH_SPEED_KM_S
    cos_theta = uy_hat
    return {
        "u": u,
        "cos_theta": cos_theta,
        "phi": phi,
        "lambda": lam,
        "ux_hat": ux_hat,
        "uy_hat": uy_hat,
        "uz_hat": uz_hat,
    }


def dn_distance_squared_from_coordinates(a: dict[str, float], b: dict[str, float]) -> float:
    du = float(b["u"] - a["u"])
    dc = float(b["cos_theta"] - a["cos_theta"])
    dphi = float(b["phi"] - a["phi"])
    dlam = float(b["lambda"] - a["lambda"])
    dphi_a = 2.0 * np.sin(0.5 * dphi)
    dphi_b = 2.0 * np.sin(0.5 * (np.pi + dphi))
    dlam_a = 2.0 * np.sin(0.5 * dlam)
    dlam_b = 2.0 * np.sin(0.5 * (np.pi + dlam))
    xi2 = min(
        float(dphi_a * dphi_a + dlam_a * dlam_a),
        float(dphi_b * dphi_b + dlam_b * dlam_b),
    )
    out = du * du + dc * dc + xi2
    if out < -1e-14 or not np.isfinite(out):
        raise RuntimeError(f"invalid D_N squared distance {out}")
    return float(max(out, 0.0))


def dual_cover_from_coordinates(coords: dict[str, np.ndarray]) -> np.ndarray:
    u = np.asarray(coords["u"], dtype=float)
    ct = np.asarray(coords["cos_theta"], dtype=float)
    phi = np.asarray(coords["phi"], dtype=float)
    lam = np.asarray(coords["lambda"], dtype=float)
    n = u.size
    if ct.shape != (n,) or phi.shape != (n,) or lam.shape != (n,):
        raise ValueError("D_N coordinate arrays have unequal shapes")
    angular = np.column_stack((np.cos(phi), np.sin(phi), np.cos(lam), np.sin(lam)))
    plus = np.column_stack((u, ct, angular))
    minus = np.column_stack((u, ct, -angular))
    cover = np.vstack((plus, minus))
    if cover.shape != (2 * n, 6) or not np.all(np.isfinite(cover)):
        raise RuntimeError("invalid D_N dual cover")
    return cover


def dual_cover(
    solar_longitude_deg: Iterable[float],
    sun_centered_radiant_lon_deg: Iterable[float],
    ecliptic_latitude_deg: Iterable[float],
    vg_km_s: Iterable[float],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    coords = dn_coordinates(
        solar_longitude_deg,
        sun_centered_radiant_lon_deg,
        ecliptic_latitude_deg,
        vg_km_s,
    )
    return dual_cover_from_coordinates(coords), coords


def member_hash(members: tuple[str, ...]) -> str:
    return hashlib.sha256(("DNDC1|" + "|".join(members)).encode()).hexdigest()[:20]


def fold_selected_cover_clusters(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    physical_event_ids: list[str],
    ordinary_stability: dict[float, float],
    synchronous_stability: dict[float, float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fold selected two-sheet cover clusters into physical meteor families.

    A physical candidate may contain at most one sheet of each meteor. Cover
    clusters violating that quotient constraint are discarded. Exact mirror
    duplicates are deterministically collapsed to one physical membership set.
    """
    labs = np.asarray(labels, dtype=np.int64)
    n = len(physical_event_ids)
    if labs.shape != (2 * n,):
        raise ValueError(f"cover labels shape {labs.shape} does not match 2N={2*n}")
    if len(set(physical_event_ids)) != n:
        raise ValueError("physical event IDs are not unique")
    positive = sorted(int(x) for x in np.unique(labs) if int(x) >= 0)
    if positive != list(range(len(selected_nodes))):
        raise RuntimeError("cover compact labels no longer map contiguously to selected nodes")

    by_members: dict[tuple[str, ...], dict[str, Any]] = {}
    invalid_duplicate_sheet = 0
    below_minimum_after_fold = 0
    raw_valid_clusters = 0
    mirror_duplicate_clusters = 0

    for lab, node in enumerate(selected_nodes):
        rep_idx = np.flatnonzero(labs == lab)
        phys_idx = rep_idx % n
        if len(np.unique(phys_idx)) != len(phys_idx):
            invalid_duplicate_sheet += 1
            continue
        members = tuple(sorted(physical_event_ids[int(i)] for i in phys_idx))
        if len(members) < MIN_CLUSTER_SIZE:
            below_minimum_after_fold += 1
            continue
        raw_valid_clusters += 1
        sync = float(synchronous_stability[float(node)])
        ordinary = float(ordinary_stability[float(node)])
        if not np.isfinite(sync) or sync < 0.0 or not np.isfinite(ordinary) or ordinary < 0.0:
            raise RuntimeError(f"invalid cover stability for selected node {node}")
        row = {
            "family_id": member_hash(members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "cover_member_count": int(len(rep_idx)),
            "density_synchronous_cover_stability": sync,
            "ordinary_cover_stability": ordinary,
        }
        if members in by_members:
            mirror_duplicate_clusters += 1
            old = by_members[members]
            old_key = (
                float(old["density_synchronous_cover_stability"]),
                float(old["ordinary_cover_stability"]),
                -int(old["node_id"]),
            )
            new_key = (sync, ordinary, -int(node))
            if new_key > old_key:
                by_members[members] = row
        else:
            by_members[members] = row

    candidates = list(by_members.values())
    candidates.sort(key=lambda f: (
        -float(f["density_synchronous_cover_stability"]),
        -float(f["ordinary_cover_stability"]),
        -int(f["member_count"]),
        str(f["family_id"]),
    ))
    if len({tuple(c["event_ids"]) for c in candidates}) != len(candidates):
        raise RuntimeError("physical membership duplicate survived mirror folding")
    if any(len(c["event_ids"]) != len(set(c["event_ids"])) for c in candidates):
        raise RuntimeError("emitted physical candidate repeats an event ID")

    audit = {
        "selected_cover_cluster_count": len(selected_nodes),
        "raw_valid_cover_cluster_count": raw_valid_clusters,
        "invalid_duplicate_sheet_cluster_count": invalid_duplicate_sheet,
        "below_minimum_after_fold_count": below_minimum_after_fold,
        "mirror_duplicate_cluster_count": mirror_duplicate_clusters,
        "physical_candidate_count": len(candidates),
    }
    return candidates, audit
