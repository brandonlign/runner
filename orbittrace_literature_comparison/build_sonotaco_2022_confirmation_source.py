#!/usr/bin/env python3
"""Adapt the validated SonotaCo-2023 confirmation/parser source to 2022 transport constants."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_2023_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-2023", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one target, found {count}")
    return source.replace(old, new)


def main() -> None:
    args = parse_args()
    payload = args.source_2023.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SOURCE_2023_SHA256:
        raise RuntimeError(f"validated 2023 source mismatch: {digest}")
    source = payload.decode("utf-8")
    replacements = (
        ('YEAR = 2023', 'YEAR = 2022', 'year'),
        ('CORPUS = "sonotaco-2023-fixed4-confirmation"', 'CORPUS = "sonotaco-2022-hybrid-validation"', 'corpus'),
        ('ARCHIVE_SHA256 = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"', 'ARCHIVE_SHA256 = "94537246035322b466df8dc17e19ef08212433e2bda0a8fe3d53dc45ba7c747d"', 'archive hash'),
        ('MEMBER = "023a/_U2_20230101_S.csv"', 'MEMBER = "022a/_U2_20220101_S.csv"', 'member'),
        ('MEMBER_SHA256 = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"', 'MEMBER_SHA256 = "0fcaab867405cc010d9b1dbd6212d58c6461106475ce79c30cce5b5e8e4226d4"', 'member hash'),
        ('EXPECTED_ROWS = 47_087', 'EXPECTED_ROWS = 48_788', 'row count'),
        ('def parse_sonotaco_2023_events(', 'def parse_sonotaco_2022_events(', 'parser function'),
        ('f"SNM2023:{row_index}"', 'f"SNM2022:{row_index}"', 'event ids'),
    )
    for old, new, label in replacements:
        source = replace_once(source, old, new, label)
    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    output_digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_SONOTACO_2022_CONFIRMATION_SOURCE", output_digest)


if __name__ == "__main__":
    main()
