from __future__ import annotations

from collections import defaultdict
from typing import Any


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def finalize_postexact(
    *,
    v6: Any,
    old: Any,
    year: int,
    exact_records_all: list[dict[str, Any]],
    event_lookup: dict[str, dict[str, Any]],
    base: Any,
    proposal_cal: dict[int, Any],
    v3_cal: dict[int, Any],
    fixed4_cal: dict[int, Any],
    preexact_audit: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute the frozen scan_year_v6 tail after exact rescoring.

    The body below is intentionally a direct structural copy of the exact
    frozen source's post-rescore logic, with only names qualified through the
    loaded v6 module where needed. The repaired source's exact
    component_records_track_v6 implementation remains authoritative.
    """
    require(sorted(proposal_cal) == sorted(v3_cal) == sorted(fixed4_cal), "calibration bin universes differ")
    require(sorted(v3_cal) == list(preexact_audit["supported_bins"]), "saved supported-bin universe differs")
    require(int(preexact_audit["deduplicated_exact_proposals"]) == len(exact_records_all), "exact proposal cardinality changed")

    primary_by_anchor: dict[str, dict[str, Any]] = {}
    rescue_by_anchor: dict[str, dict[str, Any]] = {}
    exact_rejections = 0
    for exact in exact_records_all:
        bin_index = int(exact["bin"])
        exact["proposal_p_brown"] = old.empirical_upper_pvalue(exact["proposal_brown_score"], proposal_cal[bin_index])
        exact["p_v3"] = old.empirical_upper_pvalue(exact["v3_score"], v3_cal[bin_index])
        exact["p_fixed4"] = old.empirical_upper_pvalue(exact["fixed4_score"], fixed4_cal[bin_index])
        exact["v3_detected"] = bool(exact["p_v3"] <= v6.BASE_ALPHA)
        exact["rescue_detected"] = bool(exact["p_fixed4"] <= v6.RESCUE_ALPHA + 1e-15)
        if not (exact["v3_detected"] or exact["rescue_detected"]):
            exact_rejections += 1
            continue
        if exact["v3_detected"] and len(exact["v3_member_ids"]) >= old.MIN_COMPONENT_EVENTS:
            primary = dict(exact)
            primary["channel"] = "v3"
            primary["anchor_id"] = str(exact["v3_anchor_id"])
            primary["member_ids"] = list(exact["v3_member_ids"])
            anchor_id = str(primary["anchor_id"])
            prior = primary_by_anchor.get(anchor_id)
            key = (float(primary["p_v3"]), -float(primary["v3_score"]), float(primary["p_fixed4"]), str(primary["proposal_anchor_id"]))
            if prior is None or key < (
                float(prior["p_v3"]), -float(prior["v3_score"]), float(prior["p_fixed4"]), str(prior["proposal_anchor_id"])
            ):
                primary_by_anchor[anchor_id] = primary
        if exact["rescue_detected"] and len(exact["proposal_member_ids"]) >= old.MIN_COMPONENT_EVENTS:
            rescue = dict(exact)
            rescue["channel"] = "fixed4_rescue"
            rescue["anchor_id"] = str(exact["proposal_anchor_id"])
            rescue["member_ids"] = list(exact["proposal_member_ids"])
            anchor_id = str(rescue["anchor_id"])
            prior = rescue_by_anchor.get(anchor_id)
            key = (float(rescue["p_fixed4"]), float(rescue["p_v3"]), -float(rescue["fixed4_score"]), anchor_id)
            if prior is None or key < (
                float(prior["p_fixed4"]), float(prior["p_v3"]), -float(prior["fixed4_score"]), anchor_id
            ):
                rescue_by_anchor[anchor_id] = rescue

    def cap_anchor_track(records: list[dict[str, Any]], channel: str) -> list[dict[str, Any]]:
        by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_bin[int(record["bin"])].append(record)
        capped_track: list[dict[str, Any]] = []
        for bin_index, rows in sorted(by_bin.items()):
            if channel == "v3":
                rows.sort(key=lambda row: (
                    float(row["p_v3"]), -float(row["v3_score"]), float(row["p_fixed4"]), str(row["anchor_id"])
                ))
            else:
                rows.sort(key=lambda row: (
                    float(row["p_fixed4"]), float(row["p_v3"]), -float(row["fixed4_score"]), str(row["anchor_id"])
                ))
            capped_track.extend(rows[: old.MAX_COMPONENTS_PER_BIN * 8])
        return capped_track

    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    # These are the exact two calls inserted by the already-source-audited
    # two-line scientific implementation repair before any v6 result existed.
    primary_components = v6.component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = v6.component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components

    audit = dict(preexact_audit)
    audit.update({
        "exact_rejections": exact_rejections,
        "retained_v3_anchors": len(primary_capped),
        "retained_rescue_anchors": len(rescue_capped),
        "retained_detected_anchors": len(capped),
        "v3_components": len(primary_components),
        "rescue_components": len(rescue_components),
        "components": len(components),
    })
    expected_keys = {
        "year", "scan_events", "calibration_events", "supported_bins", "calibration",
        "window_count", "unsupported_windows", "prefilter_candidates", "proposal_candidates_scored",
        "primary_proposals_selected_before_dedup", "rescue_proposals_selected_before_dedup",
        "proposal_cap_per_window", "max_primary_proposals_per_year", "deduplicated_exact_proposals",
        "exact_rejections", "retained_v3_anchors", "retained_rescue_anchors",
        "retained_detected_anchors", "v3_components", "rescue_components", "components",
    }
    require(set(audit) == expected_keys, f"reconstructed audit schema changed: {sorted(set(audit) ^ expected_keys)}")
    return audit, capped, components
