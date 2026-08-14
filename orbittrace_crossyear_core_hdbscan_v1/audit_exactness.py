from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_crossyear_core_hdbscan_v1.audit_candidate import audit_candidate
from orbittrace_crossyear_core_hdbscan_v1.reference import dense_reference
from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import (
    eom_labels,
    recurrent_stability,
    selected_eom_nodes,
)


ATOL = 1e-12
K = 10
MIN_CLUSTER_SIZE = 10


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _embed2(points: np.ndarray) -> np.ndarray:
    out = np.zeros((points.shape[0], 6), dtype=np.float64)
    out[:, :2] = points
    return out


def _fixture_recurrent_clusters() -> tuple[np.ndarray, np.ndarray, list[str]]:
    g = _rng(101)
    chunks = []
    years = []
    for yr, shift in ((2022, 0.0), (2023, 0.04)):
        a = g.normal(loc=(-2.0 + shift, 0.0), scale=0.14, size=(24, 2))
        b = g.normal(loc=(2.0 + shift, 0.2), scale=0.18, size=(24, 2))
        noise = g.uniform(low=-5.0, high=5.0, size=(12, 2))
        chunks.extend([a, b, noise])
        years.extend([yr] * 60)
    X = _embed2(np.vstack(chunks))
    ids = [f"RC-{i:04d}" for i in range(X.shape[0])]
    return X, np.asarray(years, dtype=np.int64), ids


def _fixture_one_year_only() -> tuple[np.ndarray, np.ndarray, list[str]]:
    g = _rng(202)
    y22_dense = g.normal(loc=(0.0, 0.0), scale=0.055, size=(34, 2))
    y22_bg = g.uniform(low=-4.0, high=4.0, size=(26, 2))
    y23_diffuse = g.normal(loc=(0.0, 0.0), scale=1.6, size=(34, 2))
    y23_bg = g.uniform(low=-4.0, high=4.0, size=(26, 2))
    X = _embed2(np.vstack([y22_dense, y22_bg, y23_diffuse, y23_bg]))
    years = np.asarray([2022] * 60 + [2023] * 60, dtype=np.int64)
    ids = [f"OY-{i:04d}" for i in range(X.shape[0])]
    return X, years, ids


def _fixture_unequal_years() -> tuple[np.ndarray, np.ndarray, list[str]]:
    g = _rng(303)
    y22 = np.vstack([
        g.normal(loc=(-1.5, 0.0), scale=0.16, size=(22, 2)),
        g.normal(loc=(1.5, 0.0), scale=0.20, size=(18, 2)),
    ])
    y23 = np.vstack([
        g.normal(loc=(-1.45, 0.03), scale=0.17, size=(34, 2)),
        g.normal(loc=(1.55, -0.02), scale=0.21, size=(31, 2)),
        g.uniform(low=-4.0, high=4.0, size=(15, 2)),
    ])
    X = _embed2(np.vstack([y22, y23]))
    years = np.asarray([2022] * len(y22) + [2023] * len(y23), dtype=np.int64)
    ids = [f"UY-{i:04d}" for i in range(X.shape[0])]
    return X, years, ids


def _fixture_exact_ties() -> tuple[np.ndarray, np.ndarray, list[str]]:
    grid = np.asarray([(float(i), float(j)) for i in range(5) for j in range(5)], dtype=np.float64)
    y22 = grid.copy()
    y23 = grid.copy()
    X = _embed2(np.vstack([y22, y23]))
    years = np.asarray([2022] * 25 + [2023] * 25, dtype=np.int64)
    ids = [f"TIE-{i:04d}" for i in range(X.shape[0])]
    return X, years, ids


def _fixture_nested_density() -> tuple[np.ndarray, np.ndarray, list[str]]:
    g = _rng(505)
    chunks = []
    years = []
    for yr, dx in ((2022, 0.0), (2023, 0.035)):
        tight = g.normal(loc=(dx, 0.0), scale=0.045, size=(22, 2))
        broad = g.normal(loc=(dx, 0.0), scale=0.33, size=(30, 2))
        remote = g.normal(loc=(2.4 + dx, 0.1), scale=0.15, size=(18, 2))
        chunks.extend([tight, broad, remote])
        years.extend([yr] * 70)
    X = _embed2(np.vstack(chunks))
    ids = [f"ND-{i:04d}" for i in range(X.shape[0])]
    return X, np.asarray(years, dtype=np.int64), ids


FIXTURES = {
    "two_recurrent_clusters_plus_noise": _fixture_recurrent_clusters,
    "dense_one_year_only_diffuse_opposite": _fixture_one_year_only,
    "unequal_annual_sample_sizes": _fixture_unequal_years,
    "exact_distance_ties": _fixture_exact_ties,
    "nested_density": _fixture_nested_density,
}


def _sha_array(a: np.ndarray) -> str:
    arr = np.ascontiguousarray(a)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _canonical_partition(labels: np.ndarray, ids: list[str]) -> tuple[tuple[str, ...], ...]:
    labels = np.asarray(labels, dtype=np.int64)
    families = []
    for lab in sorted(int(v) for v in np.unique(labels) if int(v) >= 0):
        members = tuple(sorted(ids[i] for i in np.flatnonzero(labels == lab)))
        families.append(members)
    noise = tuple(sorted(ids[i] for i in np.flatnonzero(labels < 0)))
    return tuple(sorted(families)) + (("__NOISE__",) + noise,)


def _cluster_leafsets(tree: np.ndarray) -> dict[int, tuple[int, ...]]:
    root = int(tree["parent"].min())
    children: dict[int, list[int]] = {}
    nodes: set[int] = set()
    for row in tree:
        p, c = int(row["parent"]), int(row["child"])
        children.setdefault(p, []).append(c)
        nodes.add(p)
        if c >= root:
            nodes.add(c)
    memo: dict[int, tuple[int, ...]] = {}
    for node in sorted(nodes, reverse=True):
        leaves: list[int] = []
        for c in children.get(node, []):
            if c < root:
                leaves.append(c)
            else:
                leaves.extend(memo[c])
        memo[node] = tuple(sorted(leaves))
    return memo


def _canonical_condensed(tree: np.ndarray) -> list[tuple[tuple[int, ...], tuple[int, ...], float, int]]:
    root = int(tree["parent"].min())
    leaves = _cluster_leafsets(tree)
    rows = []
    for row in tree:
        p, c = int(row["parent"]), int(row["child"])
        child_key = (c,) if c < root else leaves[c]
        rows.append((leaves[p], child_key, float(row["lambda_val"]), int(row["child_size"])))
    return sorted(rows, key=lambda r: (r[0], r[1], r[3], r[2]))


def _assert_condensed_equal(a: np.ndarray, b: np.ndarray) -> None:
    ca, cb = _canonical_condensed(a), _canonical_condensed(b)
    if len(ca) != len(cb):
        raise AssertionError(f"condensed row count mismatch: {len(ca)} != {len(cb)}")
    for ra, rb in zip(ca, cb):
        if ra[0] != rb[0] or ra[1] != rb[1] or ra[3] != rb[3] or abs(ra[2] - rb[2]) > ATOL:
            raise AssertionError(f"condensed mismatch: {ra} != {rb}")


def _candidate_ranking(tree: np.ndarray, years: np.ndarray, ids: list[str]) -> list[dict]:
    recurrent, _annual = recurrent_stability(tree, years)
    ordinary = compute_stability(tree)
    selected = selected_eom_nodes(tree, recurrent)
    leaves = _cluster_leafsets(tree)
    out = []
    for node in selected:
        members = tuple(sorted(ids[i] for i in leaves[int(node)]))
        family_id = hashlib.sha256("\n".join(members).encode()).hexdigest()
        out.append({
            "family_id": family_id,
            "members": members,
            "recurrent": float(recurrent[float(node)]),
            "ordinary": float(ordinary[float(node)]),
            "member_count": len(members),
        })
    out.sort(key=lambda c: (-c["recurrent"], -c["ordinary"], -c["member_count"], c["family_id"]))
    return out


def _assert_ranking_equal(a: list[dict], b: list[dict]) -> None:
    if len(a) != len(b):
        raise AssertionError(f"candidate count mismatch: {len(a)} != {len(b)}")
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca["members"] != cb["members"] or ca["member_count"] != cb["member_count"]:
            raise AssertionError(f"candidate membership/order mismatch at rank {i+1}")
        if abs(ca["recurrent"] - cb["recurrent"]) > ATOL:
            raise AssertionError(f"recurrent score mismatch at rank {i+1}")
        if abs(ca["ordinary"] - cb["ordinary"]) > ATOL:
            raise AssertionError(f"ordinary score mismatch at rank {i+1}")


def run_fixture(name: str, maker) -> dict:
    X, years, ids = maker()
    ref = dense_reference(X, years, ids, k=K, min_cluster_size=MIN_CLUSTER_SIZE)
    cand = audit_candidate(X, years, ids, k=K, min_cluster_size=MIN_CLUSTER_SIZE)

    if not np.allclose(ref.core_distances, cand.core_distances, rtol=0.0, atol=ATOL):
        delta = float(np.max(np.abs(ref.core_distances - cand.core_distances)))
        raise AssertionError(f"{name}: cross-year core distance mismatch max_abs={delta}")

    ref_w = np.sort(np.asarray(ref.mst_edges[:, 2], dtype=np.float64))
    cand_w = np.sort(np.asarray(cand.mst_edges[:, 2], dtype=np.float64))
    if not np.allclose(ref_w, cand_w, rtol=0.0, atol=ATOL):
        raise AssertionError(f"{name}: MST edge-weight multiset mismatch")

    ref_single = sorted((float(r[2]), int(r[3])) for r in np.asarray(ref.single_linkage_tree))
    cand_single = sorted((float(r[2]), int(r[3])) for r in np.asarray(cand.single_linkage_tree))
    if len(ref_single) != len(cand_single):
        raise AssertionError(f"{name}: single-linkage row-count mismatch")
    for ra, rb in zip(ref_single, cand_single):
        if ra[1] != rb[1] or abs(ra[0] - rb[0]) > ATOL:
            raise AssertionError(f"{name}: single-linkage merge distance/size mismatch")

    _assert_condensed_equal(ref.condensed_tree, cand.condensed_tree)

    ref_rec, _ = recurrent_stability(ref.condensed_tree, years)
    cand_rec, _ = recurrent_stability(cand.condensed_tree, years)
    ref_labels = eom_labels(ref.condensed_tree, ref_rec)
    cand_labels = eom_labels(cand.condensed_tree, cand_rec)
    if _canonical_partition(ref_labels, ids) != _canonical_partition(cand_labels, ids):
        raise AssertionError(f"{name}: selected recurrent-EOM partition mismatch")

    ref_rank = _candidate_ranking(ref.condensed_tree, years, ids)
    cand_rank = _candidate_ranking(cand.condensed_tree, years, ids)
    _assert_ranking_equal(ref_rank, cand_rank)

    return {
        "name": name,
        "n": int(X.shape[0]),
        "year_counts": {str(y): int(np.sum(years == y)) for y in sorted(np.unique(years))},
        "max_core_abs_delta": float(np.max(np.abs(ref.core_distances - cand.core_distances))),
        "reference_core_sha256": _sha_array(ref.core_distances),
        "candidate_core_sha256": _sha_array(cand.core_distances),
        "reference_mst_weight_sha256": _sha_array(ref_w),
        "candidate_mst_weight_sha256": _sha_array(cand_w),
        "selected_family_count": len(ref_rank),
        "status": "PASS",
    }


def main() -> None:
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for name, maker in FIXTURES.items():
        print(f"AUDIT {name}", flush=True)
        results.append(run_fixture(name, maker))
    payload = {
        "verdict": "PASS_CROSSYEAR_CORE_HDBSCAN_V1_SYNTHETIC_EXACTNESS_AUDIT",
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "orbittrace_target_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "k": K,
        "min_cluster_size": MIN_CLUSTER_SIZE,
        "absolute_tolerance_frozen_pre_gmn": ATOL,
        "fixtures": results,
    }
    path = out / "CROSSYEAR_CORE_HDBSCAN_V1_SYNTHETIC_AUDIT.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(payload["verdict"])


if __name__ == "__main__":
    main()
