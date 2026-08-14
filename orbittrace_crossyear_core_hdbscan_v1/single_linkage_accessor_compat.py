from __future__ import annotations

import numpy as np


def install_single_linkage_raw_tree_compat() -> None:
    """Provide the accessor expected by the already-frozen runner.

    hdbscan.SingleLinkageTree stores the scipy-format linkage in `_linkage` and
    its public `to_numpy()` method returns a copy of that exact array. The
    frozen OrbitTrace runner accidentally requested `_raw_tree`, an attribute
    used by the different CondensedTree wrapper. This shim adds only that
    missing accessor and defines it as the official `to_numpy()` export.
    """
    from hdbscan.plots import SingleLinkageTree

    if hasattr(SingleLinkageTree, "_raw_tree"):
        raise RuntimeError("SingleLinkageTree unexpectedly already defines _raw_tree; compatibility assumptions changed")

    original_to_numpy = SingleLinkageTree.to_numpy

    @property
    def _raw_tree(self):
        exported = np.asarray(original_to_numpy(self))
        internal = np.asarray(self._linkage)
        if exported.shape != internal.shape or exported.dtype != internal.dtype or not np.array_equal(exported, internal):
            raise RuntimeError("SingleLinkageTree.to_numpy() no longer exactly matches internal linkage")
        return exported

    SingleLinkageTree._raw_tree = _raw_tree
