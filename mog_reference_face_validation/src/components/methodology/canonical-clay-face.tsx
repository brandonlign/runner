import { useMemo } from "react";
import type { FacialLandmarks, LandmarkId, Point2D } from "@/lib/analysis/landmarks";
import { decodeGnmHeadMesh, type GnmTriangle, type GnmVertex } from "./gnm-head-mesh";

type FaceView = "front" | "profile";
type SvgPoint = { x: number; y: number };
type ProjectedFace = { face: GnmTriangle; points: string; depth: number; fill: string };

const decodedMesh = decodeGnmHeadMesh();
const TOP_Y = Math.max(...decodedMesh.vertices.map((vertex) => vertex.y));
const BOTTOM_Y = Math.min(...decodedMesh.vertices.map((vertex) => vertex.y));
const BACK_Z = Math.min(...decodedMesh.vertices.map((vertex) => vertex.z));
const CHIN_VERTEX = decodedMesh.vertices[822];
const TIP_VERTEX = decodedMesh.vertices[892];

function requiredPoint(landmarks: FacialLandmarks, id: LandmarkId): Point2D {
  const point = landmarks.points[id];
  if (!point) throw new Error(`GNM clay face is missing ${id}`);
  return point;
}

function frontMap(point: Point2D): SvgPoint {
  return { x: 300 + (point.x - 500) * 0.46, y: 50 + point.y * 0.46 };
}

function profileMap(point: Point2D): SvgPoint {
  return { x: 120 + (point.x - 150) * 0.66, y: 45 + point.y * 0.46 };
}

function projectY(vertexY: number, chinTargetY: number): number {
  const topTargetY = 16;
  const bottomTargetY = 610;
  if (vertexY >= CHIN_VERTEX.y) {
    const faceScale = (chinTargetY - topTargetY) / (TOP_Y - CHIN_VERTEX.y);
    return topTargetY + (TOP_Y - vertexY) * faceScale;
  }
  const bodyScale = (bottomTargetY - chinTargetY) / (CHIN_VERTEX.y - BOTTOM_Y);
  return chinTargetY + (CHIN_VERTEX.y - vertexY) * bodyScale;
}

function normal(a: GnmVertex, b: GnmVertex, c: GnmVertex): GnmVertex {
  const ab = { x: b.x - a.x, y: b.y - a.y, z: b.z - a.z };
  const ac = { x: c.x - a.x, y: c.y - a.y, z: c.z - a.z };
  const cross = {
    x: ab.y * ac.z - ab.z * ac.y,
    y: ab.z * ac.x - ab.x * ac.z,
    z: ab.x * ac.y - ab.y * ac.x,
  };
  const length = Math.hypot(cross.x, cross.y, cross.z) || 1;
  return { x: cross.x / length, y: cross.y / length, z: cross.z / length };
}

function clayFill(face: GnmTriangle, view: FaceView): string {
  const n = normal(
    decodedMesh.vertices[face[0]],
    decodedMesh.vertices[face[1]],
    decodedMesh.vertices[face[2]],
  );
  const light = view === "front"
    ? { x: -0.36, y: 0.36, z: 0.86 }
    : { x: 0.78, y: 0.32, z: 0.54 };
  const diffuse = Math.abs(n.x * light.x + n.y * light.y + n.z * light.z);
  const brightness = Math.min(0.975, Math.max(0.79, 0.82 + diffuse * 0.145));
  return `rgb(${Math.round(brightness * 255)} ${Math.round(brightness * 249)} ${Math.round(brightness * 242)})`;
}

function polygonPoints(face: GnmTriangle, projected: SvgPoint[]): string {
  return face.map((index) => `${projected[index].x.toFixed(2)},${projected[index].y.toFixed(2)}`).join(" ");
}

function buildFrontFaces(landmarks: FacialLandmarks): ProjectedFace[] {
  const chinTarget = frontMap(requiredPoint(landmarks, "menton"));
  const projected = decodedMesh.vertices.map((vertex) => ({
    x: 300 + vertex.x * 2180,
    y: projectY(vertex.y, chinTarget.y),
  }));
  return decodedMesh.triangles
    .map((face) => ({
      face,
      points: polygonPoints(face, projected),
      depth: (decodedMesh.vertices[face[0]].z + decodedMesh.vertices[face[1]].z + decodedMesh.vertices[face[2]].z) / 3,
      fill: clayFill(face, "front"),
    }))
    .sort((a, b) => a.depth - b.depth);
}

function buildProfileFaces(landmarks: FacialLandmarks): ProjectedFace[] {
  const chinTarget = profileMap(requiredPoint(landmarks, "menton"));
  const tipTarget = profileMap(requiredPoint(landmarks, "pronasale"));
  const backTargetX = 74;
  const horizontalScale = (tipTarget.x - backTargetX) / (TIP_VERTEX.z - BACK_Z);
  const projected = decodedMesh.vertices.map((vertex) => ({
    x: tipTarget.x + (vertex.z - TIP_VERTEX.z) * horizontalScale,
    y: projectY(vertex.y, chinTarget.y),
  }));
  return decodedMesh.triangles
    .map((face) => ({
      face,
      points: polygonPoints(face, projected),
      depth: (decodedMesh.vertices[face[0]].x + decodedMesh.vertices[face[1]].x + decodedMesh.vertices[face[2]].x) / 3,
      fill: clayFill(face, "profile"),
    }))
    .sort((a, b) => a.depth - b.depth);
}

function GnmClayMesh({ view, landmarks }: { view: FaceView; landmarks: FacialLandmarks }) {
  const faces = useMemo(
    () => view === "front" ? buildFrontFaces(landmarks) : buildProfileFaces(landmarks),
    [view, landmarks],
  );
  return (
    <g aria-label={`Google GNM neutral clay ${view} illustration`}>
      {faces.map(({ face, points, fill }, index) => (
        <polygon
          key={`${face[0]}-${face[1]}-${face[2]}-${index}`}
          points={points}
          fill={fill}
          stroke="rgba(117, 105, 96, 0.035)"
          strokeWidth="0.16"
          strokeLinejoin="round"
        />
      ))}
    </g>
  );
}

/**
 * Illustrative neutral clay surface aligned to the canonical scoring frame.
 * Only the semantic landmarks passed into the structure renderer enter Mog's
 * measurements; GNM surface vertices never enter the score.
 */
export function CanonicalClayFace({ view, landmarks }: { view: FaceView; landmarks: FacialLandmarks }) {
  return <GnmClayMesh view={view} landmarks={landmarks} />;
}
