#!/usr/bin/env python3
"""Generic two-year inference adapter for the frozen active URC architecture.

This module contains no parser or data access. It accepts an already-normalized two-year scan,
replays the frozen hard-v8 + P19 + P20 candidate generator, builds the exact #839 feature vector,
and applies the already-fitted full-GMN ranker plus frozen diversity rule.

The only transport adaptation is replacing development year symbols with the supplied two-year
pair. Scientific scales, proposal rules, candidate semantics, feature formulas, model, and
ranking rule are unchanged.
"""
from __future__ import annotations

import hashlib
import math
from collections import Counter
from typing import Any

import numpy as np


EXPECTED_FEATURE_COLUMNS = 34
LINK_RADIUS = 1.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def _year_from_id(eid: str) -> int:
    text = str(eid)
    require(len(text) >= 4 and text[:4].isdigit(), f"event ID must begin with four-digit year: {text}")
    return int(text[:4])


def generic_family_centroid_distance(family: dict[str, Any], years: tuple[int, int]) -> float:
    c = family.get("centroids", {})
    a = c.get(str(years[0]))
    b = c.get(str(years[1]))
    if not a or not b:
        return 10.0

    def cd(x: float, y: float) -> float:
        return abs((float(x) - float(y) + 180.0) % 360.0 - 180.0)

    d_sol = cd(a["sol"], b["sol"]) / 10.0
    d_sun = cd(a["sun_lon"], b["sun_lon"]) / 4.0
    d_lat = abs(float(a["ecl_lat"]) - float(b["ecl_lat"])) / 4.0
    va = max(abs(float(a["vg"])), 1e-6)
    vb = max(abs(float(b["vg"])), 1e-6)
    d_v = abs(math.log(va / vb)) / math.log(1.10)
    return float(math.sqrt(d_sol * d_sol + d_sun * d_sun + d_lat * d_lat + d_v * d_v))


def generic_member_year_balance(family: dict[str, Any], years: tuple[int, int]) -> float:
    counts = Counter(_year_from_id(str(eid)) for eid in family["event_ids"])
    a = int(counts.get(years[0], 0))
    b = int(counts.get(years[1], 0))
    return float(min(a, b) / max(a, b, 1))


def patch_rank_feature_years(urc: Any, years: tuple[int, int]) -> None:
    """Apply year-symbol transport only to exact #839 feature modules."""
    v1, v2 = urc.v1, urc.v2
    urc.YEARS = years
    v1.YEARS = years
    v2.YEARS = years
    v1.family_centroid_distance = lambda family: generic_family_centroid_distance(family, years)
    v1.member_year_balance = lambda family: generic_member_year_balance(family, years)


def _generic_p20_recurrence(
    p20: Any,
    quartets_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Exact P20 4+4 recurrence semantics with only year labels generalized."""
    y0, y1 = years
    qa = quartets_by_year[y0]
    qb = quartets_by_year[y1]
    by_id = {str(q["quartet_id"]): q for q in qa + qb}
    m01, d01, a01 = p20.nearest_other_year(qa, qb, support, base)
    m10, d10, a10 = p20.nearest_other_year(qb, qa, support, base)
    families: list[dict[str, Any]] = []
    for q0_id in sorted(m01):
        q1_id = m01[q0_id]
        if m10.get(q1_id) != q0_id:
            continue
        q0 = by_id[q0_id]
        q1 = by_id[q1_id]
        d = float(d01[(q0_id, q1_id)])
        reverse_d = float(d10[(q1_id, q0_id)])
        require(abs(d - reverse_d) < 1e-12, "reciprocal quartet distance mismatch")
        require(d <= LINK_RADIUS, "P20 pair exceeds inherited 1.5 radius")
        event_ids = sorted(set(map(str, q0["quartet_ids"])) | set(map(str, q1["quartet_ids"])))
        require(len(event_ids) == 8, "P20 family is not exact 4+4")
        stable = hashlib.sha256((q0_id + "|" + q1_id).encode()).hexdigest()[:16]
        families.append({
            "family_id": "RIQ" + stable,
            "family_type": "recurrent_isolated_quartet_4plus4",
            "years": [y0, y1],
            "year_count": 2,
            "component_ids": [],
            "component_count": 0,
            "event_ids": event_ids,
            "event_count": 8,
            "quartet_count": 2,
            "anchor_count": int(q0["anchor_count"] + q1["anchor_count"]),
            "best_score": float(max(q0["score"], q1["score"])),
            "year_strengths": {str(y0): float(q0["bin_strength"]), str(y1): float(q1["bin_strength"])},
            "centroids": {str(y0): q0["centroid"], str(y1): q1["centroid"]},
            "ranks": {},
            "ranking_scores": {},
            "p20_quartet_ids": {str(y0): q0_id, str(y1): q1_id},
            "p20_cross_year_distance": d,
            "p20_min_anchor_count": int(min(q0["anchor_count"], q1["anchor_count"])),
            "p20_min_bin_strength": float(min(q0["bin_strength"], q1["bin_strength"])),
            "p20_min_quartet_score": float(min(q0["score"], q1["score"])),
        })
    families.sort(key=lambda f: (
        float(f["p20_cross_year_distance"]),
        -int(f["p20_min_anchor_count"]),
        -float(f["p20_min_bin_strength"]),
        -float(f["p20_min_quartet_score"]),
        str(f["family_id"]),
    ))
    require(len({str(f["family_id"]) for f in families}) == len(families), "P20 family ID collision")
    require(len({tuple(f["event_ids"]) for f in families}) == len(families), "P20 event-set collision")
    return families, {
        f"{y0}_to_{y1}": a01,
        f"{y1}_to_{y0}": a10,
        "mutual_reciprocal_family_count": len(families),
        "all_family_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in families),
        "all_pair_distances_within_inherited_1_5": all(float(f["p20_cross_year_distance"]) <= LINK_RADIUS for f in families),
        "membership_expansion": False,
        "recursion": False,
        "new_scientific_radius": False,
    }


def generate_union_from_scan(
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    runtime: Any,
    support: Any,
    base: Any,
    v6: Any,
    v8: Any,
    p19: Any,
    p20: Any,
) -> dict[str, Any]:
    """Generate exact hard/P19/P20 candidate classes from normalized label-free rows."""
    require(len(years) == 2 and years[0] != years[1], "exactly two distinct years required")
    require(sorted(scan_by_year) == sorted(years), "scan year keys differ from requested pair")
    for year in years:
        for event in scan_by_year[year]:
            require(_year_from_id(str(event["id"])) == year, f"event ID/year mismatch: {event['id']}")

    # Year-symbol transport. All numerical scientific constants remain imported from frozen source.
    v6.YEARS = years
    v8.YEARS = years
    p19.YEARS = years
    p20.YEARS = years
    v6.mult.YEARS = years
    v6.mult.TOP_K = 100
    support.YEARS = years
    support.RANKING_VARIANTS = ("persistence",)
    require(int(support.MIN_COMPONENT_EVENTS) == 4, "component event floor changed")
    require(int(support.MIN_COMPONENT_QUARTETS) == 2, "component quartet floor changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence floor changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - LINK_RADIUS) < 1e-15, "family link radius changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2, "anchor multiplicity changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == 512, "quartet cap changed")

    components: list[dict[str, Any]] = []
    components_by_year: dict[int, list[dict[str, Any]]] = {}
    passing_by_year: dict[int, list[dict[str, Any]]] = {}
    scan_audits = []
    for year in years:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_by_year[year] = passing
        components_by_year[year] = year_components
        components.extend(year_components)

    hard, support_rankings = support.build_families(components, base)
    repair = v8.repair_year_centroids(hard, components, scan_by_year, support, base)
    hard_scored, hard_scoring = v6.mult.score_families(hard, scan_by_year, runtime, base)
    hard_order = [str(x) for x in v6.mult.rank_scored(hard_scored, "multiplicity")]
    require(set(hard_order) == {str(f["family_id"]) for f in hard}, "hard multiplicity order incomplete")

    # P19 build function is already generic once its frozen YEARS symbol is transported.
    p19_soft, p19_diag = p19.build_soft_recurrence(components, hard, scan_by_year, support, base)

    # P20 isolated-quartet step is year-generic; only its final constructor originally spelled 2022/23.
    quartets_by_year: dict[int, list[dict[str, Any]]] = {}
    p20_isolated_audits: dict[str, Any] = {}
    for year in years:
        quartets, audit = p20.isolated_quartets(
            year, passing_by_year[year], components_by_year[year], scan_by_year[year], support
        )
        quartets_by_year[year] = quartets
        p20_isolated_audits[str(year)] = audit
    p20_soft, p20_diag = _generic_p20_recurrence(p20, quartets_by_year, years, support, base)

    hard_ids = {str(f["family_id"]) for f in hard}
    p19_ids = {str(f["family_id"]) for f in p19_soft}
    p20_ids = {str(f["family_id"]) for f in p20_soft}
    require(not (hard_ids & p19_ids or hard_ids & p20_ids or p19_ids & p20_ids), "candidate ID collision across sources")
    families = hard + p19_soft + p20_soft
    return {
        "families": families,
        "hard_families": hard,
        "p19_soft_families": p19_soft,
        "p20_soft_families": p20_soft,
        "hard_order": hard_order,
        "source_by_id": {
            **{str(f["family_id"]): "hard" for f in hard},
            **{str(f["family_id"]): "p19" for f in p19_soft},
            **{str(f["family_id"]): "p20" for f in p20_soft},
        },
        "diagnostics": {
            "years": list(years),
            "scan_audits": scan_audits,
            "component_count": len(components),
            "component_counts_by_year": {str(y): len(components_by_year[y]) for y in years},
            "hard_count": len(hard),
            "p19_count": len(p19_soft),
            "p20_count": len(p20_soft),
            "union_count": len(families),
            "hard_support_rank_count": len(support_rankings["persistence"]),
            "pooled_centroid_repair": repair,
            "hard_scoring": hard_scoring,
            "p19": p19_diag,
            "p20_isolated": p20_isolated_audits,
            "p20": p20_diag,
        },
    }


def feature_matrix_for_union(
    generated: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    urc: Any,
    support: Any,
    base: Any,
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, str]]]:
    """Build exact #839 features and centroid matrix for unseen generated candidates."""
    patch_rank_feature_years(urc, years)
    families = generated["families"]
    source_by_id = generated["source_by_id"]
    hard_order = generated["hard_order"]
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    lookup = urc.v2.event_lookup(scan_by_year)
    cm = urc.centroid_matrix(families)
    nf = urc.neighbor_features(cm)
    rows: list[list[float]] = []
    ties: list[tuple[int, str]] = []
    for i, family in enumerate(families):
        fid = str(family["family_id"])
        src = source_by_id[fid]
        source_feats = [float(src == "hard"), float(src == "p19"), float(src == "p20")]
        p20_feats = [
            float(family.get("p20_cross_year_distance", 0.0)),
            math.log1p(max(int(family.get("p20_min_anchor_count", 0)), 0)),
            float(family.get("p20_min_bin_strength", 0.0)),
            float(family.get("p20_min_quartet_score", 0.0)),
        ]
        rows.append(
            urc.v1.structural_features(family, hard_rank)
            + urc.v2.cohesion_features(family, lookup, support, base)
            + source_feats
            + p20_feats
            + nf[i].tolist()
        )
        ties.append((hard_rank.get(fid, 999999), fid))
    X = np.asarray(rows, dtype=np.float64)
    require(X.shape == (len(families), EXPECTED_FEATURE_COLUMNS), f"unexpected feature shape: {X.shape}")
    require(np.all(np.isfinite(X)), "nonfinite final inference features")
    return X, cm, ties


def rank_generated_union(
    generated: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    urc: Any,
    support: Any,
    base: Any,
    fitted_model: Any,
) -> dict[str, Any]:
    X, cm, ties = feature_matrix_for_union(generated, scan_by_year, years, urc, support, base)
    scores = np.asarray(fitted_model.predict(X), dtype=np.float64)
    require(scores.shape == (len(generated["families"]),) and np.all(np.isfinite(scores)), "invalid model scores")
    indices = urc.diversity_order(scores, cm, 0.8, 1.0, ties)
    ids = [str(generated["families"][i]["family_id"]) for i in indices]
    require(len(ids) == len(set(ids)) == len(generated["families"]), "final rank is incomplete")
    return {
        "order": ids,
        "scores_by_id": {str(f["family_id"]): float(score) for f, score in zip(generated["families"], scores.tolist())},
        "feature_matrix": X,
        "centroid_matrix": cm,
    }
