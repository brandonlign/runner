#!/usr/bin/env python3
"""Add the frozen null-calibrated fixed4-wavelet hybrid to a wavelet runner."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one replacement target, found {count}")
    return source.replace(old, new)


def replace_first(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"{label}: replacement target missing")
    return source.replace(old, new, 1)


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    source = replace_once(
        source,
        "import wavelet_episode_comparator as wavelet\n",
        "import wavelet_episode_comparator as wavelet\nimport fixed4_wavelet_hybrid as hybrid\n",
        "hybrid import",
    )
    source = replace_once(
        source,
        '    "brown2010_wavelet_episode_core",\n)\n',
        '    "brown2010_wavelet_episode_core",\n)\nBASE_METHODS = METHODS\nMETHODS = BASE_METHODS + (hybrid.HYBRID_ID,)\n',
        "base and hybrid method registries",
    )
    source = replace_once(
        source,
        '    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        '    if set(scores) != set(BASE_METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        "episode-level method audit",
    )
    source = replace_once(
        source,
        '    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}\n'
        '    for method in METHODS:\n',
        '    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in BASE_METHODS}\n'
        '    for method in BASE_METHODS:\n',
        "base calibration registry",
    )
    source = replace_once(
        source,
        '            calibration[method][bin_index] = values\n\n'
        '    for row in negative_rows:\n',
        '            calibration[method][bin_index] = values\n\n'
        '    hybrid_calibration = {\n'
        '        bin_index: hybrid.calibration_hybrid_statistics(\n'
        '            calibration["orbittrace_fixed4"][bin_index],\n'
        '            calibration["brown2010_wavelet_episode_core"][bin_index],\n'
        '        )\n'
        '        for bin_index in supported_bins\n'
        '    }\n\n'
        '    for row in negative_rows:\n',
        "hybrid calibration construction",
    )

    old_p = '''        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in METHODS
        }
'''
    new_p = '''        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in BASE_METHODS
        }
        hybrid_statistic = hybrid.target_hybrid_statistic(
            row["scores"]["orbittrace_fixed4"],
            row["scores"]["brown2010_wavelet_episode_core"],
            calibration["orbittrace_fixed4"][row["bin"]],
            calibration["brown2010_wavelet_episode_core"][row["bin"]],
        )
        row["scores"][hybrid.HYBRID_ID] = hybrid_statistic
        row["p"][hybrid.HYBRID_ID] = hybrid.final_hybrid_pvalue(
            hybrid_statistic, hybrid_calibration[row["bin"]]
        )
'''
    if source.count(old_p) != 2:
        raise RuntimeError(f"target p-value blocks: expected two, found {source.count(old_p)}")
    source = source.replace(old_p, new_p, 2)

    dsh_gate = '''        "dsh_rules_frozen": (
            literature.RUD2014_MIN_MEMBERS == 6
            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4
            and literature.RUD2014_DSH_THRESHOLD == 0.05
        ),
'''
    if dsh_gate in source:
        source = replace_once(
            source,
            dsh_gate,
            dsh_gate
            + '        "hybrid_rule_frozen": all(hybrid.self_test().values()),\n',
            "2025 hybrid gate",
        )
    else:
        wavelet_gate = '''        "wavelet_parameters_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
        source = replace_once(
            source,
            wavelet_gate,
            wavelet_gate
            + '        "hybrid_rule_frozen": all(hybrid.self_test().values()),\n',
            "transfer hybrid gate",
        )

    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "fixed4_wavelet_tippett_hybrid": "post-comparison null-calibrated hybrid",\n'
        '    }\n',
        "hybrid report classification",
    )

    marker = '        "metrics": metrics,\n'
    source = replace_first(
        source,
        marker,
        marker
        + '        "hybrid_definition": {\n'
        + '            "id": hybrid.HYBRID_ID,\n'
        + '            "components": list(hybrid.COMPONENTS),\n'
        + '            "combiner": "Tippett -log(min empirical component p)",\n'
        + '            "component_calibration": "bin-specific",\n'
        + '            "hybrid_calibration": "bin-specific leave-one-out null statistics",\n'
        + '            "weights": None,\n'
        + '        },\n',
        "hybrid result metadata",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_FIXED4_WAVELET_HYBRID_RUNNER", digest)


if __name__ == "__main__":
    main()
