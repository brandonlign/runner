from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "generated/gnm_head_skin_template.npz"
OUTPUT = ROOT / "src/components/methodology/gnm-clay-renders.ts"
COMPONENT = ROOT / "src/components/methodology/canonical-clay-face.tsx"

PAPER = np.array([247, 244, 239], dtype=np.float64)
BASE = np.array([222, 213, 205], dtype=np.float64)


def vertex_normals(vertices: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(vertices, dtype=np.float64)
    a = vertices[triangles[:, 0]]
    b = vertices[triangles[:, 1]]
    c = vertices[triangles[:, 2]]
    faces = np.cross(b - a, c - a)
    faces /= np.maximum(np.linalg.norm(faces, axis=1)[:, None], 1e-12)
    for corner in range(3):
        np.add.at(normals, triangles[:, corner], faces)
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    return normals


def render(
    vertices: np.ndarray,
    triangles: np.ndarray,
    normals: np.ndarray,
    view: str,
    width: int = 1000,
    height: int = 1040,
) -> Image.Image:
    if view == "front":
        projected = np.column_stack((vertices[:, 0], vertices[:, 1]))
        depth = vertices[:, 2]
        projected_normals = normals
        light = np.array([-0.45, 0.50, 0.74], dtype=np.float64)
        x_min, x_max = -0.132, 0.132
    elif view == "profile":
        projected = np.column_stack((vertices[:, 2], vertices[:, 1]))
        depth = vertices[:, 0]
        projected_normals = np.column_stack((normals[:, 2], normals[:, 1], normals[:, 0]))
        light = np.array([0.55, 0.45, 0.70], dtype=np.float64)
        x_min, x_max = -0.100, 0.155
    else:
        raise ValueError(f"Unsupported view: {view}")

    light /= np.linalg.norm(light)
    y_min, y_max = 0.062, 0.414
    margin = 22
    scale = min(
        (width - 2 * margin) / (x_max - x_min),
        (height - 2 * margin) / (y_max - y_min),
    )
    pixels = np.column_stack((
        margin + (projected[:, 0] - x_min) * scale,
        height - margin - (projected[:, 1] - y_min) * scale,
    ))

    z_buffer = np.full((height, width), -np.inf, dtype=np.float64)
    rgb = np.empty((height, width, 3), dtype=np.float64)
    rgb[:] = PAPER

    for face_index in np.argsort(depth[triangles].mean(axis=1)):
        indices = triangles[face_index]
        points = pixels[indices]
        min_x = max(0, int(np.floor(points[:, 0].min())))
        max_x = min(width - 1, int(np.ceil(points[:, 0].max())))
        min_y = max(0, int(np.floor(points[:, 1].min())))
        max_y = min(height - 1, int(np.ceil(points[:, 1].max())))
        if max_x < min_x or max_y < min_y:
            continue

        x0, y0 = points[0]
        x1, y1 = points[1]
        x2, y2 = points[2]
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denominator) < 1e-9:
            continue

        yy, xx = np.mgrid[min_y:max_y + 1, min_x:max_x + 1]
        w0 = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / denominator
        w1 = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / denominator
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue

        candidate_depth = (
            w0 * depth[indices[0]]
            + w1 * depth[indices[1]]
            + w2 * depth[indices[2]]
        )
        z_region = z_buffer[min_y:max_y + 1, min_x:max_x + 1]
        take = inside & (candidate_depth > z_region)
        if not take.any():
            continue

        interpolated = (
            w0[..., None] * projected_normals[indices[0]]
            + w1[..., None] * projected_normals[indices[1]]
            + w2[..., None] * projected_normals[indices[2]]
        )
        interpolated /= np.maximum(np.linalg.norm(interpolated, axis=2)[..., None], 1e-9)
        diffuse = np.abs(interpolated @ light)
        brightness = 0.70 + 0.25 * diffuse
        highlight = np.array([255, 252, 248], dtype=np.float64)
        colour = (
            BASE[None, None, :] * brightness[..., None]
            + highlight[None, None, :] * (1 - brightness[..., None]) * 0.48
        )

        z_region[take] = candidate_depth[take]
        rgb_region = rgb[min_y:max_y + 1, min_x:max_x + 1]
        rgb_region[take] = np.clip(colour[take], 0, 255)

    alpha = (z_buffer > -np.inf).astype(np.uint8) * 255
    rgba = np.dstack((rgb.astype(np.uint8), alpha))
    image = Image.fromarray(rgba, "RGBA")
    return image.resize((600, 624), Image.Resampling.LANCZOS)


def data_uri(image: Image.Image) -> str:
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, "WEBP", quality=90, method=6, lossless=False)
    return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def main() -> None:
    data = np.load(SOURCE)
    vertices = data["positions"].astype(np.float64)
    triangles = data["triangles"].astype(np.int32)
    normals = vertex_normals(vertices, triangles)
    front = data_uri(render(vertices, triangles, normals, "front"))
    profile = data_uri(render(vertices, triangles, normals, "profile"))

    OUTPUT.write_text(
        "/** Deterministic snapshots rendered from Google GNM v3.0, Apache-2.0. */\n"
        f'export const GNM_FRONT_WEBP = "{front}";\n'
        f'export const GNM_PROFILE_WEBP = "{profile}";\n'
    )
    COMPONENT.write_text(
        'import type { FacialLandmarks } from "@/lib/analysis/landmarks";\n'
        'import { GNM_FRONT_WEBP, GNM_PROFILE_WEBP } from "./gnm-clay-renders";\n\n'
        'type FaceView = "front" | "profile";\n\n'
        '/**\n'
        ' * Reproducible full-resolution Google GNM clay snapshot. The image is\n'
        ' * illustrative only; all scoring continues to use the separate canonical\n'
        ' * semantic landmarks shown in structure mode.\n'
        ' */\n'
        'export function CanonicalClayFace({ view }: { view: FaceView; landmarks: FacialLandmarks }) {\n'
        '  const href = view === "front" ? GNM_FRONT_WEBP : GNM_PROFILE_WEBP;\n'
        '  return (\n'
        '    <g aria-label={`Google GNM neutral clay ${view} illustration`}>\n'
        '      <image href={href} x="0" y="-2" width="600" height="624" preserveAspectRatio="xMidYMid meet" />\n'
        '    </g>\n'
        '  );\n'
        '}\n'
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size} bytes)")
    print(f"wrote {COMPONENT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
