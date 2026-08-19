from __future__ import annotations

from typing import Iterable

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as parent


def geometric_joint_stability(
    tree: np.ndarray,
    years: Iterable[int],
) -> tuple[
    dict[float, float],
    dict[float, float],
    dict[float, float],
    dict[int, tuple[float, float]],
]:
    """Return parameter-free geometric joint ordinary/recurrent EOM stability.

    S_geo(C) = sqrt(S_ord(C) * S_rec(C)).
    The condensed hierarchy is read-only. Positive global rescaling of either
    input stability axis multiplies all joint scores by a common factor and does
    not change standard EOM selection or ranking.
    """
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError("year vector must align exactly with condensed-tree input points")
    if len(np.unique(years_arr)) != 2:
        raise ValueError("geometric joint EOM requires exactly two observing years")

    ordinary_raw = compute_stability(tree)
    ordinary = {float(k): float(v) for k, v in ordinary_raw.items()}
    recurrent, annual = parent.recurrent_stability(tree, years_arr)
    recurrent = {float(k): float(v) for k, v in recurrent.items()}

    if set(ordinary) != set(recurrent):
        raise RuntimeError("ordinary/recurrent stability node universes differ")

    joint: dict[float, float] = {}
    for node in ordinary:
        so = ordinary[node]
        sr = recurrent[node]
        if not np.isfinite(so) or not np.isfinite(sr) or so < 0.0 or sr < 0.0:
            raise RuntimeError(f"invalid stability at node {node}: ordinary={so}, recurrent={sr}")
        value = float(np.sqrt(so * sr))
        if not np.isfinite(value) or value < 0.0:
            raise RuntimeError(f"invalid geometric stability at node {node}: {value}")
        joint[node] = value

    return joint, ordinary, recurrent, annual
