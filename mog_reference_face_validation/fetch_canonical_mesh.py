from __future__ import annotations

import json
import pathlib
import urllib.request

SOURCE = (
    "https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/"
    "mediapipe/modules/face_geometry/data/canonical_face_model.obj"
)
OUTPUT = pathlib.Path("mog_reference_face_validation/generated/canonical_face_model.json")
NOTICE = pathlib.Path("mog_reference_face_validation/generated/MEDIAPIPE_CANONICAL_FACE_NOTICE.txt")


def parse_obj(text: str) -> tuple[list[float], list[int]]:
    positions: list[float] = []
    triangles: list[int] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            positions.extend((round(float(x), 6), round(float(y), 6), round(float(z), 6)))
        elif line.startswith("f "):
            refs = line.split()[1:]
            indices = [int(ref.split("/")[0]) - 1 for ref in refs]
            if len(indices) < 3:
                continue
            for offset in range(1, len(indices) - 1):
                triangles.extend((indices[0], indices[offset], indices[offset + 1]))

    if len(positions) != 468 * 3:
        raise RuntimeError(f"Expected 468 vertices, got {len(positions) // 3}")
    if not triangles:
        raise RuntimeError("No triangles parsed")
    if max(triangles) >= 468 or min(triangles) < 0:
        raise RuntimeError("Triangle index outside canonical vertex range")
    return positions, triangles


def main() -> None:
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "mog-mesh-vendor/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8")

    positions, triangles = parse_obj(text)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "source": SOURCE,
                "license": "Apache-2.0",
                "vertexCount": len(positions) // 3,
                "triangleCount": len(triangles) // 3,
                "positions": positions,
                "triangles": triangles,
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    NOTICE.write_text(
        "MediaPipe canonical face model\n"
        f"Source: {SOURCE}\n"
        "Copyright Google LLC\n"
        "Licensed under the Apache License, Version 2.0.\n"
        "https://www.apache.org/licenses/LICENSE-2.0\n",
        encoding="utf-8",
    )
    print(
        f"wrote {OUTPUT}: {len(positions) // 3} vertices, "
        f"{len(triangles) // 3} triangles"
    )


if __name__ == "__main__":
    main()
