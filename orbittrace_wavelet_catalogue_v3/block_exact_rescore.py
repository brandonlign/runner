#!/usr/bin/env python3
"""Bounded-memory fixed4 block acceleration for frozen catalogue-v3 rescoring.

The frozen wavelet rescoring code path is intentionally preserved per anchor.
Only fixed4's repeated Python construction of an N-event distance vector is
replaced by the algebraically identical NumPy block calculation.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable

import numpy as np

DEFAULT_BLOCK_SIZE = 64
EQUIVALENCE_TOLERANCE = 2e-13


def _wrap180_array(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    return (values + 180.0) % 360.0 - 180.0


def _fixed4_distance_block(
    anchor_indices: np.ndarray,
    sols: np.ndarray,
    sun_lons: np.ndarray,
    ecl_lats: np.ndarray,
    speeds: np.ndarray,
) -> np.ndarray:
    """Vectorize the exact frozen fixed4 anchor-distance formula."""
    anchor_indices = np.asarray(anchor_indices, dtype=np.int64)

    squared = _wrap180_array(sols[None, :] - sols[anchor_indices, None])
    squared /= 4.0
    np.square(squared, out=squared)

    tmp = _wrap180_array(sun_lons[None, :] - sun_lons[anchor_indices, None])
    mean_lat = np.radians(0.5 * (ecl_lats[None, :] + ecl_lats[anchor_indices, None]))
    tmp *= np.cos(mean_lat)
    tmp /= 2.0
    np.square(tmp, out=tmp)
    squared += tmp
    del mean_lat

    tmp = (ecl_lats[None, :] - ecl_lats[anchor_indices, None]) / 2.0
    np.square(tmp, out=tmp)
    squared += tmp

    tmp = (speeds[None, :] - speeds[anchor_indices, None]) / 2.0
    np.square(tmp, out=tmp)
    squared += tmp

    np.sqrt(squared, out=squared)
    squared[np.arange(len(anchor_indices)), anchor_indices] = np.inf
    return squared


def make_exact_rescore_window(runtime: Any, block_size: int = DEFAULT_BLOCK_SIZE) -> Callable[..., list[dict[str, Any]]]:
    """Return a drop-in replacement for the frozen `exact_rescore_window`.

    Wavelet operations below intentionally mirror the frozen grouped function
    statement-for-statement. Fixed4 nearest-three search is the only O(N)
    calculation moved into bounded NumPy blocks.
    """
    if int(block_size) <= 0:
        raise ValueError("block_size must be positive")
    block_size = int(block_size)

    def exact_rescore_window(
        records: list[dict[str, Any]],
        window_events: list[dict[str, Any]],
        event_lookup: dict[str, dict[str, Any]],
        support: Any,
        base: Any,
    ) -> list[dict[str, Any]]:
        if len(window_events) < runtime.EPISODE_SIZE:
            raise RuntimeError("insufficient exact rescore events")

        event_ids = np.asarray([str(event["id"]) for event in window_events], dtype=object)
        id_to_index = {event_id: index for index, event_id in enumerate(event_ids.tolist())}
        if len(id_to_index) != len(window_events):
            raise RuntimeError("duplicate event ids in exact rescore window")

        vectors = runtime.wavelet.radiant_unit_vectors(
            [float(event["sun_lon"]) for event in window_events],
            [float(event["ecl_lat"]) for event in window_events],
        )
        sols = np.asarray([float(event["sol"]) for event in window_events], dtype=np.float64)
        sun_lons = np.asarray([float(event["sun_lon"]) for event in window_events], dtype=np.float64)
        ecl_lats = np.asarray([float(event["ecl_lat"]) for event in window_events], dtype=np.float64)
        speeds = np.asarray([float(event["vg"]) for event in window_events], dtype=np.float64)
        if np.any(speeds <= 0.0):
            raise RuntimeError("non-positive speed")
        angular_scale = math.radians(runtime.wavelet.ANGULAR_PROBE_DEG)

        rescored: list[dict[str, Any]] = []
        completed = 0
        for start in range(0, len(records), block_size):
            block = records[start : start + block_size]
            anchor_ids = [str(record["anchor_id"]) for record in block]
            try:
                anchor_indices = np.asarray([id_to_index[anchor_id] for anchor_id in anchor_ids], dtype=np.int64)
            except KeyError as exc:
                raise RuntimeError(f"anchor absent from exact rescore window: {exc.args[0]}") from exc

            fixed4_distances = _fixed4_distance_block(
                anchor_indices, sols, sun_lons, ecl_lats, speeds
            )

            for row_index, (record, anchor_id, anchor_index) in enumerate(
                zip(block, anchor_ids, anchor_indices)
            ):
                anchor = event_lookup[anchor_id]

                # Frozen wavelet grouped implementation, preserved exactly.
                cosine = np.clip(vectors @ vectors[int(anchor_index)], -1.0, 1.0)
                angular = np.arccos(cosine) / angular_scale
                fractional = (speeds - speeds[int(anchor_index)]) / (
                    runtime.wavelet.SPEED_PROBE_FRACTION * speeds[int(anchor_index)]
                )
                r2 = np.maximum(angular * angular + fractional * fractional, 0.0)
                r2[int(anchor_index)] = np.inf
                nearest = runtime.stable_smallest_indices(r2, runtime.EPISODE_SIZE - 1)
                selected_r2 = r2[nearest]
                weights = (runtime.wavelet.KERNEL_DIMENSION - selected_r2) * np.exp(-0.5 * selected_r2)
                weights = np.where(
                    selected_r2 <= runtime.wavelet.TRUNCATION_RADIUS ** 2,
                    weights,
                    0.0,
                )
                wavelet_score = float(np.sum(weights))
                positive = nearest[selected_r2 < runtime.POSITIVE_LOBE_R2]
                member_ids = sorted(set([anchor_id] + event_ids[positive].tolist()))

                fixed4_order = runtime.stable_smallest_indices(fixed4_distances[row_index], 3)
                quartet = [anchor] + [window_events[int(index)] for index in fixed4_order]
                # Final four-event score remains delegated to the frozen support
                # implementation; only nearest-three search was vectorized.
                fixed4_score = float(support.quartet_score(quartet, base))

                exact = dict(record)
                exact.update({
                    "wavelet_score": wavelet_score,
                    "fixed4_score": fixed4_score,
                    "member_ids": member_ids,
                    "exact_rescore": True,
                })
                rescored.append(exact)

            completed += len(block)
            if completed % 2048 < len(block) or completed == len(records):
                center = float(block[-1]["window_center"]) if block else float("nan")
                print(
                    f"block exact window {center:.1f}: {completed:,}/{len(records):,} anchors",
                    flush=True,
                )
            del fixed4_distances

        return rescored

    return exact_rescore_window


def _synthetic_panel(runtime: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rng = np.random.default_rng(20260807)
    events = [
        {
            "id": f"BLOCK-{index:04d}",
            "sol": float(rng.uniform(0.0, 360.0)),
            "sun_lon": float(rng.uniform(-180.0, 180.0)),
            "ecl_lat": float(rng.uniform(-80.0, 80.0)),
            "vg": float(rng.uniform(8.0, 75.0)),
        }
        for index in range(256)
    ]
    edge = [
        (359.9, 179.9, 10.0, 40.0),
        (0.1, -179.9, 10.0, 40.0),
        (180.0, 0.0, 0.0, 30.0),
        (0.0, 180.0, 0.0, 30.0),
    ]
    for index, (sol, lon, lat, speed) in enumerate(edge):
        events[index].update(sol=sol, sun_lon=lon, ecl_lat=lat, vg=speed)
    lookup = {str(event["id"]): event for event in events}
    chosen = rng.choice(len(events), size=64, replace=False)
    records = [
        {
            "year": 2022,
            "anchor_id": str(events[int(index)]["id"]),
            "window_center": 0.0,
            "bin": 0,
            "wavelet_score": 0.0,
            "fixed4_score": 0.0,
            "member_ids": [],
            "nearest_ids": [],
            "p_wavelet": 1.0,
            "p_fixed4": 1.0,
            "wavelet_detected": False,
            "rescue_detected": False,
            "exact_rescore": False,
        }
        for index in chosen
    ]
    return events, lookup, records


def self_test(runtime: Any, support: Any) -> dict[str, Any]:
    """Compare the block implementation directly with the frozen grouped one."""

    class MockBase:
        @staticmethod
        def wrap180(value: float) -> float:
            return float((value + 180.0) % 360.0 - 180.0)

    events, lookup, records = _synthetic_panel(runtime)
    scalar = runtime.exact_rescore_window(records, events, lookup, support, MockBase)
    blocked = make_exact_rescore_window(runtime, block_size=16)(records, events, lookup, support, MockBase)

    wavelet_diffs = [
        abs(float(left["wavelet_score"]) - float(right["wavelet_score"]))
        for left, right in zip(scalar, blocked)
    ]
    fixed4_diffs = [
        abs(float(left["fixed4_score"]) - float(right["fixed4_score"]))
        for left, right in zip(scalar, blocked)
    ]

    sols = np.asarray([float(event["sol"]) for event in events], dtype=np.float64)
    lons = np.asarray([float(event["sun_lon"]) for event in events], dtype=np.float64)
    lats = np.asarray([float(event["ecl_lat"]) for event in events], dtype=np.float64)
    speeds = np.asarray([float(event["vg"]) for event in events], dtype=np.float64)
    id_to_index = {str(event["id"]): index for index, event in enumerate(events)}
    anchor_indices = np.asarray([id_to_index[str(record["anchor_id"])] for record in records], dtype=np.int64)
    fixed_block = _fixed4_distance_block(anchor_indices, sols, lons, lats, speeds)
    fixed4_nearest_equal = True
    max_fixed4_distance_diff = 0.0
    for row_index, anchor_index in enumerate(anchor_indices):
        anchor = events[int(anchor_index)]
        scalar_distances = np.asarray(
            support.exact_anchor_distances(anchor, events, MockBase), dtype=np.float64
        ).copy()
        scalar_distances[int(anchor_index)] = np.inf
        finite = np.isfinite(scalar_distances)
        max_fixed4_distance_diff = max(
            max_fixed4_distance_diff,
            float(np.max(np.abs(scalar_distances[finite] - fixed_block[row_index, finite]))),
        )
        left = runtime.stable_smallest_indices(scalar_distances, 3)
        right = runtime.stable_smallest_indices(fixed_block[row_index], 3)
        if left.tolist() != right.tolist():
            fixed4_nearest_equal = False
            break

    wrap_values = np.asarray(
        [-1080.0, -720.0, -540.0, -360.0, -180.0, -0.0, 180.0, 360.0, 540.0, 720.0, 1080.0],
        dtype=np.float64,
    )
    vector_wrap = _wrap180_array(wrap_values)
    scalar_wrap = np.asarray([MockBase.wrap180(float(value)) for value in wrap_values])

    return {
        "scalar_block_wavelet_within_tolerance": bool(max(wavelet_diffs, default=0.0) <= EQUIVALENCE_TOLERANCE),
        "scalar_block_wavelet_exact": bool(max(wavelet_diffs, default=0.0) == 0.0),
        "scalar_block_fixed4_within_tolerance": bool(max(fixed4_diffs, default=0.0) <= EQUIVALENCE_TOLERANCE),
        "scalar_block_membership_equal": bool(
            all(left["member_ids"] == right["member_ids"] for left, right in zip(scalar, blocked))
        ),
        "fixed4_nearest_three_equal": bool(fixed4_nearest_equal),
        "wrap180_vectorization_equal": bool(np.array_equal(vector_wrap, scalar_wrap)),
        "max_wavelet_abs_diff": float(max(wavelet_diffs, default=0.0)),
        "max_fixed4_abs_diff": float(max(fixed4_diffs, default=0.0)),
        "max_fixed4_distance_abs_diff": float(max_fixed4_distance_diff),
        "block_size": 16,
    }


def benchmark(runtime: Any, support: Any) -> dict[str, float]:
    """Small informative benchmark; speed is not a scientific pass/fail gate."""

    class MockBase:
        @staticmethod
        def wrap180(value: float) -> float:
            return float((value + 180.0) % 360.0 - 180.0)

    rng = np.random.default_rng(20260808)
    events = [
        {
            "id": f"BENCH-{index:05d}",
            "sol": float(rng.uniform(0.0, 360.0)),
            "sun_lon": float(rng.uniform(-180.0, 180.0)),
            "ecl_lat": float(rng.uniform(-80.0, 80.0)),
            "vg": float(rng.uniform(8.0, 75.0)),
        }
        for index in range(5000)
    ]
    lookup = {str(event["id"]): event for event in events}
    chosen = rng.choice(len(events), size=256, replace=False)
    records = [
        {
            "year": 2022,
            "anchor_id": str(events[int(index)]["id"]),
            "window_center": 0.0,
            "bin": 0,
            "wavelet_score": 0.0,
            "fixed4_score": 0.0,
            "member_ids": [],
            "nearest_ids": [],
            "p_wavelet": 1.0,
            "p_fixed4": 1.0,
            "wavelet_detected": False,
            "rescue_detected": False,
            "exact_rescore": False,
        }
        for index in chosen
    ]

    start = time.perf_counter()
    runtime.exact_rescore_window(records, events, lookup, support, MockBase)
    scalar_seconds = time.perf_counter() - start
    start = time.perf_counter()
    make_exact_rescore_window(runtime, block_size=DEFAULT_BLOCK_SIZE)(
        records, events, lookup, support, MockBase
    )
    block_seconds = time.perf_counter() - start
    return {
        "scalar_seconds": float(scalar_seconds),
        "block_seconds": float(block_seconds),
        "speedup": float(scalar_seconds / block_seconds) if block_seconds > 0 else float("inf"),
    }
