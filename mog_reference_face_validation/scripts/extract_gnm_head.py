"""Extract the neutral skin surface from Google's Apache-2.0 GNM Head model.

The upstream model archive is intentionally not committed to the runner. This
script downloads the pinned v3.0 archive during validation and writes a compact
skin-only template that can be inspected and rendered without the identity or
expression bases.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import urllib.request

import numpy as np

SOURCE_URL = (
    "https://github.com/google/GNM/raw/refs/heads/main/"
    "gnm/shape/data/versions/v3_0/gnm_head.npz"
)
LANDMARKS_URL = (
    "https://raw.githubusercontent.com/google/GNM/main/"
    "gnm/shape/data/landmarks/head_sparse_68.txt"
)
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "generated"
OUTPUT_MODEL = OUTPUT_DIR / "gnm_head_skin_template.npz"
OUTPUT_REPORT = OUTPUT_DIR / "gnm_head_skin_report.json"


def _as_strings(values: np.ndarray) -> list[str]:
    return [str(value) for value in values.tolist()]


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mog-reference-validation/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        destination.write_bytes(response.read())


def _load_landmarks(path: Path, vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    definition = np.loadtxt(path, dtype=np.float64)
    indices = definition[:, ::2].astype(np.int32)
    weights = definition[:, 1::2].astype(np.float32)
    if indices.shape != (68, 3) or weights.shape != (68, 3):
        raise ValueError(
            f"Unexpected GNM 68-point landmark definition: {indices.shape}, {weights.shape}"
        )
    if not np.allclose(weights.sum(axis=1), 1.0, atol=2e-3):
        raise ValueError("GNM landmark barycentric weights do not sum to one")
    positions = np.sum(vertices[indices] * weights[..., None], axis=1)
    return positions.astype(np.float32), indices, weights


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mog-gnm-") as temporary_dir:
        temporary = Path(temporary_dir)
        source_path = temporary / "gnm_head.npz"
        landmarks_path = temporary / "head_sparse_68.txt"
        _download(SOURCE_URL, source_path)
        _download(LANDMARKS_URL, landmarks_path)

        with np.load(source_path, allow_pickle=False) as model:
            vertices = np.asarray(model["template_vertex_positions"], dtype=np.float32)
            triangles = np.asarray(model["triangles"], dtype=np.int32)
            group_names = _as_strings(model["vertex_group_names"])
            group_weights = np.asarray(model["vertex_groups"], dtype=np.float32)
            mesh_component_names = _as_strings(model["mesh_component_names"])
            version = str(model["version"])
            variant = str(model["variant"])

        landmark_positions, landmark_indices, landmark_weights = _load_landmarks(
            landmarks_path,
            vertices,
        )

    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"Unexpected GNM vertex shape: {vertices.shape}")
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise ValueError(f"Unexpected GNM triangle shape: {triangles.shape}")
    if group_weights.ndim != 2 or group_weights.shape[1] != vertices.shape[0]:
        raise ValueError(
            "GNM vertex groups do not align with template vertices: "
            f"{group_weights.shape} vs {vertices.shape}"
        )
    if "skin" not in group_names:
        raise ValueError(f"GNM model has no skin vertex group: {group_names}")

    skin_weights = group_weights[group_names.index("skin")]
    skin_vertex_mask = skin_weights >= 0.5
    skin_triangle_mask = np.all(skin_vertex_mask[triangles], axis=1)
    skin_triangles_global = triangles[skin_triangle_mask]
    used_vertices = np.unique(skin_triangles_global.reshape(-1))

    remap = np.full(vertices.shape[0], -1, dtype=np.int32)
    remap[used_vertices] = np.arange(used_vertices.size, dtype=np.int32)
    compact_vertices = vertices[used_vertices]
    compact_triangles = remap[skin_triangles_global]
    compact_weights = skin_weights[used_vertices]

    np.savez_compressed(
        OUTPUT_MODEL,
        positions=compact_vertices,
        triangles=compact_triangles,
        source_vertex_indices=used_vertices,
        skin_weights=compact_weights,
        landmarks68=landmark_positions,
        landmark_source_indices=landmark_indices,
        landmark_barycentric_weights=landmark_weights,
    )

    minimum = compact_vertices.min(axis=0)
    maximum = compact_vertices.max(axis=0)
    report = {
        "source": SOURCE_URL,
        "landmarksSource": LANDMARKS_URL,
        "sourceLicense": "Apache-2.0",
        "version": version,
        "variant": variant,
        "sourceVertexCount": int(vertices.shape[0]),
        "sourceTriangleCount": int(triangles.shape[0]),
        "skinVertexCount": int(compact_vertices.shape[0]),
        "skinTriangleCount": int(compact_triangles.shape[0]),
        "landmarkCount": int(landmark_positions.shape[0]),
        "bounds": {
            "minimum": minimum.tolist(),
            "maximum": maximum.tolist(),
        },
        "meshComponentNames": mesh_component_names,
        "vertexGroupNames": group_names,
    }
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
