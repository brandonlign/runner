#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_INPUT_SHA256 = "067cc026dcb8aa077b432156aae52de5fa35b1cd05cb25f8051195ba4c3cf840"
NEEDLE = '    require("no orbittrace target information" in claim.lower(), f"{label}: no target-free claim found")\n'
REPLACEMENT = '''    claim_lower = claim.lower()\n    require(\n        "no orbittrace target information" in claim_lower\n        or "no source label or orbittrace target information entered" in claim_lower,\n        f"{label}: no target-free claim found",\n    )\n'''


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()

    raw = a.source.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"intermediate synthesizer SHA-256 changed: {actual}")
    text = raw.decode("utf-8")
    if text.count(NEEDLE) != 1:
        raise RuntimeError("expected target-free claim assertion exactly once")
    if "no source label or orbittrace target information entered" in text.lower():
        raise RuntimeError("source already contains AMOR target-free wording")

    corrected = text.replace(NEEDLE, REPLACEMENT)
    if corrected.count("no source label or orbittrace target information entered") != 1:
        raise RuntimeError("AMOR target-free wording correction was not exact")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(corrected, encoding="utf-8")
    print(f"input_sha256={EXPECTED_INPUT_SHA256}")
    print(f"corrected_sha256={hashlib.sha256(corrected.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
