from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import (
    FROZEN_V6_SHA256,
    event_rows_sha256,
    load_module,
    require,
    sha256_bytes,
)

YEARS = (2022, 2023)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=YEARS)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def calibration_sha(proposal_cal: Any, v3_cal: Any, fixed4_cal: Any, calibration_summary: Any) -> str:
    def normalize(value: Any) -> Any:
        if hasattr(value, "tolist"):
            return normalize(value.tolist())
        if isinstance(value, dict):
            return {str(key): normalize(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
        if isinstance(value, (list, tuple)):
            return [normalize(item) for item in value]
        if hasattr(value, "item"):
            try:
                return normalize(value.item())
            except (ValueError, TypeError):
                pass
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        raise TypeError(f"unsupported calibration hash type: {type(value)!r}")

    return canonical_sha(normalize({
        "proposal_cal": proposal_cal,
        "v3_cal": v3_cal,
        "fixed4_cal": fixed4_cal,
        "calibration_summary": calibration_summary,
    }))


def main() -> int:
    import pickle

    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repaired_sha = sha256_bytes(args.repaired_source.read_bytes())
    v6 = load_module(args.repaired_source, f"orbittrace_v6_replay_v4_capture_{args.year}")
    require(all(v6.v3.self_test().values()), "v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()), "v3 membership self-test failed")

    old = v6.load_base_runner(args.base_runner)
    require(list(old.YEARS) == [2022, 2023], "frozen base years changed")
    require(int(old.MAX_COMPONENTS_PER_BIN) == 128, "frozen component cap changed")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present in scan")
    scan_sha = event_rows_sha256(scan)
    calibration_sha_rows = event_rows_sha256(calibration)
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    centers: dict[float, dict[str, Any]] = {}
    calibration_state: dict[str, Any] = {}
    original_exact = v6.exact_rescore_window_v6
    original_calibrate = v6.calibrate_year_v6

    # Exact frozen signature is calibrate_year_v6(old, year, calibration_events,
    # candidate, base, scorer). This wrapper captures the returned arrays without
    # changing a single calibration operation or RNG seed.
    def capture_calibration(old_arg, year_arg, events_arg, candidate_arg, base_arg, scorer_arg):
        result = original_calibrate(old_arg, year_arg, events_arg, candidate_arg, base_arg, scorer_arg)
        require(isinstance(result, tuple) and len(result) == 4, "calibrate_year_v6 return contract changed")
        proposal_cal, v3_cal, fixed4_cal, calibration_summary = result
        calibration_state["proposal_cal"] = proposal_cal
        calibration_state["v3_cal"] = v3_cal
        calibration_state["fixed4_cal"] = fixed4_cal
        calibration_state["calibration_summary"] = calibration_summary
        calibration_state["sha256"] = calibration_sha(proposal_cal, v3_cal, fixed4_cal, calibration_summary)
        return result

    def capture_exact(old_arg, records, window_events, event_lookup, support_arg, base_arg):
        del old_arg, support_arg, base_arg
        require(bool(records), "unexpected empty exact-rescore call")
        center = float(records[0]["window_center"])
        require(all(float(row["window_center"]) == center for row in records), "mixed centers in exact-rescore call")
        require(center not in centers, f"duplicate exact center {center}")
        ids = [str(row["id"]) for row in window_events]
        require(all(event_lookup[event_id] is window_events[index] for index, event_id in enumerate(ids)), "event lookup/window identity mismatch")
        record_copy = [dict(row) for row in records]
        centers[center] = {
            "records": record_copy,
            "records_sha256": canonical_sha(record_copy),
            "window_event_ids": ids,
            "window_event_ids_sha256": canonical_sha(ids),
        }
        print(f"V6_REPLAY_V4_CAPTURE center={center:.1f} records={len(records):,} events={len(ids):,}", flush=True)
        return []

    v6.calibrate_year_v6 = capture_calibration
    v6.exact_rescore_window_v6 = capture_exact
    try:
        audit, anchors, components = v6.scan_year_v6(old, args.year, scan, calibration, candidate, base, scorer, support)
    finally:
        v6.exact_rescore_window_v6 = original_exact
        v6.calibrate_year_v6 = original_calibrate

    require(bool(calibration_state), "calibration state was not captured")
    require(bool(centers), "no exact centers captured")
    require(anchors == [] and components == [], "capture run unexpectedly produced scientific anchors/components")
    ordered_centers = sorted(centers)
    total_records = sum(len(centers[center]["records"]) for center in ordered_centers)
    require(total_records > 0, "no exact proposals captured")

    # These exact audit fields are all computed before exact outputs are consumed.
    # exact_rejections/retained anchors/components are intentionally reconstructed
    # later from the real exact outputs.
    valid_audit_keys = (
        "year", "scan_events", "calibration_events", "supported_bins", "calibration",
        "window_count", "unsupported_windows", "prefilter_candidates",
        "proposal_candidates_scored", "primary_proposals_selected_before_dedup",
        "rescue_proposals_selected_before_dedup", "proposal_cap_per_window",
        "max_primary_proposals_per_year", "deduplicated_exact_proposals",
    )
    preexact_audit = {key: audit[key] for key in valid_audit_keys}
    require(preexact_audit["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(preexact_audit["max_primary_proposals_per_year"] == 36864, "annual primary proposal budget changed")
    require(len(preexact_audit["supported_bins"]) >= 30, "supported calibration bins changed")
    require(preexact_audit["deduplicated_exact_proposals"] == total_records, "captured exact-proposal count differs from frozen audit")
    require(preexact_audit["calibration"] == calibration_state["calibration_summary"], "captured calibration summary differs from audit")

    checkpoint = {
        "format": "orbittrace-v6-preexact-replay-v4",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": scan_sha,
        "calibration_rows_sha256": calibration_sha_rows,
        "year_sources_sha256": source_sha,
        "ordered_centers": ordered_centers,
        "centers": centers,
        "total_records": total_records,
        "calibration_state": calibration_state,
        "preexact_audit": preexact_audit,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated": True,
            "exact_rescore_not_executed_in_capture": True,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_preexact_v4_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    (args.output / f"v6_preexact_v4_{args.year}.json").write_text(json.dumps({
        "year": args.year,
        "checkpoint_sha256": digest,
        "centers": len(ordered_centers),
        "total_records": total_records,
        "calibration_state_sha256": calibration_state["sha256"],
        "scan_rows_sha256": scan_sha,
        "calibration_rows_sha256": calibration_sha_rows,
    }, indent=2, sort_keys=True) + "\n")
    print(f"PASS_V6_REPLAY_V4_PREEXACT_CAPTURE year={args.year} centers={len(ordered_centers)} records={total_records:,} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
