from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("run_transport_screen.py.gz.b64")
EXPECTED_BYTES = 10719
EXPECTED_SHA256 = "582cc2a2362d2033662b857207fa14861eef2c465071a272f329c9a03de1799e"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    name = "cross_year_transport_stage0/run_transport_screen_source.py"
    namespace = {"__name__": "__main__", "__file__": name}
    exec(compile(raw, name, "exec"), namespace)


if __name__ == "__main__":
    main()
