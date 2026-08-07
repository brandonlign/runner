#!/usr/bin/env python3
"""Add the preregistered v6 top-four pooling family to a frozen wavelet episode runner."""
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
        "import wavelet_episode_comparator as wavelet\nimport multi_anchor_energy_v3 as v3\nimport anchor_pooling_v6 as v6\n",
        "v3/v6 imports",
    )
    source = replace_once(
        source,
        '    "brown2010_wavelet_episode_core",\n)\n',
        '    "brown2010_wavelet_episode_core",\n'
        '    "orbittrace_anchor_l1_v6",\n'
        '    "orbittrace_anchor_l1p5_v6",\n'
        '    "orbittrace_multi_anchor_wavelet_energy_v3",\n'
        '    "orbittrace_anchor_l4_v6",\n'
        '    "orbittrace_anchor_geomean_v6",\n'
        '    "orbittrace_anchor_min4_v6",\n'
        ')\n',
        "candidate registry",
    )
    source = replace_once(
        source,
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '    }\n'
        '    scores.update(v6.scores_for_episode(episode))\n',
        "candidate score injection",
    )

    v2025_gate = '''        "wavelet_rules_frozen": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
    v2023_gate = '''        "wavelet_parameters_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
    gate_addition = (
        '        "anchor_pooling_v6_rules_frozen": (\n'
        '            v6.METHOD_ORDER == (\n'
        '                "orbittrace_anchor_l1_v6",\n'
        '                "orbittrace_anchor_l1p5_v6",\n'
        '                "orbittrace_multi_anchor_wavelet_energy_v3",\n'
        '                "orbittrace_anchor_l4_v6",\n'
        '                "orbittrace_anchor_geomean_v6",\n'
        '                "orbittrace_anchor_min4_v6",\n'
        '            )\n'
        '            and v6.TOP_ANCHORS == 4\n'
        '            and all(v3.self_test().values())\n'
        '            and all(v6.self_test().values())\n'
        '        ),\n'
    )
    if v2025_gate in source:
        source = replace_once(source, v2025_gate, v2025_gate + gate_addition, "2025 v6 integrity gate")
    elif v2023_gate in source:
        source = replace_once(source, v2023_gate, v2023_gate + gate_addition, "2023 v6 integrity gate")
    else:
        raise RuntimeError("recognized wavelet gate not found")

    # Extend report classification with all v6 candidates and frozen v3 reference.
    classification_marker_2025 = '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
    classification_marker_2023 = '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
    if classification_marker_2025 not in source:
        raise RuntimeError("classification insertion point missing")
    additions = (
        '        "orbittrace_anchor_l1_v6": "OrbitTrace v6 development candidate",\n'
        '        "orbittrace_anchor_l1p5_v6": "OrbitTrace v6 development candidate",\n'
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace v3 reference",\n'
        '        "orbittrace_anchor_l4_v6": "OrbitTrace v6 development candidate",\n'
        '        "orbittrace_anchor_geomean_v6": "OrbitTrace v6 development candidate",\n'
        '        "orbittrace_anchor_min4_v6": "OrbitTrace v6 development candidate",\n'
    )
    source = replace_once(
        source,
        classification_marker_2025,
        classification_marker_2025 + additions,
        "v6 classifications",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_ANCHOR_POOLING_V6_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
