from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hdbscan
import numpy as np

from orbittrace_reciprocal_transfer_hdbscan_v1.reciprocal_transfer import (
    MIN_CLUSTER_SIZE,
    MIN_SAMPLES,
    build_reciprocal_transfer,
    fit_annual,
    strict_majority_mapping,
)


def _canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    labels = np.asarray(labels, dtype=np.int64)
    groups = []
    for label in sorted(int(v) for v in np.unique(labels) if int(v) >= 0):
        groups.append(tuple(int(i) for i in np.flatnonzero(labels == label)))
    noise = tuple(int(i) for i in np.flatnonzero(labels < 0))
    return tuple(sorted(groups)) + ((-1,) + noise,)


def _plain_model(X: np.ndarray) -> hdbscan.HDBSCAN:
    return hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)


def _fixture() -> tuple[np.ndarray, list[str], np.ndarray, list[str]]:
    rng = np.random.default_rng(2026081401)
    c1 = np.array([-1.2, -0.8, 0.1, 0.0, 0.0, -0.2])
    c2 = np.array([1.0, 0.9, -0.1, 0.2, 0.05, 0.25])
    only22 = np.array([0.0, 2.8, 0.4, -0.3, 0.2, 0.1])
    X22 = np.vstack(
        [
            rng.normal(c1, 0.035, size=(32, 6)),
            rng.normal(c2, 0.040, size=(30, 6)),
            rng.normal(only22, 0.030, size=(22, 6)),
            rng.uniform(-4.0, 4.0, size=(20, 6)),
        ]
    )
    X23 = np.vstack(
        [
            rng.normal(c1 + 0.015, 0.035, size=(35, 6)),
            rng.normal(c2 - 0.012, 0.040, size=(31, 6)),
            rng.uniform(-4.0, 4.0, size=(38, 6)),
        ]
    )
    ids22 = [f"S22-{i:04d}" for i in range(len(X22))]
    ids23 = [f"S23-{i:04d}" for i in range(len(X23))]
    return X22, ids22, X23, ids23


def _candidate_signature(result) -> list[dict]:
    out = []
    for c in result.candidates:
        out.append(
            {
                "family_id": c["family_id"],
                "event_ids_2022": list(c["event_ids_2022"]),
                "event_ids_2023": list(c["event_ids_2023"]),
                "persistence_2022": c["persistence_2022"],
                "persistence_2023": c["persistence_2023"],
                "n_2022": c["n_2022"],
                "n_2023": c["n_2023"],
            }
        )
    return out


def main() -> None:
    # Exact strict-majority boundary: 50% is not enough; >50% is enough.
    native = np.asarray([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int64)
    transported = np.asarray([2, 2, -1, -1, 3, 3, 3, -1], dtype=np.int64)
    mapping, fraction = strict_majority_mapping(native, transported)
    assert mapping[0] is None and fraction[0] == 0.5
    assert mapping[1] == 3 and fraction[1] == 0.75

    X22, ids22, X23, ids23 = _fixture()

    # Enabling prediction_data must not alter native annual clustering or persistence.
    for year, X in ((2022, X22), (2023, X23)):
        plain = _plain_model(X)
        pred = fit_annual(X)
        assert _canonical_partition(plain.labels_) == _canonical_partition(pred.labels_), year
        assert np.array_equal(np.asarray(plain.labels_), np.asarray(pred.labels_)), year
        assert np.array_equal(np.asarray(plain.cluster_persistence_), np.asarray(pred.cluster_persistence_)), year
        assert np.array_equal(np.asarray(plain.condensed_tree_._raw_tree), np.asarray(pred.condensed_tree_._raw_tree)), year

    result1 = build_reciprocal_transfer(X22, ids22, X23, ids23)
    result2 = build_reciprocal_transfer(X22, ids22, X23, ids23)

    sig1 = _candidate_signature(result1)
    sig2 = _candidate_signature(result2)
    assert sig1 == sig2
    assert np.array_equal(result1.labels_2022, result2.labels_2022)
    assert np.array_equal(result1.labels_2023, result2.labels_2023)
    assert np.array_equal(result1.predicted_2022_to_2023, result2.predicted_2022_to_2023)
    assert np.array_equal(result1.predicted_2023_to_2022, result2.predicted_2023_to_2022)

    # The two intentionally recurring compact clouds must yield at least two
    # reciprocal families; the 2022-only compact cloud must not be forced into
    # a counterpart by any centroid/radius fallback because none exists.
    assert len(result1.candidates) >= 2
    only22_ids = set(ids22[62:84])
    assert all(not only22_ids.issubset(set(c["event_ids_2022"])) for c in result1.candidates)

    # Every accepted pair must satisfy the frozen strict-majority reciprocal rule.
    for c in result1.candidates:
        a = int(c["annual_labels"]["2022"])
        b = int(c["annual_labels"]["2023"])
        assert result1.forward_mapping[a] == b
        assert result1.backward_mapping[b] == a
        assert result1.forward_fraction[a] > 0.5
        assert result1.backward_fraction[b] > 0.5
        assert c["n_2022"] >= MIN_CLUSTER_SIZE and c["n_2023"] >= MIN_CLUSTER_SIZE

    # Candidate memberships are native annual labels, never transported additions.
    for c in result1.candidates:
        a = int(c["annual_labels"]["2022"])
        b = int(c["annual_labels"]["2023"])
        expected22 = tuple(sorted(ids22[i] for i in np.flatnonzero(result1.labels_2022 == a)))
        expected23 = tuple(sorted(ids23[i] for i in np.flatnonzero(result1.labels_2023 == b)))
        assert c["event_ids_2022"] == expected22
        assert c["event_ids_2023"] == expected23

    encoded = json.dumps(sig1, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload = {
        "verdict": "PASS_RECIPROCAL_TRANSFER_HDBSCAN_V1_SYNTHETIC_AUDIT",
        "prediction_data_native_identity_2022": True,
        "prediction_data_native_identity_2023": True,
        "strict_majority_50_percent_rejected": True,
        "strict_majority_75_percent_accepted": True,
        "deterministic_repeated_execution": True,
        "reciprocal_candidate_count": len(result1.candidates),
        "candidate_signature_sha256": hashlib.sha256(encoded).hexdigest(),
        "2022_native_cluster_count": len(result1.persistence_2022),
        "2023_native_cluster_count": len(result1.persistence_2023),
        "synthetic_only": True,
        "gmn_accessed": False,
        "truth_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "efn_accessed": False,
        "orbittrace_target_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = Path("output_reciprocal_transfer_synthetic")
    out.mkdir(parents=True, exist_ok=True)
    (out / "RECIPROCAL_TRANSFER_HDBSCAN_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
