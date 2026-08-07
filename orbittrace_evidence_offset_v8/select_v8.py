#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import evidence_offset_v8 as v8

BROWN = "brown2010_wavelet_episode_core"
FIXED4 = "orbittrace_fixed4"
V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
EXPECTED_V3_AUC = {2025: 0.836860, 2023: 0.836263}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--result-2025", required=True, type=Path)
    p.add_argument("--result-2023", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def close(a: float, b: float, tol: float = 5e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> None:
    args = parse_args()
    payloads = {
        2025: json.loads(args.result_2025.read_text()),
        2023: json.loads(args.result_2023.read_text()),
    }

    candidate_rows = []
    for order_index, method in enumerate(v8.METHODS):
        offset = float(v8.METHOD_TO_OFFSET[method])
        annual = {}
        auc_margins = []
        k4_margins = []
        minimum_gate_recall_margins = []
        feasible_years = []
        for year, payload in payloads.items():
            metrics = payload["metrics"]
            candidate = metrics[method]
            brown = metrics[BROWN]
            fixed4 = metrics[FIXED4]
            v3 = metrics[V3]
            rc = candidate["recall"]["0.05"]
            rb = brown["recall"]["0.05"]
            rf = fixed4["recall"]["0.05"]
            gate_thresholds = {
                "4": float(rf["4"]),
                "6": float(rb["6"]) - 0.03,
                "8": float(rb["8"]) - 0.03,
                "12": float(rb["12"]) - 0.03,
            }
            recall_margins = {k: float(rc[k]) - gate_thresholds[k] for k in gate_thresholds}
            auc_margin = float(candidate["weak_auc"]) - float(brown["weak_auc"])
            k4_margin = float(rc["4"]) - float(rf["4"])
            gates = {
                "auc_above_brown": auc_margin > 0.0,
                "k4_at_least_fixed4": k4_margin >= -1e-15,
                "k6_within_003_brown": recall_margins["6"] >= -1e-15,
                "k8_within_003_brown": recall_margins["8"] >= -1e-15,
                "k12_within_003_brown": recall_margins["12"] >= -1e-15,
                "fpr_at_most_0055": float(candidate["fpr"]["0.05"]) <= 0.055,
                "worst_sector_at_most_008": float(candidate["worst_sector_fpr_005"]) <= 0.08,
                "v3_auc_reproduced": close(v3["weak_auc"], EXPECTED_V3_AUC[year]),
                "upstream_integrity": all(bool(value) for value in payload["gates"].values()),
            }
            feasible = all(gates.values())
            feasible_years.append(feasible)
            auc_margins.append(auc_margin)
            k4_margins.append(k4_margin)
            minimum_gate_recall_margins.append(min(recall_margins.values()))
            annual[str(year)] = {
                "weak_auc": candidate["weak_auc"],
                "brown_auc": brown["weak_auc"],
                "auc_margin": auc_margin,
                "fpr_005": candidate["fpr"]["0.05"],
                "worst_sector_fpr_005": candidate["worst_sector_fpr_005"],
                "recall_005": rc,
                "fixed4_recall_005": rf,
                "brown_recall_005": rb,
                "recall_gate_margin": recall_margins,
                "gates": gates,
                "feasible": feasible,
            }
        candidate_rows.append({
            "method": method,
            "offset": offset,
            "method_order": order_index,
            "feasible_both_years": all(feasible_years),
            "minimum_auc_margin": min(auc_margins),
            "mean_auc_margin": sum(auc_margins) / len(auc_margins),
            "minimum_k4_margin": min(k4_margins),
            "minimum_recall_gate_margin": min(minimum_gate_recall_margins),
            "annual": annual,
        })

    feasible = [row for row in candidate_rows if row["feasible_both_years"]]
    selected = None
    if feasible:
        selected = min(
            feasible,
            key=lambda row: (
                -float(row["minimum_auc_margin"]),
                -float(row["mean_auc_margin"]),
                -float(row["minimum_k4_margin"]),
                -float(row["minimum_recall_gate_margin"]),
                abs(float(row["offset"])),
                int(row["method_order"]),
            ),
        )

    verdict = "PASS_EVIDENCE_OFFSET_V8_DEVELOPMENT" if selected else "FAIL_EVIDENCE_OFFSET_V8_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "candidate_offsets": list(v8.OFFSETS),
        "candidate_methods": list(v8.METHODS),
        "selector": [
            "feasible in both 2025 and 2023",
            "largest minimum annual AUROC margin over Brown",
            "largest mean annual AUROC margin over Brown",
            "largest minimum annual k4 recall margin over fixed4",
            "largest minimum annual recall margin relative to all k gates",
            "smallest absolute offset",
            "fixed offset order",
        ],
        "selected": selected,
        "candidates": candidate_rows,
        "prospective_year_if_pass": 2016,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V8_SELECTION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace v8 calibrated evidence-offset selection",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Feasible candidates: **{len(feasible)}/{len(candidate_rows)}**",
        "",
    ]
    if selected:
        lines += [
            f"Selected: **`{selected['method']}`**, offset **{selected['offset']:+.2f}**",
            "",
            f"Minimum annual AUROC margin over Brown: **{selected['minimum_auc_margin']:+.6f}**",
            "",
            f"Minimum annual k4 margin over fixed4: **{selected['minimum_k4_margin']:+.6f}**",
            "",
        ]
    lines += [
        "| offset | both feasible | min ΔAUROC | mean ΔAUROC | min Δk4 | 2025 AUROC | 2025 k4 | 2023 AUROC | 2023 k4 |",
        "|---:|:---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in candidate_rows:
        y25 = row["annual"]["2025"]
        y23 = row["annual"]["2023"]
        lines.append(
            f"| {row['offset']:+.2f} | {'yes' if row['feasible_both_years'] else 'no'} | "
            f"{row['minimum_auc_margin']:+.6f} | {row['mean_auc_margin']:+.6f} | {row['minimum_k4_margin']:+.6f} | "
            f"{y25['weak_auc']:.6f} | {float(y25['recall_005']['4']):.6f} | "
            f"{y23['weak_auc']:.6f} | {float(y23['recall_005']['4']):.6f} |"
        )
    (args.output / "V8_SELECTION_RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
