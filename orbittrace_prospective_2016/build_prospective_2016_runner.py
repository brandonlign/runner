#!/usr/bin/env python3
"""Transport the exact validated 2023 benchmark runner to the frozen 2016 universe.

Input is a runner that already contains Brown, fixed4, frozen v3, and ONLY the
selected +0.50 v8 method. This builder changes prospective year/transport/count
constants and removes historical-year metric-reproduction gates. It does not alter
any detector score, calibration rule, threshold, or comparator implementation.
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def replace_exact(source: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} replacements, found {count}")
    return source.replace(old, new)


def regex_one(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex replacement, found {count}")
    return updated


def main() -> None:
    args = parse_args()
    source = args.base.read_text()

    source = replace_exact(source, "YEAR = 2023", "YEAR = 2016", "year")
    source = replace_exact(source, 'CORPUS = "sonotaco-2023-fixed4-confirmation"', f'CORPUS = "{CORPUS}"', "corpus")
    source = replace_exact(source, 'MEMBER = "023a/_U2_20230101_S.csv"', f'MEMBER = "{MEMBER}"', "member")
    source = replace_exact(source, 'ARCHIVE_SHA256 = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"', f'ARCHIVE_SHA256 = "{ARCHIVE_SHA256}"', "archive hash")
    source = replace_exact(source, 'MEMBER_SHA256 = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"', f'MEMBER_SHA256 = "{MEMBER_SHA256}"', "member hash")

    source = source.replace("parse_sonotaco_2023_events", "parse_sonotaco_2016_events")
    source = source.replace("SNM2023:", "SNM2016:")
    source = source.replace("SonotaCo 2023", "SonotaCo 2016")
    source = source.replace("sonotaco_2023", "sonotaco_2016")
    source = source.replace("SONOTACO_2023", "SONOTACO_2016")

    # Freeze the eligibility-universe counts observed without detector scoring.
    source = source.replace("if len(eligible_showers) != 41:", "if len(eligible_showers) != 30:")
    source = source.replace("expected 41 eligible showers", "expected 30 eligible showers")
    source = source.replace('"eligible_showers_exact_41": len(eligible_showers) == 41,', '"eligible_showers_exact_30": len(eligible_showers) == 30,')
    source = source.replace("len(positive_rows) == 656", "len(positive_rows) == 480")

    # Historical 2023 score-reproduction assertions are inappropriate on a prospective year.
    historical_gate_patterns = {
        r'"fixed4_auc_reproduced":\s*close\(metrics\["orbittrace_fixed4"\]\["weak_auc"\],\s*EXPECTED_FIXED4_WEAK_AUC\),':
            '"prospective_fixed4_metric_finite": bool(np.isfinite(metrics["orbittrace_fixed4"]["weak_auc"])),',
        r'"internal_split_auc_reproduced":\s*close\(metrics\["internal_split"\]\["weak_auc"\],\s*EXPECTED_INTERNAL_AUC\["internal_split"\]\),':
            '"prospective_internal_split_metric_finite": bool(np.isfinite(metrics["internal_split"]["weak_auc"])),',
        r'"internal_density_auc_reproduced":\s*close\(metrics\["internal_density"\]\["weak_auc"\],\s*EXPECTED_INTERNAL_AUC\["internal_density"\]\),':
            '"prospective_internal_density_metric_finite": bool(np.isfinite(metrics["internal_density"]["weak_auc"])),',
        r'"internal_dbscan_auc_reproduced":\s*close\(metrics\["internal_dbscan"\]\["weak_auc"\],\s*EXPECTED_INTERNAL_AUC\["internal_dbscan"\]\),':
            '"prospective_internal_dbscan_metric_finite": bool(np.isfinite(metrics["internal_dbscan"]["weak_auc"])),',
    }
    for pattern, replacement in historical_gate_patterns.items():
        source = regex_one(source, pattern, replacement, "prospective metric gate")

    # Freeze expected prospective counts directly into infrastructure gates.
    source = regex_one(
        source,
        r'"episode_counts_exact":\s*\(\s*len\(calibration_rows\) == 4224\s*and len\(negative_rows\) == 2112\s*and len\(positive_rows\) == 480\s*\),',
        '"episode_counts_exact": (len(calibration_rows) == 4224 and len(negative_rows) == 2112 and len(positive_rows) == 480),',
        "episode count gate",
    )

    # Add exact prospective transport/parser/eligibility metadata to the result.
    marker = '        "metrics": metrics,\n'
    if marker not in source:
        raise RuntimeError("result metrics marker missing")
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
        + '            "selected_method": "orbittrace_v3_fixed4_offset_pos050_v8",\n'
        + '            "selected_offset": 0.50,\n'
        + '        },\n',
        1,
    )

    # Prospective output naming only; scientific evaluation happens in a separate frozen evaluator.
    source = source.replace("sonotaco_2023_literature_transfer.json", "sonotaco_2016_prospective_benchmark.json")
    source = source.replace("SONOTACO_2023_LITERATURE_TRANSFER.md", "SONOTACO_2016_PROSPECTIVE_BENCHMARK.md")
    source = source.replace("PASS_SONOTACO_2023_LITERATURE_TRANSFER", "PASS_SONOTACO_2016_PROSPECTIVE_BENCHMARK_EXECUTION")
    source = source.replace("FAIL_SONOTACO_2023_LITERATURE_TRANSFER", "FAIL_SONOTACO_2016_PROSPECTIVE_BENCHMARK_EXECUTION")

    # Verify no development-only v8 alternatives survived into the prospective runner.
    forbidden_candidates = (
        "orbittrace_v3_fixed4_offset_neg075_v8",
        "orbittrace_v3_fixed4_offset_neg050_v8",
        "orbittrace_v3_fixed4_offset_neg025_v8",
        "orbittrace_v3_fixed4_offset_000_v8",
        "orbittrace_v3_fixed4_offset_pos025_v8",
    )
    for candidate in forbidden_candidates:
        if candidate in source:
            raise RuntimeError(f"development-only v8 candidate leaked into prospective runner: {candidate}")
    if source.count("orbittrace_v3_fixed4_offset_pos050_v8") < 2:
        raise RuntimeError("selected v8 method missing from prospective runner")

    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_PROSPECTIVE_2016_RUNNER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
