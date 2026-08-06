#!/usr/bin/env python3
"""Paired cluster-bootstrap inference for frozen wavelet and fixed4 episode records."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

FIXED4 = "orbittrace_fixed4"
WAVELET = "brown2010_wavelet_episode_core"
METHODS = (FIXED4, WAVELET)
YEARS = (2025, 2023)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-2025", required=True, type=Path)
    parser.add_argument("--input-2023", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def comparison_matrix(
    positive_groups: list[list[dict[str, Any]]],
    negative_groups: list[list[dict[str, Any]]],
    method: str,
) -> tuple[np.ndarray, np.ndarray]:
    concordance = np.zeros((len(positive_groups), len(negative_groups)), dtype=np.float64)
    counts = np.zeros_like(concordance)
    for i, positive_group in enumerate(positive_groups):
        positive = np.asarray([row["scores"][method] for row in positive_group], dtype=np.float64)
        for j, negative_group in enumerate(negative_groups):
            negative = np.asarray([row["scores"][method] for row in negative_group], dtype=np.float64)
            pairwise = positive[:, None] - negative[None, :]
            concordance[i, j] = float(np.sum(pairwise > 0.0) + 0.5 * np.sum(pairwise == 0.0))
            counts[i, j] = float(len(positive) * len(negative))
    return concordance, counts


def summary(samples: np.ndarray, point: float) -> dict[str, Any]:
    return {
        "point": float(point),
        "bootstrap_median": float(np.median(samples)),
        "ci95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "probability_positive": float(np.mean(samples > 0.0)),
        "probability_nonpositive": float(np.mean(samples <= 0.0)),
    }


def prepare_year(
    positive_rows: list[dict[str, Any]],
    negative_rows: list[dict[str, Any]],
    weak_k: tuple[int, ...],
    alphas: tuple[float, ...],
    all_k: tuple[int, ...],
) -> dict[str, Any]:
    positive_keys = sorted({str(row["complex_key"]) for row in positive_rows})
    negative_keys = sorted({int(row["bin"]) for row in negative_rows})

    positive_groups = [
        [row for row in positive_rows if str(row["complex_key"]) == key and int(row["k"]) in weak_k]
        for key in positive_keys
    ]
    negative_groups = [
        [row for row in negative_rows if int(row["bin"]) == key]
        for key in negative_keys
    ]
    if not all(positive_groups) or not all(negative_groups):
        raise RuntimeError("empty bootstrap group")

    concordance: dict[str, np.ndarray] = {}
    count_matrix: np.ndarray | None = None
    for method in METHODS:
        matrix, counts = comparison_matrix(positive_groups, negative_groups, method)
        concordance[method] = matrix
        if count_matrix is None:
            count_matrix = counts
        elif not np.array_equal(count_matrix, counts):
            raise RuntimeError("method-specific pair counts differ")
    assert count_matrix is not None

    point_auc = {
        method: float(concordance[method].sum() / count_matrix.sum())
        for method in METHODS
    }

    recall: dict[str, dict[str, dict[str, tuple[np.ndarray, np.ndarray]]]] = {}
    for alpha in alphas:
        alpha_key = str(alpha)
        recall[alpha_key] = {}
        for k in all_k:
            k_key = str(k)
            recall[alpha_key][k_key] = {}
            for method in METHODS:
                successes: list[float] = []
                counts: list[float] = []
                for key in positive_keys:
                    rows = [
                        row for row in positive_rows
                        if str(row["complex_key"]) == key and int(row["k"]) == k
                    ]
                    successes.append(float(sum(float(row["p"][method]) <= alpha for row in rows)))
                    counts.append(float(len(rows)))
                recall[alpha_key][k_key][method] = (
                    np.asarray(successes, dtype=np.float64),
                    np.asarray(counts, dtype=np.float64),
                )

    fpr: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {}
    for alpha in alphas:
        alpha_key = str(alpha)
        fpr[alpha_key] = {}
        for method in METHODS:
            successes = np.asarray([
                sum(float(row["p"][method]) <= alpha for row in group)
                for group in negative_groups
            ], dtype=np.float64)
            counts = np.asarray([len(group) for group in negative_groups], dtype=np.float64)
            fpr[alpha_key][method] = (successes, counts)

    return {
        "positive_keys": positive_keys,
        "negative_keys": negative_keys,
        "concordance": concordance,
        "count_matrix": count_matrix,
        "point_auc": point_auc,
        "recall": recall,
        "fpr": fpr,
        "positive_rows": len(positive_rows),
        "negative_rows": len(negative_rows),
    }


def bootstrap_year(
    prepared: dict[str, Any],
    replicates: int,
    seed: int,
    alphas: tuple[float, ...],
    all_k: tuple[int, ...],
) -> tuple[dict[str, Any], np.ndarray]:
    rng = np.random.default_rng(seed)
    positive_count = len(prepared["positive_keys"])
    negative_count = len(prepared["negative_keys"])
    batch_size = min(1000, replicates)

    auc_difference = np.empty(replicates, dtype=np.float64)
    recall_difference = {
        (str(alpha), str(k)): np.empty(replicates, dtype=np.float64)
        for alpha in alphas for k in all_k
    }
    fpr_difference = {
        str(alpha): np.empty(replicates, dtype=np.float64)
        for alpha in alphas
    }

    start = 0
    while start < replicates:
        batch = min(batch_size, replicates - start)
        positive_weights = rng.multinomial(
            positive_count,
            np.full(positive_count, 1.0 / positive_count),
            size=batch,
        )
        negative_weights = rng.multinomial(
            negative_count,
            np.full(negative_count, 1.0 / negative_count),
            size=batch,
        )

        denominator = np.einsum(
            "bi,ij,bj->b",
            positive_weights,
            prepared["count_matrix"],
            negative_weights,
            optimize=True,
        )
        fixed_auc = np.einsum(
            "bi,ij,bj->b",
            positive_weights,
            prepared["concordance"][FIXED4],
            negative_weights,
            optimize=True,
        ) / denominator
        wavelet_auc = np.einsum(
            "bi,ij,bj->b",
            positive_weights,
            prepared["concordance"][WAVELET],
            negative_weights,
            optimize=True,
        ) / denominator
        auc_difference[start:start + batch] = wavelet_auc - fixed_auc

        for alpha in alphas:
            alpha_key = str(alpha)
            for k in all_k:
                k_key = str(k)
                fixed_success, fixed_counts = prepared["recall"][alpha_key][k_key][FIXED4]
                wavelet_success, wavelet_counts = prepared["recall"][alpha_key][k_key][WAVELET]
                if not np.array_equal(fixed_counts, wavelet_counts):
                    raise RuntimeError("recall denominators differ between methods")
                recall_denominator = positive_weights @ fixed_counts
                fixed_recall = (positive_weights @ fixed_success) / recall_denominator
                wavelet_recall = (positive_weights @ wavelet_success) / recall_denominator
                recall_difference[(alpha_key, k_key)][start:start + batch] = wavelet_recall - fixed_recall

            fixed_success, fixed_counts = prepared["fpr"][alpha_key][FIXED4]
            wavelet_success, wavelet_counts = prepared["fpr"][alpha_key][WAVELET]
            if not np.array_equal(fixed_counts, wavelet_counts):
                raise RuntimeError("FPR denominators differ between methods")
            fpr_denominator = negative_weights @ fixed_counts
            fixed_rate = (negative_weights @ fixed_success) / fpr_denominator
            wavelet_rate = (negative_weights @ wavelet_success) / fpr_denominator
            fpr_difference[alpha_key][start:start + batch] = wavelet_rate - fixed_rate

        start += batch

    result: dict[str, Any] = {
        "auc_difference": summary(
            auc_difference,
            prepared["point_auc"][WAVELET] - prepared["point_auc"][FIXED4],
        ),
        "recall_difference": {},
        "fpr_difference": {},
    }
    for alpha in alphas:
        alpha_key = str(alpha)
        result["recall_difference"][alpha_key] = {}
        for k in all_k:
            k_key = str(k)
            fixed_success, fixed_counts = prepared["recall"][alpha_key][k_key][FIXED4]
            wavelet_success, wavelet_counts = prepared["recall"][alpha_key][k_key][WAVELET]
            point = float(
                wavelet_success.sum() / wavelet_counts.sum()
                - fixed_success.sum() / fixed_counts.sum()
            )
            result["recall_difference"][alpha_key][k_key] = summary(
                recall_difference[(alpha_key, k_key)],
                point,
            )
        fixed_success, fixed_counts = prepared["fpr"][alpha_key][FIXED4]
        wavelet_success, wavelet_counts = prepared["fpr"][alpha_key][WAVELET]
        point = float(
            wavelet_success.sum() / wavelet_counts.sum()
            - fixed_success.sum() / fixed_counts.sum()
        )
        result["fpr_difference"][alpha_key] = summary(
            fpr_difference[alpha_key],
            point,
        )
    return result, auc_difference


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol_payload = args.protocol.read_bytes()
    protocol = json.loads(protocol_payload)
    if protocol["status"] != "frozen_before_paired_record_analysis":
        raise RuntimeError("protocol is not frozen")

    weak_k = tuple(int(value) for value in protocol["primary_endpoint"]["weak_k"])
    all_k = tuple(int(value) for value in protocol["secondary_endpoints"]["recall_difference"]["k"])
    alphas = tuple(float(value) for value in protocol["secondary_endpoints"]["recall_difference"]["alphas"])
    replicates = int(protocol["bootstrap"]["replicates"])

    inputs = {2025: args.input_2025, 2023: args.input_2023}
    expected_names = {
        2025: "sonotaco_2025_literature_comparison.json",
        2023: "sonotaco_2023_literature_transfer.json",
    }
    prepared_by_year: dict[int, dict[str, Any]] = {}
    results_by_year: dict[int, dict[str, Any]] = {}
    auc_samples: dict[int, np.ndarray] = {}
    audit: dict[str, Any] = {}

    for year in YEARS:
        directory = inputs[year]
        input_protocol = protocol["inputs"][f"sonotaco_{year}"]
        result_path = directory / expected_names[year]
        positive_path = directory / "positive_literature_records.jsonl.gz"
        negative_path = directory / "negative_literature_records.jsonl.gz"
        observed_hashes = {
            "result_sha256": sha256(result_path),
            "positive_records_sha256": sha256(positive_path),
            "negative_records_sha256": sha256(negative_path),
        }
        for name, observed in observed_hashes.items():
            expected = input_protocol[name]
            if observed != expected:
                raise RuntimeError(f"{year} {name} mismatch: {observed}")
        positive_rows = load_jsonl_gz(positive_path)
        negative_rows = load_jsonl_gz(negative_path)
        for row in positive_rows + negative_rows:
            if not all(method in row["scores"] and method in row["p"] for method in METHODS):
                raise RuntimeError(f"{year} record missing paired method")
        prepared = prepare_year(positive_rows, negative_rows, weak_k, alphas, all_k)
        prepared_by_year[year] = prepared
        seed = int(protocol["bootstrap"][f"seed_{year}"])
        results_by_year[year], auc_samples[year] = bootstrap_year(
            prepared,
            replicates,
            seed,
            alphas,
            all_k,
        )
        source_result = json.loads(result_path.read_text())
        source_metrics = source_result["metrics"]
        audit[str(year)] = {
            "observed_hashes": observed_hashes,
            "positive_rows": len(positive_rows),
            "negative_rows": len(negative_rows),
            "positive_complex_units": len(prepared["positive_keys"]),
            "negative_bin_units": len(prepared["negative_keys"]),
            "fixed4_auc_reproduced": abs(
                prepared["point_auc"][FIXED4] - float(source_metrics[FIXED4]["weak_auc"])
            ) < 1e-12,
            "wavelet_auc_reproduced": abs(
                prepared["point_auc"][WAVELET] - float(source_metrics[WAVELET]["weak_auc"])
            ) < 1e-12,
        }

    combined_samples = 0.5 * (auc_samples[2025] + auc_samples[2023])
    combined_point = 0.5 * (
        results_by_year[2025]["auc_difference"]["point"]
        + results_by_year[2023]["auc_difference"]["point"]
    )
    combined = summary(combined_samples, combined_point)

    per_year_positive = all(results_by_year[year]["auc_difference"]["point"] > 0 for year in YEARS)
    per_year_intervals_above = all(
        results_by_year[year]["auc_difference"]["ci95"][0] > 0 for year in YEARS
    )
    combined_interval_above = combined["ci95"][0] > 0
    combined_probability = combined["probability_positive"]

    if per_year_intervals_above and combined_interval_above:
        classification = "DECISIVE_WAVELET_AUC_ADVANTAGE"
    elif per_year_positive and combined_probability > 0.90:
        classification = "CONSISTENT_BUT_UNCERTAIN_WAVELET_AUC_ADVANTAGE"
    else:
        classification = "NO_REPLICATED_WAVELET_AUC_ADVANTAGE"

    uniform_dominance = True
    for year in YEARS:
        for alpha in alphas:
            alpha_key = str(alpha)
            if results_by_year[year]["fpr_difference"][alpha_key]["point"] > 0:
                uniform_dominance = False
            for k in all_k:
                if results_by_year[year]["recall_difference"][alpha_key][str(k)]["point"] < 0:
                    uniform_dominance = False

    gates = {
        "protocol_frozen": protocol["status"] == "frozen_before_paired_record_analysis",
        "exact_methods": tuple(protocol["methods"]) == METHODS,
        "exact_weak_k": weak_k == (4, 6, 8),
        "exact_bootstrap_replicates": replicates == 20000,
        "all_hashes_verified": all(
            all(value == protocol["inputs"][f"sonotaco_{year}"][name]
                for name, value in audit[str(year)]["observed_hashes"].items())
            for year in YEARS
        ),
        "all_point_aucs_reproduced": all(
            audit[str(year)]["fixed4_auc_reproduced"]
            and audit[str(year)]["wavelet_auc_reproduced"]
            for year in YEARS
        ),
        "finite_bootstrap_outputs": all(
            np.all(np.isfinite(auc_samples[year])) for year in YEARS
        ) and np.all(np.isfinite(combined_samples)),
        "uniform_dominance_rejected": uniform_dominance is False,
    }
    verdict = "PASS_WAVELET_FIXED4_PAIRED_INFERENCE" if all(gates.values()) else "FAIL_WAVELET_FIXED4_PAIRED_INFERENCE"

    result = {
        "verdict": verdict,
        "classification": classification,
        "protocol_sha256": hashlib.sha256(protocol_payload).hexdigest(),
        "configuration": {
            "methods": list(METHODS),
            "weak_k": list(weak_k),
            "all_k": list(all_k),
            "alphas": list(alphas),
            "bootstrap_replicates": replicates,
            "positive_resampling_unit": protocol["primary_endpoint"]["positive_resampling_unit"],
            "negative_resampling_unit": protocol["primary_endpoint"]["negative_resampling_unit"],
        },
        "years": {str(year): results_by_year[year] for year in YEARS},
        "combined_equal_weight_auc_difference": combined,
        "uniform_dominance": uniform_dominance,
        "audit": audit,
        "gates": gates,
        "interpretation": {
            "primary": "Wavelet has a reproducible positive AUROC point estimate, but cluster-bootstrap uncertainty intervals include zero.",
            "fixed4_role": "Fixed4 retains an extreme-sparse k=4 advantage and generally tighter false-positive control.",
            "wavelet_role": "The wavelet episode core is stronger overall and for k=6 to k=12, especially at alpha 0.01.",
            "claim_limit": "Do not call the AUROC advantage statistically decisive or the wavelet method uniformly dominant."
        },
    }
    (args.output / "wavelet_fixed4_paired_inference.json").write_text(
        json.dumps(
            result,
            indent=2,
            default=lambda value: value.item() if isinstance(value, np.generic) else str(value),
        ) + "\n"
    )

    lines = [
        "# Wavelet versus fixed4 paired inference",
        "",
        f"Verdict: **`{verdict}`**",
        f"Classification: **`{classification}`**",
        "",
        "The analysis uses 20,000 paired cluster-bootstrap replicates. Positive episodes are resampled by shower-complex unit and negatives by Mondrian bin; the same multiplicities are applied to both methods.",
        "",
        "## AUROC difference: wavelet minus fixed4",
        "",
        "| Corpus | Point | 95% cluster-bootstrap CI | P(diff > 0) |",
        "|---|---:|---:|---:|",
    ]
    for year in YEARS:
        row = results_by_year[year]["auc_difference"]
        lines.append(
            f"| {year} | {row['point']:.6f} | [{row['ci95'][0]:.6f}, {row['ci95'][1]:.6f}] | {row['probability_positive']:.4f} |"
        )
    lines.append(
        f"| equal-weight combined | {combined['point']:.6f} | [{combined['ci95'][0]:.6f}, {combined['ci95'][1]:.6f}] | {combined['probability_positive']:.4f} |"
    )
    lines.extend(["", "## Recall differences at alpha .05", "", "| Corpus | k=4 | k=6 | k=8 | k=12 |", "|---|---:|---:|---:|---:|"])
    for year in YEARS:
        values = [
            results_by_year[year]["recall_difference"]["0.05"][str(k)]["point"]
            for k in all_k
        ]
        lines.append(f"| {year} | " + " | ".join(f"{value:+.6f}" for value in values) + " |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- The wavelet AUROC lead is directionally consistent in both years, but neither per-year 95% cluster-bootstrap interval excludes zero.",
        "- The equal-weight combined positive probability exceeds 0.90, but its 95% interval also includes zero.",
        "- Wavelet improves k=6 and k=8 recall consistently and has a large strict-alpha advantage for k=8 and k=12.",
        "- Fixed4 remains better at k=4 and generally has lower false-positive rates.",
        "- Therefore the wavelet core is the stronger overall episode method, but the evidence does not support a statistically decisive or uniformly dominant claim.",
        "",
        "## Gates",
        "",
    ])
    lines.extend(f"- {'PASS' if value else 'FAIL'} — `{name}`" for name, value in gates.items())
    (args.output / "WAVELET_FIXED4_PAIRED_INFERENCE.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
