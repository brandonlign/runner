#!/usr/bin/env python3
"""Pair-portable, label-free candidate generation for the frozen #839 URC architecture.

This module does not change any detector rule. It exposes the already-frozen hard-v8, P19 and
P20 proposal layers as functions of an explicit ordered two-year pair and a pre-truth raw scan.
The development sources themselves are retained unchanged; only literal development-year
addressing in P20 is generalized to the supplied pair.

No known-shower labels are accepted by this module.
"""
from __future__ import annotations

import hashlib
from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def configure_pair(
    years: tuple[int, int],
    *,
    support: Any,
    mult: Any,
    v6: Any,
    v8: Any,
    p19: Any,
    p20: Any,
) -> tuple[str, ...]:
    require(len(years) == 2 and years[0] != years[1], f"invalid year pair {years}")
    month_keys = tuple(f"{year}-{month:02d}" for year in years for month in range(1, 13))
    support.YEARS = years
    support.MONTH_KEYS = month_keys
    support.RANKING_VARIANTS = ("persistence",)
    mult.YEARS = years
    mult.MONTH_KEYS = month_keys
    mult.TOP_K = 100
    # v6 is the shared label-free within-year proposal source imported by P19/P20.
    # Rebind it explicitly rather than relying on its development defaults.
    v6.YEARS = years
    v6.MONTH_KEYS = month_keys
    v8.YEARS = years
    v8.MONTH_KEYS = month_keys
    p19.YEARS = years
    p19.MONTH_KEYS = month_keys
    p20.YEARS = years
    p20.MONTH_KEYS = month_keys
    return month_keys


def build_hard_v8_pair(
    *,
    years: tuple[int, int],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    runtime: Any,
    v6: Any,
    v8: Any,
    mult: Any,
) -> dict[str, Any]:
    """Reproduce the exact v8 hard family graph/ranking on an arbitrary supplied pair."""
    require(set(scan_by_year) == set(years), f"scan years {sorted(scan_by_year)} != {list(years)}")
    components: list[dict[str, Any]] = []
    components_by_year: dict[int, list[dict[str, Any]]] = {}
    passing_by_year: dict[int, list[dict[str, Any]]] = {}
    scan_audits: list[dict[str, Any]] = []
    for year in years:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_by_year[year] = passing
        components_by_year[year] = year_components
        components.extend(year_components)

    hard_families, support_rankings = support.build_families(components, base)
    require(len({str(f["family_id"]) for f in hard_families}) == len(hard_families), "hard family IDs collide")
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(set(persistence_order) == {str(f["family_id"]) for f in hard_families}, "hard persistence order incomplete")

    # v8's repair function is scientifically pair-generic once its YEARS global is rebound.
    repair = v8.repair_year_centroids(hard_families, components, scan_by_year, support, base)
    scored, scoring_summary = mult.score_families(hard_families, scan_by_year, runtime, base)
    hard_order = [str(x) for x in mult.rank_scored(scored, "multiplicity")]
    require(set(hard_order) == {str(f["family_id"]) for f in hard_families}, "hard multiplicity order incomplete")
    return {
        "hard_families": hard_families,
        "hard_order": hard_order,
        "components": components,
        "components_by_year": components_by_year,
        "passing_by_year": passing_by_year,
        "scan_audits": scan_audits,
        "repair": repair,
        "scoring_summary": scoring_summary,
    }


def build_p19_pair(
    *,
    years: tuple[int, int],
    hard: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    p19: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Exact P19 recurrence layer after pair globals have been rebound."""
    require(tuple(p19.YEARS) == tuple(years), "P19 pair configuration changed")
    # The frozen P19 execution set this support context before building the layer.
    # Preserve it exactly; the string is not allowed to become an unseen-data tuning knob.
    support.CORPUS = p19.CORPUS
    soft, diagnostics = p19.build_soft_recurrence(
        hard["components"], hard["hard_families"], scan_by_year, support, base
    )
    require(len({str(f["family_id"]) for f in soft}) == len(soft), "P19 family IDs collide")
    return soft, diagnostics


def build_p20_recurrent_pair(
    *,
    years: tuple[int, int],
    quartets_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    p20: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Exact P20 mutual-nearest 4+4 construction with year keys made pair-relative.

    The original P20 development helper hardcodes 2022/2023 in this one function. Every
    scientific operation, tie break, radius, ID construction, membership rule and sort key below
    is copied exactly; only the two year values/JSON keys come from `years`.
    """
    first, second = years
    qa = quartets_by_year[first]
    qb = quartets_by_year[second]
    by_id = {str(q["quartet_id"]): q for q in qa + qb}
    require(len(by_id) == len(qa) + len(qb), "P20 quartet IDs collide across pair")
    ma, da, aa = p20.nearest_other_year(qa, qb, support, base)
    mb, db, ab = p20.nearest_other_year(qb, qa, support, base)

    families: list[dict[str, Any]] = []
    for qa_id in sorted(ma):
        qb_id = ma[qa_id]
        if mb.get(qb_id) != qa_id:
            continue
        q_a = by_id[qa_id]
        q_b = by_id[qb_id]
        d = float(da[(qa_id, qb_id)])
        reverse_d = float(db[(qb_id, qa_id)])
        require(abs(d - reverse_d) < 1e-12, "reciprocal quartet distance mismatch")
        require(d <= float(p20.LINK_RADIUS), "reciprocal quartet pair exceeds inherited radius")
        event_ids = sorted(set(q_a["quartet_ids"]) | set(q_b["quartet_ids"]))
        require(len(event_ids) == 8, "P20 recurrent isolated-quartet family is not exact 4+4")
        stable = hashlib.sha256((qa_id + "|" + qb_id).encode()).hexdigest()[:16]
        family = {
            "family_id": "RIQ" + stable,
            "family_type": "recurrent_isolated_quartet_4plus4",
            "years": [first, second],
            "year_count": 2,
            "component_ids": [],
            "component_count": 0,
            "event_ids": event_ids,
            "event_count": 8,
            "quartet_count": 2,
            "anchor_count": int(q_a["anchor_count"] + q_b["anchor_count"]),
            "best_score": float(max(q_a["score"], q_b["score"])),
            "year_strengths": {
                str(first): float(q_a["bin_strength"]),
                str(second): float(q_b["bin_strength"]),
            },
            "centroids": {
                str(first): q_a["centroid"],
                str(second): q_b["centroid"],
            },
            "ranks": {},
            "ranking_scores": {},
            "p20_quartet_ids": {str(first): qa_id, str(second): qb_id},
            "p20_cross_year_distance": d,
            "p20_min_anchor_count": int(min(q_a["anchor_count"], q_b["anchor_count"])),
            "p20_min_bin_strength": float(min(q_a["bin_strength"], q_b["bin_strength"])),
            "p20_min_quartet_score": float(min(q_a["score"], q_b["score"])),
        }
        families.append(family)

    families.sort(key=lambda f: (
        float(f["p20_cross_year_distance"]),
        -int(f["p20_min_anchor_count"]),
        -float(f["p20_min_bin_strength"]),
        -float(f["p20_min_quartet_score"]),
        str(f["family_id"]),
    ))
    require(len({str(f["family_id"]) for f in families}) == len(families), "P20 family IDs not unique")
    require(len({tuple(f["event_ids"]) for f in families}) == len(families), "P20 event sets not unique")
    diagnostics = {
        f"{first}_to_{second}": aa,
        f"{second}_to_{first}": ab,
        "mutual_reciprocal_family_count": len(families),
        "all_family_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in families),
        "all_pair_distances_within_inherited_1_5": all(float(f["p20_cross_year_distance"]) <= float(p20.LINK_RADIUS) for f in families),
        "membership_expansion": False,
        "recursion": False,
        "new_scientific_radius": False,
    }
    return families, diagnostics


def build_p20_pair(
    *,
    years: tuple[int, int],
    hard: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    p20: Any,
) -> dict[str, Any]:
    # Preserve the frozen P20 support context independently of P19.
    support.CORPUS = p20.CORPUS
    quartets_by_year: dict[int, list[dict[str, Any]]] = {}
    isolated_audits: dict[str, Any] = {}
    for year in years:
        quartets, audit = p20.isolated_quartets(
            year,
            hard["passing_by_year"][year],
            hard["components_by_year"][year],
            scan_by_year[year],
            support,
        )
        quartets_by_year[year] = quartets
        isolated_audits[str(year)] = audit
    soft, diagnostics = build_p20_recurrent_pair(
        years=years,
        quartets_by_year=quartets_by_year,
        support=support,
        base=base,
        p20=p20,
    )
    return {
        "soft_families": soft,
        "quartets_by_year": quartets_by_year,
        "isolated_audits": isolated_audits,
        "soft_diagnostics": diagnostics,
    }


def build_union_pair(
    *,
    years: tuple[int, int],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
    runtime: Any,
    v6: Any,
    v8: Any,
    p19: Any,
    p20: Any,
    mult: Any,
) -> dict[str, Any]:
    configure_pair(years, support=support, mult=mult, v6=v6, v8=v8, p19=p19, p20=p20)
    # P19's frozen run constructs the shared hard graph in the P19 support context.
    # Hard structures are known to be identical in the P19 and P20 frozen artifacts.
    support.CORPUS = p19.CORPUS
    hard = build_hard_v8_pair(
        years=years,
        scan_by_year=scan_by_year,
        support=support,
        base=base,
        runtime=runtime,
        v6=v6,
        v8=v8,
        mult=mult,
    )
    p19_soft, p19_diag = build_p19_pair(
        years=years,
        hard=hard,
        scan_by_year=scan_by_year,
        support=support,
        base=base,
        p19=p19,
    )
    p20_result = build_p20_pair(
        years=years,
        hard=hard,
        scan_by_year=scan_by_year,
        support=support,
        base=base,
        p20=p20,
    )
    p20_soft = p20_result["soft_families"]
    families = hard["hard_families"] + p19_soft + p20_soft
    source_by_id = {str(f["family_id"]): "hard" for f in hard["hard_families"]}
    source_by_id.update({str(f["family_id"]): "p19" for f in p19_soft})
    source_by_id.update({str(f["family_id"]): "p20" for f in p20_soft})
    require(len(source_by_id) == len(families), "union family IDs collide")
    return {
        "years": list(years),
        "hard": hard,
        "p19_soft": p19_soft,
        "p19_diagnostics": p19_diag,
        "p20": p20_result,
        "families": families,
        "source_by_id": source_by_id,
        "hard_order": hard["hard_order"],
        "truth_labels_used": False,
    }
