from __future__ import annotations

import numpy as np
from sklearn.neighbors import KDTree
from hdbscan._hdbscan_boruvka import KDTreeBoruvkaAlgorithm
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import condense_tree

MIN_SAMPLES = 10
K_YEAR = 5
LEAF_SIZE = 40
BORUVKA_LEAF_SIZE = LEAF_SIZE // 3
MIN_CLUSTER_SIZE = 10
QUERY_CHUNK = 65536


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def _same_year_fifth_other_distance(
    tree: KDTree,
    X_year: np.ndarray,
    *,
    chunk_size: int = QUERY_CHUNK,
) -> np.ndarray:
    """Distance to fifth nearest *other event* within one year.

    Exact self identity is the row's local tree index. Coordinate duplicates with
    different identities remain valid neighbors. k=6 is sufficient: if exact self
    is present it is discarded; if a tie causes exact self not to appear, at least
    six other events are at the same-or-smaller distance and the fifth-other
    distance is still the fifth returned distance.
    """
    X_year = np.asarray(X_year, dtype=np.float64, order="C")
    n = X_year.shape[0]
    require(n > K_YEAR, "year has insufficient events for frozen k_year=5")
    out = np.empty(n, dtype=np.float64)
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        dist, ind = tree.query(X_year[start:stop], k=K_YEAR + 1, dualtree=True, breadth_first=True)
        for offset in range(stop - start):
            local_self = start + offset
            accepted = [float(d) for d, j in zip(dist[offset], ind[offset]) if int(j) != local_self]
            if len(accepted) >= K_YEAR:
                out[local_self] = accepted[K_YEAR - 1]
            else:
                raise RuntimeError(f"could not obtain fifth other neighbor for local row {local_self}")
    require(np.all(np.isfinite(out)) and np.all(out >= 0.0), "invalid same-year fifth-other distances")
    return out


def _cross_year_fifth_distance(
    reference_tree: KDTree,
    X_query: np.ndarray,
    *,
    chunk_size: int = QUERY_CHUNK,
) -> np.ndarray:
    X_query = np.asarray(X_query, dtype=np.float64, order="C")
    out = np.empty(X_query.shape[0], dtype=np.float64)
    for start in range(0, X_query.shape[0], chunk_size):
        stop = min(start + chunk_size, X_query.shape[0])
        dist, _ = reference_tree.query(X_query[start:stop], k=K_YEAR, dualtree=True, breadth_first=True)
        out[start:stop] = dist[:, K_YEAR - 1]
    require(np.all(np.isfinite(out)) and np.all(out >= 0.0), "invalid cross-year fifth-neighbor distances")
    return out


def stratified_core_distances(X: np.ndarray, years: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Frozen balanced 5+5 annual core-distance construction."""
    X = np.asarray(X, dtype=np.float64, order="C")
    years = np.asarray(years, dtype=np.int64)
    require(X.ndim == 2 and X.shape[0] == years.shape[0], "X/year shape mismatch")
    require(tuple(sorted(int(x) for x in np.unique(years))) == (2022, 2023), "frozen year domain changed")

    mask22 = years == 2022
    mask23 = years == 2023
    X22 = np.asarray(X[mask22], dtype=np.float64, order="C")
    X23 = np.asarray(X[mask23], dtype=np.float64, order="C")
    require(len(X22) > K_YEAR and len(X23) > K_YEAR, "insufficient annual event count")

    tree22 = KDTree(X22, metric="euclidean", leaf_size=LEAF_SIZE)
    tree23 = KDTree(X23, metric="euclidean", leaf_size=LEAF_SIZE)

    d22_for_22 = _same_year_fifth_other_distance(tree22, X22)
    d23_for_22 = _cross_year_fifth_distance(tree23, X22)
    d22_for_23 = _cross_year_fifth_distance(tree22, X23)
    d23_for_23 = _same_year_fifth_other_distance(tree23, X23)

    core = np.empty(len(X), dtype=np.float64)
    core22 = np.empty(len(X), dtype=np.float64)
    core23 = np.empty(len(X), dtype=np.float64)
    core22[mask22] = d22_for_22
    core23[mask22] = d23_for_22
    core22[mask23] = d22_for_23
    core23[mask23] = d23_for_23
    core[:] = np.maximum(core22, core23)

    require(np.all(np.isfinite(core)) and np.all(core >= 0.0), "invalid stratified core distances")
    require(np.all(core >= core22) and np.all(core >= core23), "stratified max invariant failed")
    return core, {"d_2022": core22, "d_2023": core23}


def standard_pooled_core_distances(X: np.ndarray, *, chunk_size: int = QUERY_CHUNK) -> np.ndarray:
    """Exact pooled min_samples=10 Euclidean core distances used by HDBSCAN."""
    X = np.asarray(X, dtype=np.float64, order="C")
    require(X.ndim == 2 and X.shape[0] > MIN_SAMPLES, "invalid X for standard pooled core")
    tree = KDTree(X, metric="euclidean", leaf_size=LEAF_SIZE)
    out = np.empty(X.shape[0], dtype=np.float64)
    for start in range(0, X.shape[0], chunk_size):
        stop = min(start + chunk_size, X.shape[0])
        dist, _ = tree.query(X[start:stop], k=MIN_SAMPLES + 1, dualtree=True, breadth_first=True)
        out[start:stop] = dist[:, MIN_SAMPLES]
    require(np.all(np.isfinite(out)) and np.all(out >= 0.0), "invalid standard pooled core distances")
    return out


def _seed_hdbscan_first_pass(
    alg: KDTreeBoruvkaAlgorithm,
    spatial_tree: KDTree,
    X: np.ndarray,
    injected_rdist: np.ndarray,
) -> int:
    """Recreate HDBSCAN 0.8.43's constructor shortcut under injected cores.

    The constructor was intentionally created with min_samples=0 so it committed
    no first-pass edge. We now seed the exact min_samples=10 shortcut candidates
    into the public arrays. Bounds are set to zero so the first public
    spanning_tree() traversal is a no-op and compiled update_components() consumes
    precisely these candidates.
    """
    _, knn_indices = spatial_tree.query(
        X,
        k=MIN_SAMPLES + 1,
        dualtree=True,
        breadth_first=True,
    )
    candidate_point = np.asarray(alg.candidate_point)
    candidate_neighbor = np.asarray(alg.candidate_neighbor)
    candidate_distance = np.asarray(alg.candidate_distance)
    seeded = 0
    for n in range(X.shape[0]):
        for m_raw in knn_indices[n]:
            m = int(m_raw)
            if n == m:
                continue
            if injected_rdist[m] <= injected_rdist[n]:
                candidate_point[n] = n
                candidate_neighbor[n] = m
                candidate_distance[n] = injected_rdist[n]
                seeded += 1
                break
    bounds = np.asarray(alg.bounds)
    require(bounds.ndim == 1 and len(bounds) > 0, "Boruvka public bounds unavailable")
    bounds[:] = 0.0
    return seeded


def condensed_tree_from_injected_core(
    X: np.ndarray,
    core_distances: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build HDBSCAN hierarchy using frozen externally supplied Euclidean cores."""
    X = np.asarray(X, dtype=np.float64, order="C")
    core = np.asarray(core_distances, dtype=np.float64)
    require(core.shape == (X.shape[0],), "injected core shape mismatch")
    require(np.all(np.isfinite(core)) and np.all(core >= 0.0), "invalid injected core distances")

    spatial_tree = KDTree(X, metric="euclidean", leaf_size=LEAF_SIZE)
    alg = KDTreeBoruvkaAlgorithm(
        spatial_tree,
        0,
        metric="euclidean",
        leaf_size=BORUVKA_LEAF_SIZE,
        alpha=1.0,
        approx_min_span_tree=True,
        n_jobs=1,
    )
    injected_rdist = np.square(core, dtype=np.float64)
    arr = np.asarray(alg.core_distance_arr)
    require(arr.shape == injected_rdist.shape, "Boruvka core-distance array shape changed")
    arr[:] = injected_rdist
    public_view = np.asarray(alg.core_distance)
    require(np.array_equal(public_view, injected_rdist), "in-place core-distance injection did not reach compiled memoryview")

    seeded = _seed_hdbscan_first_pass(alg, spatial_tree, X, injected_rdist)
    require(0 < seeded <= X.shape[0], "injected-core HDBSCAN first-pass seeding failed")

    mst = np.asarray(alg.spanning_tree(), dtype=np.float64)
    require(mst.shape == (X.shape[0] - 1, 3), f"unexpected Boruvka MST shape: {mst.shape}")
    require(np.all(np.isfinite(mst)), "nonfinite injected-core MST")
    row_order = np.argsort(mst.T[2])
    mst = np.asarray(mst[row_order, :], dtype=np.float64, order="C")
    single_linkage = label(mst)
    condensed = condense_tree(single_linkage, MIN_CLUSTER_SIZE)
    return condensed, single_linkage, mst
