#!/usr/bin/env python3
"""Execution correction: the preregistered design has 154 raw cells but 153 unique settings.

The baseline belongs to both the 81-cell scale factorial and the 9-cell HDBSCAN
factorial, so it is executed once. No scientific setting, range, metric, target
firewall, or stopping rule is changed by this correction.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
import run_hyperparameter_sensitivity as base

UNIQUE_CELLS = 153


def build_grid():
    settings = {}
    def add(scales, mcs, ms, source):
        key = (*map(float, scales), int(mcs), int(ms))
        settings.setdefault(key, set()).add(source)
    for scales in itertools.product(base.LON_SCALES, base.LAT_SCALES, base.SPEED_SCALES, base.SOLAR_SCALES):
        add(scales, 8, 4, "scale_factorial")
    for mcs, ms in itertools.product(base.MCS_LEVELS, base.MS_LEVELS):
        add(base.BASE_SCALES, mcs, ms, "hdbscan_factorial")
    for scales in itertools.product((2.5, 4.5), (2.0, 4.0), (1.5, 3.5), (1.5, 3.5)):
        for mcs, ms in base.HDBSCAN_CORNERS:
            add(scales, mcs, ms, "joint_extreme_interactions")
    rows = []
    for key in sorted(settings):
        lon, lat, speed, solar, mcs, ms = key
        rows.append({
            "feature_scales": [lon, lat, speed, solar],
            "min_cluster_size": mcs,
            "min_samples": ms,
            "grid_sources": sorted(settings[key]),
        })
    if len(rows) != UNIQUE_CELLS:
        raise RuntimeError(f"Expected {UNIQUE_CELLS} unique settings, found {len(rows)}")
    return rows


def run_shard(out: Path, shard_index: int, shard_count: int):
    grid = build_grid()
    selected = [(i, row) for i, row in enumerate(grid) if i % shard_count == shard_index]
    panel = base.load_panel()
    all_target = base.target_keys(base.YEARS)
    seed_target = base.target_keys(base.SEED_YEARS)
    if len(all_target) != 95 or len(seed_target) != 63:
        raise RuntimeError("target count mismatch")
    rows = []
    for pos, (i, setting) in enumerate(selected, 1):
        print(f"[{pos}/{len(selected)}] cell={i} {setting}", flush=True)
        row = base.evaluate_setting(i, setting, panel, all_target, seed_target)
        rows.append(row)
        print(f"RESULT cell={i} rank={row['rank']} overlap={row['final_overlap']}/95 N={row['final_member_count']} F1={row['final_f1']:.4f}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values("setting_index").to_csv(out / f"hyperparameter_cells_shard{shard_index}.csv", index=False)
    return 0


def aggregate(inputs, out: Path):
    paths = []
    for p in inputs:
        if p.is_dir():
            paths.extend(sorted(p.rglob("hyperparameter_cells_shard*.csv")))
        else:
            paths.append(p)
    frame = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    frame = frame.drop_duplicates(subset=["setting_index"], keep=False).sort_values("setting_index")
    if len(frame) != UNIQUE_CELLS or set(frame["setting_index"].astype(int)) != set(range(UNIQUE_CELLS)):
        raise RuntimeError(f"Expected {UNIQUE_CELLS} unique settings, found {len(frame)}")
    baseline = [r for r in frame.to_dict(orient="records") if base.baseline_match(r)]
    if len(baseline) != 1:
        raise RuntimeError(f"Expected exactly one baseline row, found {len(baseline)}")
    base.assert_baseline(baseline[0])
    tracked = frame[frame["tracked"] == True]  # noqa: E712
    top100 = tracked[tracked["within_top100"] == True]  # noqa: E712
    summary = {
        "stage": "acrf_v3_5_frozen_core_hyperparameter_robustness",
        "raw_design_cells": 154,
        "unique_parameter_settings": UNIQUE_CELLS,
        "baseline_reproduced": True,
        "tracked_cells": int(len(tracked)),
        "rank_le_100_cells": int(len(top100)),
        "rank_le_100_fraction": float(len(top100) / UNIQUE_CELLS),
        "exact_95_recovery_cells": int((frame["final_overlap"] == 95).sum()),
        "exact_95_recovery_fraction": float((frame["final_overlap"] == 95).mean()),
        "at_least_90_recovery_cells": int((frame["final_overlap"] >= 90).sum()),
        "at_least_90_recovery_fraction": float((frame["final_overlap"] >= 90).mean()),
        "at_least_80_recovery_cells": int((frame["final_overlap"] >= 80).sum()),
        "at_least_80_recovery_fraction": float((frame["final_overlap"] >= 80).mean()),
        "rank_quantiles_tracked": {str(q): float(tracked["rank"].quantile(q)) if len(tracked) else None for q in (0.0, 0.25, 0.5, 0.75, 1.0)},
        "final_overlap_quantiles_all_cells": {str(q): float(frame["final_overlap"].quantile(q)) for q in (0.0, 0.25, 0.5, 0.75, 1.0)},
        "final_f1_quantiles_top100": {str(q): float(top100["final_f1"].quantile(q)) if len(top100) else None for q in (0.0, 0.25, 0.5, 0.75, 1.0)},
        "member_count_range_top100": [int(top100["final_member_count"].min()) if len(top100) else None, int(top100["final_member_count"].max()) if len(top100) else None],
        "grid_breakdown": {},
        "interpretation_rule": "Frozen post-hoc sensitivity of the already selected ACRF-v3.5 method; no parameter replacement or tuning is authorized.",
        "count_correction": "154 raw design cells collapse to 153 unique settings because the baseline occurs in both the scale and HDBSCAN factorials.",
    }
    for source in ("scale_factorial", "hdbscan_factorial", "joint_extreme_interactions"):
        subset = frame[frame["grid_sources"].astype(str).str.contains(source, regex=False)]
        summary["grid_breakdown"][source] = {
            "cells": int(len(subset)),
            "rank_le_100_fraction": float((subset["within_top100"] == True).mean()),  # noqa: E712
            "exact_95_fraction": float((subset["final_overlap"] == 95).mean()),
            "at_least_90_fraction": float((subset["final_overlap"] >= 90).mean()),
            "at_least_80_fraction": float((subset["final_overlap"] >= 80).mean()),
            "median_final_overlap": float(subset["final_overlap"].median()),
            "minimum_final_overlap": int(subset["final_overlap"].min()),
            "maximum_final_overlap": int(subset["final_overlap"].max()),
        }
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "hyperparameter_sensitivity_cells.csv", index=False)
    (out / "hyperparameter_sensitivity_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# ACRF-v3.5 core-hyperparameter robustness", "",
        "Frozen post-hoc sensitivity; the selected method was not retuned.", "",
        "The preregistered design contains 154 raw cells but 153 unique settings because the baseline is shared by the scale and HDBSCAN factorials.", "",
        f"- Unique settings: **{UNIQUE_CELLS}**",
        f"- Baseline reproduced exactly: **{summary['baseline_reproduced']}**",
        f"- Rank <= 100: **{summary['rank_le_100_cells']}/{UNIQUE_CELLS} ({summary['rank_le_100_fraction']:.1%})**",
        f"- Exact 95/95: **{summary['exact_95_recovery_cells']}/{UNIQUE_CELLS} ({summary['exact_95_recovery_fraction']:.1%})**",
        f"- >=90/95: **{summary['at_least_90_recovery_cells']}/{UNIQUE_CELLS} ({summary['at_least_90_recovery_fraction']:.1%})**",
        f"- >=80/95: **{summary['at_least_80_recovery_cells']}/{UNIQUE_CELLS} ({summary['at_least_80_recovery_fraction']:.1%})**",
    ]
    (out / "HYPERPARAMETER_ROBUSTNESS.md").write_text("\n".join(lines) + "\n")
    print("SUMMARY_JSON=" + json.dumps(summary, sort_keys=True), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--aggregate", nargs="*", type=Path)
    args = parser.parse_args()
    if args.aggregate is not None:
        return aggregate(args.aggregate, args.out)
    if args.shard_index is None or args.shard_count is None:
        parser.error("shard mode requires --shard-index and --shard-count")
    return run_shard(args.out, args.shard_index, args.shard_count)

if __name__ == "__main__":
    raise SystemExit(main())
