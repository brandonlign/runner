#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path

EXPECTED_P11_SHA256 = "914913d0462ea6793af3836cef945f14a03cca205ac0755ed6cdadb63b8752f9"
EXPECTED_P12_SHA256 = "78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32"
PATCH_PATH = Path(__file__).with_name("PATCH_B64.txt")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p12_patch.py EXACT_P11 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = sha(raw)
    if actual != EXPECTED_P11_SHA256:
        raise RuntimeError(f"exact P11 source SHA changed: {actual}")
    patch_b64 = PATCH_PATH.read_text(encoding="utf-8").strip()
    patches = json.loads(zlib.decompress(base64.b64decode(patch_b64, validate=True)).decode("utf-8"))
    lines = raw.decode("utf-8").splitlines(keepends=True)
    for patch in sorted(patches, key=lambda item: int(item["s"]), reverse=True):
        lines[int(patch["s"]):int(patch["e"])] = str(patch["r"]).splitlines(keepends=True)
    text = "".join(lines)
    result = sha(text.encode("utf-8"))
    if result != EXPECTED_P12_SHA256:
        raise RuntimeError(f"P12 transform SHA mismatch: {result}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P12_INPUT_P11_SHA256={EXPECTED_P11_SHA256}")
    print(f"P12_OUTPUT_SHA256={result}")
    print("P12_PATCH_SCOPE=exact P11 with only static observation distance replaced by source-year-only linear drift-conditioned 3-D OAS Mahalanobis distance; inherited membership rules/gates unchanged except historical static-representation count assertions become rule-based recomputation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
