#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

JOINT = "orbittrace_joint_tippett_v5"
V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text())
    metrics = payload["metrics"]
    for method in (JOINT, V3, FIXED4, WAVELET):
        if method not in metrics:
            raise RuntimeError(f"missing method {method}")

    joint = metrics[JOINT]
    v3 = metrics[V3]
    fixed4 = metrics[FIXED4]
    wavelet = metrics[WAVELET]
    recall_j = joint["recall"]["0.05"]
    recall_f = fixed4["recall"]["0.05"]
    recall_w = wavelet["recall"]["0.05"]

    gates = {
        "v3_auc_above_wavelet": float(v3["weak_auc"]) > float(wavelet["weak_auc"]),
        "joint_k4_at_least_fixed4": float(recall_j["4"]) >= float(recall_f["4"]),
        "joint_k6_within_003_of_wavelet": float(recall_j["6"]) >= float(recall_w["6"]) - 0.03,
        "joint_k8_within_003_of_wavelet": float(recall_j["8"]) >= float(recall_w["8"]) - 0.03,
        "joint_k12_within_003_of_wavelet": float(recall_j["12"]) >= float(recall_w["12"]) - 0.03,
        "joint_fpr_005_at_most_0055": float(joint["fpr"]["0.05"]) <= 0.055,
        "joint_worst_sector_fpr_005_at_most_008": float(joint["worst_sector_fpr_005"]) <= 0.08,
        "upstream_integrity": all(bool(value) for value in payload["gates"].values()),
    }
    verdict = f"PASS_V5_{args.year}_DEVELOPMENT" if all(gates.values()) else f"FAIL_V5_{args.year}_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "year": args.year,
        "continuous_ranking": V3,
        "reporting_layer": JOINT,
        "metrics": {
            "v3_weak_auc": v3["weak_auc"],
            "wavelet_weak_auc": wavelet["weak_auc"],
            "fixed4_weak_auc": fixed4["weak_auc"],
            "joint_statistic_weak_auc_diagnostic": joint["weak_auc"],
            "joint_fpr_005": joint["fpr"]["0.05"],
            "joint_worst_sector_fpr_005": joint["worst_sector_fpr_005"],
            "joint_recall_005": recall_j,
            "fixed4_recall_005": recall_f,
            "wavelet_recall_005": recall_w,
        },
        "gates": gates,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"V5_{args.year}_DEVELOPMENT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        f"# OrbitTrace jointly calibrated Tippett v5 — {args.year}",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Frozen v3 AUROC: **{float(v3['weak_auc']):.6f}** vs Brown **{float(wavelet['weak_auc']):.6f}**",
        "",
        f"Joint reporting FPR .05: **{float(joint['fpr']['0.05']):.6f}**; worst sector: **{float(joint['worst_sector_fpr_005']):.6f}**",
        "",
        "Joint recall k=4/6/8/12: **" + " / ".join(f"{float(recall_j[str(k)]):.6f}" for k in (4,6,8,12)) + "**",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    (args.output / f"V5_{args.year}_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
