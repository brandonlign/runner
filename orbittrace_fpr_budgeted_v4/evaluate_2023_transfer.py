#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import decision_v4 as decision

V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"
EXPECTED_NEGATIVES = 33 * 64
EXPECTED_POSITIVES_PER_K = 41 * 4
K_VALUES = (4, 6, 8, 12)
FPR_CAP = 0.055
SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--negative-records", required=True, type=Path)
    parser.add_argument("--positive-records", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def p_on_grid(value: float) -> bool:
    scaled = float(value) * decision.CALIBRATION_DENOMINATOR
    return math.isclose(scaled, round(scaled), abs_tol=1e-10, rel_tol=0.0)


def detected(row: dict[str, Any]) -> bool:
    return decision.detected(row["p"][V3], row["p"][FIXED4])


def main() -> None:
    args = parse_args()
    payload = json.loads(args.benchmark.read_text())
    negatives = load_jsonl_gz(args.negative_records)
    positives = load_jsonl_gz(args.positive_records)

    metrics = payload["metrics"]
    v3 = metrics[V3]
    fixed4 = metrics[FIXED4]
    wavelet = metrics[WAVELET]

    negative_hits = [detected(row) for row in negatives]
    combined_fpr = sum(negative_hits) / len(negative_hits)

    sector_hits: dict[int, list[bool]] = defaultdict(list)
    for row, hit in zip(negatives, negative_hits):
        sector_hits[int(row["reporting_sector"])].append(hit)
    sector_fpr = {
        str(sector): sum(hits) / len(hits)
        for sector, hits in sorted(sector_hits.items())
    }
    worst_sector_fpr = max(sector_fpr.values())

    recall: dict[str, float] = {}
    positive_counts: dict[str, int] = {}
    for k in K_VALUES:
        rows = [row for row in positives if int(row["k"]) == k]
        positive_counts[str(k)] = len(rows)
        recall[str(k)] = sum(detected(row) for row in rows) / len(rows)

    all_grid_values = [
        float(row["p"][method])
        for row in negatives + positives
        for method in (V3, FIXED4)
    ]

    reference = {
        "fixed4_k4": float(fixed4["recall"]["0.05"]["4"]),
        "wavelet_k6": float(wavelet["recall"]["0.05"]["6"]),
        "wavelet_k8": float(wavelet["recall"]["0.05"]["8"]),
        "wavelet_k12": float(wavelet["recall"]["0.05"]["12"]),
    }

    gates = {
        "year_exact_2023": int(payload["configuration"]["year"]) == 2023,
        "calibration_exact_128": int(payload["configuration"]["calibration_per_bin"]) == 128,
        "frozen_decision_self_test": all(decision.self_test().values()),
        "frozen_thresholds_exact": (
            decision.V3_MAX_RANK == 3
            and decision.FIXED4_MAX_RANK == 4
            and decision.CALIBRATION_DENOMINATOR == 129
        ),
        "upstream_benchmark_integrity": all(bool(value) for value in payload["gates"].values()),
        "negative_records_exact": len(negatives) == EXPECTED_NEGATIVES,
        "positive_counts_exact": all(positive_counts[str(k)] == EXPECTED_POSITIVES_PER_K for k in K_VALUES),
        "empirical_p_values_on_129_grid": all(p_on_grid(value) for value in all_grid_values),
        "v3_auc_at_least_brown": float(v3["weak_auc"]) >= float(wavelet["weak_auc"]),
        "combined_fpr_at_most_0055": combined_fpr <= FPR_CAP,
        "worst_sector_fpr_at_most_008": worst_sector_fpr <= SECTOR_FPR_CAP,
        "k4_recall_at_least_fixed4": recall["4"] >= reference["fixed4_k4"],
        "k6_within_003_of_wavelet": recall["6"] >= reference["wavelet_k6"] - RECALL_TOLERANCE,
        "k8_within_003_of_wavelet": recall["8"] >= reference["wavelet_k8"] - RECALL_TOLERANCE,
        "k12_within_003_of_wavelet": recall["12"] >= reference["wavelet_k12"] - RECALL_TOLERANCE,
    }
    verdict = "PASS_V4_SONOTACO_2023_TRANSFER" if all(gates.values()) else "FAIL_V4_SONOTACO_2023_TRANSFER"

    result = {
        "verdict": verdict,
        "status": "unchanged transfer of frozen v3 ranking and frozen v4 decision thresholds to SonotaCo 2023",
        "configuration": {
            "v3_method": V3,
            "fixed4_method": FIXED4,
            "v3_max_rank": decision.V3_MAX_RANK,
            "fixed4_max_rank": decision.FIXED4_MAX_RANK,
            "calibration_denominator": decision.CALIBRATION_DENOMINATOR,
            "v3_threshold": decision.V3_THRESHOLD,
            "fixed4_threshold": decision.FIXED4_THRESHOLD,
            "rule": "p_v3 <= 3/129 OR p_fixed4 <= 4/129",
            "threshold_reselection": False,
        },
        "ranking": {
            "v3_weak_auc": float(v3["weak_auc"]),
            "brown_weak_auc": float(wavelet["weak_auc"]),
            "fixed4_weak_auc": float(fixed4["weak_auc"]),
            "v3_fold_auc": v3["fold_auc"],
        },
        "decision": {
            "pooled_fpr": combined_fpr,
            "worst_sector_fpr": worst_sector_fpr,
            "sector_fpr": sector_fpr,
            "recall": recall,
            "positive_counts": positive_counts,
            "negative_count": len(negatives),
        },
        "references": reference,
        "gates": gates,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V4_SONOTACO_2023_TRANSFER.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace v4 SonotaCo 2023 unchanged transfer",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "Frozen decision: **v3 <= 3/129 OR fixed4 <= 4/129**",
        "",
        "| Quantity | v4 transfer | Reference |",
        "|---|---:|---:|",
        f"| v3 weak AUROC | {float(v3['weak_auc']):.6f} | Brown {float(wavelet['weak_auc']):.6f} |",
        f"| pooled FPR | {combined_fpr:.6f} | cap {FPR_CAP:.3f} |",
        f"| worst-sector FPR | {worst_sector_fpr:.6f} | cap {SECTOR_FPR_CAP:.2f} |",
        f"| k=4 recall | {recall['4']:.6f} | fixed4 {reference['fixed4_k4']:.6f} |",
        f"| k=6 recall | {recall['6']:.6f} | Brown {reference['wavelet_k6']:.6f} |",
        f"| k=8 recall | {recall['8']:.6f} | Brown {reference['wavelet_k8']:.6f} |",
        f"| k=12 recall | {recall['12']:.6f} | Brown {reference['wavelet_k12']:.6f} |",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    lines += [
        "",
        "Thresholds were frozen on SonotaCo 2025 and were not reselected from 2023 results.",
    ]
    (args.output / "V4_SONOTACO_2023_TRANSFER.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
