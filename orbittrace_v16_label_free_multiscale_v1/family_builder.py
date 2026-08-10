#!/usr/bin/env python3
"""Pair-portable label-free recurrent-family builder for OrbitTrace v16.

This is the exact scientific proposal architecture that passed as label-free sparse-support v6:
64-neighbor first shortlist, 128-neighbor audit shortlist, anchored quartets, anchor multiplicity
>=2, top 512 quartets per 10-degree bin, exact frozen component construction, and exact frozen
cross-year family linkage. It accepts only canonical target-excluded rows and never accepts labels
or a calibration/null set.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np
from sklearn.neighbors import NearestNeighbors

from orbittrace_v15_canonical_events_v1.canonical import BLIND_HIGH, BLIND_LOW, project_existing

FIRST_SHORTLIST = 64
AUDIT_SHORTLIST = 128
MIN_ANCHOR_COUNT = 2
MAX_QUARTETS_PER_BIN = 512
FAMILY_LINK_RADIUS = 1.5
MIN_COMPONENT_EVENTS = 4
MIN_COMPONENT_QUARTETS = 2
MIN_FAMILY_YEARS = 2
RANKING_VARIANTS = (
    "persistence",
    "mean_year_strength",
    "sqrt_support_strength",
    "min_year_strength",
    "size_penalized_strength",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def _validate_scan(
    years: tuple[int, int],
    scan_by_year: Mapping[int, list[Mapping[str, Any]]],
) -> dict[int, list[dict[str, Any]]]:
    require(len(years) == 2 and years[0] != years[1], f"invalid year pair {years}")
    require(set(scan_by_year) == set(years), "scan year keys do not match pair")
    out: dict[int, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for year in years:
        rows: list[dict[str, Any]] = []
        for raw in scan_by_year[year]:
            row = project_existing(raw, allowed_years=years)
            require(row["year"] == year, f"row year {row['year']} stored under {year}")
            require(not (BLIND_LOW <= float(row["sol"]) <= BLIND_HIGH), "target-region row reached label-free family builder")
            require(row["id"] not in seen, f"duplicate canonical event id {row['id']}")
            seen.add(row["id"])
            rows.append(row)
        require(rows, f"empty canonical scan for {year}")
        out[year] = rows
    return out


def label_free_scan_year(
    year: int,
    events: list[dict[str, Any]],
    *,
    support: Any,
    base: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Exact label-free v6 anchored-quartet scan on one canonical year."""
    event_lookup = {str(e["id"]): e for e in events}
    require(len(event_lookup) == len(events), "duplicate event IDs within year")
    passing: list[dict[str, Any]] = []
    scannable_bins: list[int] = []
    passing_anchor_count = 0
    shortlist_audit_failures = 0
    per_bin: list[dict[str, Any]] = []

    for bin_index in range(36):
        low = bin_index * 10.0
        high = (bin_index + 1) * 10.0
        center = low + 5.0
        anchors = [e for e in events if low <= float(e["sol"]) < high]
        pool = [e for e in events if abs(float(base.wrap180(float(e["sol"]) - center))) <= 15.0]
        if len(pool) < AUDIT_SHORTLIST or not anchors:
            continue
        scannable_bins.append(bin_index)
        pool_index = {str(e["id"]): i for i, e in enumerate(pool)}
        features = support.feature_matrix(pool, center, base)
        k_query = min(AUDIT_SHORTLIST, len(pool))
        nn = NearestNeighbors(n_neighbors=k_query, algorithm="auto", metric="euclidean", n_jobs=-1).fit(features)
        anchor_rows = np.asarray([pool_index[str(e["id"])] for e in anchors], dtype=np.int64)
        _, neighbor_indices = nn.kneighbors(features[anchor_rows], return_distance=True)
        local_dedup: dict[tuple[str, ...], dict[str, Any]] = {}
        bin_anchor_examined = 0

        for anchor, candidates_idx in zip(anchors, neighbor_indices):
            candidate_events = [
                pool[int(i)] for i in candidates_idx
                if str(pool[int(i)]["id"]) != str(anchor["id"])
            ]
            first = candidate_events[: max(3, FIRST_SHORTLIST - 1)]
            distances = support.exact_anchor_distances(anchor, first, base)
            order = np.argsort(distances, kind="stable")[:3]
            quartet = [anchor] + [first[int(i)] for i in order]
            score = float(support.quartet_score(quartet, base))

            full = candidate_events[: max(3, AUDIT_SHORTLIST - 1)]
            full_distances = support.exact_anchor_distances(anchor, full, base)
            full_order = np.argsort(full_distances, kind="stable")[:3]
            audit_quartet = [anchor] + [full[int(i)] for i in full_order]
            audit_score = float(support.quartet_score(audit_quartet, base))
            ids = tuple(sorted(str(e["id"]) for e in quartet))
            audit_ids = tuple(sorted(str(e["id"]) for e in audit_quartet))
            if ids != audit_ids or abs(score - audit_score) > 1e-12:
                shortlist_audit_failures += 1
                quartet = audit_quartet
                score = audit_score
                ids = audit_ids

            passing_anchor_count += 1
            bin_anchor_examined += 1
            record = local_dedup.get(ids)
            if record is None:
                local_dedup[ids] = {
                    "year": year,
                    "bin": bin_index,
                    "quartet_ids": list(ids),
                    "score": score,
                    "threshold": None,
                    "anchor_count": 1,
                    "anchor_ids": [str(anchor["id"])],
                    "label_free_structural_proposal": True,
                }
            else:
                record["anchor_count"] += 1
                record["anchor_ids"].append(str(anchor["id"]))
                record["score"] = max(float(record["score"]), score)

        retained = [r for r in local_dedup.values() if int(r["anchor_count"]) >= MIN_ANCHOR_COUNT]
        retained.sort(key=lambda row: (-int(row["anchor_count"]), -float(row["score"]), row["quartet_ids"]))
        pre_cap = len(retained)
        retained = retained[:MAX_QUARTETS_PER_BIN]
        count = len(retained)
        for rank, record in enumerate(retained, 1):
            rank_fraction = (rank - 0.5) / max(1, count)
            record["bin_rank"] = rank
            record["bin_count"] = count
            record["bin_strength"] = -math.log10(rank_fraction)
        passing.extend(retained)
        per_bin.append({
            "bin": bin_index,
            "anchors": len(anchors),
            "pool": len(pool),
            "anchored_quartets_examined": bin_anchor_examined,
            "unique_quartets_before_anchor_gate": len(local_dedup),
            "anchor_multiplicity_pass_before_cap": pre_cap,
            "retained_after_fixed_512_cap": count,
        })

    passing.sort(key=lambda row: (int(row["bin"]), int(row["bin_rank"]), row["quartet_ids"]))
    components = support.component_records(year, passing, event_lookup)
    audit = {
        "year": year,
        "scan_events": len(events),
        "scannable_bins": scannable_bins,
        "scannable_bin_count": len(scannable_bins),
        "passing_anchor_count": passing_anchor_count,
        "retained_quartets": len(passing),
        "components": len(components),
        "shortlist_audit_failures": shortlist_audit_failures,
        "per_bin": per_bin,
        "calibration_events_used": 0,
        "source_labels_used_for_proposals": False,
        "score_threshold_applied": False,
        "first_shortlist": FIRST_SHORTLIST,
        "audit_shortlist": AUDIT_SHORTLIST,
        "min_anchor_count": MIN_ANCHOR_COUNT,
        "max_quartets_per_bin": MAX_QUARTETS_PER_BIN,
    }
    return audit, passing, components


def build_families(
    *,
    years: tuple[int, int],
    scan_by_year: Mapping[int, list[Mapping[str, Any]]],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build exact recurrent v6 families from a canonical two-year pair."""
    scan = _validate_scan(years, scan_by_year)
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "support blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == MIN_FAMILY_YEARS, "support family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - FAMILY_LINK_RADIUS) < 1e-15, "support family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == MIN_COMPONENT_EVENTS, "support component event minimum changed")
    require(int(support.MIN_COMPONENT_QUARTETS) == MIN_COMPONENT_QUARTETS, "support component quartet minimum changed")
    require(int(support.SHORTLIST_K) == FIRST_SHORTLIST, "support first shortlist changed")
    require(int(support.AUDIT_SHORTLIST_K) == AUDIT_SHORTLIST, "support audit shortlist changed")
    require(int(support.MIN_ANCHOR_COUNT) == MIN_ANCHOR_COUNT, "support anchor-count gate changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == MAX_QUARTETS_PER_BIN, "support per-bin cap changed")
    for name in ("feature_matrix", "exact_anchor_distances", "quartet_score", "component_records", "build_families"):
        require(hasattr(support, name), f"frozen support missing {name}")

    support.YEARS = years
    support.MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in years for month in range(1, 13))
    support.RANKING_VARIANTS = RANKING_VARIANTS

    components: list[dict[str, Any]] = []
    scans: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in years:
        audit, passing, year_components = label_free_scan_year(year, scan[year], support=support, base=base)
        scans.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)

    families, rankings = support.build_families(components, base)
    family_ids = [str(f["family_id"]) for f in families]
    persistence = [str(x) for x in rankings["persistence"]]
    require(len(family_ids) == len(set(family_ids)), "duplicate recurrent family id")
    require(set(persistence) == set(family_ids) and len(persistence) == len(family_ids), "persistence universe mismatch")
    require(all(sorted(int(y) for y in f["years"]) == sorted(years) for f in families), "nonrecurrent family survived")
    return families, {
        "scan_audits": scans,
        "passing_quartet_counts": passing_counts,
        "persistence_order": persistence,
        "family_count": len(families),
        "labels_read": False,
        "calibration_events_used": 0,
        "score_threshold_applied": False,
    }
