#!/usr/bin/env python3
from __future__ import annotations

import json
import math

import numpy as np

from local_bic import bic_quality_from_evidence, common_log_persistence, local_bic_stability


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def synthetic_tree(scale: float = 1.0) -> np.ndarray:
    dtype = np.dtype([
        ("parent", np.intp),
        ("child", np.intp),
        ("lambda_val", float),
        ("child_size", np.intp),
    ])
    # Eight points => HDBSCAN root ID 8. Two four-point child clusters are
    # born at lambda=1 and their points leave at lambda=2. Cluster 9 is
    # exactly year-balanced; cluster 10 is 3:1. Multiplying every lambda by
    # scale must leave local-BIC evidence exactly unchanged.
    rows = [
        (8, 9, 1.0 * scale, 4),
        (8, 10, 1.0 * scale, 4),
        (9, 0, 2.0 * scale, 1),
        (9, 1, 2.0 * scale, 1),
        (9, 2, 2.0 * scale, 1),
        (9, 3, 2.0 * scale, 1),
        (10, 4, 2.0 * scale, 1),
        (10, 5, 2.0 * scale, 1),
        (10, 6, 2.0 * scale, 1),
        (10, 7, 2.0 * scale, 1),
    ]
    return np.asarray(rows, dtype=dtype)


def main() -> int:
    ln2 = math.log(2.0)

    # Algebraic invariants of the frozen common-evidence and BIC formula.
    req(common_log_persistence(5.0, 5.0) == 10.0, "equality must preserve pooled evidence")
    req(common_log_persistence(5.0, 0.0) == 0.0, "one-year-only evidence must collapse to zero")
    req(common_log_persistence(3.0, 7.0) < 10.0, "imbalance must shrink common evidence")
    req(common_log_persistence(3.0, 7.0) == common_log_persistence(7.0, 3.0), "year swap changed common evidence")
    req(bic_quality_from_evidence(2.0, 8) > bic_quality_from_evidence(1.0, 8), "quality not monotone in evidence")
    req(bic_quality_from_evidence(0.0, 8) < 0.0, "zero-evidence node must have negative quality")

    years = np.asarray([2022, 2022, 2023, 2023, 2022, 2022, 2022, 2023], dtype=np.int64)
    q1, e1 = local_bic_stability(synthetic_tree(1.0), years)
    q7, e7 = local_bic_stability(synthetic_tree(7.25), years)

    # Root quality is mechanically present but root is excluded by the frozen
    # allow_single_cluster=False extraction path.
    req(q1[8.0] == 0.0 and q7[8.0] == 0.0, "root quality changed")
    req(set(e1) == {9, 10}, f"unexpected synthetic evidence nodes: {sorted(e1)}")
    req(set(e7) == {9, 10}, "scaled tree changed evidence-node set")

    # Exact positive scaling of all density lambdas cancels from every ratio.
    for node in (9, 10):
        a = e1[node]
        b = e7[node]
        req(a.year_counts == b.year_counts, "scale changed annual counts")
        req(np.allclose(a.annual_log_persistence, b.annual_log_persistence, rtol=0.0, atol=2e-15),
            "scale changed annual log persistence")
        req(math.isclose(a.common_log_persistence, b.common_log_persistence, rel_tol=0.0, abs_tol=2e-15),
            "scale changed common evidence")
        req(math.isclose(a.bic_quality, b.bic_quality, rel_tol=0.0, abs_tol=2e-14),
            "scale changed BIC quality")

    balanced = e1[9]
    imbalanced = e1[10]
    req(balanced.year_counts == (2, 2), f"balanced counts wrong: {balanced.year_counts}")
    req(imbalanced.year_counts == (3, 1), f"imbalanced counts wrong: {imbalanced.year_counts}")
    req(np.allclose(balanced.annual_log_persistence, (2 * ln2, 2 * ln2)), "balanced annual evidence wrong")
    req(balanced.common_log_persistence > imbalanced.common_log_persistence,
        "balanced recurrence did not outrank same-persistence imbalanced recurrence")
    req(balanced.bic_quality > imbalanced.bic_quality, "balanced recurrence did not improve BIC quality")

    out = {
        "verdict": "PASS_RECURRENT_LOCAL_BIC_HDBSCAN_V1_SYNTHETIC_AUDIT",
        "intrinsic_dimension": 4,
        "scale_invariance_checked": True,
        "one_year_only_negative_quality_checked": True,
        "balanced_common_evidence": balanced.common_log_persistence,
        "imbalanced_common_evidence": imbalanced.common_log_persistence,
        "balanced_bic_quality": balanced.bic_quality,
        "imbalanced_bic_quality": imbalanced.bic_quality,
        "gmn_access": False,
        "truth_access": False,
        "sonotaco_access": False,
        "target_information_access": False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
