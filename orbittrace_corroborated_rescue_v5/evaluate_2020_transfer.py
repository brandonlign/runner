#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import decision_v5 as decision

V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"
K_VALUES = (4, 6, 8, 12)
EXPECTED_CALIBRATION = 4224
EXPECTED_NEGATIVES = 2112
EXPECTED_POSITIVES = 576
EXPECTED_POSITIVES_PER_K = 144
FPR_CAP = 0.055
SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", required=True, type=Path)
    p.add_argument("--negative-records", required=True, type=Path)
    p.add_argument("--positive-records", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


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
    pooled_fpr = sum(negative_hits) / len(negative_hits)

    sectors: dict[int, list[bool]] = defaultdict(list)
    for row, hit in zip(negatives, negative_hits):
        sectors[int(row["reporting_sector"])].append(hit)
    sector_fpr = {
        str(sector): sum(hits) / len(hits)
        for sector, hits in sorted(sectors.items())
    }
    worst_sector_fpr = max(sector_fpr.values())

    recall: dict[str, float] = {}
    positive_counts: dict[str, int] = {}
    for k in K_VALUES:
        rows = [row for row in positives if int(row["k"]) == k]
        positive_counts[str(k)] = len(rows)
        recall[str(k)] = sum(detected(row) for row in rows) / len(rows)

    references = {
        "fixed4_k4": float(fixed4["recall_005"]["4"]),
        "wavelet_k6": float(wavelet["recall_005"]["6"]),
        "wavelet_k8": float(wavelet["recall_005"]["8"]),
        "wavelet_k12": float(wavelet["recall_005"]["12"]),
    }

    all_p_values = [
        float(row["p"][method])
        for row in negatives + positives
        for method in (V3, FIXED4)
    ]

    original_execution = payload["execution_gates"]
    gates = {
        "post_selection_status_explicit": True,
        "year_exact_2020": int(payload["configuration"]["year"]) == 2020,
        "calibration_exact_128": int(payload["configuration"]["calibration_per_bin"]) == 128,
        "episode_counts_exact": (
            EXPECTED_CALIBRATION == 4224
            and len(negatives) == EXPECTED_NEGATIVES
            and len(positives) == EXPECTED_POSITIVES
            and all(positive_counts[str(k)] == EXPECTED_POSITIVES_PER_K for k in K_VALUES)
        ),
        "original_2020_runner_integrity": all(bool(value) for value in original_execution.values()),
        "v3_metric_present": V3 in metrics,
        "frozen_v5_self_test": all(decision.self_test().values()),
        "frozen_v5_ranks_exact": (
            decision.CALIBRATION_DENOMINATOR == 129
            and decision.V3_PRIMARY_MAX_RANK == 4
            and decision.FIXED4_SPARSE_MAX_RANK == 3
            and decision.V3_CORROBORATION_MAX_RANK == 40
        ),
        "p_values_on_129_grid": all(p_on_grid(value) for value in all_p_values),
        "v3_auc_at_least_brown": float(v3["weak_auc"]) >= float(wavelet["weak_auc"]),
        "pooled_fpr_at_most_0055": pooled_fpr <= FPR_CAP,
        "worst_sector_fpr_at_most_008": worst_sector_fpr <= SECTOR_FPR_CAP,
        "k4_recall_at_least_fixed4": recall["4"] >= references["fixed4_k4"],
        "k6_within_003_of_wavelet": recall["6"] >= references["wavelet_k6"] - RECALL_TOLERANCE,
        "k8_within_003_of_wavelet": recall["8"] >= references["wavelet_k8"] - RECALL_TOLERANCE,
        "k12_within_003_of_wavelet": recall["12"] >= references["wavelet_k12"] - RECALL_TOLERANCE,
    }
    verdict = "PASS_V5_SONOTACO_2020_POST_SELECTION_TRANSFER" if all(gates.values()) else "FAIL_V5_SONOTACO_2020_POST_SELECTION_TRANSFER"

    result = {
        "verdict": verdict,
        "evidence_class": "independent post-selection year-level transfer on a previously scored SonotaCo 2020 benchmark; 2020 was not used in v5 architecture or selection",
        "configuration": {
            "rule": "p_v3 <= 4/129 OR (p_fixed4 <= 3/129 AND p_v3 <= 40/129)",
            "threshold_reselection": False,
            "continuous_ranking": V3,
            "calibration_denominator": 129,
        },
        "ranking": {
            "v3_weak_auc": float(v3["weak_auc"]),
            "brown_weak_auc": float(wavelet["weak_auc"]),
            "fixed4_weak_auc": float(fixed4["weak_auc"]),
            "v3_fold_auc": v3["fold_auc"],
        },
        "decision": {
            "pooled_fpr": pooled_fpr,
            "worst_sector_fpr": worst_sector_fpr,
            "sector_fpr": sector_fpr,
            "recall": recall,
            "negative_count": len(negatives),
            "positive_count": len(positives),
            "positive_counts": positive_counts,
        },
        "references": references,
        "upstream_execution_gates": original_execution,
        "gates": gates,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V5_SONOTACO_2020_TRANSFER.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace v5 — SonotaCo 2020 post-selection transfer",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "Evidence class: **independent post-selection year-level transfer on a previously scored 2020 benchmark; not an untouched archive claim**",
        "",
        "Frozen rule: **v3 <= 4/129 OR (fixed4 <= 3/129 AND v3 <= 40/129)**",
        "",
        "| Quantity | v5 transfer | Reference |",
        "|---|---:|---:|",
        f"| v3 weak AUROC | {float(v3['weak_auc']):.6f} | Brown {float(wavelet['weak_auc']):.6f} |",
        f"| pooled FPR | {pooled_fpr:.6f} | cap {FPR_CAP:.3f} |",
        f"| worst-sector FPR | {worst_sector_fpr:.6f} | cap {SECTOR_FPR_CAP:.2f} |",
        f"| k=4 recall | {recall['4']:.6f} | fixed4 {references['fixed4_k4']:.6f} |",
        f"| k=6 recall | {recall['6']:.6f} | Brown {references['wavelet_k6']:.6f} |",
        f"| k=8 recall | {recall['8']:.6f} | Brown {references['wavelet_k8']:.6f} |",
        f"| k=12 recall | {recall['12']:.6f} | Brown {references['wavelet_k12']:.6f} |",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    lines += [
        "",
        "SonotaCo 2020 was not used to design or select v5. Its older Brown/fixed4 benchmark outcomes were public within the project, so this is a post-selection transfer rather than a pristine untouched-corpus claim.",
    ]
    (args.output / "V5_SONOTACO_2020_TRANSFER.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
