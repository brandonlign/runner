#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

RADIUS = 1.0
MIN_SUPPORT = 4
LOCAL_PASSES = 1


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def _members(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def local_renormalized_basin_cut(
    structural: Any,
    support_pruned: Any,
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One-pass local density renormalization of promoted support-pruned terminals.

    No new geometric or support parameter is introduced. Each already-selected terminal
    basin is re-fit exactly once using the same radius=1/support=4 method on its induced
    event set. The parent is replaced iff the local pass yields at least two reportable
    basins. Parent and local children never coexist in the final partition.
    """
    req(float(support_pruned.RADIUS) == RADIUS, "support-pruned radius changed")
    req(int(support_pruned.MIN_SUPPORT) == MIN_SUPPORT, "support-pruned support changed")
    req(LOCAL_PASSES == 1, "local pass count changed")

    ordered = sorted(events, key=lambda e: str(e["id"]))
    event_by_id = {str(e["id"]): e for e in ordered}
    req(len(event_by_id) == len(ordered), "duplicate event id")
    panel_n = len(ordered)
    req(panel_n >= MIN_SUPPORT, "panel below support")

    base_rows, base_summary = support_pruned.support_pruned_cut(structural, ordered)
    req(bool(base_rows), "support-pruned parent catalogue empty")

    final: list[dict[str, Any]] = []
    replaced_parent_count = 0
    retained_parent_count = 0
    local_selected_count = 0
    local_discarded_events = 0
    refined_parent_member_count = 0
    produced_child_member_count = 0

    for parent in base_rows:
        pm = _members(parent)
        req(len(pm) == int(parent["member_count"]) >= MIN_SUPPORT, "bad parent membership")
        req(pm.issubset(event_by_id), "parent outside panel")
        local_events = [event_by_id[eid] for eid in sorted(pm)]
        local_rows, local_summary = support_pruned.support_pruned_cut(structural, local_events)

        local_sets = [_members(r) for r in local_rows]
        req(all(len(m) >= MIN_SUPPORT and m.issubset(pm) for m in local_sets), "bad local membership")
        req(all(not a.intersection(b) for i, a in enumerate(local_sets) for b in local_sets[i + 1 :]), "local candidates overlap")

        if len(local_rows) < 2:
            out = dict(parent)
            out["lrb_refined"] = False
            out["lrb_parent_family_hash"] = str(parent["family_hash"])
            out["lrb_parent_member_count"] = int(parent["member_count"])
            out["lrb_local_candidate_count"] = len(local_rows)
            out["lrb_local_discarded_event_count"] = int(local_summary.get("discarded_subsupport_event_count", 0))
            out["modal_contrast_local"] = None
            out["modal_contrast_globalized"] = float(parent["modal_contrast"])
            final.append(out)
            retained_parent_count += 1
            continue

        replaced_parent_count += 1
        refined_parent_member_count += len(pm)
        local_selected_count += len(local_rows)
        discarded = int(local_summary.get("discarded_subsupport_event_count", 0))
        local_discarded_events += discarded
        scale = len(pm) / panel_n
        req(scale > 0.0 and scale <= 1.0, "bad density-unit scale")

        child_union: set[str] = set()
        for child in local_rows:
            cm = _members(child)
            req(not child_union.intersection(cm), "replacement children overlap")
            child_union.update(cm)
            local_contrast = float(child["modal_contrast"])
            globalized = local_contrast * scale
            tup = tuple(sorted(cm))
            out = dict(child)
            out["family_id"] = support_pruned.family_id("LRB1", tup)
            out["family_hash"] = structural.member_hash(cm)
            out["event_ids"] = list(tup)
            out["member_count"] = len(tup)
            out["lrb_refined"] = True
            out["lrb_parent_family_hash"] = str(parent["family_hash"])
            out["lrb_parent_member_count"] = int(parent["member_count"])
            out["lrb_local_candidate_count"] = len(local_rows)
            out["lrb_local_discarded_event_count"] = discarded
            out["modal_contrast_local"] = local_contrast
            out["modal_contrast_globalized"] = globalized
            out["modal_contrast"] = globalized
            final.append(out)
            produced_child_member_count += len(cm)

        req(len(child_union) + discarded == len(pm), "replacement children+noise do not partition parent")

    sets = [_members(r) for r in final]
    req(all(not a.intersection(b) for i, a in enumerate(sets) for b in sets[i + 1 :]), "final LRB candidates overlap")
    req(len(sets) == len({tuple(sorted(m)) for m in sets}), "duplicate LRB membership")
    covered = sum(len(m) for m in sets)
    parent_covered = int(base_summary["covered_event_count"])
    expected_covered = parent_covered - local_discarded_events
    req(covered == expected_covered, "LRB coverage accounting mismatch")

    final.sort(key=lambda r: (-float(r["modal_contrast"]), str(r["family_hash"])))
    for rank, row in enumerate(final, 1):
        row["lrb_structural_rank"] = rank

    summary = {
        "parent_candidate_count": len(base_rows),
        "final_candidate_count": len(final),
        "replaced_parent_count": replaced_parent_count,
        "retained_parent_count": retained_parent_count,
        "local_selected_child_count": local_selected_count,
        "local_discarded_event_count": local_discarded_events,
        "parent_covered_event_count": parent_covered,
        "final_covered_event_count": covered,
        "refined_parent_member_count": refined_parent_member_count,
        "produced_child_member_count": produced_child_member_count,
        "mechanism_active": bool(replaced_parent_count > 0),
        "pairwise_disjoint": True,
        "one_pass_only": True,
        "radius": RADIUS,
        "minimum_support": MIN_SUPPORT,
        "local_density": "induced_radius_degree_over_parent_member_count",
        "contrast_unit_conversion": "local_modal_contrast_times_parent_member_count_over_panel_event_count",
        "replacement_rule": "replace_parent_iff_local_support_pruned_pass_has_at_least_two_reportable_candidates",
        "parent_cut_summary": base_summary,
    }
    return final, summary
