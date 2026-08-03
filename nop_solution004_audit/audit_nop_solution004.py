from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("audit_nop_solution004.py.gz.b64")
EXPECTED_BYTES = 23613
EXPECTED_SHA256 = "1dca091f0cb5740057f8c583d944333b0bf2e00157d4845b9e850426134de1fb"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split()).rstrip("=")
    encoded += "=" * (-len(encoded) % 4)
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    source_name = "nop_solution004_audit/audit_nop_solution004_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
