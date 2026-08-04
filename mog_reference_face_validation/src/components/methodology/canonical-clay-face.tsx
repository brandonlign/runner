import { useMemo } from "react";
import type { FacialLandmarks, LandmarkId, Point2D } from "@/lib/analysis/landmarks";
import {
  decodeGnmHeadMesh,
  GNM_HEAD_MESH,
  type GnmTriangle,
  type GnmVertex,
} from "./gnm-head-mesh";

type FaceView = "front" | "profile";
type Point = { x: number; y: number };
type ControlPair = { source: Point; target: Point };
type ProjectedFace = { face: GnmTriangle; points: string; depth: number; fill: string };
type FittedProjection = {
  points: Point[];
  transform: (point: Point) => Point;
  scale: number;
};

const decodedMesh = decodeGnmHeadMesh();
const landmarkVertices = GNM_HEAD_MESH.landmarkVertexIndices.map(
  (index) => decodedMesh.vertices[index],
);
const SOURCE_TRICHION_Y = 0.3597;
const SOURCE_CHIN = landmarkVertices[8];
const SOURCE_NASION = landmarkVertices[27];
const SOURCE_FACE_HEIGHT = SOURCE_TRICHION_Y - SOURCE_CHIN.y;
const VISIBLE_TRIANGLES = decodedMesh.triangles.filter((face) =>
  face.every((index) => decodedMesh.vertices[index].y > 0.135),
);

function requiredPoint(landmarks: FacialLandmarks, id: LandmarkId): Point2D {
  const point = landmarks.points[id];
  if (!point) throw new Error(`GNM clay face is missing ${id}`);
  return point;
}

function targetRaw(landmarks: FacialLandmarks, id: LandmarkId): Point {
  const point = requiredPoint(landmarks, id);
  return { x: point.x / 1000 - 0.5, y: point.y / 1000 };
}

function average(points: Point[]): Point {
  return {
    x: points.reduce((sum, point) => sum + point.x, 0) / points.length,
    y: points.reduce((sum, point) => sum + point.y, 0) / points.length,
  };
}

function frontSource(vertex: GnmVertex): Point {
  return {
    x: vertex.x / SOURCE_FACE_HEIGHT,
    y: (SOURCE_TRICHION_Y - vertex.y) / SOURCE_FACE_HEIGHT,
  };
}

function profileSource(vertex: GnmVertex): Point {
  return {
    x: (vertex.z - SOURCE_NASION.z) / SOURCE_FACE_HEIGHT,
    y: (SOURCE_TRICHION_Y - vertex.y) / SOURCE_FACE_HEIGHT,
  };
}

function frontLandmark(index: number): Point {
  return frontSource(landmarkVertices[index]);
}

function profileLandmark(index: number): Point {
  return profileSource(landmarkVertices[index]);
}

function radialKernel(a: Point, b: Point): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const radiusSquared = dx * dx + dy * dy;
  return radiusSquared < 1e-14 ? 0 : radiusSquared * Math.log(Math.sqrt(radiusSquared));
}

function solveLinear(matrix: number[][], values: number[]): number[] {
  const size = matrix.length;
  const augmented = matrix.map((row, index) => [...row, values[index]]);
  for (let column = 0; column < size; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < size; row += 1) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) < 1e-12) {
      throw new Error("GNM landmark warp became singular.");
    }
    [augmented[column], augmented[pivot]] = [augmented[pivot], augmented[column]];
    const divisor = augmented[column][column];
    for (let entry = column; entry <= size; entry += 1) augmented[column][entry] /= divisor;
    for (let row = 0; row < size; row += 1) {
      if (row === column) continue;
      const factor = augmented[row][column];
      if (Math.abs(factor) < 1e-15) continue;
      for (let entry = column; entry <= size; entry += 1) {
        augmented[row][entry] -= factor * augmented[column][entry];
      }
    }
  }
  return augmented.map((row) => row[size]);
}

function thinPlateWarp(controls: ControlPair[]): (point: Point) => Point {
  const count = controls.length;
  const size = count + 3;
  const matrix = Array.from({ length: size }, () => Array(size).fill(0));
  for (let row = 0; row < count; row += 1) {
    for (let column = 0; column < count; column += 1) {
      matrix[row][column] = radialKernel(controls[row].source, controls[column].source);
    }
    matrix[row][row] += 1e-8;
    matrix[row][count] = 1;
    matrix[row][count + 1] = controls[row].source.x;
    matrix[row][count + 2] = controls[row].source.y;
    matrix[count][row] = 1;
    matrix[count + 1][row] = controls[row].source.x;
    matrix[count + 2][row] = controls[row].source.y;
  }
  const xValues = [...controls.map(({ target }) => target.x), 0, 0, 0];
  const yValues = [...controls.map(({ target }) => target.y), 0, 0, 0];
  const xCoefficients = solveLinear(matrix.map((row) => [...row]), xValues);
  const yCoefficients = solveLinear(matrix.map((row) => [...row]), yValues);

  return (point) => {
    let x = xCoefficients[count] + xCoefficients[count + 1] * point.x + xCoefficients[count + 2] * point.y;
    let y = yCoefficients[count] + yCoefficients[count + 1] * point.x + yCoefficients[count + 2] * point.y;
    for (let index = 0; index < count; index += 1) {
      const influence = radialKernel(point, controls[index].source);
      x += xCoefficients[index] * influence;
      y += yCoefficients[index] * influence;
    }
    return { x, y };
  };
}

function fixedControls(points: Point[]): ControlPair[] {
  return points.map((point) => ({ source: point, target: point }));
}

function frontControls(landmarks: FacialLandmarks): ControlPair[] {
  const target = (id: LandmarkId) => targetRaw(landmarks, id);
  const sourceLeftPupil = average([42, 43, 44, 45, 46, 47].map(frontLandmark));
  const sourceRightPupil = average([36, 37, 38, 39, 40, 41].map(frontLandmark));
  return [
    { source: { x: 0, y: 0 }, target: target("trichion") },
    { source: average([frontLandmark(21), frontLandmark(22)]), target: target("glabella") },
    { source: frontLandmark(27), target: target("nasion") },
    { source: frontLandmark(30), target: target("pronasale") },
    { source: frontLandmark(33), target: target("subnasale") },
    { source: frontLandmark(51), target: target("labialeSuperius") },
    { source: average([frontLandmark(62), frontLandmark(66)]), target: target("stomion") },
    { source: frontLandmark(57), target: target("labialeInferius") },
    { source: frontLandmark(8), target: target("menton") },
    { source: { x: 0.4384, y: 0.4447 }, target: target("leftZygion") },
    { source: { x: -0.4384, y: 0.4447 }, target: target("rightZygion") },
    { source: frontLandmark(12), target: target("leftGonion") },
    { source: frontLandmark(4), target: target("rightGonion") },
    { source: { x: 0.4402, y: 0.3 }, target: target("leftFrontotemporale") },
    { source: { x: -0.4402, y: 0.3 }, target: target("rightFrontotemporale") },
    { source: frontLandmark(42), target: target("leftEndocanthion") },
    { source: frontLandmark(45), target: target("leftExocanthion") },
    { source: frontLandmark(39), target: target("rightEndocanthion") },
    { source: frontLandmark(36), target: target("rightExocanthion") },
    { source: sourceLeftPupil, target: target("leftPupilCenter") },
    { source: sourceRightPupil, target: target("rightPupilCenter") },
    { source: average([frontLandmark(43), frontLandmark(44)]), target: target("leftSuperiorEyelid") },
    { source: average([frontLandmark(37), frontLandmark(38)]), target: target("rightSuperiorEyelid") },
    { source: average([frontLandmark(46), frontLandmark(47)]), target: target("leftInferiorEyelid") },
    { source: average([frontLandmark(40), frontLandmark(41)]), target: target("rightInferiorEyelid") },
    { source: frontLandmark(22), target: target("leftEyebrowMedial") },
    { source: frontLandmark(21), target: target("rightEyebrowMedial") },
    { source: frontLandmark(26), target: target("leftEyebrowLateral") },
    { source: frontLandmark(17), target: target("rightEyebrowLateral") },
    { source: frontLandmark(24), target: target("leftEyebrowHigh") },
    { source: frontLandmark(19), target: target("rightEyebrowHigh") },
    { source: frontLandmark(35), target: target("leftAlare") },
    { source: frontLandmark(31), target: target("rightAlare") },
    { source: frontLandmark(54), target: target("leftCheilion") },
    { source: frontLandmark(48), target: target("rightCheilion") },
    ...fixedControls([
      { x: -0.8, y: -0.35 }, { x: -0.4, y: -0.35 }, { x: 0, y: -0.35 },
      { x: 0.4, y: -0.35 }, { x: 0.8, y: -0.35 }, { x: -0.9, y: 0 },
      { x: -0.9, y: 0.4 }, { x: -0.85, y: 0.8 }, { x: -0.65, y: 1.25 },
      { x: 0, y: 1.48 }, { x: 0.65, y: 1.25 }, { x: 0.85, y: 0.8 },
      { x: 0.9, y: 0.4 }, { x: 0.9, y: 0 },
    ]),
  ];
}

function profileControls(landmarks: FacialLandmarks): ControlPair[] {
  const target = (id: LandmarkId) => targetRaw(landmarks, id);
  return [
    { source: { x: 0, y: 0 }, target: target("trichion") },
    { source: { x: 0.03, y: 0.16 }, target: target("upperForehead") },
    { source: average([profileLandmark(21), profileLandmark(22)]), target: target("glabella") },
    { source: { x: 0.02, y: 0.285 }, target: target("browRidge") },
    { source: profileLandmark(27), target: target("nasion") },
    { source: profileLandmark(30), target: target("pronasale") },
    { source: { x: 0.105, y: 0.6 }, target: target("columella") },
    { source: profileLandmark(33), target: target("subnasale") },
    { source: profileLandmark(35), target: target("alare") },
    { source: profileLandmark(51), target: target("labialeSuperius") },
    { source: average([profileLandmark(62), profileLandmark(66)]), target: target("stomion") },
    { source: profileLandmark(57), target: target("labialeInferius") },
    { source: { x: 0.015, y: 0.88 }, target: target("mentolabialSulcus") },
    { source: { x: 0.01, y: 0.94 }, target: target("softTissuePogonion") },
    { source: profileLandmark(8), target: target("menton") },
    { source: profileLandmark(12), target: target("gonion") },
    { source: profileLandmark(14), target: target("ramusPoint") },
    { source: { x: -0.5, y: 0.4 }, target: target("tragion") },
    { source: { x: -0.05, y: 0.4 }, target: target("orbitale") },
    { source: { x: 0, y: 0.48 }, target: target("cheekProjection") },
    ...fixedControls([
      { x: -1.25, y: -0.25 }, { x: -0.8, y: -0.25 }, { x: -0.4, y: -0.25 },
      { x: 0, y: -0.25 }, { x: 0.4, y: -0.25 }, { x: -1.3, y: 0.1 },
      { x: -1.3, y: 0.4 }, { x: -1.25, y: 0.7 }, { x: -1.1, y: 1.05 },
      { x: -0.8, y: 1.3 }, { x: -0.4, y: 1.3 }, { x: 0, y: 1.3 },
      { x: 0.5, y: 1.3 }, { x: 0.75, y: 1.1 }, { x: 0.7, y: 0.2 },
      { x: 0.55, y: -0.1 },
    ]),
  ];
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

function faceNormal(face: GnmTriangle): GnmVertex {
  return normal(
    decodedMesh.vertices[face[0]],
    decodedMesh.vertices[face[1]],
    decodedMesh.vertices[face[2]],
  );
}

function facesForView(view: FaceView): GnmTriangle[] {
  return VISIBLE_TRIANGLES.filter((face) => {
    const value = faceNormal(face);
    return view === "front" ? value.z < 0 : value.x > 0;
  });
}

const vertexNormals = (() => {
  const sums = decodedMesh.vertices.map(() => ({ x: 0, y: 0, z: 0 }));
  for (const face of VISIBLE_TRIANGLES) {
    const value = faceNormal(face);
    for (const index of face) {
      sums[index].x += value.x;
      sums[index].y += value.y;
      sums[index].z += value.z;
    }
  }
  return sums.map((value) => {
    const length = Math.hypot(value.x, value.y, value.z) || 1;
    return { x: value.x / length, y: value.y / length, z: value.z / length };
  });
})();

function clayFill(face: GnmTriangle, view: FaceView): string {
  const light = view === "front"
    ? { x: -0.36, y: 0.36, z: 0.86 }
    : { x: -0.78, y: 0.32, z: 0.54 };
  const diffuse = face.reduce((sum, index) => {
    const value = vertexNormals[index];
    return sum + Math.abs(value.x * light.x + value.y * light.y + value.z * light.z);
  }, 0) / 3;
  const brightness = Math.min(0.98, Math.max(0.78, 0.82 + diffuse * 0.15));
  return `rgb(${Math.round(brightness * 255)} ${Math.round(brightness * 249)} ${Math.round(brightness * 242)})`;
}

function fitProjection(rawPoints: Point[], visibleFaces: GnmTriangle[]): FittedProjection {
  const used = new Set(visibleFaces.flatMap((face) => [...face]));
  const visible = rawPoints.filter((_, index) => used.has(index));
  const minimumX = Math.min(...visible.map((point) => point.x));
  const maximumX = Math.max(...visible.map((point) => point.x));
  const minimumY = Math.min(...visible.map((point) => point.y));
  const maximumY = Math.max(...visible.map((point) => point.y));
  const scale = Math.min(520 / (maximumX - minimumX), 584 / (maximumY - minimumY));
  const centerX = (minimumX + maximumX) / 2;
  const transform = (point: Point): Point => ({
    x: 300 + (point.x - centerX) * scale,
    y: 18 + (point.y - minimumY) * scale,
  });
  return { points: rawPoints.map(transform), transform, scale };
}

function polygonPoints(face: GnmTriangle, projected: Point[]): string {
  return face.map((index) => `${projected[index].x.toFixed(2)},${projected[index].y.toFixed(2)}`).join(" ");
}

function buildFaces(view: FaceView, landmarks: FacialLandmarks): { faces: ProjectedFace[]; fitted: FittedProjection } {
  const sourceProjection = decodedMesh.vertices.map(view === "front" ? frontSource : profileSource);
  const warp = thinPlateWarp(view === "front" ? frontControls(landmarks) : profileControls(landmarks));
  const renderFaces = facesForView(view);
  const fitted = fitProjection(sourceProjection.map(warp), renderFaces);
  const faces = renderFaces.map((face) => ({
    face,
    points: polygonPoints(face, fitted.points),
    depth: view === "front"
      ? (decodedMesh.vertices[face[0]].z + decodedMesh.vertices[face[1]].z + decodedMesh.vertices[face[2]].z) / 3
      : -(decodedMesh.vertices[face[0]].x + decodedMesh.vertices[face[1]].x + decodedMesh.vertices[face[2]].x) / 3,
    fill: clayFill(face, view),
  })).sort((a, b) => a.depth - b.depth);
  return { faces, fitted };
}

function ClayEyes({ view, landmarks, fitted }: { view: FaceView; landmarks: FacialLandmarks; fitted: FittedProjection }) {
  if (view === "profile") {
    const center = fitted.transform(targetRaw(landmarks, "orbitale"));
    return <ellipse cx={center.x} cy={center.y} rx={fitted.scale * 0.035} ry={fitted.scale * 0.022} fill="#d7d0c9" />;
  }
  const leftCenter = fitted.transform(targetRaw(landmarks, "leftPupilCenter"));
  const rightCenter = fitted.transform(targetRaw(landmarks, "rightPupilCenter"));
  const leftInner = fitted.transform(targetRaw(landmarks, "leftEndocanthion"));
  const leftOuter = fitted.transform(targetRaw(landmarks, "leftExocanthion"));
  const superior = fitted.transform(targetRaw(landmarks, "leftSuperiorEyelid"));
  const inferior = fitted.transform(targetRaw(landmarks, "leftInferiorEyelid"));
  const radiusX = Math.hypot(leftOuter.x - leftInner.x, leftOuter.y - leftInner.y) * 0.48;
  const radiusY = Math.abs(inferior.y - superior.y) * 0.48;
  return (
    <g fill="#d7d0c9">
      <ellipse cx={leftCenter.x} cy={leftCenter.y} rx={radiusX} ry={radiusY} />
      <ellipse cx={rightCenter.x} cy={rightCenter.y} rx={radiusX} ry={radiusY} />
    </g>
  );
}

function GnmClayMesh({ view, landmarks }: { view: FaceView; landmarks: FacialLandmarks }) {
  const projection = useMemo(() => buildFaces(view, landmarks), [view, landmarks]);
  return (
    <g aria-label={`Google GNM neutral clay ${view} illustration`}>
      <rect x="-100" y="-100" width="800" height="820" fill="var(--paper)" />
      {projection.faces.map(({ face, points, fill }, index) => (
        <polygon
          key={`${face[0]}-${face[1]}-${face[2]}-${index}`}
          points={points}
          fill={fill}
          stroke="none"
        />
      ))}
      <ClayEyes view={view} landmarks={landmarks} fitted={projection.fitted} />
    </g>
  );
}

/**
 * Illustrative neutral clay surface aligned by thin-plate interpolation to the
 * canonical semantic landmarks. Only those semantic landmarks enter Mog's
 * measurements; GNM surface vertices never enter the score.
 */
export function CanonicalClayFace({ view, landmarks }: { view: FaceView; landmarks: FacialLandmarks }) {
  return <GnmClayMesh view={view} landmarks={landmarks} />;
}
