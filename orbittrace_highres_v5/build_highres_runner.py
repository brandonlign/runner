#!/usr/bin/env python3
"""Patch an already-adapted v3 episode benchmark to use 512 calibration nulls.

The patch is intentionally narrow: it changes only the calibration-panel size
from 128 to 512 and makes the existing episode-count integrity gate depend on
the frozen supported-bin count. Scoring functions, sampling namespaces, held-
out negatives, positives, and all method definitions remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

OLD_CALIBRATION = 128
NEW_CALIBRATION = 512


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one target, found {count}")
    return source.replace(old, new)


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    load_line = "    base, scorer, adapter, candidate = load_sources(args)\n"
    source = replace_once(
        source,
        load_line,
        load_line
        + "    if int(scorer.CALIBRATION_NEGATIVES_PER_BIN) != 128:\n"
        + "        raise RuntimeError(f'unexpected predecessor calibration size: {scorer.CALIBRATION_NEGATIVES_PER_BIN}')\n"
        + "    scorer.CALIBRATION_NEGATIVES_PER_BIN = 512\n",
        "calibration override",
    )

    source, count = re.subn(
        r"len\(calibration_rows\) == \d+",
        "len(calibration_rows) == len(supported_bins) * scorer.CALIBRATION_NEGATIVES_PER_BIN",
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"episode-count calibration target: expected one replacement, found {count}")

    fixed4_gate = '        "fixed4_auc_reproduced": close(metrics["orbittrace_fixed4"]["weak_auc"], EXPECTED_FIXED4_WEAK_AUC),\n'
    source = replace_once(
        source,
        fixed4_gate,
        '        "high_resolution_calibration_exact_512": scorer.CALIBRATION_NEGATIVES_PER_BIN == 512,\n'
        + fixed4_gate,
        "high-resolution integrity gate",
    )

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_HIGHRES_V5_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()