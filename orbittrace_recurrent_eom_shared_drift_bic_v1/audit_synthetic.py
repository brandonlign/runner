#!/usr/bin/env python3
from __future__ import annotations

import json

import numpy as np

from shared_drift_bic import (
    aggregate_tree_stats,
    node_drift_bic,
    physical_predictor_and_response,
    shared_drift_stability,
)

DTYPE = np.dtype([
    ("parent", np.int64),
    ("child", np.int64),
    ("lambda_val", np.float64),
    ("child_size", np.int64),
])


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def point_tree(n: int) -> np.ndarray:
    root = n
    return np.asarray([(root, i, 1.0 + i / 10.0, 1) for i in range(n)], dtype=DTYPE)


def two_child_tree() -> np.ndarray:
    # 12 points, root 12, two cluster children 13/14 with six points each.
    rows = [(12, 13, 1.0, 6), (12, 14, 1.0, 6)]
    rows += [(13, i, 2.0 + i / 100.0, 1) for i in range(6)]
    rows += [(14, i, 2.0 + i / 100.0, 1) for i in range(6, 12)]
    return np.asarray(rows, dtype=DTYPE)


def linear_fixture(shared: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u_one = np.arange(6, dtype=float)
    u = np.concatenate([u_one, u_one])
    years = np.asarray([2022] * 6 + [2023] * 6, dtype=np.int64)
    intercept = np.asarray([0.2, -0.1, 0.4, 3.0])
    slope = np.asarray([0.03, -0.02, 0.01, 0.04])
    noise = np.asarray([
        [0.010, -0.020, 0.015, -0.010],
        [-0.015, 0.010, -0.005, 0.020],
        [0.020, 0.015, -0.010, -0.015],
        [-0.010, -0.005, 0.020, 0.010],
        [0.005, 0.020, -0.015, -0.005],
        [-0.020, -0.010, 0.005, 0.015],
    ])
    y0 = intercept + u_one[:, None] * slope + noise
    y1 = intercept + u_one[:, None] * slope + noise[::-1]
    if not shared:
        y1 = y1 + np.asarray([1.5, -1.2, 0.9, 0.7])
    return u, np.vstack([y0, y1]), years


def main() -> int:
    # Exact bottom-up sufficient-statistic aggregation.
    tree = two_child_tree()
    u = np.linspace(0.0, 5.5, 12)
    Y = np.column_stack((u + 1.0, 2.0 * u - 0.5, -0.25 * u + 2.0, np.log(u + 2.0)))
    years = np.asarray([2022, 2023, 2022, 2023, 2022, 2023, 2023, 2022, 2023, 2022, 2023, 2022])
    stats = aggregate_tree_stats(tree, years, u, Y)
    i13 = stats.index(13)
    i14 = stats.index(14)
    i12 = stats.index(12)
    req(tuple(stats.n[i13]) == (3, 3), "child-13 annual counts wrong")
    req(tuple(stats.n[i14]) == (3, 3), "child-14 annual counts wrong")
    req(tuple(stats.n[i12]) == (6, 6), "root annual counts wrong")
    req(abs(stats.sum_u[i13].sum() - float(u[:6].sum())) < 1e-12, "child-13 sum_u wrong")
    req(abs(stats.sum_u[i14].sum() - float(u[6:].sum())) < 1e-12, "child-14 sum_u wrong")
    req(np.allclose(stats.sum_y[i12].sum(axis=0), Y.sum(axis=0), rtol=0, atol=1e-12), "root sum_y wrong")
    req(np.allclose(stats.sum_y2[i12].sum(axis=0), (Y * Y).sum(axis=0), rtol=0, atol=1e-12), "root sum_y2 wrong")

    # Shared annual trajectory should be favored solely by BIC complexity penalty.
    us, Ys, yrs = linear_fixture(shared=True)
    shared_stats = aggregate_tree_stats(point_tree(len(us)), yrs, us, Ys)
    shared_ev = node_drift_bic(shared_stats, len(us))
    req(shared_ev.identifiable, "shared fixture unexpectedly unidentifiable")
    req(shared_ev.delta_bic is not None and shared_ev.delta_bic > 0.0, "shared fixture should favor one trajectory")
    req(shared_ev.shared_weight > 0.5, "shared fixture BIC weight should exceed 0.5")

    # A large year-specific intercept displacement should justify separate trajectories.
    ud, Yd, yrd = linear_fixture(shared=False)
    diff_stats = aggregate_tree_stats(point_tree(len(ud)), yrd, ud, Yd)
    diff_ev = node_drift_bic(diff_stats, len(ud))
    req(diff_ev.identifiable, "different-trajectory fixture unexpectedly unidentifiable")
    req(diff_ev.delta_bic is not None and diff_ev.delta_bic < 0.0, "different trajectories should favor annual models")
    req(diff_ev.shared_weight < 0.5, "different-trajectory BIC weight should be below 0.5")
    req(shared_ev.shared_weight > diff_ev.shared_weight, "BIC evidence direction reversed")

    # Year-name swap invariance.
    swapped = np.where(yrd == 2022, 2023, 2022)
    swapped_stats = aggregate_tree_stats(point_tree(len(ud)), swapped, ud, Yd)
    swapped_ev = node_drift_bic(swapped_stats, len(ud))
    req(abs(swapped_ev.shared_weight - diff_ev.shared_weight) < 1e-12, "year swap changed shared weight")
    req(abs(float(swapped_ev.delta_bic) - float(diff_ev.delta_bic)) < 1e-10, "year swap changed Delta BIC")

    # Identifiability is mathematical: fewer than three points in one year -> weight zero.
    tiny_years = np.asarray([2022, 2022] + [2023] * 6, dtype=np.int64)
    tiny_u = np.arange(8, dtype=float)
    tiny_Y = np.column_stack((tiny_u, tiny_u**2 + 1.0, np.sin(tiny_u), np.log(tiny_u + 2.0)))
    tiny_stats = aggregate_tree_stats(point_tree(8), tiny_years, tiny_u, tiny_Y)
    tiny_ev = node_drift_bic(tiny_stats, 8)
    req(not tiny_ev.identifiable and tiny_ev.shared_weight == 0.0, "unidentifiable annual model must receive zero weight")

    # Stability multiplication is exact and cannot introduce new nodes/keys.
    rec = {float(len(us)): 0.25}
    st, ev = shared_drift_stability(rec, shared_stats)
    req(set(st) == set(rec), "shared-drift stability changed node keys")
    req(abs(st[float(len(us))] - 0.25 * shared_ev.shared_weight) < 1e-15, "stability product changed")
    req(ev[len(us)] == shared_ev, "shared-drift evidence changed between direct and batch paths")

    # Physical coordinate mapping sanity.
    sol = np.asarray([60.0, 70.0])
    lon = np.asarray([0.0, 90.0])
    lat = np.asarray([0.0, 0.0])
    vg = np.asarray([20.0, 40.0])
    up, Yp = physical_predictor_and_response(sol, lon, lat, vg)
    req(np.allclose(up, [0.5, 1.5]), "accessible solar-longitude unwrap changed")
    req(np.allclose(Yp[0, :3], [1.0, 0.0, 0.0], atol=1e-15), "radiant unit-vector mapping changed")
    req(np.allclose(Yp[1, :3], [0.0, 1.0, 0.0], atol=1e-15), "radiant longitude mapping changed")

    result = {
        "verdict": "PASS_RECURRENT_EOM_SHARED_DRIFT_BIC_V1_SYNTHETIC_AUDIT",
        "shared_fixture": shared_ev.__dict__,
        "different_fixture": diff_ev.__dict__,
        "unidentifiable_fixture": tiny_ev.__dict__,
        "assertions": {
            "bottom_up_sufficient_statistics": True,
            "shared_trajectory_bic_direction": True,
            "different_trajectory_bic_direction": True,
            "year_swap_invariance": True,
            "identifiability_rule": True,
            "exact_stability_product": True,
            "physical_coordinate_mapping": True,
        },
        "scientific_data_access": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
