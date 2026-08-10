#!/usr/bin/env python3
"""Generate a complete v16 pretruth freeze on one target-excluded GMN pair."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import run_holdout_loader_corrected as v5_loader

from orbittrace_v16_label_free_multiscale_v1 import gmn_geometry, multiscale

v5 = v5_loader.core


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year-a", type=int, required=True)
    p.add_argument("--year-b", type=int, required=True)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    years = (int(a.year_a), int(a.year_b))
    require(years in ((2020, 2021), (2022, 2023)), f"unexpected development pair {years}")
    a.output.mkdir(parents=True, exist_ok=True)

    require(int(v5.EPISODE_SIZE) == 128, "frozen v5 episode identity changed")
    require(all(v5.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(v5.brown.self_test().values()), "Brown self-test failed")
    runtime = v5.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")

    class Args:
        candidate_payload = a.candidate_payload
        baseline_payload = a.baseline_payload
        scorer_parts = a.scorer_parts
        output = a.output

    _candidate, base, _scorer = support.load_sources(Args())

    # FIRST DATA ACCESS for this panel. Geometry-only parser does not resolve a truth column.
    scan_by_year, sources = gmn_geometry.parse_pair(years=years, base=base)
    scan_id_sha256 = {
        str(year): canonical_sha(sorted(str(row["id"]) for row in scan_by_year[year]))
        for year in years
    }
    scan_count = {str(year): len(scan_by_year[year]) for year in years}

    result = multiscale.run_pretruth(
        years=years,
        scan_by_year=scan_by_year,
        support=support,
        runtime=runtime,
        base=base,
        score_episode=v5.score_episode,
    )
    require(result["labels_read"] is False, "pretruth runtime reported label access")
    require(result["calibration_events_used"] == 0, "pretruth runtime used calibration events")
    result["evidence_class"] = "target_excluded_development_pretruth"
    result["gmn_sources"] = sources
    result["scan_id_sha256"] = scan_id_sha256
    result["scan_count"] = scan_count
    result["truth_column_resolved"] = False
    result["sonotaco_access"] = False
    result["maarsy_access"] = False
    result["target_information_access"] = False

    out = a.output / f"pretruth_{years[0]}_{years[1]}.json"
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    out.write_text(payload)
    (a.output / f"pretruth_{years[0]}_{years[1]}.sha256").write_text(hashlib.sha256(payload.encode()).hexdigest() + "\n")
    print(json.dumps({
        "verdict": "PASS_V16_PRETRUTH_FREEZE",
        "years": list(years),
        "family_count": result["family_count"],
        "family_universe_sha256": result["family_universe_sha256"],
        "final_order_sha256": result["final_order_sha256"],
        "labels_read": False,
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
