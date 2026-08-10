#!/usr/bin/env python3
from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from orbittrace_v16_label_free_multiscale_v1 import family_builder, multiscale


def row(event_id: str, year: int, sol: float, lon: float = 1.0, lat: float = 2.0, vg: float = 30.0):
    return {
        "id": event_id,
        "year": year,
        "sol": sol,
        "sun_lon": lon,
        "ecl_lat": lat,
        "vg": vg,
        "iau": 0,
        "complex_key": "HIDDEN",
    }


class FakeBase:
    @staticmethod
    def wrap180(value):
        arr = np.asarray(value)
        out = (arr + 180.0) % 360.0 - 180.0
        return float(out) if out.ndim == 0 else out


class FakeRuntime:
    @staticmethod
    def window_events_for_center(events, _center, _base):
        return list(events)

    @staticmethod
    def exact_wavelet_r2(_anchor, events):
        return np.arange(len(events), dtype=float)

    @staticmethod
    def stable_smallest_indices(distances, k):
        return np.argsort(distances, kind="stable")[:k]


class V16Tests(unittest.TestCase):
    def test_target_interval_fails_closed(self):
        with self.assertRaises(RuntimeError):
            family_builder._validate_scan(
                (2020, 2021),
                {2020: [row("2020a", 2020, 30.0)], 2021: [row("2021a", 2021, 100.0)]},
            )

    def test_truth_key_fails_closed(self):
        bad = row("2020a", 2020, 100.0)
        bad["label"] = "SECRET"
        with self.assertRaises(RuntimeError):
            family_builder._validate_scan(
                (2020, 2021),
                {2020: [bad], 2021: [row("2021a", 2021, 100.0)]},
            )

    def test_low_density_adaptive_episode_uses_all_available(self):
        events = [row(f"e{i}", 2020, 100.0 + i * 0.01, lon=float(i), lat=1.0, vg=30.0) for i in range(5)]
        family = {
            "family_id": "F",
            "centroids": {"2020": {"sol": 100.0, "sun_lon": 0.0, "ecl_lat": 1.0, "vg": 30.0}},
        }
        episode, meta = multiscale.adaptive_local_episode(
            family, 2020, events, cap=128, runtime=FakeRuntime(), base=FakeBase()
        )
        self.assertEqual(meta["episode_size"], 5)
        self.assertEqual(len(episode.vg), 5)

    def test_fewer_than_four_local_events_fail(self):
        events = [row(f"e{i}", 2020, 100.0 + i * 0.01) for i in range(3)]
        family = {
            "family_id": "F",
            "centroids": {"2020": {"sol": 100.0, "sun_lon": 0.0, "ecl_lat": 1.0, "vg": 30.0}},
        }
        with self.assertRaises(RuntimeError):
            multiscale.adaptive_local_episode(
                family, 2020, events, cap=128, runtime=FakeRuntime(), base=FakeBase()
            )

    def test_consensus_rule_is_exact_median_with_frozen_ties(self):
        orders = {
            128: ["A", "B", "C", "D"],
            96: ["B", "A", "D", "C"],
            64: ["B", "C", "A", "D"],
        }
        order, rows = multiscale.consensus_order(orders, (128, 96, 64))
        self.assertEqual(order, ["B", "A", "C", "D"])
        self.assertEqual({x["family_id"]: x["v16_median_rank_score"] for x in rows}, {"B": 0.0, "A": 1.0, "C": 2.0, "D": 3.0})

    def test_all_caps_and_nominal_components_are_frozen(self):
        self.assertEqual(multiscale.ALL_CAPS, (16, 24, 32, 48, 64, 72, 96, 128))
        self.assertEqual(multiscale.NOMINAL_COMPONENTS[128], (128, 96, 64))
        self.assertEqual(multiscale.NOMINAL_COMPONENTS[96], (96, 72, 48))
        self.assertEqual(multiscale.NOMINAL_COMPONENTS[64], (64, 48, 32))
        self.assertEqual(multiscale.NOMINAL_COMPONENTS[32], (32, 24, 16))


if __name__ == "__main__":
    unittest.main()
