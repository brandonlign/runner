#!/usr/bin/env python3
"""Add frozen OrbitTrace v3 scoring to the validated SonotaCo-2023 wavelet transfer runner."""
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
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace v3 transfer",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_V3_2023_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
