#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_GIT_BLOB_SHA = "2c04a1be4134ee07162b60e3168c6f1684299cf3"
NEEDLE = '(f.get("links") or {}).get("content", "")'
REPLACEMENT = '((f.get("links") or {}).get("content") or (f.get("links") or {}).get("self") or "")'


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()

    raw = a.source.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_GIT_BLOB_SHA:
        raise RuntimeError(f"frozen geometry runner blob changed: {actual}")
    text = raw.decode("utf-8")
    if text.count(NEEDLE) != 1:
        raise RuntimeError(f"expected Zenodo link expression exactly once, found {text.count(NEEDLE)}")
    if REPLACEMENT in text:
        raise RuntimeError("source already contains Zenodo link-schema correction")
    corrected = text.replace(NEEDLE, REPLACEMENT)
    if corrected.count(REPLACEMENT) != 1 or NEEDLE in corrected:
        raise RuntimeError("Zenodo link-schema correction was not exact")

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(corrected, encoding="utf-8")
    print(f"source_git_blob_sha={EXPECTED_GIT_BLOB_SHA}")
    print(f"corrected_sha256={hashlib.sha256(corrected.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
