from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import condense_tree

from boruvka_adapter import exact_crossyear_boruvka_mst
from reference import dense_reference
from reference_selftest import (
    exact_distance_ties,
    nested_density,
    one_year_only_dense,
    recurrent_clusters_plus_noise,
    unequal_year_sizes,
)
from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability


ABS_TOL = 1.0e-12  # frozen before any GMN execution


class _UF:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))
        self.r = [0] * n

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.r[a] < self.r[b]:
            a, b = b, a
        self.p[b] = a
        if self.r[a] == self.r[b]:
            self.r[a] += 1


def _canonical_components(n: int, mst: np.ndarray, threshold: float) -> tuple[tuple[int, ...], ...]:
    uf = _UF(n)
    for a, b, w in mst:
        if float(w) <= threshold:
            uf.union(int(a), int(b))
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(i)
    return tuple(sorted(tuple(v) for v in groups.values()))


def _filtration_equivalent(n: int, ref_mst: np.ndarray, opt_mst: np.ndarray) -> None:
    ref_weights = np.sort(np.asarray(ref_mst[:, 2], dtype=np.float64))
    opt_weights = np.sort(np.asarray(opt_mst[:, 2], dtype=np.float64))
    if not np.allclose(ref_weights, opt_weights, rtol=0.0, atol=ABS_TOL):
        raise AssertionError("MST edge-weight multisets differ")

    # Compare connectivity after every complete equal-weight Kruskal layer.
    i = 0
    while i < len(ref_weights):
        j = i + 1
        while j < len(ref_weights) and ref_weights[j] == ref_weights[i]:
            j += 1
        ref_t = float(ref_weights[j - 1])
        opt_t = float(opt_weights[j - 1]) + ABS_TOL
        ref_sig = _canonical_components(n, ref_mst, ref_t + ABS_TOL)
        opt_sig = _canonical_components(n, opt_mst, opt_t)
        if ref_sig != opt_sig:
            raise AssertionError(f"MST connectivity filtration differs at layer {i}:{j}")
        i = j


def _canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(np.asarray(labels, dtype=np.int64)):
        if int(lab) < 0:
            continue
        groups.setdefault(int(lab), []).append(i)
    return tuple(sorted(tuple(v) for v in groups.values()))


def _condensed_from_mst(mst: np.ndarray) -> np.ndarray:
    ordered = np.asarray(mst, dtype=np.float64)[np.argsort(np.asarray(mst)[:, 2], kind="mergesort")]
    single = label(ordered)
    return np.asarray(condense_tree(single, 10))


def _recurrent_partition(tree: np.ndarray, years: np.ndarray) -> tuple[tuple[int, ...], ...]:
    stability, _annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, stability)
    return _canonical_partition(labels)


def _fixture_rows():
    X, y, ids = recurrent_clusters_plus_noise()
    yield "recurrent_clusters_plus_noise", X, y, ids
    X, y, ids, _lone = one_year_only_dense()
    yield "one_year_only_dense", X, y, ids
    X, y, ids = unequal_year_sizes()
    yield "unequal_year_sizes", X, y, ids
    X, y, ids = exact_distance_ties()
    yield "exact_distance_ties", X, y, ids
    X, y, ids = nested_density()
    yield "nested_density", X, y, ids


def main() -> None:
    cases = []
    for name, X, years, ids in _fixture_rows():
        ref = dense_reference(X, years, ids)
        table, opt_mst = exact_crossyear_boruvka_mst(X, years, ids)

        max_core_err = float(np.max(np.abs(ref.core_distances - table.core_distances)))
        if max_core_err > ABS_TOL:
            raise AssertionError(f"{name}: opposite-year core distances differ by {max_core_err}")

        _filtration_equivalent(len(ids), ref.mst_edges, opt_mst)

        ref_tree = ref.condensed_tree
        opt_tree = _condensed_from_mst(opt_mst)
        ref_partition = _recurrent_partition(ref_tree, years)
        opt_partition = _recurrent_partition(opt_tree, years)
        if ref_partition != opt_partition:
            raise AssertionError(f"{name}: recurrent-EOM selected partition differs")

        ref_sizes = np.sort(np.asarray(ref_tree["child_size"], dtype=np.int64))
        opt_sizes = np.sort(np.asarray(opt_tree["child_size"], dtype=np.int64))
        if not np.array_equal(ref_sizes, opt_sizes):
            raise AssertionError(f"{name}: condensed-tree child-size multiset differs")

        ref_lam = np.sort(np.asarray(ref_tree["lambda_val"], dtype=np.float64))
        opt_lam = np.sort(np.asarray(opt_tree["lambda_val"], dtype=np.float64))
        if ref_lam.shape != opt_lam.shape or not np.allclose(ref_lam, opt_lam, rtol=0.0, atol=ABS_TOL, equal_nan=True):
            raise AssertionError(f"{name}: condensed-tree lambda multiset differs")

        cases.append(
            {
                "name": name,
                "n": len(ids),
                "max_core_abs_error": max_core_err,
                "mst_max_weight_abs_error": float(
                    np.max(
                        np.abs(
                            np.sort(ref.mst_edges[:, 2]) - np.sort(opt_mst[:, 2])
                        )
                    )
                ),
                "recurrent_partition_clusters": len(ref_partition),
                "recurrent_partition_identity": True,
                "connectivity_filtration_identity": True,
                "condensed_child_size_multiset_identity": True,
                "condensed_lambda_multiset_identity": True,
            }
        )

    payload = {
        "verdict": "PASS_CROSSYEAR_CORE_BORUVKA_DENSE_EQUIVALENCE_V1",
        "absolute_tolerance": ABS_TOL,
        "cases": cases,
        "boruvka_exact_mst": True,
        "approx_min_span_tree": False,
        "boruvka_n_jobs": 1,
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "amos_access": False,
        "target_access": False,
    }
    Path("crossyear_core_boruvka_equivalence.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
