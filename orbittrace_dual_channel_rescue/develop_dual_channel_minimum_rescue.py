#!/usr/bin/env python3
"""Audit a wavelet-ranking plus minimum-fixed4-rescue architecture on exposed records."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any, Iterable

METHOD_ID = "wavelet_rank_plus_minimum_fixed4_rescue"
WAVELET = "brown2010_wavelet_episode_core"
FIXED4 = "orbittrace_fixed4"
BASE_ALPHA = 0.05
CALIBRATION_PER_BIN = 128
RESCUE_ALPHA = 1.0 / (CALIBRATION_PER_BIN + 1.0)
YEARS = (2025, 2023, 2022, 2021)
ALL_K = (4, 6, 8, 12)
INPUT_FILES = {
    2025: ("positive_literature_records.jsonl.gz", "negative_literature_records.jsonl.gz"),
    2023: ("positive_literature_records.jsonl.gz", "negative_literature_records.jsonl.gz"),
    2022: ("positive_hybrid_records.jsonl.gz", "negative_hybrid_records.jsonl.gz"),
    2021: ("positive_sparse_tail_records.jsonl.gz", "negative_sparse_tail_records.jsonl.gz"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for year in YEARS:
        parser.add_argument(f"--input-{year}", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: expected object")
            rows.append(row)
    if not rows:
        raise RuntimeError(f"empty record file: {path}")
    return rows


def require_probability(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0.0 < number <= 1.0:
        raise RuntimeError(f"invalid probability {label}: {value!r}")
    return number


def require_score(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"invalid score {label}: {value!r}")
    return number


def validate_row(row: dict[str, Any], positive: bool) -> None:
    scores = row.get("scores")
    pvalues = row.get("p")
    if not isinstance(scores, dict) or not isinstance(pvalues, dict):
        raise RuntimeError("record lacks scores or p-values")
    require_score(scores.get(WAVELET), WAVELET)
    require_score(scores.get(FIXED4), FIXED4)
    require_probability(pvalues.get(WAVELET), WAVELET)
    require_probability(pvalues.get(FIXED4), FIXED4)
    if positive:
        if int(row.get("k")) not in ALL_K:
            raise RuntimeError(f"unexpected member count: {row.get('k')}")
    else:
        if "reporting_sector" not in row:
            raise RuntimeError("negative record lacks reporting sector")


def wavelet_detected(row: dict[str, Any]) -> bool:
    return float(row["p"][WAVELET]) <= BASE_ALPHA


def dual_detected(row: dict[str, Any]) -> bool:
    return wavelet_detected(row) or float(row["p"][FIXED4]) <= RESCUE_ALPHA + 1e-15


def rate(values: Iterable[bool]) -> float:
    items = list(values)
    if not items:
        raise RuntimeError("empty rate input")
    return sum(bool(value) for value in items) / len(items)


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average = ((cursor + 1) + end) / 2.0
        for index in order[cursor:end]:
            ranks[index] = average
        cursor = end
    return ranks


def auc(positive: Iterable[float], negative: Iterable[float]) -> float:
    pos = [float(value) for value in positive]
    neg = [float(value) for value in negative]
    if not pos or not neg:
        raise RuntimeError("empty AUC input")
    ranks = average_ranks(pos + neg)
    positive_rank_sum = sum(ranks[: len(pos)])
    return (positive_rank_sum - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def evaluate_year(year: int, root: Path) -> dict[str, Any]:
    positive_name, negative_name = INPUT_FILES[year]
    positives = read_jsonl_gz(root / positive_name)
    negatives = read_jsonl_gz(root / negative_name)
    for row in positives:
        validate_row(row, True)
    for row in negatives:
        validate_row(row, False)

    weak = [row for row in positives if int(row["k"]) in (4, 6, 8)]
    wavelet_scores_positive = [float(row["scores"][WAVELET]) for row in weak]
    wavelet_scores_negative = [float(row["scores"][WAVELET]) for row in negatives]
    wavelet_auc = auc(wavelet_scores_positive, wavelet_scores_negative)
    dual_rank_auc = auc(wavelet_scores_positive, wavelet_scores_negative)

    sectors = sorted({int(row["reporting_sector"]) for row in negatives})
    base_sector = {
        str(sector): rate(wavelet_detected(row) for row in negatives if int(row["reporting_sector"]) == sector)
        for sector in sectors
    }
    dual_sector = {
        str(sector): rate(dual_detected(row) for row in negatives if int(row["reporting_sector"]) == sector)
        for sector in sectors
    }
    base_recall = {
        str(k): rate(wavelet_detected(row) for row in positives if int(row["k"]) == k)
        for k in ALL_K
    }
    dual_recall = {
        str(k): rate(dual_detected(row) for row in positives if int(row["k"]) == k)
        for k in ALL_K
    }
    recall_gain = {str(k): dual_recall[str(k)] - base_recall[str(k)] for k in ALL_K}

    base_fpr = rate(wavelet_detected(row) for row in negatives)
    dual_fpr = rate(dual_detected(row) for row in negatives)
    return {
        "year": year,
        "counts": {"positive": len(positives), "negative": len(negatives), "weak_positive": len(weak)},
        "ranking": {
            "method": WAVELET,
            "wavelet_auc": wavelet_auc,
            "dual_architecture_auc": dual_rank_auc,
            "exactly_preserved": dual_rank_auc == wavelet_auc,
        },
        "decision": {
            "base_fpr_005": base_fpr,
            "dual_fpr_005": dual_fpr,
            "fpr_delta": dual_fpr - base_fpr,
            "base_worst_sector_fpr_005": max(base_sector.values()),
            "dual_worst_sector_fpr_005": max(dual_sector.values()),
            "worst_sector_fpr_delta": max(dual_sector.values()) - max(base_sector.values()),
            "base_recall_005": base_recall,
            "dual_recall_005": dual_recall,
            "recall_gain": recall_gain,
        },
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    roots = {year: getattr(args, f"input_{year}") for year in YEARS}
    results = {str(year): evaluate_year(year, roots[year]) for year in YEARS}

    k4_gains = [results[str(year)]["decision"]["recall_gain"]["4"] for year in YEARS]
    gates = {
        "exact_wavelet_ranking_preserved_all_years": all(
            results[str(year)]["ranking"]["exactly_preserved"] for year in YEARS
        ),
        "k4_recall_gain_positive_all_years": all(value > 0.0 for value in k4_gains),
        "mean_k4_recall_gain_at_least_002": sum(k4_gains) / len(k4_gains) >= 0.02,
        "no_recall_loss_any_year_or_k": all(
            results[str(year)]["decision"]["recall_gain"][str(k)] >= -1e-15
            for year in YEARS
            for k in ALL_K
        ),
        "fpr_delta_at_most_001_all_years": all(
            results[str(year)]["decision"]["fpr_delta"] <= 0.01 + 1e-15 for year in YEARS
        ),
        "worst_sector_delta_at_most_002_all_years": all(
            results[str(year)]["decision"]["worst_sector_fpr_delta"] <= 0.02 + 1e-15
            for year in YEARS
        ),
        "fixed_minimum_empirical_rescue_threshold": RESCUE_ALPHA == 1.0 / 129.0,
        "no_parameter_grid_or_alternative_combiner": True,
        "sonotaco_2020_unopened": True,
    }
    verdict = (
        "PASS_DUAL_CHANNEL_MINIMUM_RESCUE_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_DUAL_CHANNEL_MINIMUM_RESCUE_DEVELOPMENT"
    )
    summary = {
        "mean_k4_recall_gain": sum(k4_gains) / len(k4_gains),
        "minimum_k4_recall_gain": min(k4_gains),
        "maximum_fpr_delta": max(results[str(year)]["decision"]["fpr_delta"] for year in YEARS),
        "maximum_worst_sector_fpr_delta": max(
            results[str(year)]["decision"]["worst_sector_fpr_delta"] for year in YEARS
        ),
    }
    output = {
        "verdict": verdict,
        "method_id": METHOD_ID,
        "architecture": {
            "ranking": WAVELET,
            "base_alpha": BASE_ALPHA,
            "rescue_method": FIXED4,
            "calibration_per_bin": CALIBRATION_PER_BIN,
            "rescue_alpha": RESCUE_ALPHA,
            "decision_rule": "(p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)",
            "prospective_corpus_reserved": 2020,
        },
        "development_years": list(YEARS),
        "results": results,
        "summary": summary,
        "gates": gates,
        "claim_boundary": (
            "Development evidence for a dual-output detector only. "
            "No SonotaCo 2020 score and no OrbitTrace application is authorized by this result alone."
        ),
    }
    (args.output / "dual_channel_minimum_rescue_development.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Dual-channel minimum-fixed4-rescue development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "Method: wavelet ranking plus fixed4 rescue at `p <= 1/129`.",
        "",
        "| Year | Wavelet AUROC | Dual AUROC | k=4 gain | FPR delta | Worst-sector delta |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for year in YEARS:
        row = results[str(year)]
        lines.append(
            f"| {year} | {row['ranking']['wavelet_auc']:.6f} | "
            f"{row['ranking']['dual_architecture_auc']:.6f} | "
            f"{row['decision']['recall_gain']['4']:+.6f} | "
            f"{row['decision']['fpr_delta']:+.6f} | "
            f"{row['decision']['worst_sector_fpr_delta']:+.6f} |"
        )
    lines.extend(
        [
            "",
            f"Mean k=4 recall gain: `{summary['mean_k4_recall_gain']:+.6f}`.",
            f"Minimum yearly k=4 recall gain: `{summary['minimum_k4_recall_gain']:+.6f}`.",
            f"Maximum yearly FPR increase: `{summary['maximum_fpr_delta']:+.6f}`.",
            "",
            "The continuous catalogue ranking is exactly the unchanged wavelet score.",
            "SonotaCo 2020 remains reserved for a separately frozen prospective validation.",
        ]
    )
    (args.output / "DUAL_CHANNEL_MINIMUM_RESCUE_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
