#!/usr/bin/env python3
"""Label-free unseen-data application of the already-frozen #839 URC ranker.

This is a transport adapter, not a new method. The trained estimator, feature definitions,
source indicators, neighbor descriptors, diversity lambda/scale and tie rule are fixed by
#839/#853. The only scientific-data adaptation is replacing development-only literal 2022/2023
references with an explicit ordered two-year pair and an explicit event->year map.

Prediction is executed with the already-serialized forest at n_jobs=1. This changes no tree,
weight, fitted parameter or prediction formula; it only fixes floating-point accumulation order
so application is deterministic across runners. No truth labels are accepted by this module.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np

EXPECTED_FEATURES = 34
EXPECTED_HARD_SCALE = 226
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def circular_diff_deg(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def family_centroid_distance_pair(family: dict[str, Any], years: tuple[int, int]) -> float:
    c = family.get("centroids", {})
    a = c.get(str(years[0]))
    b = c.get(str(years[1]))
    if not a or not b:
        return 10.0
    d_sol = circular_diff_deg(a["sol"], b["sol"]) / 10.0
    d_sun = circular_diff_deg(a["sun_lon"], b["sun_lon"]) / 4.0
    d_lat = abs(float(a["ecl_lat"]) - float(b["ecl_lat"])) / 4.0
    va = max(abs(float(a["vg"])), 1e-6)
    vb = max(abs(float(b["vg"])), 1e-6)
    d_v = abs(math.log(va / vb)) / math.log(1.10)
    return float(math.sqrt(d_sol * d_sol + d_sun * d_sun + d_lat * d_lat + d_v * d_v))


def member_year_balance_pair(
    family: dict[str, Any],
    years: tuple[int, int],
    event_year_by_id: dict[str, int],
) -> float:
    counts: Counter[int] = Counter()
    for raw in family["event_ids"]:
        eid = str(raw)
        require(eid in event_year_by_id, f"family member absent from event-year map: {eid}")
        year = int(event_year_by_id[eid])
        require(year in years, f"family member has unexpected year {year}: {eid}")
        counts[year] += 1
    a = int(counts.get(years[0], 0))
    b = int(counts.get(years[1], 0))
    return float(min(a, b) / max(a, b, 1))


def structural_features_pair(
    family: dict[str, Any],
    hard_rank: dict[str, int],
    years: tuple[int, int],
    event_year_by_id: dict[str, int],
) -> list[float]:
    """Exact #839 v1 structural vector, with only year addressing made explicit."""
    fid = str(family["family_id"])
    is_soft = 1.0 if family.get("family_type") else 0.0
    strengths = [float(family.get("year_strengths", {}).get(str(y), 0.0)) for y in years]
    smin, smax = min(strengths), max(strengths)
    sbalance = float((smin + 1e-6) / (smax + 1e-6)) if smax >= 0.0 else 0.0
    event_count = max(int(family.get("event_count", len(family.get("event_ids", [])))), 1)
    support_count = int(family.get("soft_support_count", 0))
    trigger = float(family.get("soft_trigger_max_seed_distance", 1.5))
    h_rank = int(hard_rank.get(fid, EXPECTED_HARD_SCALE + 1))
    # Preserve the learned development scale exactly; do not renormalize by unseen hard count.
    h_pct = float((h_rank - 1) / max(EXPECTED_HARD_SCALE - 1, 1)) if not is_soft else 1.0
    return [
        is_soft,
        math.log1p(event_count),
        math.log1p(max(int(family.get("anchor_count", 0)), 0)),
        math.log1p(max(int(family.get("quartet_count", 0)), 0)),
        math.log1p(max(int(family.get("component_count", 0)), 0)),
        float(family.get("best_score", 0.0)),
        smin,
        smax,
        sbalance,
        member_year_balance_pair(family, years, event_year_by_id),
        family_centroid_distance_pair(family, years),
        h_pct,
        float(support_count / event_count),
        trigger,
    ]


def event_lookup_pair(
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    lookup: dict[str, dict[str, Any]] = {}
    event_year: dict[str, int] = {}
    require(set(scan_by_year) == set(years), f"scan years {sorted(scan_by_year)} != {list(years)}")
    for year in years:
        for row in scan_by_year[year]:
            eid = str(row["id"])
            require(eid not in lookup, f"duplicate event ID across pair: {eid}")
            lookup[eid] = row
            event_year[eid] = int(year)
    return lookup, event_year


def cohesion_features_pair(
    family: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
    event_year_by_id: dict[str, int],
    years: tuple[int, int],
    support: Any,
    base: Any,
) -> list[float]:
    """Exact #839 v2 cohesion vector with explicit event-year addressing."""
    all_distances: list[float] = []
    per_year_q90: list[float] = []
    counts: list[int] = []
    centroids = family.get("centroids", {})
    for year in years:
        ids = []
        for raw in family["event_ids"]:
            eid = str(raw)
            require(eid in event_year_by_id, f"family member absent from scan: {eid}")
            if int(event_year_by_id[eid]) == year:
                ids.append(eid)
        counts.append(len(ids))
        centroid = centroids.get(str(year))
        distances: list[float] = []
        if centroid is not None:
            for eid in ids:
                row = lookup[eid]
                d = float(support.centroid_distance(row, centroid, base))
                require(math.isfinite(d), f"nonfinite member distance for {eid}")
                distances.append(d)
                all_distances.append(d)
        per_year_q90.append(float(np.quantile(distances, 0.90)) if distances else 10.0)
    cmin, cmax = min(counts), max(counts)
    balance = float(cmin / max(cmax, 1))
    return [
        float(cmin),
        float(cmax),
        balance,
        float(np.median(all_distances)) if all_distances else 10.0,
        float(np.quantile(all_distances, 0.90)) if all_distances else 10.0,
        float(max(all_distances)) if all_distances else 10.0,
        float(max(per_year_q90)),
    ]


def centroid_matrix_pair(families: list[dict[str, Any]], years: tuple[int, int]) -> np.ndarray:
    rows: list[list[float]] = []
    for family in families:
        row: list[float] = []
        for year in years:
            c = family.get("centroids", {}).get(str(year))
            require(c is not None, f"missing centroid {family['family_id']} {year}")
            row += [
                float(c["sol"]),
                float(c["sun_lon"]),
                float(c["ecl_lat"]),
                math.log(max(abs(float(c["vg"])), 1e-6)),
            ]
        rows.append(row)
    out = np.asarray(rows, dtype=np.float64)
    require(out.ndim == 2 and out.shape[1] == 8 and np.all(np.isfinite(out)), "invalid centroid matrix")
    return out


def build_feature_matrix(
    *,
    families: list[dict[str, Any]],
    source_by_id: dict[str, str],
    hard_order: list[str],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    support: Any,
    base: Any,
    frozen_ranker_module: Any,
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, str]]]:
    """Construct the exact 34-dimensional #839 predictor vector without truth labels."""
    require(len(years) == 2 and years[0] != years[1], f"invalid year pair {years}")
    ids = [str(f["family_id"]) for f in families]
    require(len(ids) == len(set(ids)), "duplicate family IDs")
    require(set(ids) == set(source_by_id), "source map does not exactly cover candidate families")
    require(all(source_by_id[fid] in {"hard", "p19", "p20"} for fid in ids), "unknown candidate source")
    hard_rank = {str(fid): i + 1 for i, fid in enumerate(hard_order)}
    require(len(hard_rank) == len(hard_order), "duplicate hard-order ID")
    hard_ids = {fid for fid in ids if source_by_id[fid] == "hard"}
    require(set(hard_order) == hard_ids, "hard order must exactly cover hard candidates")

    lookup, event_year_by_id = event_lookup_pair(scan_by_year, years)
    centroids = centroid_matrix_pair(families, years)
    neighbors = np.asarray(frozen_ranker_module.neighbor_features(centroids), dtype=np.float64)
    require(neighbors.shape == (len(families), 6) and np.all(np.isfinite(neighbors)), "invalid neighbor features")

    rows: list[list[float]] = []
    for i, family in enumerate(families):
        fid = str(family["family_id"])
        source = source_by_id[fid]
        source_features = [float(source == "hard"), float(source == "p19"), float(source == "p20")]
        p20_features = [
            float(family.get("p20_cross_year_distance", 0.0)),
            math.log1p(max(int(family.get("p20_min_anchor_count", 0)), 0)),
            float(family.get("p20_min_bin_strength", 0.0)),
            float(family.get("p20_min_quartet_score", 0.0)),
        ]
        row = (
            structural_features_pair(family, hard_rank, years, event_year_by_id)
            + cohesion_features_pair(family, lookup, event_year_by_id, years, support, base)
            + source_features
            + p20_features
            + neighbors[i].tolist()
        )
        require(len(row) == EXPECTED_FEATURES and all(math.isfinite(float(x)) for x in row), f"invalid feature row {fid}")
        rows.append(row)
    matrix = np.asarray(rows, dtype=np.float64)
    tie = [(hard_rank.get(fid, 999999), fid) for fid in ids]
    return matrix, centroids, tie


def score_and_rank(
    *,
    model_path: Path,
    families: list[dict[str, Any]],
    source_by_id: dict[str, str],
    hard_order: list[str],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    support: Any,
    base: Any,
    frozen_ranker_module: Any,
) -> dict[str, Any]:
    X, centroid_matrix, tie = build_feature_matrix(
        families=families,
        source_by_id=source_by_id,
        hard_order=hard_order,
        scan_by_year=scan_by_year,
        years=years,
        support=support,
        base=base,
        frozen_ranker_module=frozen_ranker_module,
    )
    model = joblib.load(model_path)
    require(int(getattr(model, "n_features_in_", -1)) == EXPECTED_FEATURES, "serialized ranker feature count changed")
    serialized_n_jobs = getattr(model, "n_jobs", None)
    if hasattr(model, "set_params") and serialized_n_jobs is not None:
        model.set_params(n_jobs=1)
    scores = np.asarray(model.predict(X), dtype=np.float64)
    require(scores.shape == (len(families),) and np.all(np.isfinite(scores)), "invalid ranker predictions")
    order_idx = frozen_ranker_module.diversity_order(scores, centroid_matrix, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    require(len(order_idx) == len(families) and len(set(order_idx)) == len(families), "invalid diversity order")
    ids = [str(f["family_id"]) for f in families]
    order = [ids[i] for i in order_idx]
    return {
        "feature_matrix": X,
        "prediction": scores,
        "order": order,
        "order_sha256": hashlib.sha256("\n".join(order).encode()).hexdigest(),
        "years": list(years),
        "candidate_count": len(families),
        "label_inputs_used": False,
        "serialized_model_n_jobs": serialized_n_jobs,
        "prediction_n_jobs": 1,
        "diversity_lambda": DIVERSITY_LAMBDA,
        "diversity_scale": DIVERSITY_SCALE,
    }


def array_sha256(array: np.ndarray) -> str:
    x = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(str(x.dtype).encode())
    h.update(json.dumps(list(x.shape), separators=(",", ":")).encode())
    h.update(x.tobytes(order="C"))
    return h.hexdigest()
