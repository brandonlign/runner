#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

N_FOLDS = 10
YEARS = (2022, 2023)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for fold in range(N_FOLDS):
        matches = list(a.input_root.rglob(f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{fold}.json"))
        req(len(matches) == 1, f"expected exactly one result for fold {fold}, got {matches}")
        path = matches[0]
        r = json.loads(path.read_text())
        req(r["scientific_role"] == "TARGET_EXCLUDED_GMN_2022_2023_TRAIN_ROBUSTNESS_ONLY", f"wrong role fold {fold}")
        req(int(r["fold"]) == fold, f"fold identity mismatch {fold}")
        req(r["blind_exclusion"] == [20.0, 55.0], f"blind mismatch fold {fold}")
        for key in (
            "target_information_access", "target_region_events_accessed", "sonotaco_2013_2014_access",
            "amos_2023_2024_access", "asfn_access", "efn_access", "maarsy_scientific_access", "dms_scientific_access",
        ):
            req(r[key] is False, f"forbidden access {key} fold {fold}")
        rows.append(r)

    panels: list[dict[str, Any]] = []
    for r in rows:
        for year in YEARS:
            y = str(year)
            pm = r["parent_metrics"][y]
            sm = r["successor_metrics"][y]
            panels.append({
                "fold": int(r["fold"]),
                "year": year,
                "parent_recovered_at_50": int(pm["recovered_at_50"]),
                "successor_recovered_at_50": int(sm["recovered_at_50"]),
                "delta_recovered_at_50": int(sm["recovered_at_50"]) - int(pm["recovered_at_50"]),
                "parent_recovered_at_100": int(pm["recovered_at_100"]),
                "successor_recovered_at_100": int(sm["recovered_at_100"]),
                "delta_recovered_at_100": int(sm["recovered_at_100"]) - int(pm["recovered_at_100"]),
                "parent_top100_precision": float(pm["top100_dominant_precision"]),
                "successor_top100_precision": float(sm["top100_dominant_precision"]),
                "delta_top100_precision": float(sm["top100_dominant_precision"]) - float(pm["top100_dominant_precision"]),
                "parent_mrr": float(pm["mrr"]),
                "successor_mrr": float(sm["mrr"]),
                "delta_mrr": float(sm["mrr"]) - float(pm["mrr"]),
                "parent_fragmentation": float(pm["fragmentation_median_top500"]),
                "successor_fragmentation": float(sm["fragmentation_median_top500"]),
            })

    parent50 = sum(x["parent_recovered_at_50"] for x in panels)
    succ50 = sum(x["successor_recovered_at_50"] for x in panels)
    parent100 = sum(x["parent_recovered_at_100"] for x in panels)
    succ100 = sum(x["successor_recovered_at_100"] for x in panels)
    parent_precision = float(np.mean([x["parent_top100_precision"] for x in panels]))
    succ_precision = float(np.mean([x["successor_top100_precision"] for x in panels]))
    parent_mrr = float(np.mean([x["parent_mrr"] for x in panels]))
    succ_mrr = float(np.mean([x["successor_mrr"] for x in panels]))
    parent_frag = float(median([x["parent_fragmentation"] for x in panels]))
    succ_frag = float(median([x["successor_fragmentation"] for x in panels]))
    active_folds = sum(bool(r["mechanism_active"]) for r in rows)

    gates = {
        "total_recovered_at_50_not_lower": succ50 >= parent50,
        "total_recovered_at_100_strictly_higher": succ100 > parent100,
        "mean_top100_precision_not_lower": succ_precision >= parent_precision,
        "mean_mrr_not_lower": succ_mrr >= parent_mrr,
        "median_fragmentation_not_higher": succ_frag <= parent_frag,
        "mechanism_active_some_fold": active_folds >= 1,
    }
    passed = all(gates.values())
    verdict = "PASS_DENSITY_SYNC_GMN_TRAIN_CV_V1" if passed else "FAIL_DENSITY_SYNC_GMN_TRAIN_CV_V1"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_TRAIN_ROBUSTNESS_AGGREGATE_ONLY",
        "fold_count": N_FOLDS,
        "year_fold_panel_count": len(panels),
        "active_folds": active_folds,
        "aggregate": {
            "parent_total_recovered_at_50": parent50,
            "successor_total_recovered_at_50": succ50,
            "delta_total_recovered_at_50": succ50 - parent50,
            "parent_total_recovered_at_100": parent100,
            "successor_total_recovered_at_100": succ100,
            "delta_total_recovered_at_100": succ100 - parent100,
            "parent_mean_top100_precision": parent_precision,
            "successor_mean_top100_precision": succ_precision,
            "delta_mean_top100_precision": succ_precision - parent_precision,
            "parent_mean_mrr": parent_mrr,
            "successor_mean_mrr": succ_mrr,
            "delta_mean_mrr": succ_mrr - parent_mrr,
            "parent_median_fragmentation": parent_frag,
            "successor_median_fragmentation": succ_frag,
        },
        "gates": gates,
        "panels": panels,
        "fold_result_sha256": {str(r["fold"]): sha(next(iter(a.input_root.rglob(f"DENSITY_SYNC_GMN_TRAIN_CV_V1_FOLD_{r['fold']}.json")))) for r in rows},
        "blind_exclusion": [20.0, 55.0],
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_2023_2024_access": False,
        "asfn_access": False,
        "efn_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "DENSITY_SYNC_GMN_TRAIN_CV_V1_AGGREGATE.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
