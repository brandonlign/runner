#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

import decision_v4 as decision

V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--negative", required=True, type=Path)
    parser.add_argument("--positive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def rate(flags: list[bool]) -> float:
    if not flags:
        raise RuntimeError("empty rate")
    return sum(flags) / len(flags)


def main() -> None:
    args = parse_args()
    payload = json.loads(args.result.read_text())
    negative = load_rows(args.negative)
    positive = load_rows(args.positive)
    metrics = payload["metrics"]
    for method in (V3, FIXED4, WAVELET):
        if method not in metrics:
            raise RuntimeError(f"missing method {method}")

    if not all(decision.self_test().values()):
        raise RuntimeError("frozen v4 decision self-test failed")

    def detected(row: dict[str, Any]) -> bool:
        return decision.detected(row["p"][V3], row["p"][FIXED4])

    fpr = rate([detected(row) for row in negative])
    sectors = sorted({int(row["reporting_sector"]) for row in negative})
    sector_fpr = {
        str(sector): rate([detected(row) for row in negative if int(row["reporting_sector"]) == sector])
        for sector in sectors
    }
    recall = {
        str(k): rate([detected(row) for row in positive if int(row["k"]) == k])
        for k in (4, 6, 8, 12)
    }
    fixed4_recall = metrics[FIXED4]["recall"]["0.05"]
    wavelet_recall = metrics[WAVELET]["recall"]["0.05"]
    v3_auc = float(metrics[V3]["weak_auc"])
    wavelet_auc = float(metrics[WAVELET]["weak_auc"])

    gates = {
        "v3_auc_above_wavelet": v3_auc > wavelet_auc,
        "v4_k4_at_least_fixed4": float(recall["4"]) >= float(fixed4_recall["4"]),
        "v4_k6_within_003_of_wavelet": float(recall["6"]) >= float(wavelet_recall["6"]) - 0.03,
        "v4_k8_within_003_of_wavelet": float(recall["8"]) >= float(wavelet_recall["8"]) - 0.03,
        "v4_k12_within_003_of_wavelet": float(recall["12"]) >= float(wavelet_recall["12"]) - 0.03,
        "v4_fpr_at_most_0055": fpr <= 0.055,
        "v4_worst_sector_fpr_at_most_008": max(sector_fpr.values()) <= 0.08,
        "upstream_transfer_integrity": all(bool(value) for value in payload["gates"].values()),
        "decision_thresholds_exact": (
            decision.V3_MAX_RANK == 3
            and decision.FIXED4_MAX_RANK == 4
            and decision.CALIBRATION_DENOMINATOR == 129
        ),
    }
    verdict = "PASS_V4_SONOTACO_2023_TRANSFER" if all(gates.values()) else "FAIL_V4_SONOTACO_2023_TRANSFER"
    result = {
        "verdict": verdict,
        "year": 2023,
        "ranking": {
            "v3_weak_auc": v3_auc,
            "wavelet_weak_auc": wavelet_auc,
            "fixed4_weak_auc": float(metrics[FIXED4]["weak_auc"]),
        },
        "decision": {
            "v3_threshold_rank": decision.V3_MAX_RANK,
            "fixed4_threshold_rank": decision.FIXED4_MAX_RANK,
            "denominator": decision.CALIBRATION_DENOMINATOR,
            "fpr": fpr,
            "worst_sector_fpr": max(sector_fpr.values()),
            "sector_fpr": sector_fpr,
            "recall": recall,
        },
        "references": {
            "fixed4_recall_005": fixed4_recall,
            "wavelet_recall_005": wavelet_recall,
        },
        "gates": gates,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V4_SONOTACO_2023_TRANSFER.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# OrbitTrace v4 SonotaCo 2023 unchanged transfer",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"v3 AUROC: **{v3_auc:.6f}** vs Brown **{wavelet_auc:.6f}**",
        "",
        f"v4 pooled FPR: **{fpr:.6f}**; worst-sector FPR: **{max(sector_fpr.values()):.6f}**",
        "",
        "v4 recall k=4/6/8/12: **" + " / ".join(f"{recall[str(k)]:.6f}" for k in (4, 6, 8, 12)) + "**",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    (args.output / "V4_SONOTACO_2023_TRANSFER.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
