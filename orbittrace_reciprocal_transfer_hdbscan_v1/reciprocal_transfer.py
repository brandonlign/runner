from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from typing import Sequence

import hdbscan
import numpy as np
from hdbscan.prediction import approximate_predict


MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10


@dataclass(frozen=True)
class ReciprocalTransferResult:
    labels_2022: np.ndarray
    labels_2023: np.ndarray
    persistence_2022: np.ndarray
    persistence_2023: np.ndarray
    predicted_2022_to_2023: np.ndarray
    predicted_2023_to_2022: np.ndarray
    probabilities_2022_to_2023: np.ndarray
    probabilities_2023_to_2022: np.ndarray
    forward_mapping: dict[int, int | None]
    backward_mapping: dict[int, int | None]
    forward_fraction: dict[int, float]
    backward_fraction: dict[int, float]
    candidates: tuple[dict, ...]
    condensed_tree_2022: np.ndarray
    condensed_tree_2023: np.ndarray


def _validate(X: np.ndarray, ids: Sequence[str], year: int) -> tuple[np.ndarray, tuple[str, ...]]:
    X = np.asarray(X, dtype=np.float64)
    ids_t = tuple(str(v) for v in ids)
    if X.ndim != 2 or X.shape[0] == 0 or not np.all(np.isfinite(X)):
        raise ValueError(f"{year}: X must be a non-empty finite 2D array")
    if len(ids_t) != X.shape[0] or len(set(ids_t)) != len(ids_t):
        raise ValueError(f"{year}: IDs must be unique and align with X")
    return X, ids_t


def fit_annual(X: np.ndarray) -> hdbscan.HDBSCAN:
    return hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=True,
    ).fit(np.asarray(X, dtype=np.float64))


def strict_majority_mapping(native_labels: np.ndarray, transported_labels: np.ndarray) -> tuple[dict[int, int | None], dict[int, float]]:
    native = np.asarray(native_labels, dtype=np.int64)
    transported = np.asarray(transported_labels, dtype=np.int64)
    if native.shape != transported.shape or native.ndim != 1:
        raise ValueError("native and transported labels must be aligned 1D arrays")

    mapping: dict[int, int | None] = {}
    fractions: dict[int, float] = {}
    for label in sorted(int(v) for v in np.unique(native) if int(v) >= 0):
        idx = np.flatnonzero(native == label)
        if idx.size == 0:
            raise RuntimeError("empty selected annual cluster")
        counts = Counter(int(v) for v in transported[idx])
        best_label, best_count = min(
            counts.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
        fraction = float(best_count / idx.size)
        if best_label >= 0 and best_count * 2 > idx.size:
            mapping[label] = int(best_label)
            fractions[label] = fraction
        else:
            mapping[label] = None
            fractions[label] = fraction if best_label >= 0 else 0.0
    return mapping, fractions


def _assert_native_label_persistence_identity(labels: np.ndarray, persistence: np.ndarray, year: int) -> tuple[int, ...]:
    positive = tuple(sorted(int(v) for v in np.unique(labels) if int(v) >= 0))
    expected = tuple(range(len(persistence)))
    if positive != expected:
        raise RuntimeError(f"{year}: native HDBSCAN labels no longer align with cluster_persistence_: {positive[:10]} vs {expected[:10]}")
    if not np.all(np.isfinite(persistence)) or np.any(persistence < 0.0):
        raise RuntimeError(f"{year}: invalid cluster persistence")
    return positive


def _family_id(ids22: tuple[str, ...], ids23: tuple[str, ...]) -> str:
    payload = "RT1|2022|" + "|".join(ids22) + "|2023|" + "|".join(ids23)
    return "RT1-" + hashlib.sha256(payload.encode()).hexdigest()[:20]


def build_reciprocal_transfer(
    X22: np.ndarray,
    ids22: Sequence[str],
    X23: np.ndarray,
    ids23: Sequence[str],
) -> ReciprocalTransferResult:
    X22, ids22_t = _validate(X22, ids22, 2022)
    X23, ids23_t = _validate(X23, ids23, 2023)
    if X22.shape[1] != X23.shape[1]:
        raise ValueError("annual feature dimensions differ")

    model22 = fit_annual(X22)
    model23 = fit_annual(X23)
    labels22 = np.asarray(model22.labels_, dtype=np.int64)
    labels23 = np.asarray(model23.labels_, dtype=np.int64)
    persistence22 = np.asarray(model22.cluster_persistence_, dtype=np.float64)
    persistence23 = np.asarray(model23.cluster_persistence_, dtype=np.float64)
    selected22 = _assert_native_label_persistence_identity(labels22, persistence22, 2022)
    selected23 = _assert_native_label_persistence_identity(labels23, persistence23, 2023)

    pred22to23, prob22to23 = approximate_predict(model23, X22)
    pred23to22, prob23to22 = approximate_predict(model22, X23)
    pred22to23 = np.asarray(pred22to23, dtype=np.int64)
    pred23to22 = np.asarray(pred23to22, dtype=np.int64)
    prob22to23 = np.asarray(prob22to23, dtype=np.float64)
    prob23to22 = np.asarray(prob23to22, dtype=np.float64)
    if pred22to23.shape != labels22.shape or pred23to22.shape != labels23.shape:
        raise RuntimeError("cross-year prediction shape mismatch")
    if not np.all(np.isfinite(prob22to23)) or not np.all(np.isfinite(prob23to22)):
        raise RuntimeError("non-finite prediction probability")

    forward, forward_fraction = strict_majority_mapping(labels22, pred22to23)
    backward, backward_fraction = strict_majority_mapping(labels23, pred23to22)

    candidates: list[dict] = []
    used23: set[int] = set()
    for a in selected22:
        b = forward.get(a)
        if b is None or b not in backward or backward[b] != a:
            continue
        if b not in selected23:
            raise RuntimeError(f"2022 cluster {a} maps to nonexistent 2023 native cluster {b}")
        if b in used23:
            raise RuntimeError(f"2023 cluster {b} appears in more than one reciprocal family")
        used23.add(b)
        member22 = tuple(sorted(ids22_t[i] for i in np.flatnonzero(labels22 == a)))
        member23 = tuple(sorted(ids23_t[i] for i in np.flatnonzero(labels23 == b)))
        if len(member22) < MIN_CLUSTER_SIZE or len(member23) < MIN_CLUSTER_SIZE:
            raise RuntimeError("native reciprocal cluster below inherited min_cluster_size")
        p22 = float(persistence22[a])
        p23 = float(persistence23[b])
        candidates.append(
            {
                "family_id": _family_id(member22, member23),
                "annual_labels": {"2022": int(a), "2023": int(b)},
                "event_ids_2022": member22,
                "event_ids_2023": member23,
                "event_ids": tuple(sorted(member22 + member23)),
                "n_2022": len(member22),
                "n_2023": len(member23),
                "persistence_2022": p22,
                "persistence_2023": p23,
                "worst_year_persistence": min(p22, p23),
                "best_year_persistence": max(p22, p23),
                "forward_majority_fraction_reporting_only": float(forward_fraction[a]),
                "backward_majority_fraction_reporting_only": float(backward_fraction[b]),
            }
        )

    candidates.sort(
        key=lambda c: (
            -c["worst_year_persistence"],
            -c["best_year_persistence"],
            -min(c["n_2022"], c["n_2023"]),
            -(c["n_2022"] + c["n_2023"]),
            c["family_id"],
        )
    )

    # Independent annual HDBSCAN partitions are disjoint, so reciprocal pairs
    # must remain disjoint within each year as a construction invariant.
    seen22: set[str] = set()
    seen23: set[str] = set()
    for c in candidates:
        if seen22.intersection(c["event_ids_2022"]):
            raise RuntimeError("reciprocal families overlap within 2022")
        if seen23.intersection(c["event_ids_2023"]):
            raise RuntimeError("reciprocal families overlap within 2023")
        seen22.update(c["event_ids_2022"])
        seen23.update(c["event_ids_2023"])

    return ReciprocalTransferResult(
        labels_2022=labels22,
        labels_2023=labels23,
        persistence_2022=persistence22,
        persistence_2023=persistence23,
        predicted_2022_to_2023=pred22to23,
        predicted_2023_to_2022=pred23to22,
        probabilities_2022_to_2023=prob22to23,
        probabilities_2023_to_2022=prob23to22,
        forward_mapping=forward,
        backward_mapping=backward,
        forward_fraction=forward_fraction,
        backward_fraction=backward_fraction,
        candidates=tuple(candidates),
        condensed_tree_2022=np.asarray(model22.condensed_tree_._raw_tree).copy(),
        condensed_tree_2023=np.asarray(model23.condensed_tree_._raw_tree).copy(),
    )
