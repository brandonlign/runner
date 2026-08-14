from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import compute_stability, condense_tree

from orbittrace_crossyear_core_hdbscan_v1.boruvka_adapter import exact_crossyear_boruvka_mst
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


def _ids(n: int, prefix: str) -> list[str]:
    return [f"{prefix}-{i:04d}" for i in range(n)]


def recurrent_clusters_plus_noise() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(101)
    blocks: list[np.ndarray] = []
    years: list[int] = []
    ids: list[str] = []
    for year, offset in ((2022, -0.02), (2023, 0.02)):
        a = r.normal(loc=np.zeros(6) + offset, scale=0.035, size=(18, 6))
        b = r.normal(loc=np.array([0.7, 0.7, 0.2, 0.1, -0.1, 0.3]) + offset, scale=0.035, size=(18, 6))
        noise = r.uniform(-1.2, 1.2, size=(12, 6))
        block = np.vstack([a, b, noise])
        blocks.append(block)
        years.extend([year] * len(block))
        ids.extend(_ids(len(block), f"rec-{year}"))
    return np.vstack(blocks), np.asarray(years, dtype=np.int64), ids


def one_year_only_dense() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(202)
    shared22 = r.normal(0.0, 0.045, size=(22, 6))
    lone22 = r.normal(2.0, 0.012, size=(16, 6))
    noise22 = r.uniform(-1.5, 1.5, size=(12, 6))
    shared23 = r.normal(0.01, 0.045, size=(22, 6))
    noise23 = r.uniform(-1.5, 1.5, size=(28, 6))
    X = np.vstack([shared22, lone22, noise22, shared23, noise23])
    years = np.asarray([2022] * 50 + [2023] * 50, dtype=np.int64)
    ids = _ids(50, "solo-2022") + _ids(50, "solo-2023")
    return X, years, ids


def unequal_year_sizes() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(303)
    X22 = np.vstack([r.normal(-0.3, 0.07, size=(24, 6)), r.uniform(-1.0, 1.0, size=(13, 6))])
    X23 = np.vstack([r.normal(-0.28, 0.07, size=(31, 6)), r.uniform(-1.0, 1.0, size=(22, 6))])
    X = np.vstack([X22, X23])
    years = np.asarray([2022] * len(X22) + [2023] * len(X23), dtype=np.int64)
    ids = _ids(len(X22), "unequal-2022") + _ids(len(X23), "unequal-2023")
    return X, years, ids


def exact_distance_ties() -> tuple[np.ndarray, np.ndarray, list[str]]:
    ring = np.asarray(
        [[np.cos(t), np.sin(t), 0.0, 0.0, 0.0, 0.0] for t in np.linspace(0, 2 * np.pi, 12, endpoint=False)],
        dtype=np.float64,
    )
    X22 = np.vstack([ring, ring * 0.5])
    X23 = np.vstack([ring.copy(), ring * 0.5])
    X = np.vstack([X22, X23])
    years = np.asarray([2022] * 24 + [2023] * 24, dtype=np.int64)
    ids = [f"tie22-{i:02d}" for i in range(24)] + [f"tie23-{i:02d}" for i in range(24)]
    return X, years, ids


def nested_density() -> tuple[np.ndarray, np.ndarray, list[str]]:
    r = _rng(505)
    blocks: list[np.ndarray] = []
    years: list[int] = []
    ids: list[str] = []
    for year, shift in ((2022, 0.0), (2023, 0.015)):
        core = r.normal(shift, 0.018, size=(16, 6))
        shell = r.normal(shift, 0.12, size=(28, 6))
        background = r.uniform(-1.0, 1.0, size=(14, 6))
        block = np.vstack([core, shell, background])
        blocks.append(block)
        years.extend([year] * len(block))
        ids.extend(_ids(len(block), f"nested-{year}"))
    return np.vstack(blocks), np.asarray(years, dtype=np.int64), ids


FIXTURES = (
    ("recurrent_clusters_plus_noise", recurrent_clusters_plus_noise),
    ("one_year_only_dense", one_year_only_dense),
    ("unequal_year_sizes", unequal_year_sizes),
    ("exact_distance_ties", exact_distance_ties),
    ("nested_density", nested_density),
)


def _same_float(a: float, b: float) -> bool:
    a = float(a)
    b = float(b)
    if np.isnan(a) or np.isnan(b):
        return False
    if np.isinf(a) or np.isinf(b):
        return a == b
    return abs(a - b) <= ATOL


def _hash_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _sort_mst_for_linkage(mst: np.ndarray) -> np.ndarray:
    mst = np.asarray(mst, dtype=np.float64)
    order = sorted(
        range(mst.shape[0]),
        key=lambda r: (
            float(mst[r, 2]),
            min(int(mst[r, 0]), int(mst[r, 1])),
            max(int(mst[r, 0]), int(mst[r, 1])),
        ),
    )
    return np.asarray(mst[order], dtype=np.float64)


def _boruvka_hierarchy(X: np.ndarray, years: np.ndarray, ids: list[str]):
    table, mst = exact_crossyear_boruvka_mst(X, years, ids, k=K)
    single = np.asarray(label(_sort_mst_for_linkage(mst)))
    condensed = np.asarray(condense_tree(single, MIN_CLUSTER_SIZE))
    return table, np.asarray(mst), single, condensed


def _cluster_leafsets(tree: np.ndarray) -> dict[int, tuple[int, ...]]:
    root = int(tree["parent"].min())
    children: dict[int, list[int]] = {}
    cluster_nodes: set[int] = set()
    for row in tree:
        p = int(row["parent"])
        c = int(row["child"])
        children.setdefault(p, []).append(c)
        cluster_nodes.add(p)
        if c >= root:
            cluster_nodes.add(c)
    memo: dict[int, tuple[int, ...]] = {}
    for node in sorted(cluster_nodes, reverse=True):
        leaves: list[int] = []
        for c in children.get(node, []):
            if c < root:
                leaves.append(c)
            else:
                if c not in memo:
                    raise RuntimeError(f"missing child cluster {c} while canonicalizing node {node}")
                leaves.extend(memo[c])
        memo[node] = tuple(sorted(leaves))
    return memo


def _canonical_condensed(tree: np.ndarray, ids: list[str]) -> list[tuple[tuple[str, ...], str, tuple[str, ...], float, int]]:
    root = int(tree["parent"].min())
    leafsets = _cluster_leafsets(tree)
    rows = []
    for row in tree:
        p = int(row["parent"])
        c = int(row["child"])
        parent_ids = tuple(sorted(ids[i] for i in leafsets[p]))
        if c < root:
            kind = "POINT"
            child_ids = (ids[c],)
        else:
            kind = "CLUSTER"
            child_ids = tuple(sorted(ids[i] for i in leafsets[c]))
        rows.append((parent_ids, kind, child_ids, float(row["lambda_val"]), int(row["child_size"])))
    return sorted(rows, key=lambda r: (r[0], r[1], r[2], r[4], r[3]))


def _assert_condensed_equal(reference: np.ndarray, candidate: np.ndarray, ids: list[str], name: str) -> None:
    a = _canonical_condensed(reference, ids)
    b = _canonical_condensed(candidate, ids)
    if len(a) != len(b):
        raise AssertionError(f"{name}: condensed row count {len(a)} != {len(b)}")
    for i, (ra, rb) in enumerate(zip(a, b)):
        if ra[:3] != rb[:3] or ra[4] != rb[4] or not _same_float(ra[3], rb[3]):
            raise AssertionError(f"{name}: condensed row mismatch at canonical row {i}: {ra} != {rb}")


def _canonical_partition(labels: np.ndarray, ids: list[str]) -> tuple[tuple[str, ...], ...]:
    labels = np.asarray(labels, dtype=np.int64)
    groups = []
    for lab in sorted(int(v) for v in np.unique(labels) if int(v) >= 0):
        groups.append(tuple(sorted(ids[i] for i in np.flatnonzero(labels == lab))))
    return tuple(sorted(groups))


def _candidate_order(tree: np.ndarray, years: np.ndarray, ids: list[str]) -> list[dict]:
    recurrent, _annual = recurrent_stability(tree, years)
    ordinary = compute_stability(tree)
    labels = eom_labels(tree, recurrent)
    selected = selected_eom_nodes(tree, recurrent)
    positive = sorted(int(v) for v in np.unique(labels) if int(v) >= 0)
    if positive != list(range(len(selected))):
        raise AssertionError("compact recurrent-EOM labels no longer align with sorted selected nodes")
    rows = []
    for lab, node in enumerate(selected):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(ids[int(i)] for i in idx))
        if len(members) < MIN_CLUSTER_SIZE:
            raise AssertionError(f"selected family below min cluster size: {len(members)}")
        family_id = hashlib.sha256(("XYCORE1|" + "|".join(members)).encode()).hexdigest()[:20]
        rows.append(
            {
                "family_id": family_id,
                "members": members,
                "member_count": len(members),
                "recurrent_stability": float(recurrent[float(node)]),
                "ordinary_stability": float(ordinary[float(node)]),
            }
        )
    rows.sort(
        key=lambda r: (
            -r["recurrent_stability"],
            -r["ordinary_stability"],
            -r["member_count"],
            r["family_id"],
        )
    )
    return rows


def _assert_candidate_order_equal(a: list[dict], b: list[dict], name: str) -> None:
    if len(a) != len(b):
        raise AssertionError(f"{name}: candidate count {len(a)} != {len(b)}")
    for rank, (ra, rb) in enumerate(zip(a, b), 1):
        if ra["members"] != rb["members"] or ra["member_count"] != rb["member_count"]:
            raise AssertionError(f"{name}: membership/order mismatch at rank {rank}")
        if not _same_float(ra["recurrent_stability"], rb["recurrent_stability"]):
            raise AssertionError(f"{name}: recurrent stability mismatch at rank {rank}")
        if not _same_float(ra["ordinary_stability"], rb["ordinary_stability"]):
            raise AssertionError(f"{name}: ordinary stability mismatch at rank {rank}")


def _assert_single_linkage(reference: np.ndarray, candidate: np.ndarray, name: str) -> None:
    a = sorted((float(row[2]), int(row[3])) for row in np.asarray(reference))
    b = sorted((float(row[2]), int(row[3])) for row in np.asarray(candidate))
    if len(a) != len(b):
        raise AssertionError(f"{name}: linkage row count {len(a)} != {len(b)}")
    for i, (ra, rb) in enumerate(zip(a, b)):
        if ra[1] != rb[1] or not _same_float(ra[0], rb[0]):
            raise AssertionError(f"{name}: linkage mismatch at sorted row {i}: {ra} != {rb}")


def run_fixture(name: str, maker) -> dict:
    X, years, ids = maker()
    ref = dense_reference(X, years, ids, k=K, min_cluster_size=MIN_CLUSTER_SIZE)
    table, mst, single, condensed = _boruvka_hierarchy(X, years, ids)

    if not np.allclose(ref.core_distances, table.core_distances, rtol=0.0, atol=ATOL):
        delta = float(np.max(np.abs(ref.core_distances - table.core_distances)))
        raise AssertionError(f"{name}: core distance mismatch max_abs={delta}")

    ref_weights = np.sort(np.asarray(ref.mst_edges[:, 2], dtype=np.float64))
    boruvka_weights = np.sort(np.asarray(mst[:, 2], dtype=np.float64))
    if not np.allclose(ref_weights, boruvka_weights, rtol=0.0, atol=ATOL):
        delta = float(np.max(np.abs(ref_weights - boruvka_weights)))
        raise AssertionError(f"{name}: MST weight multiset mismatch max_abs={delta}")

    _assert_single_linkage(ref.single_linkage_tree, single, name)
    _assert_condensed_equal(ref.condensed_tree, condensed, ids, name)

    ref_rec, _ = recurrent_stability(ref.condensed_tree, years)
    bor_rec, _ = recurrent_stability(condensed, years)
    ref_labels = eom_labels(ref.condensed_tree, ref_rec)
    bor_labels = eom_labels(condensed, bor_rec)
    if _canonical_partition(ref_labels, ids) != _canonical_partition(bor_labels, ids):
        raise AssertionError(f"{name}: recurrent-EOM selected partition mismatch")

    ref_order = _candidate_order(ref.condensed_tree, years, ids)
    bor_order = _candidate_order(condensed, years, ids)
    _assert_candidate_order_equal(ref_order, bor_order, name)

    if name == "exact_distance_ties":
        table2, mst2, single2, condensed2 = _boruvka_hierarchy(X, years, ids)
        if not np.allclose(table.core_distances, table2.core_distances, rtol=0.0, atol=0.0):
            raise AssertionError("exact_distance_ties: Boruvka core distances not deterministic")
        if not np.allclose(np.sort(mst[:, 2]), np.sort(mst2[:, 2]), rtol=0.0, atol=0.0):
            raise AssertionError("exact_distance_ties: Boruvka MST weights not deterministic")
        _assert_single_linkage(single, single2, "exact_distance_ties rerun")
        _assert_condensed_equal(condensed, condensed2, ids, "exact_distance_ties rerun")
        _assert_candidate_order_equal(bor_order, _candidate_order(condensed2, years, ids), "exact_distance_ties rerun")

    return {
        "name": name,
        "n": int(X.shape[0]),
        "year_counts": {str(int(y)): int(np.sum(years == y)) for y in sorted(np.unique(years))},
        "max_core_abs_delta": float(np.max(np.abs(ref.core_distances - table.core_distances))),
        "max_mst_weight_abs_delta": float(np.max(np.abs(ref_weights - boruvka_weights))),
        "reference_core_sha256": _hash_array(ref.core_distances),
        "boruvka_core_sha256": _hash_array(table.core_distances),
        "reference_mst_weight_sha256": _hash_array(ref_weights),
        "boruvka_mst_weight_sha256": _hash_array(boruvka_weights),
        "candidate_count": len(ref_order),
        "status": "PASS",
    }


def main() -> None:
    results = []
    for name, maker in FIXTURES:
        print(f"BORUVKA_AUDIT {name}", flush=True)
        results.append(run_fixture(name, maker))
    payload = {
        "verdict": "PASS_CROSSYEAR_CORE_BORUVKA_EXACTNESS_AUDIT_V1",
        "absolute_tolerance_frozen_pre_execution": ATOL,
        "k": K,
        "min_cluster_size": MIN_CLUSTER_SIZE,
        "fixtures": results,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "orbittrace_target_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "CROSSYEAR_CORE_BORUVKA_EXACTNESS_AUDIT_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(payload["verdict"], flush=True)


if __name__ == "__main__":
    main()
