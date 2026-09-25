from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

PAYLOAD = Path(__file__).with_name("run_static_population.py.gz.b64")
EXPECTED_BYTES = 28683
EXPECTED_SHA256 = "4890dc043b7103a1749f3f11d2a2a4e913eae91f7f15bcad3872e33166b4b2eb"


def main() -> None:
    encoded = "".join(PAYLOAD.read_text(encoding="ascii").split()).rstrip("=")
    encoded += "=" * (-len(encoded) % 4)
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES:
        raise RuntimeError(f"Source size mismatch: expected {EXPECTED_BYTES}, got {len(raw)}")
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    source_name = "ghoststream_static_population_stage0/run_static_population_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
