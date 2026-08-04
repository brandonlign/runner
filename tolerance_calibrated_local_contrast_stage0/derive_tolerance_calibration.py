#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

OLD_THRESHOLD = '''def empirical_threshold(maxima: list[float], alpha: float) -> float:\n    ordered = sorted(maxima)\n    # Conservative nearest-rank estimate of the (1-alpha) quantile.\n    rank = max(0, min(len(ordered) - 1, math.ceil((1.0 - alpha) * len(ordered)) - 1))\n    return float(ordered[rank])\n'''
NEW_THRESHOLD = '''def tolerance_threshold(maxima: list[float], alpha: float) -> float:\n    \"\"\"One-sided nonparametric upper tolerance bound for a family maximum.\n\n    Select the smallest order statistic whose true exceedance probability is at\n    most ``alpha`` with at least ``CALIBRATION_CONFIDENCE`` probability under\n    exchangeable calibration maxima.\n    \"\"\"\n    ordered = sorted(maxima)\n    n = len(ordered)\n    if n < 2:\n        raise ValueError(\"at least two calibration maxima are required\")\n    target_cdf = 1.0 - alpha\n    for one_based_rank in range(1, n + 1):\n        confidence = 1.0 - beta.cdf(target_cdf, one_based_rank, n + 1 - one_based_rank)\n        if confidence + 1e-15 >= CALIBRATION_CONFIDENCE:\n            return float(ordered[one_based_rank - 1])\n    return float(ordered[-1])\n\n\ndef tolerance_rank(calibration_trials: int, alpha: float) -> int:\n    target_cdf = 1.0 - alpha\n    for one_based_rank in range(1, calibration_trials + 1):\n        confidence = 1.0 - beta.cdf(\n            target_cdf, one_based_rank, calibration_trials + 1 - one_based_rank\n        )\n        if confidence + 1e-15 >= CALIBRATION_CONFIDENCE:\n            return one_based_rank\n    return calibration_trials\n'''


def replace_exact(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    source = arguments.input.read_text()

    source = replace_exact(
        source,
        "from scipy.stats import poisson",
        "from scipy.stats import beta, poisson",
        "scipy import",
    )
    source = replace_exact(
        source,
        "EPS = 1e-300\n",
        "EPS = 1e-300\nCALIBRATION_CONFIDENCE = 0.95\n",
        "constants",
    )
    source = replace_exact(source, OLD_THRESHOLD, NEW_THRESHOLD, "threshold function")
    source = replace_exact(
        source,
        "family: {method: empirical_threshold(values, alpha) for method, values in family_maxima.items()}",
        "family: {method: tolerance_threshold(values, alpha) for method, values in family_maxima.items()}",
        "threshold call",
    )
    source = source.replace(
        '"method": "worst-family calibrated local-contrast hard recurrence scan",',
        '"method": "worst-family tolerance-calibrated local-contrast hard recurrence scan",',
        1,
    )
    source = replace_exact(
        source,
        '''        "alpha": alpha,\n        "calibration_trials": calibration_trials,\n''',
        '''        "alpha": alpha,\n        "calibration_confidence": CALIBRATION_CONFIDENCE,\n        "tolerance_rank": tolerance_rank(calibration_trials, alpha),\n        "calibration_trials": calibration_trials,\n''',
        "result metadata",
    )
    source = replace_exact(
        source,
        'verdict = "CONTINUE_LOCAL_CONTRAST_FULL_STAGE0" if all(gates.values()) else "KILL_LOCAL_CONTRAST_RECURRENCE"',
        'verdict = "CONTINUE_TOLERANCE_CALIBRATED_LOCAL_CONTRAST" if all(gates.values()) else "KILL_TOLERANCE_CALIBRATED_LOCAL_CONTRAST"',
        "verdict",
    )
    source = source.replace(
        "# Worst-family recurrence Stage-0 result",
        "# Tolerance-calibrated local-contrast recurrence result",
        1,
    )
    source = source.replace(
        "Complete-search thresholds are the maximum of separately calibrated independent-year and shared-structure thresholds.",
        "Complete-search thresholds are the maximum of separate one-sided nonparametric tolerance bounds for the independent-year and shared-structure null families.",
        1,
    )

    # Reporting-only repair after the prior run wrote its authoritative JSON but
    # failed on stale soft-recurrence keys.
    source = source.replace(
        "metrics['soft_recurrence_weak_recurrent_recovery']",
        "metrics['local_contrast_weak_recurrent_recovery']",
    )
    source = source.replace(
        "metrics['soft_recurrence_weak_transient_detection']",
        "metrics['local_contrast_weak_transient_detection']",
    )
    source = source.replace(
        "metrics['soft_recurrence_weak_recurrence_margin']",
        "metrics['local_contrast_weak_recurrence_margin']",
    )
    source = source.replace(
        "result['ideal_null']['soft_recurrence']",
        "result['ideal_null']['local_contrast']",
    )
    source = source.replace(
        "result['shared_structure_null']['soft_recurrence']",
        "result['shared_structure_null']['local_contrast']",
    )
    source = source.replace(
        "Soft recurrence recurrent recovery", "Local-contrast recurrent recovery"
    )
    source = source.replace(
        "Soft recurrence one-year-artifact detection",
        "Local-contrast one-year-artifact detection",
    )
    source = source.replace(
        "Soft recurrence recurrence margin", "Local-contrast recurrence margin"
    )

    arguments.output.write_text(source)


if __name__ == "__main__":
    main()
