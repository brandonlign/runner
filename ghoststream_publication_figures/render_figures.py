from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

EXPECTED_SOURCE_SHA256 = "dd47308762ed1a8ba418b1677d2a72c1bb49a5775919af1696b1bd49d2d2e4c1"
EXPECTED_SOURCE_BYTES = 18_973


def main() -> None:
    root = Path(__file__).resolve().parent
    parts = sorted((root / "source_parts").glob("part*.b64"))
    if [path.name for path in parts] != ["part00.b64", "part01.b64", "part02.b64"]:
        raise RuntimeError(f"unexpected renderer payload inventory: {[path.name for path in parts]}")

    encoded = "".join("".join(path.read_text(encoding="ascii").split()) for path in parts)
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if len(source) != EXPECTED_SOURCE_BYTES:
        raise RuntimeError(f"renderer source byte mismatch: {len(source)}")
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"renderer source SHA-256 mismatch: {digest}")

    filename = str(root / "decoded_render_figures.py")
    code = compile(source, filename, "exec")
    namespace = {"__name__": "__main__", "__file__": filename}
    exec(code, namespace)


if __name__ == "__main__":
    main()
