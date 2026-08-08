from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--split-records", type=int, default=512)
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    return p.parse_args()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def main() -> int:
    args = parse_args()
    require(args.split_records > 0, "split_records must be positive")
    raw = args.preexact_checkpoint.read_bytes()
    sidecar = args.preexact_checkpoint.with_suffix(".sha256")
    require(sidecar.exists(), "missing preexact SHA sidecar")
    require(sha256_bytes(raw) == sidecar.read_text().strip().split()[0], "preexact SHA mismatch")
    pre = pickle.loads(raw)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format mismatch")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "target firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "hidden-label firewall failed")

    eligible: list[tuple[int, float]] = []
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        if len(spec["records"]) > args.split_records:
            # Deterministically select the cheapest genuinely split real-data
            # center by the pre-truth execution proxy only. No label/score or
            # benchmark outcome is consulted.
            cost = len(spec["records"]) * len(spec["window_event_ids"])
            eligible.append((cost, center))
    require(bool(eligible), "no center requires a split at requested size")
    _cost, center = min(eligible, key=lambda item: (item[0], item[1]))
    spec = pre["centers"][center]
    records = spec["records"]

    require(sha256_bytes(args.repaired_source.read_bytes()) == pre["repaired_v6_sha256"], "repaired source mismatch")
    v6 = load_module(args.repaired_source, f"orbittrace_v6_subcenter_equivalence_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, _sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present")

    event_lookup = {str(row["id"]): row for row in scan}
    ids = [str(value) for value in spec["window_event_ids"]]
    require(canonical_sha(ids) == spec["window_event_ids_sha256"], "captured window hash changed")
    require(all(event_id in event_lookup for event_id in ids), "captured event missing")
    window_events = [event_lookup[event_id] for event_id in ids]
    require([str(row["id"]) for row in old.window_events_for_center(scan, center, base)] == ids, "window reconstruction changed")

    # Baseline: immutable scalar scientific function on the complete center.
    full = v6.exact_rescore_window_v6(old, records, window_events, event_lookup, support, base)
    require(
        [str(row["proposal_anchor_id"]) for row in full]
        == [str(row["proposal_anchor_id"]) for row in records],
        "full exact output order changed",
    )

    # Challenger executor semantics: the same immutable scalar scientific body
    # on contiguous proposal slices, followed only by order-preserving concat.
    pieces: list[list[dict[str, Any]]] = []
    for start in range(0, len(records), args.split_records):
        stop = min(len(records), start + args.split_records)
        chunk = records[start:stop]
        out = v6.exact_rescore_window_v6(old, chunk, window_events, event_lookup, support, base)
        require(
            [str(row["proposal_anchor_id"]) for row in out]
            == [str(row["proposal_anchor_id"]) for row in chunk],
            f"chunk output order changed {start}:{stop}",
        )
        pieces.append(out)
    merged = [row for piece in pieces for row in piece]
    require(len(pieces) >= 2, "equivalence audit failed to exercise multiple units")
    require(merged == full, "sub-center splitting changed exact scientific outputs")
    require(canonical_sha(merged) == canonical_sha(full), "sub-center canonical output hash changed")

    print(
        "PASS_V6_SUBCENTER_REAL_EXACT_EQUIVALENCE "
        f"year={args.year} center={center:.1f} proposals={len(records)} "
        f"window_events={len(ids)} units={len(pieces)} sha={canonical_sha(full)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
