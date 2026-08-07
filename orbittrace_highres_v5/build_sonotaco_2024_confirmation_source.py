#!/usr/bin/env python3
"""Adapt the validated SonotaCo-2023 parser to audited 2024 transport constants."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_2023_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"
YEAR = 2024
CORPUS = "sonotaco-2024-v5-prospective-validation"
ARCHIVE_SHA256 = "409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f"
MEMBER = "024a/_U2_20240101_S.csv"
MEMBER_SHA256 = "0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00"
EXPECTED_ROWS = 38_793
TRANSPORT_AUDIT_RUN = 31151995231
TRANSPORT_AUDIT_ARTIFACT = 8983637946
TRANSPORT_AUDIT_ARTIFACT_SHA256 = "28a22bd618aba1057f67bcfbe2cd810fb6230097a53ab61e61431c62cc14655c"


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
        ("YEAR = 2023", "YEAR = 2024", "year"),
        (
            'CORPUS = "sonotaco-2023-fixed4-confirmation"',
            f'CORPUS = "{CORPUS}"',
            "corpus",
        ),
        (
            'ARCHIVE_SHA256 = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"',
            f'ARCHIVE_SHA256 = "{ARCHIVE_SHA256}"',
            "archive hash",
        ),
        (
            'MEMBER = "023a/_U2_20230101_S.csv"',
            f'MEMBER = "{MEMBER}"',
            "member",
        ),
        (
            'MEMBER_SHA256 = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"',
            f'MEMBER_SHA256 = "{MEMBER_SHA256}"',
            "member hash",
        ),
        ("EXPECTED_ROWS = 47_087", f"EXPECTED_ROWS = {EXPECTED_ROWS:_}", "row count"),
        ("def parse_sonotaco_2023_events(", "def parse_sonotaco_2024_events(", "parser function"),
        ('f"SNM2023:{row_index}"', 'f"SNM2024:{row_index}"', "event ids"),
        (
            "required unique SonotaCo 2023 fields are unavailable",
            "required unique SonotaCo 2024 fields are unavailable",
            "schema error label",
        ),
    )
    for old, new, label in replacements:
        source = replace_once(source, old, new, label)
    compile(source, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    output_digest = hashlib.sha256(source.encode()).hexdigest()
    print("PASS_BUILD_SONOTACO_2024_CONFIRMATION_SOURCE", output_digest)


if __name__ == "__main__":
    main()