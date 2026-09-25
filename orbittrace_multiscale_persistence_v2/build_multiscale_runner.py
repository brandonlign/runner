#!/usr/bin/env python3
"""Patch the frozen wavelet episode runner to add OrbitTrace multiscale consensus v2."""
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
        "import wavelet_episode_comparator as wavelet\nimport multiscale_consensus_v2 as v2\n",
        "v2 import",
    )
    source = replace_once(
        source,
        '    "brown2010_wavelet_episode_core",\n)\n',
        '    "brown2010_wavelet_episode_core",\n    "orbittrace_multiscale_consensus_v2",\n)\n',
        "method registry",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n    }\n',
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '        "orbittrace_multiscale_consensus_v2": v2.multiscale_consensus_episode_score(episode),\n'
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
        '        "multiscale_consensus_v2_rules_frozen": (\n'
        '            v2.METHOD_ID == "orbittrace_multiscale_consensus_v2"\n'
        '            and v2.SCALE_BANK == ((2.0, 0.050), (3.0, 0.075), (4.0, 0.100), (6.0, 0.150))\n'
        '            and v2.ADJACENT_SCALE_PAIRS == ((0, 1), (1, 2), (2, 3))\n'
        '            and v2.TOP_ANCHORS == 4\n'
        '            and v2.TRUNCATION_RADIUS == 4.0\n'
        '            and v2.KERNEL_DIMENSION == 3.0\n'
        '            and all(v2.self_test().values())\n'
        '        ),\n'
        '    }\n',
        "v2 integrity gate",
    )
    source = replace_once(
        source,
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n',
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n'
        '            "multiscale_consensus_v2": "new OrbitTrace-developed multiscale and multi-anchor episode ranking",\n',
        "structural boundary",
    )
    source = replace_once(
        source,
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n',
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n'
        '        "multiscale_v2_method_id": v2.METHOD_ID,\n'
        '        "multiscale_v2_scale_bank": v2.SCALE_BANK,\n'
        '        "multiscale_v2_adjacent_pairs": v2.ADJACENT_SCALE_PAIRS,\n'
        '        "multiscale_v2_top_anchors": v2.TOP_ANCHORS,\n'
        '        "multiscale_v2_robust_scale_constant": v2.ROBUST_SCALE_CONSTANT,\n',
        "transferred parameters",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "orbittrace_multiscale_consensus_v2": "new OrbitTrace method development",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_MULTISCALE_CONSENSUS_V2_RUNNER", digest)


if __name__ == "__main__":
    main()
