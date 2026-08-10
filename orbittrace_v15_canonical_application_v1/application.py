#!/usr/bin/env python3
"""Common pre-truth v15 nominal-128 application over canonical annual event rows."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Callable, Mapping
from types import SimpleNamespace
from typing import Any

import numpy as np

from orbittrace_v15_canonical_events_v1.canonical import project_existing

FINAL_NOMINAL_CAP = 128
COMPONENT_CAPS = (128, 96, 64)
BROWN_EQ_TOL = 1e-10


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_pair(
    years: tuple[int, int],
    scan_by_year: Mapping[int, list[Mapping[str, Any]]],
) -> dict[int, list[dict[str, Any]]]:
    require(len(years) == 2 and years[0] != years[1], f"invalid ordered year pair {years}")
    require(all(isinstance(y, int) and not isinstance(y, bool) for y in years), "years must be explicit ints")
    require(set(scan_by_year) == set(years), "scan year keys do not match ordered pair")
    out: dict[int, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for year in years:
        rows: list[dict[str, Any]] = []
        for record in scan_by_year[year]:
            row = project_existing(record, allowed_years=years)
            require(row["year"] == year, f"row year {row['year']} stored under {year}")
            require(row["id"] not in seen, f"duplicate canonical event id {row['id']}")
            seen.add(row["id"])
            rows.append(row)
        require(rows, f"empty canonical scan for {year}")
        out[year] = rows
    return out


def adaptive_local_episode(
    family: Mapping[str, Any],
    year: int,
    scan_events: list[dict[str, Any]],
    *,
    cap: int,
    runtime: Any,
    base: Any,
) -> tuple[Any, dict[str, Any]]:
    require(cap in COMPONENT_CAPS, f"unexpected v15 deployment component cap {cap}")
    centroid = family.get("centroids", {}).get(str(year))
    require(centroid is not None, f"family {family.get('family_id')} missing centroid for {year}")
    center_sol = float(centroid["sol"])
    window_events = runtime.window_events_for_center(scan_events, center_sol, base)
    k = min(int(cap), len(window_events))
    require(k >= 4, f"family {family.get('family_id')} year {year} has fewer than four local events")
    anchor = {
        "sol": center_sol,
        "sun_lon": float(centroid["sun_lon"]),
        "ecl_lat": float(centroid["ecl_lat"]),
        "vg": float(centroid["vg"]),
    }
    distances = np.asarray(runtime.exact_wavelet_r2(anchor, window_events), dtype=np.float64)
    require(distances.ndim == 1 and len(distances) == len(window_events), "wavelet distance shape mismatch")
    require(np.isfinite(distances).all(), "nonfinite wavelet distance")
    selected = runtime.stable_smallest_indices(distances, k)
    indices = [int(i) for i in selected]
    require(len(indices) == k and len(set(indices)) == k, "episode index duplication")
    chosen = [window_events[i] for i in indices]
    episode = SimpleNamespace(
        sun_lon=np.asarray([float(row["sun_lon"]) for row in chosen], dtype=np.float64),
        ecl_lat=np.asarray([float(row["ecl_lat"]) for row in chosen], dtype=np.float64),
        vg=np.asarray([float(row["vg"]) for row in chosen], dtype=np.float64),
    )
    return episode, {
        "window_event_count": len(window_events),
        "episode_size": k,
        "episode_cap": int(cap),
        "adaptive_rule": "min(cap,N_local)",
        "selected_max_r2": float(np.max(distances[indices])),
        "centroid": anchor,
    }


def score_component(
    *,
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    cap: int,
    runtime: Any,
    base: Any,
    score_episode: Callable[[Any], tuple[float, float, float, float]],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    require(cap in COMPONENT_CAPS, f"invalid component cap {cap}")
    scored: list[dict[str, Any]] = []
    episode_sizes: list[int] = []
    max_difference = 0.0
    for family in families:
        fid = str(family["family_id"])
        require(sorted(int(y) for y in family["years"]) == sorted(years), f"family years changed: {fid}")
        per_year: dict[str, Any] = {}
        multiplicities: list[float] = []
        for year in years:
            episode, metadata = adaptive_local_episode(
                family, year, scan_by_year[year], cap=cap, runtime=runtime, base=base
            )
            v3_score, brown_score, multiplicity, difference = score_episode(episode)
            v3_score = float(v3_score)
            brown_score = float(brown_score)
            multiplicity = float(multiplicity)
            difference = float(difference)
            require(all(math.isfinite(x) for x in (v3_score, brown_score, multiplicity, difference)),
                    f"nonfinite score for {fid}/{year}/cap{cap}")
            require(brown_score > 0.0, f"nonpositive Brown score for {fid}/{year}/cap{cap}")
            require(difference <= BROWN_EQ_TOL, f"Brown equivalence failed for {fid}/{year}/cap{cap}")
            require(1.0 - 1e-10 <= multiplicity <= 4.0 + 1e-10,
                    f"multiplicity outside [1,4] for {fid}/{year}/cap{cap}")
            episode_sizes.append(int(metadata["episode_size"]))
            max_difference = max(max_difference, difference)
            multiplicities.append(multiplicity)
            per_year[str(year)] = {
                **metadata,
                "v3_score": v3_score,
                "brown_score": brown_score,
                "multiplicity": multiplicity,
                "brown_equivalence_difference": difference,
            }
        require(len(multiplicities) == 2, "component scoring did not cover both years")
        scored.append({
            "family_id": fid,
            "per_year": per_year,
            "multiplicity_worst_year": min(multiplicities),
            "multiplicity_geometric_mean": math.sqrt(multiplicities[0] * multiplicities[1]),
        })
    ordered = sorted(
        scored,
        key=lambda row: (
            -float(row["multiplicity_worst_year"]),
            -float(row["multiplicity_geometric_mean"]),
            str(row["family_id"]),
        ),
    )
    order = [str(row["family_id"]) for row in ordered]
    require(len(order) == len(set(order)) == len(families), f"component cap {cap} order invalid")
    summary = {
        "component_cap": int(cap),
        "family_count": len(families),
        "family_universe_sha256": canonical_sha(sorted(order)),
        "order_sha256": canonical_sha(order),
        "episode_sizes_observed": sorted(set(episode_sizes)),
        "max_brown_equivalence_difference": max_difference,
    }
    return scored, order, summary


def consensus_order(component_orders: Mapping[int, list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
    require(tuple(sorted(component_orders, reverse=True)) == COMPONENT_CAPS,
            f"component cap set changed: {sorted(component_orders)}")
    universe = set(component_orders[FINAL_NOMINAL_CAP])
    require(universe and all(set(component_orders[cap]) == universe for cap in COMPONENT_CAPS),
            "component family universe mismatch")
    require(all(len(component_orders[cap]) == len(universe) for cap in COMPONENT_CAPS),
            "duplicate family in component order")
    rank_maps = {
        cap: {fid: rank for rank, fid in enumerate(component_orders[cap])}
        for cap in COMPONENT_CAPS
    }
    rows: list[dict[str, Any]] = []
    for fid in sorted(universe):
        ranks = [int(rank_maps[cap][fid]) for cap in COMPONENT_CAPS]
        median_rank = float(statistics.median(ranks))
        require(median_rank in tuple(float(x) for x in ranks), f"three-point median identity failed for {fid}")
        rows.append({
            "family_id": fid,
            "component_caps": list(COMPONENT_CAPS),
            "component_ranks_zero_based": ranks,
            "v15_median_rank_score": median_rank,
        })
    rows.sort(key=lambda row: (
        float(row["v15_median_rank_score"]),
        int(row["component_ranks_zero_based"][0]),
        int(row["component_ranks_zero_based"][1]),
        int(row["component_ranks_zero_based"][2]),
        str(row["family_id"]),
    ))
    order = [str(row["family_id"]) for row in rows]
    require(len(order) == len(universe) and set(order) == universe, "invalid v15 consensus order")
    return order, rows


def run_pretruth(
    *,
    years: tuple[int, int],
    scan_by_year: Mapping[int, list[Mapping[str, Any]]],
    family_builder: Callable[[tuple[int, int], dict[int, list[dict[str, Any]]]], list[dict[str, Any]]],
    runtime: Any,
    base: Any,
    score_episode: Callable[[Any], tuple[float, float, float, float]],
) -> dict[str, Any]:
    canonical_scan = validate_pair(years, scan_by_year)
    families = family_builder(years, canonical_scan)
    require(isinstance(families, list) and families, "frozen family builder returned no families")
    family_ids = [str(f["family_id"]) for f in families]
    require(len(family_ids) == len(set(family_ids)), "duplicate recurrent family id")

    component_orders: dict[int, list[str]] = {}
    component_summaries: dict[str, Any] = {}
    component_scores: dict[str, Any] = {}
    for cap in COMPONENT_CAPS:
        scored, order, summary = score_component(
            families=families,
            scan_by_year=canonical_scan,
            years=years,
            cap=cap,
            runtime=runtime,
            base=base,
            score_episode=score_episode,
        )
        component_orders[cap] = order
        component_summaries[str(cap)] = summary
        component_scores[str(cap)] = scored

    order, rows = consensus_order(component_orders)
    universe_hashes = {x["family_universe_sha256"] for x in component_summaries.values()}
    require(len(universe_hashes) == 1, "component universe hash mismatch")
    return {
        "method": "orbittrace_multiscale_consensus_v15_nominal128_canonical_application",
        "years": list(years),
        "nominal_cap": FINAL_NOMINAL_CAP,
        "component_caps": list(COMPONENT_CAPS),
        "family_count": len(families),
        "family_universe_sha256": next(iter(universe_hashes)),
        "component_summaries": component_summaries,
        "component_orders": {str(k): v for k, v in component_orders.items()},
        "component_scores": component_scores,
        "v15_rows": rows,
        "v15_order": order,
        "v15_order_sha256": canonical_sha(order),
        "labels_read": False,
        "survey_conditioned_science": False,
    }
