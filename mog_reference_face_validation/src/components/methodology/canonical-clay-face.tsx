import type { FacialLandmarks, LandmarkId, Point2D } from "@/lib/analysis/landmarks";
import canonicalMesh from "../../../generated/canonical_face_model.json";

type FaceView = "front" | "profile";
type SvgPoint = { x: number; y: number };
type Vertex3 = { x: number; y: number; z: number };
type MeshData = { positions: number[]; triangles: number[] };

type Anchor = {
  vertex: number;
  target: SvgPoint;
};

const mesh = canonicalMesh as MeshData;
const vertices: Vertex3[] = Array.from(
  { length: mesh.positions.length / 3 },
  (_, index) => ({
    x: mesh.positions[index * 3],
    y: mesh.positions[index * 3 + 1],
    z: mesh.positions[index * 3 + 2],
  }),
);
const faces: [number, number, number][] = Array.from(
  { length: mesh.triangles.length / 3 },
  (_, index) => [
    mesh.triangles[index * 3],
    mesh.triangles[index * 3 + 1],
    mesh.triangles[index * 3 + 2],
  ],
);

function requiredPoint(landmarks: FacialLandmarks, id: LandmarkId): Point2D {
  const point = landmarks.points[id];
  if (!point) throw new Error(`Canonical clay face is missing ${id}`);
  return point;
}

function frontMap(point: Point2D): SvgPoint {
  return { x: 300 + (point.x - 500) * 0.46, y: 50 + point.y * 0.46 };
}

function profileMap(point: Point2D): SvgPoint {
  return { x: 120 + (point.x - 150) * 0.66, y: 45 + point.y * 0.46 };
}

function nearestAnchorDisplacement(
  point: SvgPoint,
  base: SvgPoint[],
  anchors: Anchor[],
  neighborCount: number,
  smoothing: number,
): SvgPoint {
  const ranked = anchors
    .map((anchor) => {
      const source = base[anchor.vertex];
      const dx = source.x - point.x;
      const dy = source.y - point.y;
      return { anchor, distanceSquared: dx * dx + dy * dy };
    })
    .sort((a, b) => a.distanceSquared - b.distanceSquared)
    .slice(0, neighborCount);

  let totalWeight = 0;
  let displacementX = 0;
  let displacementY = 0;
  for (const candidate of ranked) {
    const source = base[candidate.anchor.vertex];
    const weight = 1 / (candidate.distanceSquared + smoothing);
    totalWeight += weight;
    displacementX += (candidate.anchor.target.x - source.x) * weight;
    displacementY += (candidate.anchor.target.y - source.y) * weight;
  }

  return {
    x: point.x + displacementX / totalWeight,
    y: point.y + displacementY / totalWeight,
  };
}

function warpMesh(base: SvgPoint[], anchors: Anchor[], smoothing: number): SvgPoint[] {
  const exactTargets = new Map(anchors.map((anchor) => [anchor.vertex, anchor.target]));
  return base.map((point, index) =>
    exactTargets.get(index) ?? nearestAnchorDisplacement(point, base, anchors, 6, smoothing),
  );
}

function normal(a: Vertex3, b: Vertex3, c: Vertex3): Vertex3 {
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

function clayFill(face: [number, number, number], view: FaceView): string {
  const n = normal(vertices[face[0]], vertices[face[1]], vertices[face[2]]);
  const light = view === "front"
    ? { x: -0.25, y: 0.35, z: 0.9 }
    : { x: -0.7, y: 0.3, z: 0.5 };
  const brightness = Math.min(
    0.97,
    Math.max(0.7, 0.78 + Math.abs(n.x * light.x + n.y * light.y + n.z * light.z) * 0.17),
  );
  const red = Math.round(brightness * 255);
  const green = Math.round(brightness * 250);
  const blue = Math.round(brightness * 244);
  return `rgb(${red} ${green} ${blue})`;
}

function polygonPoints(face: [number, number, number], projected: SvgPoint[]): string {
  return face.map((index) => `${projected[index].x.toFixed(2)},${projected[index].y.toFixed(2)}`).join(" ");
}

function FrontClayMesh({ landmarks }: { landmarks: FacialLandmarks }) {
  const q = (id: LandmarkId) => frontMap(requiredPoint(landmarks, id));
  const trichion = q("trichion");
  const menton = q("menton");
  const leftCheek = q("leftZygion");
  const rightCheek = q("rightZygion");
  const top = vertices[10];
  const chin = vertices[152];
  const horizontalScale = (leftCheek.x - rightCheek.x) / (vertices[454].x - vertices[234].x);
  const verticalScale = (menton.y - trichion.y) / (top.y - chin.y);
  const centerX = (leftCheek.x + rightCheek.x) / 2;

  const base = vertices.map((vertex) => ({
    x: centerX + vertex.x * horizontalScale,
    y: trichion.y + (top.y - vertex.y) * verticalScale,
  }));
  const anchors: Anchor[] = [
    { vertex: 10, target: trichion },
    { vertex: 6, target: q("glabella") },
    { vertex: 197, target: q("nasion") },
    { vertex: 1, target: q("pronasale") },
    { vertex: 0, target: q("subnasale") },
    { vertex: 11, target: q("labialeSuperius") },
    { vertex: 13, target: q("stomion") },
    { vertex: 17, target: q("labialeInferius") },
    { vertex: 152, target: menton },
    { vertex: 454, target: leftCheek },
    { vertex: 234, target: rightCheek },
    { vertex: 397, target: q("leftGonion") },
    { vertex: 172, target: q("rightGonion") },
    { vertex: 356, target: q("leftFrontotemporale") },
    { vertex: 127, target: q("rightFrontotemporale") },
    { vertex: 362, target: q("leftEndocanthion") },
    { vertex: 263, target: q("leftExocanthion") },
    { vertex: 133, target: q("rightEndocanthion") },
    { vertex: 33, target: q("rightExocanthion") },
    { vertex: 327, target: q("leftAlare") },
    { vertex: 98, target: q("rightAlare") },
    { vertex: 291, target: q("leftCheilion") },
    { vertex: 61, target: q("rightCheilion") },
  ];
  const projected = warpMesh(base, anchors, 16);
  const orderedFaces = faces
    .map((face) => ({ face, depth: face.reduce((sum, index) => sum + vertices[index].z, 0) / 3 }))
    .sort((a, b) => a.depth - b.depth);

  return (
    <g aria-label="Canonical clay front face">
      {orderedFaces.map(({ face }, index) => (
        <polygon
          key={`${face.join("-")}-${index}`}
          points={polygonPoints(face, projected)}
          fill={clayFill(face, "front")}
          stroke="rgba(124, 113, 104, 0.055)"
          strokeWidth="0.22"
        />
      ))}
    </g>
  );
}

function ProfileClayMesh({ landmarks }: { landmarks: FacialLandmarks }) {
  const q = (id: LandmarkId) => profileMap(requiredPoint(landmarks, id));
  const trichion = q("trichion");
  const menton = q("menton");
  const tragion = q("tragion");
  const tip = q("pronasale");
  const top = vertices[10];
  const chin = vertices[152];
  const horizontalScale = (tip.x - tragion.x) / (vertices[4].z - vertices[234].z);
  const verticalScale = (menton.y - trichion.y) / (top.y - chin.y);

  const base = vertices.map((vertex) => ({
    x: tragion.x + (vertex.z - vertices[234].z) * horizontalScale,
    y: trichion.y + (top.y - vertex.y) * verticalScale,
  }));
  const anchors: Anchor[] = [
    { vertex: 10, target: trichion },
    { vertex: 9, target: q("upperForehead") },
    { vertex: 8, target: q("glabella") },
    { vertex: 168, target: q("nasion") },
    { vertex: 343, target: q("orbitale") },
    { vertex: 234, target: tragion },
    { vertex: 4, target: tip },
    { vertex: 1, target: q("columella") },
    { vertex: 2, target: q("subnasale") },
    { vertex: 0, target: q("labialeSuperius") },
    { vertex: 13, target: q("stomion") },
    { vertex: 14, target: q("labialeInferius") },
    { vertex: 18, target: q("mentolabialSulcus") },
    { vertex: 199, target: q("softTissuePogonion") },
    { vertex: 152, target: menton },
    { vertex: 58, target: q("gonion") },
    { vertex: 132, target: q("ramusPoint") },
    { vertex: 209, target: q("cheekProjection") },
  ];
  const projected = warpMesh(base, anchors, 25);
  const orderedFaces = faces
    .filter((face) => face.reduce((sum, index) => sum + vertices[index].x, 0) / 3 <= 0.05)
    .map((face) => ({ face, depth: -face.reduce((sum, index) => sum + vertices[index].x, 0) / 3 }))
    .sort((a, b) => a.depth - b.depth);

  return (
    <g aria-label="Canonical clay profile face">
      {orderedFaces.map(({ face }, index) => (
        <polygon
          key={`${face.join("-")}-${index}`}
          points={polygonPoints(face, projected)}
          fill={clayFill(face, "profile")}
          stroke="rgba(124, 113, 104, 0.045)"
          strokeWidth="0.2"
        />
      ))}
    </g>
  );
}

export function CanonicalClayFace({ view, landmarks }: { view: FaceView; landmarks: FacialLandmarks }) {
  return view === "front"
    ? <FrontClayMesh landmarks={landmarks} />
    : <ProfileClayMesh landmarks={landmarks} />;
}
