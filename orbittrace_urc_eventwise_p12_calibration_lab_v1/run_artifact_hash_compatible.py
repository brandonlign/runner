#!/usr/bin/env python3
"""Transport-only adapter for the frozen P12 artifact hash convention.

P12 records the SHA-256 of the decompressed decisions JSON in its scientific result and
`.sha256` sidecar. The development lab consumes the canonical `.json.gz` container. Override
only the local provenance helper for that one file so the scientific source verifies the exact
published decompressed hash before opening the unchanged gzip payload.
"""
from __future__ import annotations

import gzip
import hashlib
from pathlib import Path

from orbittrace_urc_eventwise_p12_calibration_lab_v1 import run_lab as lab

_original_sha = lab.sha


def _compatible_sha(path: Path) -> str:
    if path.name == "p12_decisions_pretruth.json.gz":
        return hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()
    return _original_sha(path)


lab.sha = _compatible_sha

if __name__ == "__main__":
    raise SystemExit(lab.main())
