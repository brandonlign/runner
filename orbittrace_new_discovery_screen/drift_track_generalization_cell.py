#!/usr/bin/env python3
"""One out-of-benchmark positive-control audit cell for selected variant A."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as drift
from orbittrace_new_discovery_screen.drift_track_generalization import CONTROLS

SELECTED_VARIANT = "A_EOM_5_3"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", choices=sorted(CONTROLS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    name = str(args.control)
    control = CONTROLS[name]
    month = int(control["month"])
    prepared = drift.prepare_all_quality(base.load_month(2025, month), 2025, month)
    tracks, diagnostics = drift.tracks_for_variant(prepared, SELECTED_VARIANT)
    evaluation = drift.evaluate_control(name, control, tracks, prepared)
    output = {
        "stage": "drift_track_generalization_cell_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_GENERALIZATION_AUDIT.md",
        "selected_variant": SELECTED_VARIANT,
        "control_name": name,
        "control": control,
        "quality_rows": int(len(prepared["data"])),
        "diagnostics": diagnostics,
        "evaluation": evaluation,
    }
    (args.out / f"generalization_{name}.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        f"{name}: tracks={len(tracks)} recovered={evaluation['recovered']} "
        f"best={evaluation.get('best')}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
