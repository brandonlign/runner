from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one source occurrence, found {count}: {old[:120]!r}")
    return source.replace(old, new)


def derive(source: str) -> str:
    source = replace_once(
        source,
        "def score_maps(self, histograms: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:",
        "def score_maps(self, histograms: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:",
    )
    source = replace_once(
        source,
        "        soft_recurrence_best = np.full(SHAPE, -np.inf, dtype=np.float64)\n",
        "        soft_recurrence_best = np.full(SHAPE, -np.inf, dtype=np.float64)\n"
        "        majority_conditioned_best = np.full(SHAPE, -np.inf, dtype=np.float64)\n",
    )
    source = replace_once(
        source,
        """            # Original hard partial-conjunction score: the third-strongest year.
            ordered_evidence = np.partition(per_year_evidence, -self.r_required, axis=0)
            replicate_score = ordered_evidence[-self.r_required]
""",
        """            # Original hard partial-conjunction score: the third-strongest year.
            ordered_evidence = np.partition(per_year_evidence, -self.r_required, axis=0)
            replicate_score = ordered_evidence[-self.r_required]

            # Remove evidence that is common to the majority of observing years.
            # The frozen recurrent injection is active in five of fifteen years,
            # whereas the persistent nuisance is shared across all years.
            common_annual_evidence = np.median(per_year_evidence, axis=0)
            conditioned_evidence = np.maximum(
                per_year_evidence - common_annual_evidence[None, ...],
                0.0,
            )
            ordered_conditioned = np.partition(
                conditioned_evidence,
                -self.r_required,
                axis=0,
            )
            majority_conditioned_score = ordered_conditioned[-self.r_required]
""",
    )
    source = replace_once(
        source,
        """            soft_recurrence_best = np.maximum(soft_recurrence_best, soft_recurrence_score)
        return pooled_best, pooled_confirm_best, replicate_best, soft_recurrence_best
""",
        """            soft_recurrence_best = np.maximum(soft_recurrence_best, soft_recurrence_score)
            majority_conditioned_best = np.maximum(
                majority_conditioned_best,
                majority_conditioned_score,
            )
        return (
            pooled_best,
            pooled_confirm_best,
            replicate_best,
            soft_recurrence_best,
            majority_conditioned_best,
        )
""",
    )
    source = replace_once(
        source,
        "    soft_recurrence_map: np.ndarray,\n",
        "    soft_recurrence_map: np.ndarray,\n    majority_conditioned_map: np.ndarray,\n",
    )
    source = replace_once(
        source,
        '        ("soft_recurrence", soft_recurrence_map),\n',
        '        ("soft_recurrence", soft_recurrence_map),\n'
        '        ("majority_conditioned", majority_conditioned_map),\n',
    )
    source = replace_once(
        source,
        '    methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence")',
        '    methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence", "majority_conditioned")',
    )

    source = source.replace(
        "pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map = bank.score_maps(",
        "pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, majority_conditioned_map = bank.score_maps(",
    )
    source = replace_once(
        source,
        '                "soft_recurrence": soft_recurrence_map,\n',
        '                "soft_recurrence": soft_recurrence_map,\n'
        '                "majority_conditioned": majority_conditioned_map,\n',
    )
    source = source.replace(
        "evaluate_maps(pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, thresholds,",
        "evaluate_maps(pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, majority_conditioned_map, thresholds,",
    )

    replacement_metrics = '''    original_baseline_methods = ("pooled", "pooled_confirm", "replicate")
    original_best_weak_power = max(metrics[f"{method}_weak_recurrent_recovery"] for method in original_baseline_methods)
    original_best_strong_power = max(metrics[f"{method}_strong_recurrent_recovery"] for method in original_baseline_methods)
    original_best_margin = max(metrics[f"{method}_weak_recurrence_margin"] for method in original_baseline_methods)
    metrics["soft_recurrence_margin_gain_vs_best_baseline"] = metrics["soft_recurrence_weak_recurrence_margin"] - original_best_margin

    comparison_methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence")
    best_baseline_weak_power = max(metrics[f"{method}_weak_recurrent_recovery"] for method in comparison_methods)
    best_baseline_strong_power = max(metrics[f"{method}_strong_recurrent_recovery"] for method in comparison_methods)
    best_baseline_margin = max(metrics[f"{method}_weak_recurrence_margin"] for method in comparison_methods)
    metrics["best_baseline_weak_recurrent_recovery"] = best_baseline_weak_power
    metrics["best_baseline_strong_recurrent_recovery"] = best_baseline_strong_power
    metrics["best_baseline_weak_recurrence_margin"] = best_baseline_margin
    metrics["majority_conditioned_margin_gain_vs_best_baseline"] = metrics["majority_conditioned_weak_recurrence_margin"] - best_baseline_margin
    metrics["majority_conditioned_weak_recovery_difference_vs_best_baseline"] = metrics["majority_conditioned_weak_recurrent_recovery"] - best_baseline_weak_power
    metrics["majority_conditioned_strong_recovery_difference_vs_best_baseline"] = metrics["majority_conditioned_strong_recurrent_recovery"] - best_baseline_strong_power

    tol = 1e-12
    gates = {
        "ideal_null_fwer_at_most_0_20": bool(ideal_summary["majority_conditioned"]["probability_any_detection"] <= 0.20 + tol),
        "shared_structure_null_fwer_at_most_0_20": bool(shared_structure_summary["majority_conditioned"]["probability_any_detection"] <= 0.20 + tol),
        "weak_recurrent_power_loss_vs_best_baseline_at_most_0_05": bool(metrics["majority_conditioned_weak_recovery_difference_vs_best_baseline"] >= -0.05 - tol),
        "weak_one_year_artifact_detection_at_most_0_20": bool(metrics["majority_conditioned_weak_transient_detection"] <= 0.20 + tol),
        "recurrence_margin_gain_vs_best_baseline_at_least_0_05": bool(metrics["majority_conditioned_margin_gain_vs_best_baseline"] >= 0.05 - tol),
        "strong_recurrent_power_no_material_collapse_vs_best_baseline": bool(metrics["majority_conditioned_strong_recovery_difference_vs_best_baseline"] >= -0.05 - tol),
    }
    verdict = "CONTINUE_MAJORITY_CONDITIONED_FULL_STAGE0" if all(gates.values()) else "KILL_MAJORITY_CONDITIONED_RECURRENCE"
'''
    start = source.index('    baseline_methods = ("pooled", "pooled_confirm", "replicate")')
    end = source.index("\n    return {", start)
    source = source[:start] + replacement_metrics + source[end:]
    source = replace_once(
        source,
        '"method": "worst-family calibrated leave-one-year-out recurrence scan",',
        '"method": "worst-family calibrated majority-conditioned hard recurrence scan",',
    )
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(derive(args.input.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
