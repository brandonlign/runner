from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("run_complex_set_model.py.gz.b64")
EXPECTED_BYTES = 31880
EXPECTED_SHA256 = "2aae9593130b9d16716a1f0aa4336fde8c99628ea0b53bbdb76883fdcbf8ad30"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    source_name = "real_shower_set_model_stage0/run_complex_set_model_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
