#!/usr/bin/env python3
"""Patch the frozen wavelet episode runner to add OrbitTrace multi-anchor energy v3."""
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
    source = replace_once(
        source,
        '        "wavelet_rules_frozen": (\n'
        '            wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and all(wavelet.self_test().values())\n'
        '        ),\n'
        '    }\n',
        '        "wavelet_rules_frozen": (\n'
        '            wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and all(wavelet.self_test().values())\n'
        '        ),\n'
        '        "multi_anchor_energy_v3_rules_frozen": (\n'
        '            v3.METHOD_ID == "orbittrace_multi_anchor_wavelet_energy_v3"\n'
        '            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and v3.TOP_ANCHORS == 4\n'
        '            and all(v3.self_test().values())\n'
        '        ),\n'
        '    }\n',
        "v3 integrity gate",
    )
    source = replace_once(
        source,
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n',
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n'
        '            "multi_anchor_energy_v3": "new OrbitTrace-developed aggregation of the exact frozen Brown-family anchor coefficients",\n',
        "structural boundary",
    )
    source = replace_once(
        source,
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n',
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n'
        '        "multi_anchor_v3_method_id": v3.METHOD_ID,\n'
        '        "multi_anchor_v3_top_anchors": v3.TOP_ANCHORS,\n'
        '        "multi_anchor_v3_aggregation": "l2_energy_of_four_largest_positive_coefficients",\n',
        "transferred parameters",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "new OrbitTrace method development",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_MULTI_ANCHOR_ENERGY_V3_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
