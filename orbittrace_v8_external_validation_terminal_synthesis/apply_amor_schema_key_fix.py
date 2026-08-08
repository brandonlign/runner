#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_GIT_BLOB_SHA = "11f7cb3fb4e372701f5da40f62102eeafa5f1c5a"
NEEDLE = 'amor["orbit_read_audit"]["orbital_elements_interpreted_only_after_rank_freeze"]'
REPLACEMENT = 'amor["orbital_read_audit"]["orbital_elements_interpreted_only_after_rank_freeze"]'


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()

    raw = a.source.read_bytes()
    if git_blob_sha(raw) != EXPECTED_GIT_BLOB_SHA:
        raise RuntimeError("terminal synthesizer source blob changed")
    text = raw.decode("utf-8")
    if text.count(NEEDLE) != 1:
        raise RuntimeError("expected AMOR audit-key typo exactly once")
    if REPLACEMENT in text:
        raise RuntimeError("source already contains corrected AMOR key")
    corrected = text.replace(NEEDLE, REPLACEMENT)
    if corrected.count(REPLACEMENT) != 1 or NEEDLE in corrected:
        raise RuntimeError("AMOR key correction was not exact")

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(corrected, encoding="utf-8")
    print(f"source_git_blob_sha={EXPECTED_GIT_BLOB_SHA}")
    print(f"corrected_sha256={hashlib.sha256(corrected.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
