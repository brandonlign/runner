#!/usr/bin/env python3
"""Adapt the validated SonotaCo-2023 parser to audited 2018 transport constants."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_2023_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"
YEAR = 2018
CORPUS = "sonotaco-2018-v6-prospective-validation"
ARCHIVE_SHA256 = "ace35a8842c7af730b08da5cf491377b02d3f962c8185fe2f542c68d28e4ab55"
MEMBER = "018a/_U2_20180101_S.csv"
MEMBER_SHA256 = "11d40ba865d56523c6c070f8afb9a0ddbd80c578fd163ef12b55daf0ab61d167"
EXPECTED_ROWS = 29_720
TRANSPORT_AUDIT_RUN = 31154842808
TRANSPORT_AUDIT_ARTIFACT = 8984722695
TRANSPORT_AUDIT_ARTIFACT_SHA256 = "ebeea7fc3c8f9e118b5fed780ab7ec71e2b742a954a274931e3f4773739ba589"


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
        raise RuntimeError(f"validated 2023 parser source mismatch: {digest}")
    source = payload.decode("utf-8")
    replacements = (
        ("YEAR = 2023", "YEAR = 2018", "year"),
        ('CORPUS = "sonotaco-2023-fixed4-confirmation"', f'CORPUS = "{CORPUS}"', "corpus"),
        ('ARCHIVE_SHA256 = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"', f'ARCHIVE_SHA256 = "{ARCHIVE_SHA256}"', "archive hash"),
        ('MEMBER = "023a/_U2_20230101_S.csv"', f'MEMBER = "{MEMBER}"', "member"),
        ('MEMBER_SHA256 = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"', f'MEMBER_SHA256 = "{MEMBER_SHA256}"', "member hash"),
        ("EXPECTED_ROWS = 47_087", f"EXPECTED_ROWS = {EXPECTED_ROWS:_}", "row count"),
        ("def parse_sonotaco_2023_events(", "def parse_sonotaco_2018_events(", "parser function"),
        ('f"SNM2023:{row_index}"', 'f"SNM2018:{row_index}"', "event ids"),
        ("required unique SonotaCo 2023 fields are unavailable", "required unique SonotaCo 2018 fields are unavailable", "schema error label"),
    )
    for old, new, label in replacements:
        source = replace_once(source, old, new, label)
    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print("PASS_BUILD_SONOTACO_2018_CONFIRMATION_SOURCE", hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
