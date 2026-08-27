#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"
DENOMINATOR = 129
PRIMARY_RANKS = (2, 3, 4, 5, 6)
SPARSE_RANKS = (2, 3, 4, 5, 6)
CORROBORATION_RANKS = (10, 15, 20, 25, 30, 35, 40)
FPR_DEVELOPMENT_CAP = 0.052
SECTOR_FPR_DEVELOPMENT_CAP = 0.075
RECALL_TOLERANCE = 0.03
K_VALUES = (4, 6, 8, 12)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-dir", required=True, type=Path)
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


def empirical_rank(p_value: float) -> int:
    scaled = float(p_value) * DENOMINATOR
    rank = int(round(scaled))
    if not math.isclose(scaled, rank, abs_tol=1e-10, rel_tol=0.0):
        raise ValueError(f"p-value not on denominator-{DENOMINATOR} grid: {p_value}")
    return rank


def detected(row: dict[str, Any], a: int, b: int, c: int) -> bool:
    v3_rank = empirical_rank(row["p"][V3])
    fixed4_rank = empirical_rank(row["p"][FIXED4])
    return v3_rank <= a or (fixed4_rank <= b and v3_rank <= c)


def evaluate(
    negatives: list[dict[str, Any]],
    positives: list[dict[str, Any]],
    a: int,
    b: int,
    c: int,
) -> dict[str, Any]:
    neg_hits = [detected(row, a, b, c) for row in negatives]
    fpr = sum(neg_hits) / len(neg_hits)

    sectors: dict[int, list[bool]] = defaultdict(list)
    for row, hit in zip(negatives, neg_hits):
        sectors[int(row["reporting_sector"])].append(hit)
    sector_fpr = {
        str(sector): sum(hits) / len(hits)
        for sector, hits in sorted(sectors.items())
    }
    worst_sector = max(sector_fpr.values())

    recall: dict[str, float] = {}
    for k in K_VALUES:
        rows = [row for row in positives if int(row["k"]) == k]
        recall[str(k)] = sum(detected(row, a, b, c) for row in rows) / len(rows)

    return {
        "a": a,
        "b": b,
        "c": c,
        "primary_threshold": a / DENOMINATOR,
        "sparse_threshold": b / DENOMINATOR,
        "corroboration_threshold": c / DENOMINATOR,
        "pooled_fpr": fpr,
        "sector_fpr": sector_fpr,
        "worst_sector_fpr": worst_sector,
        "recall": recall,
    }


def main() -> None:
    args = parse_args()
    artifact = args.artifact_dir
    payload = json.loads((artifact / "sonotaco_2025_literature_comparison.json").read_text())
    negatives = load_jsonl_gz(artifact / "negative_literature_records.jsonl.gz")
    positives = load_jsonl_gz(artifact / "positive_literature_records.jsonl.gz")

    metrics = payload["metrics"]
    fixed4 = metrics[FIXED4]
    wavelet = metrics[WAVELET]
    v3 = metrics[V3]
    thresholds = {
        "4": float(fixed4["recall"]["0.05"]["4"]),
        "6": float(wavelet["recall"]["0.05"]["6"]) - RECALL_TOLERANCE,
        "8": float(wavelet["recall"]["0.05"]["8"]) - RECALL_TOLERANCE,
        "12": float(wavelet["recall"]["0.05"]["12"]) - RECALL_TOLERANCE,
    }

    rows: list[dict[str, Any]] = []
    for a in PRIMARY_RANKS:
        for b in SPARSE_RANKS:
            for c in CORROBORATION_RANKS:
                if c <= a:
                    continue
                row = evaluate(negatives, positives, a, b, c)
                margins = {
                    k: float(row["recall"][k]) - thresholds[k]
                    for k in ("4", "6", "8", "12")
                }
                row["recall_margins"] = margins
                row["total_recall_slack"] = sum(max(0.0, value) for value in margins.values())
                row["feasible"] = (
                    row["pooled_fpr"] <= FPR_DEVELOPMENT_CAP
                    and row["worst_sector_fpr"] <= SECTOR_FPR_DEVELOPMENT_CAP
                    and all(value >= -1e-12 for value in margins.values())
                )
                rows.append(row)

    feasible = [row for row in rows if row["feasible"]]
    selected = None
    if feasible:
        selected = sorted(
            feasible,
            key=lambda r: (
                -float(r["total_recall_slack"]),
                float(r["pooled_fpr"]),
                float(r["worst_sector_fpr"]),
                int(r["a"]) + int(r["b"]) + int(r["c"]),
                int(r["a"]),
                int(r["b"]),
                int(r["c"]),
            ),
        )[0]

    upstream_ok = all(bool(value) for value in payload["gates"].values())
    grid_ok = all(
        empirical_rank(row["p"][method]) >= 1
        for row in negatives + positives
        for method in (V3, FIXED4)
    )
    gates = {
        "upstream_benchmark_integrity": upstream_ok,
        "p_values_on_129_grid": grid_ok,
        "continuous_v3_auc_above_brown": float(v3["weak_auc"]) > float(wavelet["weak_auc"]),
        "complete_candidate_grid": len(rows) == len(PRIMARY_RANKS) * len(SPARSE_RANKS) * len(CORROBORATION_RANKS),
        "at_least_one_feasible_candidate": selected is not None,
    }
    verdict = "PASS_V5_DEVELOPMENT_SELECTION" if all(gates.values()) else "FAIL_V5_DEVELOPMENT_SELECTION"

    result = {
        "verdict": verdict,
        "method": "orbittrace_corroborated_sparse_rescue_v5",
        "selection_corpus": "SonotaCo 2025 development only",
        "post_2023_development": True,
        "configuration": {
            "denominator": DENOMINATOR,
            "primary_ranks": PRIMARY_RANKS,
            "sparse_ranks": SPARSE_RANKS,
            "corroboration_ranks": CORROBORATION_RANKS,
            "pooled_fpr_development_cap": FPR_DEVELOPMENT_CAP,
            "sector_fpr_development_cap": SECTOR_FPR_DEVELOPMENT_CAP,
            "recall_tolerance": RECALL_TOLERANCE,
            "rule": "p_v3 <= a/129 OR (p_fixed4 <= b/129 AND p_v3 <= c/129)",
            "selection_order": [
                "largest total recall slack",
                "lower pooled FPR",
                "lower worst-sector FPR",
                "smaller a+b+c",
                "smaller a",
                "smaller b",
                "smaller c",
            ],
        },
        "reference_thresholds": thresholds,
        "ranking": {
            "v3_weak_auc": float(v3["weak_auc"]),
            "brown_weak_auc": float(wavelet["weak_auc"]),
        },
        "candidate_count": len(rows),
        "feasible_count": len(feasible),
        "selected": selected,
        "gates": gates,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V5_DEVELOPMENT_SELECTION.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "V5_CANDIDATE_GRID.json").write_text(json.dumps(rows, indent=2) + "\n")

    lines = [
        "# OrbitTrace corroborated sparse rescue v5 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Candidates evaluated: **{len(rows)}**",
        f"Feasible candidates: **{len(feasible)}**",
        "",
    ]
    if selected is not None:
        lines += [
            f"Selected ranks: **a={selected['a']}/129, b={selected['b']}/129, c={selected['c']}/129**",
            "",
            f"Pooled FPR: **{selected['pooled_fpr']:.6f}**",
            f"Worst-sector FPR: **{selected['worst_sector_fpr']:.6f}**",
            "",
            "Recall k=4/6/8/12: **"
            + " / ".join(f"{selected['recall'][str(k)]:.6f}" for k in K_VALUES)
            + "**",
            "",
            f"Total recall slack: **{selected['total_recall_slack']:.6f}**",
            "",
        ]
    lines += ["## Gates", ""]
    lines.extend(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    lines += [
        "",
        "SonotaCo 2023 was not used by this selector. Because its v4 result was already observed, any later 2023 v5 application is retrospective rather than untouched validation.",
    ]
    (args.output / "V5_DEVELOPMENT_SELECTION.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
