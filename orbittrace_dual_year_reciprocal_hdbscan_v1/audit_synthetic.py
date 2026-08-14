#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from run_development import annual_clusters, reciprocal_families


def canonical(fams):
    return [
        (
            f["family_id"],
            tuple(f["event_ids"]),
            float(f["score"]),
            float(f["centroid_distance"]),
            tuple(sorted(f["year_nodes"].items())),
        )
        for f in fams
    ]


def make_year(year: int, shift: np.ndarray, nuisance: np.ndarray, seed: int):
    rng = np.random.default_rng(seed)
    centers = [
        np.asarray([0.80, 0.10, 0.15, 0.92, 0.08, 0.55]),
        np.asarray([-0.20, 0.95, 0.70, -0.10, 0.20, 0.78]),
        np.asarray([-0.85, -0.15, -0.25, -0.80, 0.35, 0.42]),
    ]
    chunks = []
    ids = []
    for ci, center in enumerate(centers):
        chunk = rng.normal(center + shift, 0.025, size=(45, 6))
        chunks.append(chunk)
        ids.extend([f"{year}-S{ci}-{i:03d}" for i in range(len(chunk))])
    chunk = rng.normal(nuisance, 0.020, size=(35, 6))
    chunks.append(chunk)
    ids.extend([f"{year}-N-{i:03d}" for i in range(len(chunk))])
    X = np.vstack(chunks)
    events = [{"id": eid, "year": year} for eid in ids]
    return events, X


def main() -> int:
    e22, x22 = make_year(2022, np.zeros(6), np.asarray([1.7, -1.6, 0.2, 0.1, -0.4, 0.3]), 20260814)
    e23, x23 = make_year(2023, np.asarray([0.015, -0.010, 0.005, 0.008, -0.006, 0.004]), np.asarray([-1.6, 1.7, -0.2, 0.2, 0.4, 0.9]), 20260815)

    a, da = annual_clusters(2022, e22, x22)
    b, db = annual_clusters(2023, e23, x23)
    fams1, diag1 = reciprocal_families(a, b)
    fams2, diag2 = reciprocal_families(a, b)

    if canonical(fams1) != canonical(fams2):
        raise RuntimeError("reciprocal-family construction is not deterministic")
    if diag1 != diag2:
        raise RuntimeError("reciprocal diagnostic is not deterministic")
    if not fams1:
        raise RuntimeError("synthetic reciprocal matcher emitted no family")
    if any(len(f["event_ids"]) < 20 for f in fams1):
        raise RuntimeError("synthetic reciprocal family unexpectedly small")
    if any(set(f["year_nodes"]) != {"2022", "2023"} for f in fams1):
        raise RuntimeError("synthetic family lacks one observing year")
    if any(not np.isfinite(float(f["score"])) or float(f["score"]) < 0 for f in fams1):
        raise RuntimeError("synthetic family has invalid score")
    if any(not np.isfinite(float(f["centroid_distance"])) for f in fams1):
        raise RuntimeError("synthetic family has invalid centroid distance")

    payload = canonical(fams1)
    out = {
        "verdict": "PASS_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_SYNTHETIC_AUDIT",
        "scientific_endpoint": False,
        "synthetic_only": True,
        "annual_cluster_counts": {"2022": len(a), "2023": len(b)},
        "reciprocal_pair_count": len(fams1),
        "candidate_order_sha256": diag1["candidate_order_sha256"],
        "canonical_family_sha256": hashlib.sha256(repr(payload).encode()).hexdigest(),
        "deterministic_repeat_exact": True,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "gmn_catalogue_access": False,
        "sonotaco_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    Path("synthetic_audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
