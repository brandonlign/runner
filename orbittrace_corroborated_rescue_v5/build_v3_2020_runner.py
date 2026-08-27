#!/usr/bin/env python3
"""Add frozen OrbitTrace v3 scoring to the exact audited SonotaCo 2020 runner."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one target, found {count}")
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
        'WAVELET_ID = "brown2010_wavelet_episode_core"\nCOMPONENT_METHODS = (FIXED4_ID, WAVELET_ID)\n',
        'WAVELET_ID = "brown2010_wavelet_episode_core"\n'
        'V3_ID = "orbittrace_multi_anchor_wavelet_energy_v3"\n'
        'COMPONENT_METHODS = (FIXED4_ID, WAVELET_ID, V3_ID)\n',
        "component registry",
    )
    source = replace_once(
        source,
        '    wavelet_score = float(wavelet.wavelet_episode_score(episode))\n'
        '    scores = {FIXED4_ID: fixed4, WAVELET_ID: wavelet_score}\n',
        '    wavelet_score = float(wavelet.wavelet_episode_score(episode))\n'
        '    v3_score = float(v3.multi_anchor_energy_episode_score(episode))\n'
        '    scores = {FIXED4_ID: fixed4, WAVELET_ID: wavelet_score, V3_ID: v3_score}\n',
        "episode scores",
    )

    wavelet_gate = (
        '        "wavelet_rules_unchanged": (\n'
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
        + '        "v3_rules_unchanged": (\n'
        + '            v3.METHOD_ID == V3_ID\n'
        + '            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0\n'
        + '            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10\n'
        + '            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0\n'
        + '            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0\n'
        + '            and v3.TOP_ANCHORS == 4\n'
        + '            and all(v3.self_test().values())\n'
        + '        ),\n',
        "v3 source gate",
    )
    source = replace_once(
        source,
        '    metrics = {\n'
        '        FIXED4_ID: fixed4_metrics,\n'
        '        WAVELET_ID: wavelet_metrics,\n'
        '        DUAL_ID: dual_metrics,\n'
        '    }\n',
        '    v3_metrics = component_metrics[V3_ID]\n'
        '    metrics = {\n'
        '        FIXED4_ID: fixed4_metrics,\n'
        '        WAVELET_ID: wavelet_metrics,\n'
        '        V3_ID: v3_metrics,\n'
        '        DUAL_ID: dual_metrics,\n'
        '    }\n',
        "result metrics",
    )
    source = replace_once(
        source,
        '        f"| `{WAVELET_ID}` | {wavelet_metrics[\'weak_auc\']:.6f} | {wavelet_metrics[\'fpr_005\']:.6f} | {wavelet_metrics[\'worst_sector_fpr_005\']:.6f} |",\n'
        '        f"| `{DUAL_ID}` | {dual_metrics[\'weak_auc\']:.6f} | {dual_metrics[\'fpr_005\']:.6f} | {dual_metrics[\'worst_sector_fpr_005\']:.6f} |",\n',
        '        f"| `{WAVELET_ID}` | {wavelet_metrics[\'weak_auc\']:.6f} | {wavelet_metrics[\'fpr_005\']:.6f} | {wavelet_metrics[\'worst_sector_fpr_005\']:.6f} |",\n'
        '        f"| `{V3_ID}` | {v3_metrics[\'weak_auc\']:.6f} | {v3_metrics[\'fpr_005\']:.6f} | {v3_metrics[\'worst_sector_fpr_005\']:.6f} |",\n'
        '        f"| `{DUAL_ID}` | {dual_metrics[\'weak_auc\']:.6f} | {dual_metrics[\'fpr_005\']:.6f} | {dual_metrics[\'worst_sector_fpr_005\']:.6f} |",\n',
        "report table",
    )
    source = replace_once(
        source,
        '    for method, row in ((FIXED4_ID, fixed4_metrics), (WAVELET_ID, wavelet_metrics)):\n',
        '    for method, row in ((FIXED4_ID, fixed4_metrics), (WAVELET_ID, wavelet_metrics), (V3_ID, v3_metrics)):\n',
        "report recall loop",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_V3_2020_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
