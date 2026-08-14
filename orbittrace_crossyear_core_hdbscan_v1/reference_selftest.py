from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from reference import (
    K_INHERITED,
    dense_reference,
    opposite_year_core_distances,
)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _ids(n: int, prefix: str) -> list[str]:
    return [f"{prefix}-{i:04d}" for i in range(n)]


def _run_fixture(name: str, X: np.ndarray, years: np.ndarray, ids: list[str]) -> dict:
    out = dense_reference(X, years, ids)
    n = len(ids)
    assert out.core_distances.shape == (n,)
    assert np.all(np.isfinite(out.core_distances))
    assert np.all(out.core_distances >= 0.0)
    assert out.mutual_reachability.shape == (n, n)
    assert np.array_equal(out.mutual_reachability, out.mutual_reachability.T)
    assert np.count_nonzero(np.diag(out.mutual_reachability)) == 0
    assert out.mst_edges.shape == (n - 1, 3)
    assert out.single_linkage_tree.shape[0] == n - 1
    assert out.condensed_tree.shape[0] > 0
    return {
        "name": name,
        "n": n,
        "core_min": float(np.min(out.core_distances)),
        "core_median": float(np.median(out.core_distances)),
        "core_max": float(np.max(out.core_distances)),
        "mst_edges": int(out.mst_edges.shape[0]),
        "single_linkage_rows": int(out.single_linkage_tree.shape[0]),
        "condensed_rows": int(out.condensed_tree.shape[0]),
    }


def recurrent_clusters_plus_noise() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(101)
    blocks = []
    years = []
    ids = []
    for year, offset in [(2022, -0.02), (2023, 0.02)]:
        a = r.normal(loc=np.array([0, 0, 0, 0, 0, 0]) + offset, scale=0.035, size=(18, 6))
        b = r.normal(loc=np.array([0.7, 0.7, 0.2, 0.1, -0.1, 0.3]) + offset, scale=0.035, size=(18, 6))
        noise = r.uniform(-1.2, 1.2, size=(12, 6))
        block = np.vstack([a, b, noise])
        blocks.append(block)
        years.extend([year] * len(block))
        ids.extend(_ids(len(block), f"rec-{year}"))
    return np.vstack(blocks), np.asarray(years), ids


def one_year_only_dense() -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    r = _rng(202)
    # 2022 contains a tight extra structure around +2.0. 2023 has no matching cloud there.
    shared22 = r.normal(0.0, 0.045, size=(22, 6))
    lone22 = r.normal(2.0, 0.012, size=(16, 6))
    noise22 = r.uniform(-1.5, 1.5, size=(12, 6))
    shared23 = r.normal(0.01, 0.045, size=(22, 6))
    noise23 = r.uniform(-1.5, 1.5, size=(28, 6))
    X = np.vstack([shared22, lone22, noise22, shared23, noise23])
    years = np.asarray([2022] * 50 + [2023] * 50)
    ids = _ids(50, "solo-2022") + _ids(50, "solo-2023")
    lone_mask = np.zeros(len(X), dtype=bool)
    lone_mask[22:38] = True
    return X, years, ids, lone_mask


def unequal_year_sizes() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(303)
    X22 = np.vstack([r.normal(-0.3, 0.07, size=(24, 6)), r.uniform(-1, 1, size=(13, 6))])
    X23 = np.vstack([r.normal(-0.28, 0.07, size=(31, 6)), r.uniform(-1, 1, size=(22, 6))])
    X = np.vstack([X22, X23])
    years = np.asarray([2022] * len(X22) + [2023] * len(X23))
    ids = _ids(len(X22), "unequal-2022") + _ids(len(X23), "unequal-2023")
    return X, years, ids


def exact_distance_ties() -> tuple[np.ndarray, np.ndarray, list[str]]:
    # Repeated symmetric rings force exact geometric distance ties while IDs give a fixed tie order.
    ring = np.array(
        [[np.cos(t), np.sin(t), 0.0, 0.0, 0.0, 0.0] for t in np.linspace(0, 2 * np.pi, 12, endpoint=False)],
        dtype=np.float64,
    )
    X22 = np.vstack([ring, ring * 0.5])
    X23 = np.vstack([ring.copy(), ring * 0.5])
    X = np.vstack([X22, X23])
    years = np.asarray([2022] * 24 + [2023] * 24)
    ids = [f"tie22-{i:02d}" for i in range(24)] + [f"tie23-{i:02d}" for i in range(24)]
    return X, years, ids


def nested_density() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(505)
    blocks = []
    years = []
    ids = []
    for year, shift in [(2022, 0.0), (2023, 0.015)]:
        core = r.normal(shift, 0.018, size=(16, 6))
        shell = r.normal(shift, 0.12, size=(28, 6))
        background = r.uniform(-1.0, 1.0, size=(14, 6))
        block = np.vstack([core, shell, background])
        blocks.append(block)
        years.extend([year] * len(block))
        ids.extend(_ids(len(block), f"nested-{year}"))
    return np.vstack(blocks), np.asarray(years), ids


def main() -> None:
    results = []

    X, y, ids = recurrent_clusters_plus_noise()
    results.append(_run_fixture("recurrent_clusters_plus_noise", X, y, ids))

    X, y, ids, lone = one_year_only_dense()
    cores = opposite_year_core_distances(X, y, ids, k=K_INHERITED)
    shared22 = np.zeros(len(X), dtype=bool)
    shared22[:22] = True
    # The one-year-only tight cloud must not receive a tight density scale merely because it is dense in 2022.
    if not float(np.median(cores[lone])) > 3.0 * float(np.median(cores[shared22])):
        raise AssertionError("cross-year core distance did not suppress the one-year-only dense cloud")
    rec = _run_fixture("one_year_only_dense", X, y, ids)
    rec["one_year_core_ratio"] = float(np.median(cores[lone]) / np.median(cores[shared22]))
    results.append(rec)

    X, y, ids = unequal_year_sizes()
    results.append(_run_fixture("unequal_year_sizes", X, y, ids))

    X, y, ids = exact_distance_ties()
    first = dense_reference(X, y, ids)
    second = dense_reference(X, y, ids)
    if not np.array_equal(first.core_distances, second.core_distances):
        raise AssertionError("tie fixture core distances are not deterministic")
    if not np.array_equal(first.mst_edges, second.mst_edges):
        raise AssertionError("tie fixture MST is not deterministic")
    results.append(_run_fixture("exact_distance_ties", X, y, ids))

    X, y, ids = nested_density()
    results.append(_run_fixture("nested_density", X, y, ids))

    payload = {
        "verdict": "PASS_CROSSYEAR_CORE_DENSE_REFERENCE_SYNTHETIC_AUDIT",
        "k": K_INHERITED,
        "fixtures": results,
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "amos_access": False,
        "target_access": False,
    }
    Path("crossyear_core_reference_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
