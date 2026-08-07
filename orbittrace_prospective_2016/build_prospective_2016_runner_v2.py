#!/usr/bin/env python3
"""Robust transport-only builder for the frozen SonotaCo-2016 prospective runner.

Input is the exact validated SonotaCo-2023 benchmark runner after frozen Brown,
fixed4, v3 and ONLY the selected +0.50 v8 method have been attached. This builder
changes only year/transport/eligibility constants and converts historical-year
metric-equality gates into prospective finite-metric integrity gates. No detector,
calibration, threshold, candidate, or scientific acceptance rule is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

YEAR = 2016
CORPUS = "sonotaco-2016-prospective"
ARCHIVE_SHA256 = "f1fc4586d3efe71b9dc419261c9ad252c5d4f12e80439e94b56c86445520e530"
MEMBER = "016a/_U2_20160101_S.csv"
MEMBER_SHA256 = "6035614d6aa663f0ab0ed63e8e93f439d6e3969307085fc872eb2aaeff79be1f"
PARSER_SHA256 = "96035178fba30ecbfcbc53e35745b2032417ee9989a850009aeddb0041150cf2"
SUPPORTED_BINS = (0,1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35)
ELIGIBLE_SHOWERS = 30
CALIBRATION_ROWS = 4224
NEGATIVE_ROWS = 2112
POSITIVE_ROWS = 480
SELECTED = "orbittrace_v3_fixed4_offset_pos050_v8"
SELECTED_OFFSET = 0.50


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def regex_exact(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"{label}: expected one replacement, found {count}")
    return updated


def replace_exact(source: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} replacements, found {count}")
    return source.replace(old, new)


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    # The exact validated benchmark has one top-level constant for each transport item.
    # Match the shape, not a guessed historical literal value.
    source = regex_exact(source, r'^YEAR\s*=\s*\d+\s*$', f'YEAR = {YEAR}', 'year')
    source = regex_exact(source, r'^CORPUS\s*=\s*"[^"]+"\s*$', f'CORPUS = "{CORPUS}"', 'corpus')
    source = regex_exact(source, r'^MEMBER\s*=\s*"[^"]+"\s*$', f'MEMBER = "{MEMBER}"', 'member')
    source = regex_exact(source, r'^ARCHIVE_SHA256\s*=\s*"[0-9a-f]{64}"\s*$', f'ARCHIVE_SHA256 = "{ARCHIVE_SHA256}"', 'archive hash')
    source = regex_exact(source, r'^MEMBER_SHA256\s*=\s*"[0-9a-f]{64}"\s*$', f'MEMBER_SHA256 = "{MEMBER_SHA256}"', 'member hash')

    # Year-specific parser transport only.
    if 'parse_sonotaco_2023_events' not in source:
        raise RuntimeError('validated 2023 parser call missing')
    source = source.replace('parse_sonotaco_2023_events', 'parse_sonotaco_2016_events')
    source = source.replace('SNM2023:', 'SNM2016:')
    source = source.replace('SonotaCo 2023', 'SonotaCo 2016')
    source = source.replace('sonotaco_2023', 'sonotaco_2016')
    source = source.replace('SONOTACO_2023', 'SONOTACO_2016')

    # Freeze the detector-free eligibility universe. These replacements affect only
    # infrastructure assertions/count reporting, not episode generation.
    source = regex_exact(
        source,
        r'if len\(eligible_showers\) != \d+:',
        f'if len(eligible_showers) != {ELIGIBLE_SHOWERS}:',
        'eligible shower assertion',
    )
    source = re.sub(
        r'expected \d+ eligible showers',
        f'expected {ELIGIBLE_SHOWERS} eligible showers',
        source,
    )
    source = regex_exact(
        source,
        r'"eligible_showers_exact_\d+"\s*:\s*len\(eligible_showers\)\s*==\s*\d+,',
        f'"eligible_showers_exact_{ELIGIBLE_SHOWERS}": len(eligible_showers) == {ELIGIBLE_SHOWERS},',
        'eligible shower gate',
    )

    # The frozen 33-bin universe keeps 4224 calibration and 2112 held-out negatives;
    # 30 showers x 4 k values x 4 replicates gives 480 positives.
    source = regex_exact(
        source,
        r'"episode_counts_exact"\s*:\s*\(\s*len\(calibration_rows\)\s*==\s*\d+\s*and\s*len\(negative_rows\)\s*==\s*\d+\s*and\s*len\(positive_rows\)\s*==\s*\d+\s*\),',
        f'"episode_counts_exact": (len(calibration_rows) == {CALIBRATION_ROWS} and len(negative_rows) == {NEGATIVE_ROWS} and len(positive_rows) == {POSITIVE_ROWS}),',
        'episode count gate',
    )

    # Historical transfer runners deliberately reproduce known old-year AUCs. On a
    # prospective year those equality checks are invalid. Convert every such gate to
    # a finite-metric integrity check without touching the score or the external
    # prospective performance gates.
    gate_pattern = re.compile(
        r'"(?P<gate>[^"]*auc_reproduced)"\s*:\s*close\(metrics\["(?P<method>[^"]+)"\]\["weak_auc"\],\s*[^\n]+?\),'
    )
    seen_methods: list[str] = []
    def gate_replacement(match: re.Match[str]) -> str:
        method = match.group('method')
        seen_methods.append(method)
        safe = re.sub(r'[^a-zA-Z0-9]+', '_', method).strip('_')
        return f'"prospective_{safe}_auc_finite": bool(np.isfinite(metrics["{method}"]["weak_auc"])), '
    source, replacement_count = gate_pattern.subn(gate_replacement, source)
    if replacement_count < 4:
        raise RuntimeError(f'expected at least four historical AUC reproduction gates, replaced {replacement_count}: {seen_methods}')

    # Add exact prospective provenance next to metrics.
    marker = '        "metrics": metrics,\n'
    if source.count(marker) != 1:
        raise RuntimeError(f'result metrics marker count={source.count(marker)}')
    source = source.replace(
        marker,
        marker
        + '        "prospective_2016_freeze": {\n'
        + f'            "archive_sha256": "{ARCHIVE_SHA256}",\n'
        + f'            "member_sha256": "{MEMBER_SHA256}",\n'
        + f'            "parser_sha256": "{PARSER_SHA256}",\n'
        + f'            "supported_bins": {list(SUPPORTED_BINS)!r},\n'
        + f'            "eligible_showers": {ELIGIBLE_SHOWERS},\n'
        + f'            "calibration_rows": {CALIBRATION_ROWS},\n'
        + f'            "negative_rows": {NEGATIVE_ROWS},\n'
        + f'            "positive_rows": {POSITIVE_ROWS},\n'
        + f'            "selected_method": "{SELECTED}",\n'
        + f'            "selected_offset": {SELECTED_OFFSET:.2f},\n'
        + '        },\n',
        1,
    )

    # Prospective output naming only.
    source = source.replace('sonotaco_2023_literature_transfer.json', 'sonotaco_2016_prospective_benchmark.json')
    source = source.replace('SONOTACO_2023_LITERATURE_TRANSFER.md', 'SONOTACO_2016_PROSPECTIVE_BENCHMARK.md')
    source = source.replace('PASS_SONOTACO_2023_LITERATURE_TRANSFER', 'PASS_SONOTACO_2016_PROSPECTIVE_BENCHMARK_EXECUTION')
    source = source.replace('FAIL_SONOTACO_2023_LITERATURE_TRANSFER', 'FAIL_SONOTACO_2016_PROSPECTIVE_BENCHMARK_EXECUTION')

    # Prospective method-shopping firewall.
    rejected = (
        'orbittrace_v3_fixed4_offset_neg075_v8',
        'orbittrace_v3_fixed4_offset_neg050_v8',
        'orbittrace_v3_fixed4_offset_neg025_v8',
        'orbittrace_v3_fixed4_offset_000_v8',
        'orbittrace_v3_fixed4_offset_pos025_v8',
    )
    for candidate in rejected:
        if candidate in source:
            raise RuntimeError(f'development-only candidate leaked into prospective runner: {candidate}')
    if source.count(SELECTED) < 2:
        raise RuntimeError('selected v8 method missing from prospective runner')

    # No historical equality gate may survive.
    if 'auc_reproduced' in source:
        raise RuntimeError('historical AUC reproduction gate survived prospective transport')

    compile(source, str(args.output), 'exec')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print('PASS_BUILD_PROSPECTIVE_2016_RUNNER_V2', hashlib.sha256(source.encode()).hexdigest(), 'converted_auc_gates', replacement_count)


if __name__ == '__main__':
    main()
