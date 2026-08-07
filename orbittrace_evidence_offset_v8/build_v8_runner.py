#!/usr/bin/env python3
"""Add the fully calibrated v8 evidence-offset family to a frozen v3 runner."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import evidence_offset_v8 as v8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def rep(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one target, found {count}")
    return source.replace(old, new)


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    source = rep(
        source,
        "import multi_anchor_energy_v3 as v3\n",
        "import multi_anchor_energy_v3 as v3\nimport evidence_offset_v8 as v8\n",
        "v8 import",
    )
    source = rep(
        source,
        '    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\n',
        '    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\nBASE_METHODS = METHODS\nMETHODS = BASE_METHODS + v8.METHODS\n',
        "method registry",
    )
    source = rep(
        source,
        '    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        '    if set(scores) != set(BASE_METHODS) or not all(np.isfinite(value) for value in scores.values()):\n',
        "score audit",
    )
    source = rep(
        source,
        '    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}\n    for method in METHODS:\n',
        '    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in BASE_METHODS}\n    for method in BASE_METHODS:\n',
        "base calibration registry",
    )
    source = rep(
        source,
        '            calibration[method][bin_index] = values\n\n    for row in negative_rows:\n',
        '            calibration[method][bin_index] = values\n\n'
        '    v8_null = {\n'
        '        method: {\n'
        '            bin_index: v8.calibration_statistics(\n'
        '                calibration[v8.PRIMARY][bin_index],\n'
        '                calibration[v8.SPARSE][bin_index],\n'
        '                v8.METHOD_TO_OFFSET[method],\n'
        '            )\n'
        '            for bin_index in supported_bins\n'
        '        }\n'
        '        for method in v8.METHODS\n'
        '    }\n\n'
        '    for row in negative_rows:\n',
        "candidate null calibration",
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
        for method in v8.METHODS:
            statistic = v8.target_statistic(
                row["scores"][v8.PRIMARY],
                row["scores"][v8.SPARSE],
                calibration[v8.PRIMARY][row["bin"]],
                calibration[v8.SPARSE][row["bin"]],
                v8.METHOD_TO_OFFSET[method],
            )
            row["scores"][method] = statistic
            row["p"][method] = v8.final_pvalue(statistic, v8_null[method][row["bin"]])
'''
    if source.count(old_p) != 2:
        raise RuntimeError(f"target p blocks: expected two, found {source.count(old_p)}")
    source = source.replace(old_p, new_p, 2)

    gate_2025 = '''        "multi_anchor_energy_v3_rules_frozen": (
            v3.METHOD_ID == "orbittrace_multi_anchor_wavelet_energy_v3"
            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0
            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10
            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0
            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0
            and v3.TOP_ANCHORS == 4
            and all(v3.self_test().values())
        ),
'''
    gate_2023 = '''        "wavelet_parameters_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
    addition = '        "evidence_offset_v8_rules_frozen": all(v8.self_test().values()),\n'
    if gate_2025 in source:
        source = rep(source, gate_2025, gate_2025 + addition, "2025 v8 gate")
    elif gate_2023 in source:
        source = rep(source, gate_2023, gate_2023 + addition, "2023 v8 gate")
    else:
        raise RuntimeError("recognized integrity gate missing")

    markers = (
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "new OrbitTrace method development",\n',
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace v3 transfer",\n',
    )
    classifications = ''.join(
        f'        "{method}": "OrbitTrace v8 fully calibrated development candidate",\n'
        for method in v8.METHODS
    )
    for marker in markers:
        if marker in source:
            source = rep(source, marker, marker + classifications, "v8 classifications")
            break
    else:
        raise RuntimeError("v3 classification marker missing")

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_V8_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
