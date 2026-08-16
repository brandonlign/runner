#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np


def load_base() -> Any:
    path = Path(__file__).with_name("run_diagnostic.py")
    spec = importlib.util.spec_from_file_location("orbittrace_theory_rsl_frozen_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen diagnostic {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_sorted_rsl(X: np.ndarray, *, cut: float, k: int, alpha: float, gamma: int,
                     metric: str, algorithm: str, core_dist_n_jobs: int, **kwargs: Any):
    """Engineering-only replacement for malformed public Boruvka linkage ordering.

    The frozen caller ignores flat labels.  This computes the same frozen
    mutual-reachability hierarchy (k, alpha, Euclidean) through HDBSCAN's exact
    generic path, whose MST is sorted before conversion to linkage.
    """
    if algorithm != "boruvka_kdtree":
        raise RuntimeError(f"frozen caller algorithm changed: {algorithm}")
    if metric != "euclidean":
        raise RuntimeError(f"frozen caller metric changed: {metric}")
    if gamma != 1 or cut != 0.0:
        raise RuntimeError("frozen caller flat-only placeholders changed")
    model = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=int(k),
        alpha=float(alpha),
        metric="euclidean",
        algorithm="generic",
        approx_min_span_tree=False,
        gen_min_span_tree=True,
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        core_dist_n_jobs=1,
        prediction_data=False,
    ).fit(np.asarray(X, dtype=float))
    tree = np.asarray(model.single_linkage_tree_.to_numpy(), dtype=float)
    # The frozen diagnostic ignores the flat labels; return them only to satisfy
    # the public robust_single_linkage call signature it was written against.
    return np.asarray(model.labels_, dtype=np.int64), tree


def main() -> int:
    base = load_base()
    # Replace only the technically malformed linkage-construction call. All
    # frozen science constants, subset logic, metrics and gates remain in base.
    base.hdbscan.robust_single_linkage = exact_sorted_rsl
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
