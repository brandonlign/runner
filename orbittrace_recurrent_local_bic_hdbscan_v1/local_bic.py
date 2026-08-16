from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import _birth_lambdas, _descendant_year_counts


INTRINSIC_DIMENSION = 4


@dataclass(frozen=True)
class LocalBICEvidence:
    node_id: int
    birth_lambda: float
    year_counts: tuple[int, int]
    annual_log_persistence: tuple[float, float]
    common_log_persistence: float
    log_likelihood_ratio: float
    bic_quality: float


def common_log_persistence(a: float, b: float) -> float:
    """Twice-harmonic common evidence, preserving pooled evidence at equality."""
    a = float(a)
    b = float(b)
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("annual log-persistence evidence must be finite")
    if a < 0.0 or b < 0.0:
        raise ValueError("annual log-persistence evidence must be nonnegative")
    if a == 0.0 or b == 0.0:
        return 0.0
    return float(4.0 * a * b / (a + b))


def bic_quality_from_evidence(common: float, support: int, intrinsic_dimension: int = INTRINSIC_DIMENSION) -> float:
    common = float(common)
    support = int(support)
    intrinsic_dimension = int(intrinsic_dimension)
    if not math.isfinite(common) or common < 0.0:
        raise ValueError("common evidence must be finite and nonnegative")
    if support <= 0:
        raise ValueError("support must be positive")
    if intrinsic_dimension <= 0:
        raise ValueError("intrinsic dimension must be positive")
    log_lr = intrinsic_dimension * common
    return float(2.0 * log_lr - math.log(float(support)))


def local_bic_stability(
    tree: np.ndarray,
    years: Iterable[int],
    intrinsic_dimension: int = INTRINSIC_DIMENSION,
) -> tuple[dict[float, float], dict[int, LocalBICEvidence]]:
    """Compute the frozen scale-invariant recurrent local-BIC FOSC quality.

    The HDBSCAN condensed tree supplies a local birth density for every cluster.
    Each departing point/branch contributes its year-specific descendant count
    times log(lambda_exit/lambda_birth). Absolute density scale therefore cancels.
    Annual evidence is combined by the frozen twice-harmonic common-evidence rule,
    then converted to a one-extra-density-parameter BIC-style local quality.
    """
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError(f"year vector shape {years_arr.shape} does not match tree point count {root}")
    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(year_values) != 2:
        raise ValueError(f"local-BIC v1 requires exactly two years, got {year_values}")
    y_index = {y: i for i, y in enumerate(year_values)}

    births = _birth_lambdas(tree)
    counts = _descendant_year_counts(tree, years_arr)
    parents = sorted(set(int(x) for x in tree["parent"]))
    annual = {p: np.zeros(2, dtype=np.float64) for p in parents}

    for parent, child, lam, child_size in tree:
        p = int(parent)
        c = int(child)
        lam = float(lam)
        child_size = int(child_size)
        if not math.isfinite(lam):
            raise RuntimeError(f"nonfinite exit lambda at parent={p} child={c}")

        if c < root:
            branch_counts = np.asarray([int(years_arr[c] == y) for y in year_values], dtype=np.int64)
        else:
            if c not in counts:
                raise RuntimeError(f"missing descendant counts for cluster child {c}")
            branch_counts = counts[c]
        if int(branch_counts.sum()) != child_size:
            raise RuntimeError(
                f"condensed-tree descendant accounting mismatch child={c}: "
                f"{int(branch_counts.sum())} != {child_size}"
            )

        # Root is excluded by allow_single_cluster=False and has birth lambda zero.
        if p == root:
            continue
        birth = float(births[p])
        if not math.isfinite(birth) or birth <= 0.0:
            raise RuntimeError(f"non-root cluster has invalid birth lambda: node={p} birth={birth}")
        if lam + 1e-15 < birth:
            raise RuntimeError(f"exit lambda below birth lambda: node={p} birth={birth} exit={lam}")
        if lam <= birth:
            continue
        log_ratio = math.log(lam / birth)
        if not math.isfinite(log_ratio) or log_ratio < 0.0:
            raise RuntimeError(f"invalid local log-persistence: node={p} value={log_ratio}")
        annual[p] += log_ratio * branch_counts

    quality: dict[float, float] = {}
    evidence: dict[int, LocalBICEvidence] = {}
    for p in parents:
        if p == root:
            # HDBSCAN excludes the root from selection when allow_single_cluster=False.
            quality[float(p)] = 0.0
            continue
        if p not in counts:
            raise RuntimeError(f"missing node support counts for parent {p}")
        n1, n2 = (int(x) for x in counts[p])
        support = n1 + n2
        if support <= 0:
            raise RuntimeError(f"non-root node has zero support: {p}")
        l1, l2 = (float(x) for x in annual[p])
        common = common_log_persistence(l1, l2)
        log_lr = float(int(intrinsic_dimension) * common)
        q = bic_quality_from_evidence(common, support, intrinsic_dimension)
        row = LocalBICEvidence(
            node_id=p,
            birth_lambda=float(births[p]),
            year_counts=(n1, n2),
            annual_log_persistence=(l1, l2),
            common_log_persistence=common,
            log_likelihood_ratio=log_lr,
            bic_quality=q,
        )
        evidence[p] = row
        quality[float(p)] = q

    if set(int(k) for k in quality) != set(parents):
        raise RuntimeError("local-BIC quality dictionary does not cover exact parent-node set")
    return quality, evidence
