from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

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


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repaired_bytes = args.repaired_source.read_bytes()
    repaired_sha = sha256_bytes(repaired_bytes)

    v6 = load_module(args.repaired_source, f"orbittrace_v6_checkpoint_year_{args.year}")
    require(all(v6.v3.self_test().values()), "v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()), "v3 membership self-test failed")

    old = v6.load_base_runner(args.base_runner)
    require(list(old.YEARS) == [2022, 2023], "frozen base years changed")
    require(int(old.MAX_COMPONENTS_PER_BIN) == 128, "frozen component cap changed")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)

    print(f"V6_CHECKPOINT_YEAR_PARSE_START year={args.year}", flush=True)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    scan_sha = event_rows_sha256(scan)
    calibration_sha = event_rows_sha256(calibration)
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(
        json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    print(
        f"V6_CHECKPOINT_YEAR_SCAN_START year={args.year} scan={len(scan)} calibration={len(calibration)} "
        f"scan_sha={scan_sha[:16]} calibration_sha={calibration_sha[:16]}",
        flush=True,
    )

    audit, anchors, components = v6.scan_year_v6(
        old, args.year, scan, calibration, candidate, base, scorer, support
    )
    require(int(audit["year"]) == args.year, "year audit mismatch")
    require(int(audit["scan_events"]) == len(scan), "scan count mismatch")
    require(int(audit["calibration_events"]) == len(calibration), "calibration count mismatch")
    require(int(audit["proposal_cap_per_window"]) == 512, "proposal cap changed")
    require(int(audit["max_primary_proposals_per_year"]) == 36864, "annual proposal budget changed")

    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": scan_sha,
        "calibration_rows_sha256": calibration_sha,
        "year_sources_sha256": source_sha,
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated_in_year_job": True,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    payload_path = args.output / f"v6_year_{args.year}.pkl"
    payload_path.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / f"v6_year_{args.year}.sha256").write_text(digest + "\n")
    manifest = {
        "year": args.year,
        "checkpoint_sha256": digest,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows": len(scan),
        "calibration_rows": len(calibration),
        "anchors": len(anchors),
        "components": len(components),
        "scan_rows_sha256": scan_sha,
        "calibration_rows_sha256": calibration_sha,
        "year_sources_sha256": source_sha,
    }
    (args.output / f"v6_year_{args.year}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"V6_CHECKPOINT_YEAR_DONE year={args.year} anchors={len(anchors)} components={len(components)} "
        f"checkpoint_sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
