from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

EXPECTED_SOURCE_SHA256 = "a6db19832075e05689a0870681fee6840801453783809d2a45d5174adfd06643"
EXPECTED_SOURCE_BYTES = 43598
EXPECTED_PARTS = ["part00.b64", "part01.b64", "part02.b64"]


def main() -> None:
    root = Path(__file__).resolve().parent
    parts = sorted((root / "source_parts").glob("part*.b64"))
    if [path.name for path in parts] != EXPECTED_PARTS:
        raise RuntimeError(f"unexpected renderer payload inventory: {[path.name for path in parts]}")
    encoded = "".join("".join(path.read_text(encoding="ascii").split()) for path in parts)
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if len(source) != EXPECTED_SOURCE_BYTES:
        raise RuntimeError(f"renderer source byte mismatch: {len(source)}")
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"renderer source SHA-256 mismatch: {digest}")
    decoded_path = root / "decoded_render_figures.py"
    decoded_path.write_bytes(source)
    filename = str(decoded_path)
    namespace = {"__name__": "__main__", "__file__": filename}
    exec(compile(source, filename, "exec"), namespace)


if __name__ == "__main__":
    main()
