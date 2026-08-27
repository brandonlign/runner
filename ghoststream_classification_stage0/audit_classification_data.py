from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("audit_classification_data.py.gz.b64")
EXPECTED_BYTES = 21766
EXPECTED_SHA256 = "af48c4ecfe1151251cfe4d0bae7745544b92d0e2e040759498f26f706478d239"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    source_name = "ghoststream_classification_stage0/audit_classification_data_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
