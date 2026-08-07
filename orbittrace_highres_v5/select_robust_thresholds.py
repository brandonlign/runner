#!/usr/bin/env python3
"""Select the frozen v5 reporting thresholds from 2025+2023 development only."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from typing import Any, Callable

DENOMINATOR = 513
MAX_RANK = 26
FPR_CAP = 0.055
SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03
V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
BROWN = "brown2010_wavelet_episode_core"
YEARS = (2025, 2023)
KS = (4, 6, 8, 12)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year2025", required=True, type=Path)
    parser.add_argument("--year2023", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def find_benchmark(directory: Path, year: int) -> Path:
    candidates = sorted(directory.glob(f"sonotaco_{year}_*.json"))
    candidates = [path for path in candidates if "V" not in path.name.upper()]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one benchmark JSON for {year}, found {[p.name for p in candidates]}")
    return candidates[0]


def load_year(directory: Path, year: int) -> dict[str, Any]:
    benchmark_path = find_benchmark(directory, year)
    benchmark = json.loads(benchmark_path.read_text())
    negative = read_jsonl_gz(directory / "negative_literature_records.jsonl.gz")
    positive = read_jsonl_gz(directory / "positive_literature_records.jsonl.gz")
    if int(benchmark["configuration"]["year"]) != year:
        raise RuntimeError(f"year mismatch for {benchmark_path}")
    if int(benchmark["configuration"]["calibration_per_bin"]) != 512:
        raise RuntimeError(f"{year}: calibration is not 512")
    if not all(bool(value) for value in benchmark["gates"].values()):
        raise RuntimeError(f"{year}: upstream benchmark integrity failure")
    if V3 not in benchmark["metrics"] or FIXED4 not in benchmark["metrics"] or BROWN not in benchmark["metrics"]:
        raise RuntimeError(f"{year}: missing required methods")
    if float(benchmark["metrics"][V3]["weak_auc"]) + 1e-15 < float(benchmark["metrics"][BROWN]["weak_auc"]):
        raise RuntimeError(f"{year}: v3 AUROC no longer reaches Brown")
    for row in negative + positive:
        for method in (V3, FIXED4):
            value = float(row["p"][method])
            rank = round(value * DENOMINATOR)
            if rank < 1 or abs(value - rank / DENOMINATOR) > 1e-12:
                raise RuntimeError(f"{year}: off-grid p-value method={method} p={value}")
    return {"benchmark": benchmark, "negative": negative, "positive": positive}


def metrics_for_rule(payload: dict[str, Any], detected: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    negative = payload["negative"]
    positive = payload["positive"]
    negative_flags = [bool(detected(row)) for row in negative]
    pooled_fpr = sum(negative_flags) / len(negative_flags)
    sectors: dict[int, list[bool]] = {}
    for row, flag in zip(negative, negative_flags):
        sectors.setdefault(int(row["reporting_sector"]), []).append(flag)
    sector_fpr = {str(sector): sum(flags) / len(flags) for sector, flags in sorted(sectors.items())}
    recall: dict[str, float] = {}
    for k in KS:
        rows = [row for row in positive if int(row["k"]) == k]
        recall[str(k)] = sum(bool(detected(row)) for row in rows) / len(rows)
    return {
        "pooled_fpr": pooled_fpr,
        "sector_fpr": sector_fpr,
        "worst_sector_fpr": max(sector_fpr.values()),
        "recall": recall,
    }


def references(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["benchmark"]["metrics"]
    return {
        "v3_auc": float(metrics[V3]["weak_auc"]),
        "brown_auc": float(metrics[BROWN]["weak_auc"]),
        "fixed4_k4": float(metrics[FIXED4]["recall"]["0.05"]["4"]),
        "brown_recall": {str(k): float(metrics[BROWN]["recall"]["0.05"][str(k)]) for k in KS},
    }


def evaluate_pair(payloads: dict[int, dict[str, Any]], r_v3: int, r_f4: int) -> dict[str, Any]:
    threshold_v3 = r_v3 / DENOMINATOR
    threshold_f4 = r_f4 / DENOMINATOR
    result: dict[str, Any] = {
        "r_v3": r_v3,
        "r_fixed4": r_f4,
        "p_v3": threshold_v3,
        "p_fixed4": threshold_f4,
        "years": {},
    }
    all_margins: list[float] = []
    feasible = True
    max_fpr = 0.0
    for year in YEARS:
        payload = payloads[year]
        refs = references(payload)
        measured = metrics_for_rule(
            payload,
            lambda row, tv=threshold_v3, tf=threshold_f4: (
                float(row["p"][V3]) <= tv or float(row["p"][FIXED4]) <= tf
            ),
        )
        margins = {
            "k4": measured["recall"]["4"] - refs["fixed4_k4"],
            "k6": measured["recall"]["6"] - (refs["brown_recall"]["6"] - RECALL_TOLERANCE),
            "k8": measured["recall"]["8"] - (refs["brown_recall"]["8"] - RECALL_TOLERANCE),
            "k12": measured["recall"]["12"] - (refs["brown_recall"]["12"] - RECALL_TOLERANCE),
        }
        gates = {
            "v3_auc_at_least_brown": refs["v3_auc"] + 1e-15 >= refs["brown_auc"],
            "pooled_fpr_at_most_0055": measured["pooled_fpr"] <= FPR_CAP + 1e-15,
            "worst_sector_fpr_at_most_008": measured["worst_sector_fpr"] <= SECTOR_FPR_CAP + 1e-15,
            "k4_at_least_fixed4": margins["k4"] >= -1e-15,
            "k6_within_003_of_brown": margins["k6"] >= -1e-15,
            "k8_within_003_of_brown": margins["k8"] >= -1e-15,
            "k12_within_003_of_brown": margins["k12"] >= -1e-15,
        }
        feasible = feasible and all(gates.values())
        all_margins.extend(margins.values())
        max_fpr = max(max_fpr, measured["pooled_fpr"])
        result["years"][str(year)] = {
            "references": refs,
            "metrics": measured,
            "recall_margins": margins,
            "gates": gates,
        }
    result["feasible"] = bool(feasible)
    result["minimum_recall_margin"] = min(all_margins)
    result["maximum_pooled_fpr"] = max_fpr
    return result


def selection_key(row: dict[str, Any]) -> tuple[float, float, int, int, int, int]:
    return (
        -float(row["minimum_recall_margin"]),
        float(row["maximum_pooled_fpr"]),
        -int(row["r_v3"]),
        int(row["r_fixed4"]),
        int(row["r_v3"]),
        int(row["r_fixed4"]),
    )


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    payloads = {
        2025: load_year(args.year2025, 2025),
        2023: load_year(args.year2023, 2023),
    }
    grid = [
        evaluate_pair(payloads, r_v3, r_f4)
        for r_v3 in range(1, MAX_RANK + 1)
        for r_f4 in range(1, MAX_RANK + 1)
    ]
    feasible = [row for row in grid if row["feasible"]]
    selected = min(feasible, key=selection_key) if feasible else None
    verdict = "PASS_V5_HIGHRES_DEVELOPMENT" if selected is not None else "FAIL_V5_HIGHRES_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "development_years": list(YEARS),
            "calibration_per_bin": 512,
            "denominator": DENOMINATOR,
            "rank_grid": [1, MAX_RANK],
            "grid_pairs": len(grid),
            "fpr_cap": FPR_CAP,
            "sector_fpr_cap": SECTOR_FPR_CAP,
            "recall_tolerance": RECALL_TOLERANCE,
            "selector": "maximin recall margin; then minimum worst-year FPR; then maximum v3 rank; then minimum fixed4 rank",
        },
        "feasible_pairs": len(feasible),
        "selected": selected,
        "grid": grid,
    }
    (args.output / "V5_DEVELOPMENT_SELECTION.json").write_text(json.dumps(result, indent=2) + "\n")

    with (args.output / "V5_THRESHOLD_GRID.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "r_v3", "r_fixed4", "p_v3", "p_fixed4", "feasible", "minimum_recall_margin", "maximum_pooled_fpr",
            "fpr_2025", "k4_2025", "k6_2025", "k8_2025", "k12_2025",
            "fpr_2023", "k4_2023", "k6_2023", "k8_2023", "k12_2023",
        ])
        for row in grid:
            y25 = row["years"]["2025"]["metrics"]
            y23 = row["years"]["2023"]["metrics"]
            writer.writerow([
                row["r_v3"], row["r_fixed4"], row["p_v3"], row["p_fixed4"], int(row["feasible"]),
                row["minimum_recall_margin"], row["maximum_pooled_fpr"],
                y25["pooled_fpr"], *(y25["recall"][str(k)] for k in KS),
                y23["pooled_fpr"], *(y23["recall"][str(k)] for k in KS),
            ])

    lines = [
        "# OrbitTrace v5 high-resolution development selection",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Feasible pairs: **{len(feasible)}/{len(grid)}**",
        "",
    ]
    if selected is not None:
        lines.extend([
            f"Selected ranks: **v3={selected['r_v3']}/513, fixed4={selected['r_fixed4']}/513**",
            "",
            f"Minimum recall margin across both years: **{selected['minimum_recall_margin']:.6f}**",
            "",
            f"Maximum pooled FPR across both years: **{selected['maximum_pooled_fpr']:.6f}**",
            "",
        ])
        for year in YEARS:
            block = selected["years"][str(year)]
            metric = block["metrics"]
            refs = block["references"]
            lines.extend([
                f"## {year}",
                "",
                f"- v3 AUROC: `{refs['v3_auc']:.6f}` vs Brown `{refs['brown_auc']:.6f}`",
                f"- pooled FPR: `{metric['pooled_fpr']:.6f}`; worst-sector FPR: `{metric['worst_sector_fpr']:.6f}`",
                "- recall k=4/6/8/12: " + " / ".join(f"{metric['recall'][str(k)]:.6f}" for k in KS),
                "",
            ])
    lines.append("The complete 676-pair grid is preserved in `V5_THRESHOLD_GRID.csv` and the JSON artifact.")
    (args.output / "V5_DEVELOPMENT_SELECTION.md").write_text("\n".join(lines) + "\n")
    print("PASS_V5_SELECTOR_EXECUTION", verdict, len(feasible))


if __name__ == "__main__":
    main()