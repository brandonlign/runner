#!/usr/bin/env python3
"""Patch the frozen wavelet episode runner to add the isolated adaptive likelihood v1."""
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
        "import wavelet_episode_comparator as wavelet\nimport adaptive_likelihood_v1 as adaptive\n",
        "adaptive import",
    )
    source = replace_once(
        source,
        '    "brown2010_wavelet_episode_core",\n)\n',
        '    "brown2010_wavelet_episode_core",\n    "orbittrace_adaptive_local_likelihood_v1",\n)\n',
        "method registry",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n    }\n',
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '        "orbittrace_adaptive_local_likelihood_v1": adaptive.adaptive_likelihood_episode_score(episode),\n'
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
        '        "adaptive_likelihood_rules_frozen": (\n'
        '            adaptive.METHOD_ID == "orbittrace_adaptive_local_likelihood_v1"\n'
        '            and adaptive.SCALE_BANK == ((2.0, 0.050), (3.0, 0.075), (4.0, 0.100), (6.0, 0.150))\n'
        '            and adaptive.OUTER_RADIUS == 4.0\n'
        '            and adaptive.MIN_CORE_MEMBERS == 3\n'
        '            and adaptive.BACKGROUND_PSEUDOCOUNT == 0.5\n'
        '            and all(adaptive.self_test().values())\n'
        '        ),\n'
        '    }\n',
        "adaptive integrity gate",
    )
    source = replace_once(
        source,
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n',
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n'
        '            "adaptive_likelihood_v1": "new OrbitTrace-developed episode core; recurrence remains a later catalogue layer",\n',
        "structural boundary",
    )
    source = replace_once(
        source,
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n',
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n'
        '        "adaptive_method_id": adaptive.METHOD_ID,\n'
        '        "adaptive_scale_bank": adaptive.SCALE_BANK,\n'
        '        "adaptive_core_radius": adaptive.CORE_RADIUS,\n'
        '        "adaptive_outer_radius": adaptive.OUTER_RADIUS,\n'
        '        "adaptive_min_core_members": adaptive.MIN_CORE_MEMBERS,\n'
        '        "adaptive_background_pseudocount": adaptive.BACKGROUND_PSEUDOCOUNT,\n',
        "transferred parameters",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "orbittrace_adaptive_local_likelihood_v1": "new OrbitTrace method development",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_ADAPTIVE_LIKELIHOOD_V1_RUNNER", digest)


if __name__ == "__main__":
    main()
