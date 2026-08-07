#!/usr/bin/env python3
"""Add the v5 jointly calibrated Tippett reporting statistic to a runner that already contains frozen v3."""
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
        "import multi_anchor_energy_v3 as v3\n",
        "import multi_anchor_energy_v3 as v3\nimport joint_tippett_v5 as joint_v5\n",
        "joint v5 import",
    )
    source = replace_once(
        source,
        '    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\n',
        '    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\nBASE_METHODS = METHODS\nMETHODS = BASE_METHODS + (joint_v5.METHOD_ID,)\n',
        "base and v5 registries",
    )
    source = replace_once(
        source,
        '    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        '    if set(scores) != set(BASE_METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        "episode score registry audit",
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
        '    joint_v5_calibration = {\n'
        '        bin_index: joint_v5.calibration_joint_statistics(\n'
        '            calibration["orbittrace_multi_anchor_wavelet_energy_v3"][bin_index],\n'
        '            calibration["orbittrace_fixed4"][bin_index],\n'
        '        )\n'
        '        for bin_index in supported_bins\n'
        '    }\n\n'
        '    for row in negative_rows:\n',
        "joint calibration construction",
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
        joint_statistic = joint_v5.target_joint_statistic(
            row["scores"]["orbittrace_multi_anchor_wavelet_energy_v3"],
            row["scores"]["orbittrace_fixed4"],
            calibration["orbittrace_multi_anchor_wavelet_energy_v3"][row["bin"]],
            calibration["orbittrace_fixed4"][row["bin"]],
        )
        row["scores"][joint_v5.METHOD_ID] = joint_statistic
        row["p"][joint_v5.METHOD_ID] = joint_v5.final_joint_pvalue(
            joint_statistic, joint_v5_calibration[row["bin"]]
        )
'''
    if source.count(old_p) != 2:
        raise RuntimeError(f"target p-value blocks: expected two, found {source.count(old_p)}")
    source = source.replace(old_p, new_p, 2)

    # Add an integrity gate in either the 2025 v3 runner or the validated 2023 transfer runner.
    v3_gate_tail = '''        "multi_anchor_energy_v3_rules_frozen": (
            v3.METHOD_ID == "orbittrace_multi_anchor_wavelet_energy_v3"
            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0
            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10
            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0
            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0
            and v3.TOP_ANCHORS == 4
            and all(v3.self_test().values())
        ),
'''
    wavelet_gate_tail = '''        "wavelet_parameters_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
    if v3_gate_tail in source:
        source = replace_once(
            source,
            v3_gate_tail,
            v3_gate_tail + '        "joint_tippett_v5_rule_frozen": all(joint_v5.self_test().values()),\n',
            "2025 v5 integrity gate",
        )
    elif wavelet_gate_tail in source:
        source = replace_once(
            source,
            wavelet_gate_tail,
            wavelet_gate_tail + '        "joint_tippett_v5_rule_frozen": all(joint_v5.self_test().values()),\n',
            "2023 v5 integrity gate",
        )
    else:
        raise RuntimeError("no recognized integrity-gate insertion point")

    # Add report classification for whichever frozen-v3 runner variant is being adapted.
    classification_candidates = (
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "new OrbitTrace method development",\n',
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace v3 transfer",\n',
    )
    inserted = False
    for marker in classification_candidates:
        if marker in source:
            source = replace_once(
                source,
                marker,
                marker + '        "orbittrace_joint_tippett_v5": "jointly null-calibrated reporting layer; v3 remains continuous ranking",\n',
                "v5 report classification",
            )
            inserted = True
            break
    if not inserted:
        raise RuntimeError("v3 report classification marker missing")

    marker = '        "metrics": metrics,\n'
    source = replace_first(
        source,
        marker,
        marker
        + '        "joint_tippett_v5_definition": {\n'
        + '            "id": joint_v5.METHOD_ID,\n'
        + '            "components": list(joint_v5.COMPONENTS),\n'
        + '            "continuous_ranking": "orbittrace_multi_anchor_wavelet_energy_v3",\n'
        + '            "reporting_combiner": "Tippett -log(min empirical component p)",\n'
        + '            "component_calibration": "bin-specific conservative empirical survival p",\n'
        + '            "joint_calibration": "bin-specific paired leave-one-out null Tippett statistics",\n'
        + '            "reporting_alpha": joint_v5.REPORTING_ALPHA,\n'
        + '            "weights": None,\n'
        + '        },\n',
        "v5 result metadata",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_JOINT_TIPPETT_V5_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
