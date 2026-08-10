#!/usr/bin/env python3
"""Truth-free final SonotaCo comparator execution adapter.

This module performs no archive/network/truth access. The execution workflow supplies records from
the already-frozen shared pairwise manifest plus the exact decoded Sugar/HDBSCAN modules pinned by
#865. This adapter calls those modules rather than reimplementing either literature algorithm.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Sequence

import numpy as np

SUGAR_CORPUS = "sonotaco-final-label-free-sugar-v1"
SUGAR_PAIR_ID = "ORBITTRACE_VS_SUGAR"
SUGAR_CORE_SHA256 = "5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb"
HDBSCAN_SOURCE_SHA256 = "a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2"

SUGAR_MIN_SAMPLES = 5
SUGAR_EPS_PERCENTILE = 23.0
SUGAR_CLONE_ITERATIONS = 1000
SUGAR_MERGE_OVERLAP = 0.5
SUGAR_MIN_RECURRENCE = 100
SUGAR_STRONG_RECURRENCE = 500
SUGAR_SEED_ROOT = 20170209

HDBSCAN_MIN_CLUSTER_SIZE = 100
HDBSCAN_VERSION = "0.8.44"

FORBIDDEN_TRUTH_KEYS = {
    "label", "shower", "shower_label", "reference", "truth", "known_shower",
    "native_background", "is_sporadic", "sporadic",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def _canonical_member_ids(records: Sequence[dict[str, Any]], indices: Sequence[int]) -> list[str]:
    ids = sorted(str(records[int(index)]["id"]) for index in indices)
    require(len(ids) == len(set(ids)), "duplicate member IDs in comparator family")
    return ids


def _family_id(prefix: str, member_ids: Sequence[str]) -> str:
    payload = json.dumps(list(member_ids), separators=(",", ":"), ensure_ascii=True).encode()
    return f"{prefix}{hashlib.sha256(payload).hexdigest()[:16]}"


def _validate_records(records: Sequence[dict[str, Any]], year: int) -> None:
    require(year in {2013, 2014}, f"final comparator year must be 2013/2014, got {year}")
    require(len(records) > 0, "empty comparator row universe")
    seen: set[str] = set()
    for row in records:
        require(isinstance(row, dict), "comparator record must be object")
        require(not (FORBIDDEN_TRUTH_KEYS & set(row)), "truth-bearing key present before output freeze")
        require(int(row.get("year")) == year, "mixed/wrong year in comparator universe")
        event_id = str(row.get("id"))
        require(event_id and event_id not in seen, "missing/duplicate event ID")
        seen.add(event_id)
        for key in ("sol", "sun_lon", "ecl_lat", "vg"):
            require(row.get(key) is not None and math.isfinite(float(row[key])), f"invalid {key}")


def _families_from_labels(
    records: Sequence[dict[str, Any]],
    labels: np.ndarray,
    *,
    prefix: str,
    probabilities: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    require(labels.shape == (len(records),), "label vector length mismatch")
    if probabilities is not None:
        require(probabilities.shape == labels.shape, "probability vector length mismatch")
    grouped: dict[int, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        value = int(label)
        if value >= 0:
            grouped[value].append(i)
    families: list[dict[str, Any]] = []
    for label in sorted(grouped):
        indices = grouped[label]
        members = _canonical_member_ids(records, indices)
        row: dict[str, Any] = {
            "family_id": _family_id(prefix, members),
            "native_label": int(label),
            "member_ids": members,
            "member_count": len(members),
        }
        if probabilities is not None:
            ps = [float(probabilities[i]) for i in indices]
            require(all(math.isfinite(x) for x in ps), "nonfinite comparator probability")
            row["membership_probability_min"] = min(ps)
            row["membership_probability_mean"] = float(np.mean(ps))
            row["membership_probability_max"] = max(ps)
        families.append(row)
    families.sort(key=lambda row: (int(row["native_label"]), str(row["family_id"])))
    return families


def run_sugar(
    records: Sequence[dict[str, Any]],
    *,
    year: int,
    sugar: Any,
) -> dict[str, Any]:
    """Execute exact frozen Sugar core on an already pairwise-eligible shared manifest."""
    _validate_records(records, year)
    require(getattr(sugar, "__source_sha256__", None) == SUGAR_CORE_SHA256,
            "Sugar decoded-source SHA drift")
    for row in records:
        for key in ("ra", "dec", "ra_sd", "dec_sd", "vg_sd", "qc"):
            require(row.get(key) is not None and math.isfinite(float(row[key])), f"Sugar missing {key}")
        ra_sd = float(row["ra_sd"])
        dec_sd = float(row["dec_sd"])
        vg_sd = float(row["vg_sd"])
        qc = float(row["qc"])
        vg = float(row["vg"])
        require(ra_sd >= 0.0 and dec_sd >= 0.0 and vg_sd >= 0.0,
                "Sugar uncertainty eligibility violated")
        require(qc > 15.0, "Sugar convergence-angle eligibility violated")
        require(vg_sd <= 0.10 * vg + 1.0, "Sugar speed-uncertainty eligibility violated")

    require(int(sugar.MIN_SAMPLES) == SUGAR_MIN_SAMPLES, "Sugar MIN_SAMPLES drift")
    require(float(sugar.EPS_PERCENTILE) == SUGAR_EPS_PERCENTILE, "Sugar epsilon percentile drift")
    require(int(sugar.CLONE_ITERATIONS) == SUGAR_CLONE_ITERATIONS, "Sugar clone count drift")
    require(float(sugar.MERGE_OVERLAP_FRACTION) == SUGAR_MERGE_OVERLAP, "Sugar overlap drift")
    require(int(sugar.MIN_RECURRENCE) == SUGAR_MIN_RECURRENCE, "Sugar recurrence drift")
    require(int(sugar.STRONG_RECURRENCE) == SUGAR_STRONG_RECURRENCE, "Sugar strong recurrence drift")
    require(int(sugar.SEED_ROOT) == SUGAR_SEED_ROOT, "Sugar seed root drift")

    sol = np.asarray([float(row["sol"]) for row in records], dtype=np.float64)
    ra = np.asarray([float(row["ra"]) for row in records], dtype=np.float64)
    dec = np.asarray([float(row["dec"]) for row in records], dtype=np.float64)
    vg = np.asarray([float(row["vg"]) for row in records], dtype=np.float64)
    ra_sd = np.asarray([float(row["ra_sd"]) for row in records], dtype=np.float64)
    dec_sd = np.asarray([float(row["dec_sd"]) for row in records], dtype=np.float64)
    vg_sd = np.asarray([float(row["vg_sd"]) for row in records], dtype=np.float64)

    observed = sugar.feature_matrix_from_equatorial(sol, ra, dec, vg)
    epsilon, fourth_neighbor = sugar.transferred_epsilon(observed)
    require(np.asarray(observed).shape == (len(records), 6), "unexpected Sugar observed feature shape")
    require(np.asarray(fourth_neighbor).shape == (len(records),), "unexpected Sugar neighbor-distance shape")
    require(math.isfinite(float(epsilon)) and float(epsilon) > 0.0, "invalid Sugar epsilon")

    merger = sugar.OverlapGraphMerger(len(records))
    iteration_cluster_counts: list[int] = []
    for iteration in range(SUGAR_CLONE_ITERATIONS):
        seed = sugar.stable_seed(
            SUGAR_SEED_ROOT, SUGAR_CORPUS, int(year), SUGAR_PAIR_ID, int(iteration)
        )
        clone_features = sugar.clone_feature_matrix(
            sol, ra, dec, vg, ra_sd, dec_sd, vg_sd, seed=seed
        )
        clusters = sugar.dbscan_clusters(clone_features, float(epsilon))
        merger.add_iteration(iteration, clusters)
        iteration_cluster_counts.append(len(clusters))

    masters = merger.finalize()
    labels, probabilities = sugar.hard_assignment(
        len(records), masters, minimum_recurrence=SUGAR_MIN_RECURRENCE
    )
    labels = np.asarray(labels, dtype=np.int32)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    families = _families_from_labels(records, labels, prefix="SUGAR", probabilities=probabilities)

    return {
        "method": "Sugar",
        "year": int(year),
        "source_sha256": SUGAR_CORE_SHA256,
        "corpus_namespace": SUGAR_CORPUS,
        "comparator_pair_identifier": SUGAR_PAIR_ID,
        "event_count": len(records),
        "epsilon": float(epsilon),
        "clone_iterations": SUGAR_CLONE_ITERATIONS,
        "master_component_count": len(masters),
        "retained_family_count": len(families),
        "iteration_cluster_count_min": min(iteration_cluster_counts),
        "iteration_cluster_count_max": max(iteration_cluster_counts),
        "families": families,
        "truth_accessed": False,
    }


def run_hdbscan(
    records: Sequence[dict[str, Any]],
    *,
    year: int,
    hdbscan_runner: Any,
    core_dist_jobs: int = 1,
) -> dict[str, Any]:
    """Execute exact frozen catalogue-HDBSCAN functions on pairwise-eligible shared rows."""
    _validate_records(records, year)
    require(getattr(hdbscan_runner, "__source_sha256__", None) == HDBSCAN_SOURCE_SHA256,
            "HDBSCAN decoded-source SHA drift")
    require(int(hdbscan_runner.MIN_CLUSTER_SIZE) == HDBSCAN_MIN_CLUSTER_SIZE,
            "HDBSCAN min-cluster-size drift")
    require(str(hdbscan_runner.HDBSCAN_VERSION) == HDBSCAN_VERSION, "HDBSCAN version drift")
    require(int(core_dist_jobs) >= 1, "core_dist_jobs must be positive")

    features = np.asarray(hdbscan_runner.feature_matrix(list(records)), dtype=np.float64)
    require(features.shape == (len(records), 6), "unexpected HDBSCAN GEO feature shape")
    labels, probabilities, diagnostics = hdbscan_runner.run_hdbscan(features, int(core_dist_jobs))
    labels = np.asarray(labels, dtype=np.int32)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    families = _families_from_labels(records, labels, prefix="HDB", probabilities=probabilities)

    return {
        "method": "catalogue HDBSCAN",
        "year": int(year),
        "source_sha256": HDBSCAN_SOURCE_SHA256,
        "event_count": len(records),
        "core_dist_jobs": int(core_dist_jobs),
        "retained_family_count": len(families),
        "native_diagnostics": diagnostics,
        "families": families,
        "truth_accessed": False,
    }
