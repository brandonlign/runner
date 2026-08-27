from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("run_baseline_ceiling.py.gz.b64")
EXPECTED_BYTES = 25253
EXPECTED_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    source_name = "real_shower_meta_stage0/run_baseline_ceiling_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
