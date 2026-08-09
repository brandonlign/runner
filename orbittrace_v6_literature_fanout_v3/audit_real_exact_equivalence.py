from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter.parallel_exact_rescore import install
from orbittrace_v6_literature_fanout_v3.panel_common import canonical_sha, materialize, require


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", required=True, choices=("hdbscan", "sugar"))
    p.add_argument("--year", required=True, type=int, choices=(2023, 2025))
    p.add_argument("--split-records", required=True, type=int)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--preexact", required=True, type=Path)
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--id-manifest", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--archive", required=True, type=Path)
    return p.parse_args()


def load_pre(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), "missing preexact SHA sidecar")
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == sidecar.read_text().strip(), "preexact SHA mismatch")
    return pickle.loads(raw), digest


def main() -> int:
    args = parse_args()
    require(args.split_records > 0, "split-records must be positive")
    require(1 <= args.workers <= 4, "workers outside frozen audit range")
    pre, pre_sha = load_pre(args.preexact)
    require(pre["format"] == "orbittrace-v6-matched-literature-preexact-v3", "wrong preexact format")
    require(pre["panel"] == args.panel and int(pre["year"]) == args.year, "preexact panel/year mismatch")
    require(pre["firewall"]["truth_accessed"] is False, "truth entered preexact checkpoint")
    require(pre["firewall"]["competitor_cluster_labels_accessed"] is False, "competitor labels entered preexact checkpoint")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "target interval entered preexact checkpoint")

    ctx = materialize(args, f"real_equiv_{args.panel}_{args.year}")
    require(ctx["manifest_sha"] == pre["id_manifest_sha256"], "manifest identity changed")
    require(canonical_sha(ctx["scan_events"]) == pre["scan_rows_sha256"], "scan rows changed")
    require(canonical_sha(ctx["calibration"]) == pre["calibration_rows_sha256"], "calibration rows changed")

    eligible = []
    for raw_center in pre["ordered_centers"]:
        center = float(raw_center)
        spec = pre["centers"][center]
        n_records = len(spec["records"])
        n_events = len(spec["window_event_ids"])
        if n_records > args.split_records:
            eligible.append((n_records * n_events, n_records, n_events, center))
    require(bool(eligible), "no real center genuinely splits at frozen audit chunk size")
    _cost, n_records, n_events, center = min(eligible)
    spec = pre["centers"][center]
    records = spec["records"]
    require(canonical_sha(records) == spec["records_sha256"], "captured records hash changed")
    ids = [str(value) for value in spec["window_event_ids"]]
    require(canonical_sha(ids) == spec["window_event_ids_sha256"], "captured window IDs changed")
    lookup = {str(event["id"]): event for event in ctx["scan_events"]}
    require(all(event_id in lookup for event_id in ids), "captured event missing from exact-row universe")
    window = [lookup[event_id] for event_id in ids]
    canonical_window = ctx["old"].window_events_for_center(ctx["scan_events"], center, ctx["base"])
    require([str(event["id"]) for event in canonical_window] == ids, "real window reconstruction changed")

    v6 = ctx["v6"]
    scalar = v6.exact_rescore_window_v6
    full = scalar(ctx["old"], records, window, lookup, ctx["support"], ctx["base"])
    require([str(row["proposal_anchor_id"]) for row in full] == [str(row["proposal_anchor_id"]) for row in records], "full exact order changed")

    execution = install(v6, workers=args.workers, min_parallel_records=256)
    split = []
    unit_count = 0
    for start in range(0, len(records), args.split_records):
        stop = min(len(records), start + args.split_records)
        piece = records[start:stop]
        exact = v6.exact_rescore_window_v6(ctx["old"], piece, window, lookup, ctx["support"], ctx["base"])
        require([str(row["proposal_anchor_id"]) for row in exact] == [str(row["proposal_anchor_id"]) for row in piece], f"split exact order changed {start}:{stop}")
        split.extend(exact)
        unit_count += 1

    require(unit_count >= 2, "audit center did not actually split")
    require(split == full, "full-center and record-slice exact outputs differ")
    full_bytes = json.dumps(full, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    split_bytes = json.dumps(split, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(full_bytes == split_bytes, "canonical full/split output bytes differ")
    digest = hashlib.sha256(full_bytes).hexdigest()

    print("PASS_V6_LITERATURE_REAL_EXACT_EQUIVALENCE")
    print(json.dumps({
        "panel": args.panel,
        "year": args.year,
        "preexact_sha256": pre_sha,
        "center": center,
        "proposal_records": n_records,
        "window_events": n_events,
        "split_records": args.split_records,
        "units": unit_count,
        "workers": args.workers,
        "parallel_execution": execution,
        "canonical_output_sha256": digest,
        "truth_accessed": False,
        "competitor_cluster_labels_accessed": False,
        "target_interval_remains_excluded": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
