#!/usr/bin/env python3
"""Add the frozen wavelet episode score to the immutable 2023 transfer runner."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

WAVELET_SOURCE_SHA256 = "5ef0f7b33a1c3ed87885ee70be0cdd184055d819eb1196c65eebc7e867f747e2"


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
        'COMPARATOR_SOURCE_SHA256 = "85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a"\n',
        'COMPARATOR_SOURCE_SHA256 = "85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a"\n'
        f'WAVELET_SOURCE_SHA256 = "{WAVELET_SOURCE_SHA256}"\n',
        "wavelet source hash",
    )
    source = replace_once(
        source,
        '    "dsh4_sparse_adaptation",\n)\n',
        '    "dsh4_sparse_adaptation",\n    "brown2010_wavelet_episode_core",\n)\n',
        "method registry",
    )

    freeze_start = source.index("def validate_freeze(path: Path) -> dict[str, Any]:\n")
    freeze_end = source.index("\ndef load_orbit_sidecars(\n", freeze_start)
    replacement_freeze = '''def validate_freeze(path: Path) -> dict[str, Any]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("verdict") != "PASS_SONOTACO_2025_WAVELET_EPISODE_COMPARISON":
        raise RuntimeError("invalid SonotaCo 2025 wavelet freeze verdict")
    if freeze.get("source_commit") != "97e3b1f99b08e6bd98e021c69e7b06d81f0500e1":
        raise RuntimeError("unexpected frozen wavelet source commit")
    if freeze.get("workflow_run") != 31104654956 or freeze.get("artifact_id") != 8969020016:
        raise RuntimeError("unexpected frozen wavelet workflow provenance")
    if freeze.get("result_sha256") != "526544fc39fd441fd73472c36e8d563b245728b3d33e858f0b1da11aa024070a":
        raise RuntimeError("unexpected frozen wavelet result hash")
    configuration = freeze.get("configuration", {})
    expected = {
        "angular_probe_deg": 4.0,
        "speed_probe_fraction": 0.10,
        "kernel": "(3-r^2)*exp(-r^2/2)",
        "truncation_radius": 4.0,
        "test_locations": "observed events",
        "self_contribution": "excluded",
        "episode_score": "maximum leave-one-out coefficient",
        "episode_size": 128,
        "parameter_tuning": False,
    }
    if configuration != expected:
        raise RuntimeError(f"wavelet configuration mismatch: {configuration}")
    if not freeze.get("frozen_before_sonotaco_2023_execution", False):
        raise RuntimeError("wavelet freeze does not predate SonotaCo 2023 execution")
    return freeze

'''
    source = source[:freeze_start] + replacement_freeze + source[freeze_end + 1:]

    source = replace_once(
        source,
        '        "sugar2017_core_transfer": literature.sugar_episode_score(episode, SUGAR_EPSILON),\n    }\n',
        '        "sugar2017_core_transfer": literature.sugar_episode_score(episode, SUGAR_EPSILON),\n'
        '        "brown2010_wavelet_episode_core": wavelet.wavelet_episode_score(episode),\n'
        '    }\n',
        "episode score",
    )
    source = replace_once(
        source,
        '    comparator_hash = sha256_bytes(Path(literature.__file__).read_bytes())\n'
        '    if comparator_hash != COMPARATOR_SOURCE_SHA256:\n'
        '        raise RuntimeError(f"comparator source changed after freeze: {comparator_hash}")\n',
        '    comparator_hash = sha256_bytes(Path(literature.__file__).read_bytes())\n'
        '    if comparator_hash != COMPARATOR_SOURCE_SHA256:\n'
        '        raise RuntimeError(f"comparator source changed after freeze: {comparator_hash}")\n'
        '    wavelet_hash = sha256_bytes(Path(wavelet.__file__).read_bytes())\n'
        '    if wavelet_hash != WAVELET_SOURCE_SHA256:\n'
        '        raise RuntimeError(f"wavelet source changed after freeze: {wavelet_hash}")\n',
        "source validation",
    )
    source = replace_once(
        source,
        '        "freeze_precedes_execution": freeze["frozen_before_sonotaco_2023_comparator_execution"] is True,\n'
        '        "comparator_source_exact": comparator_hash == COMPARATOR_SOURCE_SHA256,\n',
        '        "freeze_precedes_execution": freeze["frozen_before_sonotaco_2023_execution"] is True,\n'
        '        "comparator_source_exact": comparator_hash == COMPARATOR_SOURCE_SHA256,\n'
        '        "wavelet_source_exact": wavelet_hash == WAVELET_SOURCE_SHA256,\n',
        "freeze and source gates",
    )
    source = replace_once(
        source,
        '        "dsh_parameters_unchanged": (\n'
        '            literature.RUD2014_MIN_MEMBERS == 6\n'
        '            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4\n'
        '            and literature.RUD2014_DSH_THRESHOLD == 0.05\n'
        '        ),\n',
        '        "dsh_parameters_unchanged": (\n'
        '            literature.RUD2014_MIN_MEMBERS == 6\n'
        '            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4\n'
        '            and literature.RUD2014_DSH_THRESHOLD == 0.05\n'
        '        ),\n'
        '        "wavelet_parameters_unchanged": (\n'
        '            wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        '            and wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        '            and wavelet.TRUNCATION_RADIUS == 4.0\n'
        '            and wavelet.KERNEL_DIMENSION == 3.0\n'
        '            and all(wavelet.self_test().values())\n'
        '        ),\n',
        "wavelet parameter gate",
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
    print("PASS_BUILD_WAVELET_2023_RUNNER", digest)


if __name__ == "__main__":
    main()
