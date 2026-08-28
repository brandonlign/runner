#!/usr/bin/env python3
"""One deterministic cell of the frozen drift-track positive-control benchmark.

This is a compute-partitioning wrapper only. It calls the exact generator,
track fit, orbit gates, and control evaluator in ``drift_track_controls`` for
one frozen calibration month and one frozen detector variant. Scientific
selection is still performed only after all 12 cells exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as bench


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", type=int, choices=[7, 9, 10], required=True)
    parser.add_argument("--variant", choices=sorted(bench.VARIANTS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    month = int(args.month)
    variant = str(args.variant)
    prepared = bench.prepare_all_quality(base.load_month(2025, month), 2025, month)
    tracks, diagnostics = bench.tracks_for_variant(prepared, variant)
    controls_here = {
        name: control
        for name, control in bench.CONTROLS.items()
        if int(control["month"]) == month
    }
    evaluations = {
        name: bench.evaluate_control(name, control, tracks, prepared)
        for name, control in controls_here.items()
    }
    output = {
        "stage": "drift_track_control_cell_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_CONTROL_BENCHMARK.md",
        "month": month,
        "variant": variant,
        "variant_config": bench.VARIANTS[variant],
        "quality_rows": int(len(prepared["data"])),
        "diagnostics": diagnostics,
        "controls": evaluations,
        "tracks": [bench.compact_track(track) for track in tracks],
    }
    path = args.out / f"control_{month:02d}_{variant}.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(
        f"month={month} variant={variant} nodes={diagnostics['local_nodes']} "
        f"tracks={diagnostics['retained_tracks']} "
        + " ".join(f"{name}={value['recovered']}" for name, value in evaluations.items()),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
