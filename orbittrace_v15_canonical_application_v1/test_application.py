#!/usr/bin/env python3
from __future__ import annotations

import math

import numpy as np

from orbittrace_v15_canonical_application_v1 import application as a


class Runtime:
    @staticmethod
    def window_events_for_center(events, center_sol, _base):
        return [row for row in events if abs(((row["sol"] - center_sol + 180.0) % 360.0) - 180.0) <= 5.0]

    @staticmethod
    def exact_wavelet_r2(anchor, events):
        return np.asarray([
            (float(row["sun_lon"]) - float(anchor["sun_lon"])) ** 2
            + (float(row["ecl_lat"]) - float(anchor["ecl_lat"])) ** 2
            + ((float(row["vg"]) - float(anchor["vg"])) / 5.0) ** 2
            for row in events
        ], dtype=np.float64)

    @staticmethod
    def stable_smallest_indices(distances, k):
        return np.argsort(np.asarray(distances), kind="stable")[:k]


class Base:
    pass


def row(event_id: str, year: int, j: int) -> dict:
    # All rows lie in the same 10-degree local window, but the geometry spans enough range
    # that nested caps select different tails around different family centroids.
    return {
        "id": event_id,
        "year": year,
        "sol": 100.0 + ((j % 9) - 4) * 0.5,
        "sun_lon": -40.0 + 80.0 * (j / 139.0),
        "ecl_lat": -10.0 + 20.0 * ((j % 23) / 22.0),
        "vg": 25.0 + 20.0 * ((j % 31) / 30.0),
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def scans(n=140):
    return {
        2022: [row(f"A22:{j}", 2022, j) for j in range(n)],
        2023: [row(f"A23:{j}", 2023, j) for j in range(n)],
    }


def family(fid: str, lon: float) -> dict:
    cent = {"sol": 100.0, "sun_lon": lon, "ecl_lat": 0.0, "vg": 35.0}
    return {
        "family_id": fid,
        "years": [2022, 2023],
        "centroids": {"2022": dict(cent), "2023": dict(cent)},
    }


def builder(years, canonical_scan):
    assert years == (2022, 2023)
    assert set(canonical_scan) == {2022, 2023}
    assert all(tuple(r) == (
        "id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"
    ) for ys in canonical_scan.values() for r in ys)
    return [family("F_A", -25.0), family("F_B", 0.0), family("F_C", 25.0)]


def score_episode(episode):
    # Synthetic scorer only. It preserves the exact v5 return contract and multiplicity
    # factorization while making selected episode geometry influence rank.
    mean_abs_lon = abs(float(np.mean(episode.sun_lon)))
    multiplicity = 1.0 + min(3.0, mean_abs_lon / 50.0)
    brown = 1.0
    v3 = math.sqrt(multiplicity)
    return v3, brown, multiplicity, 0.0


def expect_fail(fn, text):
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), (text, str(exc))
    else:
        raise AssertionError(f"expected failure containing {text!r}")


def test_exact_consensus_reference_rule():
    orders = {
        128: ["A", "B", "C"],
        96: ["B", "A", "C"],
        64: ["B", "C", "A"],
    }
    order, rows = a.consensus_order(orders)
    assert order == ["B", "A", "C"]
    by_id = {r["family_id"]: r for r in rows}
    assert by_id["A"]["component_ranks_zero_based"] == [0, 1, 2]
    assert by_id["A"]["v15_median_rank_score"] == 1.0
    assert by_id["B"]["component_ranks_zero_based"] == [1, 0, 0]
    assert by_id["B"]["v15_median_rank_score"] == 0.0


def test_low_density_adaptive_cardinality():
    scan = scans(50)[2022]
    fam = family("F", 0.0)
    sizes = []
    for cap in a.COMPONENT_CAPS:
        episode, meta = a.adaptive_local_episode(
            fam, 2022, scan, cap=cap, runtime=Runtime, base=Base
        )
        sizes.append(meta["episode_size"])
        assert len(episode.vg) == meta["episode_size"]
    assert sizes == [50, 50, 50]


def test_nested_caps_at_intermediate_density():
    scan = scans(100)[2022]
    fam = family("F", 0.0)
    sizes = [
        a.adaptive_local_episode(fam, 2022, scan, cap=cap, runtime=Runtime, base=Base)[1]["episode_size"]
        for cap in a.COMPONENT_CAPS
    ]
    assert sizes == [100, 96, 64]


def test_end_to_end_pretruth_application():
    out = a.run_pretruth(
        years=(2022, 2023),
        scan_by_year=scans(),
        family_builder=builder,
        runtime=Runtime,
        base=Base,
        score_episode=score_episode,
    )
    assert out["method"] == "orbittrace_multiscale_consensus_v15_nominal128_canonical_application"
    assert out["component_caps"] == [128, 96, 64]
    assert out["family_count"] == 3
    assert len(out["v15_order"]) == 3
    assert len(set(out["v15_order"])) == 3
    assert out["labels_read"] is False
    assert out["survey_conditioned_science"] is False
    assert all(
        summary["max_brown_equivalence_difference"] <= 1e-10
        for summary in out["component_summaries"].values()
    )


def test_truth_and_year_mismatch_rejected():
    bad = scans()
    bad[2022][0]["truth"] = "SECRET"
    expect_fail(lambda: a.validate_pair((2022, 2023), bad), "truth-bearing key")
    bad = scans()
    bad[2022][0]["year"] = 2023
    expect_fail(lambda: a.validate_pair((2022, 2023), bad), "stored under")


def test_fewer_than_four_local_events_fails_closed():
    tiny = scans(3)[2022]
    expect_fail(
        lambda: a.adaptive_local_episode(
            family("F", 0.0), 2022, tiny, cap=128, runtime=Runtime, base=Base
        ),
        "fewer than four local events",
    )


if __name__ == "__main__":
    test_exact_consensus_reference_rule()
    test_low_density_adaptive_cardinality()
    test_nested_caps_at_intermediate_density()
    test_end_to_end_pretruth_application()
    test_truth_and_year_mismatch_rejected()
    test_fewer_than_four_local_events_fails_closed()
    print("PASS_ORBITTRACE_V15_CANONICAL_APPLICATION_SYNTHETIC")
