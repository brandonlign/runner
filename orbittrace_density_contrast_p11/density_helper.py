#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

P11_ALPHA = 0.10


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def nearest_other_squared(tree: cKDTree, rows: np.ndarray) -> np.ndarray:
    rows = np.asarray(rows, dtype=np.float64)
    require(rows.ndim == 2 and rows.shape[1] == 2 and len(rows) >= 2, "P11 nearest-other invalid rows")
    distance, index = tree.query(rows, k=2, p=2, eps=0.0, workers=1)
    own = np.arange(len(rows), dtype=np.int64)
    # With no exact duplicate the self row is distance zero and we use neighbor 2.
    # With exact duplicate ties, if another row is returned first its distance zero
    # is already the correct nearest-other distance regardless of self tie order.
    chosen = np.where(index[:, 0] == own, distance[:, 1], distance[:, 0])
    out = np.square(chosen, dtype=np.float64)
    require(np.all(np.isfinite(out)), "P11 nearest-other produced non-finite squared distance")
    return out


def density_contrast_scores(
    positive_z: np.ndarray,
    unlabeled_z: np.ndarray,
    unlabeled_ids: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    positive_z = np.asarray(positive_z, dtype=np.float64)
    unlabeled_z = np.asarray(unlabeled_z, dtype=np.float64)
    require(positive_z.ndim == 2 and positive_z.shape[1] == 2 and len(positive_z) >= 4, "P11 invalid positive array")
    require(unlabeled_z.ndim == 2 and unlabeled_z.shape[1] == 2 and len(unlabeled_z) >= 2, "P11 invalid unlabeled array")
    require(len(unlabeled_ids) == len(unlabeled_z), "P11 unlabeled ID mismatch")
    require(np.all(np.isfinite(positive_z)) and np.all(np.isfinite(unlabeled_z)), "P11 non-finite standardized features")

    order = np.argsort(np.asarray(unlabeled_ids, dtype=str), kind="stable")
    zu = unlabeled_z[order]
    ids = [str(unlabeled_ids[int(i)]) for i in order]
    require(len(set(ids)) == len(ids), "P11 unlabeled IDs not unique")

    positive_tree = cKDTree(positive_z)
    unlabeled_tree = cKDTree(zu)

    seed_positive2 = nearest_other_squared(positive_tree, positive_z)
    seed_unlabeled_distance = unlabeled_tree.query(positive_z, k=1, p=2, eps=0.0, workers=1)[0]
    seed_unlabeled2 = np.square(seed_unlabeled_distance, dtype=np.float64)
    seed_scores = np.empty(len(positive_z), dtype=np.float64)
    seed_zero = seed_unlabeled2 == 0.0
    seed_scores[seed_zero] = np.inf
    seed_scores[~seed_zero] = seed_positive2[~seed_zero] / seed_unlabeled2[~seed_zero]

    candidate_positive_distance = positive_tree.query(zu, k=1, p=2, eps=0.0, workers=1)[0]
    candidate_positive2 = np.square(candidate_positive_distance, dtype=np.float64)
    candidate_unlabeled2 = nearest_other_squared(unlabeled_tree, zu)
    candidate_scores = np.empty(len(zu), dtype=np.float64)
    candidate_zero = candidate_unlabeled2 == 0.0
    candidate_scores[candidate_zero] = np.inf
    candidate_scores[~candidate_zero] = candidate_positive2[~candidate_zero] / candidate_unlabeled2[~candidate_zero]

    require(np.all(np.isfinite(seed_scores) | np.isposinf(seed_scores)), "P11 invalid seed nonconformity")
    require(np.all(np.isfinite(candidate_scores) | np.isposinf(candidate_scores)), "P11 invalid candidate nonconformity")
    return seed_scores, candidate_scores, candidate_zero, ids


def finite_sample_threshold(seed_scores: np.ndarray) -> tuple[int, float]:
    seed_scores = np.asarray(seed_scores, dtype=np.float64)
    n = len(seed_scores)
    require(n >= 4, "P11 needs >=4 heldout recurrent seeds")
    k = max(1, int(math.floor(P11_ALPHA * (n + 1))))
    require(1 <= k <= n, "P11 invalid inherited exclusion rank")
    ordered = np.sort(seed_scores)
    return k, float(ordered[n - k])


def candidate_passes(candidate_score: float, zero_denominator: bool, threshold: float) -> bool:
    if bool(zero_denominator):
        return False
    return bool(candidate_score <= threshold)


def self_test() -> dict[str, bool]:
    passed: dict[str, bool] = {}

    for n, expected in ((4, 1), (8, 1), (9, 1), (18, 1), (19, 2), (29, 3), (99, 10), (236, 23)):
        rank, _ = finite_sample_threshold(np.arange(n, dtype=np.float64))
        require(rank == expected, f"P11 rank mismatch n={n}: {rank} != {expected}")
    passed["exact_inherited_rank_formula"] = True

    positive = np.asarray(((0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)), dtype=np.float64)
    unlabeled = np.asarray(((3.0, 3.0), (3.0, 4.0), (4.0, 3.0), (4.0, 4.0)), dtype=np.float64)
    ids = ["d", "b", "a", "c"]
    seed1, candidate1, zero1, order1 = density_contrast_scores(positive, unlabeled, ids)
    perm = (2, 0, 3, 1)
    seed2, candidate2, zero2, order2 = density_contrast_scores(
        positive,
        unlabeled[list(perm)],
        [ids[i] for i in perm],
    )
    require(order1 == order2, "P11 stable-ID order changed under input permutation")
    require(np.array_equal(seed1, seed2), "P11 seed score changed under unlabeled input permutation")
    require(np.array_equal(candidate1, candidate2), "P11 candidate score changed under unlabeled input permutation")
    require(np.array_equal(zero1, zero2), "P11 zero flag changed under unlabeled input permutation")
    passed["stable_id_permutation_invariance"] = True

    require(np.all(~zero1) and np.all(np.isfinite(candidate1)), "P11 ordinary self-exclusion failed")
    passed["candidate_self_exclusion"] = True

    duplicate_unlabeled = np.asarray(((3.0, 3.0), (3.0, 3.0), (4.0, 3.0), (4.0, 4.0)), dtype=np.float64)
    _, duplicate_candidate, duplicate_zero, duplicate_ids = density_contrast_scores(
        positive,
        duplicate_unlabeled,
        ["x2", "x1", "x3", "x4"],
    )
    for target in ("x1", "x2"):
        idx = duplicate_ids.index(target)
        require(duplicate_zero[idx], "P11 exact duplicate did not produce zero nearest-other denominator")
        require(not candidate_passes(float(duplicate_candidate[idx]), True, math.inf), "P11 zero-denominator candidate escaped infinite threshold")
    passed["duplicate_zero_denominator_rejection"] = True

    seed_duplicate_unlabeled = np.asarray(((0.0, 0.0), (3.0, 3.0), (4.0, 3.0), (4.0, 4.0)), dtype=np.float64)
    seed_score, candidate_score, candidate_zero, _ = density_contrast_scores(
        positive,
        seed_duplicate_unlabeled,
        ["a", "b", "c", "d"],
    )
    _, threshold = finite_sample_threshold(seed_score)
    require(math.isinf(threshold), "P11 seed zero denominator did not create conservative infinite rank-one threshold")
    for score, zero in zip(candidate_score.tolist(), candidate_zero.tolist()):
        require(candidate_passes(float(score), bool(zero), threshold) == (not bool(zero)), "P11 infinite-threshold semantics changed")
    passed["infinite_threshold_semantics"] = True

    seed3, candidate3, zero3, order3 = density_contrast_scores(positive * 7.0, unlabeled * 7.0, ids)
    require(order3 == order1 and np.array_equal(zero3, zero1), "P11 common scale changed identities/zero flags")
    require(np.allclose(seed1, seed3, rtol=0.0, atol=2e-15), "P11 seed ratio changed under common scale")
    require(np.allclose(candidate1, candidate3, rtol=0.0, atol=2e-15), "P11 candidate ratio changed under common scale")
    passed["density_ratio_common_scale_invariance"] = True

    return passed


if __name__ == "__main__":
    print(self_test())
