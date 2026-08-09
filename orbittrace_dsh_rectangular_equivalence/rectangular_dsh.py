"""Engineering-only rectangular Southworth-Hawkins kernel.

This module is not a scientific-method change.  It computes only the left×right
block that the canonical square ``pairwise_dsh`` would return after its explicit
symmetry-roundoff average.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np


def wrap_pi(value: np.ndarray | float) -> np.ndarray:
    return (np.asarray(value, dtype=np.float64) + np.pi) % (2.0 * np.pi) - np.pi


def _raw_cross(
    q_left: np.ndarray,
    e_left: np.ndarray,
    inc_left: np.ndarray,
    peri_left: np.ndarray,
    node_left: np.ndarray,
    q_right: np.ndarray,
    e_right: np.ndarray,
    inc_right: np.ndarray,
    peri_right: np.ndarray,
    node_right: np.ndarray,
) -> np.ndarray:
    i1 = inc_left[:, None]
    i2 = inc_right[None, :]
    node_delta = wrap_pi(node_right[None, :] - node_left[:, None])
    cos_i = np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(node_delta)
    mutual_i = np.arccos(np.clip(cos_i, -1.0, 1.0))

    denominator = np.cos(0.5 * mutual_i)
    numerator = np.cos(0.5 * (i1 + i2)) * np.sin(0.5 * node_delta)
    ratio = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=np.abs(denominator) > 1e-15,
    )
    peri_delta = wrap_pi(
        peri_right[None, :] - peri_left[:, None]
        + 2.0 * np.arcsin(np.clip(ratio, -1.0, 1.0))
    )

    q_delta = q_left[:, None] - q_right[None, :]
    e_delta = e_left[:, None] - e_right[None, :]
    plane = 2.0 * np.sin(0.5 * mutual_i)
    peri_term = 0.5 * (e_left[:, None] + e_right[None, :]) * 2.0 * np.sin(0.5 * peri_delta)
    squared = q_delta * q_delta + e_delta * e_delta + plane * plane + peri_term * peri_term
    distance = np.sqrt(np.maximum(squared, 0.0))
    if not np.all(np.isfinite(distance)):
        raise ValueError("non-finite rectangular D_SH block")
    return distance


def rectangular_dsh(
    left_q_au: Sequence[float] | np.ndarray,
    left_eccentricity: Sequence[float] | np.ndarray,
    left_inclination_deg: Sequence[float] | np.ndarray,
    left_perihelion_argument_deg: Sequence[float] | np.ndarray,
    left_ascending_node_deg: Sequence[float] | np.ndarray,
    right_q_au: Sequence[float] | np.ndarray,
    right_eccentricity: Sequence[float] | np.ndarray,
    right_inclination_deg: Sequence[float] | np.ndarray,
    right_perihelion_argument_deg: Sequence[float] | np.ndarray,
    right_ascending_node_deg: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return exactly the canonical symmetrized pairwise_dsh left×right block."""
    lq = np.asarray(left_q_au, dtype=np.float64)
    le = np.asarray(left_eccentricity, dtype=np.float64)
    li = np.radians(np.asarray(left_inclination_deg, dtype=np.float64))
    lp = np.radians(np.asarray(left_perihelion_argument_deg, dtype=np.float64))
    ln = np.radians(np.asarray(left_ascending_node_deg, dtype=np.float64))
    rq = np.asarray(right_q_au, dtype=np.float64)
    re = np.asarray(right_eccentricity, dtype=np.float64)
    ri = np.radians(np.asarray(right_inclination_deg, dtype=np.float64))
    rp = np.radians(np.asarray(right_perihelion_argument_deg, dtype=np.float64))
    rn = np.radians(np.asarray(right_ascending_node_deg, dtype=np.float64))
    if not (lq.shape == le.shape == li.shape == lp.shape == ln.shape):
        raise ValueError("left D_SH arrays must have identical shapes")
    if not (rq.shape == re.shape == ri.shape == rp.shape == rn.shape):
        raise ValueError("right D_SH arrays must have identical shapes")
    if lq.ndim != 1 or rq.ndim != 1 or len(lq) < 1 or len(rq) < 1:
        raise ValueError("rectangular D_SH requires non-empty one-dimensional arrays")
    if not np.all(np.isfinite(np.column_stack((lq, le, li, lp, ln)))):
        raise ValueError("non-finite left orbital element in D_SH input")
    if not np.all(np.isfinite(np.column_stack((rq, re, ri, rp, rn)))):
        raise ValueError("non-finite right orbital element in D_SH input")

    left_right = _raw_cross(lq, le, li, lp, ln, rq, re, ri, rp, rn)
    right_left = _raw_cross(rq, re, ri, rp, rn, lq, le, li, lp, ln)
    distance = 0.5 * (left_right + right_left.T)
    if not np.all(np.isfinite(distance)):
        raise ValueError("non-finite symmetrized rectangular D_SH block")
    return distance
