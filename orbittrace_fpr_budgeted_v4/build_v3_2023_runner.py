#!/usr/bin/env python3
"""Patch the frozen SonotaCo 2023 wavelet transfer runner with frozen OrbitTrace v3.

This adapter changes only the method registry/score bookkeeping needed to evaluate
the already-frozen v3 multi-anchor aggregation on the validated 2023 benchmark.
It does not alter parsing, sampling, calibration, fixed4, Brown, or any benchmark
parameter.
"""
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


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    source = replace_once(
        source,
        "import wavelet_episode_comparator as wavelet\n",
        "import wavelet_episode_comparator as wavelet\nimport multi_anchor_energy_v3 as v3\n",
        "v3 import",
    )
    source = replace_once(
        source,
        '    "brown2010_wavelet_episode_core",\n)\n',
        '    "brown2010_wavelet_episode_core",\n    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\n',
        "method registry",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n    }\n',
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '        "orbittrace_multi_anchor_wavelet_energy_v3": v3.multi_anchor_energy_episode_score(episode),\n'
        '    }\n',
        "episode score",
    )

    wavelet_gate = (
        '        "wavelet_parameters_unchanged": (\n'
        '            wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and all(wavelet.self_test().values())\n'
        '        ),\n'
    )
    source = replace_once(
        source,
        wavelet_gate,
        wavelet_gate
        + '        "multi_anchor_energy_v3_parameters_unchanged": (\n'
        + '            v3.METHOD_ID == "orbittrace_multi_anchor_wavelet_energy_v3"\n'
        + '            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        + '            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        + '            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0\n'
        + '            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0\n'
        + '            and v3.TOP_ANCHORS == 4\n'
        + '            and all(v3.self_test().values())\n'
        + '        ),\n',
        "v3 integrity gate",
    )
    source = replace_once(
        source,
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n',
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n'
        '            "multi_anchor_energy_v3": "frozen OrbitTrace aggregation of the exact Brown-family leave-one-out coefficients",\n',
        "structural boundary",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace ranking transfer",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_V3_2023_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
