from __future__ import annotations

import base64
import gzip
import hashlib
import runpy
import sys
from pathlib import Path

EXPECTED_SIZE = 32787
EXPECTED_SHA256 = "9e5aff4130b416c3b12d8b05bc88c8591adfd0b968bb454f6ffcfd7ef81e56e7"
ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "run_stage0.py.gz.b64"
EXTRACTED = ROOT / "_run_stage0_extracted.py"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if len(source) != EXPECTED_SIZE:
        raise SystemExit(f"Source size mismatch: expected {EXPECTED_SIZE}, got {len(source)}")
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    EXTRACTED.write_bytes(source)
    print(f"Verified InvariantStreamNet Stage-0 source: bytes={len(source)} sha256={digest}")
    sys.argv[0] = str(EXTRACTED)
    runpy.run_path(str(EXTRACTED), run_name="__main__")


if __name__ == "__main__":
    main()
