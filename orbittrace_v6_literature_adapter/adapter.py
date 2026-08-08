from __future__ import annotations

import hashlib
import json
from typing import Any

YEARS = (2023, 2025)
CORPUS = "sonotaco-v6-exact-row-literature"
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
FROZEN_V6_SHA256 = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def configure_transfer_modules(v6: Any, old: Any, support: Any) -> None:
    """Transport-only year/corpus binding; no scientific constant may change."""
    require(int(old.MAX_COMPONENTS_PER_BIN) == 128, "MAX_COMPONENTS_PER_BIN changed")
    require(int(old.CALIBRATION_PER_BIN) == 128, "CALIBRATION_PER_BIN changed")
    require(float(old.WINDOW_WIDTH_DEG) == 10.0, "WINDOW_WIDTH_DEG changed")
    require(float(old.WINDOW_STEP_DEG) == 5.0, "WINDOW_STEP_DEG changed")
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH,
            "blind interval changed")

    # The frozen detector functions accept year/corpus as transport context.
    # These bindings are fixed before any SonotaCo benchmark row is opened.
    v6.YEARS = YEARS
    old.YEARS = list(YEARS)
    support.YEARS = list(YEARS)
    old.CORPUS = CORPUS
    support.CORPUS = CORPUS


def calibration_events_from_native_sporadic(
    scan_by_year: dict[int, list[dict[str, Any]]],
    native_sporadic_ids_by_year: dict[int, set[str]],
) -> dict[int, list[dict[str, Any]]]:
    """
    Preserve the frozen v6 null-reservoir rule.

    All exact competitor rows remain in the scan.  Only rows that the frozen
    native parser classified as actual background/SPORADIC enter calibration.
    Unsupported/unmapped non-background shower tokens are *not* silently
    converted into calibration background.
    """
    out: dict[int, list[dict[str, Any]]] = {}
    for year in YEARS:
        events = scan_by_year[year]
        event_ids = [str(event["id"]) for event in events]
        require(len(event_ids) == len(set(event_ids)), f"duplicate scan event IDs {year}")
        allowed = set(event_ids)
        sporadic = set(native_sporadic_ids_by_year[year])
        require(sporadic <= allowed, f"calibration IDs outside exact-row universe {year}")
        out[year] = [dict(event, complex_key="SPORADIC") for event in events if str(event["id"]) in sporadic]
        require(len(out[year]) >= 1000, f"insufficient exact-row sporadic calibration reservoir {year}")
    return out


def run_v6_panel(
    panel: str,
    scan_by_year: dict[int, list[dict[str, Any]]],
    calibration_by_year: dict[int, list[dict[str, Any]]],
    v6: Any,
    old: Any,
    candidate: Any,
    base: Any,
    scorer: Any,
    support: Any,
) -> dict[str, Any]:
    """Run the unchanged v6 scientific functions on one exact-row panel."""
    require(panel in {"hdbscan", "sugar"}, f"unexpected panel {panel}")
    configure_transfer_modules(v6, old, support)

    audits: list[dict[str, Any]] = []
    all_anchors: list[dict[str, Any]] = []
    all_components: list[dict[str, Any]] = []

    for year in YEARS:
        scan_ids = {str(event["id"]) for event in scan_by_year[year]}
        cal_ids = {str(event["id"]) for event in calibration_by_year[year]}
        require(cal_ids <= scan_ids, f"calibration is not a scan subset {panel} {year}")
        require(all(not (BLIND_LOW <= float(event["sol"]) <= BLIND_HIGH) for event in scan_by_year[year]),
                f"target interval entered scan {panel} {year}")

        audit, anchors, components = v6.scan_year_v6(
            old,
            year,
            scan_by_year[year],
            calibration_by_year[year],
            candidate,
            base,
            scorer,
            support,
        )
        require(len(audit["supported_bins"]) >= 30, f"insufficient calibration bins {panel} {year}")
        require(audit["proposal_cap_per_window"] == 512, f"proposal cap changed {panel} {year}")
        require(audit["max_primary_proposals_per_year"] == 36864,
                f"annual proposal budget changed {panel} {year}")
        audits.append(audit)
        all_anchors.extend(anchors)
        all_components.extend(components)

    primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
    rescue_families = v6.build_family_track_v6(old, all_components, base, "fixed4_rescue")

    # The rescue channel is deliberately returned separately.  It is never
    # concatenated into or used to rerank the primary literature output.
    primary_payload = {
        "panel": panel,
        "years": list(YEARS),
        "corpus": CORPUS,
        "primary_method": "v3",
        "primary_families": primary_families,
        "scan_audits": audits,
    }
    canonical = json.dumps(primary_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    primary_sha256 = hashlib.sha256(canonical).hexdigest()

    return {
        "panel": panel,
        "primary_families": primary_families,
        "rescue_families": rescue_families,
        "scan_audits": audits,
        "anchor_count": len(all_anchors),
        "component_count": len(all_components),
        "primary_ranking_sha256_before_truth": primary_sha256,
        "primary_payload_bytes": len(canonical),
    }


def native_sporadic_ids_from_parser_outputs(
    year: int,
    scan_ids: set[str],
    labeled: list[dict[str, Any]],
    sporadic: list[dict[str, Any]],
    parser_gates: dict[str, bool],
) -> set[str]:
    """
    Collapse pre-ranking label access to a binary calibration-reservoir set.

    `labeled` is accepted only so the wrapper can assert ID disjointness; no
    shower identity or complex_key is retained or returned from this function.
    Full mapped truth must be parsed/evaluated only after the primary ranking
    hash returned by `run_v6_panel` has been frozen.
    """
    require(year in YEARS, f"unexpected year {year}")
    require(parser_gates and all(bool(v) for v in parser_gates.values()), f"parser gates failed {year}")
    labeled_ids = {str(event["id"]) for event in labeled}
    sporadic_ids = {str(event["id"]) for event in sporadic}
    require(not (labeled_ids & sporadic_ids), f"labeled/sporadic overlap {year}")
    return sporadic_ids & set(scan_ids)
