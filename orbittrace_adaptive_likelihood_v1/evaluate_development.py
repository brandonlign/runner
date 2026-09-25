#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

METHOD = "orbittrace_adaptive_local_likelihood_v1"
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
    adaptive = metrics[METHOD]
    wavelet = metrics[WAVELET]
    fixed4 = metrics[FIXED4]

    recall_a = adaptive["recall"]["0.05"]
    recall_w = wavelet["recall"]["0.05"]
    recall_f = fixed4["recall"]["0.05"]

    gates = {
        "weak_auc_above_wavelet": float(adaptive["weak_auc"]) > float(wavelet["weak_auc"]),
        "k4_recall_at_least_fixed4": float(recall_a["4"]) >= float(recall_f["4"]),
        "k6_within_003_of_wavelet": float(recall_a["6"]) >= float(recall_w["6"]) - 0.03,
        "k8_within_003_of_wavelet": float(recall_a["8"]) >= float(recall_w["8"]) - 0.03,
        "k12_within_003_of_wavelet": float(recall_a["12"]) >= float(recall_w["12"]) - 0.03,
        "fpr_005_at_most_0055": float(adaptive["fpr"]["0.05"]) <= 0.055,
        "worst_sector_fpr_005_at_most_008": float(adaptive["worst_sector_fpr_005"]) <= 0.08,
        "upstream_benchmark_integrity": all(bool(value) for value in payload["gates"].values()),
    }
    verdict = (
        "PASS_ADAPTIVE_LOCAL_LIKELIHOOD_V1_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_ADAPTIVE_LOCAL_LIKELIHOOD_V1_DEVELOPMENT"
    )
    result = {
        "verdict": verdict,
        "method": METHOD,
        "comparison": {
            "adaptive_weak_auc": adaptive["weak_auc"],
            "wavelet_weak_auc": wavelet["weak_auc"],
            "fixed4_weak_auc": fixed4["weak_auc"],
            "adaptive_fpr_005": adaptive["fpr"]["0.05"],
            "adaptive_worst_sector_fpr_005": adaptive["worst_sector_fpr_005"],
            "adaptive_recall_005": recall_a,
            "wavelet_recall_005": recall_w,
            "fixed4_recall_005": recall_f,
        },
        "gates": gates,
        "interpretation": (
            "A pass authorizes source freezing and separately controlled transfer; "
            "a failure is preserved and does not authorize silent same-result tuning."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "DEVELOPMENT_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace adaptive local-likelihood v1 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "| Method | Weak AUROC | FPR .05 | Worst-sector FPR .05 |",
        "|---|---:|---:|---:|",
        f"| adaptive v1 | {adaptive['weak_auc']:.6f} | {adaptive['fpr']['0.05']:.6f} | {adaptive['worst_sector_fpr_005']:.6f} |",
        f"| Brown-family wavelet | {wavelet['weak_auc']:.6f} | {wavelet['fpr']['0.05']:.6f} | {wavelet['worst_sector_fpr_005']:.6f} |",
        f"| fixed4 | {fixed4['weak_auc']:.6f} | {fixed4['fpr']['0.05']:.6f} | {fixed4['worst_sector_fpr_005']:.6f} |",
        "",
        "## Alpha=.05 recall",
        "",
        "- adaptive k=4/6/8/12: " + " / ".join(f"{float(recall_a[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "- wavelet k=4/6/8/12: " + " / ".join(f"{float(recall_w[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "- fixed4 k=4/6/8/12: " + " / ".join(f"{float(recall_f[str(k)]):.6f}" for k in (4, 6, 8, 12)),
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    (args.output / "DEVELOPMENT_RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
