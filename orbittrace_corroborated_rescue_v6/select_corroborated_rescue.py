#!/usr/bin/env python3
"""Select the frozen OrbitTrace-v6 corroborated sparse-rescue decision."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

DENOMINATOR = 513
PRIMARY_RANKS = tuple(range(1, 27))
FIXED4_RANKS = tuple(range(1, 27))
CORROBORATION_RANKS = tuple(range(26, 129))
DEVELOPMENT_YEARS = (2025, 2023, 2024)
KS = (4, 6, 8, 12)
FPR_CAP = 0.055
SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03
METHOD_V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
METHOD_FIXED4 = "orbittrace_fixed4"
METHOD_BROWN = "brown2010_wavelet_episode_core"

FROZEN_REFERENCES: dict[int, dict[str, Any]] = {
    2025: {
        "fixed4_k4": 0.15441176470588236,
        "brown_recall": {"6": 0.5955882352941176, "8": 0.8308823529411765, "12": 0.9485294117647058},
    },
    2023: {
        "fixed4_k4": 0.18902439024390244,
        "brown_recall": {"6": 0.5426829268292683, "8": 0.7987804878048781, "12": 0.9207317073170732},
    },
    2024: {
        "fixed4_k4": 0.18181818181818182,
        "brown_recall": {"6": 0.5454545454545454, "8": 0.7954545454545454, "12": 0.9318181818181818},
    },
}

EXPECTED_AUC = {
    2025: {"v3": 0.836860, "brown": 0.828506},
    2023: {"v3": 0.836263, "brown": 0.831972},
    2024: {"v3": 0.855869, "brown": 0.850314},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year2025", required=True, type=Path)
    parser.add_argument("--year2023", required=True, type=Path)
    parser.add_argument("--year2024", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def exact_rank(value: float) -> int:
    rank = round(float(value) * DENOMINATOR)
    if rank < 1 or abs(float(value) - rank / DENOMINATOR) > 1e-12:
        raise RuntimeError(f"off-grid denominator-{DENOMINATOR} p-value: {value}")
    return int(rank)


def load_year(directory: Path, year: int) -> dict[str, Any]:
    if year == 2025:
        benchmark = json.loads((directory / "sonotaco_2025_literature_comparison.json").read_text())
        negative = read_jsonl_gz(directory / "negative_literature_records.jsonl.gz")
        positive = read_jsonl_gz(directory / "positive_literature_records.jsonl.gz")
        if benchmark["verdict"] != "PASS_SONOTACO_2025_LITERATURE_COMPARISON":
            raise RuntimeError("invalid 2025 predecessor artifact")
        v3_auc = float(benchmark["metrics"][METHOD_V3]["weak_auc"])
        brown_auc = float(benchmark["metrics"][METHOD_BROWN]["weak_auc"])
        getter = lambda row, method: float(row["p"][method])
    elif year == 2023:
        benchmark = json.loads((directory / "sonotaco_2023_literature_transfer.json").read_text())
        negative = read_jsonl_gz(directory / "negative_literature_records.jsonl.gz")
        positive = read_jsonl_gz(directory / "positive_literature_records.jsonl.gz")
        if benchmark["verdict"] != "PASS_SONOTACO_2023_LITERATURE_TRANSFER":
            raise RuntimeError("invalid 2023 predecessor artifact")
        v3_auc = float(benchmark["metrics"][METHOD_V3]["weak_auc"])
        brown_auc = float(benchmark["metrics"][METHOD_BROWN]["weak_auc"])
        getter = lambda row, method: float(row["p"][method])
    elif year == 2024:
        benchmark = json.loads((directory / "SONOTACO_2024_V5_PROSPECTIVE_RESULT.json").read_text())
        negative = read_jsonl_gz(directory / "negative_records.jsonl.gz")
        positive = read_jsonl_gz(directory / "positive_records.jsonl.gz")
        if benchmark["verdict"] != "FAIL_V5_SONOTACO_2024_PROSPECTIVE_VALIDATION":
            raise RuntimeError("2024 successor development must preserve the frozen v5 failure")
        v3_auc = float(benchmark["raw_auc"][METHOD_V3])
        brown_auc = float(benchmark["raw_auc"][METHOD_BROWN])
        getter = lambda row, method: float(row["p_v5"][method])
    else:
        raise RuntimeError(f"unsupported development year {year}")

    expected = EXPECTED_AUC[year]
    if abs(v3_auc - expected["v3"]) > 5e-6 or abs(brown_auc - expected["brown"]) > 5e-6:
        raise RuntimeError(f"{year}: unexpected continuous ranking metrics: {v3_auc}, {brown_auc}")
    if v3_auc + 1e-15 < brown_auc:
        raise RuntimeError(f"{year}: frozen v3 no longer exceeds Brown")

    neg_v3 = np.asarray([exact_rank(getter(row, METHOD_V3)) for row in negative], dtype=np.int16)
    neg_f4 = np.asarray([exact_rank(getter(row, METHOD_FIXED4)) for row in negative], dtype=np.int16)
    pos_v3 = np.asarray([exact_rank(getter(row, METHOD_V3)) for row in positive], dtype=np.int16)
    pos_f4 = np.asarray([exact_rank(getter(row, METHOD_FIXED4)) for row in positive], dtype=np.int16)
    sectors = np.asarray([int(row["reporting_sector"]) for row in negative], dtype=np.int16)
    ks = np.asarray([int(row["k"]) for row in positive], dtype=np.int16)
    if set(np.unique(ks)) != set(KS):
        raise RuntimeError(f"{year}: positive member-count universe changed: {sorted(set(ks))}")

    return {
        "year": year,
        "v3_auc": v3_auc,
        "brown_auc": brown_auc,
        "neg_v3": neg_v3,
        "neg_f4": neg_f4,
        "pos_v3": pos_v3,
        "pos_f4": pos_f4,
        "sectors": sectors,
        "ks": ks,
        "negative_count": len(negative),
        "positive_count": len(positive),
    }


def evaluate(payload: dict[str, Any], r_primary: int, r_fixed4: int, r_corroboration: int) -> dict[str, Any]:
    neg_detected = (payload["neg_v3"] <= r_primary) | (
        (payload["neg_f4"] <= r_fixed4) & (payload["neg_v3"] <= r_corroboration)
    )
    pos_detected = (payload["pos_v3"] <= r_primary) | (
        (payload["pos_f4"] <= r_fixed4) & (payload["pos_v3"] <= r_corroboration)
    )
    pooled_fpr = float(np.mean(neg_detected))
    sector_fpr = {
        str(int(sector)): float(np.mean(neg_detected[payload["sectors"] == sector]))
        for sector in np.unique(payload["sectors"])
    }
    worst_sector_fpr = max(sector_fpr.values())
    recall = {
        str(k): float(np.mean(pos_detected[payload["ks"] == k]))
        for k in KS
    }
    reference = FROZEN_REFERENCES[payload["year"]]
    margins = {
        "4": recall["4"] - float(reference["fixed4_k4"]),
        "6": recall["6"] - (float(reference["brown_recall"]["6"]) - RECALL_TOLERANCE),
        "8": recall["8"] - (float(reference["brown_recall"]["8"]) - RECALL_TOLERANCE),
        "12": recall["12"] - (float(reference["brown_recall"]["12"]) - RECALL_TOLERANCE),
    }
    gates = {
        "v3_auc_at_least_brown": payload["v3_auc"] + 1e-15 >= payload["brown_auc"],
        "pooled_fpr_at_most_0055": pooled_fpr <= FPR_CAP + 1e-15,
        "worst_sector_fpr_at_most_008": worst_sector_fpr <= SECTOR_FPR_CAP + 1e-15,
        "k4_at_least_fixed4": margins["4"] >= -1e-15,
        "k6_within_003_of_brown": margins["6"] >= -1e-15,
        "k8_within_003_of_brown": margins["8"] >= -1e-15,
        "k12_within_003_of_brown": margins["12"] >= -1e-15,
    }
    return {
        "pooled_fpr": pooled_fpr,
        "sector_fpr": sector_fpr,
        "worst_sector_fpr": worst_sector_fpr,
        "recall": recall,
        "recall_margins": margins,
        "gates": gates,
        "feasible": all(gates.values()),
    }


def selection_key(row: dict[str, Any]) -> tuple[float, float, int, int, int, int, int, int]:
    return (
        -float(row["minimum_recall_margin"]),
        float(row["maximum_pooled_fpr"]),
        int(row["r_corroboration"]),
        -int(row["r_primary"]),
        int(row["r_fixed4"]),
        int(row["r_primary"]),
        int(row["r_fixed4"]),
        int(row["r_corroboration"]),
    )


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    payloads = {
        2025: load_year(args.year2025, 2025),
        2023: load_year(args.year2023, 2023),
        2024: load_year(args.year2024, 2024),
    }

    grid_path = args.output / "V6_COMPLETE_GRID.csv"
    feasible_rows: list[dict[str, Any]] = []
    grid_count = 0
    with grid_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        header = [
            "r_primary", "r_fixed4", "r_corroboration", "feasible",
            "minimum_recall_margin", "maximum_pooled_fpr", "maximum_worst_sector_fpr",
        ]
        for year in DEVELOPMENT_YEARS:
            header.extend([
                f"fpr_{year}", f"worst_sector_fpr_{year}",
                f"k4_{year}", f"k6_{year}", f"k8_{year}", f"k12_{year}",
            ])
        writer.writerow(header)

        for r_primary in PRIMARY_RANKS:
            for r_fixed4 in FIXED4_RANKS:
                for r_corroboration in CORROBORATION_RANKS:
                    per_year: dict[int, dict[str, Any]] = {}
                    all_margins: list[float] = []
                    feasible = True
                    maximum_pooled_fpr = 0.0
                    maximum_worst_sector_fpr = 0.0
                    for year in DEVELOPMENT_YEARS:
                        measured = evaluate(payloads[year], r_primary, r_fixed4, r_corroboration)
                        per_year[year] = measured
                        feasible = feasible and bool(measured["feasible"])
                        all_margins.extend(float(value) for value in measured["recall_margins"].values())
                        maximum_pooled_fpr = max(maximum_pooled_fpr, float(measured["pooled_fpr"]))
                        maximum_worst_sector_fpr = max(maximum_worst_sector_fpr, float(measured["worst_sector_fpr"]))
                    minimum_recall_margin = min(all_margins)
                    row = {
                        "r_primary": r_primary,
                        "r_fixed4": r_fixed4,
                        "r_corroboration": r_corroboration,
                        "feasible": bool(feasible),
                        "minimum_recall_margin": minimum_recall_margin,
                        "maximum_pooled_fpr": maximum_pooled_fpr,
                        "maximum_worst_sector_fpr": maximum_worst_sector_fpr,
                        "years": per_year,
                    }
                    if feasible:
                        feasible_rows.append(row)
                    csv_row: list[Any] = [
                        r_primary, r_fixed4, r_corroboration, int(feasible),
                        minimum_recall_margin, maximum_pooled_fpr, maximum_worst_sector_fpr,
                    ]
                    for year in DEVELOPMENT_YEARS:
                        measured = per_year[year]
                        csv_row.extend([
                            measured["pooled_fpr"], measured["worst_sector_fpr"],
                            measured["recall"]["4"], measured["recall"]["6"],
                            measured["recall"]["8"], measured["recall"]["12"],
                        ])
                    writer.writerow(csv_row)
                    grid_count += 1

    expected_grid = len(PRIMARY_RANKS) * len(FIXED4_RANKS) * len(CORROBORATION_RANKS)
    if grid_count != expected_grid or expected_grid != 69628:
        raise RuntimeError(f"grid cardinality mismatch: {grid_count}, expected {expected_grid}")

    selected = min(feasible_rows, key=selection_key) if feasible_rows else None
    verdict = "PASS_V6_CORROBORATED_RESCUE_DEVELOPMENT" if selected is not None else "FAIL_V6_CORROBORATED_RESCUE_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "configuration": {
            "development_years": list(DEVELOPMENT_YEARS),
            "denominator": DENOMINATOR,
            "primary_ranks": [min(PRIMARY_RANKS), max(PRIMARY_RANKS)],
            "fixed4_ranks": [min(FIXED4_RANKS), max(FIXED4_RANKS)],
            "corroboration_ranks": [min(CORROBORATION_RANKS), max(CORROBORATION_RANKS)],
            "grid_pairs": grid_count,
            "fpr_cap": FPR_CAP,
            "sector_fpr_cap": SECTOR_FPR_CAP,
            "recall_tolerance": RECALL_TOLERANCE,
            "rule": "(p_v3 <= r_primary/513) OR ((p_fixed4 <= r_fixed4/513) AND (p_v3 <= r_corroboration/513))",
            "selector": "maximin recall margin; minimum worst-year pooled FPR; strongest corroboration; largest primary rank; smallest fixed4 rank",
        },
        "frozen_references": FROZEN_REFERENCES,
        "continuous_auc_guard": EXPECTED_AUC,
        "feasible_pairs": len(feasible_rows),
        "selected": selected,
        "feasible_rules": feasible_rows,
        "prospective_reservation": "SonotaCo 2018; no performance access before development freeze",
    }
    (args.output / "V6_DEVELOPMENT_SELECTION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# OrbitTrace v6 corroborated-rescue development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Complete rules evaluated: **{grid_count:,}**",
        "",
        f"Feasible rules: **{len(feasible_rows)}**",
        "",
    ]
    if selected is not None:
        lines.extend([
            f"Selected ranks: **primary v3={selected['r_primary']}/513, fixed4={selected['r_fixed4']}/513, corroboration v3={selected['r_corroboration']}/513**",
            "",
            "Selected decision:",
            "",
            f"`(p_v3 <= {selected['r_primary']}/513) OR ((p_fixed4 <= {selected['r_fixed4']}/513) AND (p_v3 <= {selected['r_corroboration']}/513))`",
            "",
            f"Minimum recall margin across all 12 constraints: **{selected['minimum_recall_margin']:.6f}**",
            "",
            f"Maximum pooled FPR across development years: **{selected['maximum_pooled_fpr']:.6f}**",
            "",
        ])
        for year in DEVELOPMENT_YEARS:
            measured = selected["years"][year]
            lines.extend([
                f"## {year}",
                "",
                f"- pooled FPR: `{measured['pooled_fpr']:.6f}`; worst-sector FPR: `{measured['worst_sector_fpr']:.6f}`",
                "- recall k=4/6/8/12: " + " / ".join(f"{measured['recall'][str(k)]:.6f}" for k in KS),
                "",
            ])
    lines.extend([
        "The complete 69,628-rule grid is preserved in `V6_COMPLETE_GRID.csv`.",
        "",
        "SonotaCo 2018 remains reserved for prospective validation and was not accessed here.",
    ])
    (args.output / "V6_DEVELOPMENT_SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
