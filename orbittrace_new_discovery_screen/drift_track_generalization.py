#!/usr/bin/env python3
"""Compute-only mirror of the frozen out-of-benchmark drift-track audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as drift

CONTROLS: dict[str, dict[str, Any]] = {
    "M2025-K1": {
        "month": 5,
        "activity": [61.0, 63.5],
        "ref_sol": 62.3,
        "slon": 229.94,
        "beta": -62.86,
        "vg": 40.6,
    },
    "M2025-O1": {
        "month": 6,
        "activity": [85.0, 99.0],
        "ref_sol": 92.2,
        "slon": 232.75,
        "beta": 23.72,
        "vg": 56.9,
    },
    "M2025-Q1": {
        "month": 8,
        "activity": [145.0, 155.0],
        "ref_sol": 153.5,
        "slon": 254.8,
        "beta": -6.0,
        "vg": 68.3,
    },
    "M2025-V1": {
        "month": 11,
        "activity": [215.0, 222.0],
        "ref_sol": 220.1,
        "slon": 239.7,
        "beta": -16.2,
        "vg": 62.3,
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(drift.VARIANTS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {}
    recovered = 0
    for name, control in CONTROLS.items():
        month = int(control["month"])
        print(f"Loading 2025-{month:02d} generalization control {name}", flush=True)
        prepared = drift.prepare_all_quality(base.load_month(2025, month), 2025, month)
        tracks, diagnostics = drift.tracks_for_variant(prepared, args.variant)
        evaluation = drift.evaluate_control(name, control, tracks, prepared)
        recovered += int(evaluation["recovered"])
        results[name] = {
            "control": control,
            "quality_rows": int(len(prepared["data"])),
            "diagnostics": diagnostics,
            "evaluation": evaluation,
        }
        print(
            f"  tracks={len(tracks)} recovered={evaluation['recovered']}",
            flush=True,
        )

    if recovered == 4:
        interpretation = "STRONG_GENERALIZATION"
    elif recovered == 3:
        interpretation = "ADEQUATE_GENERALIZATION"
    elif recovered == 2:
        interpretation = "INCOMPLETE_SENSITIVITY"
    else:
        interpretation = "POOR_BROAD_SENSITIVITY"

    output = {
        "stage": "drift_track_generalization_audit_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_GENERALIZATION_AUDIT.md",
        "variant": args.variant,
        "variant_config": drift.VARIANTS[args.variant],
        "controls_recovered": int(recovered),
        "controls_total": int(len(CONTROLS)),
        "interpretation": interpretation,
        "results": results,
    }
    (args.out / "drift_track_generalization.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Drift-track out-of-benchmark generalization audit",
        "",
        f"Variant: **{args.variant}**. Recovery: **{recovered}/4**. Interpretation: **{interpretation}**.",
        "",
        "| control | recovered | track N | radiant sep | speed delta | fitted slopes |",
        "|---|---|---:|---:|---:|---|",
    ]
    for name in CONTROLS:
        evaluation = results[name]["evaluation"]
        best = evaluation.get("best")
        if best is None:
            lines.append(f"| {name} | False | 0 | — | — | — |")
        else:
            lines.append(
                f"| {name} | {evaluation['recovered']} | {best['track_members']} | "
                f"{best['radiant_sep_deg']:.2f} | {best['speed_delta_km_s']:.2f} | "
                f"`{best['track_slopes']}` |"
            )
    markdown = "\n".join(lines) + "\n"
    (args.out / "DRIFT_TRACK_GENERALIZATION.md").write_text(markdown, encoding="utf-8")
    print(markdown, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
