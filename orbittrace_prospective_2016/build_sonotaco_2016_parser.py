#!/usr/bin/env python3
"""Build a SonotaCo-2016 parser from the already validated repaired 2023 parser source.

This is transport adaptation only. It changes year/archive/member identifiers and
expected transport constants; parsing/filtering/label mapping logic remains intact.
The prospective eligibility gates are frozen separately before this parser is run.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

YEAR = 2016
ARCHIVE_SHA256 = "f1fc4586d3efe71b9dc419261c9ad252c5d4f12e80439e94b56c86445520e530"
MEMBER = "016a/_U2_20160101_S.csv"
MEMBER_SHA256 = "6035614d6aa663f0ab0ed63e8e93f439d6e3969307085fc872eb2aaeff79be1f"
EXPECTED_ROWS = 22943


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source-2023", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def replace_exact(source: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} replacements, found {count}")
    return source.replace(old, new)


def main() -> None:
    args = parse_args()
    source = args.source_2023.read_text()
    source = replace_exact(source, "YEAR = 2023", "YEAR = 2016", "year constant")
    source = replace_exact(source, 'CORPUS = "sonotaco-2023-native"', 'CORPUS = "sonotaco-2016-prospective"', "corpus")
    source = replace_exact(source, 'ARCHIVE_SHA256 = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"', f'ARCHIVE_SHA256 = "{ARCHIVE_SHA256}"', "archive hash")
    source = replace_exact(source, 'MEMBER = "023a/_U2_20230101_S.csv"', f'MEMBER = "{MEMBER}"', "member path")
    source = replace_exact(source, 'MEMBER_SHA256 = "9de17f4c99f6de0ec3bdc88268964ec41b7fcf74d35b7a1c614a54d2aa44ed1c"', f'MEMBER_SHA256 = "{MEMBER_SHA256}"', "member hash")
    source = replace_exact(source, "EXPECTED_ROWS = 47087", f"EXPECTED_ROWS = {EXPECTED_ROWS}", "row count")
    source = source.replace("parse_sonotaco_2023_events", "parse_sonotaco_2016_events")
    source = source.replace("SNM2023:", "SNM2016:")
    source = source.replace("SonotaCo 2023", "SonotaCo 2016")
    source = source.replace("sonotaco_2023", "sonotaco_2016")
    source = source.replace("2023 parser", "2016 parser")
    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source)
    print("PASS_BUILD_SONOTACO_2016_PARSER", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
