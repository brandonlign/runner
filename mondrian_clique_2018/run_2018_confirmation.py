#!/usr/bin/env python3
"""Verify the frozen data gate and exact passed source, then run 2018 once."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

INPUT = Path("input")
OUTPUT = Path("output")
SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
BASELINE_PAYLOAD_SHA256 = "2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2"
BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    audit = json.loads((INPUT / "audit.json").read_text(encoding="utf-8"))
    coverage = json.loads((INPUT / "coverage.json").read_text(encoding="utf-8"))
    if tuple(audit["configuration"]["years"]) != (2018,):
        raise RuntimeError("unexpected confirmation year")
    if not all(audit["gates"].values()) or not all(coverage["gates"].values()):
        raise RuntimeError("fresh 2018 data gate did not pass")

    parts = sorted(Path("mondrian_clique_development/source_parts_v2").glob("part*.b64"))
    expected = [f"part{index:02d}.b64" for index in range(4)]
    if [part.name for part in parts] != expected:
        raise RuntimeError(f"unexpected source parts: {[part.name for part in parts]}")
    encoded = "".join("".join(part.read_text().split()) for part in parts)
    if len(encoded) != 9000:
        raise RuntimeError(f"unexpected encoded source length: {len(encoded)}")
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    source_hash = hashlib.sha256(source).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise RuntimeError(f"confirmation source mismatch: {source_hash}")
    executable = Path("/tmp/run_mondrian_clique_2018.py")
    executable.write_bytes(source)
    subprocess.run([sys.executable, "-m", "py_compile", str(executable)], check=True)

    payload = Path("real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64")
    payload_hash = sha256(payload)
    if payload_hash != BASELINE_PAYLOAD_SHA256:
        raise RuntimeError(f"baseline payload mismatch: {payload_hash}")
    baseline_encoded = "".join(payload.read_text(encoding="utf-8").split())
    baseline_source = gzip.decompress(base64.b64decode(baseline_encoded, validate=True))
    baseline_hash = hashlib.sha256(baseline_source).hexdigest()
    if baseline_hash != BASELINE_SOURCE_SHA256:
        raise RuntimeError(f"baseline source mismatch: {baseline_hash}")

    print("selected events SHA-256:", sha256(INPUT / "selected_events.jsonl.gz"))
    print("audit SHA-256:", sha256(INPUT / "audit.json"))
    print("coverage SHA-256:", sha256(INPUT / "coverage.json"))
    print("confirmation source SHA-256:", source_hash)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(executable),
            "--events",
            str(INPUT / "selected_events.jsonl.gz"),
            "--year",
            "2018",
            "--corpus",
            "complete-year-2018-confirmation",
            "--workers",
            "4",
            "--baseline-payload",
            str(payload),
            "--output",
            str(OUTPUT),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
