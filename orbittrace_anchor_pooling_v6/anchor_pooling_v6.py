"""OrbitTrace top-four anchor pooling candidate family, version 6.

Every candidate pools the same four strongest positive coefficients from the exact
frozen v3/Brown-family matched-filter geometry. Candidate evaluation is confined
to the exposed 2025+2023 development panel.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

import multi_anchor_energy_v3 as v3

METHOD_ORDER = (
    "orbittrace_anchor_l1_v6",
    "orbittrace_anchor_l1p5_v6",
    "orbittrace_multi_anchor_wavelet_energy_v3",
    "orbittrace_anchor_l4_v6",
    "orbittrace_anchor_geomean_v6",
    "orbittrace_anchor_min4_v6",
)
NEW_METHODS = tuple(method for method in METHOD_ORDER if method != "orbittrace_multi_anchor_wavelet_energy_v3")
TOP_ANCHORS = 4


def top_four_positive_coefficients(episode: Any) -> np.ndarray:
    coefficients = v3.wavelet_coefficients_from_arrays(episode.sun_lon, episode.ecl_lat, episode.vg)
    positive = np.maximum(np.asarray(coefficients, dtype=np.float64), 0.0)
    count = min(TOP_ANCHORS, len(positive))
    if count:
        indices = np.argpartition(positive, -count)[-count:]
        values = np.sort(positive[indices])[::-1]
    else:
        values = np.empty(0, dtype=np.float64)
    if count < TOP_ANCHORS:
        values = np.pad(values, (0, TOP_ANCHORS - count))
    if values.shape != (TOP_ANCHORS,) or not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("invalid top-four coefficient vector")
    return values


def _lp(values: np.ndarray, exponent: float) -> float:
    if exponent <= 0.0 or not math.isfinite(exponent):
        raise ValueError("positive finite exponent required")
    return float(np.sum(values ** exponent) ** (1.0 / exponent))


def scores_for_episode(episode: Any) -> dict[str, float]:
    c = top_four_positive_coefficients(episode)
    geomean = 0.0 if np.any(c <= 0.0) else float(np.prod(c) ** 0.25)
    scores = {
        "orbittrace_anchor_l1_v6": float(np.sum(c)),
        "orbittrace_anchor_l1p5_v6": _lp(c, 1.5),
        "orbittrace_multi_anchor_wavelet_energy_v3": _lp(c, 2.0),
        "orbittrace_anchor_l4_v6": _lp(c, 4.0),
        "orbittrace_anchor_geomean_v6": geomean,
        "orbittrace_anchor_min4_v6": float(c[-1]),
    }
    if tuple(scores) != METHOD_ORDER or not all(math.isfinite(value) and value >= 0.0 for value in scores.values()):
        raise RuntimeError("invalid v6 candidate score row")
    return scores


def self_test() -> dict[str, bool]:
    class Episode:
        pass

    episode = Episode()
    episode.sun_lon = np.linspace(-170.0, 170.0, 32)
    episode.ecl_lat = np.linspace(-55.0, 55.0, 32)
    episode.vg = np.linspace(15.0, 65.0, 32)
    episode.sun_lon[:4] = np.array([179.6, -179.8, 179.9, -179.5])
    episode.ecl_lat[:4] = np.array([10.0, 10.2, 9.8, 10.1])
    episode.vg[:4] = np.array([40.0, 40.2, 39.9, 40.1])

    scores = scores_for_episode(episode)
    exact_v3 = v3.multi_anchor_energy_episode_score(episode)

    permuted = Episode()
    order = np.arange(32)[::-1]
    for name in ("sun_lon", "ecl_lat", "vg"):
        setattr(permuted, name, np.asarray(getattr(episode, name))[order])
    permuted_scores = scores_for_episode(permuted)

    shifted = Episode()
    shifted.sun_lon = np.asarray(episode.sun_lon) + 360.0
    shifted.ecl_lat = np.asarray(episode.ecl_lat).copy()
    shifted.vg = np.asarray(episode.vg).copy()
    shifted_scores = scores_for_episode(shifted)

    return {
        "p2_exactly_reproduces_v3": math.isclose(
            scores["orbittrace_multi_anchor_wavelet_energy_v3"], exact_v3, abs_tol=1e-12, rel_tol=0.0
        ),
        "method_order_frozen": METHOD_ORDER == (
            "orbittrace_anchor_l1_v6",
            "orbittrace_anchor_l1p5_v6",
            "orbittrace_multi_anchor_wavelet_energy_v3",
            "orbittrace_anchor_l4_v6",
            "orbittrace_anchor_geomean_v6",
            "orbittrace_anchor_min4_v6",
        ),
        "top_anchor_count_frozen": TOP_ANCHORS == 4,
        "permutation_invariant": all(
            math.isclose(scores[key], permuted_scores[key], abs_tol=1e-10, rel_tol=0.0)
            for key in METHOD_ORDER
        ),
        "longitude_wrap_invariant": all(
            math.isclose(scores[key], shifted_scores[key], abs_tol=1e-10, rel_tol=0.0)
            for key in METHOD_ORDER
        ),
        "pooling_order_behaves": (
            scores["orbittrace_anchor_l1_v6"]
            >= scores["orbittrace_anchor_l1p5_v6"]
            >= scores["orbittrace_multi_anchor_wavelet_energy_v3"]
            >= scores["orbittrace_anchor_l4_v6"]
            >= 0.0
        ),
        "frozen_geometry_inherited": (
            v3.ANGULAR_PROBE_DEG == 4.0
            and v3.SPEED_PROBE_FRACTION == 0.10
            and v3.TRUNCATION_RADIUS == 4.0
            and v3.KERNEL_DIMENSION == 3.0
            and v3.TOP_ANCHORS == 4
        ),
    }
