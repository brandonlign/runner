"""Pure feature transforms used by the v2 detector."""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np


def circular_difference_deg(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return (np.asarray(left, dtype=float) - np.asarray(right, dtype=float) + 180.0) % 360.0 - 180.0


def circular_center_deg(values: np.ndarray) -> float:
    radians = np.radians(np.asarray(values, dtype=float))
    return float(np.degrees(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def periodic_physical6_from_raw(raw: np.ndarray, feature_scales: Sequence[float] = (3.5, 3.0, 2.5, 2.5)) -> np.ndarray:
    values = np.asarray(raw, dtype=float)
    scales = np.asarray(tuple(feature_scales), dtype=float)
    if values.ndim != 2 or values.shape[1] != 4:
        raise ValueError("raw input must have shape (n, 4)")
    if scales.shape != (4,) or np.any(scales <= 0):
        raise ValueError("feature_scales must contain four positive values")
    longitude = np.radians(values[:, 0])
    solar_offset = np.radians(values[:, 3])
    longitude_scale = 180.0 / (np.pi * scales[0])
    solar_scale = 180.0 / (np.pi * scales[3])
    return np.column_stack((
        np.cos(solar_offset) * solar_scale,
        np.sin(solar_offset) * solar_scale,
        np.cos(longitude) * longitude_scale,
        np.sin(longitude) * longitude_scale,
        values[:, 1] / scales[1],
        values[:, 2] / scales[2],
    ))


def periodic_physical6_from_mapping(rows: Sequence[Mapping[str, float]], feature_scales: Sequence[float] = (3.5, 3.0, 2.5, 2.5)) -> np.ndarray:
    solar = np.asarray([float(row["sol"]) for row in rows], dtype=float)
    raw = np.column_stack((
        np.asarray([float(row["sun_lon"]) for row in rows], dtype=float),
        np.asarray([float(row["ecl_lat"]) for row in rows], dtype=float),
        np.asarray([float(row["vg"]) for row in rows], dtype=float),
        circular_difference_deg(solar, circular_center_deg(solar)),
    ))
    return periodic_physical6_from_raw(raw, feature_scales)


__all__ = ["circular_center_deg", "circular_difference_deg", "periodic_physical6_from_mapping", "periodic_physical6_from_raw"]
