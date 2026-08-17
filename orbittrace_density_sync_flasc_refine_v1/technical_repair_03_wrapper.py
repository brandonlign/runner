#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import hdbscan
from hdbscan.branch_data import BranchDetectionData
from hdbscan.hdbscan_ import _hdbscan_boruvka_kdtree
from hdbscan.branches import detect_branches_in_clusters as _real_detect_branches

import orbittrace_density_sync_flasc_refine_v1.run_development as frozen

_OriginalHDBSCAN = hdbscan.HDBSCAN


def _ExactParentHDBSCAN(*args, branch_detection_data=False, **kwargs):
    """Construct the real upstream estimator while suppressing only its branch cache.

    This is intentionally a factory rather than an estimator subclass. The frozen
    parent fit is therefore performed by the exact upstream HDBSCAN class and its
    exact sklearn-compatible constructor/get_params implementation.
    """
    clusterer = _OriginalHDBSCAN(*args, branch_detection_data=False, **kwargs)
    clusterer._repair_branch_detection_requested = bool(branch_detection_data)
    return clusterer


def _repair_detect_branches(clusterer, cluster_labels=None, cluster_probabilities=None, **kwargs):
    if not isinstance(clusterer, _OriginalHDBSCAN):
        raise RuntimeError("technical repair wrapper received unexpected clusterer class")
    if not bool(getattr(clusterer, "_repair_branch_detection_requested", False)):
        raise RuntimeError("frozen runner did not request branch detection support")
    if cluster_labels is None:
        raise RuntimeError("technical repair requires explicit exact density-sync winner labels")
    cluster_labels = np.asarray(cluster_labels, dtype=np.int64)
    if cluster_labels.shape != (clusterer._raw_data.shape[0],):
        raise RuntimeError("exact winner label vector does not align with raw GEO6 matrix")

    # Recreate exactly the support objects that HDBSCAN's convenience flag is intended
    # to cache, without allowing that flag to alter the prerequisite parent fit.
    min_samples = clusterer.min_samples or clusterer.min_cluster_size
    if int(min_samples) != 10:
        raise RuntimeError(f"frozen min_samples changed: {min_samples}")
    if clusterer.metric != "euclidean":
        raise RuntimeError(f"frozen metric changed: {clusterer.metric}")
    if clusterer.algorithm != "best":
        raise RuntimeError(f"frozen HDBSCAN algorithm changed: {clusterer.algorithm}")
    if float(clusterer.alpha) != 1.0:
        raise RuntimeError(f"frozen alpha changed: {clusterer.alpha}")
    if int(clusterer.leaf_size) != 40:
        raise RuntimeError(f"frozen leaf_size changed: {clusterer.leaf_size}")
    if bool(clusterer.approx_min_span_tree) is not True:
        raise RuntimeError("frozen approximate-MST setting changed")

    X = np.asarray(clusterer._raw_data, dtype=np.float64)
    _aux_linkage, mst = _hdbscan_boruvka_kdtree(
        X,
        min_samples=int(min_samples),
        alpha=float(clusterer.alpha),
        metric=clusterer.metric,
        p=clusterer.p,
        leaf_size=int(clusterer.leaf_size),
        approx_min_span_tree=bool(clusterer.approx_min_span_tree),
        gen_min_span_tree=True,
        core_dist_n_jobs=int(clusterer.core_dist_n_jobs),
        **clusterer._metric_kwargs,
    )
    if mst is None or mst.shape != (X.shape[0] - 1, 3):
        raise RuntimeError(f"failed to reconstruct mutual-reachability MST: {None if mst is None else mst.shape}")

    clusterer._min_spanning_tree = mst
    clusterer._branch_detection_data = BranchDetectionData(
        X,
        cluster_labels,
        clusterer._condensed_tree,
        int(min_samples),
        tree_type="kdtree",
        metric=clusterer.metric,
        **clusterer._metric_kwargs,
    )
    return _real_detect_branches(
        clusterer,
        cluster_labels=cluster_labels,
        cluster_probabilities=cluster_probabilities,
        **kwargs,
    )


# Patch only the two runtime hooks used by the frozen scientific runner.
frozen.hdbscan.HDBSCAN = _ExactParentHDBSCAN
frozen.detect_branches_in_clusters = _repair_detect_branches


if __name__ == "__main__":
    raise SystemExit(frozen.main())
