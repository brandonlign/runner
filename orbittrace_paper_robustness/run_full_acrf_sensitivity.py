#!/usr/bin/env python3
"""Run the frozen 19-cell full ACRF-v3.5 robustness grid.

The private OrbitTrace repository is checked out separately by the workflow and
added to PYTHONPATH. In each shard, every assigned ACRF catalogue is generated
and its top-100 final memberships are frozen before the canonical target table
is opened for post-hoc family tracking.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from pipeline.pr57_novel import run_novel_search as base
from pipeline.unified_v2.application import _feature_panel, _prepare
from pipeline.unified_v3.config import V3Config
from pipeline.unified_v3.method import build_multiscale_catalogue

YEARS = (2022, 2023, 2024, 2025, 2026)
SEED_YEARS = (2025, 2026)
MONTH = 4
BASE_SCALES = (3.5, 3.0, 2.5, 2.5)
TARGET_REL = Path("candidate/mdc/OrbitTrace_April_95_GMN_lookup.csv")
EXPECTED = {
    "rank": 7,
    "reported": 123,
    "overlap": 95,
    "precision": 0.7723577235772358,
    "recall": 1.0,
    "f1": 0.8715596330275228,
}


def grid() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mcs in (6, 8, 12):
        for ms in (2, 4, 6):
            rows.append({
                "id": f"hdbscan_mcs{mcs}_ms{ms}",
                "source": "hdbscan_factorial",
                "feature_scales": list(BASE_SCALES),
                "min_cluster_size": mcs,
                "min_samples": ms,
            })
    names = ("lon", "lat", "speed", "solar")
    for dim, name in enumerate(names):
        for multiplier in (0.8, 1.2):
            scales = list(BASE_SCALES)
            scales[dim] *= multiplier
            rows.append({
                "id": f"scale_{name}_{multiplier:.1f}x",
                "source": "one_at_a_time_scale_perturbation",
                "feature_scales": scales,
                "min_cluster_size": 8,
                "min_samples": 4,
            })
    for multiplier in (0.8, 1.2):
        rows.append({
            "id": f"scales_joint_{multiplier:.1f}x",
            "source": "joint_scale_perturbation",
            "feature_scales": [value * multiplier for value in BASE_SCALES],
            "min_cluster_size": 8,
            "min_samples": 4,
        })
    if len(rows) != 19 or len({row["id"] for row in rows}) != 19:
        raise RuntimeError("Frozen full-ACRF grid must contain exactly 19 cells")
    return rows


def timestamp_key(value: Any) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    return digits[:14]


def target_keys(path: Path) -> set[str]:
    frame = pd.read_csv(path)
    timestamps = pd.to_datetime(frame["Tobs"], format="%Y-%m-%d-%H:%M:%S", errors="coerce")
    keys = {value.strftime("%Y%m%d%H%M%S") for value in timestamps.dropna()}
    if len(keys) != 95:
        raise RuntimeError(f"Expected 95 canonical target timestamps, found {len(keys)}")
    return keys


def source_sha(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def load_panel() -> dict[str, Any]:
    frames = []
    years = []
    ids: list[str] = []
    metadata: dict[str, Any] = {}
    for year in YEARS:
        prepared = _prepare(base.load_month(year, MONTH), year, MONTH)
        data = prepared["data"].copy()
        event_ids = data["unique_trajectory_identifier"].astype(str).to_numpy()
        if len(set(event_ids.tolist())) != len(event_ids):
            raise RuntimeError(f"Duplicate event IDs in {year}-{MONTH:02d}")
        frames.append(data)
        years.append(np.full(len(data), year, dtype=np.int64))
        ids.extend(event_ids.tolist())
        metadata[str(year)] = {
            "rows": int(len(data)),
            "quality_rows_before_sampling": int(prepared["quality_rows"]),
        }
    all_data = pd.concat(frames, ignore_index=True, sort=False)
    year_array = np.concatenate(years)
    event_ids = np.asarray(ids, dtype=str)
    if len(set(event_ids.tolist())) != len(event_ids):
        raise RuntimeError("Event IDs must be unique across the full panel")
    return {
        "frames": frames,
        "data": all_data,
        "years": year_array,
        "event_ids": event_ids,
        "solar": all_data["sol_lon_deg"].to_numpy(float),
        "orbits": all_data[base.ORBIT_COLUMNS].to_numpy(float),
        "metadata": metadata,
    }


def config_for(setting: dict[str, Any]) -> V3Config:
    return replace(
        V3Config(),
        feature_scales=tuple(float(value) for value in setting["feature_scales"]),
        min_cluster_size=int(setting["min_cluster_size"]),
        min_samples=int(setting["min_samples"]),
    )


def run_setting(setting: dict[str, Any], panel: dict[str, Any]) -> dict[str, Any]:
    config = config_for(setting)
    matrix = np.vstack([_feature_panel(frame, config) for frame in panel["frames"]])
    candidates, diagnostics = build_multiscale_catalogue(
        matrix,
        panel["years"],
        panel["event_ids"],
        panel["solar"],
        panel["orbits"],
        config,
        expansion_limit=100,
        seed_years=SEED_YEARS,
    )
    frozen_candidates = []
    for candidate in candidates:
        if "final_event_ids" not in candidate:
            continue
        frozen_candidates.append({
            "rank": int(candidate["global_rank"]),
            "family_id": str(candidate["family_id"]),
            "scale": candidate.get("scale"),
            "hierarchy_method": candidate.get("hierarchy_method"),
            "membership_mode": candidate.get("membership_mode"),
            "seed_member_count": int(candidate.get("member_count", len(candidate.get("event_ids", ())))),
            "final_event_ids": sorted(map(str, candidate["final_event_ids"])),
        })
    return {
        "id": setting["id"],
        "source": setting["source"],
        "feature_scales": [float(value) for value in setting["feature_scales"]],
        "min_cluster_size": int(setting["min_cluster_size"]),
        "min_samples": int(setting["min_samples"]),
        "candidate_count": int(len(candidates)),
        "materialized_candidates": int(len(frozen_candidates)),
        "diagnostics": {
            "seed_events": int(diagnostics["seed_events"]),
            "application_events": int(diagnostics["application_events"]),
            "ranked_candidates": int(diagnostics["ranked_candidates"]),
        },
        "frozen_candidates": frozen_candidates,
    }


def score_candidate(candidate: dict[str, Any], target: set[str]) -> dict[str, Any]:
    reported = {timestamp_key(value) for value in candidate["final_event_ids"]}
    overlap = len(reported & target)
    precision = overlap / len(reported) if reported else 0.0
    recall = overlap / len(target)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "rank": int(candidate["rank"]),
        "family_id": candidate["family_id"],
        "scale": candidate.get("scale"),
        "hierarchy_method": candidate.get("hierarchy_method"),
        "membership_mode": candidate.get("membership_mode"),
        "reported": int(len(reported)),
        "overlap": int(overlap),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def reveal_setting(frozen: dict[str, Any], target: set[str]) -> dict[str, Any]:
    scored = [score_candidate(candidate, target) for candidate in frozen["frozen_candidates"]]
    scored = [item for item in scored if item["overlap"] > 0]
    scored.sort(key=lambda item: (-item["f1"], -item["overlap"], item["rank"]))
    best = scored[0] if scored else None
    row = {
        "id": frozen["id"],
        "source": frozen["source"],
        "lon_scale_deg": frozen["feature_scales"][0],
        "lat_scale_deg": frozen["feature_scales"][1],
        "speed_scale_km_s": frozen["feature_scales"][2],
        "solar_scale_deg": frozen["feature_scales"][3],
        "min_cluster_size": frozen["min_cluster_size"],
        "min_samples": frozen["min_samples"],
        "candidate_count": frozen["candidate_count"],
        "materialized_candidates": frozen["materialized_candidates"],
        "tracked": best is not None,
        "rank": None,
        "reported": 0,
        "overlap": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "family_id": None,
        "scale": None,
        "hierarchy_method": None,
        "membership_mode": None,
    }
    if best:
        row.update(best)
    return row


def baseline_row(row: dict[str, Any]) -> bool:
    return (
        row["feature_scales"] == list(BASE_SCALES)
        and row["min_cluster_size"] == 8
        and row["min_samples"] == 4
    )


def assert_baseline(row: dict[str, Any]) -> None:
    for key, expected in EXPECTED.items():
        observed = row[key]
        if isinstance(expected, float):
            if not np.isclose(float(observed), expected, rtol=1e-12, atol=1e-12):
                raise RuntimeError(f"Baseline mismatch: {key}={observed}, expected {expected}")
        elif int(observed) != int(expected):
            raise RuntimeError(f"Baseline mismatch: {key}={observed}, expected {expected}")


def run_shard(out: Path, shard_index: int, shard_count: int, orbittrace_repo: Path) -> None:
    settings = grid()
    assigned = [setting for index, setting in enumerate(settings) if index % shard_count == shard_index]
    print(f"full ACRF shard {shard_index}/{shard_count}: {len(assigned)} cells", flush=True)
    panel = load_panel()
    frozen = []
    for index, setting in enumerate(assigned, start=1):
        print(f"[{index}/{len(assigned)}] {setting['id']}", flush=True)
        item = run_setting(setting, panel)
        frozen.append(item)
        print(
            f"  target-free ranked={item['candidate_count']} materialized={item['materialized_candidates']}",
            flush=True,
        )

    # Target firewall: open target only after every assigned catalogue is frozen.
    target = target_keys(orbittrace_repo / TARGET_REL)
    rows = [reveal_setting(item, target) for item in frozen]
    for item, row in zip(frozen, rows):
        if baseline_row(item):
            assert_baseline(row)
    for row in rows:
        print(
            f"  reveal {row['id']}: rank={row['rank']} overlap={row['overlap']}/95 "
            f"N={row['reported']} F1={row['f1']:.4f}", flush=True
        )

    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / f"full_acrf_rows_shard{shard_index}.csv", index=False)
    payload = {
        "stage": "full_acrf_v3_5_posthoc_sensitivity_shard",
        "shard_index": shard_index,
        "shard_count": shard_count,
        "source_commit": source_sha(orbittrace_repo),
        "target_opened_only_after_all_assigned_catalogues_frozen": True,
        "input": panel["metadata"],
        "rows": rows,
    }
    (out / f"full_acrf_rows_shard{shard_index}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


def aggregate(inputs: list[Path], out: Path) -> None:
    files: list[Path] = []
    for path in inputs:
        if path.is_dir():
            files.extend(sorted(path.rglob("full_acrf_rows_shard*.csv")))
        else:
            files.append(path)
    frame = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    frame = frame.drop_duplicates(subset=["id"], keep=False)
    if len(frame) != 19:
        raise RuntimeError(f"Expected 19 unique full-ACRF cells, found {len(frame)}")
    base = frame[
        (frame["lon_scale_deg"] == 3.5)
        & (frame["lat_scale_deg"] == 3.0)
        & (frame["speed_scale_km_s"] == 2.5)
        & (frame["solar_scale_deg"] == 2.5)
        & (frame["min_cluster_size"] == 8)
        & (frame["min_samples"] == 4)
    ]
    if len(base) != 1:
        raise RuntimeError(f"Expected one baseline, found {len(base)}")
    base_row = base.iloc[0].to_dict()
    for key, expected in EXPECTED.items():
        observed = base_row[key]
        if isinstance(expected, float):
            if not np.isclose(float(observed), expected, rtol=1e-12, atol=1e-12):
                raise RuntimeError(f"Baseline mismatch in aggregate: {key}")
        elif int(observed) != int(expected):
            raise RuntimeError(f"Baseline mismatch in aggregate: {key}")

    summary = {
        "stage": "full_acrf_v3_5_posthoc_hyperparameter_robustness",
        "cells": 19,
        "baseline_reproduced": True,
        "rank_le_100_cells": int(frame["rank"].notna().sum()),
        "exact_95_cells": int((frame["overlap"] == 95).sum()),
        "at_least_90_cells": int((frame["overlap"] >= 90).sum()),
        "at_least_85_cells": int((frame["overlap"] >= 85).sum()),
        "f1_ge_080_cells": int((frame["f1"] >= 0.80).sum()),
        "overlap_range": [int(frame["overlap"].min()), int(frame["overlap"].max())],
        "overlap_median": float(frame["overlap"].median()),
        "f1_range": [float(frame["f1"].min()), float(frame["f1"].max())],
        "f1_median": float(frame["f1"].median()),
        "rank_range": [int(frame["rank"].min()), int(frame["rank"].max())],
        "breakdown": {},
        "interpretation": "Post-hoc robustness of the already selected ACRF-v3.5 method; no alternative setting is selected from this grid.",
    }
    for source in ("hdbscan_factorial", "one_at_a_time_scale_perturbation", "joint_scale_perturbation"):
        subset = frame[frame["source"] == source]
        summary["breakdown"][source] = {
            "cells": int(len(subset)),
            "exact_95": int((subset["overlap"] == 95).sum()),
            "at_least_90": int((subset["overlap"] >= 90).sum()),
            "at_least_85": int((subset["overlap"] >= 85).sum()),
            "f1_ge_080": int((subset["f1"] >= 0.80).sum()),
            "overlap_range": [int(subset["overlap"].min()), int(subset["overlap"].max())],
            "median_overlap": float(subset["overlap"].median()),
            "rank_range": [int(subset["rank"].min()), int(subset["rank"].max())],
        }

    out.mkdir(parents=True, exist_ok=True)
    frame.sort_values(["source", "id"]).to_csv(out / "full_acrf_sensitivity_cells.csv", index=False)
    (out / "full_acrf_sensitivity_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# Full ACRF-v3.5 hyperparameter robustness", "",
        "Post-hoc robustness analysis of the already selected method; no cell is used for retuning.", "",
        f"- Frozen cells: **19**",
        f"- Baseline reproduced exactly: **{summary['baseline_reproduced']}**",
        f"- Exact 95/95 recovery: **{summary['exact_95_cells']}/19**",
        f"- At least 90/95: **{summary['at_least_90_cells']}/19**",
        f"- At least 85/95: **{summary['at_least_85_cells']}/19**",
        f"- F1 >= 0.80: **{summary['f1_ge_080_cells']}/19**",
        f"- Overlap median/range: **{summary['overlap_median']:.1f} / {summary['overlap_range'][0]}-{summary['overlap_range'][1]}**",
        f"- Rank range: **{summary['rank_range'][0]}-{summary['rank_range'][1]}**", "",
    ]
    for source, item in summary["breakdown"].items():
        lines += [
            f"## {source}", "",
            f"- Cells: {item['cells']}",
            f"- Exact 95/95: {item['exact_95']}/{item['cells']}",
            f"- >=90/95: {item['at_least_90']}/{item['cells']}",
            f"- >=85/95: {item['at_least_85']}/{item['cells']}",
            f"- F1 >= 0.80: {item['f1_ge_080']}/{item['cells']}",
            f"- Overlap median/range: {item['median_overlap']:.1f} / {item['overlap_range'][0]}-{item['overlap_range'][1]}",
            f"- Rank range: {item['rank_range'][0]}-{item['rank_range'][1]}", "",
        ]
    (out / "FULL_ACRF_HYPERPARAMETER_ROBUSTNESS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--orbittrace-repo", type=Path, default=Path("orbittrace"))
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--aggregate", nargs="*", type=Path)
    args = parser.parse_args()
    if args.aggregate is not None:
        aggregate(args.aggregate, args.out)
        return
    if args.shard_index is None or args.shard_count is None:
        parser.error("Shard mode requires --shard-index and --shard-count")
    run_shard(args.out, args.shard_index, args.shard_count, args.orbittrace_repo)


if __name__ == "__main__":
    main()
