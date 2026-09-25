#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"
DENOMINATOR = 129
RANKS = tuple(range(1, 7))
FPR_CAP = 0.055
RECALL_TOLERANCE = 0.03


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def rate(values: list[bool]) -> float:
    if not values:
        raise RuntimeError("empty rate input")
    return sum(bool(value) for value in values) / len(values)


def main() -> None:
    args = parse_args()
    metrics_payload = json.loads((args.artifact_dir / "sonotaco_2025_literature_comparison.json").read_text())
    negative = load_jsonl_gz(args.artifact_dir / "negative_literature_records.jsonl.gz")
    positive = load_jsonl_gz(args.artifact_dir / "positive_literature_records.jsonl.gz")

    if len(negative) != 2048 or len(positive) != 544:
        raise RuntimeError(f"unexpected v3 record counts: {len(negative)} / {len(positive)}")
    if not all(method in metrics_payload["metrics"] for method in (V3, FIXED4, WAVELET)):
        raise RuntimeError("required frozen methods missing")

    fixed4_recall = metrics_payload["metrics"][FIXED4]["recall"]["0.05"]
    wavelet_recall = metrics_payload["metrics"][WAVELET]["recall"]["0.05"]
    required = {
        "4": float(fixed4_recall["4"]),
        "6": float(wavelet_recall["6"]) - RECALL_TOLERANCE,
        "8": float(wavelet_recall["8"]) - RECALL_TOLERANCE,
        "12": float(wavelet_recall["12"]) - RECALL_TOLERANCE,
    }

    table: list[dict[str, Any]] = []
    for m_v3 in RANKS:
        for m_f4 in RANKS:
            threshold_v3 = m_v3 / DENOMINATOR
            threshold_f4 = m_f4 / DENOMINATOR

            def detected(row: dict[str, Any]) -> bool:
                return (
                    float(row["p"][V3]) <= threshold_v3
                    or float(row["p"][FIXED4]) <= threshold_f4
                )

            fpr = rate([detected(row) for row in negative])
            recall = {
                str(k): rate([detected(row) for row in positive if int(row["k"]) == k])
                for k in (4, 6, 8, 12)
            }
            margins = {k: float(recall[k]) - required[k] for k in required}
            feasible = (
                fpr <= FPR_CAP
                and all(margin >= -1e-15 for margin in margins.values())
            )
            table.append({
                "m_v3": m_v3,
                "m_fixed4": m_f4,
                "threshold_v3": threshold_v3,
                "threshold_fixed4": threshold_f4,
                "fpr": fpr,
                "recall": recall,
                "required_recall": required,
                "recall_margin": margins,
                "minimum_recall_margin": min(margins.values()),
                "feasible": feasible,
            })

    feasible = [row for row in table if row["feasible"]]
    selected = None
    if feasible:
        selected = min(
            feasible,
            key=lambda row: (
                float(row["fpr"]),
                -float(row["recall"]["4"]),
                -float(row["minimum_recall_margin"]),
                int(row["m_v3"]) + int(row["m_fixed4"]),
                int(row["m_v3"]),
            ),
        )

    verdict = "PASS_V4_DEVELOPMENT_SELECTION" if selected is not None else "FAIL_V4_DEVELOPMENT_SELECTION"
    result = {
        "verdict": verdict,
        "source_v3_run": 31146579074,
        "source_v3_artifact": 8981702758,
        "denominator": DENOMINATOR,
        "candidate_ranks": list(RANKS),
        "fpr_cap": FPR_CAP,
        "recall_tolerance": RECALL_TOLERANCE,
        "required_recall": required,
        "selection_rule": [
            "feasible pairs only",
            "lowest pooled FPR",
            "higher k4 recall",
            "higher minimum recall margin",
            "smaller total rank budget",
            "smaller v3 rank",
        ],
        "selected": selected,
        "complete_grid": table,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V4_DEVELOPMENT_SELECTION.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace v4 FPR-budgeted decision development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Feasible pairs: **{len(feasible)}/36**",
        "",
    ]
    if selected is not None:
        lines.extend([
            f"Selected ranks: **v3={selected['m_v3']}/129, fixed4={selected['m_fixed4']}/129**",
            "",
            f"Pooled FPR: **{selected['fpr']:.6f}**",
            "",
            "Recall k=4/6/8/12: **"
            + " / ".join(f"{float(selected['recall'][str(k)]):.6f}" for k in (4, 6, 8, 12))
            + "**",
            "",
        ])
    lines.extend([
        "| v3 rank | fixed4 rank | FPR | k4 | k6 | k8 | k12 | feasible |",
        "|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ])
    for row in table:
        lines.append(
            f"| {row['m_v3']} | {row['m_fixed4']} | {row['fpr']:.6f} | "
            f"{row['recall']['4']:.6f} | {row['recall']['6']:.6f} | "
            f"{row['recall']['8']:.6f} | {row['recall']['12']:.6f} | "
            f"{'yes' if row['feasible'] else 'no'} |"
        )
    (args.output / "V4_DEVELOPMENT_SELECTION.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))
    if selected is None:
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
