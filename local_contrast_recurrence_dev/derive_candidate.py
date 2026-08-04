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
        "        local_contrast_best = np.full(SHAPE, -np.inf, dtype=np.float64)\n",
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

            # Spatially high-pass each annual evidence map before recurrence aggregation.
            # The kernel is fixed wider than the injected/template footprint and the
            # shared smooth distortion used by the stress null.
            local_background = gaussian_filter(
                per_year_evidence,
                sigma=(0.0, 3.0, 3.0, 2.0, 1.5),
                mode=("nearest", "wrap", "wrap", "nearest", "nearest"),
            )
            contrast_evidence = np.maximum(per_year_evidence - local_background, 0.0)
            ordered_contrast = np.partition(contrast_evidence, -self.r_required, axis=0)
            local_contrast_score = ordered_contrast[-self.r_required]
""",
    )
    source = replace_once(
        source,
        """            soft_recurrence_best = np.maximum(soft_recurrence_best, soft_recurrence_score)
        return pooled_best, pooled_confirm_best, replicate_best, soft_recurrence_best
""",
        """            soft_recurrence_best = np.maximum(soft_recurrence_best, soft_recurrence_score)
            local_contrast_best = np.maximum(local_contrast_best, local_contrast_score)
        return pooled_best, pooled_confirm_best, replicate_best, soft_recurrence_best, local_contrast_best
""",
    )
    source = replace_once(
        source,
        "    soft_recurrence_map: np.ndarray,\n",
        "    soft_recurrence_map: np.ndarray,\n    local_contrast_map: np.ndarray,\n",
    )
    source = replace_once(
        source,
        '        ("soft_recurrence", soft_recurrence_map),\n',
        '        ("soft_recurrence", soft_recurrence_map),\n        ("local_contrast", local_contrast_map),\n',
    )
    source = replace_once(
        source,
        '    methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence")',
        '    methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence", "local_contrast")',
    )

    source = source.replace(
        "pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map = bank.score_maps(",
        "pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, local_contrast_map = bank.score_maps(",
    )
    source = replace_once(
        source,
        '                "soft_recurrence": soft_recurrence_map,\n',
        '                "soft_recurrence": soft_recurrence_map,\n                "local_contrast": local_contrast_map,\n',
    )
    source = source.replace(
        "evaluate_maps(pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, thresholds,",
        "evaluate_maps(pooled_map, pooled_confirm_map, replicate_map, soft_recurrence_map, local_contrast_map, thresholds,",
    )

    replacement_metrics = '''    baseline_methods = ("pooled", "pooled_confirm", "replicate", "soft_recurrence")
    best_baseline_weak_power = max(metrics[f"{method}_weak_recurrent_recovery"] for method in baseline_methods)
    best_baseline_strong_power = max(metrics[f"{method}_strong_recurrent_recovery"] for method in baseline_methods)
    best_baseline_margin = max(metrics[f"{method}_weak_recurrence_margin"] for method in baseline_methods)
    metrics["best_baseline_weak_recurrent_recovery"] = best_baseline_weak_power
    metrics["best_baseline_strong_recurrent_recovery"] = best_baseline_strong_power
    metrics["best_baseline_weak_recurrence_margin"] = best_baseline_margin
    metrics["local_contrast_margin_gain_vs_best_baseline"] = metrics["local_contrast_weak_recurrence_margin"] - best_baseline_margin
    metrics["local_contrast_weak_recovery_difference_vs_best_baseline"] = metrics["local_contrast_weak_recurrent_recovery"] - best_baseline_weak_power
    metrics["local_contrast_strong_recovery_difference_vs_best_baseline"] = metrics["local_contrast_strong_recurrent_recovery"] - best_baseline_strong_power

    tol = 1e-12
    gates = {
        "ideal_null_fwer_at_most_0_15": bool(ideal_summary["local_contrast"]["probability_any_detection"] <= 0.15 + tol),
        "shared_structure_null_fwer_at_most_0_15": bool(shared_structure_summary["local_contrast"]["probability_any_detection"] <= 0.15 + tol),
        "weak_recurrent_power_loss_vs_best_baseline_at_most_0_05": bool(metrics["local_contrast_weak_recovery_difference_vs_best_baseline"] >= -0.05 - tol),
        "weak_one_year_artifact_detection_at_most_0_20": bool(metrics["local_contrast_weak_transient_detection"] <= 0.20 + tol),
        "recurrence_margin_gain_vs_best_baseline_at_least_0_05": bool(metrics["local_contrast_margin_gain_vs_best_baseline"] >= 0.05 - tol),
        "strong_recurrent_power_no_material_collapse_vs_best_baseline": bool(metrics["local_contrast_strong_recovery_difference_vs_best_baseline"] >= -0.05 - tol),
    }
    verdict = "CONTINUE_LOCAL_CONTRAST_FULL_STAGE0" if all(gates.values()) else "KILL_LOCAL_CONTRAST_RECURRENCE"
'''
    start = source.index('    baseline_methods = ("pooled", "pooled_confirm", "replicate")')
    end = source.index("\n    return {", start)
    source = source[:start] + replacement_metrics + source[end:]
    source = replace_once(
        source,
        '"method": "worst-family calibrated leave-one-year-out recurrence scan",',
        '"method": "worst-family calibrated local-contrast hard recurrence scan",',
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
