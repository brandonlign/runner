#!/usr/bin/env python3
"""Develop a conservative persistence/mean-strength rank fusion from frozen families."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

WEIGHTS = (0.0, 0.01, 0.015, 0.02, 0.025)
PANELS = ("development", "validation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def ranking(panel: dict[str, Any], weight: float) -> list[str]:
    persistence = panel["rankings"]["persistence"]
    strength = panel["rankings"]["mean_year_strength"]
    if set(persistence) != set(strength):
        raise RuntimeError("ranking family universes differ")
    n = len(persistence)
    persistence_rank = {family_id: index for index, family_id in enumerate(persistence, start=1)}
    strength_rank = {family_id: index for index, family_id in enumerate(strength, start=1)}
    return sorted(
        persistence,
        key=lambda family_id: (
            (1.0 - weight) * persistence_rank[family_id] / n
            + weight * strength_rank[family_id] / n,
            persistence_rank[family_id],
            strength_rank[family_id],
            family_id,
        ),
    )


def invariant_matches(panel: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = panel["evaluation"]["metrics"]
    baseline = metrics["persistence"]["per_label"]
    baseline_map = {row["label"]: row.get("family_id") for row in baseline}
    for variant, result in metrics.items():
        comparison = {row["label"]: row.get("family_id") for row in result["per_label"]}
        if comparison != baseline_map:
            raise RuntimeError(f"best-match families differ under {variant}")
    return baseline


def evaluate(panel: dict[str, Any], order: list[str]) -> dict[str, Any]:
    rank = {family_id: index for index, family_id in enumerate(order, start=1)}
    per_label = invariant_matches(panel)
    qualified: list[int] = []
    for row in per_label:
        family_id = row.get("family_id")
        if bool(row.get("qualified")) and family_id in rank:
            qualified.append(rank[family_id])
    if not qualified:
        raise RuntimeError("no qualified known-shower matches")
    return {
        "eligible_labels": len(per_label),
        "qualified_matches": len(qualified),
        "recovered_at_100": sum(value <= 100 for value in qualified),
        "recovered_at_500": sum(value <= 500 for value in qualified),
        "mrr": float(np.mean([1.0 / value for value in qualified])),
        "median_rank": float(np.median(qualified)),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if payload.get("verdict") != "FAIL_SUPPORT_NORMALIZED_WRAPPER_DEVELOPMENT":
        raise RuntimeError("unexpected source artifact verdict")
    if payload["development"]["selected_variant"] != "mean_year_strength":
        raise RuntimeError("unexpected source strength variant")
    panels = payload["panel_results"]
    if tuple(panels["development"]["years"]) != (2022, 2023):
        raise RuntimeError("development years changed")
    if tuple(panels["validation"]["years"]) != (2024, 2025):
        raise RuntimeError("validation years changed")

    candidates: dict[str, Any] = {}
    for weight in WEIGHTS:
        key = f"{weight:.3f}"
        candidates[key] = {}
        for panel_name in PANELS:
            panel = panels[panel_name]
            fused = evaluate(panel, ranking(panel, weight))
            persistence = evaluate(panel, panel["rankings"]["persistence"])
            fused["delta_over_persistence"] = {
                "recovered_at_100": fused["recovered_at_100"] - persistence["recovered_at_100"],
                "recovered_at_500": fused["recovered_at_500"] - persistence["recovered_at_500"],
                "mrr": fused["mrr"] - persistence["mrr"],
            }
            fused["persistence"] = persistence
            candidates[key][panel_name] = fused

    selection_rows = []
    for weight in WEIGHTS:
        key = f"{weight:.3f}"
        metrics = candidates[key]
        recall_deltas = [metrics[panel]["delta_over_persistence"]["recovered_at_100"] for panel in PANELS]
        mrr_deltas = [metrics[panel]["delta_over_persistence"]["mrr"] for panel in PANELS]
        selection_rows.append({
            "weight": weight,
            "minimum_recall100_delta": min(recall_deltas),
            "total_recall100": sum(metrics[panel]["recovered_at_100"] for panel in PANELS),
            "minimum_mrr_delta": min(mrr_deltas),
            "mean_mrr_delta": float(np.mean(mrr_deltas)),
        })

    selected = max(
        selection_rows,
        key=lambda row: (
            row["minimum_recall100_delta"],
            row["total_recall100"],
            row["minimum_mrr_delta"],
            row["mean_mrr_delta"],
            -row["weight"],
        ),
    )
    selected_key = f"{selected['weight']:.3f}"
    selected_metrics = candidates[selected_key]
    gates = {
        "selected_weight_nonzero": selected["weight"] > 0.0,
        "recall100_non_decline_both_panels": all(
            selected_metrics[panel]["delta_over_persistence"]["recovered_at_100"] >= 0
            for panel in PANELS
        ),
        "at_least_one_recall100_gain": any(
            selected_metrics[panel]["delta_over_persistence"]["recovered_at_100"] >= 1
            for panel in PANELS
        ),
        "recall500_non_decline_both_panels": all(
            selected_metrics[panel]["delta_over_persistence"]["recovered_at_500"] >= 0
            for panel in PANELS
        ),
        "mrr_strictly_improves_both_panels": all(
            selected_metrics[panel]["delta_over_persistence"]["mrr"] > 0.0
            for panel in PANELS
        ),
    }
    verdict = (
        "PASS_PERSISTENCE_ANCHORED_RANK_FUSION_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_PERSISTENCE_ANCHORED_RANK_FUSION_DEVELOPMENT"
    )
    result = {
        "verdict": verdict,
        "method_id": "fixed4_persistence_anchored_rank_fusion",
        "formula": "(1-w)*normalized_persistence_rank + w*normalized_mean_year_strength_rank",
        "candidate_weights": list(WEIGHTS),
        "selected_weight": selected["weight"],
        "selection_summary": selected,
        "candidates": candidates,
        "gates": gates,
        "development_panels": {"development": [2022, 2023], "validation": [2024, 2025]},
        "prospective_years_reserved": [2019, 2020, 2021],
        "source_artifact": {
            "id": 8971289223,
            "sha256": "01a7158ee5cf79e212689b3eb24438bbf98f959dc3588141f073412b1a9c5999",
        },
        "claim_boundary": (
            "A pass freezes one rank-fusion weight and authorizes only a target-excluded prospective "
            "2019-2021 catalogue validation. It does not authorize OrbitTrace access."
        ),
    }
    (args.output / "fixed4_persistence_rank_fusion_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Fixed4 persistence-anchored rank-fusion development",
        "",
        f"Verdict: `{verdict}`",
        f"Selected weight: **{selected['weight']:.3f}**",
        "",
        "| weight | minimum recall@100 delta | total recall@100 | minimum MRR delta | mean MRR delta |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in selection_rows:
        lines.append(
            f"| {row['weight']:.3f} | {row['minimum_recall100_delta']:+d} | "
            f"{row['total_recall100']} | {row['minimum_mrr_delta']:+.8f} | "
            f"{row['mean_mrr_delta']:+.8f} |"
        )
    lines.extend(["", "## Selected candidate", ""])
    for panel in PANELS:
        metric = selected_metrics[panel]
        delta = metric["delta_over_persistence"]
        lines.append(
            f"- {panel}: recall@100 {metric['recovered_at_100']} "
            f"({delta['recovered_at_100']:+d}), recall@500 {metric['recovered_at_500']} "
            f"({delta['recovered_at_500']:+d}), MRR {metric['mrr']:.8f} "
            f"({delta['mrr']:+.8f})."
        )
    (args.output / "FIXED4_PERSISTENCE_RANK_FUSION_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
