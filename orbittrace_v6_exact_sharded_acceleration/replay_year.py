from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import (
    FROZEN_V6_SHA256,
    event_rows_sha256,
    load_module,
    require,
    sha256_bytes,
)
from orbittrace_v6_exact_sharded_acceleration.common import (
    REPAIRED_V6_SHA256,
    SHARD_COUNT,
    proposal_anchor_ids,
    call_fingerprint,
    load_sidecar_pickle,
    locate_proposal_owner,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--catalogue-cache", required=True, type=Path)
    p.add_argument("--prepare", required=True, type=Path)
    p.add_argument("--exact-dir", required=True, type=Path)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_bytes(args.repaired_source.read_bytes()) == REPAIRED_V6_SHA256, "repaired source hash changed")
    cache, cache_sha = load_sidecar_pickle(args.catalogue_cache)
    prep, prep_sha = load_sidecar_pickle(args.prepare)
    require(prep["catalogue_cache_sha256"] == cache_sha, "prepare cache binding changed")
    require(prep["year"] == args.year, "prepare year mismatch")
    require(event_rows_sha256(cache["scan_by_year"][args.year]) == prep["scan_rows_sha256"], "scan cache mismatch")
    require(event_rows_sha256(cache["calibration_by_year"][args.year]) == prep["calibration_rows_sha256"], "calibration cache mismatch")

    exact_by_center: dict[str, list[dict[str, Any]]] = {}
    shard_digests: dict[str, str] = {}
    observed_centers: list[str] = []
    for shard in range(SHARD_COUNT):
        path = args.exact_dir / f"exact_year_{args.year}_shard_{shard}.pkl"
        payload, digest = load_sidecar_pickle(path)
        require(payload["format"] == "orbittrace-v6-exact-shard-result-v1", "exact shard format changed")
        require(payload["year"] == args.year and payload["shard"] == shard, "exact shard identity mismatch")
        require(payload["shard_count"] == SHARD_COUNT, "shard count changed")
        require(payload["prepare_sha256"] == prep_sha, "exact shard prepare binding changed")
        require(payload["catalogue_cache_sha256"] == cache_sha, "exact shard cache binding changed")
        require(payload["repaired_v6_sha256"] == REPAIRED_V6_SHA256, "exact shard source changed")
        require(payload["firewall"]["original_exact_rescore_function_used_unchanged"] is True, "exact shard firewall failed")
        for key in payload["centers"]:
            require(key not in exact_by_center, f"duplicate exact center {key}")
            rows = payload["exact_by_center"][key]
            require(proposal_anchor_ids(rows) == proposal_anchor_ids(prep["records_by_center"][key]), f"exact row order mismatch {key}")
            exact_by_center[key] = rows
            observed_centers.append(key)
        shard_digests[str(shard)] = digest
    expected_centers = sorted(prep["records_by_center"], key=float)
    require(sorted(observed_centers, key=float) == expected_centers, "exact shard coverage mismatch")

    events = cache["scan_by_year"][args.year]
    calibration = cache["calibration_by_year"][args.year]
    v6 = load_module(args.repaired_source, f"orbittrace_v6_accel_replay_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)

    original_calibrate = v6.calibrate_year_v6
    proposal_owner_name, proposal_owner = locate_proposal_owner(v6, old, support)
    original_proposal = getattr(proposal_owner, "proposal_window_v6") if proposal_owner is not None else None
    original_exact = v6.exact_rescore_window_v6
    replay_centers: list[str] = []
    proposal_replay_index = 0
    captured_proposal_count = int(prep.get("proposal_call_count", 0))
    if captured_proposal_count > 0:
        require(proposal_owner is not None, "captured proposal outputs but proposal owner is unavailable")
        require(prep.get("proposal_owner") == proposal_owner_name, "proposal owner changed between prepare and replay")
    else:
        require(len(prep.get("proposal_calls", [])) == 0, "proposal replay metadata inconsistent")

    def replay_calibration(
        old_arg: Any,
        year_arg: int,
        calibration_events_arg: list[dict[str, Any]],
        candidate_arg: Any,
        base_arg: Any,
        scorer_arg: Any,
    ):
        del old_arg, candidate_arg, base_arg, scorer_arg
        require(year_arg == args.year, "replay calibration year changed")
        require(event_rows_sha256(calibration_events_arg) == prep["calibration_rows_sha256"], "replay calibration rows changed")
        return (
            {int(k): v.copy() for k, v in prep["proposal_cal"].items()},
            {int(k): v.copy() for k, v in prep["v3_cal"].items()},
            {int(k): v.copy() for k, v in prep["fixed4_cal"].items()},
            [dict(row) for row in prep["calibration_summary"]],
        )

    def replay_proposal(*call_args: Any, **call_kwargs: Any) -> Any:
        nonlocal proposal_replay_index
        require(original_proposal is not None, "proposal replay invoked without original function")
        require(proposal_replay_index < len(prep["proposal_calls"]), "too many proposal replay calls")
        expected = prep["proposal_calls"][proposal_replay_index]
        actual_fingerprint = call_fingerprint(original_proposal, call_args, call_kwargs)
        require(actual_fingerprint == expected["fingerprint"], f"proposal call changed index={proposal_replay_index}")
        proposal_replay_index += 1
        return pickle.loads(pickle.dumps(expected["result"], protocol=pickle.HIGHEST_PROTOCOL))

    def replay_exact(
        old_arg: Any,
        records: list[dict[str, Any]],
        window_events: list[dict[str, Any]],
        event_lookup: dict[str, dict[str, Any]],
        support_arg: Any,
        base_arg: Any,
    ) -> list[dict[str, Any]]:
        del old_arg, event_lookup, support_arg
        require(records, "unexpected empty exact replay records")
        key = f"{float(records[0]['window_center']):.1f}"
        require(all(f"{float(row['window_center']):.1f}" == key for row in records), f"mixed replay centers {key}")
        require(key in exact_by_center, f"unexpected replay center {key}")
        require(proposal_anchor_ids(records) == proposal_anchor_ids(prep["records_by_center"][key]), f"proposal inputs changed center={key}")
        expected_window = old.window_events_for_center(events, float(key), base_arg)
        require([str(row["id"]) for row in window_events] == [str(row["id"]) for row in expected_window], f"window events changed center={key}")
        replay_centers.append(key)
        return [dict(row) for row in exact_by_center[key]]

    v6.calibrate_year_v6 = replay_calibration
    if captured_proposal_count > 0:
        setattr(proposal_owner, "proposal_window_v6", replay_proposal)
    v6.exact_rescore_window_v6 = replay_exact
    try:
        audit, anchors, components = v6.scan_year_v6(old, args.year, events, calibration, candidate, base, scorer, support)
    finally:
        v6.calibrate_year_v6 = original_calibrate
        if captured_proposal_count > 0:
            setattr(proposal_owner, "proposal_window_v6", original_proposal)
        v6.exact_rescore_window_v6 = original_exact
    require(proposal_replay_index == captured_proposal_count, "not all captured proposal calls replayed")
    require(replay_centers == expected_centers, "replay center order changed")
    require(int(audit["year"]) == args.year, "audit year changed")
    require(int(audit["proposal_cap_per_window"]) == 512, "proposal cap changed")
    require(int(audit["max_primary_proposals_per_year"]) == 36864, "annual proposal budget changed")

    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": REPAIRED_V6_SHA256,
        "scan_rows_sha256": prep["scan_rows_sha256"],
        "calibration_rows_sha256": prep["calibration_rows_sha256"],
        "year_sources_sha256": cache["year_sources_sha256"][str(args.year)],
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated_in_year_job": True,
        },
        "acceleration": {
            "method": "exact-center-shards-plus-original-scan-replay",
            "shard_count": SHARD_COUNT,
            "prepare_sha256": prep_sha,
            "exact_shard_sha256": shard_digests,
            "original_exact_scalar_function_used_in_shards": True,
            "original_repaired_scan_year_used_for_post_exact_logic": True,
            "calibration_replayed_from_exact_prefix_capture": True,
            "proposal_owner": proposal_owner_name,
            "proposal_windows_replayed_from_original_prepare_outputs": captured_proposal_count > 0,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_year_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / f"v6_year_{args.year}.sha256").write_text(digest + "\n")
    manifest = {
        "year": args.year,
        "checkpoint_sha256": digest,
        "anchors": len(anchors),
        "components": len(components),
        "audit": audit,
        "acceleration": checkpoint["acceleration"],
    }
    (args.output / f"v6_year_{args.year}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"V6_ACCEL_YEAR_REPLAY_DONE year={args.year} anchors={len(anchors)} components={len(components)} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
