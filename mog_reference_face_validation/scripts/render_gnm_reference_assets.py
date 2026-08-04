from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "generated" / "gnm_head_skin_template.npz"
OUTPUT = ROOT / "generated"
RENDER_VERSION = "gnm-orthographic-clay-v1.0"


def _face_normals(positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    a = positions[triangles[:, 0]]
    b = positions[triangles[:, 1]]
    c = positions[triangles[:, 2]]
    normals = np.cross(b - a, c - a)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    return normals / np.maximum(lengths, 1e-12)


def _render(
    positions: np.ndarray,
    triangles: np.ndarray,
    normals: np.ndarray,
    view: str,
    destination: Path,
) -> None:
    if view == "front":
        projected = np.column_stack((positions[:, 0], positions[:, 1]))
        face_depth = positions[triangles].mean(axis=1)[:, 2]
        order = np.argsort(face_depth)
        bounds = (-0.145, 0.145, 0.075, 0.415)
        light = np.array([-0.35, 0.60, 0.72], dtype=np.float64)
    elif view == "profile":
        projected = np.column_stack((positions[:, 2], positions[:, 1]))
        face_depth = positions[triangles].mean(axis=1)[:, 0]
        order = np.argsort(face_depth)
        bounds = (-0.105, 0.160, 0.075, 0.415)
        light = np.array([0.55, 0.45, 0.70], dtype=np.float64)
    else:
        raise ValueError(view)

    # Remove only the source model's open lower shoulder fringe. The complete
    # cranium, ears, jaw, and neck remain visible in both views.
    eligible = positions[triangles].mean(axis=1)[:, 1] > 0.085
    order = order[eligible[order]]
    selected = triangles[order]
    selected_normals = normals[order]

    light /= np.linalg.norm(light)
    diffuse = np.clip(np.abs(selected_normals @ light), 0.0, 1.0)
    brightness = np.clip(0.74 + 0.24 * diffuse, 0.0, 1.0)
    colors = np.column_stack(
        (
            brightness,
            brightness * 0.985,
            brightness * 0.955,
            np.ones_like(brightness),
        )
    )

    figure = plt.figure(figsize=(6, 6), dpi=200)
    axes = figure.add_axes([0, 0, 1, 1])
    collection = PolyCollection(
        projected[selected],
        facecolors=colors,
        edgecolors=(0.42, 0.37, 0.34, 0.015),
        linewidths=0.05,
        antialiaseds=True,
    )
    axes.add_collection(collection)
    axes.set_aspect("equal")
    axes.set_xlim(bounds[0], bounds[1])
    axes.set_ylim(bounds[2], bounds[3])
    axes.axis("off")
    figure.patch.set_alpha(0)
    axes.patch.set_alpha(0)

    temporary_png = destination.with_suffix(".png")
    figure.savefig(temporary_png, transparent=True, bbox_inches=None, pad_inches=0)
    plt.close(figure)

    with Image.open(temporary_png) as image:
        image = image.convert("RGBA")
        image.thumbnail((760, 760), Image.Resampling.LANCZOS)
        image.save(destination, "WEBP", quality=82, method=6)
    temporary_png.unlink()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with np.load(MODEL, allow_pickle=False) as model:
        positions = np.asarray(model["positions"], dtype=np.float64)
        triangles = np.asarray(model["triangles"], dtype=np.int32)

    if positions.shape != (12466, 3):
        raise ValueError(f"Unexpected GNM skin vertex shape: {positions.shape}")
    if triangles.shape != (24820, 3):
        raise ValueError(f"Unexpected GNM skin triangle shape: {triangles.shape}")

    normals = _face_normals(positions, triangles)
    assets = {
        "front": OUTPUT / "gnm_reference_front.webp",
        "profile": OUTPUT / "gnm_reference_profile.webp",
    }
    for view, destination in assets.items():
        _render(positions, triangles, normals, view, destination)

    report = {
        "source": "Google GNM v3 head template, skin component",
        "sourceLicense": "Apache-2.0",
        "renderer": RENDER_VERSION,
        "vertexCount": int(positions.shape[0]),
        "triangleCount": int(triangles.shape[0]),
        "assets": {
            view: {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for view, path in assets.items()
        },
    }
    (OUTPUT / "gnm_reference_assets.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
