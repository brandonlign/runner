#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path

EXPECTED_P12_SHA256 = "78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32"
EXPECTED_P13_SHA256 = "7e5800236e5a3ecc280cbae2513278e4a8bcb24db06f7c999f5e5674083b6834"
PATCH_PATH = Path(__file__).with_name("PATCH_B64.txt")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p13_patch.py EXACT_P12 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = sha(raw)
    if actual != EXPECTED_P12_SHA256:
        raise RuntimeError(f"exact P12 source SHA changed: {actual}")
    patches = json.loads(zlib.decompress(base64.b64decode(PATCH_PATH.read_text().strip(), validate=True)).decode("utf-8"))
    lines = raw.decode("utf-8").splitlines(keepends=True)
    for patch in sorted(patches, key=lambda item: int(item["s"]), reverse=True):
        lines[int(patch["s"]):int(patch["e"])] = str(patch["r"]).splitlines(keepends=True)
    text = "".join(lines)
    result = sha(text.encode("utf-8"))
    if result != EXPECTED_P13_SHA256:
        raise RuntimeError(f"P13 transform SHA mismatch: {result}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P13_INPUT_P12_SHA256={EXPECTED_P12_SHA256}")
    print(f"P13_OUTPUT_SHA256={result}")
    print("P13_PATCH_SCOPE=exact P12 proposals/assignments unchanged; freeze immutable v8 cores and exact P12 halos before truth, then separate discovery-core endpoints from halo membership endpoints without new thresholds or ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
