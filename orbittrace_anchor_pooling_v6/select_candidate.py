#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import anchor_pooling_v6 as v6

BROWN = "brown2010_wavelet_episode_core"
FIXED4 = "orbittrace_fixed4"
EXPECTED_V3_AUC = {2025: 0.836860, 2023: 0.836263}
EXPECTED_BROWN_AUC = {2025: 0.828506, 2023: 0.831972}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-2025", required=True, type=Path)
    parser.add_argument("--result-2023", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def close(value: float, expected: float, tolerance: float = 5e-6) -> bool:
    return abs(float(value) - float(expected)) <= tolerance


def main() -> None:
    args = parse_args()
    payloads = {
        2025: json.loads(args.result_2025.read_text()),
        2023: json.loads(args.result_2023.read_text()),
    }

    integrity = {}
    for year, payload in payloads.items():
        metrics = payload["metrics"]
        integrity[str(year)] = {
            "upstream_gates": all(bool(value) for value in payload["gates"].values()),
            "v3_auc_reproduced": close(metrics["orbittrace_multi_anchor_wavelet_energy_v3"]["weak_auc"], EXPECTED_V3_AUC[year]),
            "brown_auc_reproduced": close(metrics[BROWN]["weak_auc"], EXPECTED_BROWN_AUC[year]),
            "candidate_set_exact": all(method in metrics for method in v6.METHOD_ORDER),
        }

    candidates = []
    for order_index, method in enumerate(v6.METHOD_ORDER):
        annual = {}
        annual_feasible = []
        auc_margins = []
        k4_margins = []
        for year, payload in payloads.items():
            metrics = payload["metrics"]
            candidate = metrics[method]
            brown = metrics[BROWN]
            fixed4 = metrics[FIXED4]
            recall_c = candidate["recall"]["0.05"]
            recall_b = brown["recall"]["0.05"]
            recall_f = fixed4["recall"]["0.05"]
            gates = {
                "auc_above_brown": float(candidate["weak_auc"]) > float(brown["weak_auc"]),
                "k4_at_least_fixed4": float(recall_c["4"]) >= float(recall_f["4"]),
                "k6_within_003_brown": float(recall_c["6"]) >= float(recall_b["6"]) - 0.03,
                "k8_within_003_brown": float(recall_c["8"]) >= float(recall_b["8"]) - 0.03,
                "k12_within_003_brown": float(recall_c["12"]) >= float(recall_b["12"]) - 0.03,
                "fpr_at_most_0055": float(candidate["fpr"]["0.05"]) <= 0.055,
                "worst_sector_at_most_008": float(candidate["worst_sector_fpr_005"]) <= 0.08,
                "year_integrity": all(integrity[str(year)].values()),
            }
            auc_margin = float(candidate["weak_auc"]) - float(brown["weak_auc"])
            k4_margin = float(recall_c["4"]) - float(recall_f["4"])
            auc_margins.append(auc_margin)
            k4_margins.append(k4_margin)
            annual_feasible.append(all(gates.values()))
            annual[str(year)] = {
                "weak_auc": candidate["weak_auc"],
                "brown_auc": brown["weak_auc"],
                "auc_margin": auc_margin,
                "fpr_005": candidate["fpr"]["0.05"],
                "worst_sector_fpr_005": candidate["worst_sector_fpr_005"],
                "recall_005": recall_c,
                "fixed4_recall_005": recall_f,
                "brown_recall_005": recall_b,
                "k4_margin": k4_margin,
                "gates": gates,
            }
        candidates.append({
            "method": method,
            "method_order": order_index,
            "feasible_both_years": all(annual_feasible),
            "minimum_auc_margin": min(auc_margins),
            "mean_auc_margin": sum(auc_margins) / len(auc_margins),
            "minimum_k4_margin": min(k4_margins),
            "mean_k4_margin": sum(k4_margins) / len(k4_margins),
            "annual": annual,
        })

    feasible = [row for row in candidates if row["feasible_both_years"]]
    selected = None
    if feasible:
        selected = min(
            feasible,
            key=lambda row: (
                -float(row["minimum_auc_margin"]),
                -float(row["mean_auc_margin"]),
                -float(row["minimum_k4_margin"]),
                -float(row["mean_k4_margin"]),
                int(row["method_order"]),
            ),
        )

    verdict = "PASS_ANCHOR_POOLING_V6_DEVELOPMENT" if selected is not None else "FAIL_ANCHOR_POOLING_V6_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "candidate_order": list(v6.METHOD_ORDER),
        "integrity": integrity,
        "selector": [
            "feasible in both 2025 and 2023",
            "largest minimum annual AUROC margin over Brown",
            "largest mean annual AUROC margin over Brown",
            "largest minimum annual k4 recall margin over fixed4",
            "largest mean annual k4 recall margin over fixed4",
            "fixed candidate order",
        ],
        "selected": selected,
        "candidates": candidates,
        "prospective_year_if_pass": 2016,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V6_SELECTION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace top-four anchor pooling v6 selection",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Feasible candidates: **{len(feasible)}/{len(candidates)}**",
        "",
    ]
    if selected:
        lines.extend([
            f"Selected: **`{selected['method']}`**",
            "",
            f"Minimum annual AUROC margin over Brown: **{selected['minimum_auc_margin']:+.6f}**",
            "",
            f"Minimum annual k4 margin over fixed4: **{selected['minimum_k4_margin']:+.6f}**",
            "",
        ])
    lines.extend([
        "| Candidate | Both years feasible | min ΔAUROC | mean ΔAUROC | min Δk4 | 2025 AUROC | 2023 AUROC |",
        "|---|:---:|---:|---:|---:|---:|---:|",
    ])
    for row in candidates:
        lines.append(
            f"| `{row['method']}` | {'yes' if row['feasible_both_years'] else 'no'} | "
            f"{row['minimum_auc_margin']:+.6f} | {row['mean_auc_margin']:+.6f} | "
            f"{row['minimum_k4_margin']:+.6f} | "
            f"{row['annual']['2025']['weak_auc']:.6f} | {row['annual']['2023']['weak_auc']:.6f} |"
        )
    (args.output / "V6_SELECTION_RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
