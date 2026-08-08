#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_INPUT_SHA256 = "90d431819212e97adbc272acfa3c34595dac411f2bfe7c14a1a53535d789a01d"
NEEDLE = '''                if selected_months[year]:
                    require(month > selected_months[year][-1], f"non-monotonic selected month order in {year}: {month}")
                selected_months[year].append(month)
'''
REPLACEMENT = '''                selected_months[year].append(month)
'''


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()

    raw = a.source.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"Zenodo-corrected intermediate runner SHA-256 changed: {actual}")
    text = raw.decode("utf-8")
    if text.count(NEEDLE) != 1:
        raise RuntimeError(f"expected archive-order assertion block exactly once, found {text.count(NEEDLE)}")
    corrected = text.replace(NEEDLE, REPLACEMENT)
    if NEEDLE in corrected or corrected.count(REPLACEMENT) < 1:
        raise RuntimeError("archive-order correction was not exact")

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(corrected, encoding="utf-8")
    print(f"input_sha256={EXPECTED_INPUT_SHA256}")
    print(f"corrected_sha256={hashlib.sha256(corrected.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
