#!/usr/bin/env python3
"""Select one wavelet-primary fixed4 sparse-tail margin on exposed record artifacts."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.metrics import roc_auc_score

MARGINS = (0.0, 0.25, 0.5, 0.75, 1.0)
WEAK_K = (4, 6, 8)
ALL_K = (4, 6, 8, 12)
FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-2025", required=True, type=Path)
    parser.add_argument("--input-2023", required=True, type=Path)
    parser.add_argument("--input-2022", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid JSON at {path}:{line_number}") from exc
            rows.append(row)
    if not rows:
        raise RuntimeError(f"empty record file: {path}")
    return rows


def unique_file(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {filename} under {root}, found {matches}")
    return matches[0]


def load_corpus(root: Path, year: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if year in (2025, 2023):
        positive_name = "positive_literature_records.jsonl.gz"
        negative_name = "negative_literature_records.jsonl.gz"
    elif year == 2022:
        positive_name = "positive_hybrid_records.jsonl.gz"
        negative_name = "negative_hybrid_records.jsonl.gz"
    else:
        raise ValueError(f"unsupported development year: {year}")
    positive = read_jsonl_gz(unique_file(root, positive_name))
    negative = read_jsonl_gz(unique_file(root, negative_name))
    for record in positive + negative:
        pvalues = record.get("p", {})
        for method in (FIXED4, WAVELET):
            value = float(pvalues.get(method, math.nan))
            if not (0.0 < value <= 1.0 and math.isfinite(value)):
                raise RuntimeError(f"invalid {method} p-value in {year}: {value}")
    return positive, negative


def evidence(record: dict[str, Any], method: str) -> float:
    return -math.log(float(record["p"][method]))


def wavelet_score(record: dict[str, Any]) -> float:
    return evidence(record, WAVELET)


def augmented_score(record: dict[str, Any], margin: float) -> float:
    return max(evidence(record, WAVELET), evidence(record, FIXED4) - margin)


def empirical_threshold(scores: np.ndarray, alpha: float = 0.05) -> float:
    if scores.ndim != 1 or not len(scores) or not np.all(np.isfinite(scores)):
        raise RuntimeError("invalid negative score vector")
    return float(np.quantile(scores, 1.0 - alpha, method="higher"))


def evaluate(
    positive: list[dict[str, Any]],
    negative: list[dict[str, Any]],
    score_function: Callable[[dict[str, Any]], float],
) -> dict[str, Any]:
    weak_positive = [record for record in positive if int(record["k"]) in WEAK_K]
    if not weak_positive:
        raise RuntimeError("no weak positive episodes")
    positive_scores = np.asarray([score_function(record) for record in weak_positive], dtype=np.float64)
    negative_scores = np.asarray([score_function(record) for record in negative], dtype=np.float64)
    labels = np.concatenate((np.ones(len(positive_scores)), np.zeros(len(negative_scores))))
    scores = np.concatenate((positive_scores, negative_scores))
    auc = float(roc_auc_score(labels, scores))
    threshold = empirical_threshold(negative_scores, 0.05)
    recall: dict[str, float] = {}
    for k in ALL_K:
        subset = [record for record in positive if int(record["k"]) == k]
        if not subset:
            raise RuntimeError(f"missing k={k} positives")
        values = np.asarray([score_function(record) for record in subset], dtype=np.float64)
        recall[str(k)] = float(np.mean(values >= threshold))
    return {
        "weak_auc": auc,
        "empirical_alpha_005_threshold": threshold,
        "recall_005": recall,
        "positive_records": len(positive),
        "negative_records": len(negative),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    roots = {2025: args.input_2025, 2023: args.input_2023, 2022: args.input_2022}
    corpora = {year: load_corpus(root, year) for year, root in roots.items()}

    baselines: dict[str, Any] = {}
    candidates: dict[str, Any] = {}
    for year, (positive, negative) in corpora.items():
        baselines[str(year)] = evaluate(positive, negative, wavelet_score)

    for margin in MARGINS:
        key = f"{margin:.2f}"
        candidates[key] = {}
        for year, (positive, negative) in corpora.items():
            metric = evaluate(
                positive,
                negative,
                lambda record, selected_margin=margin: augmented_score(record, selected_margin),
            )
            baseline = baselines[str(year)]
            metric["auc_delta_over_wavelet"] = metric["weak_auc"] - baseline["weak_auc"]
            metric["recall_delta_over_wavelet"] = {
                k: metric["recall_005"][k] - baseline["recall_005"][k]
                for k in map(str, ALL_K)
            }
            candidates[key][str(year)] = metric

    selection_rows: list[dict[str, Any]] = []
    for margin in MARGINS:
        key = f"{margin:.2f}"
        year_metrics = candidates[key]
        auc_deltas = [float(year_metrics[str(year)]["auc_delta_over_wavelet"]) for year in roots]
        k4_deltas = [float(year_metrics[str(year)]["recall_delta_over_wavelet"]["4"]) for year in roots]
        selection_rows.append(
            {
                "margin": margin,
                "minimum_auc_delta": min(auc_deltas),
                "mean_auc_delta": float(np.mean(auc_deltas)),
                "mean_k4_recall_delta": float(np.mean(k4_deltas)),
            }
        )

    selected = max(
        selection_rows,
        key=lambda row: (
            row["minimum_auc_delta"],
            row["mean_auc_delta"],
            row["mean_k4_recall_delta"],
            -row["margin"],
        ),
    )
    selected_key = f"{selected['margin']:.2f}"
    selected_metrics = candidates[selected_key]
    mean_recall_delta = {
        k: float(np.mean([
            selected_metrics[str(year)]["recall_delta_over_wavelet"][k]
            for year in roots
        ]))
        for k in map(str, ALL_K)
    }

    gates = {
        "selected_from_exact_frozen_grid": selected["margin"] in MARGINS,
        "auc_improves_in_every_corpus": all(
            selected_metrics[str(year)]["auc_delta_over_wavelet"] > 0.0 for year in roots
        ),
        "mean_k4_recall_improves": mean_recall_delta["4"] > 0.0,
        "mean_k6_recall_decline_within_002": mean_recall_delta["6"] >= -0.02,
        "mean_k8_recall_decline_within_002": mean_recall_delta["8"] >= -0.02,
    }
    verdict = (
        "PASS_SPARSE_TAIL_AUGMENTATION_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_SPARSE_TAIL_AUGMENTATION_DEVELOPMENT"
    )

    source_path = Path(__file__)
    result = {
        "verdict": verdict,
        "method_id": "wavelet_primary_fixed4_margin_augmentation",
        "score": "max(-log(p_wavelet), -log(p_fixed4) - margin)",
        "candidate_margins": list(MARGINS),
        "selected_margin": selected["margin"],
        "selection_summary": selected,
        "wavelet_baselines": baselines,
        "candidate_metrics": candidates,
        "selected_mean_recall_delta": mean_recall_delta,
        "gates": gates,
        "development_corpora": [2025, 2023, 2022],
        "prospective_corpus_reserved": 2021,
        "source_sha256": sha256(source_path),
        "claim_boundary": (
            "Development on already exposed record artifacts only; a pass authorizes one separately frozen "
            "calibrated SonotaCo 2021 prospective validation and no OrbitTrace application."
        ),
    }
    result_path = args.output / "sparse_tail_augmentation_development.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = []
    for row in sorted(selection_rows, key=lambda value: value["margin"]):
        rows.append(
            f"| {row['margin']:.2f} | {row['minimum_auc_delta']:+.6f} | "
            f"{row['mean_auc_delta']:+.6f} | {row['mean_k4_recall_delta']:+.6f} |"
        )
    markdown = f"""# Sparse-tail augmentation development

Verdict: **`{verdict}`**

Selected margin: **`{selected['margin']:.2f}`**

| margin | minimum AUROC delta | mean AUROC delta | mean k=4 recall delta |
|---:|---:|---:|---:|
{chr(10).join(rows)}

Selected mean recall deltas at alpha .05:

- k=4: `{mean_recall_delta['4']:+.6f}`
- k=6: `{mean_recall_delta['6']:+.6f}`
- k=8: `{mean_recall_delta['8']:+.6f}`
- k=12: `{mean_recall_delta['12']:+.6f}`

This result uses only already exposed record artifacts. SonotaCo 2021 remains reserved for a separately frozen prospective validation.
"""
    (args.output / "SPARSE_TAIL_AUGMENTATION_DEVELOPMENT.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
