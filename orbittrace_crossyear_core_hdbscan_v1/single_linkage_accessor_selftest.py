from __future__ import annotations

from importlib.metadata import version
import json
from pathlib import Path

import hdbscan
import numpy as np

from orbittrace_crossyear_core_hdbscan_v1.single_linkage_accessor_compat import (
    install_single_linkage_raw_tree_compat,
)


def main() -> None:
    rng = np.random.default_rng(20260814)
    X = np.vstack(
        [
            rng.normal(loc=-0.5, scale=0.05, size=(24, 6)),
            rng.normal(loc=0.5, scale=0.05, size=(24, 6)),
            rng.uniform(-1.5, 1.5, size=(12, 6)),
        ]
    )
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)

    wrapper_before = model.single_linkage_tree_
    if hasattr(wrapper_before, "_raw_tree"):
        raise AssertionError("expected hdbscan 0.8.43 SingleLinkageTree to lack _raw_tree before compatibility install")

    public_export = np.asarray(wrapper_before.to_numpy())
    estimator_raw = np.asarray(model._single_linkage_tree)
    if public_export.shape != estimator_raw.shape:
        raise AssertionError("to_numpy shape differs from estimator raw linkage")
    if public_export.dtype != estimator_raw.dtype:
        raise AssertionError("to_numpy dtype differs from estimator raw linkage")
    if not np.array_equal(public_export, estimator_raw):
        raise AssertionError("to_numpy is not bit-identical to estimator raw linkage")

    # Prove to_numpy is a copy rather than a mutable view of estimator state.
    if public_export.size:
        copy_mutation = public_export.copy()
        copy_mutation.flat[0] += 1.0
        if np.array_equal(copy_mutation, estimator_raw):
            raise AssertionError("synthetic mutation unexpectedly changed estimator raw linkage")
        if not np.array_equal(np.asarray(model.single_linkage_tree_.to_numpy()), estimator_raw):
            raise AssertionError("to_numpy mutation leaked into estimator state")

    install_single_linkage_raw_tree_compat()
    wrapper_after = model.single_linkage_tree_
    compat_export = np.asarray(wrapper_after._raw_tree)
    if not np.array_equal(compat_export, estimator_raw):
        raise AssertionError("compatibility _raw_tree is not bit-identical to estimator raw linkage")
    if not np.array_equal(compat_export, np.asarray(wrapper_after.to_numpy())):
        raise AssertionError("compatibility _raw_tree differs from official to_numpy export")

    payload = {
        "verdict": "PASS_CROSSYEAR_CORE_SINGLE_LINKAGE_ACCESSOR_COMPAT_V1",
        "hdbscan_version": version("hdbscan"),
        "shape": list(estimator_raw.shape),
        "dtype": str(estimator_raw.dtype),
        "public_to_numpy_equals_estimator_raw": True,
        "compat_raw_tree_equals_estimator_raw": True,
        "compat_raw_tree_equals_public_to_numpy": True,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "truth_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "orbittrace_target_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    Path("single_linkage_accessor_selftest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
