#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

METHOD = "orbittrace_multiscale_consensus_v2"
WAVELET = "brown2010_wavelet_episode_core"
FIXED4 = "orbittrace_fixed4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text())
    metrics = payload["metrics"]
    candidate = metrics[METHOD]
    wavelet = metrics[WAVELET]
    fixed4 = metrics[FIXED4]

    recall_c = candidate["recall"]["0.05"]
    recall_w = wavelet["recall"]["0.05"]
    recall_f = fixed4["recall"]["0.05"]

    primary_gates = {
        "weak_auc_above_wavelet": float(candidate["weak_auc"]) > float(wavelet["weak_auc"]),
        "k4_recall_at_least_fixed4": float(recall_c["4"]) >= float(recall_f["4"]),
        "k6_within_003_of_wavelet": float(recall_c["6"]) >= float(recall_w["6"]) - 0.03,
        "k8_within_003_of_wavelet": float(recall_c["8"]) >= float(recall_w["8"]) - 0.03,
        "k12_within_003_of_wavelet": float(recall_c["12"]) >= float(recall_w["12"]) - 0.03,
        "fpr_005_at_most_0055": float(candidate["fpr"]["0.05"]) <= 0.055,
        "worst_sector_fpr_005_at_most_008": float(candidate["worst_sector_fpr_005"]) <= 0.08,
        "upstream_benchmark_integrity": all(bool(value) for value in payload["gates"].values()),
    }
    primary_pass = all(primary_gates.values())
    ranking_survives = (
        primary_gates["weak_auc_above_wavelet"]
        and primary_gates["k6_within_003_of_wavelet"]
        and primary_gates["k8_within_003_of_wavelet"]
        and primary_gates["k12_within_003_of_wavelet"]
        and primary_gates["fpr_005_at_most_0055"]
        and primary_gates["worst_sector_fpr_005_at_most_008"]
        and primary_gates["upstream_benchmark_integrity"]
    )
    if primary_pass:
        verdict = "PASS_MULTISCALE_CONSENSUS_V2_PRIMARY_DEVELOPMENT"
    elif ranking_survives and not primary_gates["k4_recall_at_least_fixed4"]:
        verdict = "RETAIN_MULTISCALE_CONSENSUS_V2_RANKING_FOR_FIXED4_RESCUE_TEST"
    else:
        verdict = "FAIL_MULTISCALE_CONSENSUS_V2_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "method": METHOD,
        "primary_gates": primary_gates,
        "comparison": {
            "candidate_weak_auc": candidate["weak_auc"],
            "wavelet_weak_auc": wavelet["weak_auc"],
            "fixed4_weak_auc": fixed4["weak_auc"],
            "candidate_fpr_005": candidate["fpr"]["0.05"],
            "candidate_worst_sector_fpr_005": candidate["worst_sector_fpr_005"],
            "candidate_recall_005": recall_c,
            "wavelet_recall_005": recall_w,
            "fixed4_recall_005": recall_f,
        },
        "next_stage": (
            "freeze primary and design prospective transfer"
            if primary_pass
            else "evaluate inherited minimum-p fixed4 rescue without changing ranking"
            if ranking_survives
            else "preserve failure; material successor must be v3"
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V2_DEVELOPMENT_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace multiscale consensus v2 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "| Method | Weak AUROC | FPR .05 | Worst-sector FPR .05 |",
        "|---|---:|---:|---:|",
        f"| multiscale consensus v2 | {candidate['weak_auc']:.6f} | {candidate['fpr']['0.05']:.6f} | {candidate['worst_sector_fpr_005']:.6f} |",
        f"| Brown-family wavelet | {wavelet['weak_auc']:.6f} | {wavelet['fpr']['0.05']:.6f} | {wavelet['worst_sector_fpr_005']:.6f} |",
        f"| fixed4 | {fixed4['weak_auc']:.6f} | {fixed4['fpr']['0.05']:.6f} | {fixed4['worst_sector_fpr_005']:.6f} |",
        "",
        "## Alpha=.05 recall",
        "",
        "- v2 k=4/6/8/12: " + " / ".join(f"{float(recall_c[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "- wavelet k=4/6/8/12: " + " / ".join(f"{float(recall_w[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "- fixed4 k=4/6/8/12: " + " / ".join(f"{float(recall_f[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in primary_gates.items())
    (args.output / "V2_DEVELOPMENT_RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
