from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/components/methodology"
OUTPUT = ROOT / "public/reference"


def read_chunk(path: Path, constant: str) -> str:
    text = path.read_text()
    match = re.fullmatch(rf'export const {constant} = "([A-Za-z0-9+/=]+)";\n?', text)
    if not match:
        raise RuntimeError(f"Unexpected chunk format: {path}")
    return match.group(1)


def export(prefix: str, count: int, output_name: str) -> None:
    payload = "".join(
        read_chunk(SOURCE / f"gnm-clay-{prefix}-{index}.ts", f"GNM_CLAY_{prefix.upper()}_{index}")
        for index in range(1, count + 1)
    )
    decoded = base64.b64decode(payload, validate=True)
    if decoded[:4] != b"RIFF" or decoded[8:12] != b"WEBP":
        raise RuntimeError(f"{prefix} payload is not a WebP image")
    path = OUTPUT / output_name
    path.write_bytes(decoded)
    print(f"wrote {path.relative_to(ROOT)}: {len(decoded)} bytes")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    export("front", 5, "gnm-front.webp")
    export("profile", 3, "gnm-profile.webp")


if __name__ == "__main__":
    main()
