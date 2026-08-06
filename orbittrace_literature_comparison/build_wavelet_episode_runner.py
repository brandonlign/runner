#!/usr/bin/env python3
"""Build the frozen SonotaCo-2025 wavelet episode runner before data access."""
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
        "import literature_comparators as literature\n",
        "import literature_comparators as literature\nimport wavelet_episode_comparator as wavelet\n",
        "wavelet import",
    )
    source = replace_once(
        source,
        '    "dsh4_sparse_adaptation",\n)\n',
        '    "dsh4_sparse_adaptation",\n    "brown2010_wavelet_episode_core",\n)\n',
        "method registry",
    )
    source = replace_once(
        source,
        '        "sugar2017_core_transfer": literature.sugar_episode_score(episode, _WORKER_SUGAR_EPSILON),\n    }\n',
        '        "sugar2017_core_transfer": literature.sugar_episode_score(episode, _WORKER_SUGAR_EPSILON),\n'
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '    }\n',
        "episode score",
    )
    source = replace_once(
        source,
        '        "dsh_rules_frozen": (\n'
        '            literature.RUD2014_MIN_MEMBERS == 6\n'
        '            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4\n'
        '            and literature.RUD2014_DSH_THRESHOLD == 0.05\n'
        '        ),\n'
        '    }\n',
        '        "dsh_rules_frozen": (\n'
        '            literature.RUD2014_MIN_MEMBERS == 6\n'
        '            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4\n'
        '            and literature.RUD2014_DSH_THRESHOLD == 0.05\n'
        '        ),\n'
        '        "wavelet_rules_frozen": (\n'
        '            wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and all(wavelet.self_test().values())\n'
        '        ),\n'
        '    }\n',
        "wavelet integrity gate",
    )
    source = replace_once(
        source,
        '            "catalogue_methods": "published HDBSCAN and CMOR wavelet methods remain on the separate catalogue track",\n',
        '            "catalogue_methods": "published HDBSCAN and the full CMOR wavelet survey remain on the separate catalogue track",\n'
        '            "wavelet_episode_core": "a separately labelled sparse-episode adaptation, not the full CMOR survey",\n',
        "structural boundary",
    )
    source = replace_once(
        source,
        '        "dsh_sparse_adaptation_min_members": literature.SPARSE_ADAPTED_MIN_MEMBERS,\n',
        '        "dsh_sparse_adaptation_min_members": literature.SPARSE_ADAPTED_MIN_MEMBERS,\n'
        '        "wavelet_angular_probe_deg": wavelet.ANGULAR_PROBE_DEG,\n'
        '        "wavelet_speed_probe_fraction": wavelet.SPEED_PROBE_FRACTION,\n'
        '        "wavelet_truncation_radius": wavelet.TRUNCATION_RADIUS,\n'
        '        "wavelet_kernel_dimension": wavelet.KERNEL_DIMENSION,\n',
        "transferred parameters",
    )
    source = replace_once(
        source,
        '        "dsh4_sparse_adaptation": "predeclared adaptation",\n'
        '    }\n',
        '        "dsh4_sparse_adaptation": "predeclared adaptation",\n'
        '        "brown2010_wavelet_episode_core": "literature-inspired episode adaptation",\n'
        '    }\n',
        "report classification",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_WAVELET_EPISODE_RUNNER", digest)


if __name__ == "__main__":
    main()
