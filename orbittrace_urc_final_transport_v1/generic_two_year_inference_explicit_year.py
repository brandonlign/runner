#!/usr/bin/env python3
"""Final generic two-year URC transport using explicit event-year addressing.

Candidate generation replays the frozen hard-v8/P19/P20 algorithms without assuming any event-ID
format. Ranking delegates to the pre-result #860 unseen-ranker application source, whose only
adaptation is explicit year addressing and which must independently reproduce #853 hashes on GMN.
"""
from __future__ import annotations

from typing import Any

from orbittrace_urc_final_transport_v1 import generic_two_year_inference as legacy


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


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
    require(len(years) == 2 and years[0] != years[1], "exactly two distinct years required")
    require(set(scan_by_year) == set(years), "scan year keys differ from requested pair")
    seen: set[str] = set()
    for year in years:
        for event in scan_by_year[year]:
            eid = str(event["id"])
            require(eid not in seen, f"duplicate event ID across two-year scan: {eid}")
            seen.add(eid)
            # Input bucket, not the ID string, is the authoritative year address.
            if "year" in event:
                require(int(event["year"]) == year, f"explicit event year/bucket mismatch: {eid}")

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
    require(abs(float(support.FAMILY_LINK_RADIUS) - legacy.LINK_RADIUS) < 1e-15, "family link radius changed")
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

    p19_soft, p19_diag = p19.build_soft_recurrence(components, hard, scan_by_year, support, base)

    quartets_by_year: dict[int, list[dict[str, Any]]] = {}
    p20_isolated_audits: dict[str, Any] = {}
    for year in years:
        quartets, audit = p20.isolated_quartets(
            year, passing_by_year[year], components_by_year[year], scan_by_year[year], support
        )
        quartets_by_year[year] = quartets
        p20_isolated_audits[str(year)] = audit
    p20_soft, p20_diag = legacy._generic_p20_recurrence(p20, quartets_by_year, years, support, base)

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
            "event_year_addressing": "explicit input scan bucket; event ID format ignored",
        },
    }


def rank_generated_union(
    generated: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    years: tuple[int, int],
    support: Any,
    base: Any,
    frozen_ranker_module: Any,
    unseen_application: Any,
    model_path: Any,
) -> dict[str, Any]:
    return unseen_application.score_and_rank(
        model_path=model_path,
        families=generated["families"],
        source_by_id=generated["source_by_id"],
        hard_order=generated["hard_order"],
        scan_by_year=scan_by_year,
        years=years,
        support=support,
        base=base,
        frozen_ranker_module=frozen_ranker_module,
    )
